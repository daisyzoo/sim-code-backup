"""Execute new collector AST hooks on original histories and labelled synthetic states.
No simulator, changed-trajectory claim or training admission.
"""
from pathlib import Path
from types import SimpleNamespace
from copy import deepcopy
import ast,contextlib,datetime,hashlib,io,json,sys,traceback
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_bag_preload_hold_v1';R=W/'front_effective_height_physical_r1';D=W/'front_bag_preload_stage_native_r2';D.mkdir(exist_ok=False)
sys.path[:0]=[str(S),str(W),str(ROOT)]
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
sources={str(p):sha(p) for p in [Path(__file__),S/'collect_paired_sorting.py',S/'front_bag_preload_waypoint_candidate_v1.py',R/'PROTOCOL.json']}
try:
 from prepare_closed_peak_trial import parser_namespace
 protocol=read(R/'PROTOCOL.json');parser_checks=[]
 for c in protocol['plan']['commands']:
  old,_=parser_namespace(Path(protocol['plan']['collector']),c['args'],full=True)
  off,_=parser_namespace(S/'collect_paired_sorting.py',c['args'],full=True)
  on,_=parser_namespace(S/'collect_paired_sorting.py',c['args']+['--front-bag-preload-hold'],full=True)
  assert off==dict(old,front_bag_preload_hold=False) and on==dict(old,front_bag_preload_hold=True)
  parser_checks.append(dict(layout_id=c['layout_id'],tasks=c['tasks'],original_settings_exact=True))
 negatives=[];cli=protocol['plan']['commands'][0]['args']+['--front-bag-preload-hold']
 for flag in ['--front-initial-center-landing','--front-recontact-center-landing','--peak-load-bias-guard','--front-loaded-z-quarter','--joint-transport-clearance','--joint-transport-effective-quarter-height','--front-cop-route-axis','--self-clearance-task-ik']:
  bad=cli.copy();bad.remove(flag)
  try:
   with contextlib.redirect_stderr(io.StringIO()):parser_namespace(S/'collect_paired_sorting.py',bad,full=True)
  except (ValueError,SystemExit):negatives.append(flag)
  else:raise AssertionError('Missing prerequisite accepted: '+flag)
 tree=ast.parse((S/'collect_paired_sorting.py').read_text());blocks=[n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='args.front_bag_preload_hold']
 assert len(blocks)==8,len(blocks)
 def block(fragment):
  found=[n for n in blocks if fragment in ast.unparse(n)];assert len(found)==1,(fragment,len(found));return found[0]
 def execute(n,ctx):
  # A one-iteration loop retains collector break semantics for rejected proposal.
  body=[deepcopy(n),ast.Assign(targets=[ast.Name(id='_continued',ctx=ast.Store())],value=ast.Constant(True))]
  module=ast.Module(body=[ast.For(target=ast.Name(id='_hook_iteration',ctx=ast.Store()),iter=ast.List(elts=[ast.Constant(0)],ctx=ast.Load()),body=body,orelse=[])],type_ignores=[])
  ctx['_continued']=False;exec(compile(ast.fix_missing_locations(module),str(S/'collect_paired_sorting.py'),'exec'),ctx);return ctx['_continued']
 init=block('preload_controller = FrontBagPreload');reset=block('preload_proposal = None');target=block('preload_controller.propose(');commit=block('commit_after_final_guard(');save=block('front_bag_preload_hold.json');meta=block("episode.collect_meta[");archive=block('paths.append(')
 # Exact hook ordering, and altered goal feeds original expert before its solve.
 text=(S/'collect_paired_sorting.py').read_text()
 assert target.lineno < next(n.lineno for n in ast.walk(tree) if isinstance(n,ast.Assign) and 'expert.last_target_xyz' in ast.unparse(n) and ast.unparse(n.value)=="waypoint['target_xyz']")
 assert text.index('preload_controller.commit_after_final_guard(')>text.index("if not final_clearance['accepted']:")
 assert text.index('preload_controller.commit_after_final_guard(')<text.index('previous = action.copy()')
 # Off hooks must neither read nonexistent runtime variables nor create files.
 for b in [init,reset,target,commit,save,meta,archive]:
  ctx={'args':SimpleNamespace(front_bag_preload_hold=False)};before=set(ctx);assert execute(b,ctx);assert set(ctx)-before<={'__builtins__','_continued','_hook_iteration'}
 counts=[];entries=[]
 class Cop:
  def __init__(self):self.resets=0
  def reset(self):self.resets+=1
 def state(row,side):return SimpleNamespace(side=side,top_mode=row['mode'],recontacts=row.get('recontacts',0),command=tuple(row['target_xyz']),last_emitted_xy=tuple(row['target_xyz'][:2]),load=SimpleNamespace(desired_n=5.,min_bias_m=-.006,filtered_n=row.get('contact_load',{}).get('filtered_vertical_load_n',0.),bias_m=row.get('contact_load',{}).get('stored_z_bias_m',0.)),cop_slip=Cop())
 for c in protocol['plan']['commands']:
  for task in c['tasks']:
   ep=R/f"case_{c['layout_id']}"/f"layout_{c['layout_id']}_{task}";wait=task=='wait_no_package';side='left' if 'nudge_mailer' in task else 'right';fr=read(ep/'frontal_bypass.json') if not wait else dict(plan={},rows=[])
   with np.load(ep/'raw.npz',allow_pickle=False) as z:actions=z['action'].copy()
   guards={r['step']:r for r in read(ep/'self_clearance.json')['rows'] if r['phase']=='final_command'};rows={r['step']:r for r in fr['rows']}
   ctx=dict(args=SimpleNamespace(front_bag_preload_hold=True),np=np,json=json,side=side,frontal_plan=fr['plan'],clearance_guard=object(),default=np.zeros(23,np.float32));execute(init,ctx)
   selected=side=='left' and bool(fr['plan'].get('front_route_selected'));limit=len(actions);changed=False
   for t in range(limit):
    ctx.update(step=t,action=actions[t].copy(),final_clearance=guards[t],frontal_state=None);execute(reset,ctx)
    if t in rows:
     row=deepcopy(rows[t]);ctx.update(waypoint={k:v for k,v in row.items() if k!='step'},frontal_state=state(row,side));old_state=deepcopy(ctx['frontal_state'].__dict__);assert execute(target,ctx)
     assert ctx['frontal_state'].command==old_state['command'] and ctx['frontal_state'].load.__dict__==old_state['load'].__dict__
     if ctx['preload_proposal']['record']['kind']=='hold':
      changed=True;entries.append(dict(episode=ep.name,step=t,proposal=ctx['preload_proposal'],scope='target proposal only; original command not admitted for changed target'))
      # Original saved command is NOT a solution of the changed target. Stop replay.
      break
     assert ctx['waypoint']['target_xyz']==row['target_xyz']
    assert execute(commit,ctx)
   assert changed==selected
   if not changed:
    assert len(ctx['preload_waypoint_log'])==len(actions)
    folder=D/ep.name;folder.mkdir();ctx.update(folder=folder,qs=actions,episode=SimpleNamespace(collect_meta={}),STAGE=S,paths=[])
    for b in [save,meta,archive]:assert execute(b,ctx)
    saved=read(folder/'front_bag_preload_hold.json');assert len(saved['rows'])==len(actions) and saved['pending_unexecuted_proposal'] is None
    assert ctx['paths']==[S/'front_bag_preload_waypoint_candidate_v1.py']
    assert ctx['episode'].collect_meta['front_bag_preload_hold']['applied_hold_frames']==0
   counts.append(dict(episode=ep.name,admitted_original_unchanged_frames=len(ctx['preload_waypoint_log']),changed_prefix_cutoff=changed))
   for n in ['raw.npz','self_clearance.json']+([] if wait else ['frontal_bypass.json']):sources[str(ep/n)]=sha(ep/n)
 # Seven independent observed entry hooks, not a changed history replay.
 fr=read(R/'case_840023/layout_840023_nudge_mailer_to_bin/frontal_bypass.json');previous_mode=None;all_entries=[]
 for row in fr['rows']:
  if row['mode']=='top_push' and previous_mode!='top_push':
   ctx=dict(args=SimpleNamespace(front_bag_preload_hold=True),np=np,json=json,side='left',frontal_plan=fr['plan'],step=row['step'],waypoint={k:deepcopy(v) for k,v in row.items() if k!='step'},frontal_state=state(row,'left'));execute(init,ctx);execute(reset,ctx);assert execute(target,ctx);assert ctx['preload_proposal']['record']['kind']=='hold';all_entries.append(row['step'])
  previous_mode=row['mode']
 assert len(all_entries)==7
 # Synthetic guard/force contexts test transaction and saved stop; not motion proof.
 original=next(r for r in fr['rows'] if r['mode']=='top_push');synthetic=[]
 for load,max_frames in [(4.5,4),(1.,25)]:
  ctx=dict(args=SimpleNamespace(front_bag_preload_hold=True),np=np,json=json,side='left',frontal_plan=fr['plan'],clearance_guard=object(),default=np.zeros(23,np.float32),action=np.zeros(23,np.float32),final_clearance=dict(accepted=True,command=[0.]*11));execute(init,ctx);prev=original['cop_slip_following']['previous_command_xy'];resets=0
  for k in range(max_frames):
   row=deepcopy(original);row['step']+=k;row['contact_load'].update(observed_vertical_load_n=load,filtered_vertical_load_n=load);row['cop_slip_following']['previous_command_xy']=list(prev);row['target_xyz'][:2]=(np.asarray(prev)+[.001,.001]).tolist();obj=state(row,'left');ctx.update(step=row['step'],waypoint={k:v for k,v in row.items() if k!='step'},frontal_state=obj);execute(reset,ctx)
   if not execute(target,ctx):
    assert load==1. and k==24 and ctx['clearance_failure']['reason']=='preload_budget_exhausted_without_admitted_load';break
   pressure=deepcopy(obj.load.__dict__);assert execute(commit,ctx);assert obj.load.__dict__==pressure;prev=ctx['waypoint']['target_xyz'][:2];resets+=obj.cop_slip.resets
  folder=D/f'synthetic_load_{load}';folder.mkdir();ctx.update(folder=folder,qs=[None]*len(ctx['preload_waypoint_log']));execute(save,ctx);saved=read(folder/'front_bag_preload_hold.json')
  assert len(saved['rows'])==(4 if load==4.5 else 24) and resets==(1 if load==4.5 else 0)
  assert (saved['stop'] is not None)==(load==1.) and (saved['pending_unexecuted_proposal'] is not None)==(load==1.)
  synthetic.append(dict(load_fixture_n=load,admitted_frames=len(saved['rows']),cop_resets=resets,stop_saved=saved['stop'] is not None))
 result=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,parser_commands=parser_checks,missing_prerequisites_rejected=negatives,defaultoff_hooks_no_effect=True,unchanged_frames=counts,first_changed_target_prefix=entries,independent_entry_steps=all_entries,synthetic_bookkeeping=synthetic,new_physics=False,changed_commands_verified_here=False,physical_launch_allowed=False,training_ready=False,source_sha256=sources)
 (D/'RESULT.json').write_text(json.dumps(result,indent=2));print(json.dumps(dict(passed=True,parser_commands=len(parser_checks),negative_parameters=len(negatives),unchanged_admitted_frames=sum(r['admitted_original_unchanged_frames'] for r in counts),entry_steps=all_entries,synthetic=synthetic)))
except BaseException:
 (D/'FAILURE.log').write_text(traceback.format_exc());(D/'RESULT.json').write_text(json.dumps(dict(passed=False,training_ready=False,new_physics=False,traceback=traceback.format_exc()),indent=2));raise
