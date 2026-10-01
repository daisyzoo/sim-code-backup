"""Raw causal residual and both predicted FK responses, independent of solver logs."""
from pathlib import Path
import sys,json,hashlib,subprocess
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(w/'staged_contact_patch_approach'),str(repo)]
from articulated_hand_geometry import ArticulatedHandGeometry
p=Path(sys.argv[1]);base=subprocess.run([sys.executable,str(w/'audit_region_action_live_r2.py'),str(p)],capture_output=True,text=True);assert base.returncode==0,base.stdout+base.stderr
with np.load(p/'raw.npz') as z:q=z['q'].astype(float);u=z['action'].astype(float);task=str(z['task_id'])
with np.load(p/'trace.npz') as z:tr={k:z[k] for k in z.files}
with np.load(p/'parcel_orientation.npz') as z:ori={k:z[k] for k in z.files}
a=json.loads((p.parent/'provenance.json').read_text())['args'];assert a['region_top_approach'] and a['region_tracking_residual'] and a['role']=='diagnostic'
rows=json.loads((p/'region_approach.json').read_text())['rows'] if (p/'region_approach.json').exists() else [];side='right' if task=='push_box_to_bin' else 'left';key='box' if side=='right' else 'mailer';other='mailer' if key=='box' else 'box';size=np.array([.14,.09,.045] if side=='right' else [.15,.145,.04]);osize=(.15,.145,.04) if side=='right' else (.14,.09,.045)
model=ArticulatedHandGeometry(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json');errors=[];checked=[]
for row in rows:
 t=row['step'];res=q[t,12:23]-u[t-1,12:23]
 if np.max(abs(res-row['current_tracking_residual_rad']))>2e-6:errors.append(f'{t}:not actual causal residual')
 s=row['solver']
 if not s or not s.get('joint_override'):continue
 cmd=np.asarray(s['next_q'])
 if np.max(abs(cmd-u[t-1,12:23]))>.055002:errors.append(f'{t}:global command slew prebound')
 if np.max(abs(cmd-u[t,12:23]))>2e-6:errors.append(f'{t}:post-solver action changed')
 if s.get('handover'):continue
 if np.max(abs(res-s['causal_tracking_residual_rad']))>2e-6:errors.append(f'{t}:solver used wrong residual')
 checks=[]
 for name,shift in [('nominal',np.zeros(11)),('residual',res)]:
  g=model.scene_geometry(side,cmd+shift,target_xyz=tr[key][t],target_quat=ori[key][t],other_xyz=tr[other][t],other_quat=ori[other][t],other_size=osize);world=g['vertices']@g['hand_rotation'].T+g['hand_xyz'];local=(world-g['target_xyz'])@g['target_rotation'];index=int(local[:,2].argmin());point=local[index];safe=bool(np.all(abs(point[:2])<=size[:2]/2-.01+2e-6) and point[2]>=size[2]/2+.003-2e-6 and g['hand_other_gap_m']>=.005-2e-6 and world[:,2].min()>=.746-2e-6)
  if not safe:errors.append(f'{t}:{name} raw FK forecast violates recorded guard')
  checks.append(dict(response=name,physical_point_local_xyz=point.tolist(),min_hand_z_m=float(world[:,2].min()),other_gap_m=g['hand_other_gap_m'],sampled_geometric_guards_passed=safe))
 checked.append(dict(step=t,residual=res.tolist(),responses=checks))
out=dict(passed=not errors,errors=errors,region_log_rows=len(rows),forecast_steps_checked=len(checked),checks=checked,raw_sha256=hashlib.sha256((p/'raw.npz').read_bytes()).hexdigest(),base_audit_sha256=hashlib.sha256((p/'REGION_ACTION_LIVE_AUDIT_R2.json').read_bytes()).hexdigest(),auditor_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Actual raw q/action causal residual, unchanged global slew, independent URDF evaluation of nominal and residual command response. These two hypothetical responses are not a guarantee about real dynamics; original quality/pose/visual and full swap gates remain separate.',training_ready=False)
(p/'TRACKING_REGION_ACTION_AUDIT.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k!='checks'},indent=2));sys.exit(0 if out['passed'] else 1)
