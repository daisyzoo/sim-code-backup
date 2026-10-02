"""Freeze the same two complete swap groups for an isolated front-only repair.
Never combine the joint-edge repair; retain all original failures and horizons.
"""
from pathlib import Path
import json,copy,hashlib,datetime
W=Path(__file__).resolve().parent;P=W/'front_interval_physical_preparation_r1';assert not P.exists();P.mkdir();(P/'layouts').mkdir();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();source=W/'joint_edge_intersection_physical_preparation_r1/PLAN.json';old=json.loads(source.read_text());plan=copy.deepcopy(old);stage=W/'staged_front_corridor_interval';plan.update(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),collector=str(stage/'collect_paired_sorting.py'),collector_sha256=sha(stage/'collect_paired_sorting.py'),stage_check_sha256=sha(stage/'CHECK.json'),independent_record_check_sha256=sha(W/'FRONT_INTERVAL_INDEPENDENT_ENABLED_CHECK.json'),parent_comparison_plan_sha256=sha(source),scope=__doc__,joint_edge_repair_combined=False,launch_requirements=['Original 60-condition baseline formally closed; exact two comparison groups fully audited','Original joint-edge collection terminal and GPU compute empty; CPU auditors may continue independently','All original 27 distinct auditors retained with isolated front source/goal binding, compact-rejection handling and all-vertex KKT','New run directory; original pressure, camera, layout, seed and 1200/70 horizons preserved; storage above30GiB'])
for item,prior in zip(plan['commands'],old['commands']):
 args=item['args'];assert args.count('--edge-clearance-intersection')==1;args[args.index('--edge-clearance-intersection')]='--front-corridor-interval';args[args.index('--out-dir')+1]=str(P/f"case_{item['layout_id']}")
 if not item['wait']:
  i=args.index('--diagnostic-layout-json')+1;src=Path(args[i]);dest=P/'layouts'/src.name;assert sha(src)==item['layout_sha256'];dest.write_bytes(src.read_bytes());args[i]=str(dest)
 canonical=list(args);canonical[canonical.index('--front-corridor-interval')]='--edge-clearance-intersection';canonical[canonical.index('--out-dir')+1]=prior['args'][prior['args'].index('--out-dir')+1]
 if not item['wait']:canonical[canonical.index('--diagnostic-layout-json')+1]=prior['args'][prior['args'].index('--diagnostic-layout-json')+1]
 assert canonical==prior['args']
with (P/'PLAN.json').open('x') as f:json.dump(plan,f,indent=2)
print('prepared original8push2wait; only front interval repair enabled')
