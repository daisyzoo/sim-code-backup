"""Measured contact-line geometry for each full push bout before corridor guard.
Only actual substep contacts; no material anchoring or altered contact forces.
"""
from pathlib import Path
import json,hashlib,sys,datetime
import numpy as np
from scipy.spatial.transform import Rotation
from analyze_front_bag_yaw_torque import inspect as verify_torque
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inspect(ep):
 ep=Path(ep).resolve();saved=json.loads((ep/'FRONT_BAG_YAW_TORQUE_DIAGNOSTIC.json').read_text());verified=verify_torque(ep);assert verified['rows']==saved['rows'];rec=json.loads((ep/'SUBSTEP_CONTACT_RECORDING.json').read_text());m=rec['metadata']
 with np.load(ep/'substep_contacts.npz') as z:a={k:z[k] for k in z.files}
 stride=24+m['expected_manager_steps'];n=1200;ns=n*stride;chosen=np.asarray([[t*stride+int(np.flatnonzero(a['substep_tick'][t*stride:(t+1)*stride]==k)[0]) for k in range(25)] for t in range(n)]);prev=np.arange(ns);prev[chosen[:,1:].ravel()]=chosen[:,:-1].ravel();sid=np.repeat(np.arange(ns),np.diff(a['contact_offsets']));body=m['body_ids'][1];bodies=np.asarray(m['shape_body'])[a['shape_ids']];sign=(bodies[:,1]==body).astype(float)-(bodies[:,0]==body).astype(float);other=np.where(bodies[:,0]==body,a['shape_ids'][:,1],a['shape_ids'][:,0]);mask=(sign!=0)&np.asarray(['wrist_roll' in m['shape_labels'][int(i)] for i in other]);samples=sid[mask];f=sign[mask,None]*a['force_torque_world'][mask,:3];couple=sign[mask,None]*a['force_torque_world'][mask,3:];rot=Rotation.from_quat(a['body_q'][:,1,3:]).as_matrix();com=a['body_q'][:,1,:3]+np.einsum('sij,j->si',rot,np.asarray(m['body_com_local'][1]));lever=a['position_world'][mask]-com[prev[samples]];weight=np.maximum(-f[:,2],0)
 F=np.zeros((ns,3));T=np.zeros(ns);L=np.zeros(ns);C=np.zeros((ns,3));np.add.at(F,samples,f);np.add.at(T,samples,np.cross(lever,f)[:,2]+couple[:,2]);np.add.at(L,samples,weight);np.add.at(C,samples,weight[:,None]*lever);C=np.divide(C,L[:,None],out=np.zeros_like(C),where=L[:,None]>0)
 result=[]
 for b in saved['bouts']:
  if b['mode']!='top_push':continue
  ix=chosen[b['start']:b['end']+1,1:].ravel();planar=np.linalg.norm(F[ix,:2],axis=1);eligible=(L[ix]>.3)&(planar>.1);use=ix[eligible];assert len(use)>0
  scalar=lambda x:dict(median=float(np.median(x)),p05=float(np.quantile(x,.05)),p95=float(np.quantile(x,.95)))
  row=dict(start=b['start'],end=b['end'],all_ticks=len(ix),eligible_ticks=len(use),selection='hand downward vertical sum >0.3N and resultant planar force >0.1N',yaw_delta_deg=b['yaw_delta_deg'],vertical_load_weighted_contact_offset_mm={axis:scalar(1000*C[use,i]) for i,axis in enumerate('xyz')},signed_effective_planar_force_line_offset_mm=scalar(1000*T[use]/np.linalg.norm(F[use,:2],axis=1)),force_angle_world_deg=scalar(np.rad2deg(np.arctan2(F[use,1],F[use,0]))),negative_hand_torque_tick_fraction=float(np.mean(T[use]<0)))
  # Full-bout summed hand torque must agree with the separately validated report.
  np.testing.assert_allclose(T[ix].sum()*m['solver_dt_s'],b['start_com_impulse_z_nms']['hand']['total'],atol=1e-9,rtol=1e-6);result.append(row)
 sources=dict(saved['source_sha256']);sources.update({str(p):sha(p) for p in [Path(__file__),ep/'FRONT_BAG_YAW_TORQUE_DIAGNOSTIC.json']})
 return dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),episode=str(ep),scope=__doc__,bouts=result,limitations=['Force-line signed distance is tau_z / resultant planar force; not a unique material contact point.','Vertical-load-weighted contact position differs from tangential-force application; do not equate them.','Only actual histories are compared; moving the hand may change friction/contact and requires new physical verification.'],source_sha256=sources,training_ready=False)
if __name__=='__main__':
 ep=Path(sys.argv[1]);d=inspect(ep)
 with (ep/'FRONT_BAG_CONTACT_LINE_DIAGNOSTIC.json').open('x') as f:json.dump(d,f,indent=2)
 for b in d['bouts']:print(json.dumps(b))
