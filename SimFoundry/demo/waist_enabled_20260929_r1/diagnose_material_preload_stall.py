"""Saved physical front-box failure: finite preload saturation and lost drive.
Independent quaternion arithmetic reconstructs every emitted finite-preload XY.
This diagnoses recorded commands; it does not predict a replacement controller.
"""
from pathlib import Path
import json,hashlib,datetime
from collections import Counter
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;R=W/'front_box_material_physical_r1';ep=R/'case_840020/layout_840020_push_box_to_bin';parent=W/'front_corridor_midpoint_physical_r1/case_840020/layout_840020_push_box_to_bin';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
d=json.loads((ep/'frontal_bypass.json').read_text());rows=d['rows'];quality=json.loads((ep/'quality.json').read_text());baseline=json.loads((parent/'quality.json').read_text())
with np.load(ep/'trace.npz') as z:box=z['box'].copy();other=z['mailer'].copy()
with np.load(ep/'parcel_orientation.npz') as z:quats=z['box'].copy()
assert len(box)==1200 and not quality['passed']
records=[];reference=None;phase=None;preload=0.
for r in rows:
 e=r.get('front_box_material_preload',{})
 if not e.get('override'):reference=None;phase=None;preload=0.;continue
 t=r['step'];np.testing.assert_allclose(r['observed_target'],box[t],atol=1e-8,rtol=0)
 rot=Rotation.from_quat(quats[t]).as_matrix();support=np.asarray(r['observed_support_xyz']);newphase=(r['route_stage'],r['recontacts']);fresh=reference is None or phase!=newphase
 if fresh:reference=rot.T@(support-box[t]);phase=newphase;preload=0.
 assert e['captured_reference']==fresh;np.testing.assert_allclose(reference,e['reference_local'],atol=1e-8,rtol=0)
 preload=min(.012,preload+e['drive_step_m']);assert abs(preload-e['preload_m'])<1e-12
 assert r['front_diagonal_entry']['selected']
 goal=np.array([r['route_goal_x'],r['front_diagonal_entry']['goal_y']]);delta=goal-box[t,:2];direction=delta/np.linalg.norm(delta);anchor=box[t]+rot@reference;desired=anchor[:2]+direction*min(preload,np.linalg.norm(delta));prev=np.asarray(e['previous_command_xy']);bounded=np.clip(desired,support[:2]-.030,support[:2]+.030);emitted=prev+np.clip(bounded-prev,-.003,.003)
 for actual,stored in [(anchor,e['anchor_world']),(direction,e['drive_direction_xy']),(desired,e['desired_xy']),(emitted,e['emitted_xy']),(emitted,r['target_xyz'][:2])]:np.testing.assert_allclose(actual,stored,atol=1e-8,rtol=0)
 assert r['target_xyz'][2]==e['preserved_z']
 records.append(dict(step=t,saturated=preload>=.012-1e-12,command_step_mm=float((emitted-prev)@direction*1000),parent_step_mm=float((np.asarray(e['parent_xyz'][:2])-prev)@direction*1000),lead_mm=float((emitted-support[:2])@direction*1000),normal_load_n=r['contact_load']['observed_vertical_load_n'],tilt_rad=r['observed_parcel_tilt_rad'],lead_clipped=e['desired_lead_clipped'],parent_guard=bool(r.get('route_stop_reason') or r.get('release_reason'))))
def stats(rr):
 return dict(count=len(rr),range_steps=[rr[0]['step'],rr[-1]['step']],**{k:dict(min=float(np.min([x[k] for x in rr])),median=float(np.median([x[k] for x in rr])),max=float(np.max([x[k] for x in rr]))) for k in ['command_step_mm','parent_step_mm','lead_mm','normal_load_n','tilt_rad']},lead_clipped=sum(x['lead_clipped'] for x in rr),parent_guard=sum(x['parent_guard'] for x in rr))
sat=[x for x in records if x['saturated']];late=[x for x in records if x['step']>=600];assert len(late)==600
othermax=float(np.max(np.linalg.norm(other[:,:2]-other[0,:2],axis=1)));assert othermax==0.
files=[Path(__file__),ep/'quality.json',parent/'quality.json',ep/'trace.npz',ep/'parcel_orientation.npz',ep/'frontal_bypass.json',ep/'raw.npz',W/'staged_front_box_material_preload/material_preload_v2.py',W/'staged_front_box_material_preload/front_box_material_preload_route_v2.py']
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,all1200frames_retained=True,original_quality_passed=False,target_progress_mm=quality['metrics']['target_final_progress_m']*1000,parent_same_condition_progress_mm=baseline['metrics']['target_final_progress_m']*1000,parent_original_quality_passed=baseline['passed'],non_target_max_xy_mm=othermax*1000,verified_overrides=len(records),captures=sum(r.get('front_box_material_preload',{}).get('captured_reference',False) for r in rows),phase_counts=dict(Counter(r['mode'] for r in rows)),saturated=stats(sat),late600frames=stats(late),late_box_net_xy_mm=float(np.linalg.norm(box[-1,:2]-box[600,:2])*1000),conclusion='Finite 12mm preload saturated once and settled into almost fixed commanded XY while the parent requested continued drive. Current observed load persists and no parent stop or lead clipping explains the late stall. This supports rejecting finite preload as a standalone transport controller; exact friction/IK force balance is not established here. Do not just increase its cap without addressing continued transport, tilt and load constraints.',next_action='Keep full failed run and original audits. Investigate sustained load-aware transport with controlled recontact rather than expanding this candidate or admitting its samples.',source_sha256={str(f):sha(f) for f in files},training_ready=False,model_goal_achieved=False)
with (R/'MATERIAL_PRELOAD_STALL_DIAGNOSIS.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps({k:v for k,v in out.items() if k not in ['source_sha256','scope']},indent=2))
