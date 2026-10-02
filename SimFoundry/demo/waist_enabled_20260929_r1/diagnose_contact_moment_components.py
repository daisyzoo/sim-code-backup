"""Separate actual recorded contact moment into world-vertical/horizontal lever terms.
Signed force acts on geometry slot1; start-of-solve COM reference is used.
This explains recorded moments only, not a hypothetical control intervention.
No collision dimensions, force thresholds or quality gates are changed.
"""
from pathlib import Path
import sys,json,hashlib,datetime
import numpy as np
from scipy.spatial.transform import Rotation
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inspect(ep):
 ep=Path(ep).resolve();hp=next(ep/n for n in ['INSTANT_GUARD_LOAD_HISTORY.json','PEAK_GUARD_LOAD_HISTORY.json','SUBSTEP_LOAD_HISTORY.json'] if (ep/n).exists());h=json.loads(hp.read_text());assert h['independent_audit']['passed']
 for name,digest in h['source_sha256'].items():assert sha(ep/name)==digest
 record=json.loads((ep/'SUBSTEP_CONTACT_RECORDING.json').read_text());m=record['metadata'];assert record['recording_sha256']==sha(ep/'substep_contacts.npz')
 with np.load(ep/'substep_contacts.npz') as z:a={k:z[k] for k in z.files}
 n=h['action_intervals'];stride=24+m['expected_manager_steps'];assert n==1200
 chosen=np.array([[t*stride+int(np.flatnonzero(a['substep_tick'][t*stride:(t+1)*stride]==tick)[0]) for tick in range(25)] for t in range(n)])
 prior=np.arange(n*stride);prior[chosen[:,1:].ravel()]=chosen[:,:-1].ravel()
 key=0 if 'push_box' in ep.name else 1;body=m['body_ids'][key];labels=m['shape_labels'];bodies=np.asarray(m['shape_body'])[a['shape_ids']]
 sign=(bodies[:,1]==body).astype(float)-(bodies[:,0]==body).astype(float);mask=sign!=0;sid=np.repeat(np.arange(n*stride),np.diff(a['contact_offsets']))[mask]
 f=sign[mask,None]*a['force_torque_world'][mask,:3];couple=sign[mask,None]*a['force_torque_world'][mask,3:]
 q=a['body_q'][:,key].astype(float);rot=Rotation.from_quat(q[:,3:]).as_matrix();com=q[:,:3]+np.einsum('sjk,k->sj',rot,np.asarray(m['body_com_local'][key]));r=a['position_world'][mask]-com[prior[sid]]
 vertical=np.zeros_like(f);vertical[:,2]=f[:,2];horizontal=f-vertical
 components=np.stack([np.cross(r,vertical),np.cross(r,horizontal),couple],axis=1)
 np.testing.assert_allclose(components.sum(axis=1),np.cross(r,f)+couple,atol=1e-12,rtol=0)
 ids=a['shape_ids'][mask];bp=bodies[mask];other=np.where(bp[:,0]==body,ids[:,1],ids[:,0]);groups=[]
 for s in other:
  name=labels[int(s)];groups.append(0 if 'wrist_roll' in name else 1 if 'table' in name.lower() else 2 if '/parcel_box/' in name or '/mailer/' in name else 3)
 groups=np.asarray(groups,dtype=int);tau=np.zeros((n*stride,4,3,3));forces=np.zeros((n*stride,4,3));np.add.at(tau,(sid,groups),components);np.add.at(forces,(sid,groups),f)
 weights=np.abs(f[:,2]);local_r=np.einsum('skj,sk->sj',rot[prior[sid]],r);weighted_r=np.zeros((n*stride,4,3));weight_sum=np.zeros((n*stride,4));np.add.at(weighted_r,(sid,groups),local_r*weights[:,None]);np.add.at(weight_sum,(sid,groups),weights)
 fr=json.loads((ep/'frontal_bypass.json').read_text())['rows'];by={x['step']:x for x in fr};exits={x['step']-1:x.get('last_recontact_reason') for prev,x in zip(fr,fr[1:]) if prev['mode']=='top_push' and x['mode']!='top_push'}
 hand_only_top=[t for t in range(n) if by.get(t,{}).get('mode')=='top_push'];selected=sorted(exits);events=[];categories=['hand','table','other_parcel','other'];names=['vertical_force_lever','horizontal_force_lever','contact_couple'];dt=m['solver_dt_s']
 for t in selected:
  jj=chosen[t,1:];impulses=tau[jj].sum(axis=0)*dt;force_mean=forces[jj].mean(axis=0);weight=weight_sum[jj].sum(axis=0);wr=weighted_r[jj].sum(axis=0);cop=np.divide(wr,weight[:,None],out=np.full_like(wr,np.nan),where=weight[:,None]>0)
  peak=int(np.argmax(h['rows'][t]['vertical_load_n']));j=jj[peak]
  events.append(dict(action_step=t,exit_step=t+1,reason=exits[t],world_moment_impulse_Nms={g:{c:impulses[i,k].tolist() for k,c in enumerate(names)} for i,g in enumerate(categories)},mean_signed_force_N={g:force_mean[i].tolist() for i,g in enumerate(categories)},absolute_vertical_weighted_contact_local_from_com_mm={g:cop[i].tolist() if weight[i]>0 else None for i,g in enumerate(categories)},at_hand_peak_world_moment_Nm={g:{c:tau[j,i,k].tolist() for k,c in enumerate(names)} for i,g in enumerate(categories)},at_hand_peak_tick=peak+1,maximum_tilt_rad=h['rows'][t]['max_target_tilt_rad']))
 # Cross-check against the earlier whole moment computation where already available.
 prior_diag=next((ep/name for name in ['INSTANT_GUARD_ANGULAR_BALANCE_DIAGNOSIS.json','SUBSTEP_ANGULAR_BALANCE_DIAGNOSIS.json'] if (ep/name).exists()),None);cross=[]
 if prior_diag:
  d=json.loads(prior_diag.read_text());old={x['action_step']:x for x in d['events']}
  for e in events:
   t=e['action_step'];j=chosen[t,e['at_hand_peak_tick']]
   for i,g in enumerate(categories):np.testing.assert_allclose(tau[j,i].sum(axis=0),old[t]['per_contact_group_peak_tick_torque_Nm'][g],atol=1e-12,rtol=0)
   cross.append(t)
 files=[hp,ep/'substep_contacts.npz',ep/'SUBSTEP_CONTACT_RECORDING.json',ep/'frontal_bypass.json',Path(__file__)]+([prior_diag] if prior_diag else [])
 return dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,episode=ep.name,events=events,cross_checked_peak_group_torque_actions=cross,top_push_actions=len(hand_only_top),source_sha256={str(f):sha(f) for f in files},limitations=['Weighted contact location uses absolute world-vertical load, not a support-polygon margin.','Start/end COM and force evaluation are not perfectly synchronous; momentum residual remains nonzero.','Selected exit actions are outcome-selected diagnostics, not prospective prediction accuracy.','Vertical-force moment and horizontal-force moment are observations; no causal intervention or policy gain established.'],training_ready=False)
if __name__=='__main__':
 ep=Path(sys.argv[1]);out=inspect(ep);p=ep/'CONTACT_MOMENT_COMPONENTS.json';assert not p.exists();p.write_text(json.dumps(out,indent=2));print(json.dumps(dict(episode=ep.name,exits=len(out['events']),cross_checks=len(out['cross_checked_peak_group_torque_actions']))))
