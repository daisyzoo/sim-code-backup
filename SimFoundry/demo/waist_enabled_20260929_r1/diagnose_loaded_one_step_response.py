"""Evaluate frozen unloaded response model on ACTUAL loaded contact transitions.
Only current/previous q and previous action form the bias; future measured q is
used for evaluation only. This does not fit a new model or certify loaded use.
Original nominal command pose can differ from next actual measured hand pose.
"""
from pathlib import Path
import sys,json,hashlib,datetime
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(w),str(repo)]
from audit_unloaded_wrist_prior_live import HandModel
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();urdf=repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf';vertices=repo/'assets/robots/g1_hand_support_vertices.json';hand=HandModel(urdf,vertices);rows=[];sources={}
for run in ['unloaded_wrist_prior_groups_r1','recontact_pose_groups_r1','loaded_edge_coverage_groups_r1']:
 for cid,task,side in [(840001,'push_box_to_bin','right'),(840004,'nudge_mailer_to_bin','left')]:
  ep=w/run/f'case_{cid}'/f'layout_{cid}_{task}';fr=json.loads((ep/'frontal_bypass.json').read_text());fs={r['step']:r for r in fr['rows']};clear=json.loads((ep/'self_clearance.json').read_text());post={r['step']:r for r in clear['rows'] if r['phase']=='post'};a=np.array(fr['plan']['region_causal_response']['decay']);direction=-1 if side=='right' else 1
  with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
  records=[]
  for t in range(2,len(q)):
   f=fs[t];prev=fs[t-1];load=f.get('contact_load',{}).get('observed_vertical_load_n',0)
   if f['mode']!='top_push' or prev['mode']!='top_push' or f['recontacts']!=prev['recontacts'] or load<.3:continue
   current_bias=q[t]-a*q[t-1]-(1-a)*u[t-1];pred=a*q[t]+current_bias+(1-a)*u[t];actual=np.array(post[t]['upper_q']);offset=np.array(f['control_offset_local'])
   if t+1<len(q):assert np.max(abs(actual-q[t+1]))<1e-6
   def point(x):T=hand.fk(x,side);return T[:3,3]+T[:3,:3]@offset
   measured=point(actual);predicted=point(pred);nominal=point(u[t]);current=point(q[t]);err=predicted-measured
   records.append(dict(step=t,previous_loaded=prev.get('contact_load',{}).get('observed_vertical_load_n',0)>=.3,response_error_xyz_mm=(err*1000).tolist(),response_error_norm_mm=float(np.linalg.norm(err)*1000),nominal_command_error_norm_mm=float(np.linalg.norm(nominal-measured)*1000),constant_q_error_norm_mm=float(np.linalg.norm(current-measured)*1000),predicted_forward_mm=float(direction*(predicted[1]-current[1])*1000),nominal_command_forward_mm=float(direction*(nominal[1]-current[1])*1000),actual_hand_forward_mm=float(direction*(measured[1]-current[1])*1000)))
  stats={}
  for label,subset in [('all_current_loaded',records),('consecutive_loaded',[x for x in records if x['previous_loaded']])]:
   stats[label]=dict(frames=len(subset),response_error_mm={str(p):float(np.percentile([x['response_error_norm_mm'] for x in subset],p)) for p in [50,90,95,99,100]},nominal_command_error_median_mm=float(np.median([x['nominal_command_error_norm_mm'] for x in subset])),constant_q_error_median_mm=float(np.median([x['constant_q_error_norm_mm'] for x in subset])))
  rows.append(dict(run=run,episode=ep.name,decay=a.tolist(),stats=stats,records=records));print(run,ep.name,stats,flush=True)
  for name in ['raw.npz','frontal_bypass.json','self_clearance.json']:sources[str(ep/name)]=sha(ep/name)
for p in [Path(__file__),w/'audit_unloaded_wrist_prior_live.py',urdf,vertices]:sources[str(p)]=sha(p)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,source_sha256=sources,collector_connected=False,physical_validation=False,training_ready=False);(w/'LOADED_ONE_STEP_RESPONSE_DIAGNOSIS.json').write_text(json.dumps(out,indent=2))
