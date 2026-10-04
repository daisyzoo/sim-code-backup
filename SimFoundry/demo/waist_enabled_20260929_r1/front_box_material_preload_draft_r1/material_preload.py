"""Isolated default-off front-box XY proposal; never a dynamics prediction.
A measured support reference is captured in object coordinates. A finite12mm
preload replaces repeated drive accumulation. Parent guards, Z, task IK, solved
contacts, full action gates and final admission are mandatory outside this helper.
"""
from dataclasses import dataclass
import numpy as np

@dataclass
class MaterialPreload:
    reference_local: object = None
    phase: object = None
    preload_m: float = 0.

    def reset(self):
        self.reference_local=None;self.phase=None;self.preload_m=0.

    def update(self, *, enabled=False, selected=False, side, mode, route_stage,
               recontacts, parent_guard, object_xyz, object_rotation,
               observed_support_xyz, previous_command_xy, goal_xy,
               normal_load_n, cop_valid):
        if type(enabled) is not bool or type(selected) is not bool or type(parent_guard) is not bool or type(cop_valid) is not bool:
            raise ValueError('Expected explicit boolean dispatch')
        if not enabled:
            self.reset();return dict(override=False,reason='disabled')
        if not selected or side!='right' or mode!='top_push' or parent_guard:
            self.reset();return dict(override=False,reason='parent_or_unselected')
        if type(recontacts) is not int or recontacts<0 or route_stage not in ('front_x','lateral_y'):
            raise ValueError('Invalid actual phase/recontact')
        if not np.isfinite(normal_load_n) or normal_load_n<0:raise ValueError('Invalid observed load')
        if not cop_valid or normal_load_n<.3:
            self.reset();return dict(override=False,reason='no_valid_current_loaded_cop')
        obj,R,ref,prev,goal=[np.asarray(x,float) for x in [object_xyz,object_rotation,observed_support_xyz,previous_command_xy,goal_xy]]
        if [x.shape for x in [obj,R,ref,prev,goal]]!=[(3,),(3,3),(3,),(2,),(2,)]:raise ValueError('Invalid geometry dimensions')
        if not all(np.isfinite(x).all() for x in [obj,R,ref,prev,goal]):raise ValueError('Nonfinite geometry')
        if not np.allclose(R.T@R,np.eye(3),atol=1e-6) or np.linalg.det(R)<.99999:raise ValueError('Invalid rotation')
        delta=goal-obj[:2];distance=float(np.linalg.norm(delta))
        if distance<=1e-12:self.reset();return dict(override=False,reason='no_drive_direction')
        phase=(route_stage,recontacts);fresh=self.reference_local is None or self.phase!=phase
        if fresh:self.reference_local=R.T@(ref-obj);self.phase=phase;self.preload_m=0.
        self.preload_m=min(.012,self.preload_m+.002)
        direction=delta/distance;anchor=obj+R@self.reference_local
        desired=anchor[:2]+direction*min(self.preload_m,distance)
        bounded=np.clip(desired,ref[:2]-.030,ref[:2]+.030)
        command=prev+np.clip(bounded-prev,-.003,.003)
        return dict(override=True,reason='bounded_material_reference_preload',command_xy=command.tolist(),reference_local=self.reference_local.tolist(),captured_reference=fresh,phase=list(phase),preload_m=self.preload_m,anchor_world=anchor.tolist(),drive_direction_xy=direction.tolist(),desired_xy=desired.tolist(),previous_command_xy=prev.tolist(),observed_support_xyz=ref.tolist(),command_delta_xy=(command-prev).tolist(),command_reference_lead_xy=(command-ref[:2]).tolist(),desired_lead_clipped=bool(np.any(abs(bounded-desired)>1e-12)),retained_slew_lag_outside_lead=bool(np.any(abs(command-ref[:2])>.030+1e-9)),original_parent_checks_required=True,synthetic_proposal_only=True)
