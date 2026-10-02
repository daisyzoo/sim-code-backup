"""Observed rear envelope clearance loss across complete original trial inputs.
Independently reconstruct rotated visual envelopes. AABB overlap is not physical
contact proof; actual solved-contact evidence is separate. No controller change.
"""
from pathlib import Path
import json,hashlib,datetime,collections
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sizes={'box':np.array([.14,.09,.045]),'mailer':np.array([.15,.145,.04])};episodes=sorted((W/'fresh_closed_peak_trials_r1').glob('case_*/layout_*'))+[W/'joint_edge_intersection_physical_r1/case_840015/layout_840015_push_box_to_bin'];result=[];sources={}
for ep in episodes:
 if 'wait_no_package' in ep.name:continue
 fr=json.loads((ep/'frontal_bypass.json').read_text());plan=fr['plan']
 if plan.get('front_route_selected') or plan.get('initial_top_selected'):continue
 key='box' if 'push_box' in ep.name else 'mailer';other='mailer' if key=='box' else 'box';direction=-1 if key=='box' else 1;margin=plan['margin'];assert margin==.02
 with np.load(ep/'trace.npz') as z:target=z[key].copy();obstacle=z[other].copy()
 with np.load(ep/'parcel_orientation.npz') as z:rad={k:abs(Rotation.from_quat(z[k]).as_matrix())@sizes[k]/2 for k in sizes}
 gx=target[:,0]-obstacle[:,0]-rad[key][:,0]-rad[other][:,0];gy=abs(target[:,1]-obstacle[:,1])-rad[key][:,1]-rad[other][:,1];pending=direction*(target[:,1]-obstacle[:,1])<=rad[key][:,1]+rad[other][:,1]+margin;move=np.linalg.norm(obstacle[:,:2]-obstacle[0,:2],axis=1)*1000
 fullrows=[r for r in fr['rows'] if r['step']<len(target)];top=[r for r in fullrows if r['mode'].startswith('top_')];reached=[r['step'] for r in top if gx[r['step']]>=margin];first=reached[0] if reached else None
 lost=[r['step'] for r in top if first is not None and r['step']>first and pending[r['step']] and gx[r['step']]<margin];unsafe_push=[r['step'] for r in top if r['mode']=='top_push' and pending[r['step']] and gx[r['step']]<margin]
 mismatches=[r['step'] for r in fullrows if 'rear_clearance_measured' in r and bool(r['rear_clearance_measured'])!=bool(gx[r['step']]>=margin) and abs(gx[r['step']]-margin)>2e-6];assert not mismatches,(ep.name,mismatches[:5])
 quality=json.loads((ep/'quality.json').read_text());row=dict(episode=str(ep.relative_to(W)),frames=len(target),task_passed=quality['passed'],first_top_clearance_step=first,first_lost_corridor_while_obstacle_ahead=lost[0] if lost else None,top_push_frames_without_original_rear_margin_while_obstacle_ahead=len(unsafe_push),minimum_rear_x_gap_mm=float(gx.min()*1000),minimum_xy_max_axis_gap_mm=float(np.maximum(gx,gy).min()*1000),non_target_max_xy_mm=float(move.max()),logged_clearance_matches_independent_reconstruction=True)
 if ep.parent.parent.name=='joint_edge_intersection_physical_r1':
  steps=sorted(set([first,lost[0] if lost else None,699,1052,1199])-{None});row['key_frames']=[dict(step=t,mode=next((r['mode'] for r in fullrows if r['step']==t),None),target_xy=target[t,:2].tolist(),rear_x_gap_mm=float(gx[t]*1000),y_gap_mm=float(gy[t]*1000),non_target_xy_mm=float(move[t]),obstacle_still_ahead_or_overlapping=bool(pending[t])) for t in steps]
 result.append(row)
 for name in ['frontal_bypass.json','trace.npz','parcel_orientation.npz','quality.json']:sources[str(ep/name)]=sha(ep/name)
for p in [W.parents[1]/'simfoundry/data/top_contact_bypass.py',W/'staged_front_corridor_interval/rear_cop_route.py']:sources[str(p)]=sha(p)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,episodes=result,source_sha256=sources,analyzer_sha256=sha(__file__),original_rear_episodes=len(result)-1,original_rear_episodes_with_corridor_loss=sum(r['first_lost_corridor_while_obstacle_ahead'] is not None for r in result[:-1]),interpretation='Original rear clearance is confirmed before first top approach, but later loss is logged without a rear object-route recovery in the top/COP wrapper. Geometry-only clearance loss and progress are not physical contact or causal proof; critical actual box-mailer force starts at action699 in separate bound evidence.',next_step='Prototype a causal rear-object route recovery that maintains original20mm envelope planning clearance with table/other/hand guards and measured recontact; do not merely extend duration or relax margins. Freeze comparisons against successes and failures before separate physical test.',training_ready=False)
with (W/'REAR_CORRIDOR_LOSS_FINDINGS.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps({k:v for k,v in out.items() if k not in ['episodes','source_sha256']},indent=2));print(json.dumps(result[-1],indent=2))
