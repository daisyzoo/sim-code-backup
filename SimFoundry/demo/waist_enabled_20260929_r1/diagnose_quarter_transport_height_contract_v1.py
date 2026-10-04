"""Independent algebraic diagnosis: quarter-loaded height versus downstream original height.
Triangle inequality: original parent preservation |Jz(u-p)|<=2e-7 and original
request |Jz(u-q)-e_original|<=2e-7 cannot both hold when |Jz(p-q)-e_original|>4e-7.
This proves a contract conflict at saved contexts, not physical improvement or
permission to relax a threshold. No failed run or original auditor is modified.
"""
from pathlib import Path
import sys,json,hashlib,datetime,collections
import numpy as np
W=Path(__file__).resolve().parent;R=W/'front_loaded_z_quarter_physical_r2';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={};rows=[];summary=[]
def read(p):sources[str(p)]=sha(p);return json.loads(p.read_text())
for ep in sorted(R.glob('case_*/layout_*')):
 if not (ep/'joint_transport_clearance.json').exists() or 'wait_no_package' in ep.name:continue
 records=read(ep/'joint_transport_clearance.json')['rows'];coordinates={r['step']:r for r in read(ep/'coordination.json')};count=collections.Counter()
 for r in records:
  c=coordinates.get(r['step']);l=None if c is None else c.get('front_loaded_z_priority');p=r.get('proposal')
  if not c or not l or not l.get('applied') or 'reduced_z_task' not in l or not r['selected']:continue
  reduction=l['reduced_z_task'];task=c['task_inputs'];assert reduction['original_task']==task and reduction['fraction']==.25
  side=r['collector_context']['side'];zr=2 if side=='left' else 5;J=np.asarray(task['jacobian']);q=np.asarray(task['current']);parent=np.asarray(r['parent_command']);assert np.array_equal(parent,l['output_command']);modified=reduction['modified_task']
  expected=json.loads(json.dumps(task));expected['error'][zr]=reduction['modified_requested_z_m'];assert modified==expected
  achieved=float(J[zr]@(np.asarray(l['context']['parent_command'])-q));wanted=achieved+.25*(task['error'][zr]-achieved);assert abs(wanted-modified['error'][zr])<1e-15
  mismatch=float(J[zr]@(parent-q)-task['error'][zr]);effective_error=float(J[zr]@(parent-q)-modified['error'][zr]);conflict=abs(mismatch)>4e-7
  assert abs(effective_error)<=2e-7
  count['selected_quarter_loaded']+=1;count['contradictory_height_requirements']+=int(conflict);count['proposal_attempts']+=int(p is not None);count['runtime_applied']+=int(r['applied'])
  entry=dict(episode=ep.name,step=r['step'],side=side,downstream_reason=r['reason'],original_request_m=task['error'][zr],effective_request_m=modified['error'][zr],parent_vs_original_request_m=mismatch,parent_vs_effective_request_m=effective_error,original_two_tolerances_sum_m=4e-7,conflict_proven=conflict,proposal_present=p is not None)
  if p:
   u=np.asarray(p['command']);parent_height=float(J[zr]@(u-parent));original_residual=float(J[zr]@(u-q)-task['error'][zr]);effective_residual=float(J[zr]@(u-q)-modified['error'][zr]);check=p['original_loaded_contact_check'];assert abs(original_residual-check['z_error_mm']/1000)<1e-15
   count['iteration_limit_reached']+=int(p['solver_status']==9);count['loaded_primal_rejected']+=int(not p['original_contact_primal_preserved']);entry.update(solver_status=p['solver_status'],iterations=p['iterations'],parent_height_preservation_error_m=parent_height,proposal_vs_original_request_m=original_residual,proposal_vs_effective_request_m=effective_residual,original_primal_passed=p['original_contact_primal_preserved'])
  rows.append(entry)
 summary.append(dict(episode=ep.name,counts=dict(count)))
assert len(summary)==8 and rows
for p in [Path(__file__),W/'staged_front_contact_window_v2/front_loaded_z_fraction.py',W/'staged_front_contact_window_v2/joint_transport_solver.py',W/'staged_front_contact_window_v2/joint_transport_certificate.py',W/'staged_front_contact_window_v2/joint_transport_paths.py']:sources[str(p)]=sha(p)
totals=collections.Counter()
for s in summary:totals.update(s['counts'])
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,all_eight_push_conditions_scanned=True,summary=summary,totals=dict(totals),rows=rows,source_sha256=sources,existing_support_cache_already_integrated=True,prospective_fix='Bind downstream loaded-contact height to the independently verified effective quarter task; keep the original full task objective, original2e-7 height tolerance, all normal/path/contact/quality gates. Independently audit propagation before new physics.',runtime_changed=False,failed_audits_changed=False,physical_benefit_proven=False,training_ready=False)
with (R/'QUARTER_TRANSPORT_HEIGHT_CONTRACT_DIAGNOSIS_V1.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(summary=summary,totals=dict(totals)),indent=2))
