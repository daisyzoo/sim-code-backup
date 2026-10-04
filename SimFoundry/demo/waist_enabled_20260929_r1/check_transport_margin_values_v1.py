"""Bitwise scalar-geometry parity on saved, local perturbation and fullbounds states.
No physical feasibility inferred from synthetic states; no original gate skipped.
"""
from pathlib import Path
import sys,json,hashlib,datetime
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_effective_height_v1';D=W/'effective_height_exact_cache_probe_r1';sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from joint_transport_margin_values_v1 import pose,elbow_values,scene_margins
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text());guard=ClearanceGuard(ROOT,S);rng=np.random.default_rng(20261005);sources={};rows=[]
for case,task,step in [(840023,'nudge_mailer_to_bin',190),(840020,'push_box_to_bin',181)]:
 ep=W/f'front_loaded_z_quarter_physical_r2/case_{case}/layout_{case}_{task}';record=next(r for r in read(ep/'joint_transport_clearance.json')['rows'] if r['step']==step);ctx=record['collector_context'];scene=RecontactScene(guard,**ctx['scene']);original_record=scene.record();q=np.array(ctx['current']);points=[q,np.array(record['parent_command']),np.array(record['proposal']['command']),np.array(record['proposal']['predicted_q']),guard.lower.copy(),guard.upper.copy(),np.zeros(11)]
 points.extend(np.clip(q+rng.uniform(-.055,.055,11),guard.lower,guard.upper) for _ in range(64));points.extend(rng.uniform(guard.lower,guard.upper) for _ in range(64))
 for value in points:
  before=value.copy()
  for side in ['left','right']:np.testing.assert_array_equal(pose(guard.model,side,value),guard.model.fk(side,value)[0])
  np.testing.assert_array_equal(elbow_values(guard.geometry,value),guard.geometry.constraints(value));g=scene.details(value)
  for floor,elbow in [(.84,.005),(.8415,.0065)]:
   expected=np.r_[g['inactive_z']-floor,g['gaps']['inactive_target']-.01,g['gaps']['inactive_other']-.01,g['gaps']['active_other']-.01,guard.geometry.constraints(value)-elbow];np.testing.assert_array_equal(scene_margins(scene,value,floor,elbow),expected)
  np.testing.assert_array_equal(value,before);assert scene.record()==original_record
 rows.append(dict(episode=ep.name,step=step,states=len(points),both_hand_poses_exact=True,both_elbow_gaps_exact=True,all_six_margins_both_floors_exact=True,inputs_unchanged=True));sources[str(ep/'joint_transport_clearance.json')]=sha(ep/'joint_transport_clearance.json')
for p in [Path(__file__),W/'joint_transport_margin_values_v1.py',D/'VALUE_ONLY_DERIVATION.json',*[S/n for n in ['articulated_hand_geometry.py','self_clearance.py','recontact_scene.py']]]:sources[str(p)]=sha(p)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,rows=rows,source_sha256=sources,installed=False,physical_success=False,training_ready=False)
with (D/'SCALAR_GEOMETRY_PARITY_V1.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,states=sum(x['states'] for x in rows),installed=False)))
