"""Actual pre-AppLauncher parser checks for CLI-only1mm variant; no simulator.
Original2mm semantics must remain identical. Alternate values and missing
original prerequisite flags remain rejected by existing parser/profile guards.
"""
from pathlib import Path
import sys,json,hashlib,datetime,contextlib,io
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_drive_1mm';OLD=W/'staged_front_corridor_midpoint_integrated';P=W/'front_drive_1mm_preparation_r2';sys.path[:0]=[str(W),str(ROOT)]
from prepare_closed_peak_trial import parser_namespace
from simfoundry.data.waist_pilot_protocol import semantic_settings
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();plan=json.loads((P/'PLAN.json').read_text());profile=json.loads((P/'TRIAL_PROFILE.json').read_text());prep=json.loads((S/'COLLECTOR_PREPARATION.json').read_text());old=json.loads((OLD/'COLLECTOR_PREPARATION.json').read_text());positive=[];negative=[]
assert len(prep['stage_sha256'])==71 and set(prep['stage_sha256'])==set(old['stage_sha256'])
for n,h in prep['stage_sha256'].items():assert sha(S/n)==h
assert [n for n,h in prep['stage_sha256'].items() if h!=old['stage_sha256'][n]]==['collect_paired_sorting.py']
s=(S/'collect_paired_sorting.py').read_text()
for e in reversed(prep['edits']):assert s.count(e['new'])==1;s=s.replace(e['new'],e['old'])
assert s==(OLD/'collect_paired_sorting.py').read_text()
for c in plan['commands']:
 a=c['args'];one,_=parser_namespace(S/'collect_paired_sorting.py',a,full=True);st=semantic_settings(one)
 for k in ['front_corridor_midpoint_replan','front_loaded_z_priority','front_initial_center_landing','terminal_release_margin','edge_clearance_intersection']:assert st.pop(k) is True
 assert st==profile['prelaunch_settings'];two=list(a);two[two.index('--front-cop-drive-step-m')+1]='.002';new2,_=parser_namespace(S/'collect_paired_sorting.py',two,full=True);old2,_=parser_namespace(OLD/'collect_paired_sorting.py',two,full=True);assert new2==old2;positive.append(c['layout_id'])
a=plan['commands'][0]['args'];cases=[]
for val in ['.0005','.0015','.0025','nan']:
 bad=list(a);bad[bad.index('--front-cop-drive-step-m')+1]=val;cases.append(('unsupported_step_'+val,bad))
for flag in ['--front-cop-phase-anchor','--front-cop-route-axis','--front-cop-slip-following','--self-clearance-task-ik','--front-loaded-z-priority']:
 bad=list(a);bad.remove(flag);cases.append(('missing_'+flag,bad))
for label,bad in cases:
 try:
  with contextlib.redirect_stderr(io.StringIO()):parser_namespace(S/'collect_paired_sorting.py',bad,full=True)
 except (AssertionError,ValueError,SystemExit):negative.append(label)
 else:raise AssertionError(('accepted',label))
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,configuration_layouts=positive,original2mm_parser_semantics_identical=True,stage_files=71,unchanged_runtime_helper_files=70,exact_cli_only_reverse_restore=True,negative=negative,source_sha256={str(p):sha(p) for p in [Path(__file__),S/'COLLECTOR_PREPARATION.json',S/'collect_paired_sorting.py',OLD/'collect_paired_sorting.py',P/'PLAN.json',P/'TRIAL_PROFILE.json']},physics_started=False,training_ready=False)
with (S/'CLI_PARAMETER_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps({k:v for k,v in out.items() if k not in ['scope','source_sha256']},indent=2))
