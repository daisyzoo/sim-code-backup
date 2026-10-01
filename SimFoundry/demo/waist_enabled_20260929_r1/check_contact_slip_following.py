"""Causal feedback sign, retained preload, original-mode deference and bounds."""
from pathlib import Path
import sys,json,hashlib,copy
import numpy as np
w=Path(__file__).resolve().parent;stage=w/'staged_contact_slip_following';sys.path.insert(0,str(stage))
from contact_slip_following import CopSlipFollowing
base=dict(mode='top_push',object_xyz=np.array([.5,0.,.77]),object_rotation=np.eye(3),object_size=[.14,.09,.045],goal_xy=[.5,.2],reference_xy=[.5,0.],previous_command_xy=[.505,.005],cop_world=np.array([.5,0.,.7925]),normal_load_n=5.)
c=CopSlipFollowing();a=c.update(**base);assert np.allclose(a['command_xy'],[.505,.006]);assert np.allclose(a['slip_correction_xy'],0)
b=dict(base,cop_world=np.array([.5,.02,.7925]),previous_command_xy=a['command_xy'],reference_xy=[.5,.02]);v=c.update(**b);assert np.allclose(v['drive_xy'],[0,.001]) and np.allclose(v['slip_correction_xy'],[0,-.001]);assert np.allclose(v['command_xy'],a['command_xy'])
b.update(object_xyz=np.array([.5,.002,.77]),cop_world=np.array([.5,.022,.7925]),reference_xy=[.5,.022],previous_command_xy=v['command_xy']);v2=c.update(**b);assert np.allclose(v2['object_anchor_translation_xy'],[0,.002]);assert np.allclose(np.asarray(v2['command_xy'])-v['command_xy'],[0,.002])
checks=['retains_previous_command_preload','20mm_forward_slip_cancels1mm_drive','follows_observed_object_translation']
for mode in ['top_lift','top_cross','top_descend','top_press','top_release','front_guard_lift']:
 out=c.update(**dict(base,mode=mode));assert not out['override'] and c.local_anchor is None
checks.append('six_original_non_push_modes_never_override')
for load,cop in [(0.,None),(.1,base['cop_world']),(5.,None)]:assert not c.update(**dict(base,normal_load_n=load,cop_world=cop))['override']
checks.append('missing_or_low_measured_load_never_override')
# Real near-edge COP is not silently excluded by a new data gate.
c=CopSlipFollowing();assert c.update(**dict(base,cop_world=np.array([.5,.043,.7925])))['override'];checks.append('near_edge_contact_retained')
# A large already-existing command lead cannot be repaired by violating slew.
c=CopSlipFollowing();large=c.update(**dict(base,previous_command_xy=[.6,.1]));assert max(abs(x) for x in large['command_delta_xy'])<=.003000001 and large['retained_slew_lag_outside_lead'];checks.append('prior_large_lead_reported_without_slew_violation')
rejected=[]
for name,override in [('nonfinite_cop',dict(cop_world=[np.nan,0,0])),('bad_rotation',dict(object_rotation=np.zeros((3,3)))),('excess_step',dict(max_step_m=.01)),('negative_load',dict(normal_load_n=-1.))]:
 try:CopSlipFollowing().update(**dict(base,**override))
 except ValueError:rejected.append(name)
 else:raise AssertionError(name)
out=dict(passed=True,checks=checks,invalid_inputs_rejected=rejected,helper_sha256=hashlib.sha256((stage/'contact_slip_following.py').read_bytes()).hexdigest(),scope='Deterministic synthetic inputs verify only causal arithmetic, feedback sign, preload continuity and limits; no physical or force-response model.',training_ready=False);(stage/'SOFTWARE_CHECK.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
