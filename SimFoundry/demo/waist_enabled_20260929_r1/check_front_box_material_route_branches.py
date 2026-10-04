"""Actual wrapper branches against recorded parent rows; parent call is stubbed.
This checks wrapper routing only, not full parent evolution or physical response.
"""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import copy,datetime,hashlib,json,sys
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];D=W/'front_box_material_preload_draft_r1';S=W/'staged_front_corridor_midpoint_integrated';sys.path[:0]=[str(D),str(S),str(W),str(ROOT)]
from front_box_material_preload_route import FrontBoxMaterialPreloadState
from front_initial_center_cop_route import FrontCopRouteState
from material_preload_v2 import MaterialPreload
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();r=W/'front_recontact_headroom_physical_r1';ep=r/'case_840023/layout_840023_nudge_mailer_to_bin';bag=json.loads((ep/'frontal_bypass.json').read_text());be=W/'front_recontact_physical_r1/case_840020/layout_840020_push_box_to_bin';box=json.loads((be/'frontal_bypass.json').read_text());checks=[]
def execute(row,plan,side,enabled=True):
 obj=FrontBoxMaterialPreloadState.__new__(FrontBoxMaterialPreloadState)
 obj.material_preload_enabled=enabled;obj.material_preload=MaterialPreload();obj.last_emitted_xy=row.get('cop_slip_following',{}).get('previous_command_xy',row['target_xyz'][:2]);obj.cop_slip_enabled=obj.reset_cop_on_route_change=obj.route_axis_only=obj.edge_speed_enabled=True;obj.cop_drive_step_m=.002;obj.side=side;obj.recontacts=row.get('recontacts',0);obj.rear=SimpleNamespace(plan=plan);obj.route_report=dict(goal_y=.205 if side=='left' else -.205)
 def parent(state,*args,**kwargs):state.command=tuple(row['target_xyz']);state.last_emitted_xy=tuple(row['target_xyz'][:2]);return copy.deepcopy(row)
 target=row.get('observed_target',plan['initial_target_xyz']);tip=row.get('observed_physical_support_xyz',row['observed_support_xyz']);cop=row.get('cop_slip_following',{});slip=dict(valid=True,normal_load_n=3.,weighted_contact_local=cop.get('measured_cop_local',[0.,0.,.0225])) if cop.get('override') else None
 with patch.object(FrontCopRouteState,'update',autospec=True,side_effect=parent) as call:
  out=obj.update(target,target,[.6,.2,.77],.07,.08,tip=tip,quat=[0.,0.,0.,1.],obstacle_quat=[0.,0.,0.,1.],control_offset_local=[.23,0.,-.03],load_n=3.,hand_obstacle_gap_m=.1,slip_contact=slip)
 assert call.call_count==1
 return obj,out
# A latched guard row intentionally has no route_goal_x: must never consult drive geometry.
guard=next(x for x in bag['rows'] if x.get('route_stop_reason'));assert 'route_goal_x' not in guard
obj,out=execute(guard,bag['plan'],'left');assert out['target_xyz']==guard['target_xyz'] and not out['front_box_material_preload']['override'];checks.append('latched_guard_without_drive_fields')
for side,log in [('right',box),('left',bag)]:
 for mode in sorted({x['mode'] for x in log['rows']}):
  row=next(x for x in log['rows'] if x['mode']==mode);obj,out=execute(row,log['plan'],side,False);assert out==row;checks.append('disabled_'+side+'_'+mode)
  obj,out=execute(row,log['plan'],side,True)
  if side=='left' or mode!='top_push':assert out['target_xyz']==row['target_xyz'] and not out['front_box_material_preload']['override']
  elif out['front_box_material_preload']['override']:
   e=out['front_box_material_preload'];assert out['target_xyz'][2]==row['target_xyz'][2] and list(obj.last_emitted_xy)==e['emitted_xy']
   cross=e['preserved_cross_axis']
   if cross is not None:assert out['target_xyz'][cross]==row['target_xyz'][cross]
   assert e['drive_step_m']==row['cop_slip_following']['edge_speed']['drive_step_m']
  checks.append('dispatch_'+side+'_'+mode)
with (D/'ROUTE_BRANCH_CHECK.json').open('x') as f:json.dump(dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,checks=checks,source_sha256={str(p):sha(p) for p in [Path(__file__),D/'front_box_material_preload_route.py',D/'material_preload_v2.py',ep/'frontal_bypass.json',be/'frontal_bypass.json']},collector_integrated=False,training_ready=False),f,indent=2)
print('passed',len(checks))
