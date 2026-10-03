"""All658 unissued applied proposals checked with archived real observations.
No action history is replaced, no simulator is advanced, and no new actual-action
or episode-success claim is made. Row checker receives each proposed output as
an explicitly UNISSUED fixture. All other bindings are original episode values.
"""
from pathlib import Path
import sys,json,hashlib,datetime,importlib.util,copy,ast
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W.parents[1])]
from audit_front_loaded_z_priority_applied_row import verify_applied
from audit_self_clearance_task_optimality import IndependentElbows
from audit_unloaded_wrist_prior_live import HandModel
from screen_bag_vertical_priority_geometry import Geometry
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def functions(path):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef)}
a=functions(W/'audit_front_loaded_z_priority_offline_geometry.py');b=functions(W/'front_loaded_z_priority_audit_geometry.py');assert all(a[k]==v for k,v in b.items()) and set(b)=={'evaluate','point','radii','sweep'}
P=W/'FRONT_LOADED_Z_PRIORITY_NATIVE_FULL10_REPLAY.json';report=json.loads(P.read_text());sources={str(P):sha(P)}
for p,h in report['source_sha256'].items():assert sha(p)==h,p
C=W/'front_initial_physical_r1';results=[];negative=[]
for case in report['episodes']:
 if not case['selected']:continue
 ep=next(C.glob('case_*/'+case['episode']));prov=json.loads((ep.parent/'provenance.json').read_text());snap=ep.parent/'source_snapshot'
 def source(name):
  keys=[n for n in prov['source_sha256'] if n.endswith('/'+name)];assert len(keys)==1;p=snap/keys[0];assert sha(p)==prov['source_sha256'][keys[0]];sources[str(p)]=sha(p);return p
 spec=importlib.util.spec_from_file_location('archived_bounded_original',source('bounded_ik.py'));solver=importlib.util.module_from_spec(spec);spec.loader.exec_module(solver)
 assert sha(source('g1_assets.py'))==sha(W.parents[1]/'simfoundry/robots/g1_assets.py')
 geom=Geometry(ep.parent);sources.update(geom.sources);hand=HandModel(source('g1_23dof_rev_1_0_u1_black.urdf'),source('g1_hand_support_vertices.json'));elbows=IndependentElbows(source('elbow_torso_hulls.json'),source('g1_23dof_rev_1_0_u1_black.urdf'))
 def read(name):sources[str(ep/name)]=sha(ep/name);return json.loads((ep/name).read_text())
 cs={r['step']:r for r in read('coordination.json')};fr={r['step']:r for r in read('frontal_bypass.json')['rows']};ex={r['step']:r for r in read('expert_control.json')};captures=read('front_initial_center.json');caps={r['step']:r for r in captures['rows']};packets=read('solved_contact_forces.json')['rows'];size=next(r['context']['scene']['other_size'] for r in captures['rows'] if r.get('context',{}).get('scene'))
 side='right' if 'push_box' in ep.name else 'left';key='box' if side=='right' else 'mailer';other='mailer' if key=='box' else 'box'
 with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
 with np.load(ep/'trace.npz') as z:xyz=z[key].copy();oxy=z[other].copy()
 with np.load(ep/'parcel_orientation.npz') as z:R=Rotation.from_quat(z[key]).as_matrix();OR=Rotation.from_quat(z[other]).as_matrix()
 selected=[r for r in case['rows'] if r['metadata']['applied']];rows=[]
 for i,r in enumerate(selected):
  t=r['step'];m=r['metadata'];args=dict(metadata=m,coordinate=cs[t],row=fr[t],expert=ex[t],current=q[t],previous_actual=u[t-1],output=np.asarray(m['output_command']),side=side,elbows=elbows,bounded_solver=solver.bounded_damped_step,hand=hand,geometry=geom,capture_row=caps[t],previous_packet=packets[t-1],target_xyz=xyz[t],target_rotation=R[t],other_xyz=oxy[t],other_rotation=OR[t],other_size=size)
  assert np.array_equal(m['context']['parent_command'],u[t]);rows.append(verify_applied(**args))
  if i in [0,len(selected)//2,len(selected)-1]:
   # Exercise the actual collector's additive coordinate format, without ever
   # pretending this isolated fixture is an executed candidate episode.
   updated=dict(args);updated['coordinate']=copy.deepcopy(cs[t]);updated['coordinate']['front_loaded_z_priority']=m;updated['coordinate']['unexecuted_parent_waist_target_rad']=cs[t]['waist_target_rad'];updated['coordinate']['waist_target_rad']=float(args['output'][0]);assert verify_applied(**updated)==rows[-1]
   mutations={}
   bad=dict(args);bad['output']=u[t];mutations['old_action_claimed_as_new']=bad
   bad=dict(args);bad['previous_actual']=args['output'];mutations['unissued_candidate_used_as_previous']=bad
   for name,field,index in [('wrong_other_position','other_xyz',0),('wrong_target_rotation','target_rotation',(0,0))]:
    bad=dict(args);bad[field]=args[field].copy();bad[field][index]+=.01;mutations[name]=bad
   bad=dict(args);bad['previous_packet']=copy.deepcopy(packets[t-1]);bad['previous_packet']['after_action_step']+=1;mutations['wrong_contact_packet_step']=bad
   bad=dict(args);bad['capture_row']=copy.deepcopy(caps[t]);bad['capture_row']['center_local_after'][0]+=.001;mutations['wrong_capture_center']=bad
   for name,change in [('fake_contact_load',lambda m:m['context'].__setitem__('observed_vertical_load_n',m['context']['observed_vertical_load_n']+.1)),('missing_guard',lambda m:m['candidate_final_guard'].__setitem__('accepted',False)),('fake_nominal_progress',lambda m:m.__setitem__('candidate_exact_support_delta_z_m',-.1)),('fake_path_gap',lambda m:m['nominal_hands_non_target_paths']['left'].__setitem__('minimum_certified_gap_lower_bound_m',10.))]:
    bad=dict(args);bad['metadata']=copy.deepcopy(m);change(bad['metadata']);mutations[name]=bad
   for name,bad in mutations.items():
    try:verify_applied(**bad)
    except (AssertionError,KeyError,ValueError):negative.append(dict(episode=ep.name,step=t,mutation=name,rejected=True))
    else:raise AssertionError(('negative accepted',ep.name,t,name))
  if i%100==0:print(ep.name,i,len(selected),flush=True)
 results.append(dict(episode=ep.name,frames=len(rows),records=rows))
 for name in ['raw.npz','trace.npz','parcel_orientation.npz']:sources[str(ep/name)]=sha(ep/name)
for name in ['check_front_loaded_z_priority_applied_rows.py','audit_front_loaded_z_priority_applied_row.py','audit_front_loaded_z_priority_parent.py','front_loaded_z_priority_audit_geometry.py','audit_front_loaded_z_priority_offline_geometry.py','support_vertex_stationarity.py','audit_self_clearance_task_optimality.py','audit_unloaded_wrist_prior_live.py','screen_bag_vertical_priority_geometry.py']:sources[str(W/name)]=sha(W/name)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,episodes=results,negative_cases=negative,source_sha256=sources,geometry_ast_unchanged=True,physical_started=False,new_episode_audit_ready=False,training_ready=False)
p=W/'FRONT_LOADED_Z_PRIORITY_APPLIED_ROW_CHECK.json'
with p.open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,unissued_one_step_proposals=sum(r['frames'] for r in results),negative_cases=len(negative),maximum_stationarity=max(x['stationarity_residual'] for e in results for x in e['records'])),indent=2))
