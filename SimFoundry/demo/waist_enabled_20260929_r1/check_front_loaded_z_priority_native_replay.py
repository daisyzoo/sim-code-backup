"""Replay the staged runtime refinement on all original10 archived episodes.
This does not advance a simulator or chain candidate actions. Parent observed
state and previous action are retained at every point. Every applied proposal is
checked by the separate archived URDF model and original stationarity certificate.
Unselected/wait/zero and every fallback must return exact original float32 action.
"""
from pathlib import Path
import sys,json,datetime,hashlib,ast
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_loaded_z_priority';sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from front_loaded_z_priority import FrontLoadedZPriority
from screen_bag_vertical_priority_geometry import Geometry
from audit_unloaded_wrist_prior_live import HandModel
from audit_self_clearance_task_optimality import IndependentElbows
from support_vertex_stationarity import certificate
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();C=W/'front_initial_physical_r1';protocol=json.loads((C/'PROTOCOL.json').read_text());sources={str(C/'PROTOCOL.json'):sha(C/'PROTOCOL.json')};guard=ClearanceGuard(ROOT,S);controller=FrontLoadedZPriority(guard);episodes=[]
auditfile=W/'audit_front_loaded_z_priority_offline_geometry.py';tree=ast.parse(auditfile.read_text());functions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['evaluate','point','radii','sweep']];ns=dict(np=np,certificate=certificate);exec(compile(ast.Module(body=functions,type_ignores=[]),str(auditfile),'exec'),ns)
offline=json.loads((W/'FRONT_LOADED_Z_PRIORITY_SELECTION_SCREEN.json').read_text());off={e['episode']:{r['step']:r for r in e['rows']} for e in offline['episodes']}
for item in protocol['plan']['commands']:
 for task in item['tasks']:
  ep=C/f"case_{item['layout_id']}"/f"layout_{item['layout_id']}_{task}";wait=item['wait'];cs={r['step']:r for r in json.loads((ep/'coordination.json').read_text())} if (ep/'coordination.json').exists() else {};fr=json.loads((ep/'frontal_bypass.json').read_text()) if not wait else dict(rows=[]);frs={r['step']:r for r in fr['rows']};front=json.loads((ep/'front_initial_center.json').read_text());capture={r['step']:r for r in front['rows']};side='right' if 'push_box' in task else 'left';key='box' if side=='right' else 'mailer';other='mailer' if key=='box' else 'box';records=[];rows=[]
  with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
  assert len(q)==(70 if wait else 1200)
  scene={}
  if front['selected']:
   first=next(r['context']['scene'] for r in front['rows'] if r.get('context',{}).get('scene'));g=Geometry(ep.parent);sources.update(g.sources)
   def archived(name):return next(Path(p) for p in g.sources if p.endswith('/'+name))
   hand=HandModel(archived('g1_23dof_rev_1_0_u1_black.urdf'),archived('g1_hand_support_vertices.json'));elbows=IndependentElbows(archived('elbow_torso_hulls.json'),archived('g1_23dof_rev_1_0_u1_black.urdf'))
   with np.load(ep/'trace.npz') as z:xyz=z[other].copy()
   with np.load(ep/'parcel_orientation.npz') as z:rot=Rotation.from_quat(z[key]).as_matrix();orot=Rotation.from_quat(z[other]).as_matrix()
  for t in range(len(q)):
   selected=bool(front['selected'] and capture.get(t,{}).get('center_local_after') is not None);c=dict(cs[t],front_loaded_z_priority_side=side) if t in cs else None;row=frs.get(t);prev=u[t-1] if t else np.zeros(11)
   if selected:scene=dict(target_rotation=rot[t],other_xyz=xyz[t],other_rotation=orot[t],other_size=first['other_size'])
   out,meta=controller.refine(step=t,selected=selected,row=row,coordinate=c,current=q[t],previous=prev,parent_command=u[t],**scene)
   assert np.array_equal(out,np.asarray(meta['output_command']))
   if not meta['applied']:assert np.array_equal(out,u[t])
   else:
    assert selected and row['mode']=='top_push' and row['contact_load']['observed_vertical_load_n']>=.3
    ev=ns['evaluate'](c['task_inputs'],c,out,u[t],hand,elbows,g,side);assert ev['passed'],(ep.name,t,ev)
    center=np.array(c['active_support_reference']['center_local']);obs=ns['point'](hand,q[t],side,rot[t,:,2],center);parent_delta=ns['point'](hand,u[t],side,rot[t,:,2],center)-obs;new_delta=ns['point'](hand,out,side,rot[t,:,2],center)-obs;request=c['task_inputs']['error'][5 if side=='right' else 2];assert new_delta[2]<0 and abs(new_delta[2]-request)<abs(parent_delta[2]-request)
    np.testing.assert_allclose(new_delta[2],meta['candidate_exact_support_delta_z_m'],atol=2e-12,rtol=0)
    paths={s:ns['sweep'](g,hand,q[t],out,s,xyz[t],orot[t],np.array(meta['context']['conservative_other_size'])) for s in ['left','right']};assert all(p['certified'] for p in paths.values())
    for s in paths:np.testing.assert_allclose(paths[s]['minimum_certified_gap_lower_bound_m'],meta['nominal_hands_non_target_paths'][s]['minimum_certified_gap_lower_bound_m'],atol=2e-12,rtol=0)
    records.append(dict(step=t,independent_stationarity_residual=ev['certificate']['stationarity_residual'],independent_nominal_support_delta_z_m=float(new_delta[2]),nominal_path_minimum_gap_lower_bound_m=min(p['minimum_certified_gap_lower_bound_m'] for p in paths.values())))
   comparable=off.get(ep.name,{}).get(t);rows.append(dict(step=t,applied=meta['applied'],reason=meta['reason'],offline_selection_equal=None if comparable is None else meta['applied']==comparable['candidate_selected'],metadata=meta))
   if t%200==0:print(ep.name,t,len(q),flush=True)
  reasons={name:sum(r['reason']==name for r in rows) for name in sorted({r['reason'] for r in rows})};episodes.append(dict(episode=ep.name,wait=wait,frames=len(q),selected=front['selected'],applied=sum(r['applied'] for r in rows),reason_counts=reasons,offline_selection_disagreements=[r['step'] for r in rows if r['offline_selection_equal'] is False],independent_checks=records,rows=rows))
  for name in ['raw.npz','coordination.json','frontal_bypass.json','front_initial_center.json','trace.npz','parcel_orientation.npz']:
   if (ep/name).exists():sources[str(ep/name)]=sha(ep/name)
for p in S.iterdir():
 if p.is_file() and (p.suffix=='.py' or p.name in ['elbow_torso_hulls.json','causal_response_parameters.json']):sources[str(p)]=sha(p)
for p in [Path(__file__),auditfile,W/'screen_bag_vertical_priority_geometry.py',W/'audit_unloaded_wrist_prior_live.py',W/'audit_self_clearance_task_optimality.py',W/'support_vertex_stationarity.py',W/'FRONT_LOADED_Z_PRIORITY_SELECTION_SCREEN.json']:sources[str(p)]=sha(p)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,conditions=10,frames=sum(e['frames'] for e in episodes),episodes=episodes,source_sha256=sources,physical_started=False,collector_branches_verified=False,training_ready=False)
p=W/'FRONT_LOADED_Z_PRIORITY_NATIVE_FULL10_REPLAY.json'
with p.open('x') as f:json.dump(out,f,indent=2)
print(json.dumps([{k:v for k,v in e.items() if k not in ['rows','independent_checks']} for e in episodes],indent=2))
