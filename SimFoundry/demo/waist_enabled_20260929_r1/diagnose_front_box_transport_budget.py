"""Recorded front-box transport/relative contact-motion budget across three trials.
Descriptive sampled motion, not a causal response estimate or dynamics rollout.
No changed gates, forces, source files, or admission.
"""
from pathlib import Path
import collections,datetime,hashlib,json
import numpy as np
W=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inspect(run):
 ep=W/run/'case_840020/layout_840020_push_box_to_bin';fr=json.loads((ep/'frontal_bypass.json').read_text());q=json.loads((ep/'quality.json').read_text());rs=fr['rows'];assert len(rs)==1199 and q['frames']==1200 and not q['passed'];lookup={r['step']:r for r in rs}
 with np.load(ep/'trace.npz') as z:target=z['box'].astype(float);other=z['mailer'].astype(float)
 assert target.shape==other.shape==(1200,3)
 for r in rs:np.testing.assert_allclose(r['observed_target'],target[r['step']],atol=1e-12,rtol=0)
 runs=[]
 for r in rs:
  if not runs or runs[-1][-1]['mode']!=r['mode']:runs.append([])
  runs[-1].append(r)
 bouts=[]
 for group in runs:
  if group[0]['mode']!='top_push':continue
  a,b=group[0]['step'],group[-1]['step'];end=min(b+1,1199);nextrow=lookup.get(b+1)
  firstcop=group[0]['cop_slip_following'].get('measured_cop_local');lastcop=group[-1]['cop_slip_following'].get('measured_cop_local')
  prog=-(target[end,1]-target[a,1])*1000;hand=-float(group[-1]['observed_physical_support_xyz'][1]-group[0]['observed_physical_support_xyz'][1])*1000
  edges=[r['cop_slip_following'].get('edge_speed',{}).get('forward_core_distance_m') for r in group];edges=[float(x)*1000 for x in edges if x is not None]
  tilt=max(r['observed_parcel_tilt_rad'] for r in group+([nextrow] if nextrow else []))
  bouts.append(dict(start=a,end=b,frames=len(group),route_stage=group[0]['route_stage'],next_mode=nextrow['mode'] if nextrow else 'episode_end',exit_reason=nextrow.get('last_recontact_reason') if nextrow else None,target_progress_mm=prog,target_progress_per_control_interval_mm=prog/(end-a) if end>a else None,within_bout_hand_reference_travel_mm=hand,within_bout_target_travel_mm=-(target[b,1]-target[a,1])*1000,first_cop_local_mm=None if firstcop is None else (np.array(firstcop)*1000).tolist(),last_cop_local_mm=None if lastcop is None else (np.array(lastcop)*1000).tolist(),min_forward_core_edge_mm=min(edges) if edges else None,max_observed_tilt_rad=tilt))
 count=collections.Counter(r['mode'] for r in rs);initial=float(target[0,1]);final=float(target[-1,1]);required=max(.15,initial+.20);actual=initial-final;np.testing.assert_allclose(actual,q['metrics']['target_final_progress_m'],rtol=0,atol=1e-9)
 assert max(np.linalg.norm(other[:,:2]-other[0,:2],axis=1))==0
 sources=[ep/n for n in ['frontal_bypass.json','trace.npz','quality.json','raw.npz','coordination.json']]
 return dict(run=run,episode=str(ep),original_quality_passed=False,quality_reasons=q['reasons'],initial_target_y_m=initial,final_target_y_m=final,directed_progress_mm=actual*1000,minimum_translation_to_original_zone_and_progress_mm=required*1000,remaining_translation_to_original_zone_mm=max(0,final+.20)*1000,non_target_max_xy_mm=0.,mode_frames=dict(count),push_fraction=count['top_push']/1199,recontact_count=rs[-1]['recontacts'],exit_counts=dict(collections.Counter(b['exit_reason'] for b in bouts if b['exit_reason'])),guard_stop_frames=sum(bool(r.get('route_stop_reason')) for r in rs),bouts=bouts,source_sha256={str(p):sha(p) for p in sources})
if __name__=='__main__':
 runs=[inspect(n) for n in ['front_corridor_midpoint_physical_r1','front_drive_1mm_physical_r1','rear_waypoint_physical_r2']]
 out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,runs=runs,findings=['The box starts on the opposite side; minimum150mm progress is not the total transport requirement. Original right-zone boundary also applies.','At2mm, repeated observed tilt exits interrupt transport. At1mm, longer push segments end in loss of contact and total displacement is lower.','Recorded contact center migrates toward the forward edge within bouts; contact-center motion is not proof of a sticking material point.','No front-corridor stop is recorded in these box trials; the black-bag exhausted-corridor mechanism must not be assumed for the box.','A follow-up candidate needs to address loaded transport efficiency and relative sliding while preserving observed tilt/edge/load guards. The current bag-only run remains unchanged.'],limitations=['Per-bout displacement uses recorded state intervals [start,min(end+1,1199)]; last unsaved post-action movement is not inferred.','Changes between trials are not deterministic evidence of a single cause; rear-waypoint is not selected for this front box yet its physical trace differs.','No new controller, friction change, longer horizon, reduced safety margin, or training admission is justified by this descriptive report alone.'],source_sha256={str(Path(__file__)):sha(Path(__file__))},simulation_started=False,training_ready=False)
 dest=W/'front_box_transport_budget_20261003_r1.json'
 with dest.open('x') as f:json.dump(out,f,indent=2)
 print(json.dumps([dict(run=r['run'],progress_mm=r['directed_progress_mm'],required_mm=r['minimum_translation_to_original_zone_and_progress_mm'],remaining_zone_mm=r['remaining_translation_to_original_zone_mm'],push_fraction=r['push_fraction'],exits=r['exit_counts'],median_bout_progress_mm=float(np.median([b['target_progress_mm'] for b in r['bouts']]))) for r in runs],indent=2))
