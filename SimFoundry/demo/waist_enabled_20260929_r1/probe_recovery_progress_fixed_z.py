"""Same six inputs with a ceiling on nominal lift from the original emitted command."""
"""Fixed first/middle/last floor-bound input probes on both current failed tasks.
Retain all original geometry, pressure objective, joint limits and bias domain.
Only the explicitly labelled hypothetical predicted-X lower bound changes.
This diagnoses objective/feasibility tradeoffs; no simulated continuation,
independent full optimality claim, collector wiring or data admission.
"""
from pathlib import Path
import json,hashlib,datetime,sys,os
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_rear_transport_retry';sys.path[:0]=[str(W),str(S),str(ROOT)]
from rear_recovery_x_progress_fixed_z_probe import solve
from clearance_runtime import ClearanceGuard
from audit_unloaded_wrist_prior_live import HandModel
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();dest=W/'RECOVERY_PROGRESS_WITH_ORIGINAL_Z_CEILING.json';assert not dest.exists();rows=[];sources={};guard=ClearanceGuard(ROOT,S);hand=HandModel(ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',ROOT/'assets/robots/g1_hand_support_vertices.json')
def save(status,**kw):
 out=dict(status=status,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,source_sha256=sources,analyzer_sha256=sha(__file__),probe_sha256=sha(W/'rear_recovery_x_progress_fixed_z_probe.py'),physics=False,training_ready=False,**kw);tmp=dest.with_suffix('.tmp');tmp.write_text(json.dumps(out,indent=2));tmp.replace(dest)
try:
 save('running')
 for case,task in [(840004,'nudge_mailer_to_bin'),(840015,'push_box_to_bin')]:
  ep=W/'rear_transport_retry_physical_r1'/f'case_{case}'/f'layout_{case}_{task}';rr=json.loads((ep/'rear_corridor_recovery.json').read_text())['rows'];rs={r['step']:r for r in rr};sources[str(ep/'rear_corridor_recovery.json')]=sha(ep/'rear_corridor_recovery.json');candidates=[]
  for r in rr:
   f=r['recovery'].get('tracking_feedback',{}) if 'recovery' in r else {}
   if r['kind']=='loaded_recovery' and f.get('accepted') and abs((r['recovery']['reference_delta_xyz_m'][0]+f['correction_xyz_m'][0])-.0001)<1e-6:candidates.append(r)
  assert candidates
  for index in sorted(set([0,len(candidates)//2,len(candidates)-1])):
   r=candidates[index];t=r['step'];row=r['parent_row'];c=r['parent_coordinate'];q=np.asarray(c['upper_q']);previous=np.asarray(c['task_inputs']['previous']);kwargs=dict(enabled=True,guard=guard,row=row,coordinate=c,current=q,previous=previous,parent_command=r['parent_command'],recovery_active=True,tracking_feedback=True,previous_recovery_record=rs[t-1],**r['geometry']);offset0=np.asarray(row['control_offset_local']);T0=hand.fk(q,c['active_side']);Tbase=hand.fk(np.asarray(r['emitted_command']),c['active_side']);ceiling=float((Tbase[:3,3]+Tbase[:3,:3]@offset0-T0[:3,3]-T0[:3,:3]@offset0)[2]);kwargs['diagnostic_z_ceiling_m']=ceiling;cmd,result=solve(**kwargs);item=dict(episode=ep.name,step=t,hypothetical_predicted_x_floor_mm=.72*r['recovery']['requested_x_m']*1000,available=cmd is not None,result=result,original_command_z_ceiling_mm=ceiling*1000)
   if cmd is not None:
    assert result['applied'] and result['tracking_feedback']['accepted'];side=c['active_side'];offset=np.asarray(row['control_offset_local']);T0=hand.fk(q,side)
    def motion(x):
     T=hand.fk(x,side);return T[:3,3]+T[:3,:3]@offset-(T0[:3,3]+T0[:3,:3]@offset)
    actual_cmd=np.asarray(r['emitted_command']);bias=np.asarray(result['tracking_feedback']['correction_xyz_m']);delta=motion(cmd);assert delta[0]+bias[0]>=item['hypothetical_predicted_x_floor_mm']/1000-1e-7;assert abs(delta[1]+bias[1])<=1e-7;assert delta[2]<=ceiling+1e-7;assert guard.command(cmd,q,previous)['accepted']
    J=np.asarray(c['task_inputs']['jacobian']);e=np.asarray(result['recovery_error']);d=np.asarray(c['task_inputs']['damping']);active=slice(3,6) if side=='right' else slice(0,3);inactive=slice(0,3) if side=='right' else slice(3,6)
    def parts(x):
     residual=J@(x-q)-e;return dict(active_position_squared=float(residual[active]@residual[active]),inactive_position_squared=float(residual[inactive]@residual[inactive]),normal_squared=float(residual[6:]@residual[6:]),joint_regularization=float(sum((d*(x-q))**2)),linear_task_residual_mm=(residual[:6]*1000).tolist(),nonlinear_reference_delta_mm=(motion(x)*1000).tolist(),predicted_reference_delta_mm=((motion(x)+bias)*1000).tolist())
    item.update(independent_reference_delta_mm=(delta*1000).tolist(),baseline_cost_parts=parts(actual_cmd),probe_cost_parts=parts(cmd))
   rows.append(item);save('running');print(ep.name,t,item['available'],flush=True)
 save('complete',feasible_probes=sum(r['available'] for r in rows),total_probes=len(rows))
except BaseException as e:save('failed',error=repr(e));raise
