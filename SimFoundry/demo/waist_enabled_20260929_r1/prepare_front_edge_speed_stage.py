"""Isolate edge governor on frozen2mm front-drive sources; do not launch physics."""
from pathlib import Path
import ast,hashlib,json
w=Path(__file__).resolve().parent;parent=w/'staged_front_drive_increment';probe=w/'staged_front_edge_speed_probe';dst=w/'staged_front_edge_speed';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();m=json.loads((parent/'MANIFEST.json').read_text());replay=json.loads((probe/'EDGE_SPEED_REPLAY_CHECK.json').read_text());audit=json.loads((probe/'EDGE_SPEED_AUDITOR_CHECK.json').read_text());entry=json.loads((probe/'AUDITOR_ENTRY_CHECK.json').read_text());assert replay['passed'] and audit['passed'] and entry['passed']
for n,h in m['source_sha256'].items():assert sha(parent/n)==h
for n,h in replay['source_sha256'].items():assert sha(probe/n)==h
assert audit['counterfactual_fixture_sha256']==entry['fixture_sha256']==sha(probe/'EDGE_SPEED_REPLAY_CHECK.json');assert audit['auditor_sha256']==entry['auditor_sha256']==sha(w/'audit_front_edge_speed_live.py');assert sha(parent/'contact_slip_following.py')==sha(probe/'contact_slip_following.py')
dst.mkdir(exist_ok=False)
for n in m['source_sha256']:(dst/n).write_bytes((parent/n).read_bytes())
for n in ['front_cop_route.py','front_edge_speed.py']:(dst/n).write_bytes((probe/n).read_bytes())
p=dst/'collect_paired_sorting.py';s=p.read_text()
def rep(a,b):
 global s
 assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
rep("parser.add_argument('--front-cop-drive-step-m',", "parser.add_argument('--front-cop-edge-speed',action='store_true',help='Diagnostic front-only1..2mm drive near measured COP edge; requires2mm phase-reset route-axis COP.')\nparser.add_argument('--front-cop-drive-step-m',")
rep('args = parser.parse_args()',"args = parser.parse_args()\nif args.front_cop_edge_speed and not (args.front_cop_route_axis and args.front_cop_phase_anchor and args.front_cop_slip_following and args.front_cop_drive_step_m==.002):\n    parser.error('Front edge speed requires2mm phase-reset route-axis COP')")
needle="                    frontal_plan['front_route_live_guards'] = dict"
rep(needle,"""                    if args.front_cop_edge_speed:
                        from isaaclab.sim.utils.stage import get_current_stage
                        from simfoundry.data.parcel_collision_geometry import read_parcel_collision_geometry
                        edge_actor='parcel_box' if side=='right' else 'mailer'
                        edge_core=read_parcel_collision_geometry(get_current_stage(),'/World/envs/env_0/'+edge_actor,expected_size=env.scene[edge_actor].cfg.spawn.size)
                        edge_size=np.asarray(edge_core['collision_core_size_xyz'],dtype=float)
                        if edge_size.shape!=(3,) or not np.isfinite(edge_size).all() or np.any(edge_size<=.02) or np.any(edge_size>np.asarray(target_size)+1e-6):raise ValueError('Invalid measured front edge core')
                        top_extra.update(edge_speed_enabled=True,edge_core_size=tuple(edge_size))
                        frontal_plan['front_cop_slip_following']['edge_speed']=dict(enabled=True,minimum_drive_step_m=.001,warning_distance_m=.010,actual_core_size_xyz=edge_size.tolist(),actual_core=edge_core,current_previous_packet_only=True,original_guard_priority=True)
"""+needle)
rep("'rear_cop_centering.py','rear_cop_route.py']])", "'rear_cop_centering.py','rear_cop_route.py','front_edge_speed.py']])")
p.write_text(s)
for p in dst.glob('*.py'):ast.parse(p.read_text())
unchanged=[n for n in m['source_sha256'] if n not in ['front_cop_route.py','collect_paired_sorting.py']]
for n in unchanged:assert sha(dst/n)==sha(parent/n)
out=dict(parent_stage=str(parent),parent_manifest_sha256=sha(parent/'MANIFEST.json'),source_sha256={n:sha(dst/n) for n in [*m['source_sha256'],'front_edge_speed.py']},unchanged_parent_helpers=unchanged,probe_replay_sha256=sha(probe/'EDGE_SPEED_REPLAY_CHECK.json'),probe_audit_sha256=sha(probe/'EDGE_SPEED_AUDITOR_CHECK.json'),probe_entry_sha256=sha(probe/'AUDITOR_ENTRY_CHECK.json'),collector_wired_in_source=True,cli_checked=False,actual_collector_checked=False,expected_archive_sources=56,physical_started=False,training_ready=False,scope='New isolated front-only governor; defaultoff, nominal2mm with1mm positive minimum over10mm current forward-core edge. ActualUSD core measured, no altered objects/materials/quality/guards. Parent current run remains frozen. Complete CLI/actual wiring/audits and full parent closure before physics.')
(dst/'PREPARATION.json').write_text(json.dumps(out,indent=2));print(dst)
