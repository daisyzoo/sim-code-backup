"""Complete source-contract fixture with enabled window on parent front-box data.
All physical arrays/commands are independent unchanged copies. Added window logs
are reconstructed test inputs, NOT measurements of a new physical candidate.
"""
from pathlib import Path
import sys,json,hashlib,datetime,tempfile,shutil,copy
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ROOT=W.parents[1];D=W/'front_contact_window_preparation_r2';S=W/'staged_front_contact_window_v2';sys.path[:0]=[str(S),str(W),str(ROOT)]
from front_contact_window_stage_source_binding_v2 import verify_preparation,verify_observation_binding,WINDOW_PLAN
from front_contact_window_observation_audit_v1 import force_interval,expected_evidence
from audit_front_window_stream_v2 import inspect
from audit_front_window_r1_v2_execution import inspect as inspect_parent
from front_window_command_ledger_v2 import load_transport_ledger
from audit_front_contact_window_stream_v1 import inspect as inspect_window
from clearance_runtime import ClearanceGuard
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text());expected,bound=verify_preparation();assert len(expected)==98
original=W/'front_loaded_z_quarter_physical_r2/case_840020';name='layout_840020_push_box_to_bin';oldstage=W/'staged_front_loaded_z_quarter_v1';files=['raw.npz','frontal_bypass.json','coordination.json','joint_transport_clearance.json','expert_control.json'];before={n:sha(original/name/n) for n in files};negative=[]
def reject(label,call):
 try:call()
 except (AssertionError,ValueError,KeyError):negative.append(label)
 else:raise AssertionError('Accepted fixture '+label)
with tempfile.TemporaryDirectory(prefix='window-front-enabled-independent-copy-') as tmp:
 case=Path(tmp)/original.name
 def ignored(directory,names):
  if Path(directory)==original:return [n for n in names if n.startswith('viewer_') or (n.startswith('layout_') and n!=name)]
  return []
 shutil.copytree(original,case,copy_function=shutil.copy2,ignore=ignored);ep=case/name
 for p in case.rglob('*'):
  if p.is_file():assert not p.is_symlink() and p.stat().st_ino!=(original/p.relative_to(case)).stat().st_ino
 prefix=str(S.relative_to(ROOT))+'/';oldprefix=str(oldstage.relative_to(ROOT))+'/'
 p=case/'provenance.json';prov=read(p);prov['args']['front_contact_window']=True;assert prov['args']['front_loaded_z_quarter'] is True;prov['source_sha256']={k:v for k,v in prov['source_sha256'].items() if not k.startswith(oldprefix)}
 for n,h in expected.items():
  dest=case/'source_snapshot'/prefix/n;assert not dest.exists();dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(S/n,dest);assert dest.stat().st_ino!=(S/n).stat().st_ino;prov['source_sha256'][prefix+n]=h
 p.write_text(json.dumps(prov));p=case/'SUBSTEP_RUNTIME_BINDING.json';r=read(p);r['source_files']={str(S/Path(k).name) if Path(k).parent==oldstage else k:v for k,v in r['source_files'].items()};p.write_text(json.dumps(r));(case/'SOURCE_CONTRACT_FIXTURE.json').write_text(json.dumps(dict(fixture_only=True,physical_candidate=False,window_enabled=True)))
 with np.load(ep/'raw.npz',allow_pickle=False) as z:raw={k:z[k].copy() for k in z.files}
 with np.load(ep/'trace.npz',allow_pickle=False) as z:xyz=z['box'].copy()
 with np.load(ep/'parcel_orientation.npz',allow_pickle=False) as z:quat=z['box'].copy()
 with np.load(ep/'substep_contacts.npz',allow_pickle=False) as z:sub={k:z[k].copy() for k in z.files}
 fr=read(ep/'frontal_bypass.json');core=fr['plan']['front_cop_slip_following']['edge_speed']['actual_core_size_xyz'];meta=json.loads(str(raw['collect_meta']));n=len(raw['q']);assert n==1200
 history_report=read(D/'FULL_PARENT_LOSS_LIFECYCLE_CHECK_V2.json');history={r['step']:r for e in history_report['episodes'] if e['episode']==str((original/name).relative_to(W)) for r in e['records']};assert len(history)==n-1
 mesh=read(ROOT/'assets/robots/g1_hand_support_vertices.json');guard=ClearanceGuard(ROOT,S);verts=np.array(mesh['vertices']['right']);record=read(ep/'SUBSTEP_CONTACT_RECORDING.json');packets=read(ep/'solved_contact_forces.json')['rows'];logs=[]
 for row in fr['rows']:
  t=row['step'];T,_,_=guard.model.fk('right',raw['q'][t,12:23]);rh=T[:3,:3];rt=Rotation.from_quat(quat[t]).as_matrix();vertex=verts[np.argmin(verts@(rh.T@rt[:,2]))];physical=T[:3,3]+rh@vertex;local=rt.T@(physical-xyz[t]);margin=float(min(np.array(core)[:2]/2-abs(local[:2])));h=history[t];virtual=T[:3,3]+rh@np.array(row['observed_support_offset_local']);values,current=force_interval(sub,record['metadata'],packets[t-1],t,'right','parcel_box')
  geometry=dict(target_xyz=xyz[t].tolist(),target_quat_xyzw=quat[t].tolist(),actual_core_xyz=core,measured_hand_xyz=T[:3,3].tolist(),measured_hand_quat_xyzw=Rotation.from_matrix(rh).as_quat().tolist(),physical_support_local=vertex.tolist(),physical_support_xyz=physical.tolist(),support_local_xyz=local.tolist(),current_support_core_margin_m=margin,virtual_control_reference_xyz=virtual.tolist())
  interval=dict(action_step=t,observed_phase=h['observed_phase'],final_phase=h['native_final_phase'],output_mode=h['native_output_mode'],geometry=geometry,evidence=expected_evidence(t,values,current,margin) if h['loss_invoked'] else None,disposition='loss_counter_evaluated' if h['loss_invoked'] else 'original_guard_or_nonpush_no_loss_update',training_ready=False)
  row['contact_window_interval']=interval;logs.append(dict(step=t,**interval))
 fr['plan']['front_contact_window']=copy.deepcopy(WINDOW_PLAN);meta['frontal_bypass_plan']['front_contact_window']=copy.deepcopy(WINDOW_PLAN);meta['front_contact_window']=dict(version='front_window_native_v4',enabled=True,selected_front=True,recorded_intervals=n-1,training_ready=False);raw['collect_meta']=np.array(json.dumps(meta));np.savez_compressed(ep/'raw.npz',**raw);(ep/'frontal_bypass.json').write_text(json.dumps(fr));(ep/'front_contact_window.json').write_text(json.dumps(dict(version='front_window_native_v4',enabled=True,selected_front=True,rows=logs,executed_frames=n,training_ready=False)))
 with np.load(original/name/'raw.npz',allow_pickle=False) as z:
  for k,v in raw.items():
   if k!='collect_meta':np.testing.assert_array_equal(z[k],v)
 baseline=read(original/name/'frontal_bypass.json');stripped=copy.deepcopy(fr);stripped['plan'].pop('front_contact_window')
 for row in stripped['rows']:row.pop('contact_window_interval')
 assert stripped==baseline
 binding=verify_observation_binding(ep);assert binding['passed'];print('SOURCE_BINDING_PASS',flush=True)
 result=inspect(ep,fixture_only=True);assert result['passed'] and result['frames']==1200 and not result['physical_candidate_verified'];(ep/'FRONT_WINDOW_PARENT_STREAM_V2_AUDIT.json').write_text(json.dumps(result));print('FULL_TRANSPORT_STREAM_PASS',flush=True)
 parents,ledger=load_transport_ledger(ep,allow_source_fixture=True);assert ledger['passed'] and ledger['fixture_only'];np.testing.assert_array_equal(parents,np.asarray([r['output_command'] for r in read(ep/'front_loaded_z_priority.json')['rows']],dtype=np.float32));print('PARENT_LEDGER_PASS',flush=True)
 execution=inspect_parent(ep,allow_source_fixture=True);assert execution['passed'] and execution['fixture_only'] and not execution['physical_execution_evidence'];print('PARENT_EXECUTION_PASS',flush=True)
 window=inspect_window(ep);assert window['passed'] and window['enabled'] and window['selected_front'] and window['intervals']==1199 and window['additional_loss_observations']==0 and not window['task_success_proven'];print('FULL_WINDOW_STREAM_PASS',flush=True)
 reject('physical_stream',lambda:inspect(ep));reject('physical_parent',lambda:inspect_parent(ep));reject('physical_ledger',lambda:load_transport_ledger(ep))
 for k in ['coordination.json','joint_transport_clearance.json','expert_control.json']:assert sha(ep/k)==before[k]
for n,h in before.items():assert sha(original/name/n)==h
paths=[Path(__file__),W/'audit_front_contact_window_stream_v1.py',D/'AUDIT_FAMILY_PREPARATION.json',D/'AUDIT_FAMILY_IMPORT_INVENTORY_CHECK_V2.json',D/'FULL_PARENT_LOSS_LIFECYCLE_CHECK_V2.json',*[original/name/n for n in files]]
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,frames=1200,window_enabled=True,quarter_z_enabled=True,independent_copy_inodes_verified=True,physical_arrays_and_commands_unchanged=True,temporary_fixture_removed=True,transport_stream_passed=True,parent_ledger_passed=True,parent_execution_passed=True,window_stream_passed=True,window_intervals=1199,negative_rejections=negative,source_sha256={**bound,**{str(p):sha(p) for p in paths}},physical_started=False,training_ready=False)
with (D/'NATIVE_FRONT_ENABLED_CHECK_V1.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps({k:v for k,v in out.items() if k!='source_sha256'}),flush=True)
