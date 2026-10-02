"""Original1e-6 KKT on every recorded new command, all failures retained.
Fixed historical inputs, not physical replay or data admission.
"""
from pathlib import Path
import sys,json,hashlib,datetime,os
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_rear_corridor_recovery_guarded';sys.path[:0]=[str(W),str(ROOT)]
from audit_rear_corridor_command_records import RecoveryVerifier
from rear_corridor_stationarity import verify
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();verifier=RecoveryVerifier(ROOT,S);dest=W/'REAR_CORRIDOR_STATIONARITY_CHECK.json';assert not dest.exists();rows=[];sources={};frozen={str(p):sha(p) for p in [Path(__file__),W/'rear_corridor_stationarity.py',W/'support_vertex_stationarity.py',W/'audit_rear_corridor_command_records.py',W/'audit_self_clearance_task_optimality.py',W/'audit_unloaded_wrist_prior_live.py',W/'REAR_CORRIDOR_JOINT_RECOVERY_FULL_CHECK.json',W/'REAR_CORRIDOR_UNLOAD_CHECK.json',ROOT/'simfoundry/robots/g1_assets.py',ROOT/'assets/robots/g1_hand_support_vertices.json',ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',S/'elbow_torso_hulls.json']}
def save(status,**kw):
 temp=dest.with_suffix('.tmp');temp.write_text(json.dumps(dict(status=status,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,completed=len(rows),passed_commands=sum(r['certificate']['passed'] for r in rows),failed_commands=sum(not r['certificate']['passed'] for r in rows),source_sha256=sources,frozen_sha256=frozen,training_ready=False,**kw),indent=2));temp.replace(dest)
try:
 save('running');full=json.loads((W/'REAR_CORRIDOR_JOINT_RECOVERY_FULL_CHECK.json').read_text());lifts=json.loads((W/'REAR_CORRIDOR_UNLOAD_CHECK.json').read_text());lookup={(r['episode'],r['step']):r['result'] for r in lifts['rows']};sizes={'box':[.14,.09,.045],'mailer':[.15,.145,.04]}
 for epitem in full['episodes']:
  ep=W/epitem['episode'];fr=json.loads((ep/'frontal_bypass.json').read_text());fs={r['step']:r for r in fr['rows']};cs={c['step']:c for c in json.loads((ep/'coordination.json').read_text())};key='box' if 'push_box' in ep.name else 'mailer';other='mailer' if key=='box' else 'box'
  with np.load(ep/'trace.npz') as z:pos={k:z[k].copy() for k in sizes}
  with np.load(ep/'parcel_orientation.npz') as z:rot={k:Rotation.from_quat(z[k]).as_matrix() for k in sizes}
  with np.load(ep/'raw.npz') as z:actions=z['action'].copy()
  for n in ['frontal_bypass.json','coordination.json','trace.npz','parcel_orientation.npz','raw.npz']:sources[str(ep/n)]=sha(ep/n)
  for r in epitem['rows']:
   t=r['step'];kind='loaded_recovery' if r['result']['applied'] else 'unload';result=r['result'] if kind=='loaded_recovery' else lookup[(epitem['episode'],t)];cmd=next(a['command'] for a in result['attempts'] if a['accepted']);geometry=dict(target_xyz=pos[key][t],obstacle_xyz=pos[other][t],target_rotation=rot[key][t],obstacle_rotation=rot[other][t],target_size=sizes[key],obstacle_size=sizes[other],core_size=fr['plan']['rear_cop_centering']['actual_core_size_xyz'])
   cert=verify(verifier,row=fs[t],coordinate=cs[t],current=cs[t]['upper_q'],previous=actions[t-1,12:23],command=cmd,kind=kind,geometry=geometry);rows.append(dict(episode=epitem['episode'],step=t,kind=kind,certificate=cert))
   if len(rows)%100==0:save('running');print('KKT',len(rows),'failed',sum(not x['certificate']['passed'] for x in rows),flush=True)
 assert len(rows)==1943
 for p,h in {**sources,**frozen}.items():assert sha(p)==h,p
 save('complete',passed=all(r['certificate']['passed'] for r in rows))
except BaseException as e:save('check_failed',error=repr(e));raise
