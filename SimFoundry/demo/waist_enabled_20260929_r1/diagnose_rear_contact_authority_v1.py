"""Separate commanded correction, actual support motion, and COP redistribution.

Observational closed trajectories only: not a learned inverse or causal model.
"""
from pathlib import Path
import json, hashlib, collections
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
out=[]
for run in ['rear_core_slice_groups_r1','rear_core_slice_motion_groups_r1','front_drive_increment_groups_r1']:
    root=w/run
    result=json.loads((root/'RESULT.json').read_text())
    assert result['actual_review_complete'] and result['push_total']==8
    for cid,task in [(840001,'push_box_to_bin'),(840004,'nudge_mailer_to_bin')]:
        ep=root/f'case_{cid}/layout_{cid}_{task}'
        audit_name='REAR_CORE_SLICE_MOTION_LIVE_AUDIT.json' if 'motion_groups' in run else 'REAR_COP_CORE_SLICE_LIVE_AUDIT.json'
        audit=json.loads((ep/audit_name).read_text()); assert audit['passed'] and not audit['errors']
        for n,h in audit['source_sha256'].items(): assert sha(ep/n)==h
        fr=json.loads((ep/'frontal_bypass.json').read_text()); rows=fr['rows']; bystep={r['step']:r for r in rows}
        key='box' if 'push_box' in task else 'mailer';actor='parcel_box' if key=='box' else 'mailer';side='right' if key=='box' else 'left'
        core=np.array(fr['plan']['region_causal_response']['actual_core']['collision_core_size_xyz'])
        with np.load(ep/'trace.npz') as z: xyz=z[key].astype(float)
        with np.load(ep/'parcel_orientation.npz') as z: rot=Rotation.from_quat(z[key]).as_matrix()
        with np.load(ep/'raw.npz') as z: q=z['q'].astype(float);u=z['action'].astype(float)
        packets={p['after_action_step']:p for p in json.loads((ep/'solved_contact_forces.json').read_text())['rows']}
        samples={};bouts=[];active=[];cop_checks=0
        for row in rows:
            t=row['step'];p=packets.get(t-1);points=[];weights=[]
            if p and row['mode']=='top_push':
                assert np.max(abs(np.array(p['post_action_pose'][key])-xyz[t]))<1e-6
                for c in p['parcel_contacts']:
                    slots=[i for i,s in enumerate(c['shapes']) if '/'+actor+'/' in s]
                    if len(slots)!=1 or not any(side+'_wrist' in s for s in c['shapes']):continue
                    f=np.array(c['force_world_N'])*(1 if slots[0]==1 else -1);load=-float(f@rot[t,:,2])
                    if load>.05:points.append(c['position_world']);weights.append(load)
            if sum(weights)>=.3:
                cop=np.average(points,axis=0,weights=weights);local=rot[t].T@(cop-xyz[t]);c=row.get('rear_cop_centering',{})
                if c.get('override'):
                    assert np.max(abs(cop-np.array(c['cop_world'])))<1e-7;cop_checks+=1
                samples[t]=dict(cop=cop,local=local,normal=sum(weights))
            if row['mode']=='top_push': active.append(t)
            elif active:
                loaded=[s for s in active if s in samples]
                if loaded:
                    first,last=loaded[0],loaded[-1];a,b=bystep[first],bystep[last];sa,sb=samples[first],samples[last]
                    overrides=[bystep[k] for k in active if bystep[k].get('rear_cop_centering',{}).get('override')]
                    physical_a=np.array(a['observed_physical_support_xyz']);physical_b=np.array(b['observed_physical_support_xyz'])
                    # Exact telescoping identity in world X, using actual lowest support
                    # vertex (which can change across frames), not a material contact point.
                    dx_cop=sb['cop'][0]-sa['cop'][0];dx_obj=xyz[last,0]-xyz[first,0];dx_support=physical_b[0]-physical_a[0]
                    redistribution=(sb['cop'][0]-physical_b[0])-(sa['cop'][0]-physical_a[0])
                    assert abs((dx_cop-dx_obj)-((dx_support-dx_obj)+redistribution))<1e-12
                    used=np.array([x['step'] for x in overrides],dtype=int)
                    reason='terminal_release' if row['mode']=='top_release' else row.get('last_recontact_reason')
                    bouts.append(dict(first_loaded=first,last_loaded=last,exit_step=t,exit_reason=reason,push_steps=len(active),loaded_steps=len(loaded),override_steps=len(overrides),first_cop_local_x_mm=float(sa['local'][0]*1000),last_cop_local_x_mm=float(sb['local'][0]*1000),first_x_edge_margin_mm=float((core[0]/2-abs(sa['local'][0]))*1000),last_x_edge_margin_mm=float((core[0]/2-abs(sb['local'][0]))*1000),object_world_x_delta_mm=float(dx_obj*1000),support_world_x_delta_mm=float(dx_support*1000),support_relative_object_world_x_delta_mm=float((dx_support-dx_obj)*1000),cop_relative_object_world_x_delta_mm=float((dx_cop-dx_obj)*1000),cop_relative_lowest_support_world_x_delta_mm=float(redistribution*1000),command_x_first_to_last_mm=float((b['target_xyz'][0]-a['target_xyz'][0])*1000),first_command_to_physical_support_x_mm=float((a['target_xyz'][0]-physical_a[0])*1000),last_command_to_physical_support_x_mm=float((b['target_xyz'][0]-physical_b[0])*1000),correction_opposite_slice_count=sum(x['rear_cop_centering']['command_delta_x_m']*x['rear_cop_centering']['error_x_m']<-1e-12 for x in overrides),command_2mm_saturation_count=sum(abs(x['rear_cop_centering']['command_delta_x_m'])>=.002-1e-9 for x in overrides),command_30mm_lead_saturation_count=sum(abs(x['rear_cop_centering']['command_reference_lead_x_m'])>=.03-1e-9 for x in overrides),waist_planning_bound_count=int(np.sum(abs(u[used,12])>=.98-1e-6)),last_normal_load_n=sb['normal']))
                active=[]
        lost=[b for b in bouts if b['exit_reason']=='lost_contact']
        summary=dict(lost_bouts=len(lost),lost_bouts_support_moves_inward_relative_object=sum(b['support_relative_object_world_x_delta_mm']>0 for b in lost),lost_bouts_cop_moves_outward_relative_object=sum(b['cop_relative_object_world_x_delta_mm']<0 for b in lost),lost_bouts_inward_support_but_outward_cop=sum(b['support_relative_object_world_x_delta_mm']>0 and b['cop_relative_object_world_x_delta_mm']<0 for b in lost),lost_bouts_any_waist_bound=sum(b['waist_planning_bound_count']>0 for b in lost),lost_bouts_any_x_step_bound=sum(b['command_2mm_saturation_count']>0 for b in lost),lost_bouts_any_x_lead_bound=sum(b['command_30mm_lead_saturation_count']>0 for b in lost))
        item=dict(run=run,episode=ep.name,independent_cop_reconstructions=cop_checks,summary=summary,bouts=bouts,unfinished_push_steps=len(active),source_sha256={n:sha(ep/n) for n in ['trace.npz','parcel_orientation.npz','raw.npz','frontal_bypass.json','solved_contact_forces.json',audit_name]},closed_result_sha256=sha(root/'RESULT.json'));out.append(item);print(run,key,summary,flush=True)
report=dict(episodes=out,checker_sha256=sha(Path(__file__)),training_ready=False,scope='Observed closed rear trajectories. COP reconstructed independently from prior solved contacts; original source hashes verified. WorldX exact decomposition separates lowest support motion from COP redistribution. Lowest vertex may change, not a fixed material point; rotation also changes local margins. No causal gain estimate, continuous contact proof, prediction, or controller change.')
p=w/'REAR_CONTACT_AUTHORITY_DIAGNOSIS.json';assert not p.exists();p.write_text(json.dumps(report,indent=2))
