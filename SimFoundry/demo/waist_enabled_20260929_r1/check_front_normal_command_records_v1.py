"""Independent audit of serialized runtime outputs at all9740original contexts.
Each frame retains original physical history; this is not a recursive rollout.
Recovery transitions supplied by the previously verified native prefix replay.
"""
from pathlib import Path
import copy,datetime,gzip,hashlib,json,sys
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_normal_nondegradation_v3';D=W/'front_normal_command_records_r1';D.mkdir(exist_ok=False);sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from front_normal_nondegradation_runtime_candidate_v1 import FrontNormalNondegradation
from audit_front_normal_command_record_v1 import NormalCommandAuditor
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
G=ClearanceGuard(ROOT,S);producer=FrontNormalNondegradation(G,ROOT,S,enabled=True);consumer=NormalCommandAuditor(G,ROOT,S)
prefix=read(W/'front_normal_prefix_recovery_r3/RESULT.json');assert prefix['passed'];commits={r['step']:r['commit'] for r in prefix['recovery_forks']}
for p,h in prefix['source_sha256'].items():assert sha(p)==h,p
counts=dict(frames=0,applied=0,recoveries=0);episodes=[];negative=[];sources={}
for item in read(W/'front_cross_track_full_stream_probe_r1/CENSUS.json')['episodes']:
 ep=Path(item['episode']);wait=item['wait'];fr={} if wait else {r['step']:r for r in read(ep/'frontal_bypass.json')['rows']};cs={} if wait else {r['step']:r for r in read(ep/'coordination.json')};trs=read(ep/'joint_transport_clearance.json')['rows']
 with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
 saved=[]
 for t,tr in enumerate(trs):
  tc=tr['collector_context'];sc=tc['scene'];scene=None if sc is None else RecontactScene(G,sc['side'],sc['target_xyz'],sc['target_quat'],sc['core_size'],sc['other_xyz'],sc['other_quat'],sc['other_size'])
  kw=dict(step=t,selected=tr['selected'],side=tc['side'],row=fr.get(t),coordinate=cs.get(t),scene=scene,current=q[t],previous_q=None if not t else q[t-1],previous_command=np.zeros(11) if not t else u[t-1],parent_command=u[t],decay=tc['decay'])
  output,record=producer.refine(**kw);assert output is not None and not record['requires_stop']
  if record['requires_recovery']:
   assert ep.name=='layout_840020_push_box_to_bin';record['recovery_committed']=True;record['recovery_transition']=copy.deepcopy(commits[t])
  record=json.loads(json.dumps(record,allow_nan=False));proof=consumer.verify(record,enabled=True,executed_command=output,**kw);assert proof['passed'];saved.append(record)
  counts['frames']+=1;counts['applied']+=record['applied'];counts['recoveries']+=record['requires_recovery']
  if ep.name=='layout_840020_push_box_to_bin' and t in (682,1009):
   for label in (['missing_commit','wrong_hold','wrong_counter','wrong_support'] if t==682 else ['solver_unsuccessful','changed_policy','changed_tolerance','wrong_prediction','false_certificate','stale_previous','nan_output','wrong_direction']):
    bad=copy.deepcopy(record);ex=np.array(output)
    if label=='missing_commit':bad['recovery_committed']=False
    elif label=='wrong_hold':bad['output_command'][0]+=.001;ex[0]+=.001
    elif label=='wrong_counter':bad['recovery_transition']['after']['recontacts']+=1
    elif label=='wrong_support':bad['recovery_request']['observed_support_xyz'][0]+=.001
    elif label=='solver_unsuccessful':bad['proposal']['solver_success']=False
    elif label=='changed_policy':bad['proposal']['planning_policy']='absolute_nonseparation'
    elif label=='changed_tolerance':bad['proposal']['solver_ftol']=1e-6
    elif label=='wrong_prediction':bad['proposal']['predicted_q'][0]+=.001
    elif label=='false_certificate':bad['certificate']['passed']=False
    elif label=='stale_previous':bad['proposal']['previous_command'][0]+=.001
    elif label=='nan_output':bad['output_command'][0]=float('nan')
    else:bad['observation']['requested_direction']*=-1
    try:consumer.verify(bad,enabled=True,executed_command=ex,**kw)
    except (AssertionError,ValueError,KeyError):negative.append(dict(step=t,case=label,rejected=True))
    else:raise AssertionError(('bad command record accepted',t,label))
 with gzip.open(D/(ep.name+'.json.gz'),'wt') as f:json.dump(dict(scope=__doc__,rows=saved,training_ready=False),f,allow_nan=False)
 episodes.append(dict(episode=ep.name,frames=len(saved),applied=sum(r['applied'] for r in saved),recoveries=sum(r['requires_recovery'] for r in saved)))
 for name in ['raw.npz','joint_transport_clearance.json']+([] if wait else ['coordination.json','frontal_bypass.json']):sources[str(ep/name)]=sha(ep/name)
 (D/'STATUS.json').write_text(json.dumps(dict(status='running',episodes=len(episodes),**counts),indent=2));print(json.dumps(episodes[-1]),flush=True)
assert counts==dict(frames=9740,applied=34,recoveries=2) and len(negative)==12
for p in [Path(__file__),W/'audit_front_normal_command_record_v1.py',W/'front_normal_prefix_recovery_r3/RESULT.json',S/'front_normal_nondegradation_runtime_candidate_v1.py',S/'front_normal_nondegradation_solver_candidate_v1.py',S/'audit_front_exact_normal_planning_v1.py',S/'joint_transport_paths.py']:sources[str(p)]=sha(p)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,**counts,episodes=episodes,negative=negative,source_sha256=sources,recursive_raw_stream_verified=False,physics_started=False,training_ready=False)
(D/'RESULT.json').write_text(json.dumps(report,indent=2));(D/'STATUS.json').write_text(json.dumps(dict(status='complete',passed=True,**counts),indent=2));print(json.dumps(dict(passed=True,**counts)),flush=True)
