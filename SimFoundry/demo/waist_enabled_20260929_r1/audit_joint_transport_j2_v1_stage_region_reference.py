"""Independently verify captured region hand vertex and parcel-local contact."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(w/'staged_contact_patch_approach'),str(repo)]
from articulated_hand_geometry import ArticulatedHandGeometry

def audit(ep,rows_override=None):
 ep=Path(ep);f=ep/'region_approach.json'
 from joint_transport_j2_v1_stage_audit_context import verified_events,verified_front_events,verified_front_recovery_events
 from joint_transport_j2_reference_ledger import verified_reference_lifetimes
 verified_recontacts=verified_events(ep)
 front=verified_front_events(ep);recovery=verified_front_recovery_events(ep)
 if front or recovery:
  assert not verified_recontacts and not f.exists()
  assert rows_override is None,'front references require full native frontal rows'
  rows=json.loads((ep/'frontal_bypass.json').read_text())['rows']
  result=verified_reference_lifetimes(rows,front,recovery,side='right' if 'push_box' in ep.name else 'left')
  result.update(raw_sha256=hashlib.sha256((ep/'raw.npz').read_bytes()).hexdigest(),native_pose_sha256=hashlib.sha256((ep/'JOINT_TRANSPORT_J2_V1_STAGE_POSE_LIVE_V2_AUDIT.json').read_bytes()).hexdigest(),ledger_sha256=hashlib.sha256((w/'joint_transport_j2_reference_ledger.py').read_bytes()).hexdigest())
  return result
 if not f.exists():return dict(passed=True,centers={},surface_local_by_step={},handover_step=None,scope='No region hook')
 rows=json.loads(f.read_text())['rows'] if rows_override is None else rows_override;hs=[r for r in rows if r['solver'] and r['solver'].get('handover')];assert len(hs)<=1
 if not hs:
  assert all(r['center_local'] is None and r['selected_surface_local_xy'] is None for r in rows)
  return dict(passed=True,centers={},surface_local_by_step={},handover_step=None,scope='No region handover')
 h=hs[0];t=h['step'];side='right' if 'push_box' in ep.name else 'left';key='box' if side=='right' else 'mailer';other='mailer' if side=='right' else 'box';size=np.array([.14,.09,.045] if key=='box' else [.15,.145,.04]);osize=(.15,.145,.04) if key=='box' else (.14,.09,.045)
 with np.load(ep/'raw.npz') as z:q=z['q'].astype(float);u=z['action'].astype(float)
 with np.load(ep/'trace.npz') as z:tr={k:z[k] for k in z.files}
 with np.load(ep/'parcel_orientation.npz') as z:ori={k:z[k] for k in z.files}
 coord={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};model=ArticulatedHandGeometry(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json');g=model.scene_geometry(side,q[t,12:23],target_xyz=tr[key][t],target_quat=ori[key][t],other_xyz=tr[other][t],other_quat=ori[other][t],other_size=osize);world=g['vertices']@g['hand_rotation'].T+g['hand_xyz'];local=(world-g['target_xyz'])@g['target_rotation'];i=int(local[:,2].argmin());center=g['vertices'][i];point=local[i];gap=float(point[2]-size[2]/2);inactive=float(np.linalg.norm(g['inactive_palm']-coord[t]['inactive_anchor']));half=size[:2]/2-.01
 assert .003-1e-7<=gap<=.005+1e-7 and inactive<.002+1e-7 and np.all(abs(point[:2])<=half+1e-7)
 assert g['hand_other_gap_m']>=.005-1e-7 and world[:,2].min()>=.746-1e-7
 assert np.max(abs(q[t,12:23]-u[t,12:23]))<2e-6
 packet=next(r for r in json.loads((ep/'solved_contact_forces.json').read_text())['rows'] if r['after_action_step']==t-1);actor='parcel_box' if key=='box' else 'mailer';load=sum(abs(c['force_world_N'][2]) for c in packet['parcel_contacts'] if any(side+'_wrist_roll' in x for x in c['shapes']) and any('/'+actor+'/' in x for x in c['shapes']));assert load<.2
 selected=np.clip(point[:2],-half,half);centers={};surfaces={}
 for r in rows:
  if r['step']<t:assert r['center_local'] is None and r['selected_surface_local_xy'] is None;continue
  event=verified_recontacts.get(r['step'])
  if event is not None and event['kind']=='handover':
   from joint_transport_j2_v1_stage_audit_context import selected_after_capture
   selected=np.asarray(selected_after_capture(r,selected,verified_recontacts));center=np.asarray(event['captured_center_local'])
  assert np.max(abs(np.asarray(r['center_local'])-center))<2e-7 and np.max(abs(np.asarray(r['selected_surface_local_xy'])-selected))<2e-7
  centers[r['step']]=center.tolist();surfaces[r['step']]=selected.tolist()
 assert set(centers)==set(range(t,len(q)))
 return dict(passed=True,centers=centers,surface_local_by_step=surfaces,handover_step=t,top_gap_m=gap,inactive_error_m=inactive,load_n=float(load),actual_captured_vertex_index=i,raw_sha256=hashlib.sha256((ep/'raw.npz').read_bytes()).hexdigest(),scope='Measured URDF hand FK at handover, actual lowest vertex, target-local capture, original unloaded3–5mm/2mm inactive/10mm inset/other/table guards and raw q-hold. Entire remaining log must preserve independently captured reference. No controller helper imported.')
if __name__=='__main__':
 ep=Path(sys.argv[1]);r=audit(ep);(ep/'JOINT_TRANSPORT_J2_V1_STAGE_REGION_REFERENCE_AUDIT.json').write_text(json.dumps(r,indent=2));print({k:v for k,v in r.items() if k not in {'centers','surface_local_by_step'}})
