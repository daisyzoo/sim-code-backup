"""Freeze complete8push2wait and original audit gates, adding current-contact edge coverage.
Never rerun over an existing experiment. Preparing is not physical or data admission.
"""
from pathlib import Path
import json,hashlib,copy,datetime
w=Path(__file__).resolve().parent;repo=w.parents[1];parent=w/'recontact_pose_groups_r1';oldstage=w/'staged_recontact_pose';stage=w/'staged_loaded_edge_coverage';r=w/'loaded_edge_coverage_groups_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def prepare():
 assert not r.exists()
 closed=json.loads((parent/'RESULT.json').read_text());assert closed['status']=='diagnostic_closed_not_training_admission' and closed['push_total']==8 and closed['waits_passed']==2 and closed['actual_sampled_visual_review_complete']
 for name in ['STATUS.json','CONTROL_EVIDENCE_EXECUTION.json','ADDITIONAL_AUDIT_EXECUTION.json']:
  state=json.loads((parent/name).read_text());assert not Path(f"/proc/{state['pid']}/cmdline").exists()
 check=json.loads((stage/'RUN_PROTOCOL_CHECK.json').read_text());assert check['passed'];reports=check['current_preflight_checks']+['RUN_PROTOCOL_CHECK.json'];files={}
 for name in reports:
  d=json.loads((stage/name).read_text());assert d.get('passed',d.get('adapter_checks_passed')) is True
  for path,h in d['source_sha256'].items():assert sha(path)==h,(name,path);files[path]=h
 old=json.loads((parent/'PROTOCOL.json').read_text())
 for name,h in old['frozen_files_sha256'].items():
  assert sha(name)==h,name
  path=Path(name.replace(str(oldstage),str(stage)))
  if str(path).startswith(str(parent/'layouts')):continue
  if path.exists():files[str(path)]=sha(path)
 commands=copy.deepcopy(old['commands'])
 for c in commands:c['args']=[x.replace(str(parent),str(r)) for x in c['args']]+['--loaded-edge-coverage']
 for a,b in zip(old['commands'],commands):assert a['layout_id']==b['layout_id'] and a['tasks']==b['tasks'] and [x.replace(str(r),str(parent)) for x in b['args'][:-1]]==a['args']
 assert sum(len(c['tasks']) for c in commands if not c['wait'])==8 and sum(len(c['tasks']) for c in commands if c['wait'])==2
 for path in stage.iterdir():
  if path.suffix in ['.py','.json']:files[str(path)]=sha(path)
 for pattern in ['audit_loaded_edge*.py','check_loaded_edge*.py','*loaded_edge_coverage_groups.py','watch_loaded_edge_coverage_audits.py','loaded_edge_audit_context.py','loaded_edge_run_contract.py','LOADED_EDGE_AUDIT_VERSION_MAP.json']:
  for path in w.glob(pattern):files[str(path)]=sha(path)
 r.mkdir();(r/'layouts').mkdir()
 for src in (parent/'layouts').glob('*.json'):
  dest=r/'layouts'/src.name;dest.write_bytes(src.read_bytes());files[str(dest)]=sha(dest)
 protocol=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),collector=str(stage/'collect_paired_sorting.py'),commands=commands,frozen_files_sha256=files,parent_protocol_sha256=sha(parent/'PROTOCOL.json'),parent_result_sha256=sha(parent/'RESULT.json'),scope='Same original8push2wait/tasks/layouts/seeds/1200push70wait/order. Only loaded-edge-coverage flag added. Current causal contact and continued-push eligibility; stationary float32 multistart proposals. Original80controls with named versions plus56extra and10new native coverage audits, independent final geometry and10actualimage reviews. Original1e-6KKT and global task solver/pressure unchanged. No training admission.',training_ready=False)
 (r/'PROTOCOL.json').write_text(json.dumps(protocol,indent=2));(r/'INPUT_COMPARISON.json').write_text(json.dumps(dict(same_tasks_layouts_seeds_horizons_order=True,new_flag='--loaded-edge-coverage',commands=6,control_invocations=80,additional_invocations=56,new_coverage_invocations=10,training_ready=False),indent=2));print(r)
if __name__=='__main__':prepare()
