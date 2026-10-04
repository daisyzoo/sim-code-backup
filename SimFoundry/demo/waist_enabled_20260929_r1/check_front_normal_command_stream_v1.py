"""Historical-context stream checks, not a new physical rollout.
Off: complete original streams. On: unchanged streams, and changed prefix ending
at first modified command; original next-frame history must then be rejected.
"""
from pathlib import Path
import copy,datetime,gzip,hashlib,json,sys
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_normal_nondegradation_v3';D=W/'front_normal_command_stream_r1';D.mkdir(exist_ok=False);sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from audit_front_normal_command_stream_v1 import FinalCommandStreamAudit
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
source=read(W/'front_normal_command_records_r1/RESULT.json');assert source['passed']
for p,h in source['source_sha256'].items():assert sha(p)==h,p
G=ClearanceGuard(ROOT,S);results=[];negative=[];sources={}
for item in read(W/'front_cross_track_full_stream_probe_r1/CENSUS.json')['episodes']:
 ep=Path(item['episode']);wait=item['wait'];fr={} if wait else {r['step']:r for r in read(ep/'frontal_bypass.json')['rows']};cs={} if wait else {r['step']:r for r in read(ep/'coordination.json')};trs=read(ep/'joint_transport_clearance.json')['rows']
 normal_file=W/'front_normal_command_records_r1'/(ep.name+'.json.gz')
 with gzip.open(normal_file,'rt') as f:nrs=json.load(f)['rows']
 with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
 for enabled in [False,True]:
  stream=FinalCommandStreamAudit(ROOT,S,G,enabled=enabled,effective_quarter_height=True);first_changed=None;rejected=False
  for t,tr in enumerate(trs):
   tc=tr['collector_context'];sc=tc['scene'];scene=None if sc is None else RecontactScene(G,sc['side'],sc['target_xyz'],sc['target_quat'],sc['core_size'],sc['other_xyz'],sc['other_quat'],sc['other_size'])
   nr=nrs[t] if enabled else None;coord=copy.deepcopy(cs.get(t));out=np.asarray(nr['output_command']) if enabled else u[t]
   if enabled and coord is not None:
    coord['front_normal_nondegradation']=nr
    if nr['applied']:
     coord['normal_planning_unexecuted_parent_waist_target_rad']=coord['waist_target_rad'];coord['waist_target_rad']=float(out[0])
   kw=dict(step=t,selected=tr['selected'],side=tc['side'],row=fr.get(t),coordinate=coord,scene=scene,current=q[t],previous_q=None if not t else q[t-1],previous_command=np.zeros(11) if not t else u[t-1],parent_command=tr['parent_command'],executed_command=out,decay=tc['decay'])
   if first_changed is not None:
    assert t==first_changed+1
    before=(len(stream.rows),stream.last_q.copy(),stream.last_u.copy())
    try:stream.observe(tr,nr,**kw)
    except AssertionError as e:
     assert str(e)=='previous_command_is_not_last_emitted_command',str(e)
     assert len(stream.rows)==before[0] and np.array_equal(stream.last_q,before[1]) and np.array_equal(stream.last_u,before[2])
     negative.append(dict(episode=ep.name,step=t,case='original_history_after_changed_command',rejected=True));rejected=True;break
    else:raise AssertionError('stale original history accepted')
   stream.observe(tr,nr,**kw)
   if enabled and not np.array_equal(out,u[t]):first_changed=t
   if enabled and first_changed==t:
    # The same accepted prefix must reject malformed order/history before mutation.
    for label in ['duplicate_step','missing_step','wrong_previous_q','wrong_previous_command']:
     bad=dict(kw);bad['step']=t if label=='duplicate_step' else t+2 if label=='missing_step' else t+1
     bad['previous_q']=q[t].copy();bad['previous_command']=out.copy()
     if label=='wrong_previous_q':bad['previous_q'][0]+=.001
     if label=='wrong_previous_command':bad['previous_command'][0]+=.001
     try:stream.observe(tr,nr,**bad)
     except AssertionError:negative.append(dict(episode=ep.name,step=t,case=label,rejected=True))
     else:raise AssertionError(label)
     assert len(stream.rows)==t+1 and np.array_equal(stream.last_u,out)
  proof=stream.finish(len(stream.rows) if rejected else len(q));proof.pop('rows')
  result=dict(episode=ep.name,enabled=enabled,**proof,complete_original_stream=not rejected,first_changed_step=first_changed,expected_stale_history_rejected=rejected,physical_rollout_verified=False)
  results.append(result);(D/'STATUS.json').write_text(json.dumps(dict(status='running',episodes=results),indent=2));print(json.dumps(result),flush=True)
 for p in [normal_file,ep/'raw.npz',ep/'joint_transport_clearance.json']+([] if wait else [ep/'coordination.json',ep/'frontal_bypass.json']):sources[str(p)]=sha(p)
assert len(results)==20 and sum(r['frames'] for r in results if not r['enabled'])==9740
assert sum(r['expected_stale_history_rejected'] for r in results)==1 and len(negative)==5
for p in [Path(__file__),W/'audit_front_normal_command_stream_v1.py',W/'audit_front_normal_command_record_v1.py',W/'audit_effective_height_transport_records_v1.py',W/'front_normal_command_records_r1/RESULT.json',S/'collect_paired_sorting.py']:sources[str(p)]=sha(p)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,results=results,negative=negative,source_sha256=sources,physics_started=False,training_ready=False)
(D/'RESULT.json').write_text(json.dumps(report,indent=2));(D/'STATUS.json').write_text(json.dumps(dict(status='complete',passed=True),indent=2));print('PASS',flush=True)
