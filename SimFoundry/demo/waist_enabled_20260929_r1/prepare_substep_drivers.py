"""Version complete diagnostic orchestration, adding ten independent trace audits."""
from pathlib import Path
import ast,json,hashlib,datetime
W=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def rename(s):return s.replace('audit_box_inward','audit_substep').replace('box_inward_audit_context','substep_audit_context').replace('verify_box_inward_source','verify_substep_source').replace('staged_box_inward_correction','staged_substep_observer').replace('BOX_INWARD_','SUBSTEP_').replace('box_inward_run_contract','substep_run_contract')
rows=[]
for a,b in [('box_inward_run_contract.py','substep_run_contract.py'),('run_box_inward_groups.py','run_substep_groups.py'),('watch_box_inward_audits.py','watch_substep_audits.py'),('close_box_inward_groups.py','close_substep_groups.py')]:
 src=W/a;dst=W/b;assert not dst.exists();base=rename(src.read_text());s=base;changes=[]
 def replace(old,new):
  global s
  assert s.count(old)==1,(a,old);s=s.replace(old,new);changes.append((old,new))
 if a=='box_inward_run_contract.py':
  replace('def primary(wait):',"REPORTS['audit_substep_contacts.py']=('SUBSTEP_CONTACT_AUDIT.json',('passed',))\ndef primary(wait):")
 if a in ('run_box_inward_groups.py','close_box_inward_groups.py'):
  replace("assert prov['args']['rear_box_inward_correction'] is True","assert prov['args']['trace_substep_contacts'] is True and prov['args']['expert_top_tilt_recontact_rad']==.03 and prov['args']['rear_box_inward_correction'] is True")
 if a=='run_box_inward_groups.py':
  line="   (ep/'PRIMARY_AUDIT_EXECUTION.json').write_text(json.dumps(dict(rows=rows,completed=True,training_ready=False),indent=2))\n"
  replace(line,line+"   frozen();observer_row=run_audit(ep,'audit_substep_contacts.py');print(json.dumps(observer_row),flush=True)\n   (ep/'OBSERVATION_AUDIT_EXECUTION.json').write_text(json.dumps(dict(rows=[observer_row],completed=True,training_ready=False),indent=2))\n")
 if a=='close_box_inward_groups.py':
  replace('  invocations=list(main[\'rows\'])\n',"  observer=read(ep,'OBSERVATION_AUDIT_EXECUTION.json');assert observer['completed'] and len(observer['rows'])==1 and observer['rows'][0]['script']=='audit_substep_contacts.py'\n  invocations=list(main['rows'])+observer['rows']\n")
  replace('additional_invocations=56,actual_sampled_visual_review_complete=True','additional_invocations=56,observation_invocations=10,actual_sampled_visual_review_complete=True')
 restored=s
 for old,new in reversed(changes):assert restored.count(new)==1;restored=restored.replace(new,old)
 assert restored==base;ast.parse(s);dst.write_text(s);rows.append(dict(parent=str(src),parent_sha256=sha(src),new=str(dst),new_sha256=sha(dst),changes=changes,original_flow_preserved_except_explicit_observer_check=True))
# Prove all original inventories are preserved under source version renaming.
import box_inward_run_contract as old
import substep_run_contract as new
p=json.loads((W/'box_inward_groups_r1/PROTOCOL.json').read_text());control=0;primary=0
for c in p['commands']:
 assert new.primary(c['wait'])==[rename(s) for s in old.primary(c['wait'])]
 primary+=len(c['tasks'])*len(new.primary(c['wait']))
 if not c['wait']:
  for task in c['tasks']:
   plan=json.loads((W/'box_inward_groups_r1'/f"case_{c['layout_id']}"/f"layout_{c['layout_id']}_{task}"/'frontal_bypass.json').read_text())['plan'];assert new.controls(plan)==[rename(s) for s in old.controls(plan)];control+=len(new.controls(plan))
assert primary==36 and control==80 and len(new.ADDITIONAL)*8==56
assert new.ADDITIONAL==[rename(s) for s in old.ADDITIONAL]
assert new.REPORTS=={**{rename(k):(rename(v[0]),v[1]) for k,v in old.REPORTS.items()},'audit_substep_contacts.py':('SUBSTEP_CONTACT_AUDIT.json',('passed',))}
for name in new.REPORTS:assert (W/name).exists(),name
report=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),rows=rows,original_primary=36,original_control=80,original_additional=56,new_observation=10,source_sha256={str(p):sha(p) for p in [Path(__file__),*[W/n for n in new.REPORTS],W/'box_inward_groups_r1/PROTOCOL.json']},physical_validation=False,training_ready=False)
f=W/'SUBSTEP_DRIVER_VERSION_CHECK.json';assert not f.exists();f.write_text(json.dumps(report,indent=2));print('PASS original36/80/56 preserved; +10 explicit substep audits; no launch')
