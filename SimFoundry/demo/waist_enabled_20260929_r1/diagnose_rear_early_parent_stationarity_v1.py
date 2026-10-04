"""Read-only localization of the unchanged front-box parent certificate failure.
No metadata/action replacement, no relaxed gate, no admission evidence.
"""
from pathlib import Path
import sys,json,hashlib,datetime
import numpy as np
W=Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W.parents[1])]
from audit_self_clearance_task_optimality import IndependentElbows
from support_vertex_stationarity import certificate
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
ep=W/'front_box_trailing_physical_r2/case_840020/layout_840020_push_box_to_bin'
prov=json.loads((ep.parent/'provenance.json').read_text());bound={}
def archived(name):
 keys=[k for k in prov['source_sha256'] if k.endswith('/'+name)];assert len(keys)==1
 p=ep.parent/'source_snapshot'/keys[0];assert sha(p)==prov['source_sha256'][keys[0]];bound[str(p)]=sha(p);return p
geom=IndependentElbows(archived('elbow_torso_hulls.json'),archived('g1_23dof_rev_1_0_u1_black.urdf'))
coords=json.loads((ep/'coordination.json').read_text());zrows={r['step']:r for r in json.loads((ep/'front_loaded_z_priority.json').read_text())['rows']}
rows=[]
for c in coords:
 tr=c.get('self_clearance_task',{});a=c.get('task_inputs',{})
 if not tr.get('override'):continue
 q=np.array(a['current']);prev=np.array(a['previous']);x=np.array(tr['candidate_command']);J=np.array(a['jacobian']);E=np.array(a['error']);d=np.array(a['damping']);prior=np.array(a['preferred_step'])
 lo=np.maximum.reduce([np.array(a['lower']),q-np.array(a['step_limits']),prev-.055]);hi=np.minimum.reduce([np.array(a['upper']),q+np.array(a['step_limits']),prev+.055])
 gradient=J.T@(J@(x-q)-E)+d*d*(x-q-prior)
 cert=certificate(geometry=geom,x=x,gradient=gradient,lower=lo,upper=hi)
 rows.append(dict(step=c['step'],z_applied=zrows[c['step']]['applied'],solver_success=tr['solver_success'],iterations=tr['iterations'],certificate=cert))
bad=[r for r in rows if not r['certificate']['passed']];applied=[r for r in bad if r['z_applied']]
for p in [ep/'coordination.json',ep/'front_loaded_z_priority.json',ep.parent/'provenance.json',Path(__file__),W/'support_vertex_stationarity.py',W/'audit_front_loaded_z_priority_parent.py']:bound[str(p)]=sha(p)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,episode=str(ep),original_parent_checked=True,override_rows=len(rows),failed_rows=bad,z_applied_failed_rows=applied,records=rows,source_sha256=bound,quality_gate_changed=False,training_ready=False)
p=W/'rear_early_edge_preparation_r1/PARENT_STATIONARITY_DIAGNOSIS_V1.json'
with p.open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(override_rows=len(rows),bad=[dict(step=r['step'],z_applied=r['z_applied'],reason=r['certificate']['reason'],residual=r['certificate']['stationarity_residual']) for r in bad])))
