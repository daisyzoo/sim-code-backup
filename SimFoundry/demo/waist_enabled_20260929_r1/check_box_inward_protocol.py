"""All six actual CLIs, unchanged inventory/driver flow, no physical launch."""
from pathlib import Path
import ast,json,sys,subprocess,hashlib,os
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(w),str(repo)];stage=w/'staged_box_inward_correction';parent=w/'box_entry_lift_groups_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
from prepare_box_inward_groups import commands,run
import box_entry_run_contract as old
import box_inward_run_contract as new
mapping=json.loads((w/'BOX_INWARD_AUDIT_VERSION_MAP.json').read_text())
def rename(s):
 for a,b in sorted(mapping.items(),key=lambda x:-len(x[0])):s=s.replace(a,b)
 return s.replace('BOX_ENTRY_','BOX_INWARD_')
p,items=commands();assert len(items)==6 and sum(len(c['tasks']) for c in items if not c['wait'])==8 and sum(len(c['tasks']) for c in items if c['wait'])==2
control=[]
for c in items:
 for task in c['tasks']:
  if c['wait']:continue
  plan=json.loads((parent/f"case_{c['layout_id']}"/f"layout_{c['layout_id']}_{task}"/'frontal_bypass.json').read_text())['plan'];expected=[rename(n) for n in old.controls(plan)];assert new.controls(plan)==expected;control+=expected
assert len(control)==80 and len(new.ADDITIONAL)*8==56
assert new.ADDITIONAL==[rename(n) for n in old.ADDITIONAL]
for wait in [True,False]:assert new.primary(wait)==[rename(n) for n in old.primary(wait)]
assert new.REPORTS=={rename(k):(rename(v[0]),v[1]) for k,v in old.REPORTS.items()}
drivers={'box_entry_run_contract.py':'box_inward_run_contract.py','run_box_entry_groups.py':'run_box_inward_groups.py','watch_box_entry_audits.py':'watch_box_inward_audits.py','close_box_entry_groups.py':'close_box_inward_groups.py'}
for a,b in drivers.items():
 s=rename((w/a).read_text())
 if a in ['run_box_entry_groups.py','close_box_entry_groups.py']:
  s=s.replace("assert prov['args']['rear_box_entry_lift'] is True","assert prov['args']['rear_box_inward_correction'] is True and prov['args']['rear_box_entry_lift'] is True").replace("assert meta['rear_box_entry_lift'] is True","assert meta['rear_box_inward_correction'] is True and meta['rear_box_entry_lift'] is True")
 assert ast.dump(ast.parse(s))==ast.dump(ast.parse((w/b).read_text())),b
for script in set(control)|set(new.ADDITIONAL)|set(new.primary(True))|set(new.primary(False)):assert (w/script).is_file()
pre=json.loads((stage/'PRELAUNCH_CHECK.json').read_text());assert pre['passed'] and len(pre['rows'])==13
for path,h in pre['source_sha256'].items():assert sha(path)==h
cli=[x for x in pre['rows'] if x['invalid'] is None];negative=[x for x in pre['rows'] if x['invalid'] is not None]
sources=[Path(__file__),w/'prepare_box_inward_groups.py',parent/'PROTOCOL.json',parent/'RESULT.json',stage/'collect_paired_sorting.py',w/'BOX_INWARD_AUDIT_VERSION_MAP.json',w/'audit_box_inward_source_contract.py',w/'verify_top_pressure_setting.py',stage/'PRELAUNCH_CHECK.json',*[w/n for n in drivers],*[w/n for n in drivers.values()],*[w/n for n in new.REPORTS]]
(stage/'RUN_PROTOCOL_CHECK.json').write_text(json.dumps(dict(passed=True,commands=items,actual_prelaunch_commands=cli,negative_cli_rejected=negative,original_control_count=80,additional_count=56,complete_condition_count=10,driver_control_flow_unchanged=True,box_entry_predecessor_must_be_closed_before_prepare=True,source_sha256={str(q):sha(q) for q in sources},physical_validation=False,training_ready=False),indent=2));print('PASS6CLI+7negative same8push2wait80+56 no launch')
