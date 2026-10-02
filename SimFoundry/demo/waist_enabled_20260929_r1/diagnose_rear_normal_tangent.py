"""Decompose actual last-solved-tick rear hand/target force into normal/friction.
Force-side sign supported by archived decoder/current constraint code and full
recorded24-substep momentum check. These last-tick samples are not full-interval
impulses. Contact coordinates transformed with end-state pose are approximate.
"""
from pathlib import Path
import argparse,datetime,hashlib,json
import numpy as np
from scipy.spatial.transform import Rotation
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(run):
 run=Path(run).resolve();signpath=run/'RECORDED_CONTACT_FORCE_SIGN_CHECK.json';signcheck=json.loads(signpath.read_text());sources={str(Path(__file__)):sha(__file__),str(signpath):sha(signpath)};records=[]
 for ref in signcheck['records']:
  ep=next(run.glob('case_*/'+ref['episode']));isbox=ep.name.endswith('push_box_to_bin');key='box' if isbox else 'mailer';actor='/parcel_box/' if isbox else '/mailer/';hand='right' if isbox else 'left';bi=0 if isbox else 1
  yes,no=ref['comparisons'];assert yes['force_on_shape1_sign']==1 and no['force_on_shape1_sign']==-1 and yes['rms_force_balance_error_n']<.003 and no['rms_force_balance_error_n']>2
  packets=json.loads((ep/'solved_contact_forces.json').read_text())['rows'];fr=json.loads((ep/'frontal_bypass.json').read_text());steps=[x['step'] for x in fr['rows'] if x['mode']=='rear_push'];direction=fr['plan']['direction'];meta=json.loads((ep/'SUBSTEP_CONTACT_RECORDING.json').read_text())['metadata'];R=24+meta['expected_manager_steps']
  with np.load(ep/'substep_contacts.npz') as z:body_q=z['body_q'].copy()
  rows=[];largest=0.
  for t in steps:
   normal=np.zeros(3);tangent=np.zeros(3);result=np.zeros(3);contacts=[];pose=body_q[(t+1)*R-1,bi];rot=Rotation.from_quat(pose[3:]).as_matrix()
   for c in packets[t]['parcel_contacts']:
    labels=c['shapes']
    if not any(actor in s for s in labels) or not any(hand+'_wrist_roll' in s for s in labels):continue
    F=np.array(c['force_world_N']);local=np.array(c['force_torque_contact']);frame=np.array(c['contact_frame']);err=float(abs(local[:3]@frame-F).max());largest=max(largest,err);assert err<1e-5 and local[0]>=-1e-7
    if np.linalg.norm(F)<1e-6:continue
    sign=1 if actor in labels[1] else -1;N=sign*local[0]*frame[0];T=sign*F-N;normal+=N;tangent+=T;result+=sign*F
    contacts.append(dict(shapes=labels,normal_force_on_target=N.tolist(),tangential_force_on_target=T.tolist(),contact_position_in_post_target_frame_mm=((np.array(c['position_world'])-pose[:3])@rot*1000).tolist(),normal_in_post_target_frame=(sign*frame[0]@rot).tolist()))
   rows.append(dict(step=t,normal_force_xyz_n=normal.tolist(),tangential_force_xyz_n=tangent.tolist(),total_force_xyz_n=result.tolist(),contact_count=len(contacts),contacts=contacts))
  active=[x for x in rows if x['contact_count']];N=np.sum([x['normal_force_xyz_n'] for x in rows],axis=0);T=np.sum([x['tangential_force_xyz_n'] for x in rows],axis=0);row=dict(episode=ep.name,task_passed=json.loads((ep/'quality.json').read_text())['passed'],rear_frames=len(rows),active_last_tick_frames=len(active),last_tick_normal_vector_sum_n=N.tolist(),last_tick_tangent_vector_sum_n=T.tolist(),last_tick_total_vector_sum_n=(N+T).tolist(),signed_task_y_normal_sum_n=float(N[1]*direction),signed_task_y_tangent_sum_n=float(T[1]*direction),max_decoder_error_n=largest,rows=rows);records.append(row)
  for path in [ep/'solved_contact_forces.json',ep/'frontal_bypass.json',ep/'quality.json',ep/'substep_contacts.npz',ep/'SUBSTEP_CONTACT_RECORDING.json']:sources[str(path)]=sha(path)
  print(json.dumps({k:v for k,v in row.items() if k!='rows'}),flush=True)
 report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,records=records,source_sha256=sources,runtime_changed=False,training_ready=False)
 with (run/'REAR_NORMAL_TANGENT_DIAGNOSIS.json').open('x') as out:json.dump(report,out,indent=2)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('run');a=p.parse_args();main(a.run)
