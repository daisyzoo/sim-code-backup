"""Attribute observed object motion and duration to executed bypass phases."""
from pathlib import Path
import json,hashlib,numpy as np
w=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();reports=[]
cases=[(run,840001,'push_box_to_bin') for run in ['region_measured_bounds_groups_r1','rear_cop_measured_bounds_groups_r1','rear_core_slice_groups_r1']]+[(run,840004,'nudge_mailer_to_bin') for run in ['region_measured_bounds_groups_r1','rear_cop_measured_bounds_groups_r1']]
for run,cid,task in cases:
 ep=w/run/f'case_{cid}/layout_{cid}_{task}';fr=json.loads((ep/'frontal_bypass.json').read_text());key='box' if task=='push_box_to_bin' else 'mailer';direction=-1 if key=='box' else 1
 with np.load(ep/'trace.npz') as z:xyz=z[key].astype(float)
 with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
 assert len(xyz)==len(q)==1200;by={r['step']:r for r in fr['rows']};delta=np.diff(xyz,axis=0);phases=[]
 for mode in sorted(set(r['mode'] for r in fr['rows'])):
  ts=[t for t in range(len(delta)) if by.get(t,{}).get('mode')==mode];motion=np.sum(delta[ts],axis=0) if ts else np.zeros(3);phases.append(dict(mode=mode,intervals=len(ts),object_delta_xyz_mm=(motion*1000).tolist(),signed_progress_mm=float(direction*motion[1]*1000),waist_command_at_reserve=sum(bool(abs(u[t,0])>=.98-1e-6) for t in ts)))
 first=next(r['step'] for r in fr['rows'] if r['mode']=='top_push');plan=fr['plan'];report=dict(run=run,episode=ep.name,planned_rear_goal_x_m=plan['rear_goal_x'],planned_margin_m=plan['margin'],first_top_push_step=first,object_pre_top_push_delta_xyz_mm=((xyz[first]-xyz[0])*1000).tolist(),total_object_delta_xyz_mm=((xyz[-1]-xyz[0])*1000).tolist(),phases=phases,source_sha256={n:sha(ep/n) for n in ['raw.npz','trace.npz','frontal_bypass.json']});reports.append(report);print(run,task,'pretop',np.round(report['object_pre_top_push_delta_xyz_mm'],3).tolist(),'rear_goal_x',plan['rear_goal_x'],flush=True)
p=w/'BYPASS_MOTION_BUDGET_DIAGNOSIS.json';assert not p.exists();p.write_text(json.dumps(dict(episodes=reports,checker_sha256=sha(Path(__file__)),training_ready=False,scope='Observed interval t to t+1 assigned to current executed phase. RearX motion is a declared object-envelope bypass, not an accidental region-approach collision. Describes route cost and measured waist reserve usage; does not prove no alternative joint trajectory exists or authorize a changed route.'),indent=2))
