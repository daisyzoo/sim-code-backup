"""Offline proposed retry selection over67archived successful edge solves.
Only numerical/audit selection is evaluated; command histories remain original.
No production solver or physical trajectory is changed.
"""
from pathlib import Path
import datetime,hashlib,json
import numpy as np
W=Path(__file__).resolve().parent;D=W/'rear_early_bag_retry_selection_r1';D.mkdir(exist_ok=False);read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
d=read(W/'rear_early_bag_stationarity_r1/RESULT.json');p=read(W/'rear_early_bag_stationarity_probe_r2/RESULT.json');assert p['reproduction']['command_exact']
for report in [d,p]:
 for path,h in report['source_sha256'].items():assert sha(path)==h,path
candidate=next(r for r in p['rows'] if r['case']=='analytic_parent');assert candidate['solver_status']==0 and candidate['independent_certificate']['stationarity_residual']<=1e-6 and candidate['final_guard']['accepted']
ep=W/'rear_early_edge_physical_r1/case_840020/layout_840020_nudge_mailer_to_bin';cs={c['step']:c for c in read(ep/'coordination.json')}
with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
rows=[]
for r in d['rows']:
 t=r['step'];old=cs[t]['joint_edge_refinement'];off=np.asarray(old['final_upper_command']);selected=off if r['passed'] else np.asarray(candidate['command']);assert not r['passed'] or np.array_equal(selected,off)
 if not r['passed']:
  assert t==655 and np.array_equal(off,u[t]);assert not cs[t]['joint_edge_clearance_intersection']['changed'] and not cs[t]['front_loaded_z_priority']['applied'] and not cs[t]['joint_transport_clearance']['applied']
  g=candidate['final_guard'];assert np.array_equal(g['current'],q[t]) and np.array_equal(g['previous'],u[t-1]) and np.array_equal(g['command'],selected)
 rows.append(dict(step=t,original_passed=r['passed'],retry_selected=not r['passed'],defaultoff_identical=True,change_rad=float(np.max(abs(selected-off))),stationarity_after=r['stationarity'] if r['passed'] else candidate['independent_certificate']['stationarity_residual']))
assert sum(r['retry_selected'] for r in rows)==1 and len(rows)==67
# A certified point with SLSQP status8 is deliberately ineligible.
failed_solver=next(r for r in p['rows'] if r['case']=='analytic_original_output');assert failed_solver['solver_status']==8 and failed_solver['independent_certificate'];assert not (failed_solver['solver_status']==0 and failed_solver['independent_certificate']['stationarity_residual']<=1e-6)
quality=read(ep/'quality.json');assert quality['passed'] and quality['training_ready'] is False
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,rows=rows,selected_retries=1,unchanged_commands=66,status8_rejected_despite_certificate=True,actual_original_quality=dict(passed=quality['passed'],target_final_progress_m=quality['metrics']['target_final_progress_m'],non_target_max_xy_m=quality['metrics']['box_max_xy_m'],training_ready=False),source_sha256={str(f):sha(f) for f in [Path(__file__),W/'rear_early_bag_stationarity_r1/RESULT.json',W/'rear_early_bag_stationarity_probe_r2/RESULT.json',ep/'quality.json',ep/'raw.npz',ep/'coordination.json']},installed=False,physics_started=False,training_ready=False)
(D/'RESULT.json').write_text(json.dumps(out,indent=2));print(json.dumps(dict(passed=True,checked=67,changed=1,status8_rejected=True,training_ready=False)))
