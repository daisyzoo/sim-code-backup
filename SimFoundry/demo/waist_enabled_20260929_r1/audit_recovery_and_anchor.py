"""Independent recorded-geometry check of optional progress and fixed X commands.

No controller imports, no simulation and no automatic admission or visual approval.
"""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy.spatial.transform import Rotation
p=Path(sys.argv[1]);d=json.loads((p/'frontal_bypass.json').read_text());plan=d['plan'];rows=d['rows'];tr=np.load(p/'trace.npz');ori=np.load(p/'parcel_orientation.npz')
key='box' if 'push_box' in p.name else 'mailer';other='mailer' if key=='box' else 'box';size={'box':np.array([.14,.09,.045]),'mailer':np.array([.15,.145,.04])};errors=[];events=[];out={}
if plan.get('front_route_selected') and plan['front_route_live_guards'].get('recover_clearance'):
 guards=plan['front_route_live_guards'];clear=guards['clearance_before_lateral_m'];resume=clear+guards['recovery_resume_extra_m'];stage='front_x';hold=float(tr[key][0,1]);count=0;safe_count=0;confirm=guards.get('nominal_clearance_confirmation_frames');max_gap_error=0.;last=None;gaps=[]
 for r in rows:
  t=r['step'];radii={k:abs(Rotation.from_quat(ori[k][t]).as_matrix())@size[k]/2 for k in size}
  gap=float(tr[other][t,0]-tr[key][t,0]-radii[key][0]-radii[other][0]);gap_y=float(abs(tr[other][t,1]-tr[key][t,1])-radii[key][1]-radii[other][1]);gaps.append((t,gap,gap_y))
  if r.get('route_stop_reason'):
   events.append(dict(step=t,stop_reason=r['route_stop_reason']));break
  entered=False
  if stage=='front_x':
   safe_count=safe_count+1 if gap>=clear else 0
   if gap>=resume or (confirm is not None and safe_count>=confirm):stage='lateral_y'
  elif stage=='lateral_y' and gap<clear-guards.get('recovery_hysteresis_m',0.):stage='front_x';hold=float(tr[key][t,1]);count+=1;entered=True;safe_count=0
  a=r.get('clearance_progress',{});err=abs(gap-r['measured_front_gap_m']);max_gap_error=max(max_gap_error,err)
  if stage!=a.get('route_stage') or count!=a.get('clearance_recovery_count') or entered!=a.get('clearance_recovery_entered') or abs(hold-a.get('front_hold_y',1e9))>1e-7 or err>1e-7:errors.append(dict(step=t,kind='stage_geometry_or_current_y_mismatch'))
  if stage!=last:events.append(dict(step=t,mode=r['mode'],route_stage=stage,gap_x_m=gap,current_y_m=float(tr[key][t,1]),hold_y_m=hold,recoveries=count));last=stage
 out['front_recovery']=dict(frames=len(gaps),recoveries=count,max_gap_recompute_error_m=max_gap_error,min_axis_separation_m=min(max(v[1],v[2]) for v in gaps),stop_reasons=sorted({r['route_stop_reason'] for r in rows if r.get('route_stop_reason')}),events=events)
if plan.get('top_recontact',{}).get('hold_established_x'):
 anchor=None;push=[];anchors=[];slew_error=0.;prev=None
 for r in rows:
  if r['mode']=='top_push':
   if anchor is None:anchor=float(r['parcel_top_xyz'][0]+r['approach_xy_bias_m'][0])
   push.append(r)
   if abs(r['push_x_anchor_m']-anchor)>1e-7:errors.append(dict(step=r['step'],kind='anchor_changed'))
   if prev is not None and prev['mode']=='top_push':
    step=.002;expected=prev['target_xyz'][0]+np.clip(anchor-prev['target_xyz'][0],-step,step);slew_error=max(slew_error,abs(r['target_xyz'][0]-expected))
  if anchor is not None:
   if r.get('push_x_anchor_m') is None or abs(r['push_x_anchor_m']-anchor)>1e-7:errors.append(dict(step=r['step'],kind='anchor_lost_after_establishment'))
   anchors.append(r['push_x_anchor_m'])
  prev=r
 if slew_error>1e-7:errors.append(dict(kind='push_x_slew',max_error_m=slew_error))
 out['established_x']=dict(push_frames=len(push),anchor_m=anchor,first_push_step=push[0]['step'] if push else None,last_push_step=push[-1]['step'] if push else None,max_command_slew_error_m=slew_error,first_to_last_push_target_x_delta_m=float(tr[key][push[-1]['step'],0]-tr[key][push[0]['step'],0]) if push else None,max_recontacts=max((r.get('recontacts',0) for r in rows),default=0))
assert out,'Optional recovery/anchor not applicable'
out.update(passed=not errors,errors=errors,raw_sha256=hashlib.sha256((p/'raw.npz').read_bytes()).hexdigest(),frontal_sha256=hashlib.sha256((p/'frontal_bypass.json').read_bytes()).hexdigest(),scope='Independent replay of recorded geometric conditions and X latch/slew only; no controller import, dynamics proof, full collision certificate, visual approval or training admission.',training_ready=False)
(p/'RECOVERY_AND_ANCHOR_AUDIT.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:({x:y for x,y in v.items() if x!='events'} if isinstance(v,dict) else v) for k,v in out.items()},indent=2))
