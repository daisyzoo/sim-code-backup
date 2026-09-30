"""Test intersection of observed top-contact reach and unchanged-camera coverage."""
from pathlib import Path
import sys,ast,itertools
root=Path(__file__).resolve().parent
source=(root/'audit_terminal_reach.py').read_text()
exec(compile(source.split('results=[];rng')[0],'<validated_cached_fk_setup>','exec'))
sys.path.insert(0,str(root.parents[1]))
from simfoundry.data.top_contact_bypass import support_mesh,top_surface_point
meshes={s:np.array(v) for s,v in support_mesh().items()};vals={}
for node in ast.parse((root.parents[1]/'simfoundry/calibration/sorting_station.py').read_text()).body:
 if isinstance(node,ast.Assign):
  for target in node.targets:
   if isinstance(target,ast.Name) and target.id in ['SORTING_D435I_POS','SORTING_D435I_ROT_XYZW']:vals[target.id]=ast.literal_eval(node.value)
Ropt=Rotation.from_quat(vals['SORTING_D435I_ROT_XYZW']).as_matrix();camoff=np.array(vals['SORTING_D435I_POS'])
def fk(side,q):
 m=np.eye(4);m[:3,3]=[.08,0,.793]
 for name,orig,axis in chains[side]:
  m=m@orig
  if axis is not None:r=np.eye(4);r[:3,:3]=Rotation.from_rotvec(axis*q.get(name,0)).as_matrix();m=m@r
 return m
rng=np.random.default_rng(529);rows=[];run=root/'frontal_top_load5_long_r1'
for side,task in [('left','nudge_mailer_to_bin'),('right','push_box_to_bin')]:
 ep=run/'case_62000'/f'layout_62000_{task}';j=json.loads((ep/'frontal_bypass.json').read_text());other='right' if side=='left' else 'left';anchor=np.array(j['plan']['inactive_anchor_override']['xyz']);key='mailer' if side=='left' else 'box';size=np.array([.15,.145,.04] if side=='left' else [.14,.09,.045]);core_size=size*np.array([.90,.88,1.] if side=='left' else [.96,.96,1.]);mesh=meshes[side]
 push=[row['step'] for i,row in enumerate(j['rows']) if row['mode']=='top_push' and (i==0 or j['rows'][i-1]['mode']!='top_push')];times=[push[0],push[len(push)//2],push[-1]]
 z=np.load(ep/'raw.npz');tr=np.load(ep/'trace.npz');ori=np.load(ep/'parcel_orientation.npz');fx,fy,cx,cy=z['intrinsics'];width=z['rgb'].shape[3];height=z['rgb'].shape[2]
 for t in times:
  initial=z['q'][t,12:23];rot=Rotation.from_quat(ori[key][t]).as_matrix();center=tr[key][t];corners=np.array(list(itertools.product([-1,1],repeat=3)))*size/2;world_corners=corners@rot.T+center;n=rot[:,2]
  def projection(waist):
   rz=Rotation.from_euler('z',waist).as_matrix();pos=np.array([.08-.0039635,0,.793+.044])+rz@camoff;rc=rz@Ropt;cam=(world_corners-pos)@rc
   uv=np.c_[fx*cam[:,0]/cam[:,2]+cx,fy*cam[:,1]/cam[:,2]+cy];a=uv.min(0);b=uv.max(0);area=float(np.prod(b-a));inter=np.maximum(0,np.minimum(b,[width,height])-np.maximum(a,[0,0]));visible=float(np.prod(inter)/max(area,1e-12)) if (cam[:,2]>0).all() else 0.
   return visible
  allowed=[w for w in np.linspace(-.98,.98,393) if projection(w)>=.5];assert allowed
  fixed_waist=min(allowed,key=lambda w:abs(w-float(initial[0])))
  for inset in [.02,.025,.03]:
   direction=1 if side=='left' else -1;half=core_size[:2]/2;low=-half+.01;high=half-.01;advance=direction*rot[1,:2]*inset;low=np.maximum(low,-half-np.minimum(advance,0));high=np.minimum(high,half-np.maximum(advance,0));assert np.all(low<=high);local=np.r_[np.where(rot[0,:2]>=0,low,high),core_size[2]/2];goal=center+rot@local
   def measure(arms):
    q=np.r_[fixed_waist,arms];d=dict(zip(names,q));m=fk(side,d);world=mesh@m[:3,:3].T+m[:3,3];idx=int(np.argmin((world-goal)@n));return q,d,world,idx
   def residual(arms):
    q,d,world,idx=measure(arms)
    return np.r_[world[idx]-goal,palm(other,d)-anchor,4*max(0,.755-float(world[:,2].min()))]
   best=None
   for start in [initial[1:],np.zeros(10),*rng.uniform(lo[1:],hi[1:],(2,10))]:
    fit=least_squares(residual,np.clip(start,lo[1:]+1e-6,hi[1:]-1e-6),bounds=(lo[1:],hi[1:]),max_nfev=180);q,d,world,idx=measure(fit.x);err=float(np.linalg.norm(fit.fun))
    if best is None or err<best['error_m']:best=dict(error_m=err,point_error_m=float(np.linalg.norm(world[idx]-goal)),inactive_palm_error_m=float(np.linalg.norm(palm(other,d)-anchor)),q=q.tolist(),min_hand_z=float(world[:,2].min()))
   row=dict(side=side,frame=t,forward_margin_m=inset,edge_inset_m=.01,actual_waist_rad=float(initial[0]),actual_projected_bbox_fraction_in_image=projection(float(initial[0])),candidate_waist_rad=float(fixed_waist),candidate_projected_bbox_fraction_in_image=projection(fixed_waist),camera_allowed_grid_min_max=[float(min(allowed)),float(max(allowed))],best=best);rows.append(row);print(side,t,inset,'waist',fixed_waist,'point_error',best['point_error_m'],'actual_visibility',row['actual_projected_bbox_fraction_in_image'],flush=True)
(root/'VISIBLE_FORWARD_MARGIN_REACH_AUDIT.json').write_text(json.dumps(dict(rows=rows,scope='Actual first/middle/final top-push onset poses, unchanged calibrated camera. Choose nearest recorded waist with>=50percent projected bbox area inside image (diagnostic target, not new hard quality gate); fit actual convex-hand top support at minimum-worldX feasible top point inside 10mm XY inset plus20/25/30mm commanded-worldY forward margin of ACTUAL collision core (mailer scale.90/.88/1,box.96/.96/1 from scene_bridge/isaac_cfg.py) with fixed waist. Corner sign selected per audited fixed pose; would need phase-latching to avoid runtime corner flips under yaw. Static multistart endpoint IK, no global infeasibility/path/full-arm/collision/dynamic/occlusion proof. No candidate executed; no camera or base changed.',training_ready=False),indent=2))
