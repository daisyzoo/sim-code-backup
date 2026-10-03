"""Check both replay callers consume verified events and preserve full inventory.
One original-history prefix ends before a changed action would execute. This is
not a continuous candidate rollout, full loaded dynamics or training evidence.
"""
from pathlib import Path
import ast,copy,json,hashlib,sys,datetime
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];D=W/'rear_waypoint_reconciliation_draft_r1';sys.path[:0]=[str(D),str(W),str(ROOT)];sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
prep=json.loads((W/'REAR_WAYPOINT_LOADED_AUDIT_V3_PREPARATION.json').read_text());sources=dict(prep['source_sha256'])
for p,h in sources.items():assert sha(p)==h,p
for row in prep['adapters']:
 p=Path(row['path']);old=Path(row['parent']);assert sha(p)==row['sha256'] and sha(old)==row['parent_sha256'];s=p.read_text()
 for a,b in reversed(row['replacements']):s=s.replace(b,a)
 assert s==old.read_text();sources[str(p)]=sha(p);sources[str(old)]=sha(old)
import rear_waypoint_v3_stage_run_contract as contract
import audit_rear_waypoint_v3_stage_pose_loaded_execution as loaded
from audit_rear_waypoint_v2_stage_rear_xy import reconstruct
assert loaded.reconstruct is reconstruct
config=json.loads((W/'rear_waypoint_preparation_r1/CONFIGURATION_SOURCE_AUDIT_CHECK.json').read_text());inventory=[];oldname='audit_rear_waypoint_v2_stage_pose_loaded_execution.py';newname='audit_rear_waypoint_v3_stage_pose_loaded_execution.py'
for row in config['inventory']:
 scripts=[newname if s==oldname else s for s in row['scripts']];assert all(s in contract.REPORTS for s in scripts);assert scripts.count('audit_rear_waypoint_v2_commit.py')==1;inventory.append(dict(episode=row['episode'],scripts=scripts))
assert sum(len(r['scripts']) for r in inventory)==214 and sum(newname in r['scripts'] for r in inventory)==8
callers=[]
for p,function in [(W/'audit_rear_waypoint_v2_stage_rear_xy.py','main'),(W/newname,'replay')]:
 tree=ast.parse(p.read_text());f=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==function);calls=[n for n in ast.walk(f) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='reconstruct'];assert len(calls)==1;assert [ast.unparse(k.value) for k in calls[0].keywords if k.arg=='verified_post_commit']==['verified']
 imports=[n for n in ast.walk(f) if isinstance(n,ast.ImportFrom) and n.module=='audit_rear_waypoint_v2_commit'];assert len(imports)==1 and imports[0].names[0].name=='inspect_episode'
 assert any(isinstance(n,ast.Assign) and ast.unparse(n) == "commit = inspect_episode(ep)" for n in ast.walk(f))
 assert any(isinstance(n,ast.Assign) and ast.unparse(n)=="verified = commit['independently_verified_events']['verified_post_commit']" for n in ast.walk(f))
 callers.append(dict(file=p.name,function=function,verified_mapping_used=True));sources[str(p)]=sha(p)
from independent_post_commit_audit import load_context,verify
adapter=json.loads((D/'POST_COMMIT_ADAPTER_CHECK.json').read_text());run=next(x for x in adapter['results'] if x['run']=='front_corridor_midpoint_physical_r1');ep=W/run['run']/'case_840023/layout_840023_push_box_to_bin';urdf=ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf';ctx=load_context(ep,urdf);evidence=verify(ctx,run['records']);update=evidence['verified_post_commit'][565];prefix=copy.deepcopy([x for x in ctx['fr']['rows'] if x['step']<=566]);delta=update[1]-prefix[-2]['target_xyz'][1];assert delta>0;prefix[-1]['target_xyz'][1]+=delta;prefix[-1]['rear_cop_centering']['command_xyz'][1]+=delta
region=json.loads((ep/'region_approach.json').read_text())['rows'];handover=next(x['step'] for x in region if x['solver'] and x['solver'].get('handover'))
with np.load(ep/'parcel_orientation.npz') as z:quat=z['box'].astype(float)
args=(prefix,ctx['fr']['plan'],ctx['xyz'][:567],quat[:567],{k:v for k,v in ctx['packets'].items() if k<566},'box',handover)
good=loaded.reconstruct(*args,verified_post_commit={565:update});bad=loaded.reconstruct(*args);assert good['passed'] and good['post_commit_overrides_checked']==1 and not bad['passed']
expected=json.loads((D/'INDEPENDENT_POST_COMMIT_REPLAY_CHECK.json').read_text())['isolated_prefix_fixture']['replay'];assert good==expected
for p in [Path(__file__),W/'REAR_WAYPOINT_LOADED_AUDIT_V3_PREPARATION.json',D/'POST_COMMIT_ADAPTER_CHECK.json',D/'INDEPENDENT_POST_COMMIT_REPLAY_CHECK.json',D/'independent_post_commit_audit.py',D/'independent_rear_state_replay.py',urdf]:sources[str(p)]=sha(p)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,scope=__doc__,inventory=inventory,expected_audits=214,replay_callers=callers,isolated_unexecuted_prefix_step=566,prefix_replay_identical_to_independent_check=True,missing_commit_rejected=True,source_sha256=sources,physical_rollout=False,training_ready=False)
with (W/'rear_waypoint_preparation_r1/LOADED_AUDIT_V3_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(dict(passed=True,audits=214,replay_callers=len(callers),prefix_fixture_step=566,missing_commit_rejected=True))
