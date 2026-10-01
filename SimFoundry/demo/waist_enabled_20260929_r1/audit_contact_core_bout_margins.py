"""Relate measured contact-bout migration to frozen analytic collision size.

Descriptive only; no new contact/quality gate, no geometry/controller mutation.
"""
from pathlib import Path
import ast,json,hashlib,sys
import numpy as np
p=Path(sys.argv[1]).resolve();case=p.parent;source=case/'source_snapshot/simfoundry/scene_bridge/isaac_cfg.py'
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
prov=json.loads((case/'provenance.json').read_text());assert sha(source)==prov['source_sha256']['simfoundry/scene_bridge/isaac_cfg.py']
tree=ast.parse(source.read_text());node=next(n for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='core_scale' for t in n.targets));assert isinstance(node.value,ast.IfExp) and ast.unparse(node.value.test)=="obj.semantic == 'mailer'"
key='box' if 'push_box' in p.name else 'mailer';scale=np.array(ast.literal_eval(node.value.orelse if key=='box' else node.value.body));fr=json.loads((p/'frontal_bypass.json').read_text());nominal=np.array(fr['plan']['top_recontact']['contact_size_xyz']);assert nominal.shape==scale.shape==(3,);half=nominal*scale/2
old=json.loads((p/'TOP_CONTACT_BOUT_DIAGNOSIS.json').read_text());series={x['step']:x for x in old['series']};rows=[]
for bout in old['bouts']:
 loaded=[series[t] for t in range(bout['start'],bout['end']+1) if 'cop_local_xyz_m' in series[t]]
 def stats(rs):
  if not rs:return None
  margins=np.array([half[:2]-np.abs(r['cop_local_xyz_m'][:2]) for r in rs]);return dict(frames=[x['step'] for x in rs],median_local_cop_mm=(np.median([x['cop_local_xyz_m'] for x in rs],axis=0)*1000).tolist(),median_core_xy_margin_mm=(np.median(margins,axis=0)*1000).tolist(),min_observed_core_xy_margin_mm=float(np.min(margins)*1000))
 rows.append(dict(start=bout['start'],end=bout['end'],frames=bout['frames'],route_stages=bout['route_stages'],loaded_samples=len(loaded),target_delta_xy_mm=(np.array(bout['delta_target_xy_m'])*1000).tolist(),recontact_reason=bout['recontact_reason'],first5=stats(loaded[:5]),last5=stats(loaded[-5:])))
out=dict(episode=p.name,collision_half_size_mm=(half*1000).tolist(),nominal_half_size_mm=(nominal/2*1000).tolist(),rows=rows,source_sha256={str(f.relative_to(case)):sha(f) for f in [source,p/'TOP_CONTACT_BOUT_DIAGNOSIS.json',p/'frontal_bypass.json',p/'raw.npz',p/'solved_contact_forces.json']},auditor_sha256=sha(__file__),scope='Actual previous-last-substep force-weighted COP, object local coordinates. Collision dimensions read from archived generator, whose hash is bound to actual case provenance. Analytic core margin is descriptive and differs from visible shell dimensions; contact offset/penetration and all-substep patch not reconstructed. Association with later lost contact is not proof of unique cause or alternate-controller success.',training_ready=False)
(p/'CONTACT_CORE_BOUT_MARGINS.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
