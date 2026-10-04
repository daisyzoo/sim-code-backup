"""Isolated runtime on27 independently observed contexts; no physics or stitched future.
Checks every previously declared1.5mm candidate including all3 late failures.
"""
from pathlib import Path
import sys,json,hashlib,datetime,copy
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_joint_transport_reserve_v1';D=W/'joint_transport_reserve_preparation_r1';sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from joint_transport_runtime import JointTransportRuntime,SPEC
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={};refs={};rows=[]
def read(p):sources[str(p)]=sha(p);return json.loads(p.read_text())
for folder in ['joint_transport_scaled_reserve_probe_r1','joint_transport_early_reserve_probe_r1']:
 result=read(W/folder/'RESULT.json');assert result['complete']
 for p,h in result['source_sha256'].items():assert sha(p)==h,p
 for r in result['rows']:
  if r['reserve_m']==.0015:refs[r['source_run'],r['episode'],r['step']]=r
assert len(refs)==27
G=ClearanceGuard(ROOT,S);runtime=JointTransportRuntime(G,ROOT,S,enabled=True);disabled=JointTransportRuntime(G,ROOT,S);cache={};controls=[]
for i,((run,episode,t),ref) in enumerate(refs.items()):
 ep=W/run/('case_'+episode.split('_')[1])/episode
 if ep not in cache:
  filename='joint_transport_clearance.json' if run=='joint_transport_physical_r1' else 'inactive_transport_clearance.json'
  record=read(ep/filename)['rows'];coords={r['step']:r for r in read(ep/'coordination.json')};front={r['step']:r for r in read(ep/'frontal_bypass.json')['rows']}
  with np.load(ep/'raw.npz',allow_pickle=False) as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
  sources[str(ep/'raw.npz')]=sha(ep/'raw.npz');cache[ep]=(record,coords,front,q,u)
 records,coords,front,q,u=cache[ep];old=records[t];ctx=old['collector_context'];c=coords[t]
 for key,v in [('current',q[t]),('previous_q',q[t-1]),('previous_command',u[t-1])]:np.testing.assert_array_equal(ctx[key],v)
 np.testing.assert_array_equal(old['output_command'],u[t]);np.testing.assert_array_equal(c['front_loaded_z_priority']['output_command'],old['parent_command'])
 args=dict(step=t,selected=True,side=ctx['side'],row=front[t],coordinate=c,scene=RecontactScene(G,**ctx['scene']),parent_command=old['parent_command'],**{k:ctx[k] for k in ['current','previous_q','previous_command','decay']})
 if i==0:
  for name,controller,changes,expected in [('default_off',disabled,{},'disabled'),('unselected',runtime,{'selected':False},'not_captured_front_transport'),('first_frame',runtime,{'step':0},'not_captured_front_transport'),('path',runtime,{'coordinate':dict(c,front_initial_center_override={})},'original_joint_path_has_precedence'),('terminal',runtime,{'coordinate':dict(c,terminal_joint_hold=True)},'terminal_hold_has_precedence'),('stop',runtime,{'row':dict(front[t],route_stop_reason='existing_stop')},'parent_stop_or_guard'),('guard',runtime,{'row':dict(front[t],hand_guard_saturated=True)},'parent_stop_or_guard')]:
   cmd,r=controller.refine(**dict(args,**changes));assert not r['applied'] and r['reason']==expected;np.testing.assert_array_equal(cmd,old['parent_command']);controls.append(dict(case=name,passed=True))
  for name,changes in [('stale_current',{'current':(q[t]+.001).tolist()}),('stale_previous',{'previous_command':(u[t-1]+.001).tolist()}),('wrong_side',{'side':'right'}),('unbound_parent',{'parent_command':(np.array(old['parent_command'])+.001).astype(np.float32).tolist()}),('missing_previous',{'previous_q':None}),('invalid_decay',{'decay':[1.]*11})]:
   try:runtime.refine(**dict(args,**changes))
   except (AssertionError,ValueError):controls.append(dict(case=name,passed=True))
   else:raise AssertionError('Unsafe context accepted: '+name)
 command,record=runtime.refine(**args)
 assert record['proposal']==ref['proposal'],('Changed proposal',t)
 assert record['applied']==ref['fully_verified_unissued'],(t,record['reason'])
 if record['applied']:
  assert record['certificate']==ref['certificate'] and record['paths']==ref['paths'];np.testing.assert_array_equal(command,ref['proposal']['command'])
 else:
  assert record['reason']=='no_verified_proposal' and not ref['preliminary_passed'];np.testing.assert_array_equal(command,old['parent_command'])
 record['collector_context']=copy.deepcopy(ctx);record['scope']='Unissued runtime on one actual context only; no future state inferred.'
 file=D/f"CONTEXT_{ctx['side']}_{t}.json"
 with file.open('x') as f:json.dump(record,f,indent=2)
 row=dict(source_run=run,episode=episode,side=ctx['side'],step=t,applied=record['applied'],reason=record['reason'],reference_proposal_exact=True,record=str(file),record_sha256=sha(file));rows.append(row);print(json.dumps(row),flush=True)
for p in S.iterdir():
 if p.is_file():sources[str(p)]=sha(p)
for mod in list(sys.modules.values()):
 f=getattr(mod,'__file__',None)
 if f:
  p=Path(f).resolve()
  if p.is_file() and p.suffix=='.py' and p.is_relative_to(ROOT):sources[str(p)]=sha(p)
for p in [Path(__file__),ROOT/'assets/robots/g1_hand_support_vertices.json',ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf']:sources[str(p)]=sha(p)
assert len(rows)==27 and sum(r['applied'] for r in rows)==24 and len(controls)==13
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,contexts=rows,controls=controls,spec=SPEC,source_sha256=sources,physical_execution=False,training_ready=False)
with (D/'RUNTIME_CONTEXT_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print('COMPLETE27 matched24proposals3rejections',flush=True)
