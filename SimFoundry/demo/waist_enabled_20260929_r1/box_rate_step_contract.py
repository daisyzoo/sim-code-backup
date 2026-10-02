"""Read explicit executed-route drag increment; never infer it from a filename."""
import math

def declared_step(plan):
 cfg=plan['top_recontact'];step=cfg['drag_step_m']
 assert type(step) in (int,float) and math.isfinite(step) and step in (.001,.003)
 assert cfg['continuous_drag'] is True
 return step

def verify_declared_step(args,plan,meta):
 assert args.get('rear_box_slow_drag') is True and meta.get('rear_box_slow_drag') is True
 assert args['expert_frontal_top_drag_step_m']==.003
 rear=plan.get('rear_cop_centering',{}).get('enabled',False)
 assert type(rear) is bool
 if rear:
  assert not plan.get('front_route_selected') and not plan.get('initial_top_selected')
 assert type(plan['direction']) in (int,float) and plan['direction'] in (-1,1)
 expected=.001 if rear and plan['direction']==-1 else .003
 assert declared_step(plan)==expected,('effective drag mismatch',expected,declared_step(plan))
 return expected
