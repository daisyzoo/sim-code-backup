"""Independent raw-contact, LP and history check; no simulated effect claims."""
from pathlib import Path
import json, sys, hashlib, importlib.util, ast
import numpy as np
from scipy.optimize import linprog
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent
stage=w/'staged_rear_core_slice_motion_probe'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def module(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
old=module(w/'staged_rear_cop_core_slice/rear_cop_centering.py','motion_parent')
new=module(stage/'rear_cop_centering.py','motion_candidate')
def interval(cop,R,size):
 h=size[:2]/2-.01;a=R[0,:2];A=np.r_[a,-a][:,None];b=np.r_[h-cop[:2],h+cop[:2]]
 lo=linprog([1.],A_ub=A,b_ub=b,bounds=[(None,None)],method='highs');hi=linprog([-1.],A_ub=A,b_ub=b,bounds=[(None,None)],method='highs')
 if lo.status==2 or hi.status==2:return None
 assert lo.success and hi.success
 return np.array([lo.x[0],hi.x[0]])
class Independent:
 def __init__(self):self.reset()
 def reset(self):self.anchor=None;self.last=None
 def update(self,k):
  if k['mode']!='top_push':self.reset();return dict(override=False,reason='original_non_push_mode')
  if k['cop_local'] is None or k['normal_load_n']<.3:self.reset();return dict(override=False,reason='no_valid_loaded_contact')
  cop,R,size,obj=(k[x] for x in ['cop_local','object_rotation','core_size','object_xyz']);iv=interval(cop,R,size);cw=obj+R@cop
  if self.anchor is None:
   self.anchor=np.r_[np.clip(cop[:2],-size[:2]/2+.01,size[:2]/2-.01),cop[2]]
   self.last=None if iv is None else float(np.clip((obj+R@self.anchor)[0],*(iv+cw[0])))
   return dict(override=False,reason='preserve_first_loaded_push')
  if iv is None:self.reset();return dict(override=False,reason='no_world_x_core_interior_slice')
  chosen=float(np.clip((obj+R@self.anchor)[0],*(iv+cw[0])));prior=self.last
  feed=0. if prior is None else chosen-prior
  previous,reference,parent=(k[x] for x in ['previous_xyz','reference_xyz','parent_xyz'])
  low=max(previous[0]-.002,reference[0]-.03);high=min(previous[0]+.002,reference[0]+.03)
  if low>high:self.reset();return dict(override=False,reason='no_cartesian_slew_and_lead_interval')
  error=float(np.clip(0,*iv));desired=previous[0]+feed+.05*error;expected=parent.copy();expected[0]=np.clip(desired,low,high);self.last=chosen
  return dict(override=True,reason='loaded_rear_transverse_centering',command_xyz=expected,feed_x_m=feed,error_x_m=error,desired_x_m=desired,core_slice_target_world_x_m=chosen,previous_core_slice_target_world_x_m=prior)
def verify(got,expected,k):
 assert got['override']==expected['override'] and got['reason']==expected['reason']
 if not got['override']:return
 for key,value in expected.items():
  if key in ['override','reason']:continue
  if value is None:assert got[key] is None
  else:assert np.max(abs(np.asarray(got[key])-value))<1e-8,(key,got[key],value)
 cmd=np.array(got['command_xyz']);assert np.array_equal(cmd[1:],k['parent_xyz'][1:])
 assert abs(cmd[0]-k['previous_xyz'][0])<=.002+1e-12 and abs(cmd[0]-k['reference_xyz'][0])<=.03+1e-12
reports=[]
for run in ['region_continuity_groups_r1','region_causal_response_groups_r1','region_causal_xy_groups_r2','region_measured_bounds_groups_r1','rear_cop_measured_bounds_groups_r1','rear_core_slice_groups_r1']:
 for cid,task in [(840001,'push_box_to_bin'),(840004,'nudge_mailer_to_bin')]:
  ep=w/run/f'case_{cid}/layout_{cid}_{task}';fr=json.loads((ep/'frontal_bypass.json').read_text());key='box' if cid==840001 else 'mailer';side='right' if key=='box' else 'left';actor='parcel_box' if key=='box' else 'mailer'
  src=json.loads((ep.parent/'provenance.json').read_text())['source_sha256'];cfg=ep.parent/'source_snapshot/simfoundry/scene_bridge/isaac_cfg.py';assert sha(cfg)==src['simfoundry/scene_bridge/isaac_cfg.py'];node=next(n for n in ast.walk(ast.parse(cfg.read_text())) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='core_scale' for t in n.targets));assert ast.unparse(node.value.test)=="obj.semantic == 'mailer'";scale=np.array(ast.literal_eval(node.value.orelse if key=='box' else node.value.body));size=np.array(fr['plan']['top_recontact']['contact_size_xyz'])*scale
  with np.load(ep/'trace.npz') as z:xyz=z[key].astype(float)
  with np.load(ep/'parcel_orientation.npz') as z:R=Rotation.from_quat(z[key]).as_matrix()
  packets={p['after_action_step']:p for p in json.loads((ep/'solved_contact_forces.json').read_text())['rows']};pairs=[(old.RearCopCentering(core_slice_feedback=f),new.RearCopCentering(core_slice_feedback=f)) for f in [False,True]]
  candidate=new.RearCopCentering(core_slice_feedback=True,core_slice_motion_feedforward=True);ind=Independent();previous=None;rows=[]
  for f in fr['rows']:
   t=f['step'];packet=packets.get(t-1);points=[];weights=[]
   if packet is not None:
    assert max(abs(np.array(packet['post_action_pose'][key])-xyz[t]))<1e-6
    for contact in packet['parcel_contacts']:
     slots=[i for i,s in enumerate(contact['shapes']) if '/'+actor+'/' in s]
     if len(slots)!=1 or not any(side+'_wrist' in s for s in contact['shapes']):continue
     force=np.array(contact['force_world_N'])*(1 if slots[0]==1 else -1);normal=-float(force@R[t,:,2])
     if normal>.05:points.append(contact['position_world']);weights.append(normal)
   normal=sum(weights);cop=R[t].T@(np.average(points,axis=0,weights=weights)-xyz[t]) if weights else None;reference=np.array(f['observed_support_xyz']);parent=np.array(f['target_xyz']);prev=reference if previous is None else previous
   k=dict(mode=f['mode'],parent_xyz=parent,previous_xyz=prev,reference_xyz=reference,object_xyz=xyz[t],object_rotation=R[t],core_size=size,cop_local=cop,normal_load_n=normal)
   for a,b in pairs:assert a.update(**k)==b.update(**k)
   expected=ind.update(k);got=candidate.update(**k);verify(got,expected,k);rows.append(dict(step=t,result=got));previous=parent
  reports.append(dict(run=run,episode=ep.name,frames=len(rows),overrides=sum(x['result']['override'] for x in rows),rows=rows,source_sha256={n:sha(ep/n) for n in ['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','solved_contact_forces.json']},collision_source_sha256=sha(cfg)))
  print(run,task,len(rows),reports[-1]['overrides'],flush=True)
# Explicit independent state-machine sequences: preserve first, lost/reentry,
# no slice/reentry, disjoint command bounds/reentry, original nonpush guards.
k=dict(mode='top_push',parent_xyz=np.array([.5,0,.8]),previous_xyz=np.array([.5,0,.8]),reference_xyz=np.array([.5,0,.8]),object_xyz=np.array([.5,0,.78]),object_rotation=np.eye(3),core_size=np.array([.12,.10,.04]),cop_local=np.array([-.06,0,.02]),normal_load_n=5.)
sequence=[{}, {}, {'cop_local':None}, {}, {}, {'object_rotation':Rotation.from_euler('z',90,degrees=True).as_matrix()}, {}, {}, {'reference_xyz':np.array([.8,0,.8])}, {}, {}, {'mode':'top_recover'}, {}, {}, {'mode':'goal_hold'}, {}, {}, {'normal_load_n':.1}, {}, {}]
c=new.RearCopCentering(core_slice_feedback=True,core_slice_motion_feedforward=True);i=Independent();reasons=[]
for delta in sequence:
 data={**k,**delta};got=c.update(**data);verify(got,i.update(data),data);reasons.append(got['reason'])
assert {'no_world_x_core_interior_slice','no_cartesian_slew_and_lead_interval','preserve_first_loaded_push','original_non_push_mode','no_valid_loaded_contact'}<=set(reasons)
negative=0
for kwargs in [dict(core_slice_motion_feedforward=f,core_slice_feedback=True) for f in [0,1,None,'yes']]+[dict(core_slice_motion_feedforward=True,core_slice_feedback=False)]:
 try:new.RearCopCentering(**kwargs)
 except ValueError:negative+=1
 else:raise AssertionError('Invalid flag accepted')
for delta in [{'normal_load_n':float('nan')},{'normal_load_n':-1},{'object_xyz':np.array([np.nan,0,0])},{'object_rotation':np.zeros((3,3))},{'core_size':np.array([.01,.1,.04])},{'parent_xyz':np.zeros(2)}]:
 try:new.RearCopCentering(core_slice_feedback=True,core_slice_motion_feedforward=True).update(**{**k,**delta})
 except ValueError:negative+=1
 else:raise AssertionError('Invalid input accepted')
out=dict(passed=True,episodes=reports,total_frames=sum(r['frames'] for r in reports),default_parity_flag_variants=2,total_overrides=sum(r['overrides'] for r in reports),state_fixtures=len(sequence),negative_cases=negative,candidate_sha256=sha(stage/'rear_cop_centering.py'),parent_sha256=sha(w/'staged_rear_cop_core_slice/rear_cop_centering.py'),checker_sha256=sha(Path(__file__)),collector_wired=False,physical_started=False,training_ready=False,scope='Independent previous raw-force COP, archived collision geometry, LP slice, separately maintained anchor/slice history. Twelve fixed histories; candidate actions are NOT fed to physics. Default off exact both parent flags, first loaded and guard reset preserved, fixed gain/YZ/step/lead. This does not predict closed-loop success.')
p=stage/'CHECK.json';assert not p.exists();p.write_text(json.dumps(out,indent=2));print('PASSED',out['total_frames'],out['total_overrides'],negative,flush=True)
