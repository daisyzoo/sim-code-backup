"""Independent measured-hand-height, selection, wrist prior and fallback audit.
No candidate helper/solver/geometry imports. Full action chain and original KKT
remain separate audits. FK reconstructs URDF hand poses and archived vertices.
"""
from pathlib import Path
import sys,json,hashlib,xml.etree.ElementTree as ET
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path.insert(0,str(repo))
from simfoundry.calibration.sorting_station import SORTING_ROBOT_POS,SORTING_ROBOT_ROT_XYZW
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def near(a,b,tol=1e-8):
 a,b=np.asarray(a,float),np.asarray(b,float);assert a.shape==b.shape and np.isfinite(a).all() and np.isfinite(b).all() and np.max(abs(a-b),initial=0)<=tol
class HandModel:
 def __init__(self,urdf,vertices):
  self.names=['waist_yaw_joint']+[s+'_'+j+'_joint' for s in ['left','right'] for j in ['shoulder_pitch','shoulder_roll','shoulder_yaw','elbow','wrist_roll']];self.vertices={k:np.array(v) for k,v in json.loads(Path(vertices).read_text())['vertices'].items()};self.base=np.eye(4);self.base[:3,3]=SORTING_ROBOT_POS;self.base[:3,:3]=Rotation.from_quat(SORTING_ROBOT_ROT_XYZW).as_matrix();xml=ET.parse(urdf).getroot();bychild={j.find('child').get('link'):j for j in xml.findall('joint')};self.chains={}
  for side in ['left','right']:
   link=side+'_wrist_roll_rubber_hand';chain=[]
   while link in bychild:
    j=bychild[link];O=np.eye(4);origin=j.find('origin')
    if origin is not None:O[:3,3]=np.fromstring(origin.get('xyz','0 0 0'),sep=' ');O[:3,:3]=Rotation.from_euler('xyz',np.fromstring(origin.get('rpy','0 0 0'),sep=' ')).as_matrix()
    moving=j.get('type') in ['continuous','revolute'];axis=np.fromstring(j.find('axis').get('xyz'),sep=' ') if moving else None;name=j.get('name');idx=self.names.index(name) if name in self.names else None
    if moving and idx is None:assert name in ['waist_roll_joint','waist_pitch_joint']
    chain.append((O,axis,idx));link=j.find('parent').get('link')
   self.chains[side]=chain[::-1]
 def fk(self,q,side):
  M=self.base.copy()
  for O,axis,i in self.chains[side]:
   M=M@O
   if axis is not None:
    A=np.eye(4);A[:3,:3]=Rotation.from_rotvec(axis*(q[i] if i is not None else 0.)).as_matrix();M=M@A
  return M
 def minz(self,q,side):
  M=self.fk(q,side);return float((self.vertices[side]@M[:3,:3].T+M[:3,3])[:,2].min())
def verify_record(q,c,f,selected,side,model):
 inp=c['task_inputs'];original=np.zeros(11);original[0]=c['preferred_waist_step_rad'];rec=c['self_clearance_task'].get('unloaded_wrist_prior');wi=5 if side=='left' else 10
 if 'contact_load' not in f:
  assert rec is None;near(inp['preferred_step'],original,0);return dict(step=f['step'],eligible=False,applied=False,expected_prior=original.tolist())
 assert isinstance(rec,dict);ctx=rec['context'];assert set(ctx)=={'selected','side','mode','recontacts','observed_load_n','filtered_load_n','min_hand_z_m','hand_position_world','hand_rotation_world'}
 for key,value in dict(selected=selected,side=side,mode=f['mode'],recontacts=f['recontacts'],observed_load_n=f['contact_load']['observed_vertical_load_n'],filtered_load_n=f['contact_load']['filtered_vertical_load_n']).items():assert type(ctx[key]) is type(value) and ctx[key]==value,(f['step'],key)
 pos=np.array(ctx['hand_position_world']);R=np.array(ctx['hand_rotation_world']);near(R.T@R,np.eye(3),1e-6);assert np.linalg.det(R)>.999999;M=model.fk(q,side);near(pos,M[:3,3],1e-4);assert Rotation.from_matrix(M[:3,:3].T@R).magnitude()<=1e-4
 near(pos+R@np.array(c['active_point_offset_local']),c['control_point_positions'][side],2e-6)
 if c['contact_normal_tracking'] is not None:near(R[2],c['contact_normal_tracking']['current_local_up'],1e-6)
 height=float((model.vertices[side]@R.T+pos)[:,2].min());near(height,ctx['min_hand_z_m'],1e-10)
 expected=dict(enabled=True,selected=selected,recovery_mode=f['mode'] in ['top_lift','top_cross'],not_initial=f['recontacts']>0,zero_observed_load=ctx['observed_load_n']==0.,filtered_unloaded=0.<=ctx['filtered_load_n']<=.05,high_hand=height>=.84)
 assert rec['gates']==expected and all(type(v) is bool for v in rec['gates'].values());eligible=all(expected.values());assert type(rec['eligible']) is bool and rec['eligible']==eligible
 near(rec['wrist_target_rad'],0.,0);assert rec['wrist_index']==wi and rec['task_and_normal_rows_unchanged'] is True and rec['loaded_control_unchanged'] is True
 prior=original.copy();request=float(np.clip(-.15*q[wi],-.04,.04)) if eligible else 0.;near(rec['prior_wrist_step_rad'],request,0);assert type(rec['applied']) is bool
 if not eligible:
  assert not rec['applied'] and 'attempted_command' not in rec;near(inp['preferred_step'],prior,0)
 else:
  assert c['contact_normal_tracking'] is not None
  proposed=original.copy();proposed[wi]=np.float32(request);attempt=rec['attempted_task_inputs'];near(attempt['preferred_step'],proposed,0);near(rec['requested_preferred_step'],proposed,0)
  assert {k:v for k,v in attempt.items() if k!='preferred_step'}=={k:v for k,v in inp.items() if k!='preferred_step'}
  x=rec['attempted_command'];meta=rec['attempted_solver_trace']
  if x is None:
   assert meta['accepted'] is False and not rec['applied'] and rec['candidate_nominal_min_hand_z_m'] is None and rec['fallback_reason']=='no_verified_prior_command'
  else:
   x=np.array(x);near(x,x.astype(np.float32),0);assert meta['accepted'] is True;height_next=model.minz(x,side);near(height_next,rec['candidate_nominal_min_hand_z_m'],1e-10)
   assert rec['applied']==(height_next>=.84)
   if not rec['applied']:assert rec['fallback_reason']=='nominal_hand_height'
   else:
    prior=proposed;assert 'fallback_reason' not in rec
    chosen={k:v for k,v in c['self_clearance_task'].items() if k!='unloaded_wrist_prior'};assert chosen==meta
  near(inp['preferred_step'],prior,0)
 return dict(step=f['step'],eligible=eligible,applied=rec['applied'],expected_prior=prior.tolist(),measured_min_hand_z_m=height)
def source_contract(ep):
 prov=json.loads((ep.parent/'provenance.json').read_text());src=prov['source_sha256'];snap=ep.parent/'source_snapshot';args=prov['args'];assert args.get('unloaded_wrist_prior') is True and args['rear_short_recovery'] is True and args['expert_top_contact_normal_hold'] is True and args['self_clearance_task_ik'] is True and args['role']=='diagnostic' and not args['policy_port'] and not args['waist_probe'] and not args['idle']
 for n,h in src.items():assert sha(snap/n)==h
 stage=w/'staged_unloaded_wrist_prior'
 for name in ['collect_paired_sorting.py','waist_coordination_clearance.py','unloaded_wrist_prior.py','unloaded_wrist_task.py','task_ik.py']:
  keys=[n for n in src if n.endswith('/'+name)];assert len(keys)==1 and sha(stage/name)==src[keys[0]]
 for name in ['simfoundry/calibration/sorting_station.py','assets/robots/g1_hand_support_vertices.json','third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf']:assert sha(repo/name)==src[name]
 return prov
def inspect(ep):
 ep=Path(ep).resolve();prov=source_contract(ep);fr=json.loads((ep/'frontal_bypass.json').read_text());cs={x['step']:x for x in json.loads((ep/'coordination.json').read_text())};selected=bool(fr['plan'].get('rear_joint_xy_progress',{}).get('enabled'))
 with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);side='right' if str(z['task_id'])=='push_box_to_bin' else 'left';meta=json.loads(str(z['collect_meta']));assert meta['unloaded_wrist_prior'] is True
 model=HandModel(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json');rows=[]
 assert [r['step'] for r in fr['rows']]==list(range(1,len(q)))
 for f in fr['rows']:rows.append(verify_record(q[f['step']],cs[f['step']],f,selected,side,model))
 return dict(passed=True,errors=[],frames=len(rows),eligible_frames=sum(x['eligible'] for x in rows),applied_frames=sum(x['applied'] for x in rows),records=rows,scope=__doc__,source_sha256={n:sha(ep/n) for n in ['raw.npz','coordination.json','frontal_bypass.json']},provenance_sha256=sha(ep.parent/'provenance.json'),auditor_sha256=sha(Path(__file__)),training_ready=False)
if __name__=='__main__':
 ep=Path(sys.argv[1]);out=ep/'UNLOADED_WRIST_PRIOR_LIVE_AUDIT.json';assert not out.exists();result=inspect(ep);out.write_text(json.dumps(result,indent=2));print({k:v for k,v in result.items() if k not in ['records','source_sha256','scope']})
