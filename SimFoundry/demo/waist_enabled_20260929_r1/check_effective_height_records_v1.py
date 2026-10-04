"""Independent effective-target record positives, tampering negatives and70frame wait.
Proposed pushes and generated wait records are explicit fixtures, not new physics.
"""
from pathlib import Path
import sys,json,copy,datetime,hashlib
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_effective_height_v1';D=W/'front_effective_height_preparation_r1';sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from audit_effective_height_transport_records_v1 import JointRecordAudit,JointStreamAudit
from joint_transport_effective_height_runtime_v1 import JointTransportRuntime
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={};good=[];bad=[]
def read(p):sources[str(p)]=sha(p);return json.loads(p.read_text())
def reject(name,fn):
 try:fn()
 except (AssertionError,ValueError,KeyError):bad.append(name)
 else:raise AssertionError('Accepted mutation '+name)
guard=ClearanceGuard(ROOT,S);audit=JointRecordAudit(ROOT,S,guard,effective_quarter_height=True);off=JointRecordAudit(ROOT,S,guard)
for ref in read(W/'front_loaded_z_quarter_physical_r2/EFFECTIVE_HEIGHT_RUNTIME_CHECK_V1.json')['rows']:
 t=ref['step'];ep=next((W/'front_loaded_z_quarter_physical_r2').glob('case_*/'+ref['episode']));old=next(r for r in read(ep/'joint_transport_clearance.json')['rows'] if r['step']==t);c=copy.deepcopy(next(r for r in read(ep/'coordination.json') if r['step']==t));front=next(r for r in read(ep/'frontal_bypass.json')['rows'] if r['step']==t);ctx=old['collector_context'];r=copy.deepcopy(ref['enabled_result']);r['collector_context']=copy.deepcopy(ctx);c['joint_transport_clearance']=r;c['joint_transport_unexecuted_parent_waist_target_rad']=r['parent_command'][0];c['waist_target_rad']=r['output_command'][0]
 args=dict(step=t,selected=True,side=ctx['side'],row=front,coordinate=c,scene=ctx['scene'],current=ctx['current'],previous_q=ctx['previous_q'],previous_command=ctx['previous_command'],parent_command=r['parent_command'],final_command=r['output_command'],decay=ctx['decay'])
 assert audit.verify(r,**args)['applied'];legacy=copy.deepcopy(args);legacy['coordinate']=next(r for r in read(ep/'coordination.json') if r['step']==t);legacy['final_command']=old['output_command'];assert not off.verify(old,**legacy)['applied'];good.append(dict(side=ctx['side'],step=t,enabled_record_passed=True,legacy_unchanged_record_passed=True))
 for name in ['effective_request','height_tolerance','missing_binding','missing_reduction','wrong_fraction','modified_xy','original_objective','record_current','scene_pose','wrong_previous','final_output','proposal_parent','predicted_q','applied_flag','false_contact_primal','claimed_solver_success','wrong_version']:
  rec=copy.deepcopy(r);a=copy.deepcopy(args);a['coordinate']['joint_transport_clearance']=rec;p=rec['proposal'];red=a['coordinate']['front_loaded_z_priority'].get('reduced_z_task')
  if name=='effective_request':p['effective_loaded_contact_binding']['effective_request_m']+=1e-4
  elif name=='height_tolerance':p['effective_loaded_contact_binding']['height_tolerance_m']=2e-4
  elif name=='missing_binding':p.pop('effective_loaded_contact_binding')
  elif name=='missing_reduction':a['coordinate']['front_loaded_z_priority'].pop('reduced_z_task')
  elif name=='wrong_fraction':red['fraction']=.5
  elif name=='modified_xy':red['modified_task']['error'][0]+=.001
  elif name=='original_objective':a['coordinate']['task_inputs']['error'][0]+=.001
  elif name=='record_current':rec['collector_context']['current'][1]+=.001
  elif name=='scene_pose':rec['collector_context']['scene']['target_xyz'][0]+=.002
  elif name=='wrong_previous':rec['collector_context']['previous_command'][0]+=.001
  elif name=='final_output':rec['output_command'][0]+=.01
  elif name=='proposal_parent':p['parent_command'][0]+=.01
  elif name=='predicted_q':p['predicted_q'][0]+=.01
  elif name=='applied_flag':rec['applied']=False
  elif name=='false_contact_primal':p['original_contact_primal_preserved']=False
  elif name=='claimed_solver_success':p['solver_success']=False
  elif name=='wrong_version':rec['version']='joint_transport_clearance_reserve_v1'
  reject(ctx['side']+':'+name,lambda:audit.verify(rec,**a))
# Actual original wait states/actions, native new-runtime metadata, no invented future state.
ep=W/'front_loaded_z_quarter_physical_r2/case_841010/layout_841010_wait_no_package'
with np.load(ep/'raw.npz',allow_pickle=False) as z:q=z['q'][:,12:23].copy();u=z['action'][:,12:23].copy()
assert len(q)==70 and not np.any(u);sources[str(ep/'raw.npz')]=sha(ep/'raw.npz');runtime=JointTransportRuntime(guard,ROOT,S,enabled=True,effective_quarter_height=True);stream=JointStreamAudit(audit);wait=[]
for t in range(70):
 prev=np.zeros(11) if t==0 else u[t-1];qp=None if t==0 else q[t-1];args=dict(step=t,selected=False,side='left',row=None,coordinate=None,scene=None,current=q[t],previous_q=qp,previous_command=prev,parent_command=u[t],decay=None)
 cmd,r=runtime.refine(**args);np.testing.assert_array_equal(cmd,u[t]);r['collector_context']=dict(side='left',scene=None,decay=None,current=q[t].tolist(),previous_q=None if qp is None else qp.tolist(),previous_command=prev.tolist());args['final_command']=u[t];stream.observe(r,**args);wait.append((r,args))
assert stream.finish(70)['applied']==0
for name in ['missing_first','duplicate','wrong_previous_action','wrong_previous_state','short_stream']:
 st=JointStreamAudit(audit)
 if name=='missing_first':fn=lambda:st.observe(wait[1][0],**wait[1][1])
 elif name=='duplicate':st.observe(wait[0][0],**wait[0][1]);fn=lambda:st.observe(wait[0][0],**wait[0][1])
 elif name=='short_stream':st.observe(wait[0][0],**wait[0][1]);fn=lambda:st.finish(70)
 else:
  st.observe(wait[0][0],**wait[0][1]);r,a=copy.deepcopy(wait[1]);a['previous_command' if name=='wrong_previous_action' else 'previous_q'][0]+=.01;fn=lambda:st.observe(r,**a)
 reject('wait:'+name,fn)
for p in [Path(__file__),W/'audit_effective_height_contact_v1.py',W/'audit_effective_height_transport_records_v1.py',D/'RECORD_AUDITOR_PREPARATION.json']:sources[str(p)]=sha(p)
for p in S.iterdir():
 if p.is_file():sources[str(p)]=sha(p)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,positive_records=good,negative_rejections=bad,native_wait_frames=70,independent_target_not_imported_from_runtime=True,source_sha256=sources,full_source_and_stream_binding_pending=True,physics_started=False,training_ready=False)
with (D/'INDEPENDENT_RECORD_CHECK_V1.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,positive_records=len(good),negative_rejections=len(bad),native_wait_frames=70)))
