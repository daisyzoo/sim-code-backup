"""Recorded candidate action reconstruction; original quality and visuals separate."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
w=Path(__file__).resolve().parent;sys.path.insert(0,str(w.parents[1]))
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
p=Path(sys.argv[1]);errors=[];override=[];handovers=[]
with np.load(p/'raw.npz') as raw:q=raw['q'].copy();actions=raw['action'].copy();meta=json.loads(str(raw['collect_meta']))
assert np.isfinite(q).all() and np.isfinite(actions).all()
assert np.max(abs(q[0,12:23]))==0 and np.max(abs(actions[0,12:23]))==0 and meta['assist_frames']==0
path=p/'region_approach.json';coords={x['step']:x for x in json.loads((p/'coordination.json').read_text())};frontal=json.loads((p/'frontal_bypass.json').read_text());plan=frontal['plan'];rows=json.loads(path.read_text())['rows'] if path.exists() else []
expected=bool(plan.get('region_approach',{}).get('enabled'))
if expected != path.exists():errors.append('region log/route mismatch')
if path.exists() and (plan.get('front_route_selected') or plan.get('initial_top_selected')):errors.append('candidate touched excluded route')
expected_steps=[x['step'] for x in frontal.get('rows',[]) if x.get('projected_support_reference') is not None]
if path.exists() and [x['step'] for x in rows]!=expected_steps:errors.append('region log coverage mismatch')
from front_recontact_headroom_v1_stage_audit_context import verified_events,selected_after_capture
verified_recontacts=verified_events(p)
selected=None
for row in rows:
 step=row['step'];s=row['solver'];c=coords[step]
 selected=selected_after_capture(row,selected,verified_recontacts)
 if row['selected_surface_local_xy'] is not None:
  if selected is None:selected=row['selected_surface_local_xy']
  if row['selected_surface_local_xy']!=selected:errors.append(f'{step}: lost selected surface')
 if not s or not s.get('joint_override'):
  if 'region_joint_override' in c:errors.append(f'{step}: unexpected override')
  continue
 if c.get('region_joint_override')!=s:errors.append(f'{step}: solver/coord log differs')
 if c.get('terminal_joint_hold'):errors.append(f'{step}: hold competes with approach')
 nq=np.asarray(s['next_q']);assert nq.shape==(11,) and np.isfinite(nq).all();dq=abs(nq-q[step,12:23]);limits=np.r_[.015,np.full(10,.04)]
 if not s['accepted'] or not s['inside_10mm_inset'] or np.any(dq>limits+2e-6):errors.append(f'{step}: invalid accepted step')
 if abs(nq[0])>.980002:errors.append(f'{step}: waist working bound')
 expected_action=np.clip(nq,actions[step-1,12:23]-.055,actions[step-1,12:23]+.055)
 expected_action=np.clip(expected_action,np.asarray(U1_JOINT_LIMIT_LO)[12:23],np.asarray(U1_JOINT_LIMIT_HI)[12:23]);expected_action[0]=np.clip(expected_action[0],-1.,1.)
 error=float(np.max(abs(actions[step,12:23]-expected_action)))
 if error>2e-6:errors.append(f'{step}: executed action reconstruction {error}')
 for value in s['runtime_fk_check'].values():
  if value['position_max_error_m']>1e-4 or value['rotation_max_error']>1e-4:errors.append(f'{step}: FK disagreement')
 clipped=float(np.max(abs(expected_action-nq)))
 override.append(dict(step=step,action_error_rad=error,global_slew_adjustment_rad=clipped,top_gap_m=s['top_gap_m']))
 if s.get('handover'):
  if not s['reached'] or np.max(abs(nq-q[step,12:23]))>1e-9 or row['mode']!='top_press':errors.append(f'{step}: invalid measured-q handover')
  handovers.append(dict(step=step,selected_surface_local_xy=selected,top_gap_m=s['top_gap_m']))
if np.max(abs(np.diff(actions[:,12:23],axis=0)))>.055002:errors.append('global slew exceeded')
report=dict(verified_recontact_frames=len(verified_recontacts),verified_recontact_handovers=sum(e['kind']=='handover' for e in verified_recontacts.values()),passed=not errors,errors=errors,expected_region_route=expected,override_steps=len(override),handover=handovers,global_slew_modified_steps=sum(x['global_slew_adjustment_rad']>2e-6 for x in override),maximum_action_reconstruction_error_rad=max((x['action_error_rad'] for x in override),default=0),override_rows=override,abort_reasons=sorted({x['abort_reason'] for x in rows if x['abort_reason']}),source_sha256={f:hashlib.sha256((p/f).read_bytes()).hexdigest() for f in ['raw.npz','coordination.json','frontal_bypass.json']+(['region_approach.json'] if path.exists() else [])},scope='Actual raw actions and measured q against candidate logs, original global slew/limits and unchanged first zero/no assistance. No full collision, impulse, task, visibility or training approval.',training_ready=False)
(p/'FRONT_RECONTACT_HEADROOM_V1_STAGE_REGION_ACTION_AUDIT.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='override_rows'},indent=2));sys.exit(0 if report['passed'] else 1)
