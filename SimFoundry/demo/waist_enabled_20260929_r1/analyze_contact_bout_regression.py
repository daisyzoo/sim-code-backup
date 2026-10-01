"""Read-only matched-layout physical comparison. Never approves raw data."""
from pathlib import Path
import json,hashlib
from collections import Counter
import numpy as np
w=Path(__file__).resolve().parent
new=w/'contact_bout_yaw_groups_r1';old=w/'y_path_nearhalf_groups_r1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def quantile(a):
 return np.quantile(a,[0,.5,.95,1]).tolist() if len(a) else None
def episode(ep):
 quality=json.loads((ep/'quality.json').read_text());rows=json.loads((ep/'frontal_bypass.json').read_text())['rows'];push=[r for r in rows if r['mode']=='top_push'];events=[];prev=0
 for r in rows:
  if r.get('recontacts',prev)>prev:events.append(dict(step=r['step'],reason=r['last_recontact_reason']))
  prev=r.get('recontacts',prev)
 target='mailer' if 'mailer' in ep.name else 'box';other='box' if target=='mailer' else 'mailer'
 with np.load(ep/'trace.npz') as z:t=z[target].astype(float);nt=z[other].astype(float)
 with np.load(ep/'raw.npz') as z:q=z['q'].copy();a=z['action'].copy();meta=json.loads(str(z['collect_meta']))
 return dict(episode=str(ep),raw_sha256=sha(ep/'raw.npz'),frontal_sha256=sha(ep/'frontal_bypass.json'),passed=quality['passed'],progress_m=quality['metrics']['target_final_progress_m'],non_target_max_xy_m=float(np.linalg.norm(nt[:,:2]-nt[0,:2],axis=1).max()),mode_counts=dict(Counter(r['mode'] for r in rows)),recontacts=events,push_load_n_min_median_p95_max=quantile([r['contact_load']['observed_vertical_load_n'] for r in push]),push_bias_at_lower_limit_frames=sum(r['contact_load']['applied_z_bias_m']<=-.006+1e-8 for r in push),push_load_below_0p2_frames=sum(r['contact_load']['observed_vertical_load_n']<.2 for r in push),push_vertical_point_minus_goal_m_min_median_p95_max=quantile([r['observed_support_xyz'][2]-r['target_xyz'][2] for r in push]),push_xy_tracking_norm_m_min_median_p95_max=quantile([np.linalg.norm(np.array(r['observed_support_xyz'])[:2]-np.array(r['target_xyz'])[:2]) for r in push]),first_push_step=push[0]['step'] if push else None),q,a,meta
results=[]
for ni in [898002,898003]:
 oi=ni-1000
 for task in ['push_box_to_bin','nudge_mailer_to_bin']:
  ne=new/f'case_{ni}'/f'layout_{ni}_{task}';oe=old/f'case_{oi}'/f'layout_{oi}_{task}'
  n,nq,na,nm=episode(ne);o,oq,oa,om=episode(oe)
  # Compare actual recorded reset positions, orientations, seed, not just IDs.
  checks={}
  with np.load(ne/'trace.npz') as nz,np.load(oe/'trace.npz') as oz:
   for k in ['box','mailer']:checks[k+'_reset']=bool(np.allclose(nz[k][0],oz[k][0],atol=1e-7,rtol=0))
  with np.load(ne/'parcel_orientation.npz') as nz,np.load(oe/'parcel_orientation.npz') as oz:
   for k in ['box','mailer']:checks[k+'_quat_reset']=bool(np.allclose(nz[k][0],oz[k][0],atol=1e-7,rtol=0))
  npv=json.loads((ne.parent/'provenance.json').read_text())['args'];opv=json.loads((oe.parent/'provenance.json').read_text())['args'];checks['seed']=npv['environment_seed']==opv['environment_seed'];assert all(checks.values())
  first=min(n['first_push_step'],o['first_push_step']);different=np.flatnonzero(np.max(abs(nq-oq),axis=1)>1e-6)
  results.append(dict(current=n,parent=o,reset_and_seed_checks=checks,first_measured_q_difference_over_1e_6_frame=int(different[0]) if len(different) else None,max_q_difference_through_first_push=float(abs(nq[:first+1]-oq[:first+1]).max()),max_action_difference_before_first_push=float(abs(na[:first]-oa[:first]).max())))
report=dict(rows=results,scope='Matched physical runs. Statistics use recorded top_push frames and last-substep loads, not force integrals. A changed orientation objective can alter position tracking; correlations do not prove force alone causes regression. No production changes, quality relaxation, or training admission.',training_ready=False)
(new/'DEPTH_REGRESSION_DIAGNOSIS.json').write_text(json.dumps(report,indent=2))
for r in results:
 print(Path(r['current']['episode']).name)
 for label in ['parent','current']:
  s=r[label];print(label,json.dumps({k:s[k] for k in ['passed','progress_m','mode_counts','push_load_n_min_median_p95_max','push_bias_at_lower_limit_frames','push_vertical_point_minus_goal_m_min_median_p95_max','push_xy_tracking_norm_m_min_median_p95_max']}), 'recontacts',len(s['recontacts']),dict(Counter(x['reason'] for x in s['recontacts'])))
 print('same_before',r['max_q_difference_through_first_push'],r['max_action_difference_before_first_push'],'firstdiff',r['first_measured_q_difference_over_1e_6_frame'])
