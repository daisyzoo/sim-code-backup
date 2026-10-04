"""Full70-frame source/transport/ledger/parent chain on independent-copy wait fixtures.
Original arrays and sources stay untouched. Fixtures must fail physical entry.
"""
from pathlib import Path
import sys,json,copy,hashlib,datetime,tempfile,shutil,inspect as reflection
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_effective_height_v1';D=W/'front_effective_height_preparation_r1';sys.path[:0]=[str(S),str(W),str(ROOT)]
from front_effective_height_stage_source_binding_v1 import verify_preparation,verify_settings,verify_trial_provenance,verify_observation_binding,EFFECTIVE_HELPERS
from audit_front_effective_height_stream_v2 import inspect
from audit_front_effective_height_r1_v2_execution import inspect as inspect_parent_execution
from front_effective_height_command_ledger_v2 import load_transport_ledger
from audit_front_effective_height_r1_v3_stage_self_clearance import audit as audit_clearance
# Audit adapters alter search precedence; restore the actual collector stage.
sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from joint_transport_effective_height_runtime_v1 import JointTransportRuntime
assert Path(reflection.getfile(JointTransportRuntime)).resolve()==S/'joint_transport_effective_height_runtime_v1.py'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();expected,bound=verify_preparation();assert len(expected)==97;enabled='--disabled' not in sys.argv
if not enabled:expected={k:v for k,v in expected.items() if k not in EFFECTIVE_HELPERS}
original=W/'front_loaded_z_quarter_physical_r2/case_841010';name='layout_841010_wait_no_package';before=sha(original/name/'raw.npz');negative=[];spec=json.loads((original/name/'joint_transport_clearance.json').read_text())['spec']
if enabled:spec=dict(spec,version='joint_transport_clearance_effective_quarter_v1',effective_quarter_height=True,contact_height_target='verified_effective_quarter_task',original_full_task_objective=True,original_height_tolerance_m=2e-7)
def reject(label,fn):
 try:fn()
 except (AssertionError,ValueError,KeyError,FileNotFoundError):negative.append(label)
 else:raise AssertionError('Accepted wrong binding '+label)
reject('unmodified_parent_source',lambda:verify_trial_provenance(original));assert shutil.disk_usage(W).free>26*2**30
with tempfile.TemporaryDirectory(prefix='effective_height_wait_copy_') as tmp:
 case=Path(tmp)/original.name;shutil.copytree(original,case,copy_function=shutil.copy2);ep=case/name;assert (ep/'raw.npz').stat().st_ino!=(original/name/'raw.npz').stat().st_ino
 oldstage=W/'staged_front_loaded_z_quarter_v1';oldprefix=str(oldstage.relative_to(ROOT))+'/';prefix=str(S.relative_to(ROOT))+'/'
 p=case/'provenance.json';prov=json.loads(p.read_text());prov['args']['joint_transport_effective_quarter_height']=enabled;prov['source_sha256']={k:v for k,v in prov['source_sha256'].items() if not k.startswith(oldprefix)}
 for n,h in expected.items():
  dest=case/'source_snapshot'/prefix/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(S/n,dest);prov['source_sha256'][prefix+n]=h
 p.write_text(json.dumps(prov));rp=case/'SUBSTEP_RUNTIME_BINDING.json';runtime=json.loads(rp.read_text());runtime['source_files']={str(S/Path(k).name) if Path(k).parent==oldstage else k:v for k,v in runtime['source_files'].items()};rp.write_text(json.dumps(runtime));(case/'SOURCE_CONTRACT_FIXTURE.json').write_text(json.dumps(dict(fixture_only=True,physical_candidate=False,independent_copy2=True)))
 with np.load(ep/'raw.npz',allow_pickle=False) as z:arrays={k:z[k].copy() for k in z.files}
 q,u=arrays['q'][:,12:23],arrays['action'][:,12:23];meta=json.loads(str(arrays['collect_meta']));meta['joint_transport_clearance']=spec
 if enabled:meta['joint_transport_effective_quarter_height']=True
 else:assert 'joint_transport_effective_quarter_height' not in meta
 arrays['collect_meta']=np.array(json.dumps(meta));np.savez_compressed(ep/'raw.npz',**arrays)
 with np.load(original/name/'raw.npz',allow_pickle=False) as z:
  for k,v in arrays.items():
   if k!='collect_meta':assert np.array_equal(z[k],v),k
 guard=ClearanceGuard(ROOT,S);controller=JointTransportRuntime(guard,ROOT,S,enabled=True,effective_quarter_height=enabled);rows=[]
 for t in range(len(q)):
  prev=np.zeros(11) if t==0 else u[t-1];qp=None if t==0 else q[t-1];cmd,r=controller.refine(step=t,selected=False,side='left',row=None,coordinate=None,scene=None,current=q[t],previous_q=qp,previous_command=prev,parent_command=u[t],decay=None);np.testing.assert_array_equal(cmd,u[t]);r['collector_context']=dict(side='left',current=q[t].tolist(),previous_q=None if qp is None else qp.tolist(),previous_command=prev.tolist(),scene=None,decay=None);rows.append(r)
 data=dict(rows=rows,spec=spec,training_ready=False);record=ep/'joint_transport_clearance.json';record.write_text(json.dumps(data));verify_trial_provenance(case);assert verify_observation_binding(ep)['passed'];stream_result=inspect(ep,fixture_only=True);assert stream_result['passed'] and stream_result['frames']==70 and stream_result['applied']==0 and not stream_result['physical_candidate_verified'];reject('fixture_at_physical_stream_entry',lambda:inspect(ep));(ep/'FRONT_EFFECTIVE_HEIGHT_STREAM_V2_AUDIT.json').write_text(json.dumps(stream_result))
 parents,ledger=load_transport_ledger(ep,allow_source_fixture=True);assert ledger['passed'] and ledger['fixture_only'];np.testing.assert_array_equal(parents,u);execution=inspect_parent_execution(ep,allow_source_fixture=True);assert execution['passed'] and execution['fixture_only'] and not execution['physical_execution_evidence']
 reject('fixture_at_physical_ledger_entry',lambda:load_transport_ledger(ep));reject('fixture_at_physical_execution_entry',lambda:inspect_parent_execution(ep));reject('fixture_at_physical_clearance_entry',lambda:audit_clearance(ep,{},verified_front_events={},verified_front_recovery_events={}))
 for k,v in [('joint_transport_effective_quarter_height',1),('front_loaded_z_quarter',False),('joint_transport_clearance',False),('push_assist',True),('steps',320)]:
  if k=='front_loaded_z_quarter' and not enabled:continue
  a=copy.deepcopy(prov['args']);a[k]=v;reject('setting_'+k,lambda:verify_settings(a))
 for k,v in [('measured_inactive_floor_m',.839),('elbow_gap_m',.004),('stationarity_max',1e-5),('solver_maxiter',120),('solver_ftol',1e-11)]+([('original_height_tolerance_m',2e-4),('contact_height_target','original_full_task'),('original_full_task_objective',False)] if enabled else []):
  m=copy.deepcopy(meta);m['joint_transport_clearance'][k]=v;np.savez_compressed(ep/'raw.npz',**dict(arrays,collect_meta=np.array(json.dumps(m))));reject('metadata_'+k,lambda:verify_observation_binding(ep))
 m=copy.deepcopy(meta)
 if enabled:m.pop('joint_transport_effective_quarter_height')
 else:m['joint_transport_effective_quarter_height']=True
 np.savez_compressed(ep/'raw.npz',**dict(arrays,collect_meta=np.array(json.dumps(m))));reject('wrong_enabled_metadata',lambda:verify_observation_binding(ep));np.savez_compressed(ep/'raw.npz',**arrays)
 for label in ['missing_step','wrong_output','wrong_previous','wrong_version','wrong_enabled_row']:
  d=copy.deepcopy(data)
  if label=='missing_step':d['rows'].pop(20)
  elif label=='wrong_output':d['rows'][20]['output_command'][3]=.001
  elif label=='wrong_previous':d['rows'][20]['collector_context']['previous_command'][3]=.001
  elif label=='wrong_version':d['rows'][20]['version']='other'
  elif enabled:d['rows'][20].pop('effective_quarter_height')
  else:d['rows'][20]['effective_quarter_height']=True
  record.write_text(json.dumps(d));reject(label,lambda:verify_observation_binding(ep))
 record.write_text(json.dumps(data));changed=case/'source_snapshot'/prefix/'joint_transport_runtime.py';changed.write_text(changed.read_text()+'\n# explicit fixture tamper\n');reject('archive_source_tamper',lambda:verify_trial_provenance(case))
assert sha(original/name/'raw.npz')==before
sources={**bound,**{str(p):sha(p) for p in [Path(__file__),D/'AUDIT_FAMILY_IMPORT_CHECK.json',W/'front_effective_height_stage_source_binding_v1.py',W/'audit_front_effective_height_stream_v2.py',W/'audit_effective_height_transport_records_v1.py',W/'audit_effective_height_contact_v1.py',original/name/'raw.npz']}}
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,effective_enabled=enabled,active_sources=len(expected),fixture_frames=70,negative_cases=negative,original_physical_arrays_identical=True,independent_copy2=True,temporary_fixture_removed=True,source_sha256=sources,native_stream=stream_result,parent_execution=execution,parent_ledger=ledger,full_audit_family_ready=False,physics_started=False,training_ready=False)
with (D/('NATIVE_WAIT_ENABLED_CHECK_V2.json' if enabled else 'NATIVE_WAIT_DISABLED_CHECK_V2.json')).open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,enabled=enabled,active_sources=len(expected),frames=70,negative_rejections=len(negative))))
