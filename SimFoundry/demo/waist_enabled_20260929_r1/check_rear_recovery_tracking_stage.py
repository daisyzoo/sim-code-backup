"""Actual collector parser, proposal selection and state commits on real inputs.
No physics. Past-only history is verified over complete loaded-recovery streams;
commands are verified independently by the previously frozen component check.
"""
from pathlib import Path
from types import SimpleNamespace
import ast,sys,json,hashlib,datetime,copy,os,contextlib,io
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_rear_recovery_tracking';sys.path[:0]=[str(S),str(W),str(ROOT)]
from rear_recovery_tracking_adapter import propose,commit,commit_phase
from rear_corridor_latched_adapter import propose as parent_propose
from rear_recovery_tracking_observation_v2 import observe
from rear_cop_route import RearCopRouteState
from clearance_runtime import ClearanceGuard
from prepare_closed_peak_trial import parser_namespace
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();prep=json.loads((S/'PREPARATION.json').read_text());frozen={str(S/n):h for n,h in prep['stage_sha256'].items()};frozen[str(Path(__file__))]=sha(__file__)
component=W/'REAR_RECOVERY_TRACKING_SOLVER_V2_CHECK.json';frozen[str(component)]=sha(component);cand=json.loads(component.read_text());assert cand['passed'];guard=ClearanceGuard(ROOT,S)
report=S/'CHECK.json';assert not report.exists();rows=[];cli=[];negative=[];hist=[];sources={};off=0

def save(status,**kw):
 p=report.with_suffix('.tmp');p.write_text(json.dumps(dict(status=status,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,cli_checks=cli,negative_checks=negative,history=hist,default_off_rows=off,source_sha256=sources,frozen_sha256=frozen,simulation_started=False,training_ready=False,**kw),indent=2));p.replace(report)
try:
 save('running')
 base=list(json.loads((W/'peak_guard_groups_r1/PROTOCOL.json').read_text())['commands'][0]['args'])+['--out-dir','/tmp/tracking_CLI_NO_SIMULATION']
 for name,opts,expect in [('default_off',[],True),('parent',['--rear-corridor-recovery','--rear-corridor-hysteresis'],True),('tracking',['--rear-corridor-recovery','--rear-corridor-hysteresis','--rear-recovery-tracking'],True),('missing_phase',['--rear-corridor-recovery','--rear-recovery-tracking'],False),('missing_contract',['--rear-recovery-tracking'],False)]:
  try:
   with contextlib.redirect_stderr(io.StringIO()):settings,_=parser_namespace(S/'collect_paired_sorting.py',base+opts,full=True)
   accepted=True
  except (ValueError,SystemExit):accepted=False
  assert accepted==expect
  if accepted:assert settings['rear_recovery_tracking']==(name=='tracking')
  cli.append(dict(name=name,accepted=accepted))
 sys.path[:0]=[str(S),str(W),str(ROOT)]
 tree=ast.parse((S/'collect_paired_sorting.py').read_text());sel=[n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='args.rear_recovery_tracking' and any(isinstance(k,ast.ImportFrom) and k.module=='rear_recovery_tracking_adapter' for k in n.body)];assert len(sel)==1
 select_ast=compile(ast.fix_missing_locations(ast.Module(body=sel,type_ignores=[])),str(S/'collect_paired_sorting.py'),'exec')
 phase=[n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='args.rear_corridor_hysteresis and rear_recovery_record is not None'];assert len(phase)==1
 phase_ast=compile(ast.fix_missing_locations(ast.Module(body=phase,type_ignores=[])),str(S/'collect_paired_sorting.py'),'exec')
 for rel in sorted(set(x['episode'] for x in cand['rows'])):
  ep=W/'rear_latched_physical_r1'/rel;fr=json.loads((ep/'frontal_bypass.json').read_text());records=json.loads((ep/'rear_corridor_recovery.json').read_text())['rows'];rs={x['step']:x for x in records}
  for n in ['raw.npz','rear_corridor_recovery.json','frontal_bypass.json']:sources[str(ep/n)]=sha(ep/n)
  with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
  for t,parent in enumerate(u):
   out,rr=propose(enabled=False,step=t,selected=True,parent_command=parent);assert out is parent and rr['kind']=='unchanged';off+=1
  accepted=outside=starts=0
  for r in records:
   if r['kind']!='loaded_recovery':continue
   t=r['step'];obs=observe(enabled=True,guard=guard,row=r['parent_row'],coordinate=r['parent_coordinate'],current=q[t],previous=u[t-1],previous_record=rs.get(t-1))
   accepted+=int(obs['accepted']);outside+=int(obs['reason']=='outside_tracking_domain');starts+=int(obs['reason']=='no_previous_executed_recovery')
  hist.append(dict(episode=rel,accepted=accepted,outside_domain=outside,no_previous_loaded=starts))
  for item in [x for x in cand['rows'] if x['episode']==rel]:
   t=item['step'];r=rs[t];row=r['parent_row'];c=r['parent_coordinate'];state_before=r['phase']['before'];side=c['active_side'];prior=rs[t-1]
   args=dict(enabled=True,step=t,selected=True,parent_command=np.asarray(r['parent_command']),phase_state=state_before,side=side,guard=guard,row=row,coordinate=c,current=q[t],previous=u[t-1],**r['geometry'])
   pc,pr=parent_propose(**args);oc,orr=propose(**args);assert pr==orr and np.array_equal(pc,oc)
   ns=dict(args=SimpleNamespace(rear_recovery_tracking=True),rear_phase_kwargs=dict(phase_state=state_before,side=side),rear_corridor_log=[prior]);exec(select_ast,ns);assert ns['rear_phase_kwargs']['previous_recovery_record'] is prior
   used=dict(args);used.update(ns['rear_phase_kwargs']);before=copy.deepcopy((row,c,prior,state_before));cmd,rr=ns['propose_rear_recovery'](**used)
   assert (row,c,prior,state_before)==before and rr['kind']=='loaded_recovery';assert np.array_equal(cmd,item['result']['attempts'][-1]['command'])
   state=RearCopRouteState(rear=SimpleNamespace(plan=fr['plan']),side=side,size=tuple(r['geometry']['target_size']),hold_established_x=True)
   state.top_mode=state.mode=row['mode'];state.command=tuple(row['target_xyz']);state.last_waypoint_xy=state.command[:2];state.push_x_anchor=row.get('push_x_anchor_m');state.recontacts=row['recontacts'];state.load.bias_m=row['contact_load']['stored_z_bias_m'];state.load.filtered_n=row['contact_load']['filtered_vertical_load_n'];state.rear_corridor_recontact_pending=False
   load=(state.load.bias_m,state.load.filtered_n,state.recontacts)
   updated=commit(state=state,guard=guard,row=row,coordinate=c,current=q[t],previous=u[t-1],command=cmd,record=rr)
   assert load==(state.load.bias_m,state.load.filtered_n,state.recontacts) and not state.rear_corridor_recontact_pending
   assert state.command==tuple(updated['target_xyz']) and state.last_waypoint_xy==state.command[:2]
   u23=np.zeros(23);u23[12:23]=cmd;prev23=np.zeros(23);prev23[12:23]=u[t-1]
   ns=dict(args=SimpleNamespace(rear_corridor_hysteresis=True),rear_recovery_record=rr,rear_corridor_phase=state_before,clearance_guard=guard,rear_current=q[t],previous=prev23,action=u23);exec(phase_ast,ns)
   assert rr['phase_committed']==ns['rear_corridor_phase']==r['phase']['after']
   for label,change in [('duplicate',{}),('stale',dict(phase_state=rr['phase_committed'])),('altered_action',dict(command=cmd+.001))]:
    kw=dict(phase_state=state_before,record=copy.deepcopy(rr),guard=guard,current=q[t],previous=u[t-1],command=cmd)
    if label!='duplicate':kw['record'].pop('phase_committed')
    kw.update(change)
    try:commit_phase(**kw)
    except ValueError:pass
    else:raise AssertionError(label)
    if label not in negative:negative.append(label)
   rows.append(dict(episode=rel,step=t,actual_selection_and_phase_ast=True,command_matches_independent_component_check=True,pressure_state_unchanged=True,default_off_parent_identical=True));save('running');print(rel,t,'committed',flush=True)
 for p,h in {**sources,**frozen}.items():assert sha(p)==h,p
 assert off==2400 and len(rows)==14
 save('complete',passed=True,remaining='Independent native tracking and unload audits, source binding and fixed paired physical comparison. No task improvement demonstrated.')
except BaseException as e:save('check_failed',passed=False,error=repr(e));raise
