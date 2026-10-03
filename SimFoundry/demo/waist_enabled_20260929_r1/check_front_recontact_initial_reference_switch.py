"""Execute actual native-initial audit capture/reference block on explicit fixtures.
The recovery events are previously independently certified affine fixtures;
this verifies initial-audit reference switching, not real physical performance.
"""
from pathlib import Path
import ast,copy,datetime,hashlib,json,sys
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_recontact_center';D=W/'front_bag_recontact_center_draft_r4';sys.path[:0]=[str(W),str(ROOT)]
from audit_front_recontact_center_events import RecoveryEventAudit
from audit_unloaded_wrist_prior_live import near
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();p=W/'audit_front_recontact_initial_live.py';tree=ast.parse(p.read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='verify_files');loop=next(n for n in fn.body if isinstance(n,ast.For));nodes=loop.body;start=next(i for i,n in enumerate(nodes) if isinstance(n,ast.Assign) and any(isinstance(v,ast.Name) and v.id=='recovery_event' for v in n.targets));code=compile(ast.fix_missing_locations(ast.Module(body=copy.deepcopy(nodes[start:]),type_ignores=[])),str(p),'exec');audit=RecoveryEventAudit(ROOT,S);base=json.loads((D/'LIFECYCLE_CHECK.json').read_text());records=[];negative=[]
for f in base['records']:
 ep=W/f['run']/'case_840023/layout_840023_nudge_mailer_to_bin';initial=next(x for x in json.loads((ep/'front_initial_center.json').read_text())['rows'] if x['kind']=='handover');old=np.array(initial['captured_center_local']);last=f['events'][-1]
 ns=dict(np=np,Rotation=Rotation,near=near,audit=audit,side='left',center=old,captured_normal=initial['captured_normal_local_up'],captured_anchor=initial['captured_inactive_anchor_world'],recovery_center=None,recovery_normal=None,recovery_anchor=None,event=dict(kind='unchanged',reason='initial_handover_already_complete'),raw=dict(center_local_after=old.tolist()))
 for label,event in [('tracking',f['events'][0]),('handover',last),('following_loaded',None)]:
  e=copy.deepcopy(event);t=(e or last)['context']['step']+(1 if e is None else 0);cc=(e or last)['context'];q=np.zeros((t+1,11));q[t]=cc['current'];tq=np.tile(cc['scene']['target_quat'],(t+1,1));capture=old if label=='tracking' else np.array(last['captured_center_local']);anchor=initial['captured_inactive_anchor_world'] if label=='tracking' else last['captured_inactive_anchor_world'];normal=initial['captured_normal_local_up'] if label=='tracking' else last['captured_normal_local_up']
  pose=audit.hand.fk(q[t],'left');R=pose[:3,:3];nl=R.T@Rotation.from_quat(tq[t]).as_matrix()[:,2];reference=capture+nl*(min(audit.hand.vertices['left']@nl)-capture@nl)
  row=dict(mode='top_push' if e is None else 'top_press' if label=='handover' else 'top_cross',front_initial_captured_center_local=old.tolist(),projected_support_reference=dict(center_local=capture.tolist(),reference_local=reference.tolist()),control_offset_local=reference.tolist(),target_xyz=[.3,0.,.85]);co=dict(inactive_anchor=anchor,contact_normal_tracking=None if e else dict(target_local_up=normal));experts={t:dict(mode=row['mode'],target_xyz=row['target_xyz'])}
  ns.update(t=t,q=q,tq=tq,row=row,coordinate=co,experts=experts,verified_recovery_events={} if e is None else {t:e});exec(code,ns);records.append(dict(run=f['run'],counter=f['recontacts'],phase=label,passed=True))
  if label=='following_loaded' and len(negative)==0:
   for kind in ['old_anchor','old_center','old_normal','corrupt_initial','unverified_capture']:
    bad=dict(ns);bad['row']=copy.deepcopy(row);bad['coordinate']=copy.deepcopy(co);bad['raw']=copy.deepcopy(ns['raw'])
    if kind=='old_anchor':bad['coordinate']['inactive_anchor']=list(initial['captured_inactive_anchor_world']);bad['coordinate']['inactive_anchor'][0]+=.01
    elif kind=='old_center':bad['row']['projected_support_reference']['center_local']=old.tolist();bad['row']['projected_support_reference']['center_local'][0]+=.01
    elif kind=='old_normal':bad['coordinate']['contact_normal_tracking']['target_local_up']=list(initial['captured_normal_local_up']);bad['coordinate']['contact_normal_tracking']['target_local_up'][0]+=.01
    elif kind=='corrupt_initial':bad['raw']['center_local_after'][0]+=.01
    else:bad['recovery_center']=bad['recovery_normal']=bad['recovery_anchor']=None
    try:exec(code,bad)
    except (AssertionError,ValueError,KeyError):negative.append(kind)
    else:raise AssertionError('stale capture accepted '+kind)
paths=[Path(__file__),p,D/'LIFECYCLE_CHECK.json',S/'INDEPENDENT_STREAM_CHECK.json',S/'CAPTURE_AUDIT_PREPARATION.json'];out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,records=records,negative_cases=negative,source_sha256={str(x):sha(x) for x in paths},simulation_started=False,training_ready=False)
with (S/'INITIAL_REFERENCE_SWITCH_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,capture_phase_fixtures=len(records),negative=len(negative))))
