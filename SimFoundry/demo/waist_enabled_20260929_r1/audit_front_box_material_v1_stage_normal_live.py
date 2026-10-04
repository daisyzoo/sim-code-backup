"""File entry for original normal mathematics and explicitly verified recapture."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(w),str(repo)]
from front_box_material_v1_stage_audit_context import verified_events,verified_front_events
from audit_front_initial_center_normal import verify_normal_rows
from audit_unloaded_wrist_prior_live import HandModel
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def audit(ep):
 ep=Path(ep);events=verified_events(ep);front=verified_front_events(ep)
 with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);task=str(z['task_id'])
 coords=json.loads((ep/'coordination.json').read_text());experts={r['step']:r for r in json.loads((ep/'expert_control.json').read_text())};fr=json.loads((ep/'frontal_bypass.json').read_text());side='right' if task=='push_box_to_bin' else 'left';model=HandModel(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json')
 out=verify_normal_rows(q,coords,experts,{r['step'] for r in fr['rows']},events,model,side,verified_front_events=front)
 out.update(source_sha256={n:sha(ep/n) for n in ['front_initial_center.json','FRONT_BOX_MATERIAL_V1_STAGE_POSE_LIVE_V2_AUDIT.json','raw.npz','coordination.json','expert_control.json','frontal_bypass.json']+(['recontact_pose.json','FRONT_BOX_MATERIAL_V1_STAGE_POSE_LIVE_V2_AUDIT.json'] if events else [])},auditor_sha256=sha(Path(__file__)),training_ready=False,scope=__doc__)
 return out
if __name__=='__main__':
 ep=Path(sys.argv[1]);out=audit(ep);(ep/'FRONT_BOX_MATERIAL_V1_STAGE_NORMAL_LIVE_V2_AUDIT.json').write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k not in ['records','source_sha256']})
