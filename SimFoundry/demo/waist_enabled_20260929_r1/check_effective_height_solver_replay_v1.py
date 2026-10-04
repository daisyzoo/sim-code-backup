"""Uninstalled actual-solver replay, one fixed converged context per side.
Candidate commands remain unissued; full path/runtime/source audits and physical
comparison are pending. Original objective and optimizer settings are unchanged.
"""
from pathlib import Path
import sys,json,hashlib,datetime,time
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_contact_window_v2';sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from joint_transport_effective_height_solver_v1 import propose
from joint_transport_effective_height_certificate_v1 import verify
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={};rows=[];guard=ClearanceGuard(ROOT,S)
def read(p):sources[str(p)]=sha(p);return json.loads(p.read_text())
for case,task_name,t in [(840023,'nudge_mailer_to_bin',165),(840020,'push_box_to_bin',181)]:
 ep=W/'front_loaded_z_quarter_physical_r2'/f'case_{case}'/f'layout_{case}_{task_name}';r=next(v for v in read(ep/'joint_transport_clearance.json')['rows'] if v['step']==t);c=next(v for v in read(ep/'coordination.json') if v['step']==t);ctx=r['collector_context'];scene=RecontactScene(guard,**ctx['scene']);started=time.perf_counter()
 cmd,p=propose(step=t,side=ctx['side'],scene=scene,parent_command=r['parent_command'],coordinate=c,elbow_reserve_m=.0015,quarter_enabled=True,**{k:ctx[k] for k in ['current','previous_q','previous_command','decay']});elapsed=time.perf_counter()-started
 assert cmd is not None and p['preliminary_passed'] and p['solver_success'];np.testing.assert_array_equal(cmd,r['proposal']['command'])
 permitted={'original_loaded_contact_check','original_contact_primal_preserved','preliminary_passed','effective_loaded_contact_binding'}
 for k,v in r['proposal'].items():
  if k not in permitted:assert p[k]==v,(t,k)
 cert=verify(p,c['task_inputs'],c,guard=guard,elbow_reserve_m=.0015,quarter_enabled=True);assert cert['passed']
 rows.append(dict(episode=ep.name,step=t,elapsed_unprofiled_s=elapsed,original_runtime_applied=r['applied'],candidate_command_equals_original_unissued_proposal=True,original_solver_record_except_contact_checks_exact=True,candidate=p,certificate=cert,physical_command_issued=False));print(json.dumps(dict(step=t,side=ctx['side'],certificate_passed=True,seconds=elapsed)),flush=True)
for p in [Path(__file__),W/'joint_transport_effective_height_solver_v1.py',W/'joint_transport_effective_height_certificate_v1.py',W/'effective_loaded_contact_task_v1.py']:sources[str(p)]=sha(p)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,rows=rows,source_sha256=sources,full_paths_pending=True,runtime_integrated=False,training_ready=False)
with (W/'front_loaded_z_quarter_physical_r2/EFFECTIVE_HEIGHT_SOLVER_REPLAY_V1.json').open('x') as f:json.dump(out,f,indent=2)
