"""Verify diagnostic geometry with actual archived collision configuration."""
from pathlib import Path
import json,hashlib,ast
w=Path(__file__).resolve().parent;p=w/'REAR_CONTACT_EXIT_DIAGNOSIS.json';d=json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rows=[]
for e in d['episodes']:
 ep=w/e['run']/('case_'+e['episode'].split('_')[1])/e['episode'];prov=json.loads((ep.parent/'provenance.json').read_text());cfg=ep.parent/'source_snapshot/simfoundry/scene_bridge/isaac_cfg.py';assert sha(cfg)==prov['source_sha256']['simfoundry/scene_bridge/isaac_cfg.py'];node=next(n for n in ast.walk(ast.parse(cfg.read_text())) if isinstance(n,ast.Assign) and any(isinstance(v,ast.Name) and v.id=='core_scale' for v in n.targets));key='box' if 'push_box' in ep.name else 'mailer';scale=ast.literal_eval(node.value.orelse if key=='box' else node.value.body);plan=json.loads((ep/'frontal_bypass.json').read_text())['plan'];nominal=[.14,.09,.045] if key=='box' else [.15,.145,.04];actual=plan['region_causal_response']['actual_core']['collision_core_size_xyz'];assert max(abs(a*b-c) for a,b,c in zip(nominal,scale,actual))<1e-7
 for f,h in e['source_sha256'].items():assert sha(ep/f)==h
 rows.append(dict(run=e['run'],episode=e['episode'],archived_collision_config_sha256=sha(cfg),actual_core_matches_archive=True))
out=dict(passed=True,rows=rows,diagnosis_sha256=sha(p),checker_sha256=sha(Path(__file__)),scope='Cross-check actual core dimensions against archived collision scale and nominal parcel geometry, plus all diagnostic input hashes.',training_ready=False);q=w/'REAR_CONTACT_EXIT_SOURCE_CHECK.json';assert not q.exists();q.write_text(json.dumps(out,indent=2));print('source/core checked',len(rows))
