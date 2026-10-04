"""Prospective source/observation binding fixtures from original ten conditions.
Not collected candidate data: image arrays/unused trace fields omitted; new
normal rows are explicit identity fixtures, not semantic runtime certificates.
No quality.json, no promotion or model training. Original artifacts untouched.
"""
from pathlib import Path
import copy,datetime,hashlib,json,shutil,sys,traceback
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_normal_nondegradation_v3';P=W/'staged_front_effective_height_v1';D=W/'front_normal_observation_binding_checks_r2';D.mkdir(exist_ok=False);sys.path[:0]=[str(W),str(ROOT)]
import front_normal_stage_source_binding_v3 as binding
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();write=lambda p,x:p.write_text(json.dumps(x,indent=2,allow_nan=False))
oldprefix=str(P.relative_to(ROOT))+'/';newprefix=str(S.relative_to(ROOT))+'/';made={};sources={};checks=[];negative=[];unexpected=[]
for item in read(W/'front_cross_track_full_stream_probe_r1/CENSUS.json')['episodes']:
 original=Path(item['episode']);origcase=original.parent;case=D/origcase.name
 if origcase.name not in made:
  case.mkdir();prov=read(origcase/'provenance.json');newsrc={}
  for name in prov['source_sha256']:
   newname=newprefix+Path(name).name if name.startswith(oldprefix) else name;newsrc[newname]=sha(ROOT/newname)
  for name in binding.NORMAL_HELPERS:newsrc[newprefix+name]=sha(S/name)
  for name,h in newsrc.items():
   dst=case/'source_snapshot'/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,dst);assert sha(dst)==h and dst.stat().st_ino!=(ROOT/name).stat().st_ino
  prov['source_sha256']=newsrc;prov['args']['front_normal_nondegradation']=True;write(case/'provenance.json',prov)
  runtime=read(origcase/'SUBSTEP_RUNTIME_BINDING.json');files={}
  for name,r in runtime['source_files'].items():
   newname=str(S/Path(name).name) if Path(name).parent==P else name;assert sha(newname)==r['sha256'];files[newname]=r
   dst=case/r['snapshot'];dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(origcase/r['snapshot'],dst)
  runtime['source_files']=files;write(case/'SUBSTEP_RUNTIME_BINDING.json',runtime);shutil.copy2(origcase/'runtime_collision_arrays.npz',case/'runtime_collision_arrays.npz')
  write(case/'DIAGNOSTIC_ONLY.json',dict(scope=__doc__,physical_collection=False,training_ready=False));made[origcase.name]=copy.deepcopy(prov)
 ep=case/original.name;ep.mkdir();wait=item['wait'];tp=read(original/'joint_transport_clearance.json')
 with np.load(original/'raw.npz',allow_pickle=False) as z:q=z['q'].copy();u=z['action'].copy();task=str(z['task_id']);meta=json.loads(str(z['collect_meta']))
 n=len(q);base_meta=copy.deepcopy(meta);normal=[dict(step=t,enabled=True,selected=r['selected'],applied=False,requires_stop=False,requires_recovery=False,parent_command=u[t,12:23].tolist(),output_command=u[t,12:23].tolist(),training_ready=False,reason='diagnostic_identity_source_fixture') for t,r in enumerate(tp['rows'])]
 coords=[] if wait else [dict(step=t,front_normal_nondegradation=normal[t]) for t in range(1,n)]
 for name in ['SUBSTEP_CONTACT_RECORDING.json','substep_contacts.npz','peak_load_updates.json']:
  shutil.copy2(original/name,ep/name);sources[str(original/name)]=sha(original/name)
 for name in ['front_initial_center.json','front_recontact_center.json']:
  x=read(original/name);x['rows']=[{k:r[k] for k in ['step','kind','front_box_recenter_version'] if k in r} for r in x['rows']];write(ep/name,x);sources[str(original/name)]=sha(original/name)
 if not wait:
  x=read(original/'frontal_bypass.json');x['rows']=[{k:r[k] for k in ['step','front_corridor_midpoint'] if k in r} for r in x['rows']];write(ep/'frontal_bypass.json',x);sources[str(original/'frontal_bypass.json')]=sha(original/'frontal_bypass.json')
 priority=read(original/'front_loaded_z_priority.json');priority['rows']=[{k:r[k] for k in ['step','applied','reduced_z_task'] if k in r} for r in priority['rows']];write(ep/'front_loaded_z_priority.json',priority)
 tp['rows']=[{k:r[k] for k in ['step','applied','training_ready','version','effective_quarter_height','output_command','collector_context']} for r in tp['rows']];write(ep/'joint_transport_clearance.json',tp)
 for enabled in [False,True]:
  prov=copy.deepcopy(made[origcase.name]);prov['args']['front_normal_nondegradation']=enabled;meta=copy.deepcopy(base_meta)
  if enabled:
   meta['front_normal_nondegradation']=binding.NORMAL_META;meta['front_normal_planning_applied_frames']=0;write(ep/'front_normal_nondegradation.json',dict(rows=normal,training_ready=False));write(ep/'coordination.json',coords)
  else:
   for name in set(binding.NORMAL_HELPERS)-{'audit_unloaded_wrist_prior_live.py'}:prov['source_sha256'].pop(newprefix+name)
  write(case/'provenance.json',prov);np.savez_compressed(ep/'raw.npz',q=q,action=u,task_id=task,collect_meta=json.dumps(meta))
  r=binding.verify_observation_binding(ep);assert r['passed'];checks.append(dict(episode=original.name,frames=n,enabled=enabled,passed=True));print(json.dumps(checks[-1]),flush=True)
 if original.name=='layout_840020_push_box_to_bin':
  for label in ['missing_normal','duplicate_normal','nan_normal','wrong_parent','wrong_frame_count','metadata_threshold','missing_coord','duplicate_coord','wrong_coord_record']:
   nr=copy.deepcopy(normal);cc=copy.deepcopy(coords);mm=copy.deepcopy(meta)
   if label=='missing_normal':nr.pop(5)
   elif label=='duplicate_normal':nr.append(copy.deepcopy(nr[5]))
   elif label=='nan_normal':nr[5]['output_command'][0]=float('nan')
   elif label=='wrong_parent':nr[5]['parent_command'][0]+=.01;cc[4]['front_normal_nondegradation']=nr[5]
   elif label=='wrong_frame_count':mm['front_normal_planning_applied_frames']=1
   elif label=='metadata_threshold':mm['front_normal_nondegradation']['stationarity_max']=1e-5
   elif label=='missing_coord':cc.pop(4)
   elif label=='duplicate_coord':cc.append(copy.deepcopy(cc[4]))
   else:cc[4]['front_normal_nondegradation']['reason']='wrong'
   (ep/'front_normal_nondegradation.json').write_text(json.dumps(dict(rows=nr,training_ready=False)));write(ep/'coordination.json',cc);np.savez_compressed(ep/'raw.npz',q=q,action=u,task_id=task,collect_meta=json.dumps(mm))
   try:binding.verify_observation_binding(ep)
   except (AssertionError,KeyError,ValueError):negative.append(label)
   else:unexpected.append(label)
  write(ep/'front_normal_nondegradation.json',dict(rows=normal,training_ready=False));write(ep/'coordination.json',coords);np.savez_compressed(ep/'raw.npz',q=q,action=u,task_id=task,collect_meta=json.dumps(meta))
 for name in ['raw.npz','joint_transport_clearance.json','front_loaded_z_priority.json']:sources[str(original/name)]=sha(original/name)
write(D/'RESULT.json',dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=not unexpected,checks=checks,negative_rejected=negative,unexpected_accepts=unexpected,source_sha256={**sources,**{str(p):sha(p) for p in [Path(__file__),W/'front_normal_stage_source_binding_v3.py']}},training_ready=False,physics_started=False))
print(json.dumps(dict(positive=len(checks),rejected=negative,unexpected_accepts=unexpected)),flush=True)
