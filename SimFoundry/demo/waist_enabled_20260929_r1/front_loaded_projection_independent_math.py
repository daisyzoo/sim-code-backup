"""Independent scalar feasible-set/nearest-parent audit, never a control helper.
Inputs must be bound to measured geometry and previous emitted action by caller.
This proves recorded command mathematics, not physical feasibility or success.
"""
import math
STRATEGY='nearest_parent_in_slew_hand_material_intersection'
def vec(v):
 assert isinstance(v,(list,tuple)) and len(v)==2
 assert all(type(x) in (int,float) and math.isfinite(x) for x in v)
 return [float(x) for x in v]
def near(a,b):
 a,b=vec(a),vec(b);assert max(abs(x-y) for x,y in zip(a,b))<=1e-10,(a,b)
def verify(record,*,parent,previous,reference,material,normal):
 parent,previous,reference,material=map(vec,(parent,previous,reference,material))
 assert math.isfinite(normal) and normal>=.3
 assert record['projection_strategy']==STRATEGY
 assert record['cap_xy_m']==.010 and record['original_step_m']==.003 and record['original_hand_lead_m']==.030
 assert abs(record['normal_load_n']-normal)<=2e-6
 for key,want in [('parent_xy',parent),('previous_command_xy',previous),('reference_xy',reference),('material_surface_xy',material)]:near(record[key],want)
 assert max(abs(x-y) for x,y in zip(parent,previous))<=.003+1e-10
 ranges=[[(previous[j]-.003,previous[j]+.003),(reference[j]-.030,reference[j]+.030),(material[j]-.010,material[j]+.010)] for j in range(2)]
 bounds=[(max(x[0] for x in axis),min(x[1] for x in axis)) for axis in ranges]
 lower,upper=[b[0] for b in bounds],[b[1] for b in bounds]
 near(record['lower'],lower);near(record['upper'],upper)
 feasible=all(lo<=hi for lo,hi in bounds)
 old_feasible=all(max(lower[j],min(previous[j],parent[j]))<=min(upper[j],max(previous[j],parent[j])) for j in range(2))
 assert record['previous_added_segment_was_feasible'] is old_feasible
 if not feasible:
  assert record['command_xy'] is None and record['requires_recontact'] is True
  assert record['applied'] is False and record['changed'] is False
  assert record['reason']=='empty_original_slew_lead_material_intersection'
  return dict(feasible=False,command_xy=None,boundary_following_repair=False)
 expected=[min(hi,max(lo,parent[j])) for j,(lo,hi) in enumerate(bounds)]
 assert record['requires_recontact'] is False and record['applied'] is True and record['reason']=='bounded_material_reference'
 near(record['command_xy'],expected)
 assert record['changed'] is (max(abs(x-y) for x,y in zip(expected,parent))>1e-12)
 assert record['boundary_following_repair'] is (not old_feasible)
 near(record['command_delta_xy'],[x-y for x,y in zip(expected,previous)])
 near(record['command_reference_lead_xy'],[x-y for x,y in zip(expected,reference)])
 near(record['command_material_offset_xy'],[x-y for x,y in zip(expected,material)])
 return dict(feasible=True,command_xy=expected,boundary_following_repair=not old_feasible)
