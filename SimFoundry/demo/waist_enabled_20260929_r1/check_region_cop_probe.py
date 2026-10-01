# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
"""Real failed push-bout inputs; no new trajectories or inferred force response."""
from pathlib import Path
import sys,json,hashlib,copy
import numpy as np
w=Path(__file__).resolve().parent;stage=w/'staged_region_cop_slip_probe';sys.path[:0]=[str(stage),str(w.parents[1])]
from region_top_contact import TopContactBypassState
from region_cop_route import RegionCopRouteState
from simfoundry.data.frontal_bypass import FrontalBypassState
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();results=[]
for case,task,key,other,side,size in [(840001,'push_box_to_bin','box','mailer','right',(.14,.09,.045)),(840004,'nudge_mailer_to_bin','mailer','box','left',(.15,.145,.04))]:
 ep=w/'region_continuity_groups_r1'/f'case_{case}'/f'layout_{case}_{task}';log=json.loads((ep/'frontal_bypass.json').read_text());plan=log['plan'];by={r['step']:r for r in log['rows']};diag=json.loads((ep/'TOP_CONTACT_BOUT_DIAGNOSIS.json').read_text());measured={r['step']:r for r in diag['series']}
 for f,h in diag['source_sha256'].items():assert sha(ep/f)==h
 reg=json.loads((ep/'region_approach.json').read_text())['rows'];handover=next(r for r in reg if r['solver'] and r['solver'].get('handover'));selected=handover['selected_surface_local_xy']
 with np.load(ep/'trace.npz') as z:tr={k:z[k] for k in z.files}
 with np.load(ep/'parcel_orientation.npz') as z:ori={k:z[k] for k in z.files}
 records=[];bout_reports=[]
 def arguments(t):
  r=by[t];m=measured.get(t);cop=dict(valid=True,normal_load_n=m['normal_load_n'],weighted_contact_local=m['cop_local_xyz_m']) if m and 'cop_local_xyz_m' in m else None
  args=(tr['palm_'+side][t],tr[key][t],tr[other][t],plan['target_radius_x'],plan['obstacle_radius_x']);kw=dict(tip=r['observed_support_xyz'],quat=ori[key][t],control_offset_local=r['control_offset_local'],load_n=r['contact_load']['observed_vertical_load_n'],hand_obstacle_gap_m=r['hand_obstacle_gap_m']);return args,kw,cop
 for bout in diag['bouts']:
  t=bout['start'];prev=by[t-1];assert prev['mode']=='top_press';args,kw,cop=arguments(t);states={}
  for label,cls,enabled in [('parent',TopContactBypassState,False),('disabled',RegionCopRouteState,False),('enabled',RegionCopRouteState,True)]:
   extra={'cop_slip_enabled':enabled} if label!='parent' else {}
   s=cls(FrontalBypassState(plan,staging_z=.92,press_z=.822,feedback_rear_endpoint=True,follow_target_y=True),side,size,guarded_descent=True,continuous_drag=True,alignment_tolerance_m=.01,tilt_recontact_rad=.03,confirm_terminal_release=True,hold_established_x=True,**extra)
   s.top_mode='top_press';s.settled=2;s.load.desired_n=5.;s.load.bias_m=prev['contact_load']['stored_z_bias_m'];s.load.filtered_n=prev['contact_load']['filtered_vertical_load_n'];s.push_x_anchor=prev['push_x_anchor_m'];s.selected_surface_local_xy=tuple(selected);s.last_waypoint_xy=tuple(prev['target_xyz'][:2]);s.recontacts=prev['recontacts'];s.start=tuple(kw['tip']);states[label]=s
  initial=copy.deepcopy(states)
  max_parent_error=0.;overrides=0;maxstep=0.;maxlead=0.
  for t in range(bout['start'],bout['end']+1):
   args,kw,cop=arguments(t);out={}
   for label,s in states.items():out[label]=s.update(*args,**kw,**({'slip_contact':cop} if label!='parent' else {}))
   assert out['parent']==out['disabled'],(key,t,'disabled drift')
   err=float(np.max(abs(np.asarray(out['parent']['target_xyz'])-by[t]['target_xyz'])));max_parent_error=max(max_parent_error,err);assert err<2e-6,(key,t,'parent reconstruction',err)
   a,b=out['parent'],out['enabled'];assert a['mode']==b['mode'] and abs(a['target_xyz'][2]-b['target_xyz'][2])<1e-12
   f=b['region_cop_slip_following']
   if f['override']:
    overrides+=1;maxstep=max(maxstep,max(abs(x) for x in f['command_delta_xy']));maxlead=max(maxlead,max(abs(x) for x in f['command_reference_lead_xy']));assert maxstep<=.002000001
    assert abs(f['drive_xy'][0])<1e-12
   records.append(dict(step=t,counterfactual_row=b,parent_waypoint_error_m=err))
  # Test actual triggering of original emergency/release branches, no hidden override.
  guards=[]
  for guard in ['tilt','lost_contact','terminal','zero_load','no_cop']:
   pair={};args,kw,cop=arguments(bout['start']);args=list(args)
   for label in ['parent','enabled']:
    s=copy.deepcopy(initial[label]);gkw=dict(kw);gargs=list(args)
    if guard in ['tilt','lost_contact','terminal']:s.top_mode='top_push';s.command=tuple(prev['target_xyz']);s.lost_contact_steps=2
    if guard=='tilt':gkw['quat']=(float(np.sin(.06/2)),0.,0.,float(np.cos(.06/2)))
    elif guard=='lost_contact':gkw['load_n']=0.
    elif guard=='terminal':gargs[1]=np.array(args[1],copy=True);gargs[1][1]=.35 if side=='left' else -.35
    elif guard=='zero_load':s.settled=0;s.load.filtered_n=0.;gkw['load_n']=0.
    count=12 if guard=='zero_load' else 1
    for _ in range(count):
     row=s.update(*gargs,**gkw,**({'slip_contact':None if guard in ['no_cop','zero_load'] else cop} if label=='enabled' else {}))
     if guard=='zero_load':assert row['mode']!='top_push'
    pair[label]=row
   clean=dict(pair['enabled']);f=clean.pop('region_cop_slip_following');assert clean==pair['parent'],(key,bout['start'],guard,'parent guard output mismatch');assert not f['override']
   if guard in ['tilt','lost_contact']:assert clean['mode']=='top_lift'
   if guard=='terminal':assert clean['mode']=='top_release'
   guards.append(guard)
  bout_reports.append(dict(start=bout['start'],frames=bout['frames'],counterfactual_loaded_overrides=overrides,max_parent_waypoint_error_m=max_parent_error,max_xy_step_m=maxstep,max_reference_axis_lead_m=maxlead,actual_guard_fixtures=guards))
 assert len(bout_reports)==10
 result=dict(episode=ep.name,bouts=bout_reports,records=records,source_sha256={f:sha(ep/f) for f in ['raw.npz','trace.npz','frontal_bypass.json','parcel_orientation.npz','region_approach.json','TOP_CONTACT_BOUT_DIAGNOSIS.json']});results.append(result)
 print(ep.name,'bouts',len(bout_reports),'frames',len(records),'overrides',sum(b['counterfactual_loaded_overrides'] for b in bout_reports),'maxparent',max(b['max_parent_waypoint_error_m'] for b in bout_reports))
report=dict(passed=True,results=results,source_sha256={f:sha(stage/f) for f in ['region_top_contact.py','region_cop_route.py','contact_slip_following.py']},checker_sha256=sha(__file__),scope='All20 recorded failed rear bouts; parent actual-waypoint reconstruction, disabled equality, fixed-old-observation mode/Z equality and original guard fixtures. Only counterfactual command outputs, no new physical force/pose or success inference. Collector unwired.',training_ready=False)
(stage/'RECORDED_BOUT_CHECK.json').write_text(json.dumps(report,indent=2))
