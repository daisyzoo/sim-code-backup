"""Diagnostic certificate of saved unissued proposals with effective quarter height.
Every sampled outcome is retained; no proposal is issued or admitted. Full path
and new runtime integration remain required even for a passing certificate.
"""
from pathlib import Path
import sys,json,hashlib,datetime
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_contact_window_v2';sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from joint_transport_effective_height_certificate_v1 import verify
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={};rows=[];guard=ClearanceGuard(ROOT,S)
def read(p):sources[str(p)]=sha(p);return json.loads(p.read_text())
# Fixed selection established before outcomes: first three and last three
# converged affected proposals per side plus first iteration-limit example.
for case,task_name in [(840023,'nudge_mailer_to_bin'),(840020,'push_box_to_bin')]:
 ep=W/'front_loaded_z_quarter_physical_r2'/f'case_{case}'/f'layout_{case}_{task_name}';records=read(ep/'joint_transport_clearance.json')['rows'];coords={x['step']:x for x in read(ep/'coordination.json')}
 affected=[r for r in records if r.get('proposal') and coords[r['step']].get('front_loaded_z_priority',{}).get('applied') and 'reduced_z_task' in coords[r['step']]['front_loaded_z_priority']]
 converged=[r for r in affected if r['proposal']['solver_success']];limited=[r for r in affected if r['proposal']['solver_status']==9];selected=converged[:3]+converged[-3:]+limited[:1];assert len({r['step'] for r in selected})==len(selected)==7
 for r in selected:
  c=coords[r['step']];result=verify(r['proposal'],c['task_inputs'],c,guard=guard,elbow_reserve_m=.0015,quarter_enabled=True)
  row=dict(episode=ep.name,step=r['step'],original_solver_success=r['proposal']['solver_success'],original_solver_status=r['proposal']['solver_status'],certificate=result,original_applied=r['applied'],physical_command_issued=False)
  rows.append(row);print(json.dumps(dict(episode=ep.name,step=r['step'],certificate_passed=result['passed'],checks=result.get('checks'),reason=result.get('reason'))),flush=True)
for p in [Path(__file__),W/'effective_loaded_contact_task_v1.py',W/'joint_transport_effective_height_certificate_v1.py']:sources[str(p)]=sha(p)
for m in list(sys.modules.values()):
 f=getattr(m,'__file__',None)
 if f:
  p=Path(f).resolve()
  if p.is_file() and p.suffix=='.py' and p.is_relative_to(ROOT):sources[str(p)]=sha(p)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,contexts=len(rows),certificates_passed=sum(r['certificate']['passed'] for r in rows),rows=rows,source_sha256=sources,full_paths_pending=True,runtime_integrated=False,training_ready=False)
with (W/'front_loaded_z_quarter_physical_r2/EFFECTIVE_HEIGHT_SAVED_PROPOSALS_V1.json').open('x') as f:json.dump(out,f,indent=2)
