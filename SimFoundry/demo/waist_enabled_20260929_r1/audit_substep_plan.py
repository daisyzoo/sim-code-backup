"""Original center-plan dispatcher plus independent entry-lift attempt checks."""
import numpy as np
from audit_box_center_plan import PlanAudit
from audit_unloaded_wrist_prior_live import near

def verify_entry_plan(audit,created,*,current,scene,step):
 q=np.asarray(current,float);assert scene['side']=='right' and type(step) is int and created['step']==step and created['scene']==scene
 near(created['start'],q,1e-7);assert audit.hand.minz(q,'right')<.84 and audit.geometry(q,scene)[0]['accepted']
 height=.845-float(scene['target_xyz'][2])-float(scene['core_size'][2])/2
 lift=created['lift'];audit.lift(lift,q,height,scene);path=created['path'];endz=None
 if lift['accepted']:
  assert path is not None;audit.checked_path(path,[q,np.array(lift['candidate'])],scene)
  if path['accepted']:endz=audit.hand.minz(lift['candidate'],'right')
 else:assert path is None
 if endz is None:assert created['endpoint_lowest_world_z_m'] is None
 else:near(endz,created['endpoint_lowest_world_z_m'],1e-8)
 expected=bool(path and path['accepted'] and endz>=.84)
 assert created['accepted'] is expected
 return dict(accepted=expected,endpoint_lowest_world_z_m=endz)
