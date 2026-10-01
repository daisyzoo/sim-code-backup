# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
"""Check existing release configuration without changing a run, gate or source."""
from pathlib import Path
import sys,types,json,hashlib,contextlib,io,tempfile
w=Path(__file__).resolve().parent;repo=w.parents[1];collector=w/'staged_front_cop_transverse/collect_paired_sorting.py';source=collector.read_text();prefix=source.split('app = AppLauncher(args, enable_cameras=True).app')[0];p=json.loads((w/'front_cop_groups_r1/PROTOCOL.json').read_text());args=p['commands'][0]['args'];assert '--expert-top-confirmed-release' in args
with tempfile.TemporaryDirectory(prefix='release_config_review_') as td:
 cli=args+['--out-dir',str(Path(td)/'NOT_STARTED')]
 def parse(cli):
  m=types.ModuleType('release_config_fixture');m.__file__=str(collector);sys.modules[m.__name__]=m;old=sys.argv;sys.argv=[str(collector),*cli]
  try:
   with contextlib.redirect_stderr(io.StringIO()):exec(compile(prefix,str(collector),'exec'),m.__dict__)
   return vars(m.args)
  finally:sys.argv=old;sys.modules.pop(m.__name__,None)
 on=parse(cli);off=parse([x for x in cli if x!='--expert-top-confirmed-release']);changes={k:[on[k],off[k]] for k in on if on[k]!=off[k]};assert changes=={'expert_top_confirmed_release':[True,False]};assert not (Path(td)/'NOT_STARTED').exists()
sys.path.insert(0,str(repo));from simfoundry.data.reach_sweep import ready_to_release
cases=[]
for direction,initial_y in [(1,-.15),(-1,.15),(1,.12),(-1,-.15)]:
 original=max(.20,direction*initial_y+.15);buffered=max(.205,direction*initial_y+.16)
 assert not ready_to_release(initial_y,direction*original,direction)
 assert ready_to_release(initial_y,direction*buffered,direction)
 cases.append(dict(direction=direction,initial_y_m=initial_y,original_signed_target_y_m=original,buffered_signed_target_y_m=buffered,additional_goal_distance_mm=1000*(buffered-original)))
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest();report=dict(passed=True,actual_prelauncher_parser_changes=changes,source_changed=False,physical_started=False,controller_gate_functions_changed=False,cases=cases,source_sha256={str(f.relative_to(repo)):sha(f) for f in [collector,repo/'simfoundry/data/top_contact_bypass.py',repo/'simfoundry/data/confirmed_position_release.py',repo/'simfoundry/data/reach_sweep.py',repo/'simfoundry/data/paired_sorting.py']},scope='Existing optional confirmed-release flag can be omitted under actual collector validation; no new controller needed to retain existing original-margin release. A separate future complete-group physical comparison is required. Removing confirmation changes release availability during recovery, so software and endpoint arithmetic do not prove preserved task success/stability. Current and next transverse-COP comparison flags stay unchanged.',training_ready=False)
(w/'RELEASE_MARGIN_CONFIG_REVIEW.json').write_text(json.dumps(report,indent=2));print(report)
