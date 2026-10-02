"""Describe observed contact migration within complete loaded push bouts.
Uses independently audited24-substep records. No counterfactual dynamics,
controller changes or new quality gates. All coordinate frames are explicit.
"""
from pathlib import Path
import sys,json,hashlib,datetime
import numpy as np
from scipy.spatial.transform import Rotation
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main(ep):
 ep=Path(ep).resolve();hp=next(ep/n for n in ['CLOSED_PEAK_TRIAL_LOAD_HISTORY.json'] if (ep/n).exists());h=json.loads(hp.read_text());assert h['independent_audit']['passed']
 for name,digest in h['source_sha256'].items():assert sha(ep/name)==digest
 record=json.loads((ep/'SUBSTEP_CONTACT_RECORDING.json').read_text());m=record['metadata'];assert record['recording_sha256']==sha(ep/'substep_contacts.npz')
 with np.load(ep/'substep_contacts.npz') as z:a={k:z[k] for k in z.files}
 n=h['action_intervals'];stride=24+m['expected_manager_steps'];assert n==1200
 chosen=np.array([[t*stride+int(np.flatnonzero(a['substep_tick'][t*stride:(t+1)*stride]==tick)[0]) for tick in range(25)] for t in range(n)])
 prior=np.arange(n*stride);prior[chosen[:,1:].ravel()]=chosen[:,:-1].ravel()
 key='box' if 'push_box' in ep.name else 'mailer';body_index=0 if key=='box' else 1;direction=-1 if key=='box' else 1;body=m['body_ids'][body_index];labels=m['shape_labels'];bodies=np.asarray(m['shape_body'])[a['shape_ids']]
 sign=(bodies[:,1]==body).astype(float)-(bodies[:,0]==body).astype(float);mask=sign!=0;sample=np.repeat(np.arange(n*stride),np.diff(a['contact_offsets']))[mask]
 forces=sign[mask,None]*a['force_torque_world'][mask,:3];ids=a['shape_ids'][mask];bp=bodies[mask];other=np.where(bp[:,0]==body,ids[:,1],ids[:,0]);groups=np.array([0 if 'wrist_roll' in labels[int(s)] else 1 if 'table' in labels[int(s)].lower() else 2 for s in other])
 q=a['body_q'][:,body_index].astype(float);rot=Rotation.from_quat(q[:,3:]).as_matrix();com_local=np.asarray(m['body_com_local'][body_index]);com=q[:,:3]+np.einsum('sjk,k->sj',rot,com_local)
 local=np.einsum('skj,sk->sj',rot[prior[sample]],a['position_world'][mask]-com[prior[sample]])
 weight=np.abs(forces[:,2]);weight_sum=np.zeros((n*stride,3));weighted=np.zeros((n*stride,3,3));signed_fz=np.zeros((n*stride,3));np.add.at(weight_sum,(sample,groups),weight);np.add.at(weighted,(sample,groups),local*weight[:,None]);np.add.at(signed_fz,(sample,groups),forces[:,2])
 slots=chosen[:,1:];weights=weight_sum[slots].sum(axis=1);points=weighted[slots].sum(axis=1);cop=np.divide(points,weights[:,:,None],out=np.full_like(points,np.nan),where=weights[:,:,None]>0)*1000;fz=signed_fz[slots].mean(axis=1)
 fr=json.loads((ep/'frontal_bypass.json').read_text());fs={x['step']:x for x in fr['rows']};modes=[fs.get(t,{}).get('mode','before_frontal') for t in range(n)]
 with np.load(ep/'trace.npz') as tr,np.load(ep/'parcel_orientation.npz') as ori:
  xyz=tr[key].astype(float);palm=tr['palm_right' if key=='box' else 'palm_left'].astype(float);rotation=Rotation.from_quat(ori[key]).as_matrix()
 palm_local=np.einsum('tji,tj->ti',rotation,palm-xyz)-com_local
 progress=direction*(xyz[:,1]-xyz[0,1])*1000
 tilt=np.array([fs.get(t,{}).get('observed_parcel_tilt_rad',np.nan) for t in range(n)])
 bouts=[];start=None
 for t in range(n+1):
  active=t<n and modes[t]=='top_push'
  if active and start is None:start=t
  if not active and start is not None:
   end=t-1;valid=[i for i in range(start,t) if -fz[i,0]>=.3 and np.isfinite(cop[i,0,1])];first=valid[:3];last=valid[-3:]
   def med(indices,arr):return float(np.median(arr[indices])) if indices else None
   b=dict(start=start,end=end,frames=t-start,loaded_frames=len(valid),exit_reason=fs.get(t,{}).get('last_recontact_reason','episode_end'),observed_signed_motion_mm=float(progress[min(t,n-1)]-progress[start]),first3_loaded_actions=first,last3_loaded_actions=last,first3_hand_local_y_from_com_mm=med(first,cop[:,0,1]),last3_hand_local_y_from_com_mm=med(last,cop[:,0,1]),first3_table_local_y_from_com_mm=med(first,cop[:,1,1]),last3_table_local_y_from_com_mm=med(last,cop[:,1,1]),first3_palm_local_y_from_com_mm=med(first,palm_local[:,1]*1000),last3_palm_local_y_from_com_mm=med(last,palm_local[:,1]*1000))
   if first and last:b['hand_contact_y_change_mm']=b['last3_hand_local_y_from_com_mm']-b['first3_hand_local_y_from_com_mm']
   bouts.append(b);start=None
 events=json.loads((ep/'recontact_pose.json').read_text())['rows'];handovers=[x['step'] for x in events if x['kind']=='handover']
 core=fr['plan'].get('region_causal_response',{}).get('actual_core',{}).get('collision_core_size_xyz');half_y=float(core[1]/2*1000) if core else None
 # Verify selected exit action positions against independently saved decomposition.
 previous=ep/'CONTACT_MOMENT_COMPONENTS_MM.json';cross=[]
 if previous.exists():
  for event in json.loads(previous.read_text())['events']:
   t=event['action_step']
   for i,g in enumerate(['hand','table']):
    old=event['absolute_vertical_weighted_contact_local_from_com_mm'][g]
    if old is not None:np.testing.assert_allclose(cop[t,i],old,atol=1e-10,rtol=0)
   cross.append(t)
 fig,axes=plt.subplots(4,1,figsize=(12,10),sharex=True,layout='constrained');x=np.arange(n)
 axes[0].plot(x,progress,label='target signed progress (mm)');axes[0].legend(loc='upper left');axes[0].set_ylabel('mm')
 for b in bouts:
  for ax in axes:ax.axvspan(b['start'],b['end'],color='grey',alpha=.1)
 axes[1].plot(x,np.where(-fz[:,0]>=.3,cop[:,0,1],np.nan),label='hand contact local Y / COM');axes[1].plot(x,cop[:,1,1],label='table contact local Y / COM',alpha=.7)
 if half_y:
  for value in [-half_y-com_local[1]*1000,half_y-com_local[1]*1000]:axes[1].axhline(value,color='black',linestyle=':',alpha=.5)
 axes[1].set_ylabel('mm');axes[1].legend(loc='upper right')
 axes[2].plot(x,palm_local[:,1]*1000,label='palm center local Y / COM');axes[2].plot(x,np.where(-fz[:,0]>=.3,cop[:,0,1],np.nan),label='loaded hand contact Y');axes[2].set_ylabel('mm');axes[2].legend(loc='upper right')
 axes[3].plot(x,-fz[:,0],label='mean downward hand force (N)',color='tab:blue');axes[3].set_ylabel('N');right=axes[3].twinx();right.plot(x,tilt,label='observed tilt(rad)',color='tab:red',alpha=.7);right.axhline(.03,color='tab:red',linestyle=':');right.set_ylabel('rad');axes[3].set_xlabel('Recorded action index; gray = top_push; vertical lines = unloaded handover')
 for t in handovers:
  for ax in axes:ax.axvline(t,color='green',alpha=.22)
 fig.suptitle(ep.parent.parent.name+' / '+ep.name+'\nObserved migration only; absolute vertical-weighted contact, not a support-polygon stability margin')
 image=ep/'CONTACT_MIGRATION.png';assert not image.exists();fig.savefig(image,dpi=140);plt.close(fig)
 files=[hp,ep/'substep_contacts.npz',ep/'SUBSTEP_CONTACT_RECORDING.json',ep/'frontal_bypass.json',ep/'trace.npz',ep/'parcel_orientation.npz',ep/'recontact_pose.json',Path(__file__)]+([previous] if previous.exists() else [])
 out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,episode=ep.name,coordinate_frame='All local contact/palm values in current target-body axes relative to COM; recontact selected_surface_local_xy is not interpreted as target-frame position.',load_filter_n=.3,bouts=bouts,unloaded_handovers=handovers,core_half_y_mm=half_y,cross_checked_exit_actions=cross,image_sha256=sha(image),source_sha256={str(p):sha(p) for p in files},training_ready=False,limitations=['Contact positions use start-of-solve body frame; force and pose sampling timing is not exact.', 'Palm is observed control state, whereas contact is24-substep action average; do not treat their difference as exact support-point tracking error.', 'Selected bouts are outcome-conditioned descriptive records, not causal intervention evidence.'])
 with (ep/'CONTACT_MIGRATION.json').open('x') as f:json.dump(out,f,indent=2)
 print(json.dumps(dict(episode=ep.name,bouts=bouts,cross_checked_exit_actions=cross),indent=2))
if __name__=='__main__':main(sys.argv[1])
