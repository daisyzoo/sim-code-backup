"""Freeze same complete8push2wait, adding only interior recovery preference.
No training admission. All parent frozen evidence retained, current runtime,
audit versions and actual preflight dependencies frozen before one collector.
"""
from pathlib import Path
import json,hashlib,copy,datetime
w=Path(__file__).resolve().parent;repo=w.parents[1];parent=w/'recontact_pose_groups_r1';stage=w/'staged_recontact_interior';r=w/'recontact_interior_groups_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def prepare():
 assert not r.exists()
 result=json.loads((parent/'RESULT.json').read_text());assert result['push_total']==8 and result['waits_passed']==2 and result['actual_sampled_visual_review_complete'] and not result['training_ready']
 for name in ['STATUS.json','CONTROL_EVIDENCE_EXECUTION.json','ADDITIONAL_AUDIT_EXECUTION.json']:
  d=json.loads((parent/name).read_text());assert not Path(f"/proc/{d['pid']}/cmdline").exists()
 reports=['CONTRACT_CHECK.json','LIFECYCLE_CHECK.json','LIVE_FILES_CHECK.json','AUDIT_VERSION_CHECK.json','RUN_PROTOCOL_CHECK.json'];files={}
 old=json.loads((parent/'PROTOCOL.json').read_text())
 for path,h in old['frozen_files_sha256'].items():assert sha(path)==h;files[path]=h
 for name in reports:
  d=json.loads((stage/name).read_text());assert d['passed'],name
  for path,h in d['source_sha256'].items():assert sha(path)==h,(name,path);files[path]=h
  if 'fixture_sha256' in d:assert sha(stage/'LIFECYCLE_CHECK.json')==d['fixture_sha256']
 commands=copy.deepcopy(old['commands'])
 for c in commands:c['args']=[x.replace(str(parent),str(r)) for x in c['args']]+['--recontact-interior-preference']
 for a,b in zip(old['commands'],commands):assert a['layout_id']==b['layout_id'] and a['tasks']==b['tasks'] and [x.replace(str(r),str(parent)) for x in b['args'][:-1]]==a['args']
 assert sum(len(c['tasks']) for c in commands if not c['wait'])==8 and sum(len(c['tasks']) for c in commands if c['wait'])==2
 for p in stage.iterdir():
  if p.suffix in ['.py','.json']:files[str(p)]=sha(p)
 for pattern in ['audit_interior_*.py','audit_recontact_interior_events.py','check_recontact_interior_*.py','*recontact_interior_groups.py','watch_recontact_interior_audits.py','interior_audit_context.py','interior_run_contract.py','INTERIOR_AUDIT_VERSION_MAP.json']:
  for p in w.glob(pattern):files[str(p)]=sha(p)
 r.mkdir();(r/'layouts').mkdir()
 for src in (parent/'layouts').glob('*.json'):
  dst=r/'layouts'/src.name;dst.write_bytes(src.read_bytes());files[str(dst)]=sha(dst)
 out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),collector=str(stage/'collect_paired_sorting.py'),commands=commands,frozen_files_sha256=files,parent_protocol_sha256=sha(parent/'PROTOCOL.json'),parent_result_sha256=sha(parent/'RESULT.json'),scope='Same8push2wait/layouts/tasks/seeds/1200push70wait/order. Only interior preference20mm then explicit original12mm fallback. No new loaded edge adapter, task precision or pressure change. Original80controls+56extra and10actualRGB reviews, unchanged task/data/modelh10 gates.',training_ready=False)
 (r/'PROTOCOL.json').write_text(json.dumps(out,indent=2));(r/'INPUT_COMPARISON.json').write_text(json.dumps(dict(same_tasks_layouts_seeds_horizons_order=True,new_flag='--recontact-interior-preference',commands=6,control_invocations=80,additional_invocations=56,training_ready=False),indent=2));print(r,len(files))
if __name__=='__main__':prepare()
