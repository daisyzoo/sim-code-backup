"""Fixed real physical observations, sequential candidate action history; not physics."""
from pathlib import Path
import sys,json,hashlib,copy,importlib.util
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_joint_edge_retry';sys.path[:0]=[str(stage),str(repo),str(w)]
from joint_edge_adapter import refine_record
from articulated_hand_geometry import ArticulatedHandGeometry
from simfoundry.data.top_contact_bypass import rotation_xyzw
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
from audit_rear_coupled_execution_live import replay_record
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();root=stage/'entry_fixtures';assert not root.exists();root.mkdir();parent=w/'joint_edge_groups_r1';manifest=json.loads((w/'staged_joint_edge_command/MANIFEST.json').read_text());model=ArticulatedHandGeometry(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json');results=[]
for cid,task in [(840001,'push_box_to_bin'),(840004,'nudge_mailer_to_bin'),(840001,'nudge_mailer_to_bin')]:
 source=parent/f'case_{cid}'/f'layout_{cid}_{task}';case=root/(str(cid)+'_'+task);ep=case/source.name;ep.mkdir(parents=True);prov=json.loads((source.parent/'provenance.json').read_text());prov['args']['rear_joint_edge_command']=True;prov['args']['rear_joint_edge_analytic_retry']=True;prov['source_sha256']={n:h for n,h in prov['source_sha256'].items() if '/staged_' not in n};newpaths={}
 for name in manifest['source_sha256']:
  p=stage/name;rel=str(p.relative_to(repo));prov['source_sha256'][rel]=sha(p);newpaths[rel]=p
 for rel in prov['source_sha256']:
  original=newpaths.get(rel,source.parent/'source_snapshot'/rel);dest=case/'source_snapshot'/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.symlink_to(original.resolve());assert sha(dest)==prov['source_sha256'][rel]
 assert len(prov['source_sha256'])==60
 (case/'provenance.json').write_text(json.dumps(prov,indent=2))
 for name in ['trace.npz','parcel_orientation.npz','expert_control.json','solved_contact_forces.json']:
  if (source/name).exists():(ep/name).symlink_to((source/name).resolve())
 with np.load(source/'raw.npz') as z:raw={k:z[k].copy() for k in ['q','action','task_id','collect_meta']}
 q=raw['q'][:,12:23].astype(np.float32);original_u=raw['action'][:,12:23].copy();actual=raw['action'][:,12:23].copy();fr=json.loads((source/'frontal_bypass.json').read_text());coords=json.loads((source/'coordination.json').read_text());cs={c['step']:c for c in coords};experts={r['step']:r for r in json.loads((source/'expert_control.json').read_text())};enabled=bool(fr['plan'].get('rear_joint_xy_progress',{}).get('enabled'));side='right' if 'push_box' in task else 'left';key='box' if side=='right' else 'mailer';rows=[]
 with np.load(source/'trace.npz') as z:obj=z[key].copy()
 with np.load(source/'parcel_orientation.npz') as z:quat=z[key].copy()
 if enabled:
  fr['plan']['rear_joint_edge_command']=dict(enabled=True,core_inset_m=.01,waist_command_limit_rad=.98,waist_step_rad=.015,arm_step_rad=.04,final_slew_rad=.055,original_guard_priority=True,first_loaded_preserved=True,requires_joint_xy_override=True,reference='current_offset_frozen_virtual_reference_not_physical_contact',fallback='preserve_parent_command',full_push_ik_trace=True)
  fr['plan']['rear_joint_edge_analytic_retry']=dict(enabled=True,primary_solver_unchanged=True,retry_status=8,finite_endpoint_required=True,maximum_retries=1,initializer='original_linear_feasible_point',objective_bounds_tolerances_unchanged=True,failed_retry='preserve_parent_command')
  spec=importlib.util.spec_from_file_location('fixture_parent_ik',source.parent/'source_snapshot/simfoundry/data/bounded_ik.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
  low=np.asarray(U1_JOINT_LIMIT_LO)[12:23].copy();high=np.asarray(U1_JOINT_LIMIT_HI)[12:23].copy();low[0]=-.98;high[0]=.98;limits=np.full(11,.04);limits[0]=.015;penalty=np.full(11,np.float32(.045**2),dtype=np.float32);penalty[0]=np.float32(.12**2)
  for f in fr['rows']:
   t=f['step'];c=cs[t];prev=actual[t-1]
   if f['mode']=='top_push':
    J=np.vstack([np.asarray(c['control_jacobian_world'],dtype=np.float32),np.asarray(c['contact_normal_tracking']['jacobian'],dtype=np.float32)]);err=[]
    for hand in ['left','right']:
     target=f['target_xyz'] if hand==side else c['inactive_anchor'];err.extend(np.clip(np.float32(.72)*(np.asarray(target,dtype=np.float32)-np.asarray(c['control_point_positions'][hand],dtype=np.float32)),np.float32(-.035),np.float32(.035)).tolist())
    error=np.r_[np.asarray(err,dtype=np.float32),np.asarray(c['contact_normal_tracking']['error'],dtype=np.float32)]
    dq=mod.bounded_damped_step(J,error,q[t],low,high,limits,np.sqrt(penalty),preferred_step=np.zeros(11,dtype=np.float32));target=q[t]+dq;target[0]=np.clip(target[0],-.98,.98);original=target.astype(np.float32)
   else:
    assert np.array_equal(prev,original_u[t-1]),'Changed history reaches unmodeled nonpush controller'
    original=np.asarray(c['joint_edge_refinement']['parent_final_upper_command'],dtype=np.float32)
   original=np.clip(np.clip(original,prev-np.float32(.055),prev+np.float32(.055)),np.asarray(U1_JOINT_LIMIT_LO)[12:23],np.asarray(U1_JOINT_LIMIT_HI)[12:23]).astype(np.float32)
   if f['mode']=='top_push':replay_record(c,f,experts[t],q[t],prev,original,side,mod.bounded_damped_step)
   command,trace=refine_record(enabled=True,row=f,coordinate=c,current=q[t],previous=prev,parent_command=original,object_xyz=obj[t],object_rotation=rotation_xyzw(quat[t].tolist()),core_size=fr['plan']['region_causal_response']['actual_core']['collision_core_size_xyz'],model=model,side=side,analytic_retry=True)
   actual[t]=command;c['joint_edge_refinement']=trace;rows.append(dict(step=t,overridden=trace['override'],reason=trace['reason']))
 if (source/'region_approach.json').exists():
  region=json.loads((source/'region_approach.json').read_text())
  for record in region['rows']:
   t=record['step']
   if not np.array_equal(actual[t-1],original_u[t-1]):assert record['solver'] is None
   record['current_tracking_residual_rad']=(q[t]-actual[t-1]).tolist()
  (ep/'region_approach.json').write_text(json.dumps(region))
 raw['action'][:,12:23]=actual;np.savez(ep/'raw.npz',**raw);(ep/'coordination.json').write_text(json.dumps(coords));(ep/'frontal_bypass.json').write_text(json.dumps(fr));(ep/'FIXTURE_ONLY.json').write_text(json.dumps(dict(training_ready=False,physical_observations='unchanged real parent; synthetic actual commands sequentially propagated',rgb_omitted=True,not_physics=True)))
 results.append(dict(source=str(source),fixture=str(ep),selected=enabled,changed_commands=int(np.sum(np.max(abs(actual-original_u),axis=1)>0)),candidate_overrides=sum(x['overridden'] for x in rows),numeric_fallbacks=sum(x['reason']=='nonlinear_solver_failed' for x in rows),source_sha256={n:sha(source/n) for n in ['raw.npz','coordination.json','frontal_bypass.json','region_approach.json','trace.npz','parcel_orientation.npz','expert_control.json','solved_contact_forces.json'] if (source/n).exists()}));print(results[-1],flush=True)
(stage/'ENTRY_FIXTURES.json').write_text(json.dumps(dict(rows=results,checker_sha256=sha(Path(__file__)),collector_sha256=sha(stage/'collect_paired_sorting.py'),adapter_sha256=sha(stage/'joint_edge_adapter.py'),helper_sha256=sha(stage/'joint_edge_command.py'),training_ready=False,scope=__doc__),indent=2))
