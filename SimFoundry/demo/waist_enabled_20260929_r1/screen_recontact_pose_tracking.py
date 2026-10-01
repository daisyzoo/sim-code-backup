"""Recursive tracking screen of previously planned unloaded recontact endpoints.
Compare uncompensated versus inverse causal response with identical scene checks.
No physical controller or objects changed. Fixed locally measured bias is a
stress model, not a validated long-horizon predictor. Replace the earlier .84m
inactive-hand floor proxy with direct >=10mm hand-face separation from BOTH
parcels, matching allowed coordinated arm motion. Elbow/hand samples are not
full-body/substep collision certification. No loaded contact is simulated.
"""
from pathlib import Path
import json,sys,hashlib
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_unloaded_wrist_prior';sys.path[:0]=[str(stage),str(repo)]
from clearance_runtime import ClearanceGuard
from simfoundry.data.hand_obstacle_clearance import hand_face_separation
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();guard=ClearanceGuard(repo,stage);source=w/'RECONTACT_POSE_REGION_SCREEN.json';plans=json.loads(source.read_text());reports=[]
for record in plans['rows']:
 name=record['episode'];cid=int(name.split('_')[1]);ep=w/'unloaded_wrist_prior_groups_r1'/f'case_{cid}'/name;t=record['step'];side='right' if 'push_box' in name else 'left';inactive='left' if side=='right' else 'right';key='box' if side=='right' else 'mailer';other='mailer' if key=='box' else 'box';wi=10 if side=='right' else 5
 fr=json.loads((ep/'frontal_bypass.json').read_text());core=np.array(fr['plan']['region_causal_response']['actual_core']['collision_core_size_xyz']);sizes={key:core,other:np.array([.15,.145,.04] if other=='mailer' else [.14,.09,.045])};decay=np.array(fr['plan']['region_causal_response']['decay'])
 with np.load(ep/'raw.npz') as z:q=z['q'][t,12:23].astype(float);qp=z['q'][t-1,12:23].astype(float);previous=z['action'][t-1,12:23].astype(float)
 with np.load(ep/'trace.npz') as z:pos={k:z[k][t].astype(float) for k in [key,other]}
 with np.load(ep/'parcel_orientation.npz') as z:quat={k:z[k][t].astype(float) for k in [key,other]}
 rot=Rotation.from_quat(quat[key]).as_matrix();bias=(q-previous)-decay*(qp-previous);seps={s:hand_face_separation(s) for s in [side,inactive]};physical_lo=guard.lower.copy();physical_hi=guard.upper.copy();physical_lo[0]=-1.;physical_hi[0]=1.
 def geometry(x):
  transforms={s:guard.model.fk(s,x)[0] for s in [side,inactive]};T=transforms[side];points=(guard.model.vertices[side]@T[:3,:3].T+T[:3,3]-pos[key])@rot;ix=int(points[:,2].argmin());gaps={}
  for s,k in [(side,other),(inactive,key),(inactive,other)]:
   a=transforms[s];gaps[s+'_'+k]=float(seps[s].gap(a[:3,3],Rotation.from_matrix(a[:3,:3]).as_quat(),pos[k],quat[k],sizes[k]))
  result=dict(active_above_top_m=float(points[ix,2]-core[2]/2),hand_parcel_gaps_m=gaps,elbow_gap_m=float(min(guard.geometry.constraints(x))),physical_bounds=bool(np.all(x>=physical_lo-2e-7) and np.all(x<=physical_hi+2e-7)),contact_object_local=points[ix].tolist())
  result['accepted']=bool(result['active_above_top_m']>=.004 and min(gaps.values())>=.01 and result['elbow_gap_m']>0 and result['physical_bounds']);return result
 variants=[]
 for plan in record['variants']:
  best=plan['best']
  if not best['success']:continue
  goal=np.array(best['candidate']);steps=max(1,int(np.ceil(max(abs(goal-q)/(guard.limits*.25)))));waypoints=[q+(goal-q)*i/steps for i in range(1,steps+1)]
  for compensated in [False,True]:
   current=q.copy();prev=previous.copy();index=0;trace=[];failure=None;hold=0
   for tick in range(600):
    target=waypoints[min(index,len(waypoints)-1)];desired=(target-decay*current-bias)/(1-decay) if compensated else target
    low=np.maximum.reduce([guard.lower,current-guard.limits,prev-.055]);high=np.minimum.reduce([guard.upper,current+guard.limits,prev+.055])
    if np.any(low>high):failure=dict(tick=tick,reason='empty_original_bounds');break
    command=np.clip(desired,low,high).astype(np.float32);check=guard.command(command,current,prev);nextq=(1-decay)*command+decay*current+bias;gc=geometry(command);gn=geometry(nextq);distance=float(max(abs(nextq-target)));trace.append(dict(tick=tick,waypoint=index,max_tracking_error_rad=distance,command=command.tolist(),predicted_q=nextq.tolist(),command_geometry=gc,predicted_geometry=gn,command_accepted=check['accepted']))
    if not(check['accepted'] and gc['accepted'] and gn['accepted']):failure=dict(tick=tick,reason='command_or_predicted_geometry',command_checks=check['checks'],command_geometry=gc,predicted_geometry=gn);break
    current=nextq;prev=command
    if distance<=.003:
     if index<len(waypoints)-1:index+=1
     else:
      hold+=1
      if hold==10:break
   completed=bool(failure is None and hold==10);final=geometry(current);summary=dict(compensated=compensated,wrist_preference=plan['wrist_preference'],completed=completed,ticks=len(trace),waypoints=len(waypoints),reached_waypoint=index,timeout=bool(failure is None and not completed),failure=failure,final_wrist_rad=float(current[wi]),wrist_abs_reduction_rad=float(abs(q[wi])-abs(current[wi])),final_geometry=final,max_endpoint_joint_error_rad=float(max(abs(current-goal))))
   variants.append(dict(summary=summary,trace=trace));print(name,t,'wrist',plan['wrist_preference'],'compensated',compensated,'complete',completed,'ticks',len(trace),'failure',failure and (failure['tick'],failure['reason']),flush=True)
 reports.append(dict(episode=name,step=t,variants=variants,source_sha256={n:sha(ep/n) for n in ['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json']}))
 (w/'RECONTACT_POSE_TRACKING_SCREEN.json').write_text(json.dumps(dict(scope=__doc__,rows=reports,source_plan_sha256=sha(source),checker_sha256=sha(Path(__file__)),geometry_sources={str(p):sha(p) for p in [stage/'clearance_runtime.py',stage/'articulated_hand_geometry.py',stage/'self_clearance.py',repo/'simfoundry/data/hand_obstacle_clearance.py']},model_sources=guard.model.source_sha256,controller_changed=False,physical_validation=False,training_ready=False),indent=2))
