"""Exact linear tangent-cone diagnosis at two recorded unexecuted stops.
Freeze instantaneous object pose and restrict reference movement to its top
plane. Inward constraints on threatened local axes plus forward-only movement
can forbid tangent progress. This is not full robot/global task infeasibility:
object motion, surface tilt/normal movement and later phase changes are omitted.
"""
from pathlib import Path
import json,hashlib,datetime
import numpy as np
from scipy.optimize import linprog
w=Path(__file__).resolve().parent;records=[];sources={};sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
for cid,task,direction in [(840001,'push_box_to_bin',-1),(840004,'nudge_mailer_to_bin',1)]:
 ep=w/'loaded_edge_coverage_groups_r1'/f'case_{cid}'/f'layout_{cid}_{task}';p=ep/'loaded_edge_coverage.json';d=json.loads(p.read_text());tr=d['rows'][-1];assert tr['accepted'] is False and d['failure']['step']==tr['step'];R=np.array(tr['context']['object_rotation']);cop=np.array(tr['context']['current_cop_local']);axes=tr['threatened_axes'];assert axes==[0,1]
 # z_local=0 exactly. Forward signed worldY is a linear form in localXY.
 forward=direction*R[1,:2];inward=np.array([-np.sign(cop[k])*np.eye(2)[k] for k in axes]);A=np.vstack([inward,forward]);fit=linprog(-forward,A_ub=-A,b_ub=np.zeros(len(A)),bounds=[(-.01,.01)]*2,method='highs');assert fit.success
 maximum=float(forward@fit.x);inward_coefficients=forward*np.array([-np.sign(cop[k]) for k in axes]);certificate=bool(np.all(inward_coefficients<=0))
 # Exact no-positive-tangent certificate: every inward basis has nonpositive
 # forward component. Coupled with forward>=0, maximum is zero.
 if certificate:assert abs(maximum)<1e-12
 q=np.array(json.loads((ep/'coordination.json').read_text())[-1]['upper_q']);arm='right' if direction==-1 else 'left'
 records.append(dict(episode=ep.name,step=tr['step'],axes=axes,cop_local_m=cop.tolist(),signed_world_forward_components_in_localXY=forward.tolist(),signed_forward_of_each_unit_inward_axis=inward_coefficients.tolist(),no_positive_tangent_progress_certificate=certificate,localXY_bound_m=.01,max_signed_forward_m=maximum,maximizing_local_delta_xy_m=fit.x.tolist(),world_delta_m=(R[:,:2]@fit.x).tolist(),normal_world_forward_coefficient=float(direction*R[1,2]),parent_nominal_inward_and_forward_m=tr['parent_check']['nominal_inward_and_forward_m'],original_attempt_nominal_directions=[dict(seed=a['seed'],directions=a['final']['nominal_inward_and_forward_m']) for a in tr['attempts']]))
 sources[str(p)]=sha(p);sources[str(ep/'coordination.json')]=sha(ep/'coordination.json')
sources[str(Path(__file__))]=sha(__file__);out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,records=records,source_sha256=sources,physical_validation=False,training_ready=False)
(w/'LOADED_EDGE_TANGENT_CONE_DIAGNOSIS.json').write_text(json.dumps(out,indent=2))
for r in records:print(r['episode'],'no-positive-tangent',r['no_positive_tangent_progress_certificate'],'maxforward_mm_per10mm_axis',r['max_signed_forward_m']*1000,'inward-basis-forward',r['signed_forward_of_each_unit_inward_axis'])
