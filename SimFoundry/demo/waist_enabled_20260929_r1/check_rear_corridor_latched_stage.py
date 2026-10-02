"""Actual parser, adapter, route-state and extracted phase-commit AST checks.
Uses fixed historical inputs; no physics and no training admission.
"""
from pathlib import Path
from types import SimpleNamespace
import ast,sys,json,hashlib,datetime,copy,os,contextlib,io
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_rear_corridor_latched';sys.path[:0]=[str(S),str(W),str(ROOT)]
from rear_corridor_latched_adapter import propose,commit,commit_phase
from rear_corridor_latched_phase_v2 import initial_state,propose_phase
from rear_cop_route import RearCopRouteState
from clearance_runtime import ClearanceGuard
from prepare_closed_peak_trial import parser_namespace
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
prep=json.loads((S/'PREPARATION.json').read_text());assert all(sha(S/n)==h for n,h in prep['stage_sha256'].items())
frozen={str(S/n):h for n,h in prep['stage_sha256'].items()};frozen[str(Path(__file__))]=sha(__file__)
report=S/'CHECK.json';assert not report.exists();rows=[];negative=[];cli_checks=[];off_count=0
check_path=W/'REAR_CORRIDOR_LATCHED_CANDIDATE_V3_CHECK.json';frozen[str(check_path)]=sha(check_path);candidate=json.loads(check_path.read_text());assert candidate['passed'];sources=candidate['source_sha256'];guard=ClearanceGuard(ROOT,S)
def save(status,**kw):
 tmp=report.with_suffix('.tmp');tmp.write_text(json.dumps(dict(status=status,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,negative_checks=negative,cli_checks=cli_checks,default_off_rows=off_count,frozen_sha256=frozen,source_sha256=sources,simulation_started=False,training_ready=False,**kw),indent=2));tmp.replace(report)
try:
 save('running');protocol=json.loads((W/'rear_corridor_physical_r1/PROTOCOL.json').read_text());base=list(json.loads((W/'peak_guard_groups_r1/PROTOCOL.json').read_text())['commands'][0]['args'])+['--out-dir','/tmp/latched_CLI_NO_SIMULATION']
 for name,args,expect in [('default_off',base,True),('existing_recovery',base+['--rear-corridor-recovery'],True),('new_phase',base+['--rear-corridor-recovery','--rear-corridor-hysteresis'],True),('reject_missing_recovery',base+['--rear-corridor-hysteresis'],False)]:
  try:
   with contextlib.redirect_stderr(io.StringIO()):settings,_=parser_namespace(S/'collect_paired_sorting.py',args,full=True)
   accepted=True
  except (ValueError,SystemExit):accepted=False
  assert accepted==expect;cli_checks.append(dict(name=name,accepted=accepted))
  if accepted:assert settings['rear_corridor_hysteresis']==(name=='new_phase')
 sys.path[:0]=[str(S),str(W),str(ROOT)]
 tree=ast.parse((S/'collect_paired_sorting.py').read_text());matches=[n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='args.rear_corridor_hysteresis and rear_recovery_record is not None'];assert len(matches)==1
 phase_commit_ast=compile(ast.fix_missing_locations(ast.Module(body=matches,type_ignores=[])),str(S/'collect_paired_sorting.py'),'exec')
 sizes={'box':[.14,.09,.045],'mailer':[.15,.145,.04]}
 for item in candidate['episodes']:
  ep=W/item['episode'];fr=json.loads((ep/'frontal_bypass.json').read_text());fs={r['step']:r for r in fr['rows']};cs={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};rr=json.loads((ep/'rear_corridor_recovery.json').read_text())['rows'];selected={r['step'] for r in item['solver_rows']};side='right' if 'push_box' in ep.name else 'left';key='box' if side=='right' else 'mailer';other='mailer' if key=='box' else 'box'
  with np.load(ep/'raw.npz') as z:actions=z['action'].copy()
  with np.load(ep/'trace.npz') as z:pos={k:z[k].copy() for k in sizes}
  with np.load(ep/'parcel_orientation.npz') as z:rot={k:Rotation.from_quat(z[k]).as_matrix() for k in sizes}
  phase=initial_state()
  for t,action in enumerate(actions):
   p=action[12:23];off,record=propose(enabled=False,step=t,selected=True,parent_command=p);assert off is p and record['kind']=='unchanged';off_count+=1
  for record in rr:
   t=record['step'];r=record.get('parent_row',fs[t]);c=record.get('parent_coordinate',cs[t]);geom=dict(target_xyz=pos[key][t],obstacle_xyz=pos[other][t],target_rotation=rot[key][t],obstacle_rotation=rot[other][t],target_size=sizes[key],obstacle_size=sizes[other]);next_phase=propose_phase(state=phase,step=t,side=side,row=r,coordinate=c,**geom)['after']
   if t in selected:
    q=np.asarray(c['upper_q']);prev=actions[t-1,12:23];args=dict(enabled=True,step=t,selected=True,parent_command=np.asarray(record['parent_command']),phase_state=phase,side=side,guard=guard,row=r,coordinate=c,current=q,previous=prev,core_size=fr['plan']['rear_cop_centering']['actual_core_size_xyz'],**geom)
    before=copy.deepcopy((r,c,phase));cmd,proposed=propose(**args);assert (r,c,phase)==before;assert proposed['kind']=='loaded_recovery'
    state=RearCopRouteState(rear=SimpleNamespace(plan=fr['plan']),side=side,size=tuple(sizes[key]),hold_established_x=True)
    state.top_mode=state.mode=r['mode'];state.command=tuple(r['target_xyz']);state.last_waypoint_xy=tuple(r['target_xyz'][:2]);state.push_x_anchor=r.get('push_x_anchor_m');state.recontacts=r['recontacts'];state.load.bias_m=r['contact_load']['stored_z_bias_m'];state.load.filtered_n=r['contact_load']['filtered_vertical_load_n'];state.rear_corridor_recontact_pending=False
    original_load=(state.load.bias_m,state.load.filtered_n,state.recontacts)
    updated=commit(state=state,guard=guard,row=r,coordinate=c,current=q,previous=prev,command=cmd,record=proposed)
    assert original_load==(state.load.bias_m,state.load.filtered_n,state.recontacts) and not state.rear_corridor_recontact_pending
    assert tuple(updated['target_xyz'])==state.command and state.last_waypoint_xy==state.command[:2]
    action=actions[t].copy();action[12:23]=cmd
    ns=dict(args=SimpleNamespace(rear_corridor_hysteresis=True),rear_recovery_record=proposed,rear_corridor_phase=phase,clearance_guard=guard,rear_current=q,previous=actions[t-1],action=action)
    exec(phase_commit_ast,ns);assert ns['rear_corridor_phase']==next_phase==proposed['phase_committed'] and phase==before[2]
    for label,changes in [('duplicate_commit',{}),('stale_state',dict(phase_state=next_phase)),('altered_command',dict(command=cmd+.001))]:
     kw=dict(phase_state=phase,record=copy.deepcopy(proposed),guard=guard,current=q,previous=prev,command=cmd)
     if label!='duplicate_commit':kw['record'].pop('phase_committed')
     kw.update(changes)
     try:commit_phase(**kw)
     except ValueError:pass
     else:raise AssertionError(label)
     if label not in negative:negative.append(label)
    rows.append(dict(episode=ep.name,step=t,kind=proposed['kind'],phase_reason=proposed['phase']['reason'],phase_after=next_phase,actual_commit_ast_passed=True,pressure_state_unchanged=True))
    print(ep.name,t,'committed',flush=True)
   phase=next_phase
  save('running')
 for p,h in {**sources,**frozen}.items():assert sha(p)==h,p
 assert len(rows)==14 and off_count==2400
 save('complete',passed=True,remaining='Independent full native phase/command audits and original source-contract integration. No new physical experiment launched.')
except BaseException as e:save('check_failed',passed=False,error=repr(e));raise
