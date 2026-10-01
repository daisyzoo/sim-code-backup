"""Audit full recorded-input shadows and reject damaged evidence; not physics."""
from pathlib import Path
import json,hashlib,copy
import numpy as np
from audit_front_edge_speed_live import reconstruct
w=Path(__file__).resolve().parent;stage=w/'staged_front_edge_speed_probe';fixture=json.loads((stage/'EDGE_SPEED_REPLAY_CHECK.json').read_text());profile=json.loads((w/'region_continuity_groups_r1/case_840001/layout_840001_nudge_mailer_to_bin/frontal_bypass.json').read_text())['plan']['front_route_live_guards'];reports=[]
for case in fixture['rows']:
 ep=Path(case['episode']);plan=json.loads((ep/'frontal_bypass.json').read_text())['plan'];plan['front_route_live_guards']=profile;plan['front_cop_slip_following']['drive_step_m']=.002;plan['front_cop_slip_following']['edge_speed']=dict(enabled=True,minimum_drive_step_m=.001,warning_distance_m=.010,actual_core_size_xyz=(np.array([.14,.09,.045] if 'push_box' in ep.name else [.15,.145,.04])*np.array([.96,.96,1.] if 'push_box' in ep.name else [.90,.88,1.])).tolist());rows=[dict(x['counterfactual_row'],step=x['step']) for x in case['records']]
 with np.load(ep/'trace.npz') as z:tr={k:z[k] for k in z.files}
 with np.load(ep/'parcel_orientation.npz') as z:ori={k:z[k] for k in z.files}
 packets={x['after_action_step']:x for x in json.loads((ep/'solved_contact_forces.json').read_text())['rows']};key='box' if 'push_box' in ep.name else 'mailer';records,errors=reconstruct(rows,plan,tr,ori,packets,key);print(ep.name,'errors',errors[:5],flush=True);assert not errors and len(records)==case['override_frames']
 t=records[0]['step'];idx=next(i for i,x in enumerate(rows) if x['step']==t);rejected=[]
 for kind in ['command','anchor','route_stage','missing_trace','wrong_packet_pose','missing_previous_frame','route_anchor_reset','previous_route_stage','cross_axis_parent','wrong_active_axis','drive_vector','declared_drive','edge_distance','edge_step','edge_core','inactive_edge_override','inactive_edge_step']:
  damaged=copy.deepcopy(rows);fp=packets;used_plan=plan
  if kind in ['inactive_edge_override','inactive_edge_step']:
   ii=next(j for j,x in enumerate(damaged) if x['mode']!='top_push')
   damaged[ii]['cop_slip_following']['edge_speed']['applied' if kind=='inactive_edge_override' else 'drive_step_m']=True if kind=='inactive_edge_override' else .003
  elif kind=='edge_distance':damaged[idx]['cop_slip_following']['edge_speed']['forward_core_distance_m']+=.01
  elif kind=='edge_step':damaged[idx]['cop_slip_following']['edge_speed']['drive_step_m']+=.0005
  elif kind=='edge_core':used_plan=copy.deepcopy(plan);used_plan['front_cop_slip_following']['edge_speed']['actual_core_size_xyz'][0]+=.03
  elif kind=='command':damaged[idx]['target_xyz'][0]+=.001
  elif kind=='anchor':damaged[idx]['cop_slip_following']['anchor_local'][0]+=.01
  elif kind=='drive_vector':damaged[idx]['cop_slip_following']['drive_xy'][0]+=.001
  elif kind=='declared_drive':used_plan=copy.deepcopy(plan);used_plan['front_cop_slip_following']['drive_step_m']=.001
  elif kind=='route_stage':damaged[idx]['route_stage']='corrupt'
  elif kind=='missing_trace':damaged[idx].pop('cop_slip_following')
  elif kind=='wrong_packet_pose':
   fp=dict(packets);fp[t-1]=copy.deepcopy(fp[t-1]);fp[t-1]['post_action_pose'][key][0]+=.01
  elif kind=='route_anchor_reset':damaged[idx]['cop_slip_following']['route_anchor_reset']=not damaged[idx]['cop_slip_following']['route_anchor_reset']
  elif kind=='previous_route_stage':damaged[idx]['cop_slip_following']['previous_route_stage']='corrupt'
  elif kind=='cross_axis_parent':damaged[idx]['cop_slip_following']['route_axis_control']['parent_xy'][0]+=.001
  elif kind=='wrong_active_axis':damaged[idx]['cop_slip_following']['route_axis_control']['active_axis']=1-damaged[idx]['cop_slip_following']['route_axis_control']['active_axis']
  else:damaged.pop(idx-1)
  _,errs=reconstruct(damaged,used_plan,tr,ori,fp,key);assert errs,kind;rejected.append(kind)
 reports.append(dict(episode=str(ep),frames=len(rows),loaded_steps_checked=len(records),max_waypoint_error_m=max(r['waypoint_error_m'] for r in records),corruptions_rejected=rejected))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();out=dict(passed=True,rows=reports,auditor_sha256=sha(w/'audit_front_edge_speed_live.py'),checker_sha256=sha(Path(__file__)),counterfactual_fixture_sha256=sha(stage/'EDGE_SPEED_REPLAY_CHECK.json'),scope='Full counterfactual controller output on fixed recorded trajectories. Independent actual packet/geometry/math recomputation and17 corruptions per case. No new physical rollout or successful task.',training_ready=False);(stage/'EDGE_SPEED_AUDITOR_CHECK.json').write_text(json.dumps(out,indent=2));print(out)
