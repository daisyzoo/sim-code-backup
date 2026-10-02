"""Read-only temporal attribution of actual parcel interference; no admission.
Forces use magnitudes only: body sign and force/state synchrony are not assumed.
Substep samples retain recording duplicates; counts are not integrated impulses.
"""
from pathlib import Path
import json,hashlib,datetime,collections
import numpy as np
W=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
results=[];bindings={}
for run in ['fresh_closed_peak_trials_r1','joint_edge_intersection_physical_r1']:
 ep=W/run/'case_840015/layout_840015_push_box_to_bin'
 files=['trace.npz','quality.json','coordination.json','SUBSTEP_CONTACT_RECORDING.json','substep_contacts.npz','solved_contact_forces.json','frontal_bypass.json']
 for name in files:bindings[str(ep/name)]=sha(ep/name)
 quality=json.loads((ep/'quality.json').read_text());coord=json.loads((ep/'coordination.json').read_text());fr=json.loads((ep/'frontal_bypass.json').read_text());md=json.loads((ep/'SUBSTEP_CONTACT_RECORDING.json').read_text())['metadata']
 with np.load(ep/'trace.npz') as z:other=z['mailer'].copy();target=z['box'].copy()
 displacement=np.linalg.norm(other[:,:2]-other[0,:2],axis=1)*1000
 changed=[r['step'] for r in coord if r.get('joint_edge_clearance_intersection',{}).get('changed')]
 with np.load(ep/'substep_contacts.npz') as z:
  ids=z['shape_ids'];forces=np.linalg.norm(z['force_torque_world'][:,:3],axis=1);offset=z['contact_offsets'];steps=z['action_step'];kinds=z['kind'];bodies=np.array(md['shape_body'])[ids];labels=md['shape_labels'];mailer=md['body_ids'][1];box=md['body_ids'][0]
  sample=np.repeat(np.arange(len(steps)),np.diff(offset));contactsteps=steps[sample];active=forces>1e-6
  mask_bag=np.any(bodies==mailer,axis=1);mask_box=np.any(bodies==box,axis=1);robot=np.array(['/Robot/' in p for p in labels]);mask_robot=np.any(robot[ids],axis=1)
  contacts={}
  for label,mask in [('box_mailer',mask_bag&mask_box&active),('robot_mailer',mask_bag&mask_robot&active)]:
   ix=np.flatnonzero(mask);ss=contactsteps[ix];pairs=collections.Counter(tuple(sorted(labels[int(v)] for v in ids[i])) for i in ix)
   contacts[label]=dict(contact_records=len(ix),action_steps=len(np.unique(ss)),first_action_step=int(ss.min()) if len(ss) else None,last_action_step=int(ss.max()) if len(ss) else None,max_force_norm_n=float(forces[ix].max()) if len(ix) else 0.,before_first_repair_records=int(np.sum(ss<changed[0])) if changed else None,shape_pairs=[dict(shapes=list(pair),records=count) for pair,count in pairs.items()],sample_kinds={str(int(k)):int(np.sum(kinds[sample[ix]]==k)) for k in np.unique(kinds[sample[ix]])})
 results.append(dict(run=run,frames=len(other),task_passed=quality['passed'],reasons=quality['reasons'],progress_mm=quality['metrics']['target_final_progress_m']*1000,final10_signed_y_min_mm=float(np.min(-target[-10:,1])*1000),non_target_max_xy_mm=float(displacement.max()),non_target_max_frame=int(displacement.argmax()),first_non_target_displacement_frames={str(th):int(np.flatnonzero(displacement>th)[0]) if np.any(displacement>th) else None for th in [.01,1,5,10,13,15]},repair_steps=changed,displacement_at_first_repair_mm=float(displacement[changed[0]]) if changed else None,solved_substep_contacts=contacts))
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,episodes=results,source_sha256=bindings,analyzer_sha256=sha(__file__),training_ready=False,interpretation='Time ordering distinguishes pre-existing interference from repair-associated later evolution; rerun numerical divergence and coupled physics prevent assigning all trajectory differences uniquely to the repair. Both tasks remain failures.')
with (W/'joint_edge_intersection_physical_r1/SWAP_BOX_INTERFERENCE_FINDINGS.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(results,indent=2))
