"""Independent record positives, mutation rejection and contiguous actual wait.
Saved push states with unissued proposals are explicitly fixture-only; no next
state is attributed to a new command. Wait uses original actual states/actions.
Native physical source entry and all parent audits remain separate requirements.
"""
from pathlib import Path
import sys,json,hashlib,datetime,copy
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_joint_transport_bounded_v1';D=W/'joint_transport_bounded_preparation_r1';sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from audit_joint_transport_records_v1 import JointRecordAudit,JointStreamAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={str(p):sha(p) for p in S.iterdir() if p.suffix=='.py'}
def read(p):sources[str(p)]=sha(p);return json.loads(p.read_text())
def reject(name,callback):
 try:callback()
 except (AssertionError,ValueError,KeyError) as e:return dict(case=name,passed=True,rejected=type(e).__name__)
 raise AssertionError('Mutation accepted: '+name)
def main():
 guard=ClearanceGuard(ROOT,S);audit=JointRecordAudit(ROOT,S,guard);positives=[];negative=[]
 for side,t,case,task in [('left',373,840023,'nudge_mailer_to_bin'),('right',808,840020,'push_box_to_bin')]:
  r=read(D/f'CONTEXT_{side}_{t}.json');p=r['proposal'];ep=W/'inactive_transport_physical_r1'/f'case_{case}'/f'layout_{case}_{task}';c={v['step']:v for v in read(ep/'coordination.json')}[t];row={v['step']:v for v in read(ep/'frontal_bypass.json')['rows']}[t];scene=p['scene']
  r['collector_context']=dict(side=side,current=p['current'],previous_q=p['previous_q'],previous_command=p['previous_command'],scene=scene,decay=p['decay']);c['waist_target_rad']=r['output_command'][0];c['joint_transport_unexecuted_parent_waist_target_rad']=p['parent_command'][0];c['joint_transport_clearance']=r
  ctx=dict(step=t,selected=True,side=side,row=row,coordinate=c,scene=scene,current=p['current'],previous_q=p['previous_q'],previous_command=p['previous_command'],parent_command=p['parent_command'],final_command=r['output_command'],decay=p['decay'])
  result=audit.verify(r,**ctx);assert result['applied'];positives.append(dict(side=side,step=t,passed=True,scope='fixture_only_unissued_saved_context'));print(json.dumps(positives[-1]),flush=True)
  for name in ['record_current','record_previous_q','record_previous_command','scene_pose','side','final_output','proposal_parent','prediction','original_bounds','first_zero','applied_status']:
   rec=copy.deepcopy(r);context=copy.deepcopy(ctx);context['coordinate']['joint_transport_clearance']=rec
   if name in ['record_current','record_previous_q','record_previous_command']:rec['collector_context'][name[7:]][1]+=.001
   elif name=='scene_pose':rec['collector_context']['scene']['target_xyz'][0]+=.002
   elif name=='side':rec['collector_context']['side']='left' if side=='right' else 'right'
   elif name=='final_output':rec['output_command'][1]=float(np.float32(rec['output_command'][1]+.001))
   elif name=='proposal_parent':rec['proposal']['parent_command'][1]=float(np.float32(rec['proposal']['parent_command'][1]+.001))
   elif name=='prediction':rec['proposal']['predicted_q'][1]+=.001
   elif name=='original_bounds':context['coordinate']['task_inputs']['lower'][0]-=.01
   elif name=='first_zero':context['step']=0
   elif name=='applied_status':rec['applied']=False
   negative.append(dict(side=side,**reject(name,lambda:audit.verify(rec,**context))))
 # Entire actual zero-start wait, with explicit fixture candidate records.
 ep=W/'inactive_transport_physical_r1/case_841010/layout_841010_wait_no_package'
 with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].copy();u=z['action'][:,12:23].copy()
 sources[str(ep/'raw.npz')]=sha(ep/'raw.npz');assert len(q)==70 and not np.any(u);stream=JointStreamAudit(audit);wait=[]
 for t in range(len(q)):
  prev=np.zeros(11) if t==0 else u[t-1];qp=None if t==0 else q[t-1];r=dict(version='joint_transport_clearance_v1',step=t,selected=False,applied=False,training_ready=False,parent_command=u[t].tolist(),output_command=u[t].tolist(),reason='not_captured_front_transport',collector_context=dict(side='left',scene=None,decay=None,current=q[t].tolist(),previous_q=None if qp is None else qp.tolist(),previous_command=prev.tolist()))
  ctx=dict(step=t,selected=False,side='left',row=None,coordinate=None,scene=None,current=q[t],previous_q=qp,previous_command=prev,parent_command=u[t],final_command=u[t],decay=None);stream.observe(r,**ctx);wait.append((r,ctx))
 wait_result=stream.finish(70);assert wait_result['applied']==0
 for name in ['missing_first','duplicate_step','wrong_previous_action','wrong_previous_state','short_stream']:
  st=JointStreamAudit(audit)
  if name=='missing_first':callback=lambda:st.observe(wait[1][0],**wait[1][1])
  elif name=='duplicate_step':st.observe(wait[0][0],**wait[0][1]);callback=lambda:st.observe(wait[0][0],**wait[0][1])
  elif name=='short_stream':st.observe(wait[0][0],**wait[0][1]);callback=lambda:st.finish(70)
  else:
   st.observe(wait[0][0],**wait[0][1]);r,c=copy.deepcopy(wait[1]);key='previous_command' if name=='wrong_previous_action' else 'previous_q';c[key][0]+=.001;callback=lambda:st.observe(r,**c)
  negative.append(reject(name,callback))
 for p in [Path(__file__),W/'audit_joint_transport_records_v1.py']:sources[str(p)]=sha(p)
 for p,h in sources.items():assert sha(p)==h,p
 out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,positive_records=positives,negative_cases=negative,actual_wait_frames=70,actual_wait_passed=True,source_sha256=sources,native_physical_source_contract_validated=False,physical_commands_issued=False,training_ready=False)
 with (D/'INDEPENDENT_RECORD_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
 print(json.dumps(dict(passed=True,positive_records=len(positives),negative_cases=len(negative),actual_wait_frames=70)),flush=True)
if __name__=='__main__':main()
