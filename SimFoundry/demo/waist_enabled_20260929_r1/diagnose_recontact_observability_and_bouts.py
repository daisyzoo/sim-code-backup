"""Read-only diagnosis of completed recontact episodes; never training admission.
Camera projection uses recorded camera poses, not imagined visibility. A projected
bounding box is geometric coverage, not segmentation/occlusion evidence. Contact
forces are final substep samples; bout associations do not establish causality.
"""
from pathlib import Path
import sys,json,hashlib,itertools,datetime,collections
import numpy as np
from scipy.spatial.transform import Rotation
from PIL import Image,ImageDraw
w=Path(__file__).resolve().parent
run=w/'recontact_pose_groups_r1'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
results=[]
for ep in sorted(run.glob('case_*/layout_*')):
 if not (ep/'quality.json').exists() or 'wait' in ep.name:continue
 quality=json.loads((ep/'quality.json').read_text())
 if quality['frames']!=1200:continue
 target='box' if 'push_box' in ep.name else 'mailer'
 other='mailer' if target=='box' else 'box';direction=-1 if target=='box' else 1
 with np.load(ep/'raw.npz') as z:q=z['q'].copy();rgb=z['rgb'].copy()
 with np.load(ep/'trace.npz') as z:xyz={k:z[k].copy() for k in [target,other]}
 with np.load(ep/'parcel_orientation.npz') as z:rot={k:Rotation.from_quat(z[k]).as_matrix() for k in [target,other]}
 fr=json.loads((ep/'frontal_bypass.json').read_text())['rows'];by_step={r['step']:r for r in fr}
 events=json.loads((ep/'recontact_pose.json').read_text())['rows']
 captures=[r for r in events if r['kind']=='handover'];commands=[r for r in events if r['kind']=='command']
 tilt=np.arccos(np.clip(rot[target][:,2,2],-1,1))
 view=json.loads((ep/'viewer_observer.json').read_text())['frames'];camrows=[]
 for v in view:
  t=v['pre_action_step'];R=Rotation.from_quat(v['policy_camera_quat_ros_xyzw']).as_matrix();pos=np.array(v['policy_camera_position_world']);K=np.array(v['policy_camera_intrinsics']);entry={'step':t,'waist_rad':float(q[t,12])}
  for k in [target,other]:
   size=np.array([.14,.09,.045] if k=='box' else [.15,.145,.04]);corners=np.array(list(itertools.product([-1,1],repeat=3)))*size/2
   world=corners@rot[k][t].T+xyz[k][t];camera=(world-pos)@R
   assert (camera[:,2]>0).all(),(ep.name,t,k)
   px=camera@K.T;uv=px[:,:2]/px[:,2:];lo=uv.min(0);hi=uv.max(0)
   clipped=np.maximum(0,np.minimum(hi,[rgb.shape[3],rgb.shape[2]])-np.maximum(lo,0));fraction=float(np.prod(clipped)/np.prod(hi-lo))
   entry[k]={'bbox_min':lo.tolist(),'bbox_max':hi.tolist(),'projected_bbox_fraction':fraction,'completely_outside':fraction==0}
  camrows.append(entry)
 samples=np.linspace(0,len(camrows)-1,8,dtype=int).tolist();canvas=Image.new('RGB',(1280,530));draw=ImageDraw.Draw(canvas)
 for i,j in enumerate(samples):
  v=camrows[j];t=v['step'];im=Image.fromarray(rgb[t].transpose(1,2,0));d=ImageDraw.Draw(im)
  for k,color in [(target,'red'),(other,'yellow')]:d.rectangle([*v[k]['bbox_min'],*v[k]['bbox_max']],outline=color,width=3)
  x=(i%4)*320;y=(i//4)*265;canvas.paste(im.resize((320,240)),(x,y));draw.text((x,y+241),f"{t} yaw={v['waist_rad']:.2f} target={v[target]['projected_bbox_fraction']:.2f}")
 sheet=ep/'RECONTACT_CAMERA_PROJECTION.jpg';canvas.save(sheet)
 bouts=[];start=None
 for r in fr:
  t=r['step']
  if r['mode']=='top_push' and start is None:start=t
  elif r['mode']!='top_push' and start is not None:
   recent=[c for c in captures if c['step']<start];capture=recent[-1] if recent else None
   window=[by_step[k] for k in range(start,t)];load=[x['contact_load']['observed_vertical_load_n'] for x in window]
   bouts.append({'start':start,'end':t-1,'exit_step':t,'exit_reason':r.get('last_recontact_reason'),'push_frames':t-start,'preceding_capture_step':capture['step'] if capture else None,'tilt_at_push_start_rad':float(tilt[start]),'tilt_at_exit_rad':float(tilt[t]),'max_tilt_during_push_rad':float(tilt[start:t+1].max()),'median_vertical_load_n':float(np.median(load)),'max_vertical_load_n':float(max(load)),'signed_progress_mm':float(direction*(xyz[target][t,1]-xyz[target][start,1])*1000)})
   start=None
 summary={'original_task_passed':quality['passed'],'progress_mm':quality['metrics']['target_final_progress_m']*1000,'non_target_max_xy_mm':quality['metrics'][other+'_max_xy_m']*1000,'new_path_command_frames':len(commands),'handover_frames':len(captures),'completed_push_bouts':len(bouts),'unfinished_push_start':start,'push_mode_frames':sum(r['mode']=='top_push' for r in fr),'exit_reasons':dict(collections.Counter(b['exit_reason'] for b in bouts)),'camera_sample_count':len(camrows),'target_bbox_completely_outside_samples':sum(v[target]['completely_outside'] for v in camrows),'both_bbox_completely_outside_samples':sum(v[target]['completely_outside'] and v[other]['completely_outside'] for v in camrows),'target_half_bbox_samples':sum(v[target]['projected_bbox_fraction']>=.5 for v in camrows),'max_tilt_rad':float(tilt.max())}
 names=['quality.json','raw.npz','trace.npz','parcel_orientation.npz','viewer_observer.json','frontal_bypass.json','recontact_pose.json'];out={'episode':ep.name,'summary':summary,'bouts':bouts,'captures':[{'step':c['step'],'path_ticks':c['ticks'],'waist_rad':c['context']['current'][0],'selected_surface_local_xy':c['selected_surface_local_xy'],'normal_local_up':c['captured_normal_local_up']} for c in captures],'camera_rows':camrows,'projection_sheet_sha256':sha(sheet),'source_sha256':{n:sha(ep/n) for n in names}}
 results.append(out);print(ep.name,json.dumps(summary),flush=True)
report={'updated_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':__doc__,'episodes':results,'script_sha256':sha(__file__),'training_ready':False,'physical_controller_changed':False}
(run/'OBSERVABILITY_AND_BOUTS_PARTIAL.json').write_text(json.dumps(report,indent=2))
