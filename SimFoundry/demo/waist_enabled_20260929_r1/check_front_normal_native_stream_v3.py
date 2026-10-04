"""Execute actual isolated collector correction -> final guard -> history nodes.
All10 archived conditions, off/on on v3. Prepared pressure states test execution
plumbing; real state reconstruction is covered separately by prefix_r3/r4.
No physics, observations and original parent history held fixed.
"""
from pathlib import Path
from types import SimpleNamespace as NS
import ast,copy,datetime,hashlib,inspect,json,os,sys
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_normal_nondegradation_v3';D=W/'front_normal_native_stream_r3';D.mkdir(exist_ok=False);sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from front_initial_center_top_contact import TopContactBypassState
from recontact_scene import RecontactScene
from front_normal_nondegradation_runtime_candidate_v1 import FrontNormalNondegradation
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text());tree=ast.parse((S/'collect_paired_sorting.py').read_text());new=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='args.front_normal_nondegradation' and 'normal_command, normal_record' in ast.unparse(n));final=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='clearance_guard is not None' and 'final_clearance' in ast.unparse(n));previous=next(n for n in ast.walk(tree) if isinstance(n,ast.Assign) and ast.unparse(n)=='previous = action.copy()' and n.lineno>final.lineno);assert new.lineno<final.lineno<previous.lineno
recovery=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and 'commit_original_recovery(normal_record' in ast.unparse(n) and isinstance(n.test,ast.BoolOp));assert final.lineno<recovery.lineno<previous.lineno
loop=ast.For(target=ast.Name(id='_once',ctx=ast.Store()),iter=ast.List(elts=[ast.Constant(0)],ctx=ast.Load()),body=[new,final,recovery,previous,ast.Assign(targets=[ast.Name(id='reached',ctx=ast.Store())],value=ast.Constant(True))],orelse=[]);program=compile(ast.fix_missing_locations(ast.Module(body=[loop],type_ignores=[])),'<actual collector correction final guard history>','exec')
class Tensor:
 def __init__(self,x):self.x=np.asarray(x);self.torch=self
 def __getitem__(self,k):return Tensor(self.x[k])
 def detach(self):return self
 def cpu(self):return self
 def numpy(self):return self.x
class NoProposal:
 def refine(self,**kw):return None,dict(applied=False,requires_stop=True,output_command=None,reason='injected_no_proposal')
class Unsafe:
 def refine(self,**kw):
  x=np.array(kw['parent_command']);x[0]=10.
  return x,dict(applied=True,requires_stop=False,output_command=x.tolist(),reason='injected_unsafe_final')
G=ClearanceGuard(ROOT,S);controller=FrontNormalNondegradation(G,ROOT,S,enabled=True);assert Path(inspect.getfile(type(controller))).resolve()==S/'front_normal_nondegradation_runtime_candidate_v1.py';census=read(W/'front_cross_track_full_stream_probe_r1/CENSUS.json');reference=read(W/'front_normal_runtime_stream_r1/RESULT.json');want={e['episode']:{r['step']:r for r in e['rows']} for e in reference['episodes']};episodes=[];negative=[];calls=0
for p,h in reference['source_sha256'].items():assert sha(p)==h,p
for item in census['episodes']:
 ep=Path(item['episode']);wait=item['wait'];coords={} if wait else {r['step']:r for r in read(ep/'coordination.json')};fr={} if wait else {r['step']:r for r in read(ep/'frontal_bypass.json')['rows']};trs=read(ep/'joint_transport_clearance.json')['rows'];rows=[]
 with np.load(ep/'raw.npz') as z:q=z['q'].copy();u=z['action'].copy()
 for t,tr in enumerate(trs):
  tc=tr['collector_context'];sc=tc['scene'];scene=None if sc is None else RecontactScene(G,sc['side'],sc['target_xyz'],sc['target_quat'],sc['core_size'],sc['other_xyz'],sc['other_quat'],sc['other_size']);original_prev=u[t-1].copy() if t else np.zeros(23,np.float32)
  def environment(enabled,actor=None):
   state=TopContactBypassState(None,'right',(.15,.145,.04));state.top_mode='top_push';state.recontacts=fr[t].get('recontacts',0) if t in fr else 0;state.lost_contact_steps=1;state.load.bias_m=-.006
   return dict(frontal_state=state,args=NS(front_normal_nondegradation=enabled,peak_load_bias_guard=True),peak_load_frame_log=[dict(step=t,top_mode=state.top_mode,bias_m=state.load.bias_m,filtered_n=state.load.filtered_n,pressure_update_count=len(state.load.updates))],normal_planning_controller=actor or controller,normal_planning_log=[],transport_selected=tr['selected'],transport_row=copy.deepcopy(fr.get(t)),transport_scene=scene,transport_current=q[t,12:23].copy(),transport_previous_q=None if not t else q[t-1,12:23].copy(),transport_decay=tc['decay'],side=tc['side'],step=t,coordination_log=[] if t not in coords else [copy.deepcopy(coords[t])],action=u[t].copy(),previous=original_prev.copy(),default=np.zeros(23,np.float32),robot=NS(data=NS(joint_pos=Tensor(q[t][None]))),ordered_ids=list(range(23)),clearance_guard=G,clearance_rows=[],clearance_failure=None,reached=False,np=np)
  for enabled in [False,True]:
   e=environment(enabled);exec(program,e);assert e['reached'] and e['clearance_failure'] is None and e['clearance_rows'][-1]['accepted'],(ep.name,t,enabled)
   expected=want[ep.name][t]['output_command'] if enabled else u[t,12:23];np.testing.assert_array_equal(e['action'][12:23],expected);np.testing.assert_array_equal(e['previous'],e['action']);np.testing.assert_array_equal(e['action'][:12],u[t,:12])
   if enabled:
    r=e['normal_planning_log'][-1];assert r['applied']==want[ep.name][t]['applied'] and not r['requires_stop']
    if r['applied']:
     assert e['coordination_log'][-1]['waist_target_rad']==float(expected[0]);assert e['coordination_log'][-1]['normal_planning_unexecuted_parent_waist_target_rad']==coords[t]['waist_target_rad']
     if r['requires_recovery']:
      assert r['recovery_committed'] and e['frontal_state'].top_mode=='top_lift' and e['frontal_state'].recontacts==fr[t]['recontacts']+1 and e['frontal_state'].load.bias_m==0
      pressure=e['peak_load_frame_log'][-1];assert pressure['top_mode']=='top_lift' and pressure['bias_m']==0 and pressure['before_final_recovery']['top_mode']=='top_push' and pressure['before_final_recovery']['bias_m']==-.006
      assert pressure['filtered_n']==pressure['before_final_recovery']['filtered_n'] and pressure['final_recovery_transition']==r['recovery_transition']
     else:assert r['certificate']['passed'] and r['certificate']['certificate']['stationarity_residual']==want[ep.name][t]['stationarity']
   else:assert e['normal_planning_log']==[]
   calls+=1
  rows.append(dict(step=t,applied=want[ep.name][t]['applied'],recovery_committed=want[ep.name][t]['requires_recovery'],off_on_actions_exact=True,history_and_waist_checked=True))
  if ep.name=='layout_840020_push_box_to_bin' and t==1009:
   for label,actor in [('no_proposal',NoProposal()),('unsafe_final',Unsafe())]:
    e=environment(True,actor);exec(program,e);assert not e['reached'];np.testing.assert_array_equal(e['previous'],original_prev)
    if label=='no_proposal':assert e['clearance_failure']['reason']=='normal_planning_no_verified_command' and not e['clearance_rows'];np.testing.assert_array_equal(e['action'],u[t])
    else:assert e['clearance_failure']['reason']=='final_override_not_verified'
    negative.append(dict(case=label,stopped_before_history=True,no_physics_executed=True));print(json.dumps(negative[-1]),flush=True)
  if t%200==0:
   status=dict(status='running',pid=os.getpid(),episode=ep.name,step=t,native_calls=calls,training_ready=False);(D/'STATUS.json').write_text(json.dumps(status,indent=2));print(json.dumps(status),flush=True)
 episodes.append(dict(episode=ep.name,frames=len(rows),rows=rows))
sources={str(p):sha(p) for p in [Path(__file__),W/'front_normal_runtime_stream_r1/RESULT.json',W/'front_cross_track_full_stream_probe_r1/CENSUS.json',W/'front_normal_preparation_r3/STAGE_PREPARATION.json']}
for p in S.iterdir():
 if p.is_file():sources[str(p)]=sha(p)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,native_calls=calls,frames=sum(e['frames'] for e in episodes),applied=sum(r['applied'] for e in episodes for r in e['rows']),episodes=episodes,negative_cases=negative,recovery_commits=sum(r['recovery_committed'] for e in episodes for r in e['rows']),native_statement_lines=[new.lineno,final.lineno,recovery.lineno,previous.lineno],source_sha256=sources,physics_started=False,training_ready=False,remaining=['Whole saved stream/source/actual control-auditor updates and new incomplete-stop lifecycle before physical launch.','Static candidate history is not recursive physical evidence; no whole task success claim.'])
assert report['frames']==9740 and calls==19480 and report['applied']==34 and len(negative)==2 and report['recovery_commits']==2
with (D/'RESULT.json').open('x') as f:json.dump(report,f,indent=2)
(D/'STATUS.json').write_text(json.dumps(dict(status='complete',passed=True,native_calls=calls,frames=9740,applied=34),indent=2));print(json.dumps(dict(passed=True,native_calls=calls,frames=9740,applied=34)),flush=True)
