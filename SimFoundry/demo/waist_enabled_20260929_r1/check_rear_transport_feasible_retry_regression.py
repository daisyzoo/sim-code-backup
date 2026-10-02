"""Fixed first/middle/last original successes per side and endpoint role.
Original status9 boundary is tested separately. No new physics or data admission.
"""
from pathlib import Path
import sys,json,hashlib,datetime,os,collections,copy
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_rear_recovery_tracking';sys.path[:0]=[str(W),str(S),str(ROOT)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from rear_transport_feasible_retry_candidate import witness
from rear_recontact_transport_witness import witness as parent_witness
from audit_rear_transport_witness import EventAudit,verify_witness
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();history_path=W/'REAR_TRANSPORT_LIFECYCLE_CHECK.json';history=json.loads(history_path.read_text());assert history['status']=='complete';groups=collections.defaultdict(list)
for item in history['rows']:
 measured=item['case']=='actual_measured_handover';rec=item['measured_witness'] if measured else item['planning_witness']
 if rec and rec['accepted']:groups[('right' if 'push_box' in item['episode'] else 'left',measured)].append(item)
selected=[]
for key,items in sorted(groups.items()):
 for i in sorted(set([0,len(items)//2,len(items)-1])):selected.append((key,items[i]))
assert len(groups)==4 and len(selected)==12
guard=ClearanceGuard(ROOT,S);audit=EventAudit(ROOT,S);dest=W/'REAR_TRANSPORT_FEASIBLE_RETRY_REGRESSION.json';assert not dest.exists();rows=[];sources={str(history_path):sha(history_path)};frozen={str(p):sha(p) for p in [Path(__file__),W/'rear_transport_feasible_retry_candidate.py',W/'rear_recontact_transport_witness.py',W/'audit_rear_transport_witness.py',S/'recontact_scene.py',S/'clearance_runtime.py']}
def save(status,**kw):
 p=dest.with_suffix('.tmp');p.write_text(json.dumps(dict(status=status,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,selected_requests=[dict(side=k[0],measured=k[1],episode=x['episode'],step=x['step']) for k,x in selected],rows=rows,source_sha256=sources,frozen_sha256=frozen,simulation_started=False,training_ready=False,**kw),indent=2));p.replace(dest)
try:
 save('running')
 for (side,measured),item in selected:
  path=W/item['episode']/'recontact_pose.json';sources[str(path)]=sha(path);event=next(x for x in json.loads(path.read_text())['rows'] if x['step']==item['step']);ctx=event['context'];r=ctx['scene'];q=np.asarray(ctx['current'] if measured else event['planning']['endpoint']);scene=RecontactScene(guard,r['side'],r['target_xyz'],r['target_quat'],r['core_size'],r['other_xyz'],r['other_quat'],r['other_size']);before=parent_witness(scene,q);off=witness(scene,q);assert off==before
  new=witness(scene,q,retry_feasible=True);metadata=new['feasible_endpoint_retry'];projection={k:v for k,v in new.items() if k!='feasible_endpoint_retry'};assert before['accepted'] and not metadata['attempted'] and projection==before;proof=verify_witness(audit,new,endpoint=q,scene=r)
  rows.append(dict(episode=item['episode'],step=item['step'],side=side,measured=measured,default_off_identical=True,enabled_original_success_identical=True,independent_proof=proof));save('running');print(side,measured,item['step'],'verified',flush=True)
 for p,h in {**sources,**frozen}.items():assert sha(p)==h,p
 save('complete',passed=True,requests=len(rows))
except BaseException as e:save('check_failed',passed=False,error=repr(e));raise
