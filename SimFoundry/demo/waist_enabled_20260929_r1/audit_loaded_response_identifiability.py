"""Leave-one-parent-bout-out coefficient sensitivity, no new held-out tuning."""
from pathlib import Path
import json,hashlib,numpy as np
from scipy.optimize import lsq_linear
w=Path(__file__).resolve().parent;d=w/'loaded_causal_response_diagnosis_r1';rp=d/'RESULT.json';result=json.loads(rp.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();out=[]
for case in result['episodes']:
 task=case['task'];cid=840001 if task=='push_box_to_bin' else 840004;ep=w/'region_measured_bounds_groups_r1'/f'case_{cid}/layout_{cid}_{task}'
 for n,h in case['train_source_sha256'].items():assert sha(ep/n)==h
 with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
 fr=json.loads((ep/'frontal_bypass.json').read_text())['rows'];t=np.array([r['step'] for r in fr if r['mode']=='top_push' and r['contact_load']['observed_vertical_load_n']>=.2 and 0<r['step']<len(q)-1]);bout=np.cumsum(np.r_[True,np.diff(t)>1]);e=u[t]-q[t];v=q[t]-q[t-1];y=q[t+1]-q[t];fits=[]
 for b in np.unique(bout):
  mask=bout!=b;coeff=[]
  for j in range(11):
   fit=lsq_linear(np.c_[e[mask,j],v[mask,j]],y[mask,j],bounds=([0,-.5],[1.5,1.5]),tol=1e-12);assert fit.success;coeff.append(fit.x.tolist())
  fits.append(dict(excluded_bout=int(b),excluded_start=int(t[bout==b][0]),excluded_end=int(t[bout==b][-1]),coefficients=coeff))
 arr=np.array([f['coefficients'] for f in fits]);corr=[float(np.corrcoef(e[:,j],v[:,j])[0,1]) for j in range(11)];evaluations=case['evaluations'];a=evaluations['parent_gain_momentum']['per_bout'];base=evaluations['constant_velocity']['per_bout'];better=np.array([np.array(x['cartesian_error_mm']['mae'])<np.array(z['cartesian_error_mm']['mae']) for x,z in zip(a,base)]);active=[0]+(list(range(6,11)) if cid==840001 else list(range(1,6)));joints=[dict(index=j,name=case['joint_names'][j],error_velocity_correlation=corr[j],gain_full=case['gain_momentum_coefficients'][j][0],gain_leave_bout_out_min=float(arr[:,j,0].min()),gain_leave_bout_out_max=float(arr[:,j,0].max()),momentum_min=float(arr[:,j,1].min()),momentum_max=float(arr[:,j,1].max())) for j in active];out.append(dict(task=task,parent_bouts=len(fits),heldout_bouts=len(a),heldout_bouts_model_mae_better_than_constant_velocity_xyz=better.sum(axis=0).tolist(),active_joints=joints,leave_bout_out_fits=fits));print(task,'heldout_better',better.sum(0).tolist(),'of',len(a));print(json.dumps(joints,indent=2))
p=d/'IDENTIFIABILITY.json';assert not p.exists();p.write_text(json.dumps(dict(episodes=out,parent_result_sha256=sha(rp),checker_sha256=sha(Path(__file__)),training_ready=False,no_new_controller=True,scope='Deterministic leave-one-complete-parent-loaded-bout-out coefficient sensitivity, not statistical confidence bounds. Held-out prediction compared to constant velocity by complete bout. No inversion/controller permission inferred from low prediction error.'),indent=2))
