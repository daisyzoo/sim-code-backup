"""Complete-file synthetic admission integration, never physical training data.

No validator/loader/auditor mocks. Synthetic RGB/trajectories are deleted with
TemporaryDirectory; an approved fixture marker is NOT an actual image review.
"""
from pathlib import Path
import sys,json,hashlib,importlib.util,tempfile,copy,shutil
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_trial_collection';sys.path.insert(0,str(repo));sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
for name in ['waist_trial_collection','waist_pilot_protocol']:
 spec=importlib.util.spec_from_file_location('simfoundry.data.'+name,stage/(name+'.py'));mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod)
from simfoundry.data.waist_pilot_protocol import REQUIRED_SOURCES,GATES,semantic_settings
from simfoundry.data.waist_trial_collection import EXTRA_SOURCES
from simfoundry.data.schema import TrajectoryEpisode,save_episode,load_episode
from simfoundry.data.prompts import PAIRED_SORTING_PROMPTS
spec=importlib.util.spec_from_file_location('actual_converter',repo/'scripts/prepare_paired_sorting_lerobot.py');converter=importlib.util.module_from_spec(spec);spec.loader.exec_module(converter)
production_before={str(p):sha(p) for p in [repo/'scripts/collect_paired_sorting.py',repo/'simfoundry/data/waist_pilot_protocol.py',repo/'scripts/prepare_paired_sorting_lerobot.py']}
settings=semantic_settings(json.loads((w/'y_path_nearhalf_groups_r1/case_897002/provenance.json').read_text())['args']);settings.update(steps=120,wait_steps=50,expert_top_contact_bout_yaw_hold=False)
catalog=w/'fresh_pilot_layout_proposal_r1/PROPOSAL.json';failures=[]
with tempfile.TemporaryDirectory(prefix='SYNTHETIC-trial-admission-NOT-TRAINING-') as tmp:
 base=Path(tmp);roots=[]
 for group in ['fresh_lateral_00','fresh_lateral_08']:
  root=base/group;root.mkdir();roots.append(root);planpath=catalog.parent/(group+'.json');plan=json.loads(planpath.read_text());hashes={}
  for rel in REQUIRED_SOURCES|EXTRA_SOURCES|{'scripts/collect_paired_sorting.py'}:
   src=stage/Path(rel).name if Path(rel).name in ['waist_trial_collection.py','waist_pilot_protocol.py','collect_paired_sorting.py'] else repo/rel
   dst=root/'source_snapshot'/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);hashes[rel]=sha(dst)
  c=dict(version=2,motion_protocol='waist_yaw_enabled_v1',approved_for_pilot=True,admission_kind='frozen_trial_collection',collection_admission_only=True,training_ready=False,feasibility=[],gates=GATES,collector_settings=settings,prelaunch_collector_settings=settings,pilot_collector_sha256=hashes['scripts/collect_paired_sorting.py'],controller_source_sha256={k:v for k,v in hashes.items() if k!='scripts/collect_paired_sorting.py'},layouts=plan['layouts'],wait_layouts=plan['wait_layouts'],trial_plan=dict(catalog_path=str(catalog),catalog_sha256=sha(catalog),group_plan_path=str(planpath),group_plan_sha256=sha(planpath)))
  contract=root/'waist_pilot_contract.json';contract.write_text(json.dumps(c));digest=sha(contract)
  (root/'provenance.json').write_text(json.dumps(dict(args=dict(settings,role='pilot',layouts=2,wait_episodes=1),source_sha256=hashes)))
  (root/'STATUS.json').write_text(json.dumps(dict(status='numeric_pass_visual_review_pending',SYNTHETIC_TEST_ONLY=True)))
  for layout in plan['layouts']+plan['wait_layouts']:
   tasks=list(PAIRED_SORTING_PROMPTS)[:2] if layout in plan['layouts'] else ['wait_no_package']
   assert set(tasks)==({'push_box_to_bin','nudge_mailer_to_bin'} if layout in plan['layouts'] else {'wait_no_package'})
   for task in tasks:
    wait=task=='wait_no_package';n=50 if wait else 120;ep=root/f"layout_{layout['layout_id']}_{task}";ep.mkdir();trace={};orient={}
    for obj in ['box','mailer']:
     trace[obj]=np.tile(layout[obj+'_xyz'],(n,1));quat=Rotation.from_euler('z',layout[obj+'_yaw']).as_quat();orient[obj]=np.tile(quat,(n,1))
    trace['palm_left']=np.tile([.1,.6,.90],(n,1));trace['palm_right']=np.tile([.1,-.6,.90],(n,1))
    if wait:
     trace['box'][:]=[15.,15.,.77];trace['mailer'][:]=[16.,16.,.77]
    else:
     target='box' if task=='push_box_to_bin' else 'mailer';hand='right' if target=='box' else 'left';direction=-1 if target=='box' else 1;start=trace[target][0,1];goal=direction*max(.24,direction*start+.17)
     trace[target][:,1]=np.r_[np.linspace(start,goal,n-20),np.full(20,goal)]
     trace['palm_'+hand]=trace[target].copy();trace['palm_'+hand][:,2]+=.08
    meta=dict(SYNTHETIC_TEST_ONLY=True,collection_role='pilot',motion_protocol='waist_yaw_enabled_v1',assist_frames=0,push_assist=False,idle_diagnostic=False,wait_force_n=0,push_force_n=0,collision_pipeline='newton',layout_id=layout['layout_id'],layout=layout,waist_pilot_contract_sha256=digest,waist_limit_rad=settings['waist_limit_rad'],waist_wait_tolerance_rad=settings['waist_wait_tolerance_rad'],environment_seed=settings['environment_seed'],box_xyz=layout['box_xyz'],mailer_xyz=layout['mailer_xyz'],box_quat_xyzw=orient['box'][0].tolist(),mailer_quat_xyzw=orient['mailer'][0].tolist())
    raw=TrajectoryEpisode(rgb=np.full((n,3,480,640),120,dtype=np.uint8),q=np.zeros((n,23),np.float32),action=np.zeros((n,23),np.float32),instruction=PAIRED_SORTING_PROMPTS[task],scene_id='SYNTHETIC_TEST_ONLY',task_id=task,collect_meta=meta)
    save_episode(raw,ep/'raw.npz');np.savez_compressed(ep/'trace.npz',**trace);np.savez_compressed(ep/'parcel_orientation.npz',**orient)
    (ep/'quality.json').write_text(json.dumps(dict(passed=True,motion_protocol='waist_yaw_enabled_v1',SYNTHETIC_TEST_ONLY=True)))
  def review_for(rt):return dict(approved=True,method='SYNTHETIC automated software fixture; NOT actual image review or physical evidence',episodes={str(p.relative_to(rt)):sha(p) for p in rt.glob('layout_*/raw.npz')})
  (root/'review.json').write_text(json.dumps(review_for(root)))
 records=converter.checked_sources(roots);assert len(records)==10
 vals={r['layout_id'] for r in records if r['planned_split']=='validation'};split=converter.make_split(records,vals);assert len(split['train'])==len(split['validation'])==5
 print('full ten-file loader/audit/contract/pose/pair/split positive passed',flush=True)
 root=roots[0];ep=root/'layout_840000_push_box_to_bin';rawpath=ep/'raw.npz'
 # Restore all bytes after each independent mutation. Exclude source tree unless altered.
 baseline={p:p.read_bytes() for p in root.rglob('*') if p.is_file()}
 def reject(label,mutate,expected):
  mutate()
  try:converter.checked_sources(roots)
  except (ValueError,FileNotFoundError) as e:
   assert expected in str(e),(label,str(e));failures.append(dict(case=label,error=str(e).replace(str(base),'<fixture>')));print('rejected',label,flush=True)
  else:raise AssertionError('accepted '+label)
  finally:
   for p,b in baseline.items():p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
 def edit_json(p,fn):
  j=json.loads(p.read_text());fn(j);p.write_text(json.dumps(j))
 def edit_raw(fn,rehash=True):
  obj=load_episode(rawpath);fn(obj);save_episode(obj,rawpath)
  if rehash:(root/'review.json').write_text(json.dumps(review_for(root)))
 def edit_npz(p,fn):
  with np.load(p) as z:data={k:z[k].copy() for k in z.files}
  fn(data);np.savez_compressed(p,**data)
 reject('no_visual_review',lambda:(root/'review.json').unlink(),'review.json')
 reject('review_not_approved',lambda:edit_json(root/'review.json',lambda j:j.update(approved=False)),'explicit visual review')
 reject('raw_review_hash_changed',lambda:edit_raw(lambda e:e.q.__setitem__((3,13),.001),False),'not bound to the visual review')
 reject('diagnostic_cannot_promote',lambda:edit_raw(lambda e:e.collect_meta.update(collection_role='diagnostic')),'diagnostic or assisted')
 reject('failed_saved_quality',lambda:edit_json(ep/'quality.json',lambda j:j.update(passed=False)),'failed original task/waist/pose gates')
 reject('first_state_not_zero',lambda:edit_raw(lambda e:e.q.__setitem__((0,13),.01)),'failed original task/waist/pose gates')
 reject('first_action_not_zero',lambda:edit_raw(lambda e:e.action.__setitem__((0,13),.01)),'failed original task/waist/pose gates')
 reject('non_target_20mm_excursion',lambda:edit_npz(ep/'trace.npz',lambda d:d['mailer'].__setitem__((60,1),d['mailer'][0,1]+.02)),'failed original task/waist/pose gates')
 reject('failed_target_task',lambda:edit_npz(ep/'trace.npz',lambda d:d['box'].__setitem__((slice(None),1),d['box'][0,1])),'failed original task/waist/pose gates')
 reject('tilt_0p21_rad',lambda:edit_npz(ep/'parcel_orientation.npz',lambda d:d['box'].__setitem__(60,Rotation.from_euler('x',.21).as_quat())),'failed original task/waist/pose gates')
 wait=root/'layout_841000_wait_no_package'
 reject('wait_palm_20mm_drift',lambda:edit_npz(wait/'trace.npz',lambda d:d['palm_left'].__setitem__((30,1),.62)),'failed original task/waist/pose gates')
 reject('source_archive_byte_tamper',lambda:(root/'source_snapshot/simfoundry/data/waist_trial_collection.py').write_text('tampered'),'source snapshot differs')
 reject('test_split_metadata',lambda:edit_raw(lambda e:e.collect_meta['layout'].update(planned_split='test')),'preassigned test geometry')
 reject('wrong_instruction',lambda:edit_raw(lambda e:setattr(e,'instruction','wrong')),'Task instruction mismatch')
 reject('paired_initial_rgb_mismatch',lambda:edit_raw(lambda e:e.rgb.__setitem__(0,150)),'paired first RGB')
 def remove_swap():
  for p in root.glob('layout_840001_*/raw.npz'):p.unlink()
  edit_json(root/'provenance.json',lambda j:j['args'].update(layouts=1));(root/'review.json').write_text(json.dumps(review_for(root)))
 reject('missing_swap_even_with_adjusted_counts',remove_swap,'waist contract episode coverage')
 def remove_wait():
  (wait/'raw.npz').unlink();edit_json(root/'provenance.json',lambda j:j['args'].update(wait_episodes=0));(root/'review.json').write_text(json.dumps(review_for(root)))
 reject('missing_wait_even_with_adjusted_counts',remove_wait,'waist contract episode coverage')
 for label,validation in [('split_swap_leak',vals|{840000}),('override_registered_split',{840000,840001,841000})]:
  try:converter.make_split(records,validation)
  except ValueError as e:
   assert ('requested split differs' in str(e)) if label=='override_registered_split' else ('leaked across' in str(e))
   failures.append(dict(case=label,error=str(e)));print('rejected',label,flush=True)
  else:raise AssertionError(label)
 assert len(converter.checked_sources(roots))==10
for p,h in production_before.items():assert sha(p)==h
report=dict(passed=True,positive_episodes=10,positive_groups=2,train_episodes=5,validation_episodes=5,negative_cases=failures,production_sources_unchanged=True,scope='Actual file loaders, v2 contract/source validation, original numeric/pose/pair audits, converter.checked_sources and make_split. No function mocks. All trajectories/RGB and review approvals are conspicuous synthetic fixtures in deleted temporary storage; NOT real demonstrations, actual visual reviews, physics, LeRobot export or model training proof. Production sources unchanged.',training_ready=False)
(stage/'DATA_ADMISSION_CHECK.json').write_text(json.dumps(report,indent=2));print('PASS',len(failures),flush=True)
