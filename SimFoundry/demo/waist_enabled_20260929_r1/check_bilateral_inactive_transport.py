"""Left-parent parity plus new right-box real-context unissued refinements.
Not an imagined rollout or admission. Candidate only changes inactive joints.
"""
from pathlib import Path
import sys,json,hashlib,datetime
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_inactive_clearance';D=W/'inactive_transport_clearance_bilateral_draft_r1';OLD=W/'inactive_transport_clearance_draft_r1';sys.path[:0]=[str(D),str(S),str(W),str(ROOT)]
from inactive_transport_runtime import InactiveTransportRuntime
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();guard=ClearanceGuard(ROOT,S);runtime=InactiveTransportRuntime(guard,ROOT,S,enabled=True);rows=[];sources={}
prep=read(D/'PREPARATION.json')
for r in prep['files']:
 assert sha(r['parent'])==r['parent_sha256'] and sha(r['path'])==r['sha256'];text=Path(r['path']).read_text()
 for c in reversed(r['edits']):text=text.replace(c['new'],c['old'])
 assert text==Path(r['parent']).read_text()
old=read(OLD/'RUNTIME_CHECK.json');expected={(r['run'],r['step']):r['record'] for r in old['records']}
contexts=[(run,840023,'nudge_mailer_to_bin','left',[step for rn,step in expected if rn==run]) for run in ['front_inactive_clearance_physical_r1','front_recontact_headroom_physical_r1']]+[('front_box_recenter_physical_r2',840020,'push_box_to_bin','right',[185,195,205,215,300,443,444,450,454,460,480,520])]
for run,case,task,side,steps in contexts:
 ep=W/run/f'case_{case}'/f'layout_{case}_{task}';fr={r['step']:r for r in read(ep/'frontal_bypass.json')['rows']};co={r['step']:r for r in read(ep/'coordination.json')};target='mailer' if side=='left' else 'box';other='box' if side=='left' else 'mailer';sizes={'box':[.14,.09,.045],'mailer':[.15,.145,.04]}
 with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23];u=z['action'][:,12:23]
 with np.load(ep/'trace.npz') as z:xyz=z[target];oxy=z[other]
 with np.load(ep/'parcel_orientation.npz') as z:quat=z[target];oq=z[other]
 decay=read(S/'causal_response_parameters.json')['tasks'][task]['decay'];initial=read(ep/'front_initial_center.json');assert initial['selected']
 for t in steps:
  scene=RecontactScene(guard,side,xyz[t],quat[t],sizes[target],oxy[t],oq[t],sizes[other]);f=fr[t];c=co[t]
  out,record=runtime.refine(step=t,selected=True,side=side,row=f,coordinate=c,scene=scene,current=q[t],previous_q=q[t-1],previous_command=u[t-1],parent_command=u[t],decay=decay)
  fixed=np.r_[0:6] if side=='left' else np.r_[0,6:11];np.testing.assert_array_equal(out[fixed],u[t,fixed]);assert guard.command(out,q[t],u[t-1])['accepted']
  if side=='left':assert record['applied'];np.testing.assert_array_equal(out,expected[(run,t)]['output_command']);assert record['certificate']==expected[(run,t)]['certificate'] and record['paths']==expected[(run,t)]['paths']
  rows.append(dict(run=run,task=task,step=t,side=side,mode=f['mode'],measured_inactive_z_mm=runtime.audit.hand.minz(q[t],'right' if side=='left' else 'left')*1000,record=record));print(json.dumps(dict(side=side,step=t,applied=record['applied'],reason=record['reason'])),flush=True)
 for p in [ep/'raw.npz',ep/'coordination.json',ep/'frontal_bypass.json',ep/'trace.npz',ep/'parcel_orientation.npz',ep/'front_initial_center.json']:sources[str(p)]=sha(p)
for p in [Path(__file__),D/'PREPARATION.json',*D.glob('*.py'),OLD/'RUNTIME_CHECK.json',S/'causal_response_parameters.json']:sources[str(p)]=sha(p)
summary={side:dict(contexts=sum(r['side']==side for r in rows),applied_unissued=sum(r['side']==side and r['record']['applied'] for r in rows)) for side in ['left','right']};out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,records=rows,summary=summary,left_original_outputs_and_certificates_unchanged=True,source_sha256=sources,collector_wired=False,physics_started=False,training_ready=False)
with (D/'BILATERAL_RUNTIME_PROBE.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(summary))
