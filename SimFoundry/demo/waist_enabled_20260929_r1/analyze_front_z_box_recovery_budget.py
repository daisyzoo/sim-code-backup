"""Observed contact/phase budget only; fixed-rate arithmetic is not a rollout.
No scene friction, quality gate, controller or episode duration changes.
"""
from pathlib import Path
import collections,datetime,hashlib,json
import numpy as np
W=Path(__file__).resolve().parent;Z=W/'front_z_priority_physical_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();outrows=[];sources={}
for run in ['front_initial_physical_r1','front_z_priority_physical_r1']:
 ep=W/run/'case_840020/layout_840020_push_box_to_bin'
 def read(name):
  p=ep/name;sources[str(p)]=sha(p);return json.loads(p.read_text())
 fr=read('frontal_bypass.json');rows={r['step']:r for r in fr['rows']};b=read('OBSERVED24_CONTACT_BOUT_DIAGNOSTIC.json');mom=read('FRONT_INITIAL_CONTACT_MOMENT_DIAGNOSTIC.json');moment={r['step']:r for r in mom['rows']};packets=read('solved_contact_forces.json')['rows'];quality=read('quality.json')
 with np.load(ep/'trace.npz') as z:xyz=z['box'].copy()
 sources[str(ep/'trace.npz')]=sha(ep/'trace.npz');direction=fr['plan']['direction'];assert direction==-1
 total_needed=max(.15,direction*(direction*.2-xyz[0,1]));remaining=max(0,direction*(direction*.2-xyz[-1,1]));push=sum(r['mode']=='top_push' for r in rows.values());assert push==b['top_push_frames']
 recoveries=[]
 for i,bout in enumerate(b['bouts']):
  after=bout['end']+1;next_start=b['bouts'][i+1]['start'] if i+1<len(b['bouts']) else len(xyz)
  segment=[rows[t] for t in range(after,next_start) if t in rows];counts=dict(collections.Counter(r['mode'] for r in segment));samples=[]
  for t in [bout['start'],bout['end']]:
   m=moment[t];s=rows[t];groups=m['moments'];net=np.sum([g['moment_world_Nm'] for g in groups.values()],axis=0)
   samples.append(dict(step=t,tilt_rad=s['observed_parcel_tilt_rad'],cop_local_m=None if m['cop'] is None else m['cop']['local_m'],hand_moment_Nm=groups.get('active_hand',{}).get('moment_world_Nm'),table_moment_Nm=groups.get('table',{}).get('moment_world_Nm'),net_recorded_contact_moment_Nm=net.tolist(),edge_speed=s.get('cop_slip_following',{}).get('edge_speed'),stored_z_bias_m=s['contact_load']['stored_z_bias_m']))
  recoveries.append(dict(bout=bout['bout'],push_frames=bout['push_frames'],progress_mm=bout['target_signed_y_progress_mm'],exit_reason=bout['exit_reason'],recovery_complete=i+1<len(b['bouts']),recovery_frame_count=len(segment),recovery_modes=counts,first_last_contact_samples=samples))
 # Report actual contact-pair friction, rather than assume the hand equals table.
 mus=collections.defaultdict(set)
 for r in rows.values():
  if r['mode']!='top_push':continue
  for c in packets[r['step']-1]['parcel_contacts']:
   labels=c['shapes']
   if not any('/parcel_box/' in label for label in labels):continue
   pair='active_hand' if any('right_wrist' in label for label in labels) else 'table' if any('/table/' in label for label in labels) else 'other'
   mus[pair].add(tuple(c['friction'][:2]))
 initial=b['bouts'][0]['start'];tilt=[r for r in recoveries if r['exit_reason']=='incipient_tilt_independent' and r['recovery_complete']]
 typical=None
 if tilt:
  push_n=float(np.mean([r['push_frames'] for r in tilt]));prog=float(np.mean([r['progress_mm']/1000 for r in tilt]));recover_n=float(np.mean([r['recovery_frame_count'] for r in tilt]));desc=float(np.mean([r['recovery_modes'].get('top_descend',0) for r in tilt]));needed=total_needed/prog
  typical=dict(complete_tilt_bouts=len(tilt),mean_push_frames=push_n,mean_progress_m=prog,mean_recovery_frames=recover_n,mean_descent_frames=desc,arithmetic_required_bouts_at_same_progress=needed,arithmetic_frames_at_same_cycles=initial+needed*(push_n+recover_n),arithmetic_frames_if_all_descent_removed=initial+needed*(push_n+recover_n-desc),caveat='Stationary same-bout arithmetic, NOT a physical feasibility bound or predicted rollout. Removing descent is impossible; shown only to evaluate whether descent-only optimization is promising.')
 outrows.append(dict(run=run,episode=ep.name,frames=len(xyz),target_start_y=float(xyz[0,1]),target_end_y=float(xyz[-1,1]),required_progress_to_original_zone_m=total_needed,remaining_to_original_zone_m=remaining,actual_progress_m=quality['metrics']['target_final_progress_m'],passed=quality['passed'],non_target_max_xy_m=quality['metrics']['mailer_max_xy_m'],initial_frames_before_first_push=initial,push_frames=push,mode_counts=dict(collections.Counter(r['mode'] for r in rows.values())),contact_pair_friction={k:[list(v) for v in sorted(vals)] for k,vals in mus.items()},recoveries=recoveries,tilt_cycle_budget=typical))
sources[str(Path(__file__))]=sha(__file__)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,runs=outrows,source_sha256=sources,decision='Prioritize sustained interior contact/progress. Do not treat shorter descent alone or larger downward bias as an established solution. Hand/table moments nearly balance at sampled ticks; eccentric hand moment alone does not establish net tilt causality.',training_ready=False)
with (Z/'BOX_RECOVERY_AND_CONTACT_BUDGET_DIAGNOSTIC.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps([{k:v for k,v in r.items() if k!='recoveries'} for r in outrows],indent=2))
