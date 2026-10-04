"""Evaluate inactive-hand one-step forecasts against actual recorded next states.
Uses only q[t], q[t-1], u[t-1] to form bias; q[t+1] is evaluation only.
No fitting, no counterfactual continuation, no training or gate relaxation.
"""
from pathlib import Path
import argparse, collections, datetime, hashlib, json, sys
import numpy as np
W=Path(__file__).resolve().parent; ROOT=W.parents[1]
sys.path[:0]=[str(W),str(ROOT)]
from audit_unloaded_wrist_prior_live import HandModel

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);ap.add_argument('--stage',required=True);ap.add_argument('--output',required=True);args=ap.parse_args()
 run=Path(args.run).resolve();stage=Path(args.stage).resolve();out=Path(args.output).resolve();assert not out.exists()
 sources={}
 def read(p):
  sources[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest();return json.loads(p.read_text())
 params=read(stage/'causal_response_parameters.json')
 urdf=ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf';vertices=ROOT/'assets/robots/g1_hand_support_vertices.json'
 hand=HandModel(urdf,vertices);episodes=[]
 for cid,task,side in [(840023,'nudge_mailer_to_bin','left'),(840020,'push_box_to_bin','right')]:
  ep=run/f'case_{cid}'/f'layout_{cid}_{task}';raw=ep/'raw.npz'
  with np.load(raw,allow_pickle=False) as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float);assert str(z['task_id'])==task
  sources[str(raw)]=hashlib.sha256(raw.read_bytes()).hexdigest();assert q.shape==u.shape==(1200,11)
  fr=read(ep/'frontal_bypass.json');fs={r['step']:r for r in fr['rows']};assert fr['plan']['front_route_selected']
  coords={r['step']:r for r in read(ep/'coordination.json')};clearance=read(ep/'self_clearance.json')['rows'];post={r['step']:r for r in clearance if r['phase']=='post'};final={r['step']:r for r in clearance if r['phase']=='final_command'}
  captures=sorted(r['step'] for name in ['front_initial_center.json','front_recontact_center.json'] for r in read(ep/name)['rows'] if r['kind']=='handover');assert captures and captures[0]>0
  recfile=ep/'inactive_transport_clearance.json';records=read(recfile)['rows'] if recfile.exists() else None
  if records is not None:assert [r['step'] for r in records]==list(range(len(q)))
  decay=np.asarray(params['tasks'][task]['decay']);inactive='right' if side=='left' else 'left';rows=[]
  for t in range(captures[0],len(q)-1):
   assert t in fs and t in coords and t in post
   np.testing.assert_allclose(final[t]['current'],q[t],atol=1e-6,rtol=0)
   np.testing.assert_array_equal(final[t]['command'],u[t])
   if 'upper_q' in coords[t]:np.testing.assert_allclose(coords[t]['upper_q'],q[t],atol=1e-6,rtol=0)
   elif coords[t].get('task_inputs'):np.testing.assert_allclose(coords[t]['task_inputs']['current'],q[t],atol=1e-6,rtol=0)
   np.testing.assert_allclose(post[t]['upper_q'],q[t+1],atol=1e-6,rtol=0)
   bias=q[t]-u[t-1]-decay*(q[t-1]-u[t-1]);pred=(1-decay)*u[t]+decay*q[t]+bias
   measured,nominal,predicted,actual=[1000*hand.minz(v,inactive) for v in [q[t],u[t],pred,q[t+1]]]
   c=coords[t];f=fs[t];eligible=(not any(c.get(k) is not None for k in ['front_recontact_center_override','front_initial_center_override','recontact_pose_override']) and not c.get('terminal_joint_hold') and not f.get('route_stop_reason') and not f.get('hand_guard_saturated') and f.get('mode') in ['top_press','top_push','top_lift','top_cross','top_descend'] and c.get('task_inputs') is not None and c.get('contact_normal_tracking') is not None)
   rec=records[t] if records is not None else None
   if rec is not None:np.testing.assert_array_equal(rec['output_command'],u[t])
   rows.append(dict(step=t,mode=f['mode'],recontacts=f.get('recontacts'),transport_priority_eligible=bool(eligible),observed_load_n=f.get('contact_load',{}).get('observed_vertical_load_n'),measured_lowest_mm=measured,nominal_lowest_mm=nominal,predicted_next_lowest_mm=predicted,actual_next_lowest_mm=actual,optimistic_forecast_error_mm=predicted-actual,actual_delta_mm=actual-measured,applied=None if rec is None else rec['applied'],reason=None if rec is None else rec['reason']))
  subsets={'all_after_first_capture':rows,'transport_eligible_above_original_floor':[r for r in rows if r['transport_priority_eligible'] and r['measured_lowest_mm']>=840-.0002],'applied':[r for r in rows if r['applied']]}
  stats={}
  for label,rs in subsets.items():
   errs=[r['optimistic_forecast_error_mm'] for r in rs]
   stats[label]=dict(frames=len(rs),optimistic_error_mm_percentiles={str(p):float(np.percentile(errs,p)) for p in [0,50,90,95,99,100]} if rs else {},forecast_at_least_841_5_but_actual_below_840=[r['step'] for r in rs if r['predicted_next_lowest_mm']>=841.5 and r['actual_next_lowest_mm']<840-.0002],optimistic_error_over_1_5_mm_steps=[r['step'] for r in rs if r['optimistic_forecast_error_mm']>1.5])
  episodes.append(dict(episode=ep.name,inactive_side=inactive,first_capture=captures[0],stats=stats,first_actual_floor_loss=next((r for r in rows if r['actual_next_lowest_mm']<840-.0002),None),minimum_actual_next=min(rows,key=lambda r:r['actual_next_lowest_mm']),application_reasons=dict(collections.Counter(r['reason'] for r in rows)),rows=rows))
 for p in [Path(__file__),W/'audit_unloaded_wrist_prior_live.py',urdf,vertices,ROOT/'simfoundry/calibration/sorting_station.py']:sources[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
 result=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,run=str(run),stage=str(stage),episodes=episodes,source_sha256=sources,physical_recorded_transitions=True,new_candidate_effect_demonstrated=False,scope_limit='Historical forecast errors do not certify new inactive-arm commands or future dynamic clearance; all original physical, task and audit gates remain required.',training_ready=False)
 with out.open('x') as f:json.dump(result,f,indent=2)
 print(json.dumps(dict(output=str(out),episodes=[{k:v for k,v in e.items() if k not in ['rows','minimum_actual_next','application_reasons']} for e in episodes]),indent=2))
if __name__=='__main__':main()
