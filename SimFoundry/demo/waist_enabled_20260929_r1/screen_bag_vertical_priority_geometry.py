"""Archived-geometry one-step screen of factor2 vertical-task probe.
Independent URDF FK and original elbow/torso separation axes, original palm/table
criterion, hand/non-target face separation, and actual nonlinear wrist attitude.
No cumulative dynamics, swept path or physical contacts are simulated.
"""
from pathlib import Path
import sys,json,hashlib,datetime,itertools,ast,xml.etree.ElementTree as ET
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.spatial import ConvexHull
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from simfoundry.data.bounded_ik import bounded_damped_step
from simfoundry.calibration.sorting_station import SORTING_ROBOT_POS,SORTING_ROBOT_ROT_XYZW,TABLE_TOP_Z
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
class Geometry:
 def __init__(self,case):
  p=json.loads((case/'provenance.json').read_text());self.sources={}
  def archived(suffix):
   names=[x for x in p['source_sha256'] if x.endswith(suffix)];assert len(names)==1;f=case/'source_snapshot'/names[0];assert sha(f)==p['source_sha256'][names[0]];self.sources[str(f)]=sha(f);return f
  hp=archived('/elbow_torso_hulls.json');h=json.loads(hp.read_text());urdf=archived('/g1_23dof_rev_1_0_u1_black.urdf');assert sha(urdf)==h['urdf_sha256'];hand=json.loads(archived('/g1_hand_support_vertices.json').read_text());self.hand={k:np.array(v) for k,v in hand['vertices'].items()};self.hulls=h
  mesh=case/'source_snapshot'/hand['source_path'];assert sha(mesh)==hand['source_sha256'];self.sources[str(mesh)]=sha(mesh)
  for k in ['simfoundry/calibration/sorting_station.py','simfoundry/data/bounded_ik.py']:
   assert sha(ROOT/k)==p['source_sha256'][k];self.sources[str(ROOT/k)]=sha(ROOT/k)
  constants={}
  for node in ast.parse((ROOT/'simfoundry/data/sorting_quality.py').read_text()).body:
   if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id in {'PALM_OFFSET','PALM_COLLISION_HALF_Z','TABLE_PENETRATION_TOLERANCE'}:constants[node.targets[0].id]=ast.literal_eval(node.value)
  assert constants==dict(PALM_OFFSET=(.20,0.,.007),PALM_COLLISION_HALF_Z=.049,TABLE_PENETRATION_TOLERANCE=.004)
  self.sources[str(ROOT/'simfoundry/data/sorting_quality.py')]=sha(ROOT/'simfoundry/data/sorting_quality.py')
  self.constants=constants;children={j.find('child').get('link'):j for j in ET.parse(urdf).getroot().findall('joint')};self.names=['waist_yaw_joint']+[s+'_'+j+'_joint' for s in ['left','right'] for j in ['shoulder_pitch','shoulder_roll','shoulder_yaw','elbow','wrist_roll']];self.chains={}
  for link in ['torso_link','left_elbow_link','right_elbow_link','left_wrist_roll_rubber_hand','right_wrist_roll_rubber_hand']:
   assert link in children, link
   chain=[];l=link
   while l in children:
    j=children[l];o=j.find('origin');M=np.eye(4)
    if o is not None:M[:3,3]=np.fromstring(o.get('xyz','0 0 0'),sep=' ');M[:3,:3]=Rotation.from_euler('xyz',np.fromstring(o.get('rpy','0 0 0'),sep=' ')).as_matrix()
    a=j.find('axis');axis=None if a is None else np.fromstring(a.get('xyz'),sep=' ');chain.append((j.get('name'),M,axis));l=j.find('parent').get('link')
   self.chains[link]=list(reversed(chain))
  z=np.linspace(-1,1,80);theta=np.arange(80)*np.pi*(3-np.sqrt(5));self.axes=np.vstack([np.eye(3),np.stack([np.sqrt(1-z*z)*np.cos(theta),np.sqrt(1-z*z)*np.sin(theta),z],axis=1)]);self.tp=np.array(h['torso']['vertices'])@self.axes.T
  self.hand_axes={}
  for side,vertices in self.hand.items():
   axes=np.unique(np.round(ConvexHull(vertices).equations[:,:3],10),axis=0);axes/=np.linalg.norm(axes,axis=1)[:,None];self.hand_axes[side]=axes
 def fk(self,q):
  poses={}
  for link,chain in self.chains.items():
   M=np.eye(4);M[:3,3]=SORTING_ROBOT_POS;M[:3,:3]=Rotation.from_quat(SORTING_ROBOT_ROT_XYZW).as_matrix()
   for name,O,axis in chain:
    M=M@O
    if axis is not None:R=np.eye(4);R[:3,:3]=Rotation.from_rotvec(axis*(q[self.names.index(name)] if name in self.names else 0)).as_matrix();M=M@R
   poses[link]=M
  return poses
 def elbow_gaps(self,p):
  out=[]
  for side in ['left','right']:
   rel=np.linalg.inv(p['torso_link'])@p[side+'_elbow_link'];v=np.array(self.hulls[side]['vertices'])@rel[:3,:3].T+rel[:3,3];a=v@self.axes.T;out.append(float(max(np.max(a.min(0)-self.tp.max(0)),np.max(self.tp.min(0)-a.max(0)))))
  return out
 def table_margins(self,p):
  out=[]
  for side in ['left','right']:
   M=p[side+'_wrist_roll_rubber_hand'];palm=M[:3,3]+M[:3,:3]@self.constants['PALM_OFFSET'];out.append(float(palm[2]-self.constants['PALM_COLLISION_HALF_Z']-(TABLE_TOP_Z-self.constants['TABLE_PENETRATION_TOLERANCE'])))
  return out
 def hand_box_gap(self,p,side,xyz,rotation,size):
  M=p[side+'_wrist_roll_rubber_hand'];rh=M[:3,:3];axes=self.hand_axes[side];hp=self.hand[side]@axes.T;corners=np.array(list(itertools.product([-1,1],repeat=3)))*size/2;bp=((corners@rotation.T+xyz-M[:3,3])@rh)@axes.T
  hand_gap=max(np.max(bp.min(0)-hp.max(0)),np.max(hp.min(0)-bp.max(0)));h=((self.hand[side]@rh.T+M[:3,3])-xyz)@rotation;return float(max(hand_gap,np.max(h.min(0)-size/2),np.max(-size/2-h.max(0))))
def run_one(ep,steps):
 g=Geometry(ep.parent);coords={x['step']:x for x in json.loads((ep/'coordination.json').read_text())};clear=json.loads((ep/'self_clearance.json').read_text());pre={x['step']:x for x in clear['rows'] if x['phase']=='pre'};final={x['step']:x for x in clear['rows'] if x['phase']=='final_command'}
 with np.load(ep/'trace.npz') as z:box=z['box'].astype(float)
 with np.load(ep/'parcel_orientation.npz') as z:box_rot=Rotation.from_quat(z['box']).as_matrix()
 rows=[];max_position_error=0.;max_gap_error=0.
 for t in steps:
  c=coords[t];a=c['task_inputs'];J=np.array(a['jacobian']);e=np.array(a['error']);q=np.array(a['current']);args={k:np.array(a[k]) for k in ['lower','upper','step_limits','damping','preferred_step']};base=q+bounded_damped_step(J,e,q,**args);jw=J.copy();ew=e.copy();jw[2]*=2;ew[2]*=2;candidate=q+bounded_damped_step(jw,ew,q,**args);np.testing.assert_allclose(base,final[t]['command'],atol=1e-6,rtol=0)
  observed=g.fk(q);left=observed['left_wrist_roll_rubber_hand'];reference=left[:3,3]+left[:3,:3]@np.array(c['active_point_offset_local']);err=float(np.max(abs(reference-c['control_point_positions']['left'])));max_position_error=max(max_position_error,err);assert err<2e-6
  for link in ['torso_link','left_elbow_link','right_elbow_link']:np.testing.assert_allclose(observed[link],pre[t]['runtime_link_poses'][link],atol=2e-6,rtol=0)
  pb=g.fk(np.array(final[t]['command']));gaperror=float(np.max(abs(np.array(g.elbow_gaps(pb))-final[t]['gaps_m'])));max_gap_error=max(max_gap_error,gaperror);assert gaperror<2e-10
  target=np.array(c['contact_normal_tracking']['target_local_up']);obs_up=left[:3,:3].T@np.array([0.,0.,1.]);np.testing.assert_allclose(obs_up,c['contact_normal_tracking']['current_local_up'],atol=2e-6,rtol=0)
  row=dict(step=t)
  for label,poses in [('parent',pb),('candidate',g.fk(candidate))]:
   up=poses['left_wrist_roll_rubber_hand'][:3,:3].T@np.array([0.,0.,1.]);angle=float(np.arctan2(np.linalg.norm(np.cross(up,target)),up@target));row[label]=dict(elbow_torso_gaps_m=g.elbow_gaps(poses),original_palm_table_margins_m=g.table_margins(poses),left_hand_non_target_box_gap_m=g.hand_box_gap(poses,'left',box[t],box_rot[t],np.array([.14,.09,.045])),normal_angle_rad=angle)
  rows.append(row)
 summary=dict(frames=len(rows),max_observed_hand_reference_fk_error_m=max_position_error,max_original_elbow_gap_replay_error_m=max_gap_error)
 for label in ['parent','candidate']:
  summary[label]=dict(min_elbow_torso_gap_m=min(min(x[label]['elbow_torso_gaps_m']) for x in rows),elbow_below_original_5mm_frames=sum(min(x[label]['elbow_torso_gaps_m'])<.005-2e-7 for x in rows),min_original_palm_table_margin_m=min(min(x[label]['original_palm_table_margins_m']) for x in rows),original_palm_table_criterion_violated_frames=sum(min(x[label]['original_palm_table_margins_m'])<0 for x in rows),min_hand_non_target_separation_m=min(x[label]['left_hand_non_target_box_gap_m'] for x in rows),potential_hand_non_target_overlap_frames=sum(x[label]['left_hand_non_target_box_gap_m']<=0 for x in rows),mean_normal_angle_rad=float(np.mean([x[label]['normal_angle_rad'] for x in rows])),max_normal_angle_rad=max(x[label]['normal_angle_rad'] for x in rows))
 return dict(episode=ep.name,summary=summary,rows=rows,source_sha256={**g.sources,**{str(p):sha(p) for p in [ep/'coordination.json',ep/'self_clearance.json',ep/'trace.npz',ep/'parcel_orientation.npz']}})
if __name__=='__main__':
 r=Path(sys.argv[1]).resolve();sp=r/'BAG_VERTICAL_PRIORITY_OFFLINE_SCREEN.json';s=json.loads(sp.read_text());rows=[run_one(next(r.glob('case_*/'+x['episode'])),[q['step'] for q in x['rows']]) for x in s['rows']];out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,screen_sha256=sha(sp),script_sha256=sha(__file__),one_step_only=True,swept_clearance_verified=False,cumulative_contact_verified=False,runtime_candidate_installed=False,training_ready=False);dest=r/'BAG_VERTICAL_PRIORITY_GEOMETRY_SCREEN.json';assert not dest.exists();dest.write_text(json.dumps(out,indent=2));print(json.dumps([dict(episode=x['episode'],**x['summary']) for x in rows],indent=2))
