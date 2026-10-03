"""Actual 24-tick signed force/momentum budgets by executed control phase.
Reuse original angular-balance inspector unchanged, adding its local arrays only
at return. No altered physics or counterfactual trajectories. The per-body
velocity/state timing and residual limits from the original reports remain.
"""
from pathlib import Path
import ast,datetime,hashlib,json,sys,copy
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inspect(ep):
 ep=Path(ep).resolve();source=W/'diagnose_substep_angular_balance.py';tree=ast.parse(source.read_text());fn=copy.deepcopy(next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='inspect'));assert isinstance(fn.body[-1],ast.Return)
 # This diagnostic exports originals from the same inspect invocation; no
 # arithmetic, source validation or event selection in it is replaced.
 original_return=fn.body[-1].value
 fn.body[-1].value=ast.Dict(keys=[ast.Constant('original'),ast.Constant('arrays')],values=[original_return,ast.Call(func=ast.Name(id='locals',ctx=ast.Load()),args=[],keywords=[])])
 env=dict(Path=Path,np=np,Rotation=Rotation,json=json,datetime=datetime,sha=sha,__file__=str(source),__doc__=source.read_text().split('"""')[1]);exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),str(source),'exec'),env)
 result=env['inspect'](ep);ctx=result['arrays'];original=result['original'];bound=json.loads((ep/'SUBSTEP_ANGULAR_BALANCE_DIAGNOSIS.json').read_text());assert original['body_results']==bound['body_results']
 a,m,chosen=[ctx[k] for k in ['a','m','chosen']];n=1200;stride=24+m['expected_manager_steps'];target=0;body=m['body_ids'][target];bodies=np.asarray(m['shape_body'])[a['shape_ids']];sign=(bodies[:,1]==body).astype(float)-(bodies[:,0]==body).astype(float);mask=sign!=0;sample=ctx['sid'][mask];ids=a['shape_ids'][mask];other=np.where(bodies[mask,0]==body,ids[:,1],ids[:,0]);labels=m['shape_labels'];categories=ctx['categories']
 groups=np.asarray([0 if 'wrist_roll' in labels[int(i)] else 1 if 'table' in labels[int(i)].lower() else 2 if '/parcel_box/' in labels[int(i)] or '/mailer/' in labels[int(i)] else 3 for i in other]);forces=np.zeros((n*stride,4,3));np.add.at(forces,(sample,groups),sign[mask,None]*a['force_torque_world'][mask,:3]);np.testing.assert_allclose(forces.sum(axis=1),ctx['force'][:,target],atol=1e-12,rtol=0)
 ix=chosen[:,1:];dt=m['solver_dt_s'];mass=m['body_mass_kg'][target];F=forces[ix];v=ctx['qd'][chosen,target,:3];normal=ctx['rot'][ix,target,:,2];loads=-np.sum(F[:,:,0]*normal,axis=-1);linear=np.diff(v,axis=1)*mass
 cfg=json.loads((ep.parent/'runtime_configuration.json').read_text());gravity=np.asarray(cfg['simulation']['gravity']);linear_prediction=(F.sum(axis=2)+mass*gravity)*dt;linear_residual=linear-linear_prediction
 angular=ctx['measured'][:,:,target];angular_residual=angular-ctx['pred']['start_com'][:,:,target];angular_groups=ctx['torques']['start_com'][ix,target]*dt
 rows=json.loads((ep/'frontal_bypass.json').read_text())['rows'];modes={r['step']:r for r in rows};measurements=[]
 for t in range(1,1199):
  r=modes[t]
  if r['mode']!='top_push' or loads[t].mean()<.3:continue
  direction=np.array([-1.,0.,0.]) if r.get('route_stage','rear_top')=='front_x' else np.array([0.,-1.,0.]);idx=ix[t]
  measurements.append(dict(step=t,stage=r.get('route_stage','rear_top'),mean_hand_downward_n=float(loads[t].mean()),mean_hand_force_along_route_n=float(F[t,:,0].mean(axis=0)@direction),mean_table_force_along_route_n=float(F[t,:,1].mean(axis=0)@direction),mean_other_force_norm_n=float(np.linalg.norm(F[t,:,2:].sum(axis=1),axis=1).mean()),mean_target_speed_along_route_mps=float(v[t,1:].mean(axis=0)@direction),linear_impulse_residual_rms_ns=float(np.sqrt(np.mean(np.sum(linear_residual[t]**2,axis=-1)))),measured_linear_impulse_rms_ns=float(np.sqrt(np.mean(np.sum(linear[t]**2,axis=-1)))),angular_impulse_residual_rms_nms=float(np.sqrt(np.mean(np.sum(angular_residual[t]**2,axis=-1)))),measured_angular_impulse_rms_nms=float(np.sqrt(np.mean(np.sum(angular[t]**2,axis=-1)))),angular_impulse_by_contact_nms={name:angular_groups[t,:,i].sum(axis=0).tolist() for i,name in enumerate(categories)},net_angular_impulse_nms=angular_groups[t].sum(axis=(0,1)).tolist(),measured_angular_impulse_nms=angular[t].sum(axis=0).tolist(),max_tilt_rad=float(np.arccos(np.clip(ctx['rot'][idx,target,2,2],-1,1)).max())))
 summaries={}
 for stage in sorted({r['stage'] for r in measurements}):
  rr=[r for r in measurements if r['stage']==stage];fields=[k for k,vv in rr[0].items() if isinstance(vv,float)];summaries[stage]=dict(actions=len(rr),ticks=24*len(rr),median={k:float(np.median([r[k] for r in rr])) for k in fields},max={k:float(max(r[k] for r in rr)) for k in fields})
 sources=dict(original['source_sha256'])
 for p in [Path(__file__),ep/'SUBSTEP_ANGULAR_BALANCE_DIAGNOSIS.json',ep/'SUBSTEP_LINEAR_BALANCE.json',ep.parent/'runtime_configuration.json']:sources[str(p)]=sha(p)
 return dict(episode=ep.name,scope=__doc__,selection='Executed top_push intervals with actual 24-tick mean hand downward force >=0.3N. No selection by task success.',summary=summaries,rows=measurements,source_sha256=sources,training_ready=False)
if __name__=='__main__':
 out=inspect(sys.argv[1]);ep=Path(sys.argv[1])
 with (ep/'REAR_SUBSTEP_PHASE_FORCE_BALANCE_DIAGNOSTIC.json').open('x') as f:json.dump(out,f,indent=2)
 print(json.dumps(out['summary'],indent=2))
