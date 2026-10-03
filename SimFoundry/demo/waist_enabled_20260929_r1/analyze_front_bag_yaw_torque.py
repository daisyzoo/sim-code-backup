"""Full recorded bag yaw and signed contact-torque decomposition; no new physics.
Original angular inspector mathematics and input checks are reused verbatim,
except exposing its locals at return. No contact COP is treated as a material
point. Torque impulse is not equated with angle. Timing residuals retained.
"""
from pathlib import Path
import ast,copy,datetime,hashlib,json,sys
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inspect(ep):
 ep=Path(ep).resolve();source=W/'diagnose_substep_angular_balance.py';tree=ast.parse(source.read_text());fn=copy.deepcopy(next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='inspect'));assert isinstance(fn.body[-1],ast.Return)
 ret=fn.body[-1].value;fn.body[-1].value=ast.Dict(keys=[ast.Constant('original'),ast.Constant('arrays')],values=[ret,ast.Call(func=ast.Name(id='locals',ctx=ast.Load()),args=[],keywords=[])])
 env=dict(Path=Path,np=np,Rotation=Rotation,json=json,datetime=datetime,sha=sha,__file__=str(source),__doc__=source.read_text().split('"""')[1]);exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),str(source),'exec'),env)
 result=env['inspect'](ep);c=result['arrays'];bound=json.loads((ep/'SUBSTEP_ANGULAR_BALANCE_DIAGNOSIS.json').read_text());assert result['original']['body_results']==bound['body_results']
 a,m,chosen=[c[k] for k in ['a','m','chosen']];target=1;assert m['body_labels'][target].endswith('/mailer');body=m['body_ids'][target];ns=len(a['action_step']);dt=m['solver_dt_s']
 bodies=np.asarray(m['shape_body'])[a['shape_ids']];sign=(bodies[:,1]==body).astype(float)-(bodies[:,0]==body).astype(float);mask=sign!=0;sample=c['sid'][mask];ids=a['shape_ids'][mask];other=np.where(bodies[mask,0]==body,ids[:,1],ids[:,0]);labels=m['shape_labels'];groups=np.asarray([0 if 'wrist_roll' in labels[int(i)] else 1 if 'table' in labels[int(i)].lower() else 2 if '/parcel_box/' in labels[int(i)] or '/mailer/' in labels[int(i)] else 3 for i in other]);f=sign[mask,None]*a['force_torque_world'][mask,:3];couple=sign[mask,None]*a['force_torque_world'][mask,3:]
 decomposition={};categories=c['categories']
 for ref,idx in [('start_com',c['previous'][sample]),('end_com',sample)]:
  lever=a['position_world'][mask]-c['com'][idx,target];parts=np.stack([lever[:,0]*f[:,1],-lever[:,1]*f[:,0],couple[:,2]],axis=1);tot=np.zeros((ns,4,3));np.add.at(tot,(sample,groups),parts);np.testing.assert_allclose(tot.sum(axis=-1),c['torques'][ref][:,target,:,2],atol=1e-12,rtol=0);decomposition[ref]=tot
 forces=np.zeros((ns,4,3));np.add.at(forces,(sample,groups),f);np.testing.assert_allclose(forces.sum(axis=1),c['force'][:,target],atol=1e-12,rtol=0)
 rot=c['rot'][:,target];yaw=np.arctan2(rot[:,1,0],rot[:,0,0]);delta=lambda x:np.rad2deg(np.arctan2(np.sin(x),np.cos(x)))
 control={r['step']:r for r in json.loads((ep/'frontal_bypass.json').read_text())['rows']};guard=next(t for t,r in control.items() if r['mode']=='front_guard_lift');rows=[]
 for t,ix in enumerate(chosen):
  mode=control.get(t,{}).get('mode','initial_zero');ticks=ix[1:];mom=c['measured'][t,:,target,2];r=dict(step=t,mode=mode,route_stage=control.get(t,{}).get('route_stage'),yaw_start_deg=float(np.rad2deg(yaw[ix[0]])),yaw_end_deg=float(np.rad2deg(yaw[ix[-1]])),yaw_delta_deg=float(delta(yaw[ix[-1]]-yaw[ix[0]])),boundary_yaw_delta_deg=float(delta(yaw[ix[0]]-yaw[chosen[t-1,-1]])) if t else 0.,hand_downward_mean_n=float(-forces[ticks,0,2].mean()),measured_angular_impulse_z_nms=float(mom.sum()),hand_force_mean_xyz_n=forces[ticks,0].mean(axis=0).tolist())
  for ref in decomposition:
   parts=decomposition[ref][ticks].sum(axis=0)*dt;r[ref+'_impulse_z_nms']={g:dict(rx_Fy=float(parts[i,0]),minus_ry_Fx=float(parts[i,1]),couple=float(parts[i,2]),total=float(parts[i].sum())) for i,g in enumerate(categories)}
   r[ref+'_residual_z_rms_nms']=float(np.sqrt(np.mean((mom-c['pred'][ref][t,:,target,2])**2)))
  rows.append(r)
 def summarize(rr):
  return dict(actions=len(rr),yaw_delta_deg=sum(r['yaw_delta_deg'] for r in rr),boundary_yaw_delta_deg=sum(r['boundary_yaw_delta_deg'] for r in rr),mean_hand_downward_n=float(np.mean([r['hand_downward_mean_n'] for r in rr])),start_com_impulse_z_nms={g:{k:sum(r['start_com_impulse_z_nms'][g][k] for r in rr) for k in ['rx_Fy','minus_ry_Fx','couple','total']} for g in categories},max_start_com_residual_z_rms_nms=max(r['start_com_residual_z_rms_nms'] for r in rr))
 pre=rows[:guard];summary={mode:summarize([r for r in pre if r['mode']==mode]) for mode in sorted({r['mode'] for r in pre})};bouts=[]
 for r in pre:
  if not bouts or bouts[-1][-1]['mode']!=r['mode']:bouts.append([])
  bouts[-1].append(r)
 files=[Path(__file__),ep/'SUBSTEP_ANGULAR_BALANCE_DIAGNOSIS.json',ep/'SUBSTEP_LINEAR_BALANCE.json']
 return dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,episode=str(ep),guard_step=guard,initial_yaw_deg=rows[0]['yaw_start_deg'],guard_yaw_deg=rows[guard]['yaw_start_deg'],pre_guard_summary=summary,bouts=[dict(start=rr[0]['step'],end=rr[-1]['step'],mode=rr[0]['mode'],**summarize(rr)) for rr in bouts],rows=rows,original_angular_balance=bound['body_results'],source_sha256=dict(result['original']['source_sha256'],**{str(p):sha(p) for p in files}),limitations=['Descriptive recorded contact moments, not identified causal response to a changed contact point.','Earliest samples for ticks0..24; manager boundary changes separately reported.','Both COM timing references retained; no claim of exact angular balance or torque-to-yaw equality.'],training_ready=False)
if __name__=='__main__':
 ep=Path(sys.argv[1]);out=inspect(ep)
 with (ep/'FRONT_BAG_YAW_TORQUE_DIAGNOSTIC.json').open('x') as f:json.dump(out,f,indent=2)
 print(json.dumps({k:out[k] for k in ['guard_step','initial_yaw_deg','guard_yaw_deg','pre_guard_summary']},indent=2))
