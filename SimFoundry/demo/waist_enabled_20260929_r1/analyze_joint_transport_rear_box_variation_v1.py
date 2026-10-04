"""Three latest actual unselected rear-box trajectories: source/phase/bout comparison.
No success selection: include both passing and failing runs. Phase-assigned
motion is descriptive, not causal attribution; small early differences are not
proof of a particular simulator nondeterminism mechanism.
"""
from pathlib import Path
import json,hashlib,datetime,collections
import numpy as np
W=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();runs=['front_box_recenter_physical_r2','inactive_transport_physical_r1','joint_transport_physical_r1'];records=[];sources={};baseline=None
helpers=['rear_cop_route.py','region_top_contact.py','box_center_preference_plan.py','box_recovery_entry_lift.py','box_entry_lift_recontact_guarded.py','joint_edge_inward_command.py','joint_edge_inward_adapter.py','waist_coordination_clearance.py','task_ik.py','task_ik_precision.py','clearance_runtime.py']
for run in runs:
 ep=W/run/'case_840023/layout_840023_push_box_to_bin';fr=json.loads((ep/'frontal_bypass.json').read_text());rows=fr['rows'];assert len(rows)==1199 and [r['step'] for r in rows]==list(range(1,1200));assert not fr['plan'].get('front_route_selected')
 quality=json.loads((ep/'quality.json').read_text());assert quality['frames']==1200
 with np.load(ep/'raw.npz') as z:q=z['q'].copy();u=z['action'].copy()
 with np.load(ep/'trace.npz') as z:box=z['box'].copy();bag=z['mailer'].copy()
 assert np.max(abs(q[0,12:23]))<1e-4 and np.max(abs(u[0,12:23]))<1e-4
 prov=json.loads((ep.parent/'provenance.json').read_text());helper_hashes={}
 for name in helpers:
  keys=[k for k in prov['source_sha256'] if Path(k).name==name];assert len(keys)==1,(name,keys);k=keys[0];assert sha(ep.parent/'source_snapshot'/k)==prov['source_sha256'][k];helper_hashes[name]=prov['source_sha256'][k]
 phases=collections.defaultdict(lambda:dict(frames=0,measured_signed_progress_mm=0.,last_tick_observed_loaded_frames=0));bouts=[];start=None;lookup={r['step']:r for r in rows};dy=-np.diff(box[:,1].astype(float))*1000
 phases['first_zero_frame']['frames']=1;phases['first_zero_frame']['measured_signed_progress_mm']=float(dy[0])
 for t in range(1,1200):
  r=lookup[t];bucket=phases[r['mode']];bucket['frames']+=1;bucket['last_tick_observed_loaded_frames']+=int(r.get('contact_load',{}).get('observed_vertical_load_n',0.)>=.3)
  if t<1199:bucket['measured_signed_progress_mm']+=float(dy[t])
  if r['mode']=='top_push' and start is None:start=t
  if start is not None and (r['mode']!='top_push' or t==1199):
   last=t-1 if r['mode']!='top_push' else t;exit_step=t if r['mode']!='top_push' else None;endobs=min(last+1,1199);b=dict(start=start,last=last,frames=last-start+1,measured_progress_mm=float((box[start,1]-box[endobs,1])*1000),loaded_observation_frames=sum(lookup[j].get('contact_load',{}).get('observed_vertical_load_n',0.)>=.3 for j in range(start,last+1)),exit_step=exit_step,exit_mode=None if exit_step is None else r['mode'],new_recontact=bool(exit_step is not None and r['recontacts']>lookup[last]['recontacts']),exit_reason=None if exit_step is None or r['mode']=='top_release' else r.get('last_recontact_reason'),tilt_before_exit_rad=lookup[last]['observed_parcel_tilt_rad'],tilt_at_exit_rad=None if exit_step is None else r['observed_parcel_tilt_rad']);bouts.append(b);start=None
 for b,nxt in zip(bouts,bouts[1:]):b['frames_until_next_push']=nxt['start']-b['last']-1;b['between_modes']=dict(collections.Counter(lookup[t]['mode'] for t in range(b['last']+1,nxt['start'])))
 total=float((box[0,1]-box[-1,1])*1000);assert abs(sum(x['measured_signed_progress_mm'] for x in phases.values())-total)<1e-7;assert sum(x['frames'] for x in phases.values())==1200
 row=dict(run=run,passed=quality['passed'],progress_mm=total,required_zone_progress_mm=float((box[0,1]+.2)*1000),final_zone_deficit_mm=float(max(0.,box[-1,1]+.2)*1000),initial_box_xyz=box[0].tolist(),initial_bag_xyz=bag[0].tolist(),non_target_max_xy_mm=float(np.linalg.norm(bag[:,:2]-bag[0,:2],axis=1).max()*1000),phase_allocation=dict(phases),bouts=bouts,rear_helper_sha256=helper_hashes)
 if baseline is None:baseline=dict(q=q,u=u,box=box,bag=bag,args=prov['args'],helpers=helper_hashes)
 else:
  row['helpers_different_from_first_center']=[n for n in helpers if helper_hashes[n]!=baseline['helpers'][n]];assert not row['helpers_different_from_first_center']
  row['argument_differences_from_first_center']={k:dict(parent=baseline['args'].get(k),current=prov['args'].get(k)) for k in set(prov['args'])|set(baseline['args']) if baseline['args'].get(k)!=prov['args'].get(k)}
  first={}
  for name,values,old in [('q_upper',q[:,12:23],baseline['q'][:,12:23]),('action_upper',u[:,12:23],baseline['u'][:,12:23]),('box_position',box,baseline['box'])]:
   err=np.max(abs(values.astype(float)-old.astype(float)),axis=1);first[name]={str(tol):None if not np.any(err>tol) else int(np.flatnonzero(err>tol)[0]) for tol in [0.,1e-6,.001]}
  row['first_difference_steps_from_first_center']=first
 for f in [ep/'raw.npz',ep/'trace.npz',ep/'frontal_bypass.json',ep/'quality.json',ep.parent/'provenance.json']:sources[str(f)]=sha(f)
 for fn in ['front_loaded_z_priority.json','front_loaded_material_projection.json','inactive_transport_clearance.json','joint_transport_clearance.json']:
  if (ep/fn).exists():
   d=json.loads((ep/fn).read_text());count=sum(bool(r.get('applied',False)) for r in d['rows']);assert count==0;row[fn+'_applied']=count;sources[str(ep/fn)]=sha(ep/fn)
 records.append(row)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,records=records,source_sha256=dict(sources,**{str(Path(__file__)):sha(__file__)}),findings=['All three latest actual attempts retained, including passing direct parent and both failures. Eleven named rear runtime helpers are byte-identical; source identity alone does not prove identical dynamics.','Early joint differences precede visible box divergence; no attribution to unexecuted front variants or a proven numerical mechanism.','Later command/motion allocation and repeated recovery are observable budget costs; no quality gate relaxed.'],training_ready=False)
with (W/'joint_transport_physical_r1/REAR_BOX_THREE_RUN_BUDGET_DIAGNOSTIC.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps([{k:v for k,v in r.items() if k in ['run','passed','progress_mm','final_zone_deficit_mm','phase_allocation','first_difference_steps_from_first_center']} for r in records],indent=2))
