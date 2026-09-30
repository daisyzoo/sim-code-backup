"""Recorded clipped-hand vertices against fixed table top, sampled geometric audit."""
from pathlib import Path
import sys,re,ast
root=Path(__file__).resolve().parent
source=(root/'audit_terminal_reach.py').read_text()
exec(compile(source.split('results=[];rng')[0],'<validated_cached_fk_setup>','exec'))
asset=root.parents[1]/'assets/robots/g1_23dof_u1_rubber/g1_23dof_rev_1_0_u1_black/payloads/hand_collision.usda'
arrays=re.findall(r'point3f\[\] points = (\[.*?\])',asset.read_text());meshes={side:np.unique(np.array(ast.literal_eval(a)),axis=0) for side,a in zip(['left','right'],arrays)}
run=Path(sys.argv[1]);rows=[]
for ep in sorted(run.glob('case_*/layout_*')):
 z=np.load(ep/'raw.npz');hands={}
 for side in ['left','right']:
  depths=[];counts=[]
  for q in z['q'][:,12:23]:
   d=dict(zip(names,q));m=np.eye(4);m[:3,3]=[.08,0,.793]
   for name,orig,axis in chains[side]:
    m=m@orig
    if axis is not None:r=np.eye(4);r[:3,:3]=Rotation.from_rotvec(axis*d.get(name,0)).as_matrix();m=m@r
   world=meshes[side]@m[:3,:3].T+m[:3,3];inside=(world[:,0]>=.28)&(world[:,0]<=.88)&(abs(world[:,1])<=.74);v=world[inside];top=np.where(v[:,0]<=.292,.753,.750);dep=np.maximum(top-v[:,2],0);depths.append(float(dep.max()) if len(dep) else 0.);counts.append(int((dep>.001).sum()))
  hands[side]=dict(max_vertex_below_table_m=max(depths),worst_frame=int(np.argmax(depths)),frames_over_1mm=sum(d>.001 for d in depths),max_vertices_over_1mm=max(counts))
 rows.append(dict(episode=ep.name,hands=hands));print(ep.name,hands,flush=True)
(run/'HAND_TABLE_GEOMETRY_AUDIT.json').write_text(json.dumps(dict(rows=rows,scope='Actual pre-action joint FK and exact clipped-hand USD vertices; tabletop rectangleX[.28,.88],Y[-.74,.74],Z.750 with frontX<=.292 stripZ.753. Vertex-inside-footprint check, no faces/forearm/all-substep or actual engine collision-margin certification. Does not replace original quality gates.',training_ready=False),indent=2))
