"""Matched parent-margin baseline for first two complete hard groups.
Original controller, source/quality/profile/storage gates unchanged. Only layout
scheduling differs from closed margin comparison; candidate not activated.
"""
from pathlib import Path
import json,hashlib,datetime,ast
W=Path(__file__).resolve().parent;ROOT=W.parents[1];P=W/'front_initial_margin_baseline_preparation_r1';S=W/'staged_terminal_release_margin';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert not P.exists();(P/'layouts').mkdir(parents=True)
parent=W/'terminal_margin_physical_preparation_r1/PLAN.json';old=json.loads(parent.read_text());coverage=json.loads((W/'FRONT_INITIAL_CENTER_COMPLETE_GROUP_COVERAGE_PLAN.json').read_text());groups=[];commands=[]
for group in coverage['groups'][:2]:
 name=group['group'];source=W/'fresh_pilot_layout_proposal_r1'/f'{name}.json';proposal=json.loads(source.read_text());contract=Path(group['conditions'][0]['original_contract_path']);assert sha(contract)==group['conditions'][0]['original_contract_sha256'];c=json.loads(contract.read_text());assert c['layouts']==proposal['layouts'] and c['wait_layouts']==proposal['wait_layouts']
 groups.append(dict(group=name,source=str(source),sha256=sha(source),contract=str(contract),contract_sha256=sha(contract),purpose='Complete difficult pair; matched existing margin baseline before candidate comparison'))
 for condition,layout in zip(group['conditions'],proposal['layouts']+proposal['wait_layouts']):
  assert condition['layout_id']==layout['layout_id'];template=old['commands'][2 if condition['wait'] else 0];args=list(template['args']);identity='--wait-layout-start' if condition['wait'] else '--layout-start';args[args.index(identity)+1]=str(layout['layout_id']);args[args.index('--out-dir')+1]=str(P/f"case_{layout['layout_id']}");h=None
  if not condition['wait']:
   dest=P/'layouts'/f"{layout['layout_id']}.json";dest.write_text(json.dumps(layout,indent=2));args[args.index('--diagnostic-layout-json')+1]=str(dest);h=sha(dest)
  commands.append(dict(group=name,layout_id=layout['layout_id'],wait=condition['wait'],tasks=condition['tasks'],args=args,layout_sha256=h))
plan=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='prepared_not_launched',collector=str(S/'collect_paired_sorting.py'),collector_sha256=sha(S/'collect_paired_sorting.py'),groups=groups,commands=commands,parent_template=str(parent),parent_template_sha256=sha(parent),coverage_plan_sha256=sha(W/'FRONT_INITIAL_CENTER_COMPLETE_GROUP_COVERAGE_PLAN.json'),scope=__doc__,simulation_started=False,training_ready=False)
(P/'PLAN.json').write_text(json.dumps(plan,indent=2))
source=W/'run_terminal_margin_physical.py';s=source.read_text();s=s.replace("P=W/'terminal_margin_physical_preparation_r1'","P=W/'front_initial_margin_baseline_preparation_r1'").replace("PREVIOUS=W/'joint_edge_intersection_physical_r1'","PREVIOUS=W/'terminal_margin_physical_r1'")
start=s.index(" parent_plan=W/'joint_edge_intersection_physical_preparation_r1/PLAN.json'");end=s.index(" prep=json.loads((S/'PREPARATION.json').read_text())",start)
s=s[:start]+''' parent_plan=Path(plan['parent_template']);assert sha(parent_plan)==plan['parent_template_sha256'];old=json.loads(parent_plan.read_text())
 assert sha(W/'FRONT_INITIAL_CENTER_COMPLETE_GROUP_COVERAGE_PLAN.json')==plan['coverage_plan_sha256']
 assert len(plan['commands'])==6 and sum(len(c['tasks']) for c in plan['commands'])==10
 assert [g['group'] for g in plan['groups']]==['fresh_reverse_diagonal_11','fresh_diagonal_10']
 from prepare_closed_peak_trial import parser_namespace
 from simfoundry.data.waist_pilot_protocol import semantic_settings
 for group in plan['groups']:
  assert sha(group['source'])==group['sha256'] and sha(group['contract'])==group['contract_sha256']
  proposal=json.loads(Path(group['source']).read_text());members=[c for c in plan['commands'] if c['group']==group['group']]
  assert [c['layout_id'] for c in members]==[r['layout_id'] for r in proposal['layouts']+proposal['wait_layouts']]
  assert [c['tasks'] for c in members]==[['push_box_to_bin','nudge_mailer_to_bin'],['push_box_to_bin','nudge_mailer_to_bin'],['wait_no_package']]
  for current,layout in zip(members,proposal['layouts']+proposal['wait_layouts']):
   args=current['args'];template=old['commands'][2 if current['wait'] else 0];expected=list(template['args']);key='--wait-layout-start' if current['wait'] else '--layout-start'
   for flag in [key,'--out-dir']+([] if current['wait'] else ['--diagnostic-layout-json']):expected[expected.index(flag)+1]=args[args.index(flag)+1]
   assert args==expected and args[args.index(key)+1]==str(current['layout_id'])
   if not current['wait']:
    path=Path(args[args.index('--diagnostic-layout-json')+1]);assert sha(path)==current['layout_sha256'] and json.loads(path.read_text())==layout
   resolved,_=parser_namespace(S/'collect_paired_sorting.py',args,full=True)
   settings=semantic_settings(resolved);assert settings.pop('terminal_release_margin') is True and settings.pop('edge_clearance_intersection') is True
   assert settings==json.loads((W/'staged_closed_peak_trial/TRIAL_PROFILE.json').read_text())['resolved_settings']
''' + s[end:]
start=s.index(" try:verify_trial_provenance(PREVIOUS/'case_840004')");end=s.index(' from simfoundry.data.waist_pilot_protocol import semantic_settings',start)
s=s[:start]+" verify_trial_provenance(PREVIOUS/'case_840004')\n"+s[end:]
s=s.replace("*W.glob('*.py')","*[p for p in W.glob('*.py') if 'front_initial' not in p.name]")
s=s.replace("P/'PLAN.json',BASE/'RESULT.json'","Path(__file__),W/'watch_front_initial_margin_baseline.py',P/'PLAN.json',BASE/'RESULT.json'")
s=s.replace('watch_terminal_margin_physical_audits.py','watch_front_initial_margin_baseline.py').replace("default=str(W/'terminal_margin_physical_r1')","default=str(W/'front_initial_margin_baseline_r1')")
s=s.replace('"""Isolated full paired physics for existing terminal-release margins.','"""Matched margin baseline on complete reverse11/diagonal10 hard pairs.')
p=W/'run_front_initial_margin_baseline.py';assert not p.exists();ast.parse(s);p.write_text(s)
watch=(W/'watch_terminal_margin_physical_audits.py').read_text().replace("'run_terminal_margin_physical.py'","'run_front_initial_margin_baseline.py'");p=W/'watch_front_initial_margin_baseline.py';assert not p.exists();ast.parse(watch);p.write_text(watch)
print('Prepared baseline 8 push + 2 wait on complete reverse11/diagonal10; original margin controller unchanged.')
