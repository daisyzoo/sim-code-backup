"""Actual parser/class selection plus original state-machine boundary checks.
Constructed geometric contexts exercise transitions; they are not robot rollouts.
"""
from pathlib import Path
from types import SimpleNamespace
import ast,sys,json,hashlib,datetime,copy,contextlib,io
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_terminal_directional_lead';sys.path[:0]=[str(S),str(W),str(ROOT)]
from prepare_closed_peak_trial import parser_namespace
from simfoundry.data.initial_top_route import InitialTopRouteState
from simfoundry.data.top_contact_bypass import top_surface_point
from terminal_directional_lead_state import TerminalLeadInitialTopState,DirectionalLeadFeedback
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();prep=json.loads((S/'PREPARATION.json').read_text());base=json.loads((W/'terminal_margin_physical_preparation_r1/PLAN.json').read_text())['commands'][0]['args'];tree=ast.parse((S/'collect_paired_sorting.py').read_text());blocks=[n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='initial_top_selected' and any(isinstance(x,ast.ImportFrom) and x.module=='simfoundry.data.initial_top_route' for x in n.body)];assert len(blocks)==1;code=compile(ast.fix_missing_locations(ast.Module(body=blocks,type_ignores=[])),str(S/'collect_paired_sorting.py'),'exec')
release=[n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='args.terminal_release_margin' and any(isinstance(x,ast.ImportFrom) and x.module=='margin_confirmed_position_release' for x in n.body)];assert len(release)==1;releasecode=compile(ast.fix_missing_locations(ast.Module(body=release,type_ignores=[])),str(S/'collect_paired_sorting.py'),'exec');parser_rows=[];settings={}
for label,args,expected in [('off',base,True),('on',base+['--terminal-directional-lead'],True),('missing_margin',[x for x in base if x!='--terminal-release-margin']+['--terminal-directional-lead'],False)]:
 try:
  with contextlib.redirect_stderr(io.StringIO()):ns,_=parser_namespace(S/'collect_paired_sorting.py',args,full=True)
  ok=True
 except (ValueError,SystemExit):ok=False
 assert ok==expected,label;parser_rows.append(dict(case=label,accepted=ok))
 if ok:settings[label]=ns
records=[]
for side,direction in [('left',1),('right',-1)]:
 size=(.15,.145,.04) if side=='left' else (.14,.09,.045);other=(.14,.09,.045) if side=='left' else (.15,.145,.04);initial=[.60,0.,.77];obstacle=[.39,0.,.77];quat=[0.,0.,0.,1.];plan=dict(required=False,initial_target_xyz=initial,obstacle_initial_xyz=obstacle,direction=direction,margin=.02)
 def new_state(label):
  env=dict(args=SimpleNamespace(**settings[label]),initial_top_selected=True,obstacle_size=other,frontal_plan={});exec(code,env);cls=env['top_cls'];assert cls is (TerminalLeadInitialTopState if label=='on' else InitialTopRouteState)
  state=cls(SimpleNamespace(plan=copy.deepcopy(plan)),side,size,**env['top_extra'],guarded_descent=True,continuous_drag=True,drag_step_m=.003,front_inset_fraction=1.,confirm_terminal_release=True);state.load.desired_n=5.;env['frontal_state']=state;exec(releasecode,env)
  state.update(initial,initial,obstacle,size[0]/2,other[0]/2,tip=(.6,0.,.90),quat=quat,obstacle_quat=quat,control_offset_local=(0.,0.,0.),load_n=0.,hand_obstacle_gap_m=.1)
  return state
 for mode,remaining,load,gap,moved in [('top_press',.0015,5.,.1,False),('top_push',.0015,5.,.1,False),('top_push',.004,5.,.1,False),('top_push',0.,5.,.1,False),('top_push',.0015,0.,.1,False),('top_push',.0015,5.,.001,False),('top_push',.0015,5.,.1,True)]:
  states=[new_state('off'),new_state('on')];target=[.6,direction*(.205-remaining),.77];tip=top_surface_point(target,quat,size,front_inset_fraction=1.);obs=obstacle.copy();obs[1]+=.02 if moved else 0.;outputs=[]
  for state in states:
   state.top_mode=mode;state.settled=2;state.load.filtered_n=5.;state.command=None if mode=='top_press' else (tip[0],tip[1]-direction*.001,tip[2]);state.lost_contact_steps=2 if load==0 else 0
   outputs.append(state.update(tip,target,obs,size[0]/2,other[0]/2,tip=tip,quat=quat,obstacle_quat=quat,control_offset_local=(0.,0.,0.),load_n=load,hand_obstacle_gap_m=gap))
  old,new=outputs;assert old['mode']==new['mode'];assert vars(states[0].load)==vars(states[1].load)
  changed='terminal_directional_lead_floor' in (new.get('clearance_feedback') or {})
  expected=remaining==.0015 and load>0 and gap>=.005 and not moved;assert changed==expected,(side,mode,remaining,load,gap,moved,new)
  if changed:
   assert new['target_xyz'][0]==old['target_xyz'][0] and new['target_xyz'][2]==old['target_xyz'][2]
   f=new['clearance_feedback'];assert abs(f['desired_support_xy'][1]-tip[1]-direction*.003)<1e-15
   # Revert exactly the declared Y fields and annotation; all other parent output must match.
   restored=copy.deepcopy(new);restored['target_xyz']=old['target_xyz'];f=restored['clearance_feedback'];del f['terminal_directional_lead_floor'];f['desired_support_xy'][1]=old['clearance_feedback']['desired_support_xy'][1];f['command_xy'][1]=old['clearance_feedback']['command_xy'][1];assert restored==old
  else:assert new==old
  records.append(dict(side=side,input_mode=mode,remaining_m=remaining,load_n=load,hand_gap_m=gap,other_moved=moved,output_mode=new['mode'],candidate_changed=changed,parent_pressure_and_guards_preserved=True))
 # Explicit off subclass equivalence and history replacement rejection.
 a=new_state('off');b=copy.deepcopy(a);b.__class__=TerminalLeadInitialTopState;b.terminal_directional_lead_enabled=False
 args=(initial,initial,obstacle,size[0]/2,other[0]/2);kwargs=dict(tip=(.6,0.,.9),quat=quat,obstacle_quat=quat,control_offset_local=(0.,0.,0.),load_n=0.,hand_obstacle_gap_m=.1)
 assert a.update(*args,**kwargs)==b.update(*args,**kwargs)
 c=new_state('on');c.clearance_feedback=object()
 try:c.update(*args,**kwargs);raise AssertionError('history replacement accepted')
 except ValueError as e:assert 'history' in str(e)
for n,h in prep['stage_sha256'].items():assert sha(S/n)==h,n
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,parser_rows=parser_rows,lifecycle_rows=records,default_off_identical=True,live_history_replacement_rejected=True,stage_sha256=prep['stage_sha256'],source_sha256={str(p):sha(p) for p in [Path(__file__),ROOT/'simfoundry/data/initial_top_route.py',ROOT/'simfoundry/data/top_contact_bypass.py',ROOT/'simfoundry/data/contact_load_control.py']},simulation_started=False,training_ready=False,remaining='Full feedback/history audit adapters and new physical experiment still required.')
dest=S/'CHECK.json';assert not dest.exists();dest.write_text(json.dumps(out,indent=2));print('passed',len(parser_rows),'parser cases;',len(records),'actual state-machine boundaries')
