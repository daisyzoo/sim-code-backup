"""Static checks on saved candidate commands: current contact centroid, hull gaps.
The force-weighted centroid is anchored to the current hand transform for one
nominal FK step. This does not predict next COP, force, collision along the path,
full arm clearance, or actual dynamics. Nonpositive face gap is inconclusive.
"""
from pathlib import Path
import sys,json,hashlib,importlib.util
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path.insert(0,str(repo))
from simfoundry.data.hand_obstacle_clearance import hand_face_separation
from simfoundry.data.sorting_quality import PALM_OFFSET
from simfoundry.calibration.sorting_station import TABLE_TOP_Z,PARCEL_BOX_SIZE,MAILER_SIZE_XYH
ep=Path(sys.argv[1]).resolve();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();source=ep/'JOINT_EDGE_NONLINEAR_IK_SCREEN.json';screen=json.loads(source.read_text());assert screen['checker_sha256']==sha(w/'screen_joint_edge_nonlinear_ik.py')
for n,h in screen['source_sha256'].items():assert sha(ep/n)==h
for n,h in screen['assets_sha256'].items():assert sha(repo/n)==h
prov=json.loads((ep.parent/'provenance.json').read_text());n=next(n for n in prov['source_sha256'] if n.endswith('/articulated_hand_geometry.py'));gp=ep.parent/'source_snapshot'/n;assert sha(gp)==screen['archived_geometry_sha256'];sp=importlib.util.spec_from_file_location('edge_contact_geometry',gp);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);model=m.ArticulatedHandGeometry(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json')
fr={r['step']:r for r in json.loads((ep/'frontal_bypass.json').read_text())['rows']};cs={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};side='right' if 'push_box' in ep.name else 'left';inactive='left' if side=='right' else 'right';key='box' if side=='right' else 'mailer';other='mailer' if key=='box' else 'box';sizes={'box':PARCEL_BOX_SIZE,'mailer':MAILER_SIZE_XYH}
with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float)
with np.load(ep/'trace.npz') as z:xyz={k:z[k].astype(float) for k in sizes}
with np.load(ep/'parcel_orientation.npz') as z:quat={k:z[k].copy() for k in sizes}
rows=[]
for sr in screen['rows']:
 if sr['status']!='feasible':continue
 t=sr['step'];f=fr[t];c=cs[t];R=Rotation.from_quat(quat[key][t]).as_matrix();T,_,_=model.fk(side,q[t]);cop=np.asarray(f['rear_cop_centering']['cop_world']);local_hand=T[:3,:3].T@(cop-T[:3,3]);local_obj=R.T@(cop-xyz[key][t]);normals=np.asarray([-np.sign(local_obj[k])*R[:,k] for k in sr['threatened_axes']]);variants=[]
 for v in sr['variants']:
  cmd=np.asarray(v['command']);Ts,_,_=model.fk(side,cmd);Ti,_,_=model.fk(inactive,cmd);cop_nominal=Ts[:3,3]+Ts[:3,:3]@local_hand
  gaps={}
  for hand,Th in [(side,Ts),(inactive,Ti)]:
   hq=Rotation.from_matrix(Th[:3,:3]).as_quat()
   for parcel in sizes:
    if hand==side and parcel==key:continue
    gaps[hand+'_'+parcel]=hand_face_separation(hand).gap(Th[:3,3],hq,xyz[parcel][t],quat[parcel][t],sizes[parcel])*1000
  ip=Ti[:3,3]+Ti[:3,:3]@np.asarray(PALM_OFFSET);anchor=np.asarray(c['inactive_anchor']);normal_anchor=np.asarray(c['contact_normal_tracking']['target_local_up']);normal_angle=np.arccos(np.clip((Ts[:3,:3].T@np.array([0.,0.,1.]))@normal_anchor,-1,1))
  variants.append(dict(name=v['name'],contact_centroid_anchored_nominal_min_inward_mm=float(np.min(normals@(cop_nominal-cop))*1000),inactive_palm_anchor_error_mm=float(np.linalg.norm(ip-anchor)*1000),active_normal_angle_rad=float(normal_angle),hand_parcel_separation_mm=gaps,hand_lowest_z_above_table_mm={hand:float(((model.vertices[hand]@Th[:3,:3].T+Th[:3,3])[:,2].min()-TABLE_TOP_Z)*1000) for hand,Th in [(side,Ts),(inactive,Ti)]}))
 rows.append(dict(step=t,variants=variants))
summary=[]
for i in [0,1]:
 vals=[r['variants'][i] for r in rows];base=[r['variants'][0] for r in rows];d=[v['inactive_palm_anchor_error_mm']-b['inactive_palm_anchor_error_mm'] for v,b in zip(vals,base)]
 summary.append(dict(name=vals[0]['name'],frames=len(vals),anchored_centroid_outward_over_0_05mm=sum(v['contact_centroid_anchored_nominal_min_inward_mm']<-.05 for v in vals),minimum_anchored_centroid_inward_mm=min(v['contact_centroid_anchored_nominal_min_inward_mm'] for v in vals),median_anchored_centroid_inward_mm=float(np.median([v['contact_centroid_anchored_nominal_min_inward_mm'] for v in vals])),minimum_hand_parcel_separation_mm=min(min(v['hand_parcel_separation_mm'].values()) for v in vals),max_inactive_palm_anchor_error_increase_mm=max(d),median_inactive_palm_anchor_error_increase_mm=float(np.median(d)),normal_angle_increase_over_0_001rad=sum(v['active_normal_angle_rad']>b['active_normal_angle_rad']+.001 for v,b in zip(vals,base)),minimum_hand_bottom_above_table_mm=min(min(v['hand_lowest_z_above_table_mm'].values()) for v in vals)))
out=dict(episode=ep.name,summary=summary,rows=rows,screen_sha256=sha(source),source_sha256={n:sha(ep/n) for n in ['raw.npz','trace.npz','parcel_orientation.npz','coordination.json','frontal_bypass.json']},checker_sha256=sha(Path(__file__)),training_ready=False,scope=__doc__+' Parcel envelopes use bound nominal geometry, not inferred current camera boxes. The actual target core is used by the upstream directional screen; non-target conservative nominal envelope gaps are one-step static only.')
(ep/'JOINT_EDGE_CONTACT_GEOMETRY.json').write_text(json.dumps(out,indent=2));print(json.dumps(dict(episode=ep.name,summary=summary),indent=2))
