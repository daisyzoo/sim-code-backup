"""Audit full recorded-input shadows and reject damaged evidence; not physics."""
from pathlib import Path
import json,hashlib,copy
import numpy as np
from audit_front_cop_route_axis_probe import reconstruct
w=Path(__file__).resolve().parent;stage=w/'staged_front_cop_route_axis_probe';fixture=json.loads((stage/'ROUTE_AXIS_REPLAY_CHECK.json').read_text());profile=json.loads((w/'region_continuity_groups_r1/case_840001/layout_840001_nudge_mailer_to_bin/frontal_bypass.json').read_text())['plan']['front_route_live_guards'];reports=[]
for case in fixture['rows']:
 ep=Path(case['episode']);plan=json.loads((ep/'frontal_bypass.json').read_text())['plan'];plan['front_route_live_guards']=profile;rows=[dict(x['counterfactual_row'],step=x['step']) for x in case['records']]
 with np.load(ep/'trace.npz') as z:tr={k:z[k] for k in z.files}
 with np.load(ep/'parcel_orientation.npz') as z:ori={k:z[k] for k in z.files}
 packets={x['after_action_step']:x for x in json.loads((ep/'solved_contact_forces.json').read_text())['rows']};key='box' if 'push_box' in ep.name else 'mailer';records,errors=reconstruct(rows,plan,tr,ori,packets,key);print(ep.name,'errors',errors[:5],flush=True);assert not errors and len(records)==case['override_frames']
 t=records[0]['step'];idx=next(i for i,x in enumerate(rows) if x['step']==t);rejected=[]
 for kind in ['command','anchor','route_stage','missing_trace','wrong_packet_pose','missing_previous_frame','route_anchor_reset','previous_route_stage','cross_axis_parent','wrong_active_axis']:
  damaged=copy.deepcopy(rows);fp=packets
  if kind=='command':damaged[idx]['target_xyz'][0]+=.001
  elif kind=='anchor':damaged[idx]['cop_slip_following']['anchor_local'][0]+=.01
  elif kind=='route_stage':damaged[idx]['route_stage']='corrupt'
  elif kind=='missing_trace':damaged[idx].pop('cop_slip_following')
  elif kind=='wrong_packet_pose':
   fp=dict(packets);fp[t-1]=copy.deepcopy(fp[t-1]);fp[t-1]['post_action_pose'][key][0]+=.01
  elif kind=='route_anchor_reset':damaged[idx]['cop_slip_following']['route_anchor_reset']=not damaged[idx]['cop_slip_following']['route_anchor_reset']
  elif kind=='previous_route_stage':damaged[idx]['cop_slip_following']['previous_route_stage']='corrupt'
  elif kind=='cross_axis_parent':damaged[idx]['cop_slip_following']['route_axis_control']['parent_xy'][0]+=.001
  elif kind=='wrong_active_axis':damaged[idx]['cop_slip_following']['route_axis_control']['active_axis']=1-damaged[idx]['cop_slip_following']['route_axis_control']['active_axis']
  else:damaged.pop(idx-1)
  _,errs=reconstruct(damaged,plan,tr,ori,fp,key);assert errs,kind;rejected.append(kind)
 reports.append(dict(episode=str(ep),frames=len(rows),loaded_steps_checked=len(records),max_waypoint_error_m=max(r['waypoint_error_m'] for r in records),corruptions_rejected=rejected))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();out=dict(passed=True,rows=reports,auditor_sha256=sha(w/'audit_front_cop_route_axis_probe.py'),checker_sha256=sha(Path(__file__)),counterfactual_fixture_sha256=sha(stage/'ROUTE_AXIS_REPLAY_CHECK.json'),scope='Full counterfactual controller output on fixed recorded failed trajectories. Independent actual packet/geometry/math recomputation and10 corruptions per case. No new physical rollout or successful task.',training_ready=False);(stage/'ROUTE_AXIS_AUDITOR_CHECK.json').write_text(json.dumps(out,indent=2));print(out)
