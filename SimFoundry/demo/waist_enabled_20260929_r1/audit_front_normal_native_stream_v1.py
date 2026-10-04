"""Native-file transport and final-normal audit: raw history, capture and scene.
No raw rewriting or counterfactual physical-state reconstruction. Parent loaded-Z
output is an intermediate-command ledger that still requires original math audits.
"""
from pathlib import Path
import sys,json,hashlib
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_normal_nondegradation_v3';sys.path[:0]=[str(S),str(W),str(ROOT)]
from front_normal_stage_source_binding_v3 import verify_observation_binding
from audit_front_normal_command_stream_v1 import FinalCommandStreamAudit
from recontact_scene import RecontactScene
from clearance_runtime import ClearanceGuard
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def inspect(ep,*,fixture_only=False):
 assert type(fixture_only) is bool
 ep=Path(ep).resolve();is_fixture=any((ep.parent/n).exists() for n in ['SOURCE_CONTRACT_FIXTURE.json','DIAGNOSTIC_ONLY.json'])
 assert is_fixture is fixture_only,'Fixture must never pass physical entry'
 bound=verify_observation_binding(ep)
 enabled=read(ep.parent/'provenance.json')['args']['front_normal_nondegradation'];assert type(enabled) is bool
 with np.load(ep/'raw.npz',allow_pickle=False) as z:
  q=z['q'][:,12:23].copy();u=z['action'][:,12:23].copy();task=str(z['task_id']);meta=json.loads(str(z['collect_meta']))
 assert task in ['push_box_to_bin','nudge_mailer_to_bin','wait_no_package'] and len(q)==len(u)
 side='right' if task=='push_box_to_bin' else 'left';wait=task=='wait_no_package';target='box' if side=='right' else 'mailer';other='mailer' if side=='right' else 'box'
 normal=read(ep/'front_normal_nondegradation.json')['rows'] if enabled else None
 if enabled:assert [r['step'] for r in normal]==list(range(len(q)))
 records=read(ep/'joint_transport_clearance.json')['rows'];assert [r['step'] for r in records]==list(range(len(q)))
 loaded=read(ep/'front_loaded_z_priority.json')['rows'];assert [r['step'] for r in loaded]==list(range(len(q)))
 initial=read(ep/'front_initial_center.json');recovery=read(ep/'front_recontact_center.json');capture=[r['step'] for d in [initial,recovery] for r in d['rows'] if r['kind']=='handover']
 if wait:assert not initial['selected'] and not recovery['selected'] and not capture;front={};coords={};plan={}
 else:
  frontal=read(ep/'frontal_bypass.json');plan=frontal['plan'];front={r['step']:r for r in frontal['rows']};cs=read(ep/'coordination.json');coords={r['step']:r for r in cs};assert len(coords)==len(cs)
 with np.load(ep/'trace.npz') as z:xyz={k:z[k].copy() for k in ['box','mailer']}
 with np.load(ep/'parcel_orientation.npz') as z:quat={k:z[k].copy() for k in ['box','mailer']}
 decay=None if wait else read(S/'causal_response_parameters.json')['tasks'][task]['decay'];guard=ClearanceGuard(ROOT,S);stream=FinalCommandStreamAudit(ROOT,S,guard,enabled=enabled,effective_quarter_height=meta.get('joint_transport_effective_quarter_height',False));sizes={'box':[.14,.09,.045],'mailer':[.15,.145,.04]}
 for t in range(len(q)):
  selected=bool(capture and t>=min(capture));assert loaded[t]['selected'] is selected
  scene=None
  if selected:
   assert plan.get('front_route_selected') and initial['selected']
   scene=dict(side=side,target_xyz=xyz[target][t].tolist(),target_quat=quat[target][t].tolist(),core_size=plan['front_initial_center_landing']['actual_core']['collision_core_size_xyz'],other_xyz=xyz[other][t].tolist(),other_quat=quat[other][t].tolist(),other_size=sizes[other])
  parent=loaded[t]['output_command'];assert records[t]['parent_command']==parent
  if t in coords:assert coords[t]['joint_transport_clearance']==records[t]
  obj=None if scene is None else RecontactScene(guard,scene['side'],scene['target_xyz'],scene['target_quat'],scene['core_size'],scene['other_xyz'],scene['other_quat'],scene['other_size'])
  stream.observe(records[t],None if normal is None else normal[t],step=t,selected=selected,side=side,row=front.get(t),coordinate=coords.get(t),scene=obj,current=q[t],previous_q=None if t==0 else q[t-1],previous_command=np.zeros(11) if t==0 else u[t-1],parent_command=parent,executed_command=u[t],decay=decay if selected else None)
 result=stream.finish(len(q));result.update(scope=__doc__,task=task,fixture_only=fixture_only,command_chain_verified=True,physical_candidate_verified=False,original_parent_control_math_audits_required=True,full_task_success=False,training_ready=False)
 files=[Path(__file__),W/'audit_effective_height_transport_records_v1.py',W/'audit_effective_height_contact_v1.py',W/'front_normal_stage_source_binding_v3.py',W/'audit_front_normal_command_stream_v1.py',W/'audit_front_normal_command_record_v1.py',ep/'raw.npz',ep/'trace.npz',ep/'parcel_orientation.npz',ep/'front_initial_center.json',ep/'front_recontact_center.json',ep/'front_loaded_z_priority.json',ep/'joint_transport_clearance.json']
 if enabled:files.append(ep/'front_normal_nondegradation.json')
 if not wait:files.extend([ep/'coordination.json',ep/'frontal_bypass.json'])
 result['source_sha256']={**bound['source_sha256'],**{str(p):sha(p) for p in files}}
 return result

if __name__=='__main__':
 ep=Path(sys.argv[1]);out=ep/'FRONT_NORMAL_NATIVE_STREAM_V1_AUDIT.json';assert not out.exists();result=inspect(ep)
 with out.open('x') as f:json.dump(result,f,indent=2)
 print(json.dumps({k:v for k,v in result.items() if k not in ['rows','source_sha256','scope']}))
