"""Exercise the exact added collector AST block on frozen lifecycle events.
Disabled and nonpending preserve object identity. Pending no-handover descent,
press and push are refused; this is command admission, not physical recovery.
"""
from pathlib import Path
from types import SimpleNamespace
import json,hashlib,datetime,sys,copy,pickle,ast,contextlib,io
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_rear_corridor_recovery_guarded';sys.path[:0]=[str(S),str(W),str(ROOT)]
from rear_corridor_recontact_gate import guard_pending
from prepare_closed_peak_trial import parser_namespace
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();prep=json.loads((S/'PREPARATION.json').read_text());assert all(sha(S/n)==h for n,h in prep['stage_sha256'].items());DEST=S/'PENDING_GATE_CHECK.json';assert not DEST.exists()
base=list(json.loads((W/'peak_guard_groups_r1/PROTOCOL.json').read_text())['commands'][0]['args'])+['--out-dir','/tmp/rear_corridor_gate_CLI_NO_SIMULATION'];cli=[]
for enabled in [False,True]:
 with contextlib.redirect_stderr(io.StringIO()):settings,_=parser_namespace(S/'collect_paired_sorting.py',base+(['--rear-corridor-recovery'] if enabled else []),full=True)
 assert settings['rear_corridor_recovery'] is enabled;cli.append(dict(enabled=enabled,accepted=True))
# Execute the real collector's added block, without importing/running its simulator.
tree=ast.parse((S/'collect_paired_sorting.py').read_text());matches=[n for n in ast.walk(tree) if isinstance(n,ast.If) and len(n.body)==2 and isinstance(n.body[0],ast.ImportFrom) and n.body[0].module=='rear_corridor_recontact_gate'];assert len(matches)==1
code=compile(ast.fix_missing_locations(ast.Module(body=matches,type_ignores=[])),str(S/'collect_paired_sorting.py'),'exec')
def call(event,mode,*,enabled,pending):
 state=SimpleNamespace(rear_corridor_recontact_pending=pending);before=pickle.dumps(state);ev_before=pickle.dumps(event);ns=dict(args=SimpleNamespace(rear_corridor_recovery=enabled),frontal_state=state,recontact_event=event,waypoint=dict(mode=mode));exec(code,ns);assert pickle.dumps(state)==before and pickle.dumps(event)==ev_before;return ns['recontact_event']
report=json.loads((W/'REAR_TRANSPORT_LIFECYCLE_CHECK.json').read_text());eps=sorted({r['episode'] for r in report['rows']});rows=[];sources={};counts=dict(original_events=0,disabled_identity=0,nonpending_identity=0,pending_refusals=0,pending_allowed=0)
for name in eps:
 path=W/name/'recontact_pose.json';sources[str(path)]=sha(path);events=json.loads(path.read_text())['rows'];er=dict(episode=name,events=len(events),pending_refusals=[])
 for event in events:
  mode=event.get('context',{}).get('parent_mode')
  # Contextless terminal rejection is preserved as stop; no invented parent input.
  if mode is None:assert event['kind']=='stop';mode='unknown'
  for pending in [False,True]:assert call(event,mode,enabled=False,pending=pending) is event;counts['disabled_identity']+=1
  assert call(event,mode,enabled=True,pending=False) is event;counts['nonpending_identity']+=1
  result=call(event,mode,enabled=True,pending=True);reject=event['kind']=='unchanged' and mode in ['top_descend','top_press','top_push']
  if reject:assert result['kind']=='stop' and result['original_event'] is event;counts['pending_refusals']+=1;er['pending_refusals'].append(event['step'])
  else:assert result is event;counts['pending_allowed']+=1
  counts['original_events']+=1
 rows.append(er)
negative=[]
for mode in ['top_lift','top_cross','top_descend','top_press','top_push','top_release','front_guard_lift']:
 ev=dict(kind='unchanged',reason='not_new_eligible_recovery');result=call(ev,mode,enabled=True,pending=True)
 assert (result['kind']=='stop')==(mode in ['top_descend','top_press','top_push']);negative.append(mode)
for ev in [dict(kind='command'),dict(kind='handover')]:
 try:call(ev,'top_push',enabled=True,pending=True)
 except ValueError:negative.append('bad_mode_'+ev['kind'])
 else:raise AssertionError('Incompatible event accepted')
try:guard_pending(enabled=1,state=None,event=None,parent_mode=None)
except ValueError:negative.append('non_bool_rejected')
else:raise AssertionError('Nonbool admitted')
for p,h in sources.items():assert sha(p)==h
sources.update({str(p):sha(p) for p in [Path(__file__),W/'REAR_TRANSPORT_LIFECYCLE_CHECK.json',S/'PREPARATION.json',S/'collect_paired_sorting.py',S/'rear_corridor_recontact_gate.py']})
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,scope=__doc__,cli=cli,counts=counts,episodes=rows,negative_checks=negative,source_sha256=sources,simulation_started=False,training_ready=False)
DEST.write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k not in ['episodes','source_sha256','scope']},indent=2))
