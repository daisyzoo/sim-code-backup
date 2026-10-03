"""Construct a labelled source-contract fixture from an unchanged old wait trace.
Metadata/source paths are deliberately projected to the new stage for testing.
This is NOT a new physical rollout or admissible demonstration.
"""
from pathlib import Path
import hashlib,json,shutil,datetime,sys
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_loaded_projection';A=W/'staged_front_loaded_reference';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
checks=['FRONT_LOADED_MATERIAL_PROJECTION_CHECK.json','FRONT_LOADED_PROJECTION_STAGE_CHECK.json','FRONT_LOADED_PROJECTION_AUDIT_CHECK.json','FRONT_PROJECTION_AUDIT_DEPENDENCIES_CHECK.json'];prep=json.loads((S/'PREPARATION.json').read_text())
for n,h in prep['stage_sha256'].items():assert sha(S/n)==h
for name in checks:
 d=json.loads((W/name).read_text());assert d['passed'] is True
 for p,h in d.get('source_sha256',{}).items():assert sha(p)==h,p
assert json.loads((S/'CHECK.json').read_text())['passed']
old=W/'front_loaded_physical_r1/case_841010';dest=W/'front_projection_wait_source_fixture_r1/case_841010';assert not dest.exists();dest.mkdir(parents=True)
old_ep=old/'layout_841010_wait_no_package';ep=dest/old_ep.name;ep.mkdir()
for p in old_ep.iterdir():
 if p.is_file() and (p.suffix=='.npz' or p.name in ['SUBSTEP_CONTACT_RECORDING.json','expert_control.json','front_initial_center.json','peak_load_updates.json','quality.json','recontact_pose.json','self_clearance.json','solved_contact_forces.json','episode_contacts.json','reset_contacts.json']):shutil.copy2(p,ep/p.name)
with np.load(ep/'raw.npz') as z:arrays={k:z[k].copy() for k in z.files}
meta=json.loads(str(arrays['collect_meta']));meta.update(front_loaded_material_projection=True,front_loaded_projection_strategy='nearest_parent_in_slew_hand_material_intersection',audit_fixture_only=True,training_ready=False);arrays['collect_meta']=np.array(json.dumps(meta));np.savez_compressed(ep/'raw.npz',**arrays)
prov=json.loads((old/'provenance.json').read_text());prov['args']['front_loaded_material_projection']=True;prov['args']['out_dir']=str(dest);new_sources={}
for name,h in prov['source_sha256'].items():
 old_src=ROOT/name;assert sha(old_src)==h
 new_src=S/old_src.name if old_src.parent==A else old_src;new_name=str(new_src.relative_to(ROOT));new_sources[new_name]=sha(new_src);snapshot=dest/'source_snapshot'/new_name;snapshot.parent.mkdir(parents=True,exist_ok=True);snapshot.write_bytes(new_src.read_bytes())
for name in ['front_loaded_reference_adapter.py','front_initial_loaded_reference_cap.py','front_loaded_material_projection.py']:
 src=S/name;rel=str(src.relative_to(ROOT));new_sources[rel]=sha(src);(dest/'source_snapshot'/rel).write_bytes(src.read_bytes())
prov.update(source_sha256=new_sources,audit_fixture_only=True,training_ready=False);(dest/'provenance.json').write_text(json.dumps(prov,indent=2))
runtime=json.loads((old/'SUBSTEP_RUNTIME_BINDING.json').read_text());new_runtime={}
for name,row in runtime['source_files'].items():
 src=Path(name);new=S/src.name if src.parent==A else src;assert sha(new)==row['sha256'];new_runtime[str(new)]=row;snapshot=dest/row['snapshot'];snapshot.parent.mkdir(parents=True,exist_ok=True);snapshot.write_bytes((old/row['snapshot']).read_bytes())
runtime.update(source_files=new_runtime,audit_fixture_only=True);(dest/'SUBSTEP_RUNTIME_BINDING.json').write_text(json.dumps(runtime,indent=2));shutil.copy2(old/'runtime_collision_arrays.npz',dest/'runtime_collision_arrays.npz')
for name in ['runtime_geometry_provenance.json','runtime_configuration.json']:
 shutil.copy2(old/name,dest/name)
shutil.copytree(old/'runtime_source',dest/'runtime_source')
shutil.copy2(old_ep/'viewer_observer.json',ep/'viewer_observer.json')
fixture=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,audit_fixture_only=True,simulation_started=False,training_ready=False,original_episode=str(old_ep),original_raw_sha256=sha(old_ep/'raw.npz'),fixture_raw_sha256=sha(ep/'raw.npz'),new_stage=str(S),generator_sha256=sha(__file__))
(dest.parent/'FIXTURE_ONLY.json').write_text(json.dumps(fixture,indent=2));print('Constructed labelled wait source fixture',ep)
