"""Recorded-contact serializer fixture; synthetic substep repetition, no physics."""
from pathlib import Path
from types import SimpleNamespace as NS
import json,hashlib,datetime,copy,tempfile
import numpy as np
from substep_contact_recording import pack_interval,EpisodeSubstepRecording
W=Path(__file__).resolve().parent;ep=W/'tilt05_groups_r1/case_840001/layout_840001_push_box_to_bin'
original=next(x for x in json.loads((ep/'solved_contact_forces.json').read_text())['rows'] if x['after_action_step']==300)
contacts=original['parcel_contacts'];labels=sorted({s for c in contacts for s in c['shapes']});lookup={s:i for i,s in enumerate(labels)};capacity=original['solved_contact_count'];n=25
with np.load(ep/'trace.npz') as tr,np.load(ep/'parcel_orientation.npz') as ori:q=np.stack([np.r_[tr[k][301],ori[k][301]] for k in ['box','mailer']]).astype(np.float32)
qd=np.zeros((2,6),dtype=np.float32)
p=dict(action_step=300,kinds=np.r_[np.zeros(24),1].astype(int),substep_stamps=np.arange(25),valid=np.zeros((n,capacity),bool),body_q=np.tile(q,(n,1,1)),body_qd=np.tile(qd,(n,1,1)),solved_contact_counts=np.full(n,capacity),shapes=np.zeros((n,capacity,2),np.int32),positions=np.zeros((n,capacity,3),np.float32),forces_world=np.zeros((n,capacity,6),np.float32))
for c in contacts:
 i=c['contact_id'];p['valid'][:,i]=True;p['shapes'][:,i]=[lookup[s] for s in c['shapes']];p['positions'][:,i]=c['position_world'];local=np.asarray(c['force_torque_contact']);frame=np.asarray(c['contact_frame']);p['forces_world'][:,i]=np.r_[local[:3]@frame,local[3:]@frame]
metadata=dict(geom_to_shape=[list(range(len(labels)))],shape_labels=labels,body_ids=[0,1],expected_substeps=24,expected_manager_steps=1,fixture_cpu=True)
checks=[];before={k:v.tobytes() for k,v in p.items() if isinstance(v,np.ndarray)};o_before=json.dumps(original,sort_keys=True)
packed,cmp=pack_interval(p,metadata,original,q,qd)
assert before=={k:v.tobytes() for k,v in p.items() if isinstance(v,np.ndarray)} and json.dumps(original,sort_keys=True)==o_before
assert packed['contact_offsets'][-1]==n*len(contacts)
checks.append(dict(kind='real_packet_last_tick_comparison_and_input_immutability',**cmp))
def reject(name,fn):
 try:fn()
 except (ValueError,AssertionError):checks.append(dict(rejected=name))
 else:raise AssertionError('accepted '+name)
for name,mutate in [('step_identity',lambda x:x.update(action_step=299)),('force_mismatch',lambda x:x['forces_world'].__setitem__((-1,contacts[0]['contact_id'],0),99)),('missing_contact',lambda x:x['valid'].__setitem__((-1,contacts[0]['contact_id']),False)),('state_mismatch',lambda x:x['body_q'].__setitem__((-1,0,0),99)),('contact_count',lambda x:x['solved_contact_counts'].__setitem__(-1,0)),('final_kind',lambda x:x['kinds'].__setitem__(-1,0)),('position_mismatch',lambda x:x['positions'].__setitem__((-1,contacts[0]['contact_id'],0),99))]:
 bad=copy.deepcopy(p);mutate(bad);reject(name,lambda:pack_interval(bad,metadata,original,q,qd))
badmeta=copy.deepcopy(metadata);badmeta['geom_to_shape']*=2;reject('multiple_worlds_not_recorded',lambda:pack_interval(p,badmeta,original,q,qd))
class Array:
 def __init__(self,v):self.v=v
 def numpy(self):return self.v.copy()
state=NS(body_q=Array(q),body_qd=Array(qd));bridge=NS(metadata=metadata,manager=NS(get_state_0=lambda:state));rec=EpisodeSubstepRecording(bridge)
reject('nonconsecutive_step',lambda:rec.record(p,original))
for t in range(2):
 part=copy.deepcopy(p);part['action_step']=t;ori=copy.deepcopy(original);ori['after_action_step']=t;rec.record(part,ori)
outdir=Path(tempfile.mkdtemp(prefix='substep_serialization_fixture_'));reject('incomplete_recording',lambda:rec.save(outdir,3));rec.save(outdir,2)
with np.load(outdir/'substep_contacts.npz') as z:
 assert len(z['action_step'])==50 and z['contact_offsets'].shape==(51,)
 for t in range(50):
  sl=slice(z['contact_offsets'][t],z['contact_offsets'][t+1]);assert z['contact_id'][sl].tolist()==sorted(c['contact_id'] for c in contacts)
 assert z['contact_offsets'][-1]==50*len(contacts)
 checks.append(dict(kind='compressed_roundtrip_two_intervals',records=50,contacts=int(z['contact_offsets'][-1])))
reject('overwrite_refused',lambda:rec.save(outdir,2))
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
report=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,checks=checks,synthetic_output_directory=str(outdir),physics_initialized=False,actual_runtime_installed=False,training_ready=False,source_sha256={str(f):sha(f) for f in [Path(__file__),W/'substep_contact_recording.py',ep/'solved_contact_forces.json',ep/'trace.npz',ep/'parcel_orientation.npz']})
p=W/'SUBSTEP_RECORDING_CHECK.json';assert not p.exists();p.write_text(json.dumps(report,indent=2));print('PASS',len(checks),'recorded-packet serialization checks, no actual substep physics')
