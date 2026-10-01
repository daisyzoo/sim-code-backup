"""Bind current actual Newton elbow/torso shape filtering; no historical inference."""
from pathlib import Path
import json,hashlib,sys
import numpy as np
w=Path(__file__).resolve().parent;case=Path(sys.argv[1]).resolve();prov=json.loads((case/'runtime_geometry_provenance.json').read_text());source=json.loads((case/'provenance.json').read_text());hullname=next(n for n in source['source_sha256'] if n.endswith('/elbow_torso_hulls.json'));hulls=json.loads((case/'source_snapshot'/hullname).read_text());labels=prov['shape_labels'];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
with np.load(case/'runtime_collision_arrays.npz') as z:a={k:z[k].copy() for k in z.files}
assert sha(case/'runtime_collision_arrays.npz')==prov['collision_arrays_sha256'];filtered={tuple(sorted(map(int,p))) for p in a['shape_collision_filter_pairs']};contact_pairs={tuple(sorted(map(int,p))) for p in a['shape_contact_pairs']};ids={}
for side in ['left','right','torso']:
 suffix=hulls[side]['path'].split('/Geometry/',1)[1];matched=[i for i,label in enumerate(labels) if label.endswith('/Geometry/'+suffix)];assert len(matched)==1;ids[side]=matched[0]
rows=[]
for side in ['left','right']:
 elbow,torso=ids[side],ids['torso'];key=tuple(sorted([elbow,torso]));rows.append(dict(side=side,shape_indices=[elbow,torso],labels=[labels[elbow],labels[torso]],shape_flags=[int(a['shape_flags'][elbow]),int(a['shape_flags'][torso])],collision_groups=[int(a['shape_collision_group'][elbow]),int(a['shape_collision_group'][torso])],body_indices=[int(a['shape_body'][elbow]),int(a['shape_body'][torso])],explicitly_filtered=key in filtered,in_precomputed_contact_pairs=key in contact_pairs))
out=dict(scope='This current run only; exact hull-linked runtime shape indices. No reconstruction of older unarchived masks.',enabled_self_collisions=prov['enabled_self_collisions'],rows=rows,source_sha256={str(p):sha(p) for p in [Path(__file__),case/'runtime_geometry_provenance.json',case/'runtime_collision_arrays.npz',case/'provenance.json']},training_ready=False);(case/'ELBOW_COLLISION_FILTER_AUDIT.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k!='source_sha256'},indent=2))
