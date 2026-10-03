"""Real archived-history tests of the original-command row audit.
All records are independent one-step contexts, not an invented candidate rollout.
Negative cases deliberately alter one binding. No simulator/action emission.
"""
from pathlib import Path
import sys,json,hashlib,datetime,importlib.util,copy
import numpy as np
W=Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W.parents[1])]
from audit_front_loaded_z_priority_parent import verify_parent
from audit_self_clearance_task_optimality import IndependentElbows
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
P=W/'FRONT_LOADED_Z_PRIORITY_NATIVE_FULL10_REPLAY.json';report=json.loads(P.read_text());sources={str(P):sha(P)}
for p,h in report['source_sha256'].items():assert sha(p)==h,p
C=W/'front_initial_physical_r1';results=[];negatives=[]
for case in report['episodes']:
 if not case['selected']:continue
 ep=next(C.glob('case_*/'+case['episode']));provenance=json.loads((ep.parent/'provenance.json').read_text());snap=ep.parent/'source_snapshot'
 def source(name):
  found=[n for n in provenance['source_sha256'] if n.endswith('/'+name)];assert len(found)==1
  p=snap/found[0];assert sha(p)==provenance['source_sha256'][found[0]];sources[str(p)]=sha(p);return p
 solverpath=source('bounded_ik.py');spec=importlib.util.spec_from_file_location('archived_original_bounded',solverpath);solver=importlib.util.module_from_spec(spec);spec.loader.exec_module(solver)
 assert sha(source('g1_assets.py'))==sha(W.parents[1]/'simfoundry/robots/g1_assets.py')
 geom=IndependentElbows(source('elbow_torso_hulls.json'),source('g1_23dof_rev_1_0_u1_black.urdf'))
 cs={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};fr={r['step']:r for r in json.loads((ep/'frontal_bypass.json').read_text())['rows']};ex={r['step']:r for r in json.loads((ep/'expert_control.json').read_text())}
 with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
 side='right' if 'push_box' in ep.name else 'left';records=[]
 selected=[r for r in case['rows'] if 'target_rotation' in r['metadata']['context']]
 for index,r in enumerate(selected):
  t=r['step'];meta=r['metadata'];context=meta['context']
  for key,value in [('current',q[t]),('previous',u[t-1]),('parent_command',u[t])]:assert np.array_equal(np.asarray(context[key]),value)
  args=dict(coordinate=cs[t],row=fr[t],expert=ex[t],current=q[t],previous_actual=u[t-1],parent=np.asarray(context['parent_command']),side=side,elbows=geom,bounded_solver=solver.bounded_damped_step)
  result=verify_parent(**args);records.append(result)
  if index in [0,len(selected)//2,len(selected)-1]:
   mutations={}
   for name,key in [('wrong_actual_previous','previous_actual'),('wrong_actual_current','current'),('wrong_original_command','parent')]:
    bad=dict(args);bad[key]=args[key].copy();bad[key][0]=np.float32(bad[key][0]+.001);mutations[name]=bad
   for name,field in [('logged_previous_mismatch','previous'),('task_error_mismatch','error'),('task_damping_mismatch','damping')]:
    bad=dict(args);bad['coordinate']=copy.deepcopy(cs[t]);bad['coordinate']['task_inputs'][field][0]+=.001;mutations[name]=bad
   bad=dict(args);bad['coordinate']=copy.deepcopy(cs[t]);bad['coordinate']['task_inputs']['current'][0]=float('nan');mutations['nonfinite_logged_current']=bad
   bad=dict(args);bad['row']=copy.deepcopy(fr[t]);bad['row']['step']+=1;mutations['wrong_step']=bad
   if meta['applied']:bad=dict(args);bad['parent']=np.asarray(meta['output_command']);mutations['unissued_candidate_as_original_parent']=bad
   for name,bad in mutations.items():
    try:verify_parent(**bad)
    except (AssertionError,ValueError,KeyError):negatives.append(dict(episode=ep.name,step=t,mutation=name,rejected=True))
    else:raise AssertionError(('negative accepted',ep.name,t,name))
  if index%150==0:print(ep.name,index,len(selected),flush=True)
 results.append(dict(episode=ep.name,frames=len(records),applied_candidate_contexts=sum(r['metadata']['applied'] for r in selected),original_nonlinear_overrides=sum(r['original_task_override'] for r in records),records=records))
 for name in ['raw.npz','coordination.json','frontal_bypass.json','expert_control.json']:
  p=ep/name;sources[str(p)]=sha(p)
for name in ['audit_front_loaded_z_priority_parent.py','check_front_loaded_z_priority_parent.py','audit_rear_coupled_execution_live.py','audit_self_clearance_task_optimality.py','support_vertex_stationarity.py']:sources[str(W/name)]=sha(W/name)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,episodes=results,negative_cases=negatives,source_sha256=sources,physical_started=False,new_episode_audit_ready=False,training_ready=False)
p=W/'FRONT_LOADED_Z_PRIORITY_PARENT_RECONSTRUCTION_CHECK.json'
with p.open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,frames=sum(r['frames'] for r in results),negative_cases=len(negatives),episodes=[{k:v for k,v in r.items() if k!='records'} for r in results]),indent=2))
