"""Fit development unloaded joint lag on closed parent; test on closed child.
No controller mutation. No inference from last-substep zero force to all-substep
contact absence; filtering and scope are recorded explicitly.
"""
from pathlib import Path
import json,hashlib,sys
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(w/'staged_front_cop_route_axis'),str(repo)]
from articulated_hand_geometry import ArticulatedHandGeometry
from scipy.spatial.transform import Rotation
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
model=ArticulatedHandGeometry(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json');modes={'top_lift','top_cross','top_descend'}
source={};data={};conditions=[(840001,'nudge_mailer_to_bin'),(840004,'push_box_to_bin'),(840001,'push_box_to_bin'),(840004,'nudge_mailer_to_bin')]
for run in ['front_cop_phase_anchor_groups_r1','front_cop_route_axis_groups_r1']:
 data[run]=[]
 for cid,task in conditions+([(cid,task) for cid in [840000,840005] for task in ['push_box_to_bin','nudge_mailer_to_bin']] if run=='front_cop_route_axis_groups_r1' else []):
  ep=w/f'{run}/case_{cid}/layout_{cid}_{task}';side='right' if 'push_box' in task else 'left';key='box' if side=='right' else 'mailer';fr={r['step']:r for r in json.loads((ep/'frontal_bypass.json').read_text())['rows']};packets=json.loads((ep/'solved_contact_forces.json').read_text())['rows'];loads={}
  for p in packets:
   loads[p['after_action_step']]=sum(abs(c['force_torque_contact'][0]) for c in p['parcel_contacts'] if any(side+'_wrist' in s for s in c['shapes']))
  with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
  with np.load(ep/'trace.npz') as z:xyz=z[key].astype(float);palm=z['palm_'+side].astype(float)
  with np.load(ep/'parcel_orientation.npz') as z:rot=Rotation.from_quat(z[key]).as_matrix()
  selected=[t for t in range(1,len(q)-1) if t in fr and t+1 in fr and fr[t]['mode'] in modes and fr[t+1]['mode'] in modes and loads.get(t,1)<.05 and loads.get(t-1,1)<.05 and fr[t].get('contact_load',{}).get('observed_vertical_load_n',1)<.05]
  assert len(selected)>15
  idx=np.array(selected);row=dict(episode=ep.name,task=task,side=side,t=idx,q=q[idx],previous_q=q[idx-1],u=u[idx],previous_u=u[idx-1],next_q=q[idx+1],modes=[fr[t]['mode'] for t in selected],actual_xyz=xyz[idx+1],actual_rot=rot[idx+1],actual_palm=palm[idx+1]);data[run].append(row)
  source[str(ep.resolve())]={f:sha(ep/f) for f in ['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','solved_contact_forces.json']}
train=data['front_cop_phase_anchor_groups_r1'];test=data['front_cop_route_axis_groups_r1'];fits={}
for task in sorted({r['task'] for r in train}):
 rr=[r for r in train if r['task']==task];x=np.concatenate([r['q']-r['u'] for r in rr]);y=np.concatenate([r['next_q']-r['u'] for r in rr]);xm=x.mean(0);ym=y.mean(0);variance=np.sum((x-xm)**2,axis=0);a=np.clip(np.sum((x-xm)*(y-ym),axis=0)/np.maximum(variance,1e-12),0,1);b=ym-a*xm;fits[task]=dict(a=a.tolist(),bias_rad=b.tolist(),n=len(x),x_variance_sum=variance.tolist())
def errors(e,active):return dict(all11_rmse_rad=float(np.sqrt(np.mean(e**2))),active_waist_rmse_rad=float(np.sqrt(np.mean(e[:,active]**2))),active_waist_max_abs_rad=float(np.max(abs(e[:,active]))))
rows=[]
for r in test:
 a=np.array(fits[r['task']]['a']);b=np.array(fits[r['task']]['bias_rad']);pred={'command_only':r['u'],'held_current_residual':r['u']+r['q']-r['previous_u'],'first_order_parent_fit':r['u']+a*(r['q']-r['u'])+b,'previous_measured_q':r['q'],'first_order_causal_bias':r['u']+a*(r['q']-r['u'])+(r['q']-r['previous_u'])-a*(r['previous_q']-r['previous_u'])};active=[0]+list(range(6,11) if r['side']=='right' else range(1,6));metrics={k:errors(v-r['next_q'],active) for k,v in pred.items()};mode_metrics={}
 for mode in sorted(set(r['modes'])):
  mask=np.array([m==mode for m in r['modes']]);mode_metrics[mode]=dict(n=int(mask.sum()),metrics={k:errors(v[mask]-r['next_q'][mask],active) for k,v in pred.items()})
 height_errors={k:[] for k in pred};fk_error=0.
 for i,q in enumerate(r['next_q']):
  T=model.fk(r['side'],q)[0];fk_error=max(fk_error,float(np.max(abs(T[:3,3]+T[:3,:3]@np.array([.2,0,.007])-r['actual_palm'][i]))));pts=model.vertices[r['side']];R=r['actual_rot'][i];center=r['actual_xyz'][i];actual_min=float(((pts@T[:3,:3].T+T[:3,3]-center)@R)[:,2].min())
  for k,v in pred.items():
   P=model.fk(r['side'],v[i])[0];minimum=float(((pts@P[:3,:3].T+P[:3,3]-center)@R)[:,2].min());height_errors[k].append((minimum-actual_min)*1000)
 assert fk_error<2e-6
 hmetrics={k:dict(rmse_mm=float(np.sqrt(np.mean(np.array(v)**2))),median_abs_mm=float(np.median(abs(np.array(v)))),p95_abs_mm=float(np.percentile(abs(np.array(v)),95)),max_abs_mm=float(np.max(abs(np.array(v))))) for k,v in height_errors.items()}
 rows.append(dict(episode=r['episode'],n=len(r['t']),actual_frames=r['t'].tolist(),metrics=metrics,by_mode=mode_metrics,support_height_prediction_error=hmetrics,max_actual_fk_palm_error_m=fk_error,actual_command_step_p50_rad=float(np.median(np.max(abs(r['u']-r['previous_u']),axis=1)))))
 print(json.dumps({k:rows[-1][k] for k in ['episode','n','metrics','support_height_prediction_error']}),flush=True)
out=w/'unloaded_tracking_dynamics_bias_audit_r1';out.mkdir(exist_ok=False);report=dict(fit_parent='front_cop_phase_anchor_groups_r1',heldout_child='front_cop_route_axis_groups_r1',fits=fits,rows=rows,source_sha256=source,script_sha256=sha(__file__),geometry_source_sha256=model.source_sha256,scope='Development episode-level parent/child fit comparison on known development layouts, parent4hard episodes fit / child8hard-and-control episodes test, not independent task/policy validation. Diagonal first-order q[t+1]=u[t]+a*(q[t]-u[t])+b, a clipped0..1. Held-current-residual baseline u[t]+q[t]-u[t-1]. Both adjacent top_lift/top_cross/top_descend, measured prior/current last-substep hand parcel load<0.05N. Last-substep samples cannot exclude intervening contacts. Predictions use only current/past q/actions, parent-fit parameters; measured next object pose used only to score support-height errors. Causal-bias variant uses b[t]=(q[t]-u[t-1])-a*(q[t-1]-u[t-1]) from past/current observations; no child fitting. Constant lag/bias is an approximation, no new simulator response or controller implementation. No gates changed.',training_ready=False);(out/'RESULT.json').write_text(json.dumps(report,indent=2))
