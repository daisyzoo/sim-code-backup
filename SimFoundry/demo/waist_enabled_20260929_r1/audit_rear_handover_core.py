"""Compare measured unloaded handover and first real COP with collision core.
Descriptive only, no optimization, contact prediction, gate or source mutation.
"""
from pathlib import Path
import json,hashlib,sys,ast
import numpy as np
from scipy.spatial.transform import Rotation
p=Path(sys.argv[1]).resolve();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();case=p.parent
source=case/'source_snapshot/simfoundry/scene_bridge/isaac_cfg.py';prov=json.loads((case/'provenance.json').read_text());assert sha(source)==prov['source_sha256']['simfoundry/scene_bridge/isaac_cfg.py']
node=next(n for n in ast.walk(ast.parse(source.read_text())) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='core_scale' for t in n.targets));assert isinstance(node.value,ast.IfExp) and ast.unparse(node.value.test)=="obj.semantic == 'mailer'"
key='box' if 'push_box' in p.name else 'mailer';side='right' if key=='box' else 'left';actor='parcel_box' if key=='box' else 'mailer';scale=np.array(ast.literal_eval(node.value.orelse if key=='box' else node.value.body));f=json.loads((p/'frontal_bypass.json').read_text());size=np.array(f['plan']['top_recontact']['contact_size_xyz']);core=size*scale/2;rows=f['rows'];by={r['step']:r for r in rows};h=next(r for r in rows if r.get('region_handover'));start=h['step'];reg=json.loads((p/'region_approach.json').read_text());solver=next(r['solver'] for r in reg['rows'] if r['step']==start);assert solver['reached'] and solver['handover']
with np.load(p/'trace.npz') as z:xyz=z[key].astype(float)
with np.load(p/'parcel_orientation.npz') as z:rot=Rotation.from_quat(z[key]).as_matrix()
packets={r['after_action_step']:r for r in json.loads((p/'solved_contact_forces.json').read_text())['rows']};t=start;local=rot[t].T@(np.asarray(h['observed_physical_support_xyz'])-xyz[t]);logged=np.asarray(solver['physical_point_local_xyz']);assert np.max(abs(local-logged))<2e-6
end=next((r['step'] for r in rows if r['step']>start and r.get('recontacts',0)>h['recontacts']),rows[-1]['step']);contacts=[]
for t in range(start,end+1):
 pack=packets.get(t-1);points=[];weights=[]
 if pack:
  assert np.max(abs(np.asarray(pack['post_action_pose'][key])-xyz[t]))<1e-6
  for c in pack['parcel_contacts']:
   slots=[i for i,s in enumerate(c['shapes']) if '/'+actor+'/' in s]
   if len(slots)!=1 or not any(side+'_wrist' in s for s in c['shapes']):continue
   force=np.asarray(c['force_world_N'])*(1 if slots[0]==1 else -1);n=-float(force@rot[t,:,2])
   if n>.05:points.append(c['position_world']);weights.append(n)
 if weights and sum(weights)>=.3:
  cop=rot[t].T@(np.average(points,axis=0,weights=weights)-xyz[t]);contacts.append(dict(step=t,mode=by[t]['mode'],load_n=sum(weights),cop_local_mm=(cop*1000).tolist(),core_xy_margin_mm=((core[:2]-abs(cop[:2]))*1000).tolist(),delta_from_handover_local_mm=((cop-local)*1000).tolist()))
assert contacts
out=dict(episode=p.name,handover_step=start,first_recontact_step=end,handover_local_mm=(local*1000).tolist(),nominal_xy_margin_mm=((size[:2]/2-abs(local[:2]))*1000).tolist(),core_xy_margin_mm=((core[:2]-abs(local[:2]))*1000).tolist(),nominal_10mm_inset_implied_core_reserve_mm=((core[:2]-(size[:2]/2-.01))*1000).tolist(),core_half_mm=(core*1000).tolist(),unloaded_vertical_gap_mm=float((local[2]-core[2])*1000),first_contact=contacts[0],first5=contacts[:5],last5=contacts[-5:],all_loaded_steps_before_first_recontact=len(contacts),source_sha256={str(f.relative_to(case)):sha(f) for f in [source,p/'frontal_bypass.json',p/'region_approach.json',p/'trace.npz',p/'parcel_orientation.npz',p/'solved_contact_forces.json']},auditor_sha256=sha(__file__),scope='Measured handover lowest support, checked against actual solver geometry, followed by previous-last-substep signed load COP in object coordinates. Different physical points across unloaded and loaded phases; geometric reserve loss is not proof of unique cause or that more interior contact is dynamically reachable. No new gate, altered source, training admission or optimized trajectory.',training_ready=False)
(p/'HANDOVER_CORE_RESERVE_AUDIT.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k not in ['source_sha256','first5','last5','scope']}))
