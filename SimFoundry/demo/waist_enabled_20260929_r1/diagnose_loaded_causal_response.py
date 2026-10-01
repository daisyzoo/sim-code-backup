"""Frozen parent-fit, new-run held-out loaded joint response prediction."""
from pathlib import Path
import sys,json,hashlib,importlib.util
import numpy as np
from scipy.optimize import lsq_linear
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path.insert(0,str(repo));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def module(p,name):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
outdir=w/'loaded_causal_response_diagnosis_r1';outdir.mkdir(exist_ok=False)
protocol=dict(parent='region_measured_bounds_groups_r1',held_out_run='rear_cop_measured_bounds_groups_r1',cases=[(840001,'push_box_to_bin'),(840004,'nudge_mailer_to_bin')],selection='mode top_push and observed prior vertical load>=0.2N; q[t],u[t],q[t]-q[t-1] predict q[t+1]. Boundary and next-loss samples retained.',features=['current absolute command minus current measured joint','last measured joint delta'],models=['stationary','constant_velocity','instant_command','parent_scalar_gain','parent_gain_momentum'],gain_bounds=[0.,1.5],momentum_bounds=[-.5,1.5],selection_or_model_tuning_on_held_out=False,scope='Development response prediction only. Parent run fitted separately for each task; all new-run selected samples evaluated, no per-frame refit. Whole new contact bouts remain held out. Not independent policy evaluation or evidence that changed actions follow the same dynamics.')
(outdir/'PROTOCOL.json').write_text(json.dumps(protocol,indent=2));reports=[]
def load(run,cid,task):
 ep=w/run/f'case_{cid}/layout_{cid}_{task}';prov=json.loads((ep.parent/'provenance.json').read_text());src=prov['source_sha256'];snap=ep.parent/'source_snapshot';gr=next(n for n in src if n.endswith('/articulated_hand_geometry.py'));pr='simfoundry/data/projected_support_reference.py'
 for n in [gr,pr]:assert sha(snap/n)==src[n]
 assets=['third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf','assets/robots/g1_hand_support_vertices.json','simfoundry/calibration/sorting_station.py','simfoundry/data/hand_obstacle_clearance.py']
 for a in assets:assert sha(repo/a)==src[a]
 model=module(snap/gr,'response_geometry').ArticulatedHandGeometry(repo/assets[0],repo/assets[1]);pm=module(snap/pr,'response_projected');side='right' if task=='push_box_to_bin' else 'left'
 with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
 cs={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};fr=json.loads((ep/'frontal_bypass.json').read_text())['rows'];indices=[r['step'] for r in fr if r['mode']=='top_push' and r['contact_load']['observed_vertical_load_n']>=.2 and 0<r['step']<len(q)-1];ts=np.array(indices);error=u[ts]-q[ts];velocity=q[ts]-q[ts-1];response=q[ts+1]-q[ts];assert len(ts)>50;by={r['step']:r for r in fr};bouts=np.cumsum(np.r_[True,np.diff(ts)>1]).tolist()
 def point(qv,t):
  T,_,_=model.fk(side,qv);ref=cs[t]['active_support_reference'];rr=pm.projected_support_reference(model.vertices[side],T[:3,:3],ref['world_normal'],center_local=ref['center_local']);return T[:3,3]+T[:3,:3]@rr['reference_local']
 for t in ts:assert np.max(abs(point(q[t],t)-by[t]['observed_support_xyz']))<2e-6
 return dict(ep=ep,q=q,u=u,ts=ts,error=error,velocity=velocity,response=response,bouts=bouts,model=model,point=point,source_sha256={n:sha(ep/n) for n in ['raw.npz','coordination.json','frontal_bypass.json']},geometry_sha256=src[gr],projected_sha256=src[pr],asset_sha256={n:src[n] for n in assets})
def metrics(errors):
 a=np.asarray(errors);return dict(mae=np.mean(abs(a),axis=0).tolist(),median_abs=np.median(abs(a),axis=0).tolist(),p95_abs=np.percentile(abs(a),95,axis=0).tolist(),max_abs=np.max(abs(a),axis=0).tolist())
for cid,task in protocol['cases']:
 train=load(protocol['parent'],cid,task);test=load(protocol['held_out_run'],cid,task);e=train['error'];v=train['velocity'];y=train['response'];gain=np.clip(np.sum(e*y,axis=0)/np.maximum(np.sum(e*e,axis=0),1e-12),0,1.5);coef=[];conditioning=[]
 for j in range(11):
  X=np.c_[e[:,j],v[:,j]];fit=lsq_linear(X,y[:,j],bounds=([0,-.5],[1.5,1.5]),tol=1e-12);assert fit.success;coef.append(fit.x);conditioning.append(float(np.linalg.cond(X)))
 coef=np.asarray(coef);evals={};rawrows=[]
 predictions=dict(stationary=np.zeros_like(test['response']),constant_velocity=test['velocity'],instant_command=test['error'],parent_scalar_gain=test['error']*gain,parent_gain_momentum=test['error']*coef[:,0]+test['velocity']*coef[:,1])
 for name,pred in predictions.items():
  joint=pred-test['response'];cart=[]
  for i,t in enumerate(test['ts']):cart.append((test['point'](test['q'][t]+pred[i],t)-test['point'](test['q'][t+1],t))*1000)
  cart=np.array(cart);perbout=[]
  for bout in sorted(set(test['bouts'])):
   mask=np.array(test['bouts'])==bout;perbout.append(dict(bout=bout,start=int(test['ts'][mask][0]),end=int(test['ts'][mask][-1]),n=int(sum(mask)),cartesian_error_mm=metrics(cart[mask]),joint_error_rad=metrics(joint[mask])))
  evals[name]=dict(joint_error_rad=metrics(joint),cartesian_error_mm=metrics(cart),per_bout=perbout)
  for i,t in enumerate(test['ts']):rawrows.append(dict(model=name,step=int(t),bout=test['bouts'][i],predicted_joint_delta_rad=pred[i].tolist(),actual_joint_delta_rad=test['response'][i].tolist(),predicted_minus_actual_reference_mm=cart[i].tolist()))
 summary=dict(task=task,train_n=len(train['ts']),test_n=len(test['ts']),test_bouts=len(set(test['bouts'])),joint_names=train['model'].names,scalar_gain=gain.tolist(),gain_momentum_coefficients=coef.tolist(),training_feature_condition_number=conditioning,train_source_sha256=train['source_sha256'],test_source_sha256=test['source_sha256'],geometry_sha256=train['geometry_sha256'],projected_sha256=train['projected_sha256'],asset_sha256=train['asset_sha256'],evaluations=evals,rows=rawrows);reports.append(summary)
 print(task,'train',len(train['ts']),'test',len(test['ts']),'coeff',np.round(coef,3).tolist(),flush=True)
 for name,val in evals.items():print(name,'XYZ MAE mm',np.round(val['cartesian_error_mm']['mae'],3).tolist(),'p95',np.round(val['cartesian_error_mm']['p95_abs'],3).tolist(),flush=True)
result=dict(episodes=reports,protocol_sha256=sha(outdir/'PROTOCOL.json'),checker_sha256=sha(Path(__file__)),training_ready=False,no_new_controller=True,scope=protocol['scope']);(outdir/'RESULT.json').write_text(json.dumps(result,indent=2))
