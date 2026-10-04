"""Original6command parser and actual snapshot hash binding, no physical data.
Local fixtures contain copied sources/provenance only, explicitly diagnostic.
"""
from pathlib import Path
import copy,datetime,hashlib,json,shutil,sys
W=Path(__file__).resolve().parent;ROOT=W.parents[1];D=W/'front_normal_source_binding_checks_r4';D.mkdir(exist_ok=False);sys.path[:0]=[str(W),str(ROOT)]
import front_normal_stage_source_binding_v2 as binding
from prepare_closed_peak_trial import parser_namespace
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
used,bound=binding.verify_preparation();assert len(used)==101
# Copies have distinct inodes and never masquerade as collected episodes.
case=D/'diagnostic_source_fixture';case.mkdir();old=W/'staged_front_effective_height_v1';stage=binding.S
base=read(W/'front_effective_height_physical_r1/case_840020/provenance.json');source={}
oldprefix=str(old.relative_to(ROOT))+'/';newprefix=str(stage.relative_to(ROOT))+'/'
for name,h in base['source_sha256'].items():
 newname=newprefix+Path(name).name if name.startswith(oldprefix) else name
 source[newname]=sha(ROOT/newname)
for name in binding.NORMAL_HELPERS:source[newprefix+name]=sha(stage/name)
for name,h in source.items():
 dest=case/'source_snapshot'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,dest);assert sha(dest)==h and dest.stat().st_ino!=(ROOT/name).stat().st_ino
rows=[];protocol=read(W/'front_effective_height_physical_r1/PROTOCOL.json')
for cmd in protocol['plan']['commands']:
 for enabled in [False,True]:
  before=list(sys.path)
  try:args=parser_namespace(stage/'collect_paired_sorting.py',cmd['args']+(['--front-normal-nondegradation'] if enabled else []),full=True)[0]
  finally:sys.path[:]=before
  raw_parent,_=parser_namespace(old/'collect_paired_sorting.py',cmd['args'],full=True)
  declared=args.pop('front_normal_nondegradation');assert declared is enabled and args==raw_parent
  # AppLauncher resolves/removes launch-only fields. Reuse the actual archived
  # resolved namespace for this exact original command; change only our flag.
  args=read(W/f"front_effective_height_physical_r1/case_{cmd['layout_id']}/provenance.json")['args']
  args['front_normal_nondegradation']=enabled
  binding.verify_settings(args);prov=copy.deepcopy(base);prov['args']=args;prov['source_sha256']=dict(source)
  if not enabled:
   for name in set(binding.NORMAL_HELPERS)-{'audit_unloaded_wrist_prior_live.py'}:prov['source_sha256'].pop(newprefix+name)
  (case/'provenance.json').write_text(json.dumps(prov,indent=2))
  out,_,_=binding.verify_trial_provenance(case);assert out==prov
  rows.append(dict(layout_id=cmd['layout_id'],enabled=enabled,source_count=len(prov['source_sha256']),passed=True))
  print(json.dumps(rows[-1]),flush=True)
# Final provenance is an enabled wait command. The source verifier does not
# claim these fixture files are a complete collection or a physical result.
good=copy.deepcopy(prov);negative=[]
for label in ['missing_new_helper','duplicate_collector','wrong_helper_hash','missing_flag','disabled_with_enabled_archive','traversal_path','bad_prerequisite']:
 bad=copy.deepcopy(good)
 if label=='missing_new_helper':bad['source_sha256'].pop(newprefix+'front_normal_nondegradation_runtime_candidate_v1.py')
 elif label=='duplicate_collector':bad['source_sha256'][oldprefix+'collect_paired_sorting.py']=sha(old/'collect_paired_sorting.py')
 elif label=='wrong_helper_hash':bad['source_sha256'][newprefix+'front_normal_nondegradation_runtime_candidate_v1.py']='0'*64
 elif label=='missing_flag':bad['args'].pop('front_normal_nondegradation')
 elif label=='disabled_with_enabled_archive':bad['args']['front_normal_nondegradation']=False
 elif label=='traversal_path':bad['source_sha256']['../forbidden']='0'*64
 else:bad['args']['joint_transport_effective_quarter_height']=False
 (case/'provenance.json').write_text(json.dumps(bad,indent=2))
 try:binding.verify_trial_provenance(case)
 except (AssertionError,KeyError):negative.append(label)
 else:raise AssertionError(('accepted invalid source binding',label))
(case/'provenance.json').write_text(json.dumps(good,indent=2))
(case/'DIAGNOSTIC_ONLY.json').write_text(json.dumps(dict(physical_collection=False,training_ready=False,scope=__doc__),indent=2))
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,stage_sources=len(used),commands=rows,negative_cases=negative,source_sha256={**bound,**{str(p):sha(p) for p in [Path(__file__),W/'front_normal_stage_source_binding_v2.py',stage/'collect_paired_sorting.py',W/'prepare_closed_peak_trial.py']}},observation_binding_tested=False,physics_started=False,training_ready=False)
(D/'RESULT.json').write_text(json.dumps(report,indent=2));print(json.dumps(dict(passed=True,commands=len(rows),negative=len(negative),stage_sources=len(used))),flush=True)
