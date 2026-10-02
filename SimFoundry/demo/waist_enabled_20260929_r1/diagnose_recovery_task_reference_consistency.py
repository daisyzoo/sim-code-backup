"""Quantify virtual-reference versus frozen-material Jacobian mismatch.
A small discrepancy rules out this particular task-definition explanation for
large recovery tracking losses. No solver or physical trajectory is changed.
"""
from pathlib import Path
import sys,json,hashlib,datetime
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_rear_transport_retry';sys.path[:0]=[str(S),str(ROOT),str(W)]
from clearance_runtime import ClearanceGuard
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();ep=Path(sys.argv[1]).resolve();dest=ep/'RECOVERY_TASK_REFERENCE_CONSISTENCY.json';assert not dest.exists();guard=ClearanceGuard(ROOT,S);rows=[]
for r in json.loads((ep/'rear_corridor_recovery.json').read_text())['rows']:
 if r['kind']!='loaded_recovery':continue
 c=r['parent_coordinate'];q=np.array(c['upper_q']);x=np.array(r['emitted_command']);side=c['active_side'];off=np.array(r['parent_row']['control_offset_local']);T,jl,jw=guard.model.fk(side,q);v=T[:3,:3]@off;a,b,d=v;skew=np.array([[0.,-d,b],[d,0.,-a],[-b,a,0.]]);fixed=jl-skew@jw;i=3 if side=='right' else 0;task=np.array(c['task_inputs']['jacobian'])[i:i+3];delta=(fixed-task)@(x-q);feedback=r['recovery'].get('tracking_feedback',{});bias=np.array(feedback.get('correction_xyz_m',[0.,0.,0.]));pred=np.array(r['recovery']['reference_delta_xyz_m'])+bias
 rows.append(dict(step=r['step'],jacobian_xy_max_abs=float(abs(fixed[:2]-task[:2]).max()),linear_command_difference_xyz_mm=(delta*1000).tolist(),predicted_x_mm=float(pred[0]*1000),tracking_applied=feedback.get('accepted') is True))
a=np.array([r['linear_command_difference_xyz_mm'] for r in rows]);summary=dict(recovery_commands=len(rows),maximum_xy_linear_effect_mm=float(abs(a[:,:2]).max()),median_abs_x_linear_effect_mm=float(np.median(abs(a[:,0]))),floor_tracking_commands=int(sum(r['tracking_applied'] and abs(r['predicted_x_mm']-.1)<.001 for r in rows)))
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,summary=summary,rows=rows,source_sha256={str(ep/'rear_corridor_recovery.json'):sha(ep/'rear_corridor_recovery.json')},analyzer_sha256=sha(__file__),model_source_sha256={str(S/n):sha(S/n) for n in ['clearance_runtime.py','articulated_hand_geometry.py']},training_ready=False,physics=False)
with dest.open('x') as f:json.dump(out,f,indent=2)
print(ep.name,summary)
