"""First eligibility of optional joint hold on recorded development trajectories."""
from pathlib import Path
import sys,json,hashlib,numpy as np
from scipy.spatial.transform import Rotation
root=Path(__file__).resolve().parent;sys.path[:0]=[str(root),str(root.parents[1])]
src=(root/'audit_terminal_reach.py').read_text();exec(compile(src.split("p=root/'contact_x_ablation")[0],'<cached_fk>','exec'))
from terminal_joint_hold_candidate import TerminalJointHold
from simfoundry.data.contact_load_control import hand_target_vertical_load
run=Path(sys.argv[1]).resolve();mesh=json.loads((root.parents[1]/'assets/robots/g1_hand_support_vertices.json').read_text())['vertices'];results=[]
def hand_points(side,q):
 m=np.eye(4);m[:3,3]=[.08,0,.793]
 for name,origin,axis in chains[side]:
  m=m@origin
  if axis is not None:
   a=np.eye(4);a[:3,:3]=Rotation.from_rotvec(axis*q.get(name,0)).as_matrix();m=m@a
 return m[:3,3]+np.asarray(mesh[side])@m[:3,:3].T
for ep in sorted(run.glob('case_*/layout_*')):
 if not (ep/'quality.json').exists():continue
 with np.load(ep/'raw.npz') as z,np.load(ep/'trace.npz') as tr,np.load(ep/'parcel_orientation.npz') as ori:
  side='right' if 'push_box' in ep.name else 'left';key='box' if side=='right' else 'mailer';other='mailer' if key=='box' else 'box';inactive='left' if side=='right' else 'right';direction=-1 if side=='right' else 1
  control=json.loads((ep/'expert_control.json').read_text());coord={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};packets={r['after_action_step']:r for r in json.loads((ep/'solved_contact_forces.json').read_text())['rows']}
  state=TerminalJointHold();first=None;other_max=np.maximum.accumulate(np.linalg.norm(tr[other][:,:2]-tr[other][0,:2],axis=1));first_release=None
  for row in control:
   t=row['step']
   if row['mode'] not in ('goal_release','top_release','bypass_release'):continue
   if first_release is None:first_release=t
   c=coord[t];q=dict(zip(names,z['q'][t,12:23]));height=max(tr[k][t,2]+float(abs(Rotation.from_quat(ori[k][t]).as_matrix()[2])@np.array(size)/2) for k,size in [('box',[.14,.09,.045]),('mailer',[.15,.145,.04])]);clearance=min(float(hand_points(s,q)[:,2].min()) for s in ('left','right'))-height
   target_window=tr[key][max(0,t-9):t+1];confirmed=len(target_window)==10 and direction*(tr[key][t,1]-tr[key][0,1])>=.15 and bool((direction*target_window[:,1]>=.20).all()) and np.linalg.norm(target_window[-1,:2]-target_window[0,:2])<=.01
   assert t-1 in packets
   load=hand_target_vertical_load(packets[t-1],side,'parcel_box' if key=='box' else 'mailer')
   observation=dict(mode=row['mode'],target_confirmed=bool(confirmed),hand_clearance_m=clearance,load_n=float(load),active_error_m=float(np.max(abs(np.array(c['control_point_positions'][side])-row['target_xyz']))),inactive_error_m=float(np.max(abs(np.array(c['palm_positions'][inactive])-c['inactive_anchor']))),other_max_xy_m=float(other_max[t]),current_upper_q=z['q'][t,12:23].tolist(),previous_upper_command=z['action'][t-1,12:23].tolist())
   command=state.observe(**observation)
   if command is not None:first=dict(frame=t,observation=observation,hold_command=command);break
  results.append(dict(episode=ep.name,first_release_frame=first_release,first_hold_proposal=first,raw_sha256=hashlib.sha256((ep/'raw.npz').read_bytes()).hexdigest()))
out=dict(rows=results,candidate_sha256=hashlib.sha256((root/'terminal_joint_hold_candidate.py').read_bytes()).hexdigest(),scope='Recorded-trajectory eligibility only: real q/FK entire hand meshes above both object tops, solved last-tick load, measured control/inactive errors, original target position confirmation and original15mm other-motion bound. Five consecutive ready frames propose repeating the previous exact command. No joint command executed; later counterfactual states unknown. No substep collision/dynamics or task/quality approval.',training_ready=False)
(run/'TERMINAL_JOINT_HOLD_SHADOW.json').write_text(json.dumps(out,indent=2));print(json.dumps([dict(episode=r['episode'],release=r['first_release_frame'],hold=None if r['first_hold_proposal'] is None else r['first_hold_proposal']['frame']) for r in results],indent=2))
