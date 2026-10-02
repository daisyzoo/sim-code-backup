"""Offline current-state corridor proposal, not installed in the controller.
Keep original12mm parcel planning clearance and5mm table margin. Preserve valid
original goals; only when its extra3mm reserve makes that goal infeasible, propose
the midpoint of the remaining safe X interval. Existing non-corridor protections
and an already latched stop remain protected. No future measurements are used by
the proposal; recorded future states are not a simulated candidate trajectory.
"""
from pathlib import Path
import argparse,datetime,hashlib,json
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.optimize import linprog
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def propose(original,lower,upper,*,protected):
 if not np.isfinite([original,lower,upper]).all() or type(protected) is not bool:raise ValueError('Invalid current-state corridor inputs')
 if protected:return dict(changed=False,goal_x=original,reason='preserve_other_guard_or_latched_stop')
 if lower<=original<=upper:return dict(changed=False,goal_x=original,reason='preserve_valid_original')
 if lower>=upper:return dict(changed=False,goal_x=original,reason='no_positive_width_safe_interval')
 return dict(changed=True,goal_x=(lower+upper)/2,reason='midpoint_of_original_margin_interval')

def main(run,out):
 run=Path(run).resolve();protocol=json.loads((run/'PROTOCOL.json').read_text());summaries=[];all_rows=[];sources={str(run/'PROTOCOL.json'):sha(run/'PROTOCOL.json'),str(Path(__file__)):sha(__file__)}
 for p,h in protocol['frozen_files_sha256'].items():assert sha(p)==h,p
 for qp in sorted(run.glob('case_*/layout_*/quality.json')):
  ep=qp.parent
  if 'wait_no_package' in ep.name:continue
  fp=ep/'frontal_bypass.json';f=json.loads(fp.read_text());plan=f['plan']
  if not plan.get('front_route_selected'):continue
  key='box' if 'push_box' in ep.name else 'mailer';other='mailer' if key=='box' else 'box';size=np.array([.14,.09,.045] if key=='box' else [.15,.145,.04]);osize=np.array([.15,.145,.04] if key=='box' else [.14,.09,.045]);prov=json.loads((ep.parent/'provenance.json').read_text());margin=prov['args']['expert_front_clearance_m'];assert margin==.012
  source='demo/waist_enabled_20260929_r1/staged_closed_peak_trial/front_top_route_micro.py';archive=ep.parent/'source_snapshot'/source;assert sha(archive)==prov['source_sha256'][source];sources[str(archive)]=sha(archive)
  with np.load(ep/'trace.npz') as z:target=z[key].copy();obstacle=z[other].copy()
  with np.load(ep/'parcel_orientation.npz') as z:rad=np.abs(Rotation.from_quat(z[key]).as_matrix())@size/2;orad=np.abs(Rotation.from_quat(z[other]).as_matrix())@osize/2
  front=next(x for x in plan['front_route_candidates']['candidates'] if x['route']=='front');route_x=front['waypoints_xy'][1][0]-.003;rows=[];previous_stop=False;max_goal_error=0.;replayed=0
  for row in f['rows']:
   t=row['step'];required=obstacle[t,0]-orad[t,0]-rad[t,0]-margin;old=min(route_x,required-.003);lower=.285+rad[t,0];upper=required
   if 'route_goal_x' in row:max_goal_error=max(max_goal_error,abs(old-row['route_goal_x']));replayed+=1
   current_table=min(target[t,0]-rad[t,0]-.28,.88-target[t,0]-rad[t,0],target[t,1]-rad[t,1]+.75,.75-target[t,1]-rad[t,1]);gap_x=obstacle[t,0]-target[t,0]-orad[t,0]-rad[t,0];gap_y=abs(obstacle[t,1]-target[t,1])-orad[t,1]-rad[t,1]
   other_guards=bool(np.linalg.norm(obstacle[t,:2]-np.array(plan['obstacle_initial_xyz'][:2]))>.01 or current_table<.005 or row['hand_obstacle_gap_m']<.005 or max(gap_x,gap_y)<.01)
   proposed=propose(old,float(lower),float(upper),protected=bool(other_guards or previous_stop))
   if proposed['changed']:
    # Independent linear program maximizes equal slack to both fixed bounds.
    lp=linprog([0.,-1.],A_ub=[[-1.,1.],[1.,1.]],b_ub=[-lower,upper],bounds=[(None,None),(0,None)],method='highs');assert lp.success
    assert abs(lp.x[0]-proposed['goal_x'])<1e-9 and lower<=proposed['goal_x']<=upper
   rows.append(dict(step=t,mode=row['mode'],original_goal_x=float(old),original_planned_table_margin_mm=float((old-rad[t,0]-.28)*1000),safe_interval_x=[float(lower),float(upper)],existing_other_guard=other_guards,prior_stop_latched=previous_stop,proposal=proposed))
   previous_stop=previous_stop or bool(row.get('route_stop_reason'))
  assert replayed>0 and max_goal_error<2e-6,(ep.name,max_goal_error)
  changes=[x for x in rows if x['proposal']['changed']];summary=dict(episode=ep.name,original_quality_passed=json.loads(qp.read_text())['passed'],observed_rows=len(rows),original_goals_replayed=replayed,max_original_goal_replay_error_m=max_goal_error,proposed_changes=changes,changed_count=len(changes),protected_rows=sum(x['existing_other_guard'] or x['prior_stop_latched'] for x in rows))
  summaries.append(summary);all_rows.append(dict(episode=ep.name,rows=rows))
  for p in [fp,qp,ep/'trace.npz',ep/'parcel_orientation.npz',ep.parent/'provenance.json']:sources[str(p)]=sha(p)
 assert len(summaries)>=3
 report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,episodes=summaries,rows=all_rows,source_sha256=sources,original_constraints=dict(table_margin_m=.005,parcel_planning_clearance_m=.012,hand_gap_m=.005,parcel_live_gap_m=.01,non_target_live_motion_m=.01),runtime_candidate_installed=False,hand_arm_swept_path_verified=False,tracking_uncertainty_verified=False,physics_verified=False,training_ready=False)
 with Path(out).open('x') as file:json.dump(report,file,indent=2)
 print(json.dumps(summaries,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('run');p.add_argument('--out',required=True);a=p.parse_args();main(a.run,a.out)
