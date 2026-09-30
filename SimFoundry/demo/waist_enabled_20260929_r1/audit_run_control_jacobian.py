"""Compare recorded world point Jacobians with independent URDF central differences."""
from pathlib import Path
import sys
root=Path(__file__).resolve().parent
source=(root/'audit_terminal_reach.py').read_text()
exec(compile(source.split('results=[];rng')[0],'<validated_cached_fk_setup>','exec'))
run=Path(sys.argv[1]).resolve()
def point(side,q,offset):
 m=np.eye(4);m[:3,3]=[.08,0,.793]
 for name,orig,axis in chains[side]:
  m=m@orig
  if axis is not None:r=np.eye(4);r[:3,:3]=Rotation.from_rotvec(axis*q.get(name,0)).as_matrix();m=m@r
 return m[:3,:3]@offset+m[:3,3]
rows=[]
for ep in sorted(run.glob('case_*/layout_*')):
 log=json.loads((ep/'coordination.json').read_text());samples=[]
 for row in log:
  if 'control_jacobian_world' not in row:continue
  q=np.array(row['upper_q']);actual=np.array(row['control_jacobian_world']);off=row['active_point_offset_local']
  def forward(q):
   d=dict(zip(names,q));return np.concatenate([point(side,d,off if side==row['active_side'] and off is not None else [.20,0,.007]) for side in ['left','right']])
  eps=1e-5;fd=np.column_stack([(forward(q+np.eye(11)[i]*eps)-forward(q-np.eye(11)[i]*eps))/(2*eps) for i in range(11)])
  samples.append(dict(step=row['step'],max_abs_error_m_per_rad=float(np.max(abs(fd-actual))),per_column_max_error=np.max(abs(fd-actual),axis=0).tolist()))
 if not samples:raise ValueError('No Jacobian samples')
 rows.append(dict(episode=ep.name,samples=samples,max_error_m_per_rad=max(s['max_abs_error_m_per_rad'] for s in samples)))
report=dict(rows=rows,passed=all(r['max_error_m_per_rad']<1e-5 for r in rows),scope='Read-only sampled analytic world point Jacobian versus central difference of independent validated URDF FK. Does not prove dynamics, collision avoidance or controller optimality.',training_ready=False)
(run/'CONTROL_JACOBIAN_AUDIT.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
