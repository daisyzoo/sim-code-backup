"""All reversing contexts in all original ten conditions, with actual fixed history.
Candidate optimization, independent constraint certificate and original continuous
static paths. No recursive rollout, no physical command and no training admission.
"""
from pathlib import Path
import collections,datetime,gzip,hashlib,json,sys,time
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_effective_height_v1';D=W/'front_cross_track_full_stream_probe_r1';sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from joint_transport_paths import JointTransportPaths
from audit_unloaded_wrist_prior_live import HandModel
from front_cross_track_nonreversal_solver_candidate_v1 import propose
from audit_front_cross_track_nonreversal_candidate_v1 import verify
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();census=read(D/'CENSUS.json')
for p,h in census['source_sha256'].items():assert sha(p)==h,p
assert census['frame_count']==9740 and len(census['episodes'])==10
G=ClearanceGuard(ROOT,S);paths=JointTransportPaths(ROOT,S);hand=HandModel(ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',ROOT/'assets/robots/g1_hand_support_vertices.json');cached={};rows=[]
(D/'contexts').mkdir(exist_ok=False)
for item in census['required_proposals']:
 ep=Path(item['episode']);t=item['step']
 if str(ep) not in cached:cached[str(ep)]={c['step']:c for c in read(ep/'coordination.json')}
 c=cached[str(ep)][t];old=c['joint_transport_clearance'];tc=old['collector_context'];sc=tc['scene'];scene=RecontactScene(G,sc['side'],sc['target_xyz'],sc['target_quat'],sc['core_size'],sc['other_xyz'],sc['other_quat'],sc['other_size']);kw=dict(step=t,side=sc['side'],scene=scene,current=tc['current'],previous_q=tc['previous_q'],previous_command=tc['previous_command'],parent_command=old['parent_command'],decay=tc['decay'],coordinate=c,elbow_reserve_m=.0015,quarter_enabled=True)
 start=time.monotonic();u,p=propose(**kw,cross_track_nonreversal=True,route_stage='lateral_y');cert=None;pathproofs=None;regularity=None
 if u is not None:
  cert=verify(p,c['task_inputs'],c,guard=G,elbow_reserve_m=.0015,quarter_enabled=True)
  # Independently inspect the active minimum supporting vertex at every point
  # used by the original 2e-7 finite-difference derivative. No global claim.
  side=sc['side'];normal=Rotation.from_quat(sc['target_quat']).as_matrix()[:,2];indices=[];gaps=[]
  for x in [u,*[u+sign*np.eye(11)[j]*2e-7 for j in range(11) for sign in [-1,1]]]:
   T=hand.fk(x,side);values=hand.vertices[side]@(T[:3,:3].T@normal);ordered=np.sort(values);indices.append(int(np.argmin(values)));gaps.append(float(ordered[1]-ordered[0]))
  regularity=dict(fd_step=2e-7,vertex_indices=indices,stable_index=len(set(indices))==1,minimum_separation_m=min(gaps),unique_with_1e12_tolerance=min(gaps)>1e-12)
  if cert['passed']:
   pathproofs={name:paths.certify(np.array(tc['current']),end,scene.record()) for name,end in [('nominal',u),('predicted',np.array(p['predicted_q']))]}
 all_paths=bool(pathproofs is not None and all(v['passed'] for v in pathproofs.values()));accepted=bool(u is not None and cert['passed'] and all_paths and regularity['stable_index'] and regularity['unique_with_1e12_tolerance'])
 summary=dict(episode=ep.name,step=t,solver_success=p['solver_success'],solver_status=p['solver_status'],proposal_exists=u is not None,certificate_passed=None if cert is None else cert['passed'],certificate_reason=None if cert is None else cert.get('reason'),stationarity=None if cert is None else cert.get('certificate',{}).get('stationarity_residual'),all_paths_passed=all_paths,regularity=regularity,verified_in_this_context=accepted,elapsed_s=time.monotonic()-start,original_reversed_dx_m=item['emitted_nominal_dx_m'],candidate_signed_dx_m=p['cross_track_nonreversal']['proposal_signed_nominal_dx_m'],unissued=True)
 detail=dict(summary=summary,proposal=p,certificate=cert,path_proofs=pathproofs);out=D/'contexts'/f'{ep.name}_{t}.json.gz';payload=json.dumps(detail,indent=2).encode()
 with out.open('xb') as raw:
  with gzip.GzipFile(fileobj=raw,mode='wb',mtime=0) as zipped:zipped.write(payload)
 rows.append(dict(summary,detail=str(out),detail_sha256=sha(out)))
 status=dict(status='running',completed=len(rows),expected=len(census['required_proposals']),verified=sum(r['verified_in_this_context'] for r in rows),latest=summary)
 (D/'STATUS.json').write_text(json.dumps(status,indent=2));print(json.dumps({k:v for k,v in summary.items() if k!='regularity'}),flush=True)
sources={str(p):sha(p) for p in [Path(__file__),D/'CENSUS.json',W/'front_cross_track_nonreversal_solver_candidate_v1.py',W/'audit_front_cross_track_nonreversal_candidate_v1.py',W/'audit_unloaded_wrist_prior_live.py']}
for p in S.iterdir():
 if p.is_file():sources[str(p)]=sha(p)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,total_frames_screened=9740,expected=len(census['required_proposals']),verified=sum(r['verified_in_this_context'] for r in rows),rows=rows,source_sha256=sources,physics_started=False,installed=False,training_ready=False,limitations=['Original nonreversing contexts were screened, not reoptimized.','Recorded current/previous state and parcel poses held fixed for every candidate.','A failed candidate requires explicit rejection/stop if original final command reverses; full native integration remains pending.','Static paths and local FD branch checks do not prove continuous dynamic safety or task success.'])
with (D/'RESULT.json').open('x') as f:json.dump(report,f,indent=2)
(D/'STATUS.json').write_text(json.dumps(dict(status='complete',completed=len(rows),expected=report['expected'],verified=report['verified'],training_ready=False),indent=2));print(json.dumps(dict(complete=True,verified=report['verified'],expected=report['expected'])),flush=True)
