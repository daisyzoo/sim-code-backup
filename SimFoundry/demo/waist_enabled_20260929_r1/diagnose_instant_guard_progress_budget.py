"""Read-only full-episode comparison for the final-load guard; both withdraw at0.03.
Phase-attributed motion and last-substep contact forces are descriptive, not
integrated impulses or causal estimates. Never substitutes complete group,
original gates, actual images, repeated-source trials or model h10 validation.
"""
from pathlib import Path
import sys,json,hashlib,datetime,collections
import numpy as np
W=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
new=Path(sys.argv[1]).resolve();assert new.parent.parent==W/'instant_guard_groups_r1'
assert 'wait_no_package' not in new.name
old=W/'peak_guard_groups_r1'/new.parent.name/new.name
outpath=new/'INSTANT_GUARD_PROGRESS_BUDGET.json';assert not outpath.exists()
key='box' if 'push_box' in new.name else 'mailer';other='mailer' if key=='box' else 'box';direction=-1 if key=='box' else 1
sources={};arrays=[];results=[]
def read(ep,name):
 p=ep/name;sources[str(p)]=sha(p);return json.loads(p.read_text())
for ep,threshold,reviewname in [(old,.03,'PEAK_GUARD_NUMERIC_REVIEW.json'),(new,.03,'INSTANT_GUARD_NUMERIC_REVIEW.json')]:
 review=read(ep,reviewname);assert review['frames']==1200
 for name,h in review['source_sha256'].items():assert sha(ep/name)==h
 fr=read(ep,'frontal_bypass.json');fs={x['step']:x for x in fr['rows']};assert fr['plan']['contact_stability_candidate']['tilt_recontact_rad']==threshold
 expert={x['step']:x for x in read(ep,'expert_control.json')};assert sorted(expert)==list(range(1200));assert all(f['mode']==expert[t]['mode'] for t,f in fs.items())
 events=read(ep,'recontact_pose.json')['rows'];recover={x['step'] for x in events if x['kind'] in ['command','handover']}
 first=min(t for t,f in fs.items() if f['mode']=='top_push')
 with np.load(ep/'trace.npz') as tr,np.load(ep/'raw.npz') as raw:
  xyz=tr[key].astype(float);obstacle=tr[other].astype(float);y=direction*xyz[:,1];q=raw['q'][:,12:23].astype(float);action=raw['action'][:,12:23].astype(float)
 assert q.shape==action.shape==(1200,11) and len(xyz)==1200
 arrays.append(dict(q=q,action=action,target=xyz,non_target=obstacle))
 buckets=collections.defaultdict(lambda:dict(frames=0,observed_signed_motion_mm=0.,forward_motion_mm=0.,backward_motion_mm=0.))
 for t in range(1200):
  if t<first:label='before_first_push'
  elif t in recover:label='verified_unloaded_recovery'
  elif fs[t]['mode']=='top_push':label='push_observed_loaded' if fs[t]['contact_load']['observed_vertical_load_n']>=.3 else 'push_observed_low_load'
  else:label='other_'+fs[t]['mode']
  b=buckets[label];b['frames']+=1
  if t<1199:
   dy=(y[t+1]-y[t])*1000;b['observed_signed_motion_mm']+=dy;b['forward_motion_mm']+=max(0.,dy);b['backward_motion_mm']+=max(0.,-dy)
 assert sum(b['frames'] for b in buckets.values())==1200
 assert abs(sum(b['observed_signed_motion_mm'] for b in buckets.values())-(y[-1]-y[0])*1000)<1e-7
 packets=read(ep,'solved_contact_forces.json')['rows'];contacts=[];peak=0.;tag='/parcel_box/' if key=='box' else '/mailer/'
 for packet in packets:
  t=packet['after_action_step']+1
  if t>=1200:continue
  assert packet['solver_force_buffer_unchanged'];assert np.max(abs(packet['post_action_pose'][key]-xyz[t]))<1e-6
  forces=[]
  for c in packet['parcel_contacts']:
   box=[i for i,s in enumerate(c['shapes']) if '/parcel_box/' in s];bag=[i for i,s in enumerate(c['shapes']) if '/mailer/' in s]
   if not(box and bag):continue
   assert len(box)==len(bag)==1 and box[0]!=bag[0]
   target_index=box[0] if key=='box' else bag[0];forces.append(np.asarray(c['force_world_N'],float)*(1 if target_index==1 else -1))
  magnitude=sum(float(np.linalg.norm(f)) for f in forces);peak=max(peak,magnitude)
  if magnitude>.05:contacts.append(dict(step=t,sum_contact_magnitudes_n=magnitude,force_on_target_world_n=np.sum(forces,axis=0).tolist()))
 previous=None;threshold_exposure=[]
 for row in fr['rows']:
  if previous is not None and previous['mode'] in ('top_press','top_push') and row.get('observed_parcel_tilt_rad',0)>.03:threshold_exposure.append(row['step'])
  previous=row
 results.append(dict(run=ep.parent.parent.name,episode=ep.name,configured_withdrawal_rad=threshold,task_and_pose_passed=review['original_task_and_pose_passed'],progress_mm=review['progress_mm'],final10_signed_y_min_mm=review['final10_signed_y_min_mm'],non_target_max_xy_mm=review['non_target_max_xy_mm'],tilt_exit_count=review['tilt_exit_count'],lost_contact_exit_count=review['lost_contact_exit_count'],maximum_observed_tilt_rad=review['maximum_observed_tilt_rad'],first_push_step=first,buckets=dict(buckets),parcel_force_gt005N_frames=len(contacts),first_nonzero_parcel_contact=contacts[0] if contacts else None,peak_sum_parcel_contact_magnitudes_n=peak,first_observed_tilt_gt003_after_press_push=threshold_exposure[0] if threshold_exposure else None))
 for name in ['raw.npz','trace.npz']:sources[str(ep/name)]=sha(ep/name)
# Equal source/inputs are prerequisites; differences below are still not proof of causality.
prov=[json.loads((ep.parent/'provenance.json').read_text()) for ep in [old,new]]
from instant_guard_source_binding import verify_observation_binding
assert verify_observation_binding(new)['passed']
a=json.loads(json.dumps(prov[1]['args']).replace(str(new.parent.parent),str(old.parent.parent)));assert a.pop('instant_load_bias_guard') is True;assert a==prov[0]['args']
for name in ['runtime_randomization.json','runtime_configuration.json','explicit_layout.json']:
 assert json.loads((old.parent/name).read_text())==json.loads((new.parent/name).read_text())
 for ep in [old,new]:sources[str(ep.parent/name)]=sha(ep.parent/name)
for ep in [old,new]:sources[str(ep.parent/'provenance.json')]=sha(ep.parent/'provenance.json')
cutoffs=[x['first_observed_tilt_gt003_after_press_push'] for x in results if x['first_observed_tilt_gt003_after_press_push'] is not None];cutoff=min(cutoffs) if cutoffs else 1200
comparisons=[]
for name in arrays[0]:
 x=arrays[0][name];y=arrays[1][name];delta=np.max(abs(x-y),axis=1);assert np.array_equal(x[0],y[0]);comparisons.append(dict(key=name,first_different_frame={str(t):int(np.flatnonzero(delta>t)[0]) if np.any(delta>t) else None for t in [0.,1e-7,1e-6,1e-4,1e-3]},max_delta_before_first_observed_threshold_exposure=float(np.max(delta[:cutoff]))))
sources[str(Path(__file__))]=sha(__file__)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,episodes=results,loaded_threshold_n=.3,parcel_force_threshold_n=.05,first_observed_threshold_exposure_frame=cutoff if cutoffs else None,initial_states_identical=True,pre_exposure_comparisons=comparisons,source_sha256=sources,training_ready=False,limitations=['Threshold exposure is a descriptive state predicate, not an intervention timestamp or proof of identical hidden simulator state.','Single paired run cannot establish robust improvement.','A15mm non-target pass does not prove there was no obstruction.'])
outpath.write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k!='source_sha256'},indent=2))
