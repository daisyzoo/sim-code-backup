"""Isolate direct-route terminal lead adapter without changing frozen parent.
This preparation grants no physical launch or training admission.
"""
from pathlib import Path
import json,hashlib,ast,datetime
W=Path(__file__).resolve().parent;A=W/'staged_terminal_release_margin';B=W/'staged_terminal_directional_lead';assert not B.exists();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();parent=json.loads((A/'PREPARATION.json').read_text());history=W/'TERMINAL_DIRECTIONAL_LEAD_CANDIDATE_CHECK_V2.json';assert json.loads(history.read_text())['passed']
for n,h in parent['stage_sha256'].items():assert sha(A/n)==h,n
s=(A/'collect_paired_sorting.py').read_text();edits=[]
def edit(a,b):
 global s
 assert s.count(a)==1,a;s=s.replace(a,b);edits.append(dict(old=a,new=b))
a="parser.add_argument('--terminal-release-margin',action='store_true',help='Diagnostic confirmed release also requires existing5mm zone/10mm progress margins; default off.')"
edit(a,a+"\nparser.add_argument('--terminal-directional-lead',action='store_true',help='Diagnostic direct-route last-step directional lead; original3mm step, default off.')")
a="if args.terminal_release_margin and not ("
edit(a,"if args.terminal_directional_lead and not (args.terminal_release_margin and args.role=='diagnostic' and not args.policy_port and not args.waist_pilot_contract):\n    raise ValueError('Terminal directional lead requires diagnostic margin protocol')\n"+a)
a="                    top_cls, top_extra = InitialTopRouteState, dict(obstacle_size=tuple(obstacle_size))"
edit(a,a+"\n                    if args.terminal_directional_lead:\n                        from terminal_directional_lead_state import TerminalLeadInitialTopState\n                        top_cls=TerminalLeadInitialTopState\n                        top_extra['terminal_directional_lead_enabled']=True\n                        frontal_plan['terminal_directional_lead']=dict(enabled=True,scope='initial_top_lateral_y_only',maximum_original_step_m=.003,force_and_quality_unchanged=True)")
a="    if args.terminal_release_margin:\n        episode.collect_meta['terminal_release_margin']=True"
edit(a,"    if args.terminal_directional_lead:\n        episode.collect_meta['terminal_directional_lead']=True\n"+a)
a="    if args.terminal_release_margin:\n        paths.append(STAGE/'margin_confirmed_position_release.py')"
edit(a,a+"\n    if args.terminal_directional_lead:\n        paths.extend([STAGE/'terminal_directional_lead_state.py',STAGE/'terminal_directional_lead_candidate.py'])")
back=s
for e in reversed(edits):assert back.count(e['new'])==1;back=back.replace(e['new'],e['old'])
assert back==(A/'collect_paired_sorting.py').read_text();ast.parse(s);B.mkdir()
for n in parent['stage_sha256']:(B/n).write_bytes((A/n).read_bytes())
(B/'collect_paired_sorting.py').write_text(s)
for n in ['terminal_directional_lead_state.py','terminal_directional_lead_candidate.py']:(B/n).write_bytes((W/n).read_bytes())
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,parent_stage=str(A),parent_preparation_sha256=sha(A/'PREPARATION.json'),history_check_sha256=sha(history),edits=edits,stage_sha256={p.name:sha(p) for p in B.iterdir() if p.is_file()},simulation_started=False,training_ready=False,remaining='Actual parser/state lifecycle and independent new feedback audit; original-source audit adapters then full fixed conditions physics. No hard-layout route fix is claimed.')
(B/'PREPARATION.json').write_text(json.dumps(report,indent=2));print('prepared',len(report['stage_sha256']),'files')
