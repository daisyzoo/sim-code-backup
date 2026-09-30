"""Independent logged guard/shift/FK clearance consistency; not admission."""
from pathlib import Path
import json,sys
import numpy as np
from scipy.spatial.transform import Rotation
run=Path(sys.argv[1]).resolve();assert json.loads((run/'STATUS.json').read_text())['stage']=='numeric_complete_actual_visual_review_pending'
full=json.loads((run/'HAND_OBSTACLE_CLEARANCE_AUDIT.json').read_text());results=[]
for ep in sorted(run.glob('case_*/layout_*')):
 doc=json.loads((ep/'frontal_bypass.json').read_text());p=doc['plan']['top_recontact'];guard=p['hand_obstacle_guard_m'];assert guard>0
 key='box' if 'push_box' in ep.name else 'mailer';direction=-1 if key=='box' else 1;half=np.array(p['contact_size_xyz'])/2;ori=np.load(ep/'parcel_orientation.npz')[key]
 expected_shift=0.;previous_count=0;errors=[];events=[];cycle_seen=set();geometry_errors=[]
 for row in doc['rows']:
  t=row['step'];count=row.get('recontacts',0)
  if count>previous_count:
   if count!=previous_count+1:errors.append([t,'recontact_count_skip'])
   if row['last_recontact_reason']=='hand_obstacle_clearance':
    expected_shift=min(.03,expected_shift+.01);gap=row['hand_obstacle_gap_m']
    if not gap<guard or row['mode']!='top_lift' or row['contact_load']['applied_z_bias_m']!=0:errors.append([t,'invalid_guard_transition'])
    events.append(dict(step=t,trigger_gap_m=gap,requested_rear_shift_m=expected_shift))
   previous_count=count
  if abs(row.get('contact_rear_shift_m',0)-expected_shift)>1e-12:errors.append([t,'shift_change_without_guard'])
  if row.get('corner_local') is None or count in cycle_seen:continue
  cycle_seen.add(count);rot=Rotation.from_quat(ori[t]).as_matrix();travel=direction*rot[1,:2]*p['forward_margin_m']
  low=np.maximum(-half[:2]+.01,-half[:2]-np.minimum(travel,0));high=np.minimum(half[:2]-.01,half[:2]-np.maximum(travel,0));start=np.where(rot[0,:2]>=0,low,high)
  delta=rot[0,:2];limit=expected_shift
  for i in (0,1):
   if abs(delta[i])>1e-12:limit=min(limit,max(0.,((high[i] if delta[i]>0 else low[i])-start[i])/delta[i]))
  predicted=np.r_[start+limit*delta,half[2]];err=float(np.max(abs(predicted-np.array(row['corner_local']))));geometry_errors.append(err)
  if err>1e-6:errors.append([t,'shifted_contact_geometry_mismatch',err])
 audit=next(r for r in full['rows'] if r['episode']==ep.name);face=[]
 for r in audit['records']:
  if r['logged_face_axis_gap_m'] is not None:
   error=abs(r['logged_face_axis_gap_m']-r['independent_face_axis_gap_m']);face.append(error)
   if error>1e-6:errors.append([r['frame'],'independent_fk_face_gap_mismatch',error])
 passed=bool(face and geometry_errors and not errors)
 report=dict(episode=ep.name,implementation_consistency_passed=passed,errors=errors,guard_events=events,max_requested_shift_m=expected_shift,max_shift_geometry_error_m=max(geometry_errors,default=None),matched_independent_clearance_samples=len(face),max_independent_clearance_error_m=max(face,default=None),hand_other_contact_events=audit['contact_events'],max_recorded_hand_other_force_n=max((e['hand_other_force_n'] for e in audit['contact_events']),default=0),min_sampled_full_sat_gap_m=audit['min_sampled_gap_m'])
 results.append(report);print(ep.name,'implementation',passed,'guard events',events,'max hand-other force',report['max_recorded_hand_other_force_n'],'errors',errors[:5],flush=True)
report=dict(rows=results,implementation_consistency_passed=len(results)==2 and all(x['implementation_consistency_passed'] for x in results),scope='Recorded guard threshold/phase/load withdrawal and bounded persistent inset bookkeeping; actual parcel pose/core constraints replay; live observer vs independent URDF FK/full hand face projections at sampled times. Contact events and SAT reported separately, no all-substep certificate or task/model/admission claim.',training_ready=False)
(run/'HAND_GUARD_LIVE_AUDIT.json').write_text(json.dumps(report,indent=2))
if not report['implementation_consistency_passed']:raise SystemExit(1)
