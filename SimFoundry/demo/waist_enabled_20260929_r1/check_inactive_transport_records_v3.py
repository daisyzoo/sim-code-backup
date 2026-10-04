"""Independent recorded-context proposal audit, real wait stream and tamper tests.
Push proposals are unissued isolated alternatives, not a counterfactual rollout.
"""
from pathlib import Path
import sys,json,copy,hashlib,datetime
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_inactive_transport_v2';D=W/'inactive_transport_clearance_bilateral_draft_r1';sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from audit_inactive_transport_records_v1 import TransportRecordAudit,TransportStreamAudit
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
guard=ClearanceGuard(ROOT,S);audit=TransportRecordAudit(ROOT,S,guard);results=[];negative=[];sources={};tested=set()
probe=read(S/'ACTUAL_CORE_RUNTIME_PROBE.json');native=read(S/'NATIVE_HOOK_CHECK.json');assert probe['passed'] and native['passed']
for p,h in native['source_sha256'].items():assert sha(p)==h,p
for rr in probe['records']:
 side,t,task=rr['side'],rr['step'],rr['task'];case=840020 if side=='right' else 840023;ep=W/rr['run']/f'case_{case}'/f'layout_{case}_{task}'
 with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23];u=z['action'][:,12:23]
 with np.load(ep/'trace.npz') as z:xyz={k:z[k][t].tolist() for k in ['box','mailer']}
 with np.load(ep/'parcel_orientation.npz') as z:quat={k:z[k][t].tolist() for k in ['box','mailer']}
 target='box' if side=='right' else 'mailer';other='mailer' if side=='right' else 'box';sizes={'box':[.14,.09,.045],'mailer':[.15,.145,.04]}
 scene=dict(side=side,target_xyz=xyz[target],target_quat=quat[target],core_size=read(ep/'frontal_bypass.json')['plan']['front_initial_center_landing']['actual_core']['collision_core_size_xyz'],other_xyz=xyz[other],other_quat=quat[other],other_size=sizes[other]);decay=read(S/'causal_response_parameters.json')['tasks'][task]['decay']
 row=next(r for r in read(ep/'frontal_bypass.json')['rows'] if r['step']==t);co=next(r for r in read(ep/'coordination.json') if r['step']==t);record=copy.deepcopy(rr['record']);record['collector_context']=dict(side=side,current=q[t].tolist(),previous_q=q[t-1].tolist(),previous_command=u[t-1].tolist(),scene=scene,decay=decay);co['inactive_transport_clearance']=record
 context=dict(step=t,selected=True,side=side,row=row,coordinate=co,scene=scene,current=q[t],previous_q=q[t-1],previous_command=u[t-1],parent_command=u[t],final_command=record['output_command'],decay=decay)
 result=audit.verify(record,**context);results.append(dict(run=rr['run'],side=side,**result));print(json.dumps(results[-1]),flush=True)
 if side not in tested and record['applied']:
  tested.add(side)
  for name in ['wrong_output','wrong_parent','wrong_previous_q','wrong_previous_command','wrong_current','wrong_side','changed_active_joint','wrong_scene','wrong_decay','fake_certificate','fake_path','missing_coordinate_record','selection_flip','wrong_version']:
   r=copy.deepcopy(record);c=copy.deepcopy(context);c['coordinate']['inactive_transport_clearance']=r
   if name=='wrong_output':r['output_command'][0]+=.001
   elif name=='wrong_parent':r['parent_command'][0]+=.001
   elif name=='wrong_previous_q':c['previous_q'][0]+=.001
   elif name=='wrong_previous_command':c['previous_command'][0]+=.001
   elif name=='wrong_current':c['current'][0]+=.001
   elif name=='wrong_side':c['side']='left' if side=='right' else 'right'
   elif name=='changed_active_joint':r['proposal']['command'][5 if side=='left' else 10]+=.001
   elif name=='wrong_scene':c['scene']['target_xyz'][0]+=.001
   elif name=='wrong_decay':r['collector_context']['decay'][0]+=.01
   elif name=='fake_certificate':r['certificate']['passed']=False
   elif name=='fake_path':r['paths']['nominal']['passed']=False
   elif name=='missing_coordinate_record':c['coordinate'].pop('inactive_transport_clearance')
   elif name=='selection_flip':r['selected']=False
   elif name=='wrong_version':r['version']='other'
   try:audit.verify(r,**c)
   except (AssertionError,ValueError,KeyError):negative.append(dict(side=side,case=name,rejected=True))
   else:raise AssertionError('Accepted tamper '+name)
 for n in ['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','coordination.json']:sources[str(ep/n)]=sha(ep/n)
waits=list((W/'front_box_recenter_physical_r2/case_841011').glob('layout_*_wait_no_package'));assert len(waits)==1;ep=waits[0]
with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].copy();u=z['action'][:,12:23].copy()
assert len(q)==70 and np.array_equal(u,np.zeros_like(u))
stream=TransportStreamAudit(audit);first=None;second=None
for t in range(len(q)):
 prev=np.zeros(11) if t==0 else u[t-1];qp=None if t==0 else q[t-1]
 r=dict(step=t,selected=False,applied=False,version='inactive_transport_clearance_bilateral_v1',parent_command=u[t].tolist(),output_command=u[t].tolist(),training_ready=False,reason='not_captured_front_transport',collector_context=dict(side='left',current=q[t].tolist(),previous_q=None if qp is None else qp.tolist(),previous_command=prev.tolist(),scene=None,decay=None))
 c=dict(step=t,selected=False,side='left',row=None,coordinate=None,scene=None,current=q[t],previous_q=qp,previous_command=prev,parent_command=u[t],final_command=u[t],decay=None)
 stream.observe(r,**c)
 if t==0:first=(r,c)
 elif t==1:second=(r,c)
wait=stream.finish(70)
for name in ['skip_first','repeat_step','skip_step','wrong_previous_q','wrong_previous_command','short_horizon']:
 st=TransportStreamAudit(audit)
 try:
  if name=='skip_first':st.observe(second[0],**second[1])
  else:
   st.observe(first[0],**first[1]);r,c=copy.deepcopy(second)
   if name=='repeat_step':st.observe(first[0],**first[1])
   elif name=='skip_step':c['step']=2;st.observe(r,**c)
   elif name=='wrong_previous_q':c['previous_q'][0]+=.001;st.observe(r,**c)
   elif name=='wrong_previous_command':c['previous_command'][0]+=.001;st.observe(r,**c)
   else:st.finish(70)
 except (AssertionError,ValueError,KeyError):negative.append(dict(case=name,rejected=True))
 else:raise AssertionError(name)
assert len(results)==22 and len(negative)==34
for p in [Path(__file__),W/'audit_inactive_transport_records_v1.py',S/'NATIVE_HOOK_CHECK.json',S/'ACTUAL_CORE_RUNTIME_PROBE.json',ep/'raw.npz']:sources[str(p)]=sha(p)
for p,h in sources.items():assert sha(p)==h,p
out=dict(passed=True,scope=__doc__,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),records=results,negative_cases=negative,real_wait_arrays_with_synthetic_transport_records=wait,source_sha256=sources,native_file_source_contract_ready=False,full_parent_audit_family_ready=False,physics_started=False,training_ready=False)
with (S/'INDEPENDENT_RECORD_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,push_contexts=len(results),wait_frames=70,negative=len(negative))))
