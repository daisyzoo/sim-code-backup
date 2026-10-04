"""Complete uninstalled runtime and original continuous-path checks,2fixed contexts.
Both default-off identity and enabled proposal are checked; no physical command.
"""
from pathlib import Path
import sys,json,hashlib,datetime,time
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_contact_window_v2';sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from joint_transport_effective_height_runtime_v1 import JointTransportRuntime
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={};rows=[];guard=ClearanceGuard(ROOT,S)
def read(p):sources[str(p)]=sha(p);return json.loads(p.read_text())
for case,task_name,t in [(840023,'nudge_mailer_to_bin',165),(840020,'push_box_to_bin',181)]:
 ep=W/'front_loaded_z_quarter_physical_r2'/f'case_{case}'/f'layout_{case}_{task_name}';r=next(v for v in read(ep/'joint_transport_clearance.json')['rows'] if v['step']==t);c=next(v for v in read(ep/'coordination.json') if v['step']==t);front=next(v for v in read(ep/'frontal_bypass.json')['rows'] if v['step']==t);ctx=r['collector_context'];scene=RecontactScene(guard,**ctx['scene']);args=dict(step=t,selected=r['selected'],side=ctx['side'],row=front,coordinate=c,scene=scene,parent_command=r['parent_command'],**{k:ctx[k] for k in ['current','previous_q','previous_command','decay']})
 off=JointTransportRuntime(guard,ROOT,S,enabled=True);oc,orr=off.refine(**args);np.testing.assert_array_equal(oc,r['output_command']);assert orr=={k:v for k,v in r.items() if k!='collector_context'}
 on=JointTransportRuntime(guard,ROOT,S,enabled=True,effective_quarter_height=True);start=time.perf_counter();cmd,result=on.refine(**args);elapsed=time.perf_counter()-start
 row=dict(episode=ep.name,step=t,default_off_entire_record_exact=True,enabled_elapsed_s=elapsed,enabled_applied=result['applied'],reason=result['reason'],enabled_result=result,physical_command_issued=False);rows.append(row)
 print(json.dumps(dict(step=t,side=ctx['side'],applied=result['applied'],reason=result['reason'],seconds=elapsed)),flush=True)
for p in [Path(__file__),W/'joint_transport_effective_height_runtime_v1.py',W/'joint_transport_effective_height_solver_v1.py',W/'joint_transport_effective_height_certificate_v1.py',W/'effective_loaded_contact_task_v1.py']:sources[str(p)]=sha(p)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,contexts=len(rows),default_off_identity_passed=True,enabled_applied_count=sum(r['enabled_applied'] for r in rows),rows=rows,source_sha256=sources,collector_integrated=False,full_stream_audit_integration_pending=True,new_physics=False,training_ready=False)
with (W/'front_loaded_z_quarter_physical_r2/EFFECTIVE_HEIGHT_RUNTIME_CHECK_V1.json').open('x') as f:json.dump(out,f,indent=2)
