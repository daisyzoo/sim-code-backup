"""Independent causal response and real core handover audit. No solver imported."""
from pathlib import Path
import sys,json,hashlib,subprocess,ast
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(w/'staged_contact_patch_approach'),str(repo)]
from articulated_hand_geometry import ArticulatedHandGeometry
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def verify_record(record,current,prior,previous_command,decay,core_scale):
 errors=[];gain=1-decay;offset=decay*current+(current-previous_command)-decay*(prior-previous_command)
 for name,want in [('current_q',current),('previous_q',prior),('previous_command',previous_command),('decay',decay),('gain',gain),('offset',offset),('core_scale',core_scale)]:
  try:got=np.asarray(record[name],dtype=float);assert got.shape==want.shape and np.isfinite(got).all() and np.max(abs(got-want))<=2e-6
  except (KeyError,ValueError,AssertionError):errors.append('causal_'+name)
 if record.get('command_change_damping') is not True:errors.append('command_change_damping')
 if record.get('response_centered_xy_objective') is not True:errors.append('response_centered_xy_objective')
 return gain,offset,errors

def inspect_geometry(model,side,q,target,quat,obstacle,oquat,size,osize,core_scale=None,anchor=None):
 g=model.scene_geometry(side,q,target_xyz=target,target_quat=quat,other_xyz=obstacle,other_quat=oquat,other_size=osize);world=g['vertices']@g['hand_rotation'].T+g['hand_xyz'];local=(world-g['target_xyz'])@g['target_rotation'];i=int(local[:,2].argmin());point=local[i];half=size[:2]/2-.01 if core_scale is None else size[:2]*core_scale[:2]/2-.01;lo=np.array(U1_JOINT_LIMIT_LO)[12:23].copy();hi=np.array(U1_JOINT_LIMIT_HI)[12:23].copy();lo[0]=-.98;hi[0]=.98;errors=[]
 for bad,name in [(np.any(abs(point[:2])>half+2e-6),'inside_region'),(point[2]<size[2]/2+.003-2e-6,'minimum_height'),(g['hand_other_gap_m']<.005-2e-6,'other_gap'),(world[:,2].min()<.746-2e-6,'table_height'),(np.any(q<lo-2e-6) or np.any(q>hi+2e-6),'joint_bounds')]:
  if bad:errors.append(name)
 inactive=None
 if core_scale is not None:
  inactive=float(np.linalg.norm(g['inactive_palm']-anchor))
  if point[2]>size[2]/2+.005+2e-6:errors.append('handover_max_height')
  if inactive>.002+2e-6:errors.append('handover_inactive_anchor')
 return dict(point_local=point.tolist(),top_gap_m=float(point[2]-size[2]/2),other_gap_m=float(g['hand_other_gap_m']),min_hand_z_m=float(world[:,2].min()),inactive_error_m=inactive,errors=errors)

def main(p):
 base=subprocess.run([sys.executable,str(w/'audit_box_entry_region_action.py'),str(p)],capture_output=True,text=True);assert base.returncode==0,base.stdout+base.stderr
 prov=json.loads((p.parent/'provenance.json').read_text());a=prov['args'];assert a['region_causal_xy_response'] and a['region_causal_response'] and a['region_top_approach'] and a['region_tracking_residual'] and a['role']=='diagnostic'
 params_rel=next(k for k in prov['source_sha256'] if k.endswith('/causal_response_parameters.json'));params_file=p.parent/'source_snapshot'/params_rel;assert sha(params_file)==prov['source_sha256'][params_rel];params=json.loads(params_file.read_text())
 with np.load(p/'raw.npz') as z:q=z['q'].astype(float);u=z['action'].astype(float);task=str(z['task_id'])
 with np.load(p/'trace.npz') as z:tr={k:z[k] for k in z.files}
 with np.load(p/'parcel_orientation.npz') as z:ori={k:z[k] for k in z.files}
 log=json.loads((p/'frontal_bypass.json').read_text());plan=log['plan'];rpath=p/'region_approach.json';rows=json.loads(rpath.read_text())['rows'] if rpath.exists() else [];assert bool(rows)==bool(plan.get('region_causal_response',{}).get('enabled'));side='right' if task=='push_box_to_bin' else 'left';key='box' if side=='right' else 'mailer';other='mailer' if key=='box' else 'box';size=np.array([.14,.09,.045] if key=='box' else [.15,.145,.04]);osize=(.15,.145,.04) if key=='box' else (.14,.09,.045);decay=np.array(params['tasks'][task]['decay']);assert decay.shape==(11,) and np.all((0<=decay)&(decay<=.95))
 cfg=p.parent/'source_snapshot/simfoundry/scene_bridge/isaac_cfg.py';assert sha(cfg)==prov['source_sha256']['simfoundry/scene_bridge/isaac_cfg.py'];node=next(n for n in ast.walk(ast.parse(cfg.read_text())) if isinstance(n,ast.Assign) and any(isinstance(v,ast.Name) and v.id=='core_scale' for v in n.targets));assert ast.unparse(node.value.test)=="obj.semantic == 'mailer'";scale=np.array(ast.literal_eval(node.value.orelse if key=='box' else node.value.body));errors=[];checks=[];handovers=[]
 if rows:
  config=plan['region_causal_response'];assert config['parameters_sha256']==sha(params_file) and config['command_change_damping'] and config['response_centered_xy_objective'] and config['core_inset_m']==.01 and config['planner_waist_reserve_rad']==.02
  assert np.max(abs(np.array(config['core_scale'])-scale))<1e-7 and np.max(abs(np.array(config['actual_core']['collision_core_size_xyz'])-size*scale))<1e-7 and np.array_equal(config['decay'],decay)
 model=ArticulatedHandGeometry(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json');coords={r['step']:r for r in json.loads((p/'coordination.json').read_text())};packets={r['after_action_step']:r for r in json.loads((p/'solved_contact_forces.json').read_text())['rows']};actor='parcel_box' if key=='box' else 'mailer'
 for row in rows:
  t=row['step'];assert 0<t<len(q);s=row['solver'];res=q[t,12:23]-u[t-1,12:23]
  if np.max(abs(res-row['current_tracking_residual_rad']))>2e-6:errors.append([t,'current_residual'])
  if not s:continue
  gain,offset,bad=verify_record(s.get('causal_response',{}),q[t,12:23],q[t-1,12:23],u[t-1,12:23],decay,scale);errors.extend([[t,v] for v in bad])
  if not s.get('joint_override'):continue
  cmd=np.asarray(s['next_q']);assert cmd.shape==(11,)
  if np.max(abs(cmd-u[t,12:23]))>2e-6 or np.max(abs(cmd-u[t-1,12:23]))>.055002:errors.append([t,'executed_command_or_slew'])
  load=sum(abs(c['force_world_N'][2]) for c in packets[t-1]['parcel_contacts'] if any(side+'_wrist_roll' in x for x in c['shapes']) and any('/'+actor+'/' in x for x in c['shapes']))
  if load>=.200002:errors.append([t,'loaded_region_override'])
  if s.get('handover'):
   check=inspect_geometry(model,side,q[t,12:23],tr[key][t],ori[key][t],tr[other][t],ori[other][t],size,osize,scale,coords[t]['inactive_anchor']);errors.extend([[t,'handover_'+v] for v in check['errors']]);handovers.append(dict(step=t,geometry=check,load_n=load));continue
  responses=[]
  for name,value in [('nominal',cmd),('causal',gain*cmd+offset)]:
   check=inspect_geometry(model,side,value,tr[key][t],ori[key][t],tr[other][t],ori[other][t],size,osize);errors.extend([[t,name+'_'+v] for v in check['errors']]);responses.append(dict(response=name,**check))
  checks.append(dict(step=t,responses=responses,load_n=load))
 assets=['third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf','assets/robots/g1_hand_support_vertices.json','simfoundry/calibration/sorting_station.py','simfoundry/data/hand_obstacle_clearance.py']
 for f in assets:assert sha(repo/f)==prov['source_sha256'][f]
 files=['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','coordination.json','solved_contact_forces.json']+(['region_approach.json'] if rows else [])
 out=dict(passed=not errors,errors=errors,region_selected=bool(rows),forecast_steps_checked=len(checks),checks=checks,handovers=handovers,raw_sha256=sha(p/'raw.npz'),base_audit_sha256=sha(p/'BOX_ENTRY_REGION_ACTION_AUDIT.json'),auditor_sha256=sha(__file__),source_sha256={f:sha(p/f) for f in files},parameter_archive_sha256=sha(params_file),collision_source_sha256=sha(cfg),scope='Independent raw previous/current q and executed command, parent-frozen decay, algebraic causal forecast and nominal/response FK. Actual core10mm handover, original bounds/load guards, raw action audit. No solver or response helper imported; no real-dynamics guarantee or quality/visual/data approval.',training_ready=False);(p/'BOX_ENTRY_REGION_CAUSAL_AUDIT.json').write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k not in ['checks','source_sha256']});return 0 if out['passed'] else 1
if __name__=='__main__':sys.exit(main(Path(sys.argv[1]).resolve()))
