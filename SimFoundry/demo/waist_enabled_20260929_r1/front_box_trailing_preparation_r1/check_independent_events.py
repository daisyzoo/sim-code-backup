"""Independent event audit of all three moving-runtime hypothetical streams.
Actual episode source was used only for starts. These new commands and moving
object poses are synthetic, not a recorded physical experiment.
"""
from pathlib import Path
import sys,json,hashlib,datetime,copy
import numpy as np
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];S=W/'staged_front_box_trailing_v1';sys.path[:0]=[str(D),str(S),str(W),str(ROOT)]
from audit_trailing_events import RecoveryEventAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();src=W/'front_box_trailing_runtime_preparation_r2/MOVING_RUNTIME_CHECK.json';data=json.loads(src.read_text());assert data['complete']
for p,h in data['source_sha256'].items():assert sha(p)==h,p
prep=json.loads((D/'EVENT_AUDITOR_PREPARATION.json').read_text())
for k in ['parent','candidate']:assert sha(prep[k])==prep[k+'_sha256']
rows=[]
for case in data['rows']:
 audit=RecoveryEventAudit(ROOT,S);neg=[];records=[]
 for ix,t in enumerate(case['trace']):
  event=t['event'];c=event['context'];kw={k:c[k] for k in ['step','current','previous_q','previous_command','scene','decay','selected','parent_mode','recontacts','guard_stop','observed_load_n','filtered_load_n']};kw['final_command']=event['command']
  if ix==0:
   for label in ['planning_reserve','planning_offset','command','readiness','observed_offset']:
    bad=copy.deepcopy(event)
    if label=='planning_reserve':bad['planning']['planning_xy_reserve_m']=0.
    if label=='planning_offset':bad['planning']['landing_preference_local_xy']=[0.,0.]
    if label=='command':bad['command'][0]+=.001
    if label=='readiness':bad['measured_ready_count']=3
    if label=='observed_offset':bad['landing_preference_local_xy']=[0.,0.]
    try:copy.deepcopy(audit).verify(bad,**kw)
    except AssertionError:neg.append(label)
    else:raise AssertionError('Tamper accepted:'+label)
  if event['kind']=='handover':
   for label in ['capture_vertex','capture_xy','capture_world','stale_rotation']:
    bad=copy.deepcopy(event)
    if label=='capture_vertex':bad['captured_center_local'][0]+=.001
    if label=='capture_xy':bad['selected_surface_local_xy'][0]+=.001
    if label=='capture_world':bad['observed_support_xyz'][0]+=.001
    if label=='stale_rotation':bad['landing_preference_local_xy']=case['trace'][0]['event']['planning']['landing_preference_local_xy']
    try:copy.deepcopy(audit).verify(bad,**kw)
    except AssertionError:neg.append(label)
    else:raise AssertionError('Capture tamper accepted:'+label)
  records.append(audit.verify(event,**kw))
 assert records[-1]['kind']=='handover';r=dict(start_step=case['start_step'],checked_events=len(records),negative_rejections=neg,handover=True,records=records);rows.append(r);print(json.dumps({k:v for k,v in r.items() if k!='records'}),flush=True)
sources={str(p):sha(p) for p in [Path(__file__),D/'EVENT_AUDITOR_PREPARATION.json',src,S/'COLLECTOR_PREPARATION.json',S/'elbow_torso_hulls.json',ROOT/'assets/robots/g1_hand_support_vertices.json',ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf']}
for mod in list(sys.modules.values()):
 f=getattr(mod,'__file__',None)
 if f:
  p=Path(f).resolve()
  if p.is_file() and p.suffix=='.py' and p.is_relative_to(ROOT):sources[str(p)]=sha(p)
for name in ['trailing_plan','trailing_static','trailing_selection','trailing_lifecycle','trailing_runtime','trailing_adapter']:assert name not in sys.modules
with (D/'INDEPENDENT_EVENT_CHECK.json').open('x') as f:json.dump(dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,streams=len(rows),checked_events=sum(r['checked_events'] for r in rows),negative_rejections=sum(len(r['negative_rejections']) for r in rows),rows=rows,source_sha256=sources,candidate_control_imports=False,physical_started=False,training_ready=False),f,indent=2)
print('COMPLETE3',flush=True)
