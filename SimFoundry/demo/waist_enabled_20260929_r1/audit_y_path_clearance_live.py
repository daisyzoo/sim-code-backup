"""Independent remaining-Y-segment and commanded object-X goal audit."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy.spatial.transform import Rotation

def check_row(plan,row,target,obstacle,quat,other_quat,size,other_size):
 f=row.get('clearance_feedback')
 if not f or not f['eligible']:return []
 errors=[];r=np.abs(Rotation.from_quat(quat).as_matrix())@np.asarray(size)/2;ro=np.abs(Rotation.from_quat(other_quat).as_matrix())@np.asarray(other_size)/2
 goal_y=plan['initial_top_proposal']['goal_y'];a,b=sorted((float(target[1]),float(goal_y)));remaining_gap=max(a-obstacle[1],obstacle[1]-b,0)-r[1]-ro[1];needed=bool(remaining_gap<.024);initial_x=plan['initial_target_xyz'][0];away=-1 if initial_x<plan['obstacle_initial_xyz'][0] else 1;boundary=obstacle[0]+away*(r[0]+ro[0]+.024);expected_x=(min(initial_x,boundary) if away<0 else max(initial_x,boundary)) if needed else initial_x
 if f.get('needs_x_corridor') is not needed:errors.append('needs_x_corridor')
 if 'remaining_y_gap_m' not in f or abs(f['remaining_y_gap_m']-remaining_gap)>1e-6:errors.append('remaining_y_geometry')
 if abs(f['object_goal_xy'][0]-expected_x)>1e-6:errors.append('object_x_goal')
 if min(expected_x-r[0]-.28,.88-expected_x-r[0])<.005-1e-7:errors.append('table_margin')
 actualgap=max(abs(target[i]-obstacle[i])-r[i]-ro[i] for i in [0,1])
 if actualgap<.01-1e-7:errors.append('original_parcel_guard')
 return errors

def main():
 ep=Path(sys.argv[1]);log=json.loads((ep/'frontal_bypass.json').read_text());assert log['plan'].get('initial_top_selected'),'Audit only applicable to initial-top';key='box' if 'push_box' in ep.name else 'mailer';other='mailer' if key=='box' else 'box';size=(.14,.09,.045) if key=='box' else (.15,.145,.04);osize=(.15,.145,.04) if key=='box' else (.14,.09,.045);rows=[];errors=[]
 with np.load(ep/'trace.npz') as tr,np.load(ep/'parcel_orientation.npz') as ori:
  for r in log['rows']:
   f=r.get('clearance_feedback')
   if not f or not f['eligible']:continue
   t=r['step'];e=check_row(log['plan'],r,tr[key][t],tr[other][t],ori[key][t],ori[other][t],size,osize);errors.extend(dict(frame=t,kind=k) for k in e);rows.append(dict(frame=t,needs_x_corridor=f.get('needs_x_corridor'),remaining_y_gap_m=f.get('remaining_y_gap_m'),object_goal_xy=f['object_goal_xy']))
 if any(r['mode']=='top_push' for r in log['rows']) and not rows:errors.append(dict(kind='missing_push_feedback'))
 sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();result=dict(passed=not errors,errors=errors,checked_frames=len(rows),required_x_corridor_frames=sum(r['needs_x_corridor'] is True for r in rows),kept_reset_x_frames=sum(r['needs_x_corridor'] is False for r in rows),rows=rows,raw_sha256=sha(ep/'raw.npz'),frontal_sha256=sha(ep/'frontal_bypass.json'),scope='Scipy independent rotated-footprint remainingYsegment and required Xgoal, original parcel/table constraints. Actual waypoint mapping and slew remain existing clearanceaudit; no task/physical/visual/admission certificate.',training_ready=False);(ep/'Y_PATH_CLEARANCE_LIVE_AUDIT.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k not in ['errors','rows']}));return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
