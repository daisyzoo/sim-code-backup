"""Real-record default/guard preservation and independent output checks; no physics."""
from pathlib import Path
import sys,json,hashlib,importlib.util,time,copy
from types import SimpleNamespace
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(w),str(repo),str(w/'staged_joint_edge_probe')]
import joint_edge_command as helper
from audit_rear_coupled_execution_live import inspect
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
from simfoundry.data.top_contact_bypass import rotation_xyzw
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();r=w/'rear_joint_xy_groups_r1';reports=[];default_calls=0;protected_calls=0;rejects=0;last=None
for cid,task in [(840001,'push_box_to_bin'),(840004,'nudge_mailer_to_bin'),(840001,'nudge_mailer_to_bin'),(840004,'push_box_to_bin')]:
 ep=r/f'case_{cid}'/f'layout_{cid}_{task}';fr=json.loads((ep/'frontal_bypass.json').read_text());enabled=bool(fr['plan'].get('rear_joint_xy_progress',{}).get('enabled'));coords={x['step']:x for x in json.loads((ep/'coordination.json').read_text())};prov=json.loads((ep.parent/'provenance.json').read_text())
 if enabled:
  a=inspect(ep);assert a['passed'] and a['complete_push_coverage'];raw_audit=json.loads((ep/'REAR_JOINT_XY_LIVE_AUDIT.json').read_text());assert raw_audit['passed']
  for n,h in raw_audit['source_sha256'].items():assert sha(ep/n)==h
  name=next(n for n in prov['source_sha256'] if n.endswith('/articulated_hand_geometry.py'));gp=ep.parent/'source_snapshot'/name;assert sha(gp)==prov['source_sha256'][name];spec=importlib.util.spec_from_file_location('probe_fk_'+str(cid),gp);gm=importlib.util.module_from_spec(spec);spec.loader.exec_module(gm);model=gm.ArticulatedHandGeometry(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json')
  for asset in ['third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf','assets/robots/g1_hand_support_vertices.json','simfoundry/calibration/sorting_station.py','simfoundry/data/hand_obstacle_clearance.py']:assert sha(repo/asset)==prov['source_sha256'][asset]
 with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(np.float32);u=z['action'][:,12:23].astype(np.float32)
 key='box' if 'push_box' in task else 'mailer';side='right' if key=='box' else 'left';direction=-1 if side=='right' else 1;ai=[3,4,5] if side=='right' else [0,1,2]
 with np.load(ep/'trace.npz') as z:obj=z[key].astype(float)
 with np.load(ep/'parcel_orientation.npz') as z:rot=np.asarray([rotation_xyzw(v.tolist()) for v in z[key]])
 rows=[]
 for f in fr['rows']:
  t=f['step'];selected=enabled and bool(f.get('rear_joint_xy_progress',{}).get('override'))
  base=dict(mode=f['mode'],selected=selected)
  assert helper.refine_rear_command(**base)==dict(override=False,reason='disabled');default_calls+=1
  if not selected:
   out=helper.refine_rear_command(enabled=True,**base);assert not out['override'];protected_calls+=1;continue
  c=coords[t];J=np.vstack([np.asarray(c['control_jacobian_world'],dtype=np.float32),np.asarray(c['contact_normal_tracking']['jacobian'],dtype=np.float32)]);err=[]
  for hand in ['left','right']:
   target=f['target_xyz'] if hand==side else c['inactive_anchor'];point=np.asarray(c['control_point_positions'][hand],dtype=np.float32);err.extend(np.clip(np.float32(.72)*(np.asarray(target,dtype=np.float32)-point),np.float32(-.035),np.float32(.035)).tolist())
  e=np.r_[np.asarray(err,dtype=np.float32),np.asarray(c['contact_normal_tracking']['error'],dtype=np.float32)];lo=np.asarray(U1_JOINT_LIMIT_LO)[12:23].copy();hi=np.asarray(U1_JOINT_LIMIT_HI)[12:23].copy();lo[0]=-.98;hi[0]=.98;limits=np.full(11,.04);limits[0]=.015;damping=np.sqrt(np.array([np.float32(.12**2)]+[np.float32(.045**2)]*10));offset=np.asarray(f['control_offset_local'])
  def point_fn(cmd,offset=offset,model=model,side=side):
   T,_,_=model.fk(side,cmd);return T[:3,3]+T[:3,:3]@offset
  cop=rot[t].T@(np.asarray(f['rear_cop_centering']['cop_world'])-obj[t]);core=np.asarray(fr['plan']['region_causal_response']['actual_core']['collision_core_size_xyz'])
  kwargs=dict(**base,current=q[t],previous=u[t-1],parent_command=u[t],jacobian=J,error=e,damping=damping,lower=lo,upper=hi,step_limits=limits,object_rotation=rot[t],cop_local=cop,core_size=core,direction=direction,active_rows=ai,point_fn=point_fn)
  copies={k:np.array(v,copy=True) for k,v in kwargs.items() if isinstance(v,np.ndarray)};start=time.perf_counter();out=helper.refine_rear_command(enabled=True,**kwargs);elapsed=time.perf_counter()-start
  for k,v in copies.items():assert np.array_equal(kwargs[k],v),k
  actual=np.asarray(out['command'],dtype=np.float32) if out['override'] else u[t].copy()
  if out['override']:
   assert actual.shape==(11,) and np.isfinite(actual).all();assert np.max(abs(actual-u[t-1]))<=.0550002;assert np.all(actual>=lo-2e-7) and np.all(actual<=hi+2e-7);assert np.all(abs(actual-q[t])<=limits+2e-7)
   d=point_fn(actual)-point_fn(q[t]);axes=[k for k in [0,1] if core[k]/2-abs(cop[k])<=.01];inward=[-np.sign(cop[k])*rot[t,:,k]@d for k in axes];assert min(inward)>=-1e-7 and direction*d[1]>=-1e-7
   assert np.max(abs(np.asarray(out['nominal_edge_inward_m'])-inward))<1e-10
  else:assert np.array_equal(actual,u[t])
  rows.append(dict(step=t,result=out,elapsed_s=elapsed));last=kwargs
 reports.append(dict(episode=ep.name,selected=enabled,rows=rows,overrides=sum(x['result']['override'] for x in rows),fallback_reasons={reason:sum(x['result']['reason']==reason for x in rows) for reason in sorted({x['result']['reason'] for x in rows})},median_elapsed_s=float(np.median([x['elapsed_s'] for x in rows])) if rows else 0,max_elapsed_s=max((x['elapsed_s'] for x in rows),default=0),source_sha256={n:sha(ep/n) for n in ['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','coordination.json']}))
assert last is not None
for mode in ['top_lift','top_descend','top_press','top_release','region_approach']:
 args=dict(last,mode=mode);assert helper.refine_rear_command(enabled=True,**args)['reason']=='original_mode_guard';protected_calls+=1
assert helper.refine_rear_command(enabled=True,**dict(last,selected=False))['reason']=='original_rear_not_overridden';protected_calls+=1
for field,value in [('current',np.full(11,np.nan)),('jacobian',np.zeros((8,11))),('object_rotation',np.zeros((3,3))),('core_size',np.zeros(3)),('direction',0),('selected',1),('step_limits',np.zeros(11)),('active_rows',[2,3,4])]:
 try:helper.refine_rear_command(enabled=True,**dict(last,**{field:value}))
 except ValueError:rejects+=1
 else:raise AssertionError(('invalid accepted',field))
# Explicit numeric/infeasible paths must retain the parent; no silent substitute.
old=helper.linprog
try:
 helper.linprog=lambda *a,**k:SimpleNamespace(success=False,status=2)
 assert helper.refine_rear_command(enabled=True,**last)['reason']=='linear_initialization_infeasible'
finally:helper.linprog=old
old=helper.minimize
try:
 helper.minimize=lambda *a,**k:SimpleNamespace(success=False,status=9)
 assert helper.refine_rear_command(enabled=True,**last)['reason']=='nonlinear_solver_failed'
finally:helper.minimize=old
out=dict(passed=True,default_calls=default_calls,protected_calls=protected_calls,invalid_rejections=rejects,injected_failure_paths=2,episodes=reports,helper_sha256=sha(w/'staged_joint_edge_probe/joint_edge_command.py'),checker_sha256=sha(Path(__file__)),training_ready=False,scope='Unwired helper on four completed1200-frame real streams. Original full baseline replay on selected rear streams. Default/transition/front exclusion preserve original command, valid outputs checked independently with FK/bounds/slew; inputs unmodified. Fixed real states, no recursive rollout or physical contact proof; virtual reference is not physical contact.')
(w/'JOINT_EDGE_COMMAND_PROBE_CHECK.json').write_text(json.dumps(out,indent=2));print(json.dumps({**{k:v for k,v in out.items() if k not in ['episodes']},'episodes':[{k:v for k,v in x.items() if k not in ['rows','source_sha256']} for x in reports]},indent=2))
