"""QUARANTINED synthetic binding fixtures built from archived parent observations.
New labels/current-source snapshots are deliberately constructed test inputs.
They are not new physics, demonstrations, or training data; temporary copies are
removed on exit. Checks only validation of complete source/observation metadata.
"""
from pathlib import Path
import sys,json,hashlib,tempfile,datetime,copy,shutil
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_initial_center';sys.path[:0]=[str(W),str(ROOT)]
from front_initial_center_stage_source_binding import verify_observation_binding
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
prep=json.loads((S/'PREPARATION.json').read_text());old=str((W/'staged_terminal_release_margin').relative_to(ROOT))+'/';new=str(S.relative_to(ROOT))+'/'
out=W/'FRONT_INITIAL_OBSERVATION_BINDING_CHECK.json';assert not out.exists();report=dict(status='running',scope=__doc__,positive=[],negative=[],simulation_started=False,training_ready=False,source_sha256={str(p):sha(p) for p in [Path(__file__),W/'front_initial_center_stage_source_binding.py',S/'PREPARATION.json',S/'CHECK.json']})
def save():report['updated_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();out.write_text(json.dumps(report,indent=2))
def put(p,value):p.write_text(json.dumps(value))
try:
 save()
 with tempfile.TemporaryDirectory(prefix='front-binding-SYNTHETIC-') as temp:
  for case_id,task in [(840015,'nudge_mailer_to_bin'),(840014,'push_box_to_bin'),(841007,'wait_no_package')]:
   origin=W/'terminal_margin_physical_r1'/f'case_{case_id}';src=origin/f'layout_{case_id}_{task}';case=Path(temp)/origin.name;ep=case/src.name;ep.mkdir(parents=True)
   prov=json.loads((origin/'provenance.json').read_text());sources={}
   for name in prov['source_sha256']:
    name=new+name[len(old):] if name.startswith(old) else name;sources[name]=sha(ROOT/name)
   sources.update({new+n:h for n,h in prep['stage_sha256'].items()})
   for name in sources:
    dest=case/'source_snapshot'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((ROOT/name).read_bytes())
   prov['args']['front_initial_center_landing']=True;prov.update(source_sha256=sources,fixture_only=True,physics='NONE: constructed metadata fixture');put(case/'provenance.json',prov)
   runtime=json.loads((origin/'SUBSTEP_RUNTIME_BINDING.json').read_text());bound={}
   for path,row in runtime['source_files'].items():
    path=str(S/Path(path).name) if Path(path).parent.name=='staged_terminal_release_margin' else path
    row=copy.deepcopy(row);row['sha256']=sha(path);dest=case/row['snapshot'];dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(Path(path).read_bytes());bound[path]=row
   runtime['source_files']=bound;put(case/'SUBSTEP_RUNTIME_BINDING.json',runtime)
   shutil.copyfile(origin/'runtime_collision_arrays.npz',case/'runtime_collision_arrays.npz')
   for name in ['substep_contacts.npz','SUBSTEP_CONTACT_RECORDING.json','peak_load_updates.json']:shutil.copyfile(src/name,ep/name)
   with np.load(src/'raw.npz') as z:raw={k:z[k].copy() for k in ['q','action','task_id','collect_meta']}
   meta=json.loads(str(raw['collect_meta']));meta.update(front_initial_center_landing=True,front_initial_center_failure=None,fixture_only=True)
   selected=False
   if task!='wait_no_package':
    fr=json.loads((src/'frontal_bypass.json').read_text());plan=fr['plan'];selected=bool(plan.get('front_route_selected'))
    if selected:
     declaration=dict(enabled=True,actual_core=plan['front_cop_slip_following']['edge_speed']['actual_core'],maximum_ticks=240,actual_ready_frames=3,center_xy_m=.002,precontact_height_m=[.006,.007],measured_height_m=[.004,.010],alignment_abs_min=.8,numerical_tolerance=2e-7,parameter_sha256=sha(S/'causal_response_parameters.json'),causal_preflight_only=True,no_plan_behavior='original_parent_before_any_override')
     plan['front_initial_center_landing']=declaration
    meta['frontal_bypass_plan']=copy.deepcopy(plan);put(ep/'frontal_bypass.json',fr)
   raw['collect_meta']=np.asarray(json.dumps(meta));raw['fixture_only']=np.asarray(True);np.savez_compressed(ep/'raw.npz',**raw)
   put(ep/'front_initial_center.json',dict(selected=selected,rows=[dict(step=t,kind='unchanged',fixture_only=True) for t in range(1,len(raw['q']))] if selected else [],training_ready=False))
   result=verify_observation_binding(ep);assert result['passed'];report['positive'].append(dict(parent_episode=src.name,selected_front=selected,frames=len(raw['q']),binding_passed=True,fixture_only=True));save()
   if selected:
    originals={n:(ep/n).read_bytes() for n in ['raw.npz','front_initial_center.json','SUBSTEP_CONTACT_RECORDING.json','peak_load_updates.json']};runtime_bytes=(case/'SUBSTEP_RUNTIME_BINDING.json').read_bytes()
    for label in ['recording_hash','runtime_substeps','runtime_helper_hash','raw_assist','raw_front_failure','declaration_ready_frames','missing_events','stop_event','pressure_count','recording_runtime_disagreement']:
     if label.startswith('runtime_'):
      r=copy.deepcopy(runtime)
      if label=='runtime_substeps':r['metadata']['expected_substeps']=23
      else:next(iter(r['source_files'].values()))['sha256']='0'*64
      put(case/'SUBSTEP_RUNTIME_BINDING.json',r)
     elif label.startswith('raw_') or label=='declaration_ready_frames':
      m=copy.deepcopy(meta)
      if label=='raw_assist':m['assist_frames']=1
      elif label=='raw_front_failure':m['front_initial_center_failure']='stopped'
      else:m['frontal_bypass_plan']['front_initial_center_landing']['actual_ready_frames']=2
      a=dict(raw,collect_meta=np.asarray(json.dumps(m)));np.savez_compressed(ep/'raw.npz',**a)
     elif label in ['missing_events','stop_event']:
      f=json.loads(originals['front_initial_center.json']);f['rows']=[] if label=='missing_events' else [dict(step=1,kind='stop')];put(ep/'front_initial_center.json',f)
     elif label=='pressure_count':
      f=json.loads(originals['peak_load_updates.json']);f['executed_action_count']-=1;put(ep/'peak_load_updates.json',f)
     else:
      f=json.loads(originals['SUBSTEP_CONTACT_RECORDING.json'])
      if label=='recording_hash':f['recording_sha256']='0'*64
      else:f['metadata']['control_decimation']=7
      put(ep/'SUBSTEP_CONTACT_RECORDING.json',f)
     rejected=False
     try:verify_observation_binding(ep)
     except (AssertionError,KeyError,ValueError):rejected=True
     finally:
      for n,b in originals.items():(ep/n).write_bytes(b)
      (case/'SUBSTEP_RUNTIME_BINDING.json').write_bytes(runtime_bytes)
     assert rejected,label;report['negative'].append(dict(case=label,rejected=True));save()
 report.update(status='complete',passed=True);save();print('binding',len(report['positive']),'positive',len(report['negative']),'rejections',flush=True)
except Exception as e:report.update(status='failed',error=repr(e));save();raise
