from pathlib import Path
root=Path(__file__).resolve().parent
source=(root/'audit_terminal_reach.py').read_text()
exec(compile(source.split('results=[];rng')[0],'<validated_cached_fk_setup>','exec'))
import sys
sys.path.insert(0,str(root.parents[1]))
from simfoundry.data.fingertip_bypass import distal_mesh_vertex
rows=[]
for ep in (root/'frontal_tip_side_smoke_r1/case_62000').glob('layout_*'):
 side='right' if 'push_box' in ep.name else 'left';z=np.load(ep/'raw.npz');log=json.loads((ep/'frontal_bypass.json').read_text());errs=[]
 for row in log['rows']:
  q=dict(zip(names,z['q'][row['step'],12:23]));m=np.eye(4);m[:3,3]=[.08,0,.793]
  for name,orig,axis in chains[side]:
   m=m@orig
   if axis is not None:rot=np.eye(4);rot[:3,:3]=Rotation.from_rotvec(axis*q.get(name,0)).as_matrix();m=m@rot
  expected=m[:3,:3]@distal_mesh_vertex(side)+m[:3,3];errs.append(float(np.max(np.abs(expected-row['observed_tip_xyz']))))
 rows.append(dict(episode=ep.name,frames=len(errs),max_tip_fk_error_m=max(errs),zero_first_state=bool(np.max(np.abs(z['q'][0,12:23]))<1e-4),zero_first_action=bool(np.max(np.abs(z['action'][0,12:23]))<1e-4)))
report=dict(rows=rows,scope='Actual recorded world mesh-point vs independent URDF FK at every pre-action frame; coordinate check only, not force/clearance/quality proof.',training_ready=False);(root/'TIP_MAPPING_AUDIT.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
