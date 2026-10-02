"""Preserve full diagnostic orchestration and add ten independent pressure audits."""
from pathlib import Path
import ast,json,hashlib,datetime
W=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def rename(s):return s.replace('audit_substep','audit_peak_guard').replace('substep_run_contract','peak_guard_run_contract').replace('staged_substep_observer','staged_peak_load_guard').replace('SUBSTEP_','PEAK_GUARD_')
rows=[]
for a,b in [('substep_run_contract.py','peak_guard_run_contract.py'),('run_substep_groups.py','run_peak_guard_groups.py'),('watch_substep_audits.py','watch_peak_guard_audits.py'),('close_substep_groups.py','close_peak_guard_groups.py')]:
 src=W/a;dst=W/b;assert not dst.exists();base=rename(src.read_text());s=base;changes=[]
 def replace(old,new):
  global s
  assert s.count(old)==1,(a,old);s=s.replace(old,new);changes.append((old,new))
 if a=='substep_run_contract.py':
  replace('def primary(wait):',"REPORTS['audit_peak_guard_pressure.py']=('PEAK_GUARD_PRESSURE_AUDIT.json',('passed',))\ndef primary(wait):")
 if a in ('run_substep_groups.py','close_substep_groups.py'):
  replace("assert prov['args']['trace_substep_contacts'] is True","assert prov['args']['peak_load_bias_guard'] is True and prov['args']['trace_substep_contacts'] is True")
 if a=='run_substep_groups.py':
  line="   (ep/'OBSERVATION_AUDIT_EXECUTION.json').write_text(json.dumps(dict(rows=[observer_row],completed=True,training_ready=False),indent=2))\n"
  replace(line,line+"   frozen();pressure_row=run_audit(ep,'audit_peak_guard_pressure.py');print(json.dumps(pressure_row),flush=True)\n   (ep/'PRESSURE_AUDIT_EXECUTION.json').write_text(json.dumps(dict(rows=[pressure_row],completed=True,training_ready=False),indent=2))\n")
 if a=='close_substep_groups.py':
  replace("assert meta['assist_frames']==0", "assert meta['peak_load_bias_guard'] is True;assert meta['assist_frames']==0")
  replace("  invocations=list(main['rows'])+observer['rows']\n", "  pressure=read(ep,'PRESSURE_AUDIT_EXECUTION.json');assert pressure['completed'] and len(pressure['rows'])==1 and pressure['rows'][0]['script']=='audit_peak_guard_pressure.py'\n  invocations=list(main['rows'])+observer['rows']+pressure['rows']\n")
  replace('observation_invocations=10,actual_sampled_visual_review_complete=True','observation_invocations=10,pressure_invocations=10,actual_sampled_visual_review_complete=True')
 restored=s
 for old,new in reversed(changes):assert restored.count(new)==1;restored=restored.replace(new,old)
 assert restored==base;ast.parse(s);dst.write_text(s)
 rows.append(dict(parent=str(src),parent_sha256=sha(src),new=str(dst),new_sha256=sha(dst),changes=changes,original_flow_preserved_except_explicit_pressure_check=True))
import substep_run_contract as old
import peak_guard_run_contract as new
r=W/'substep_reference03_groups_r1';p=json.loads((r/'PROTOCOL.json').read_text());control=0;primary=0
for c in p['commands']:
 assert new.primary(c['wait'])==[rename(s) for s in old.primary(c['wait'])]
 primary+=len(c['tasks'])*len(new.primary(c['wait']))
 if not c['wait']:
  for task in c['tasks']:
   plan=json.loads((r/f"case_{c['layout_id']}"/f"layout_{c['layout_id']}_{task}"/'frontal_bypass.json').read_text())['plan']
   assert new.controls(plan)==[rename(s) for s in old.controls(plan)];control+=len(new.controls(plan))
assert primary==36 and control==80 and len(new.ADDITIONAL)*8==56
assert new.ADDITIONAL==[rename(s) for s in old.ADDITIONAL]
assert new.REPORTS=={**{rename(k):(rename(v[0]),v[1]) for k,v in old.REPORTS.items()},'audit_peak_guard_pressure.py':('PEAK_GUARD_PRESSURE_AUDIT.json',('passed',))}
for name in new.REPORTS:assert (W/name).exists(),name
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),rows=rows,original_primary=36,original_control=80,original_additional=56,original_observation=10,new_pressure=10,source_sha256={str(p):sha(p) for p in [Path(__file__),*[W/n for n in new.REPORTS],r/'PROTOCOL.json']},physical_validation=False,training_ready=False)
f=W/'PEAK_GUARD_DRIVER_VERSION_CHECK.json';assert not f.exists();f.write_text(json.dumps(out,indent=2));print('PASS original36/80/56/10 preserved; +10 independent pressure audits; no launch')
