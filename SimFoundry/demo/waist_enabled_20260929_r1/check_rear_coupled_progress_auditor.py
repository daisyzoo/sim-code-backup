"""Raw-force input replay and corrupted-stream rejection for new independent audit."""
from pathlib import Path
import json,sys,copy,hashlib,importlib.util
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;stage=w/'staged_rear_coupled_progress_probe';sys.path[:0]=[str(stage),str(w/'staged_front_drive_increment'),str(w)]
from rear_cop_centering import RearCopCentering
from rear_coupled_progress import govern_rear_progress
from audit_rear_coupled_progress_live import reconstruct
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();reports=[];total_rejected=0
for run in ['rear_core_slice_groups_r1','front_drive_increment_groups_r1','front_edge_speed_groups_r1']:
 for cid,task in [(840001,'push_box_to_bin'),(840004,'nudge_mailer_to_bin')]:
  ep=w/run/f'case_{cid}/layout_{cid}_{task}';fr=json.loads((ep/'frontal_bypass.json').read_text());plan=fr['plan'];rows=fr['rows'];key='box' if cid==840001 else 'mailer';side='right' if key=='box' else 'left';actor='parcel_box' if key=='box' else 'mailer'
  oldaudit=json.loads((ep/'REAR_COP_CORE_SLICE_LIVE_AUDIT.json').read_text());assert oldaudit['passed'] and not oldaudit['errors']
  for n,h in oldaudit['source_sha256'].items():assert sha(ep/n)==h
  with np.load(ep/'trace.npz') as z:xyz=z[key].astype(float)
  with np.load(ep/'parcel_orientation.npz') as z:quat=z[key].astype(float)
  R=Rotation.from_quat(quat).as_matrix();packets={r['after_action_step']:r for r in json.loads((ep/'solved_contact_forces.json').read_text())['rows']}
  region=json.loads((ep/'region_approach.json').read_text())['rows'];handover=next((r['step'] for r in region if r['solver'] and r['solver'].get('handover')),None);assert handover is not None
  original=reconstruct(rows,plan,xyz,quat,packets,key,handover);assert original['passed'],original['errors'][:4]
  candidate_plan=copy.deepcopy(plan);candidate_plan['rear_coupled_progress']=dict(enabled=True,core_inset_m=.01,parent_xz_unchanged=True,original_guard_priority=True,first_loaded_preserved=True,infeasible_fallback='preserve_parent');size=np.array(plan['rear_cop_centering']['actual_core_size_xyz']);state=RearCopCentering(core_slice_feedback=True);previous=None;previous_mode=None;synth=[];changed=[];fallback=[]
  for original_row in rows:
   row=copy.deepcopy(original_row);t=row['step'];ref=np.array(row['observed_support_xyz']);parent=np.array(row['target_xyz']);base=ref.copy() if previous is None else previous.copy()
   if previous_mode=='top_press':base[2]=ref[2]
   if row['mode']=='top_push' and t>handover:
    parent=np.array([base[0]+np.clip(row['push_x_anchor_m']-base[0],-.002,.002),base[1]+np.clip(plan['direction']*min(.34,plan['direction']*base[1]+.003)-base[1],-.003,.003),base[2]+np.clip(row['parcel_top_xyz'][2]+.002+row['contact_load']['applied_z_bias_m']-base[2],-.001,.001)])
   points=[];weights=[];packet=packets.get(t-1)
   if packet:
    assert np.max(abs(np.array(packet['post_action_pose'][key])-xyz[t]))<1e-6
    for c in packet['parcel_contacts']:
     slots=[i for i,s in enumerate(c['shapes']) if '/'+actor+'/' in s]
     if len(slots)!=1 or not any(side+'_wrist' in s for s in c['shapes']):continue
     force=np.array(c['force_world_N'])*(1 if slots[0]==1 else -1);load=-float(force@R[t,:,2])
     if load>.05:points.append(c['position_world']);weights.append(load)
   normal=sum(weights);cop=R[t].T@(np.average(points,axis=0,weights=weights)-xyz[t]) if weights else None
   if t<=handover:
    state.reset();f=dict(override=False,reason='region_not_handed_over')
   else:
    f=state.update(mode=row['mode'],parent_xyz=parent,previous_xyz=base,reference_xyz=ref,object_xyz=xyz[t],object_rotation=R[t],core_size=size,cop_local=cop,normal_load_n=normal)
    if f['override']:parent=np.array(f['command_xyz'])
    progress=(govern_rear_progress(enabled=True,mode=row['mode'],previous_xyz=base,parent_xyz=parent,object_rotation=R[t],core_size=size,cop_local=cop,normal_load_n=normal,direction=plan['direction']) if f['override'] else dict(override=False,reason='original_rear_not_overridden'))
    row['rear_coupled_progress']=progress
    if progress['override']:parent=np.array(progress['command_xyz']);changed.append(len(synth))
    else:fallback.append(len(synth))
   row['rear_cop_centering']=f;row['target_xyz']=parent.tolist();synth.append(row);previous=parent;previous_mode=row['mode']
  result=reconstruct(synth,candidate_plan,xyz,quat,packets,key,handover);assert result['passed'],(run,task,result['errors'][:5]);assert changed
  bads=[]
  for dimension in range(3):
   b=copy.deepcopy(synth);b[changed[0]]['target_xyz'][dimension]+=.001;bads.append(('emitted_'+str(dimension),b,candidate_plan,packets))
  for field in ['scale','command_xyz','parent_delta_xyz_m','projected_local_xy_delta_m','local_xy_margin_m','constraints','feasible_scale_interval','override','reason']:
   b=copy.deepcopy(synth);v=b[changed[0]]['rear_coupled_progress']
   if field=='scale':v[field]*=.5
   elif field=='constraints':v[field][0]['scaled_m']+=.001
   elif field=='override':v[field]=False
   elif field=='reason':v[field]='disabled'
   else:v[field][0]+=.001
   bads.append((field,b,candidate_plan,packets))
  b=copy.deepcopy(synth);del b[changed[0]]['rear_coupled_progress'];bads.append(('missing_progress',b,candidate_plan,packets))
  b=copy.deepcopy(synth);b[changed[0]]['rear_cop_centering']['command_xyz'][1]+=.001;bads.append(('parent_y',b,candidate_plan,packets))
  b=copy.deepcopy(synth);i=next(i for i,r in enumerate(b) if r['step']>handover and r['mode']!='top_push');b[i]['rear_coupled_progress']=copy.deepcopy(b[changed[0]]['rear_coupled_progress']);bads.append(('guard_bypass',b,candidate_plan,packets))
  p=copy.deepcopy(candidate_plan);p['rear_coupled_progress']['enabled']=False;bads.append(('disabled_trace',synth,p,packets))
  damaged=copy.deepcopy(packets);t=synth[changed[0]]['step'];altered=0
  for c in damaged[t-1]['parcel_contacts']:
   if any('/'+actor+'/' in sh for sh in c['shapes']) and any(side+'_wrist' in sh for sh in c['shapes']):c['position_world'][0]+=.003;altered+=1
  assert altered;bads.append(('raw_contact_position',synth,candidate_plan,damaged))
  rejected=[]
  for name,b,p,pk in bads:
   result=reconstruct(b,p,xyz,quat,pk,key,handover);assert not result['passed'],(name,run,task);rejected.append(name)
  total_rejected+=len(rejected);reports.append(dict(run=run,episode=ep.name,default_frames=len(rows),synthetic_modified_steps=len(changed),rejected=rejected,source_sha256={n:sha(ep/n) for n in ['trace.npz','parcel_orientation.npz','frontal_bypass.json','region_approach.json','solved_contact_forces.json','REAR_COP_CORE_SLICE_LIVE_AUDIT.json']}));print(run,key,len(rows),len(changed),len(rejected),flush=True)
for value in [1,None,'yes']:
 p=copy.deepcopy(candidate_plan);p['rear_coupled_progress']['enabled']=value
 try:reconstruct(synth,p,xyz,quat,packets,key,handover)
 except AssertionError:total_rejected+=1
 else:raise AssertionError('Invalid enable accepted')
report=dict(passed=True,episodes=reports,total_default_frames=sum(x['default_frames'] for x in reports),total_synthetic_modified_steps=sum(x['synthetic_modified_steps'] for x in reports),total_rejected=total_rejected,auditor_sha256=sha(w/'audit_rear_coupled_progress_live.py'),source_sha256={n:sha(stage/n) for n in ['rear_coupled_progress.py','rear_cop_route.py']},checker_sha256=sha(Path(__file__)),collector_wired=False,physical_started=False,training_ready=False,scope='Default actual streams and synthesized full command histories reconstructed from original recorded modes/observations and raw forces; candidate emissions propagate into subsequent command history only, not physics. Independent LP auditor verifies parent XYZ and external Y. Corruption rejects emittedXYZ, feedback parentY, scale/constraints/geometry, missing/disabled/guard traces and raw contact position. CLI entry and collector wiring remain separate.')
p=stage/'AUDITOR_CHECK.json';assert not p.exists();p.write_text(json.dumps(report,indent=2));print('PASSED',report['total_default_frames'],report['total_synthetic_modified_steps'],total_rejected)
