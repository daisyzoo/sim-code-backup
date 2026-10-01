"""Real measurement/synthetic-command fixtures and corruptions for the new auditor."""
from pathlib import Path
import copy,hashlib,json,sys
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_rear_core_slice_motion_probe'
sys.path[:0]=[str(stage),str(repo),str(w)]
from rear_cop_centering import RearCopCentering
from simfoundry.data.top_contact_load_geometry import loaded_forward_margin
from audit_rear_core_slice_motion_live import reconstruct
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();reports=[];negative=[]
for run in ['region_continuity_groups_r1','region_causal_response_groups_r1','region_causal_xy_groups_r2','region_measured_bounds_groups_r1','rear_cop_measured_bounds_groups_r1','rear_core_slice_groups_r1']:
 for cid,task in [(840001,'push_box_to_bin'),(840004,'nudge_mailer_to_bin')]:
  ep=w/run/f'case_{cid}/layout_{cid}_{task}';fr=json.loads((ep/'frontal_bypass.json').read_text());rows=fr['rows'];plan=fr['plan'];key='box' if 'push_box' in task else 'mailer';side='right' if key=='box' else 'left';actor='parcel_box' if key=='box' else 'mailer';direction=plan['direction']
  region=json.loads((ep/'region_approach.json').read_text())['rows'];handover=next((r['step'] for r in region if r['solver'] and r['solver'].get('handover')),None)
  size=np.array(plan['top_recontact']['contact_size_xyz']);scale=np.array([.96,.96,1.] if key=='box' else [.90,.88,1.]);core=size*scale
  plan['rear_cop_centering']=dict(enabled=True,core_slice_feedback=True,core_slice_motion_feedforward=True,actual_core_size_xyz=core.tolist(),core_inset_m=.01,feedback_gain=.05,max_x_step_m=.002,max_reference_x_lead_m=.030,preserve_first_loaded_push=True,parent_yz_unchanged=True,original_guard_priority=True)
  with np.load(ep/'trace.npz') as z:xyz=z[key].astype(float)
  with np.load(ep/'parcel_orientation.npz') as z:quat=z[key].astype(float)
  rotations=Rotation.from_quat(quat).as_matrix();packets={r['after_action_step']:r for r in json.loads((ep/'solved_contact_forces.json').read_text())['rows']};helper=RearCopCentering(core_slice_feedback=True,core_slice_motion_feedforward=True);previous=None;prior_mode=None
  for row in rows:
   t=row['step'];ref=np.asarray(row['observed_support_xyz']);parent=np.asarray(row['target_xyz']).copy();base=previous.copy() if previous is not None else ref.copy()
   if row['mode']=='top_push' and handover is not None and t>handover:
    if prior_mode=='top_press':base[2]=ref[2]
    goal=[row['push_x_anchor_m'],direction*min(.34,direction*base[1]+.003),row['parcel_top_xyz'][2]+.002+row['contact_load']['applied_z_bias_m']]
    parent=base+np.clip(np.asarray(goal)-base,[-.002,-.003,-.001],[.002,.003,.001])
   if handover is None or t<=handover:
    helper.reset();feedback=dict(override=False,reason='region_not_handed_over')
   else:
    contact=loaded_forward_margin(packets.get(t-1),side,actor,xyz[t],quat[t],size,direction)
    feedback=helper.update(mode=row['mode'],parent_xyz=parent,previous_xyz=base,reference_xyz=ref,object_xyz=xyz[t],object_rotation=rotations[t],core_size=core,cop_local=contact.get('weighted_contact_local'),normal_load_n=contact['normal_load_n'])
   row['target_xyz']=feedback['command_xyz'] if feedback['override'] else parent.tolist();row['rear_cop_centering']=feedback;previous=np.array(row['target_xyz']);prior_mode=row['mode']
  report=reconstruct(rows,plan,xyz,quat,packets,key,handover);assert report['passed'],(run,key,report['errors'][:4])
  candidates=[i for i,r in enumerate(rows) if r['rear_cop_centering']['override']]
  for i in candidates[::max(1,len(candidates)//2)][:2]:
   for field in ['x','y','z','anchor','override','reason','feedback','slice_interval','feedback_frame','feed','slice_target','slice_prior','anchor_feed','feedforward_frame']:
    changed=copy.deepcopy(rows);r=changed[i];f=r['rear_cop_centering']
    if field in ['x','y','z']:r['target_xyz'][['x','y','z'].index(field)]+=.004
    elif field=='anchor':f['anchor_local'][0]+=.005
    elif field=='override':f['override']=False
    elif field=='reason':f['reason']='original_non_push_mode'
    elif field=='slice_interval':f['core_x_displacement_interval_m'][0]+=.004
    elif field=='feedback_frame':f['feedback_frame']='world_anchor'
    elif field=='feed':f['feed_x_m']+=.004
    elif field=='slice_target':f['core_slice_target_world_x_m']+=.004
    elif field=='slice_prior':f['previous_core_slice_target_world_x_m']=(f['previous_core_slice_target_world_x_m'] or 0.)+.004
    elif field=='anchor_feed':f['object_anchor_feed_x_m']+=.004
    elif field=='feedforward_frame':f['feedforward_frame']='fixed_anchor'
    else:f['feedback_x_m']+=.004
    bad=reconstruct(changed,plan,xyz,quat,packets,key,handover);assert not bad['passed'],(run,key,i,field)
    negative.append(dict(run=run,episode=ep.name,step=r['step'],field=field,rejected=True))
  reports.append(dict(run=run,episode=ep.name,rows=len(rows),synthetic_overrides=report['overrides_checked'],passed=True,source_sha256={f:sha(ep/f) for f in ['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','region_approach.json','solved_contact_forces.json']}))
out=dict(passed=True,rows=reports,negative_checks=negative,total_synthetic_overrides=sum(r['synthetic_overrides'] for r in reports),auditor_sha256=sha(w/'audit_rear_core_slice_motion_live.py'),helper_sha256=sha(stage/'rear_cop_centering.py'),checker_sha256=sha(Path(__file__)),physical_started=False,training_ready=False,scope='Twelve complete recorded measurement streams with explicitly synthetic commanded waypoints; independent force/COP and parentY/Z reconstruction plus corrupted fields. Not actual new closed-loop commands or contact outcomes.')
(stage/'AUDITOR_CHECK.json').write_text(json.dumps(out,indent=2));print(dict(passed=True,streams=len(reports),overrides=out['total_synthetic_overrides'],corruptions_rejected=len(negative)))
