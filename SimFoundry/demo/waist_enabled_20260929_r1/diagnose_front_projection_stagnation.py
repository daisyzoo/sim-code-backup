"""Diagnose complete actual projection rollout; no counterfactual physics.
Independently recompute cap interval arithmetic and observed force sums. Full
native FK/route/COP/control audits remain required separately. Fixed material
boundary saturation is evidence of command suppression, not proof a wider cap
will succeed. No threshold changes or data admission.
"""
from pathlib import Path
import datetime,hashlib,json,sys
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;E=Path(sys.argv[1]).resolve();ROOT=W.parents[1]
from front_loaded_projection_independent_math import verify
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={}
def read(n):sources[str(E/n)]=sha(E/n);return json.loads((E/n).read_text())
def stats(x):
 a=np.asarray(x,float);assert np.isfinite(a).all();return dict(min=float(a.min()),median=float(np.median(a)),max=float(a.max()))
marker=read('READY_FOR_AUDIT.json');assert marker['executed_frames']==marker['requested_frames']==1200
for p,h in marker['source_sha256'].items():assert sha(p)==h
num=read('FRONT_PROJECTION_STAGE_NUMERIC_REVIEW.json');fr=read('frontal_bypass.json');clear=read('self_clearance.json');assert clear['failure'] is None
with np.load(E/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
with np.load(E/'trace.npz') as z:trace={k:z[k].copy() for k in ['box','mailer']}
with np.load(E/'parcel_orientation.npz') as z:quat={k:z[k].copy() for k in ['box','mailer']}
packets={r['after_action_step']:r for r in read('solved_contact_forces.json')['rows']};key='box' if 'push_box' in E.name else 'mailer';other='mailer' if key=='box' else 'box';side='right' if key=='box' else 'left';actor='parcel_box' if key=='box' else 'mailer';direction=-1 if key=='box' else 1
assert len(q)==len(u)==len(trace[key])==1200 and [r['step'] for r in fr['rows']]==list(range(1,1200))
by_step={r['step']:r for r in fr['rows']};records=[]
for row in fr['rows']:
 a=row.get('loaded_reference_cap')
 if not a or not a.get('applied'):continue
 t=row['step'];previous=by_step[t-1]['target_xyz'][:2];parent=a['parent_xy'];reference=row['observed_support_xyz'][:2];material=row['parcel_top_xyz'][:2]
 assert a['previous_command_xy']==previous and a['reference_xy']==reference and a['material_surface_xy']==material
 packet=packets[t-1];assert np.max(abs(np.array(packet['post_action_pose'][key])-trace[key][t]))<=2e-6
 rotation=Rotation.from_quat(quat[key][t]).as_matrix();normal=0.;handforce=np.zeros(3);tableforce=np.zeros(3);otherforce=np.zeros(3);other_contacts=0
 for c in packet['parcel_contacts']:
  slots=[i for i,s in enumerate(c['shapes']) if '/'+actor+'/' in s]
  if len(slots)!=1:continue
  force=np.asarray(c['force_world_N'],float)*(1. if slots[0]==1 else -1.)
  if any(side+'_wrist' in s for s in c['shapes']):
   handforce+=force;load=-float(force@rotation[:,2])
   if load>.05:normal+=load
  elif any('/table/' in s for s in c['shapes']):tableforce+=force
  else:otherforce+=force;other_contacts+=1
 v=verify(a,parent=parent,previous=previous,reference=reference,material=material,normal=normal);assert v['feasible']
 emitted=np.array(row['target_xyz'][:2]);assert np.max(abs(emitted-v['command_xy']))<1e-10
 drive=np.asarray(row['cop_slip_following']['drive_direction_xy'],float);assert abs(np.linalg.norm(drive)-1)<1e-7
 pd=np.asarray(parent)-previous;ed=emitted-previous;parent_drive=float(pd@drive);emit_drive=float(ed@drive);offset=emitted-material
 bound=np.isclose(abs(offset),.010,rtol=0,atol=1e-10)
 records.append(dict(step=t,route_stage=row['route_stage'],normal_load_n=normal,parent_drive_mm=parent_drive*1000,emitted_drive_mm=emit_drive*1000,suppressed_drive_mm=(parent_drive-emit_drive)*1000,material_offset_xy_mm=(offset*1000).tolist(),both_material_axes_saturated=bool(bound.all()),command_material_delta_error_mm=float(np.linalg.norm(ed-(np.array(material)-np.array(by_step[t-1]['parcel_top_xyz'][:2])))*1000),hand_force_world_N=handforce.tolist(),table_force_world_N=tableforce.tolist(),other_force_world_N=otherforce.tolist(),other_contact_count=other_contacts,hand_table_xy_balance_norm_N=float(np.linalg.norm((handforce+tableforce)[:2])),boundary_following_repair=a['boundary_following_repair']))
assert records
summaries={}
for label,selected in [('all_loaded',records),('late_steps600_1199',[r for r in records if r['step']>=600])]:
 assert selected;first,last=selected[0]['step'],selected[-1]['step'];summaries[label]=dict(rows=len(selected),step_range=[first,last],all_route_stages=sorted(set(r['route_stage'] for r in selected)),both_material_axes_saturated=sum(r['both_material_axes_saturated'] for r in selected),boundary_following_repairs=sum(r['boundary_following_repair'] for r in selected),normal_load_n=stats([r['normal_load_n'] for r in selected]),parent_drive_mm=stats([r['parent_drive_mm'] for r in selected]),emitted_drive_mm=stats([r['emitted_drive_mm'] for r in selected]),suppressed_drive_mm=stats([r['suppressed_drive_mm'] for r in selected]),command_material_delta_error_mm=stats([r['command_material_delta_error_mm'] for r in selected]),signed_y_progress_mm=float(direction*(trace[key][last,1]-trace[key][first,1])*1000),actual_target_xy_span_mm=(np.ptp(trace[key][first:last+1,:2],axis=0)*1000).tolist(),upper_q_max_per_joint_range_rad=float(np.ptp(q[first:last+1],axis=0).max()),upper_action_max_per_joint_range_rad=float(np.ptp(u[first:last+1],axis=0).max()),hand_force_world_median_N=np.median([r['hand_force_world_N'] for r in selected],axis=0).tolist(),table_force_world_median_N=np.median([r['table_force_world_N'] for r in selected],axis=0).tolist(),hand_table_xy_balance_norm_N=stats([r['hand_table_xy_balance_norm_N'] for r in selected]),other_contact_count=sum(r['other_contact_count'] for r in selected))
for p in [E/'raw.npz',E/'trace.npz',E/'parcel_orientation.npz',Path(__file__),W/'front_loaded_projection_independent_math.py']:sources[str(p)]=sha(p)
out=E/'FRONT_PROJECTION_STAGNATION_DIAGNOSTIC.json';assert not out.exists();report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,episode=E.name,frames=1200,original_task_and_pose_passed=num['original_task_and_pose_passed'],progress_mm=num['progress_mm'],non_target_max_xy_mm=num['non_target_max_xy_mm'],failed_original_reasons=num['recomputed_quality']['reasons'],summaries=summaries,records=records,source_sha256=sources,independent_original_full_control_audits_required=True,physical_success_of_alternative_unproven=True,training_ready=False)
out.write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ['scope','records','source_sha256']},indent=2))
