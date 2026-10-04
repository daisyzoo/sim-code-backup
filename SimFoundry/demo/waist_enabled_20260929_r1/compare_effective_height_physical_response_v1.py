"""Descriptive matched-condition physics comparison; never substitute for audits/admission.
Uses only completed READY episodes. No hypothetical successor states or old-to-new
causal attribution: equal initial states do not guarantee bitwise repeatability.
"""
from pathlib import Path
import argparse,collections,datetime,hashlib,json
import numpy as np
W=Path(__file__).resolve().parent;R=W/'front_effective_height_physical_r1';Q=W/'front_loaded_z_quarter_physical_r2';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text())
def summary(ep):
 quality=read(ep/'quality.json');raw=ep/'raw.npz'
 with np.load(raw,allow_pickle=False) as z:q=z['q'].copy();u=z['action'].copy();task=str(z['task_id']);meta=json.loads(str(z['collect_meta']))
 with np.load(ep/'trace.npz',allow_pickle=False) as z:tr={n:z[n].copy() for n in ['box','mailer']}
 data=read(ep/'joint_transport_clearance.json');rows=data['rows'];assert len(rows)==len(q) and [r['step'] for r in rows]==list(range(len(q)))
 proposals=[r['proposal'] for r in rows if 'proposal' in r];target='box' if task=='push_box_to_bin' else 'mailer';other='mailer' if target=='box' else 'box'
 stable={n:float(np.linalg.norm(v[:,:2]-v[0,:2],axis=1).max()) for n,v in tr.items()}
 output=dict(episode=ep.name,frames=len(q),task=task,saved_quality_passed=quality['passed'],saved_quality_reasons=quality.get('reasons'),target_final_progress_m=quality['metrics'].get('target_final_progress_m'),object_max_xy_m=stable,non_target_max_xy_m=None if task=='wait_no_package' else stable[other],first_upper11_state_zero=bool(np.all(q[0,12:23]==0)),first_upper11_action_zero=bool(np.all(u[0,12:23]==0)),assist_frames=meta['assist_frames'],effective_height_enabled=meta.get('joint_transport_effective_quarter_height',False),transport_selected=sum(r['selected'] for r in rows),transport_applied=sum(r['applied'] for r in rows),transport_reasons=dict(collections.Counter(r['reason'] for r in rows)),proposals=len(proposals),solver_status=dict(collections.Counter(str(r['solver_status']) for r in proposals)),contact_primal_rejected=sum(not p['original_contact_primal_preserved'] for p in proposals),solver_unsuccessful=sum(not p['solver_success'] for p in proposals),applied_steps=[r['step'] for r in rows if r['applied']],independent_audits_required=True,training_ready=False)
 return output,q,u,tr
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);a=parser.parse_args();dest=Path(a.out).resolve();assert dest.parent==R.resolve() and not dest.exists()
 plan=read(R/'PROTOCOL.json')['plan'];rows=[];sources={str(Path(__file__).resolve()):sha(Path(__file__)),str(R/'PROTOCOL.json'):sha(R/'PROTOCOL.json'),str(Q/'PROTOCOL.json'):sha(Q/'PROTOCOL.json')}
 for c in plan['commands']:
  for task in c['tasks']:
   ep=R/f"case_{c['layout_id']}"/f"layout_{c['layout_id']}_{task}";mark=ep/'READY_FOR_AUDIT.json'
   if not mark.exists():continue
   marker=read(mark)
   for p,h in marker['source_sha256'].items():assert sha(p)==h,p
   old=Q/ep.parent.name/ep.name;new,q,u,tr=summary(ep);parent,pq,pu,ptr=summary(old)
   assert new['effective_height_enabled'] and not parent['effective_height_enabled']
   assert new['assist_frames']==parent['assist_frames']==0
   initial=dict(q_identical=np.array_equal(q[0],pq[0]),action_identical=np.array_equal(u[0],pu[0]),objects_identical=all(np.array_equal(tr[n][0],ptr[n][0]) for n in tr))
   n=min(len(u),len(pu));changed=np.flatnonzero(np.any(u[:n]!=pu[:n],axis=1));state_changed=np.flatnonzero(np.any(q[:n]!=pq[:n],axis=1))
   rows.append(dict(group=c['group'],wait=c['wait'],candidate=new,parent=parent,initial=initial,first_action_difference=None if not len(changed) else int(changed[0]),first_state_difference=None if not len(state_changed) else int(state_changed[0]),causal_improvement_not_proven=True))
   for p in [mark,*[base/name for base in [ep,old] for name in ['raw.npz','trace.npz','quality.json','joint_transport_clearance.json']]]:sources[str(p)]=sha(p)
 assert rows,'No complete READY episodes to compare'
 out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,completed_conditions_compared=len(rows),expected_conditions=10,rows=rows,source_sha256=sources,full_control_audits_and_actual_images_pending=True,training_ready=False,goal_complete=False)
 with dest.open('x') as f:json.dump(out,f,indent=2)
 print(json.dumps(dict(completed_conditions=len(rows),candidate_saved_passed=sum(r['candidate']['saved_quality_passed'] for r in rows),parent_saved_passed=sum(r['parent']['saved_quality_passed'] for r in rows),candidate_applied=sum(r['candidate']['transport_applied'] for r in rows),training_ready=False)))
