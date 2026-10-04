"""All9740 original frames through explicit off/on final-command adapter.
Actual original histories retained, not a recursive physical rollout.
"""
from pathlib import Path
import collections,copy,datetime,gzip,hashlib,json,sys
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_effective_height_v1';D=W/'front_cross_track_runtime_stream_r2';D.mkdir(exist_ok=False);sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from front_cross_track_runtime_candidate_v2 import FrontCrossTrackNonreversal
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text());C=W/'front_cross_track_full_stream_probe_r1';census=read(C/'CENSUS.json');prior=read(C/'RESULT.json');expected={(r['episode'],r['step']):r for r in prior['rows']};guard=ClearanceGuard(ROOT,S);off=FrontCrossTrackNonreversal(guard,ROOT,S);on=FrontCrossTrackNonreversal(guard,ROOT,S,enabled=True);episodes=[];rejections=[]
for f,h in census['source_sha256'].items():assert sha(f)==h,f
for item in census['episodes']:
 ep=Path(item['episode']);wait=item['wait'];co={} if wait else {r['step']:r for r in read(ep/'coordination.json')};fr={} if wait else {r['step']:r for r in read(ep/'frontal_bypass.json')['rows']};tp=read(ep/'joint_transport_clearance.json')['rows'];counts=collections.Counter();rows=[]
 with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].copy();u=z['action'][:,12:23].copy()
 for t,tr in enumerate(tp):
  tc=tr['collector_context'];sc=tc['scene'];scene=None if sc is None else RecontactScene(guard,sc['side'],sc['target_xyz'],sc['target_quat'],sc['core_size'],sc['other_xyz'],sc['other_quat'],sc['other_size']);kw=dict(step=t,selected=tr['selected'],side=tc['side'],row=fr.get(t),coordinate=co.get(t),scene=scene,current=q[t],previous_q=None if t==0 else q[t-1],previous_command=np.zeros(11,dtype=np.float32) if t==0 else u[t-1],parent_command=u[t],decay=tc['decay'])
  before=copy.deepcopy(co.get(t));a,ar=off.refine(**kw);np.testing.assert_array_equal(a,u[t]);assert ar['reason']=='disabled' and not ar['requires_stop']
  b,br=on.refine(**kw);assert co.get(t)==before,'Input coordinate mutated';counts[br['reason']]+=1
  key=(ep.name,t)
  if key in expected:
   assert b is not None and br['applied'] and not br['requires_stop'],(key,br['reason'])
   detail=json.loads(gzip.decompress(Path(expected[key]['detail']).read_bytes()));np.testing.assert_array_equal(b,detail['proposal']['command']);assert guard.command(b,q[t],u[t-1])['accepted']
  else:assert b is not None and not br['applied'] and not br['requires_stop'];np.testing.assert_array_equal(b,u[t])
  rows.append(dict(step=t,reason=br['reason'],applied=br['applied'],requires_stop=br['requires_stop'],output_command=b.tolist(),certificate_passed=None if not br['applied'] else br['certificate']['passed'],stationarity=None if not br['applied'] else br['certificate']['certificate']['stationarity_residual']))
 summary=dict(episode=ep.name,frames=len(rows),counts=dict(counts),rows=rows);episodes.append(summary)
 with (D/(ep.name+'.json')).open('x') as f:json.dump(summary,f,indent=2)
 (D/'STATUS.json').write_text(json.dumps(dict(status='running',completed_episodes=len(episodes),frames=sum(e['frames'] for e in episodes),applied=sum(r['applied'] for e in episodes for r in e['rows'])),indent=2));print(json.dumps({k:v for k,v in summary.items() if k!='rows'}),flush=True)
sources={str(p):sha(p) for p in [Path(__file__),C/'CENSUS.json',C/'RESULT.json',W/'front_cross_track_runtime_candidate_v2.py',W/'front_cross_track_nonreversal_solver_candidate_v1.py',W/'audit_front_cross_track_certificate_v3.py',W/'audit_front_cross_track_nonreversal_candidate_v1.py']}
for p in S.iterdir():
 if p.is_file():sources[str(p)]=sha(p)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,frames=sum(e['frames'] for e in episodes),off_on_calls=2*sum(e['frames'] for e in episodes),applied=sum(r['applied'] for e in episodes for r in e['rows']),episodes=episodes,source_sha256=sources,installed=False,physics_started=False,training_ready=False,limitations=['Actual recorded parent outputs/history retained. Does not prove trajectories after these changes.','All expected replacement commands equal separately independently certified/path-checked candidates.','Native collector stop/history/waist/source/stream wiring and failure-injection checks remain required.'])
assert report['frames']==9740 and report['applied']==34
with (D/'RESULT.json').open('x') as f:json.dump(report,f,indent=2)
(D/'STATUS.json').write_text(json.dumps(dict(status='complete',passed=True,frames=9740,off_on_calls=19480,applied=34,training_ready=False),indent=2));print(json.dumps(dict(passed=True,frames=9740,applied=34)),flush=True)
