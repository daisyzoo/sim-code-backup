"""Physical recovery outcome: actual same-point FK, actual object motion and gates.
Uses post-action measurements, never solver predictions as evidence of movement.
Descriptive comparison with fixed original and latched trajectories is not a
unique friction/actuator causal attribution and does not admit training data.
"""
from pathlib import Path
import sys,json,hashlib,datetime,collections
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path[:0]=[str(W),str(ROOT)]
from audit_unloaded_wrist_prior_live import HandModel
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();ep=Path(sys.argv[1]).resolve();dest=ep/'REAR_TRACKING_PHYSICAL_EFFECT.json';assert not dest.exists();sources={}
def read(p):
 p=Path(p);sources[str(p)]=sha(p);return json.loads(p.read_text())
model=HandModel(ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',ROOT/'assets/robots/g1_hand_support_vertices.json')
for n in ['raw.npz','trace.npz']:sources[str(ep/n)]=sha(ep/n)
with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float);task=str(z['task_id'])
assert task in ['push_box_to_bin','nudge_mailer_to_bin'];n=len(q);assert q.shape==u.shape==(n,11)
side='right' if task=='push_box_to_bin' else 'left';key='box' if side=='right' else 'mailer';other='mailer' if key=='box' else 'box';direction=-1 if side=='right' else 1
with np.load(ep/'trace.npz') as z:pos={k:z[k].astype(float) for k in ['box','mailer']}
log=read(ep/'rear_corridor_recovery.json');assert log['executed_action_count']==n
records=log['rows'];assert len({r['step'] for r in records})==len(records)
post={r['step']:r for r in read(ep/'self_clearance.json')['rows'] if r['phase']=='post'};packets={r['after_action_step']:r for r in read(ep/'solved_contact_forces.json')['rows']};quality=read(ep/'quality.json');rows=[];all_executed=[r for r in records if r['step']<n];stopped=[r['step'] for r in records if r['step']>=n]
for r in all_executed:
 if r['kind']!='loaded_recovery':continue
 t=r['step'];qpost=np.asarray(post[t]['upper_q'],float);offset=np.asarray(r['parent_row']['control_offset_local'],float);assert np.array_equal(u[t],r['emitted_command'])
 if t+1<n:assert max(abs(qpost-q[t+1]))<1e-6
 def point(x):
  T=model.fk(x,side);return T[:3,3]+T[:3,:3]@offset
 measured=point(q[t]);nominal=point(u[t]);real=point(qpost);assert max(abs(measured-r['parent_row']['observed_support_xyz']))<2e-6;assert max(abs(nominal-r['commit']['new']['command']))<2e-6
 packet=packets[t];target_after=np.asarray(packet['post_action_pose'][key]);other_after=np.asarray(packet['post_action_pose'][other]);target_delta=target_after-pos[key][t];feedback=r['recovery'].get('tracking_feedback',{});active=feedback.get('accepted') is True
 item=dict(step=t,tracking_active=active,tracking_reason=feedback.get('reason','disabled'),nominal_delta_xyz_mm=((nominal-measured)*1000).tolist(),actual_delta_xyz_mm=((real-measured)*1000).tolist(),object_delta_xyz_mm=(target_delta*1000).tolist(),object_signed_y_mm=float(direction*target_delta[1]*1000),non_target_post_xy_mm=float(np.linalg.norm(other_after[:2]-pos[other][0,:2])*1000),filtered_load_n=r['parent_row']['contact_load']['filtered_vertical_load_n'])
 if active:
  bias=np.asarray(feedback['correction_xyz_m']);assert feedback['step']==t and feedback['previous_step']==t-1;prior_prediction=measured-point(u[t-1]);assert max(abs(prior_prediction[:2]-bias[:2]))<2e-10
  predicted=nominal-measured+bias;err=real-measured-predicted
  item.update(predicted_delta_xyz_mm=(predicted*1000).tolist(),prediction_error_xy_mm=(err[:2]*1000).tolist())
 rows.append(item)
def stats(values):
 a=np.asarray(values,float)
 if not a.size:return None
 return dict(count=len(a),min=float(a.min()),median=float(np.median(a)),mean=float(a.mean()),p95=float(np.quantile(a,.95)),max=float(a.max()),sum=float(a.sum()))
def group(rs):
 return dict(count=len(rs),nominal_x_mm=stats([x['nominal_delta_xyz_mm'][0] for x in rs]),actual_x_mm=stats([x['actual_delta_xyz_mm'][0] for x in rs]),object_x_mm=stats([x['object_delta_xyz_mm'][0] for x in rs]),object_signed_y_mm=stats([x['object_signed_y_mm'] for x in rs]),positive_actual_x_frames=sum(x['actual_delta_xyz_mm'][0]>0 for x in rs),positive_object_x_frames=sum(x['object_delta_xyz_mm'][0]>0 for x in rs),prediction_abs_x_error_mm=stats([abs(x['prediction_error_xy_mm'][0]) for x in rs if 'prediction_error_xy_mm' in x]),filtered_load_n=stats([x['filtered_load_n'] for x in rs]))
phase=[r for r in all_executed if 'phase' in r];transitions=[dict(step=r['step'],active=r['phase']['after']['active'],reason=r['phase']['reason']) for r in phase if r['phase']['before']['active']!=r['phase']['after']['active']]
comparisons=[]
for run in ['fresh_closed_peak_trials_r1','rear_corridor_physical_r1','rear_latched_physical_r1']:
 p=W/run/ep.parent.name/ep.name/'quality.json'
 if p.exists():
  d=read(p);comparisons.append(dict(run=run,frames=d['frames'],quality_passed=d['passed'],target_final_progress_mm=d['metrics']['target_final_progress_m']*1000))
non_target_peak=max(float(np.linalg.norm(pos[other][:,:2]-pos[other][0,:2],axis=1).max()*1000),max([x['non_target_post_xy_mm'] for x in rows],default=0.))
summary=dict(frames=n,full_horizon=n==1200,quality_passed=quality['passed'],task_progress_mm=quality['metrics']['target_final_progress_m']*1000,non_target_sampled_max_xy_mm=non_target_peak,initial_q_max_abs=float(abs(q[0]).max()),initial_action_max_abs=float(abs(u[0]).max()),recovery_all=group(rows),tracking_applied=group([x for x in rows if x['tracking_active']]),tracking_fallback=group([x for x in rows if not x['tracking_active']]),tracking_reason_counts=dict(collections.Counter(x['tracking_reason'] for x in rows)),unload_steps=sum(r['kind']=='unload' for r in all_executed),recovery_fraction_of_episode=len(rows)/n,phase_transitions=transitions,not_executed_record_steps=stopped,comparisons=comparisons)
for p,h in sources.items():assert sha(p)==h,p
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,summary=summary,rows=rows,source_sha256=sources,analyzer_sha256=sha(__file__),fk_source_sha256=sha(W/'audit_unloaded_wrist_prior_live.py'),training_ready=False,limitations=['Control-tick motion and post-action measurements do not replace complete substep contact audits.','Same local material point frozen separately each step; sums of FK deltas are not one fixed material-point trajectory.','Numeric task quality does not substitute for all pose/control/actual-image/full-group gates.'])
with dest.open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(summary,indent=2))
