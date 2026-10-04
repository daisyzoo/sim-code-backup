"""Causal-observation XY proposal replay, NOT a simulated or executed trajectory.
Measured states/contacts remain from old controls; only proposed XY history is
hypothetical. Full IK, force response and success cannot be inferred from this.
"""
from pathlib import Path
import copy,datetime,hashlib,json,sys
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;D=W/'front_box_material_preload_draft_r1';sys.path.insert(0,str(D));from material_preload import MaterialPreload
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();runs=[];sources={};checks=[]
for run in ['front_corridor_midpoint_physical_r1','front_drive_1mm_physical_r1','front_recontact_physical_r1']:
 ep=W/run/'case_840020/layout_840020_push_box_to_bin';fr=json.loads((ep/'frontal_bypass.json').read_text());assert fr['plan']['front_route_selected'];rows=fr['rows'];assert len(rows)==1199
 with np.load(ep/'parcel_orientation.npz') as z:rot=Rotation.from_quat(z['box']).as_matrix()
 life=MaterialPreload();proposal_previous=None;outs=[]
 for r in rows:
  t=r['step'];cop=r.get('cop_slip_following',{});valid=cop.get('override',False);normal=r.get('direction_change_recontact',{}).get('micro_repair_retention',{}).get('normal_load_n',0.)
  prev=np.asarray(cop.get('previous_command_xy',r['target_xyz'][:2]) if proposal_previous is None else proposal_previous)
  if r.get('front_diagonal_entry',{}).get('selected'):gy=r['front_diagonal_entry']['goal_y']
  elif r['route_stage']=='front_x':gy=fr['plan']['initial_target_xyz'][1]
  else:gy=-.205
  args=dict(enabled=True,selected=True,side='right',mode=r['mode'],route_stage=r['route_stage'],recontacts=r['recontacts'],parent_guard=bool(r.get('route_stop_reason') or r.get('release_reason')),object_xyz=r['observed_target'],object_rotation=rot[t],observed_support_xyz=r['observed_physical_support_xyz'],previous_command_xy=prev,goal_xy=[r['route_goal_x'],gy],normal_load_n=normal,cop_valid=bool(valid))
  e=life.update(**args)
  if e['override']:
   command=np.asarray(e['command_xy']);ref=np.asarray(args['observed_support_xyz']);obj=np.asarray(args['object_xyz']);anchor=obj+rot[t]@np.asarray(e['reference_local']);delta=np.asarray(args['goal_xy'])-obj[:2];unit=delta/np.linalg.norm(delta)
   assert np.max(abs(command-prev))<=.003+1e-12 and e['preload_m']<=.012
   np.testing.assert_allclose(anchor,e['anchor_world'],atol=1e-12,rtol=0)
   desired=anchor[:2]+unit*min(e['preload_m'],np.linalg.norm(delta));expected=prev+np.clip(np.clip(desired,ref[:2]-.030,ref[:2]+.030)-prev,-.003,.003);np.testing.assert_allclose(command,expected,atol=1e-12,rtol=0)
   e['step']=t;outs.append(e);proposal_previous=command
  else:proposal_previous=np.asarray(r['target_xyz'][:2])
  disabled=MaterialPreload().update(**dict(args,enabled=False));assert disabled==dict(override=False,reason='disabled')
 runs.append(dict(run=run,original_frames=1200,checked_rows=len(rows),proposal_count=len(outs),captures=sum(e['captured_reference'] for e in outs),max_preload_m=max(e['preload_m'] for e in outs),lead_lag_flag_count=sum(e['retained_slew_lag_outside_lead'] for e in outs),rows=outs))
 for name in ['frontal_bypass.json','parcel_orientation.npz']:sources[str(ep/name)]=sha(ep/name)
# Independent exact rigid-translation behavior after finite preload saturation.
a=dict(enabled=True,selected=True,side='right',mode='top_push',route_stage='lateral_y',recontacts=0,parent_guard=False,object_xyz=np.array([.4,.1,.77]),object_rotation=np.eye(3),observed_support_xyz=np.array([.4,.1,.795]),previous_command_xy=np.array([.4,.1]),goal_xy=[.4,-.2],normal_load_n=3.,cop_valid=True)
l=MaterialPreload()
for j in range(30):
 e=l.update(**a);a['previous_command_xy']=e['command_xy']
assert abs(e['preload_m']-.012)<1e-12;np.testing.assert_allclose(e['command_xy'],[.4,.088],atol=1e-12,rtol=0);checks.append('no_unbounded_drive_accumulation')
a['object_xyz'][1]-=.001;a['observed_support_xyz'][1]-=.001;e=l.update(**a);np.testing.assert_allclose(e['command_xy'],[.4,.087],atol=1e-12,rtol=0);checks.append('measured_object_translation_following')
for name,change in [('disabled',dict(enabled=False)),('unselected',dict(selected=False)),('wrong_hand',dict(side='left')),('non_push',dict(mode='top_lift')),('parent_guard',dict(parent_guard=True)),('lost_load',dict(normal_load_n=.2)),('invalid_cop',dict(cop_valid=False))]:
 l=MaterialPreload();l.update(**a);e=l.update(**dict(a,**change));assert e['override'] is False and l.reference_local is None;checks.append(name)
for name,change in [('new_counter',dict(recontacts=1)),('new_route',dict(route_stage='front_x'))]:
 l=MaterialPreload();l.update(**a);e=l.update(**dict(a,**change));assert e['captured_reference'] and e['preload_m']==.002;checks.append(name)
for name,change in [('nan_load',dict(normal_load_n=float('nan'))),('nan_geometry',dict(object_xyz=[float('nan'),0,0])),('invalid_rotation',dict(object_rotation=np.zeros((3,3))))]:
 try:MaterialPreload().update(**dict(a,**change))
 except ValueError:checks.append(name)
 else:raise AssertionError(name)
sources.update({str(p):sha(p) for p in [Path(__file__),D/'material_preload.py',W/'front_box_directed_force_findings_20261003_r1.json']})
with (D/'REPLAY_CHECK.json').open('x') as f:json.dump(dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,runs=runs,checks=checks,source_sha256=sources,unwired=True,simulation_started=False,training_ready=False),f,indent=2)
print(json.dumps(dict(passed=True,runs=[{k:v for k,v in r.items() if k!='rows'} for r in runs],guard_checks=len(checks))))
