from pathlib import Path
import json,hashlib,copy,datetime
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_self_clearance_task_ik';parent=w/'joint_edge_retry_groups_r1';r=w/'self_clearance_groups_r1';assert not r.exists();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
checks=json.loads((stage/'INTEGRATION_CHECK.json').read_text());assert checks['default_off_cases']==64 and checks['historical_overlap_rejected'];assert json.loads((stage/'AUDITOR_CHECK.json').read_text())['all_passed']
pre=w/'self_clearance_runtime_preflight_r1/case/layout_841000_wait_no_package';assert json.loads((pre/'SELF_CLEARANCE_LIVE_AUDIT.json').read_text())['episode_clearance_passed'];assert json.loads((pre/'WAIT_STABILITY_AUDIT.json').read_text())['passed']
old=json.loads((parent/'PROTOCOL.json').read_text());commands=copy.deepcopy(old['commands']);r.mkdir();(r/'layouts').mkdir();files={}
for path,h in old['layout_sha256'].items():
 src=Path(path);assert sha(src)==h;dest=r/'layouts'/src.name;dest.write_bytes(src.read_bytes());files[str(dest)]=h
for c in commands:c['args']=[x.replace(str(parent),str(r)) for x in c['args']]+['--self-clearance-task-ik']
assert sum(len(c['tasks']) for c in commands if not c['wait'])==8 and sum(len(c['tasks']) for c in commands if c['wait'])==2
for a,b in zip(old['commands'],commands):assert a['layout_id']==b['layout_id'] and a['tasks']==b['tasks'] and [x.replace(str(r),str(parent)) for x in b['args'][:-1]]==a['args']
oldstage=str((w/'staged_joint_edge_retry').relative_to(repo));newstage=str(stage.relative_to(repo))
for n,h in old['source_sha256'].items():
 path=repo/n.replace(oldstage,newstage);files[str(path)]=sha(path)
 if oldstage not in n:assert files[str(path)]==h
for path in stage.iterdir():
 if path.suffix in ['.py','.json']:files[str(path)]=sha(path)
for path,h in json.loads((stage/'elbow_torso_hulls.json').read_text())['usd_layers_sha256'].items():assert sha(path)==h;files[path]=h
for name in ['run_self_clearance_groups.py','audit_self_clearance_live.py','audit_normal_wait.py','check_self_clearance_integration.py','check_self_clearance_auditor.py','prepare_self_clearance_groups.py']:files[str(w/name)]=sha(w/name)
p=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),collector=str(stage/'collect_paired_sorting.py'),commands=commands,frozen_files_sha256=files,parent_protocol_sha256=sha(parent/'PROTOCOL.json'),parent_result_sha256=sha(parent/'RESULT.json'),scope='Original8push2wait/layout/seed/horizon/order. Only new clearance IK flag plus read-only actual pose,final-action,asset/config/filter/K provenance. Early failure stays failed; no training/export. Independent geometry/command-chain audit is NOT original contact/refinement/full-control/visual admission.',training_ready=False)
(r/'PROTOCOL.json').write_text(json.dumps(p,indent=2));(r/'INPUT_COMPARISON.json').write_text(json.dumps(dict(same_tasks_layouts_seeds_horizons_order=True,commands=6,new_flag='--self-clearance-task-ik',training_ready=False),indent=2));print(r)
