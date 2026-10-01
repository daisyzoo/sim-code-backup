"""Decompose measured COP motion; no controller change or dynamical prediction.
Force packet(t-1) belongs to observation(t). Same-bout consecutive loaded samples
only. Exact geometric identity separates fixed hand-reference movement, object
translation, object rotation, and contact migration relative to that reference.
A valid nominal FK command is not a guarantee of actual relative contact motion.
"""
from pathlib import Path
import sys,json,hashlib,datetime
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(w),str(repo)]
from audit_unloaded_wrist_prior_live import HandModel
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
urdf=repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf';vertices=repo/'assets/robots/g1_hand_support_vertices.json';hand=HandModel(urdf,vertices);results=[]
for run in ['rear_short_recovery_groups_r1','unloaded_wrist_prior_groups_r1','recontact_pose_groups_r1']:
 for cid,task,key,side,actor in [(840001,'push_box_to_bin','box','right','parcel_box'),(840004,'nudge_mailer_to_bin','mailer','left','mailer')]:
  ep=w/run/f'case_{cid}/layout_{cid}_{task}';fr=json.loads((ep/'frontal_bypass.json').read_text());rows={r['step']:r for r in fr['rows']};core=np.array(fr['plan']['region_causal_response']['actual_core']['collision_core_size_xyz']);packets=json.loads((ep/'solved_contact_forces.json').read_text())['rows'];coords={r['step']:r for r in json.loads((ep/'coordination.json').read_text())}
  with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
  with np.load(ep/'trace.npz') as z:xyz=z[key].astype(float)
  with np.load(ep/'parcel_orientation.npz') as z:R=Rotation.from_quat(z[key]).as_matrix()
  cop={};loads={}
  for packet in packets:
   t=packet['after_action_step']+1
   if t>=len(q) or t not in rows or rows[t]['mode']!='top_push':continue
   assert np.max(abs(np.array(packet['post_action_pose'][key])-xyz[t]))<1e-6
   points=[];weights=[]
   for c in packet['parcel_contacts']:
    slots=[i for i,s in enumerate(c['shapes']) if '/'+actor+'/' in s]
    if len(slots)!=1 or not any(side+'_wrist' in s for s in c['shapes']):continue
    f=np.array(c['force_world_N'])*(1 if slots[0]==1 else -1);load=-float(f@R[t,:,2])
    if load>.05:points.append(c['position_world']);weights.append(load)
   if sum(weights)>=.3:cop[t]=np.average(points,axis=0,weights=weights);loads[t]=sum(weights)
  records=[]
  for t in sorted(cop):
   if t+1 not in cop or rows[t]['recontacts']!=rows[t+1]['recontacts']:continue
   offset=np.array(rows[t]['control_offset_local']);T=hand.fk(q[t],side);h=T[:3,3]+T[:3,:3]@offset;Tn=hand.fk(q[t+1],side);hn=Tn[:3,3]+Tn[:3,:3]@offset;Tu=hand.fk(u[t],side);hu=Tu[:3,3]+Tu[:3,:3]@offset
   assert np.max(abs(h-np.array(rows[t]['observed_support_xyz'])))<2e-6
   assert np.max(abs(q[t]-coords[t]['upper_q']))<1e-6
   a=R[t].T@(cop[t]-xyz[t]);b=R[t+1].T@(cop[t+1]-xyz[t+1]);d=b-a
   components={'hand':R[t].T@(hn-h),'object_translation':-R[t].T@(xyz[t+1]-xyz[t]),'object_rotation':(R[t+1].T-R[t].T)@(cop[t+1]-xyz[t+1]),'contact_migration':R[t].T@((cop[t+1]-hn)-(cop[t]-h))}
   assert np.max(abs(sum(components.values())-d))<1e-10
   nominal=R[t].T@(hu-h);sign=-float(np.sign(a[0]));near=bool(core[0]/2-abs(a[0])<=.01)
   records.append({'step':t,'near_x_edge':near,'cop_local_mm':(a*1000).tolist(),'next_cop_local_mm':(b*1000).tolist(),'cop_delta_local_mm':(d*1000).tolist(),'nominal_reference_delta_local_mm':(nominal*1000).tolist(),'inward_x_nominal_mm':float(sign*nominal[0]*1000),'inward_x_measured_cop_mm':float(sign*d[0]*1000),'inward_x_components_mm':{k:float(sign*v[0]*1000) for k,v in components.items()},'command_refinement_reason':coords[t].get('joint_edge_refinement',{}).get('reason'),'command_refinement_applied':coords[t].get('joint_edge_refinement',{}).get('override',False),'load_n':loads[t],'next_load_n':loads[t+1]})
  near=[r for r in records if r['near_x_edge']];disagree=[r for r in near if r['inward_x_nominal_mm']>=-.0001 and r['inward_x_measured_cop_mm']<-.1]
  summary={'consecutive_loaded_pairs':len(records),'near_x_edge_pairs':len(near),'nominal_nonoutward_but_actual_outward_over_point1mm':len(disagree),'disagree_median_nominal_inward_mm':float(np.median([r['inward_x_nominal_mm'] for r in disagree])) if disagree else None,'disagree_median_actual_inward_mm':float(np.median([r['inward_x_measured_cop_mm'] for r in disagree])) if disagree else None,'disagree_median_components_mm':{k:float(np.median([r['inward_x_components_mm'][k] for r in disagree])) for k in ['hand','object_translation','object_rotation','contact_migration']} if disagree else {}}
  names=['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','solved_contact_forces.json','coordination.json'];results.append({'run':run,'episode':ep.name,'summary':summary,'records':records,'source_sha256':{n:sha(ep/n) for n in names}});print(run,task,summary,flush=True)
(w/'LOADED_RELATIVE_CONTACT_MOTION.json').write_text(json.dumps({'scope':__doc__,'created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'rows':results,'source_sha256':{str(p):sha(p) for p in [Path(__file__),w/'audit_unloaded_wrist_prior_live.py',urdf,vertices]},'training_ready':False},indent=2))
