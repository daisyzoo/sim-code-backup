"""Evaluate existing rear object-envelope route at actual initial and stopped poses.
Geometry only; no new robot commands, dynamic rollout, guard bypass or admission.
"""
from pathlib import Path
import sys,json,hashlib,datetime
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from simfoundry.data.tabletop_route_candidates import tabletop_route_candidates,footprint_radii,_segment_gap
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
records=[];sources={str(Path(__file__)):sha(__file__)}
for name in ['front_box_recenter_physical_r2','inactive_transport_physical_r1','joint_transport_physical_r1']:
 ep=W/name/'case_840023/layout_840023_nudge_mailer_to_bin';fr=json.loads((ep/'frontal_bypass.json').read_text());stop=next(r for r in fr['rows'] if r.get('route_stop_reason')=='front_corridor_no_table_margin')
 with np.load(ep/'trace.npz') as z:target=z['mailer'].copy();other=z['box'].copy()
 with np.load(ep/'parcel_orientation.npz') as z:tq=z['mailer'].copy();oq=z['box'].copy()
 assert target.shape==other.shape==(1200,3);np.testing.assert_array_equal(target[stop['step']],stop['observed_target'])
 for step in [0,stop['step']]:
  # Native rear route uses20mm original margin; front uses registered12mm.
  report=tabletop_route_candidates(target[step].tolist(),other[step].tolist(),(.15,.145,.04),(.14,.09,.045),tq[step].tolist(),oq[step].tolist(),1,margin=.020)
  rear=next(r for r in report['candidates'] if r['route']=='rear');front=tabletop_route_candidates(target[step].tolist(),other[step].tolist(),(.15,.145,.04),(.14,.09,.045),tq[step].tolist(),oq[step].tolist(),1,margin=.012)
  points=rear['waypoints_xy'];radii=np.asarray(report['target_radii_xy'])+np.asarray(report['other_radii_xy']);gaps=[_segment_gap(a,b,other[step],radii) for a,b in zip(points,points[1:])]
  # Conservative swept AABB corners at every waypoint; axis segments preserve these bounds.
  tr=report['target_radii_xy'];tm=min(min(x-tr[0]-.28,.88-x-tr[0],y-tr[1]+.75,.75-y-tr[1]) for x,y in points)
  np.testing.assert_allclose(tm,rear['target_table_margin_m'],atol=1e-12,rtol=0);np.testing.assert_allclose(min(gaps),rear['min_object_axis_separation_m'],atol=1e-12,rtol=0)
  wrong=max(0.,float(target[0,1])-min(y for x,y in points));remaining=1199-step
  records.append(dict(run=name,step=step,context='initial' if step==0 else 'first_actual_latched_front_corridor_stop',front_stop_reason=None if step==0 else stop['route_stop_reason'],front_stop_corridor=None if step==0 else stop['front_corridor_midpoint'],front_native_report=front,rear_native_report=rear,meets_original5mm_table_and20mm_rear_clearance=bool(rear['object_envelope_eligible'] and tm>=.005-1e-10 and min(gaps)>=.020-1e-10),path_wrong_way_relative_to_episode_start_m=wrong,within_original35mm_wrong_way_gate=wrong<=.035,remaining_control_intervals=remaining,mean_center_path_advance_required_if_all_remaining_intervals_used_mm=rear['object_path_length_m']*1000/remaining,physical_feasibility_proved=False,training_ready=False))
 for f in [ep/'trace.npz',ep/'parcel_orientation.npz',ep/'frontal_bypass.json',ep/'quality.json',ep/'raw.npz']:sources[str(f)]=sha(f)
for relative in ['simfoundry/data/tabletop_route_candidates.py','simfoundry/data/top_contact_bypass.py','simfoundry/data/paired_sorting.py','simfoundry/data/frontal_bypass.py']:sources[str(ROOT/relative)]=sha(ROOT/relative)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,contexts=records,source_sha256=sources,limitations=['Object paths assume frozen observed orientations. Full hand/arm clearance, reach, contact and changing orientation remain unverified.','The lower-bound mean path speed allocates all remaining intervals to object motion; real lifting/repositioning/contact loss increases required speed.','Reusing rear routing from the initial pose is a distinct prospective candidate. Clearing the existing latched stop at a later frame is not authorized by this geometry result.','Do not inject old future observations after a changed route or mix this into current reserve/rear-offset trials.'],training_ready=False)
r=W/'front_bag_alternate_route_probe_r1';r.mkdir(exist_ok=False)
with (r/'RESULT.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps([dict(run=x['run'],step=x['step'],rear_eligible=x['meets_original5mm_table_and20mm_rear_clearance'],rear_goal_x=x['rear_native_report']['waypoints_xy'][1][0],path_length_mm=x['rear_native_report']['object_path_length_m']*1000,table_margin_mm=x['rear_native_report']['target_table_margin_m']*1000,wrong_way_mm=x['path_wrong_way_relative_to_episode_start_m']*1000,required_mean_mm_per_interval=x['mean_center_path_advance_required_if_all_remaining_intervals_used_mm']) for x in records],indent=2))
