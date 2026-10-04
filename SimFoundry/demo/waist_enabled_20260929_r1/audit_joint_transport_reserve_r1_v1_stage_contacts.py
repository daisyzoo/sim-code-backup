"""Independent packed substep audit; never imports the recorder or observer.
Verifies sequence/coverage and last-solve force against original contact packets.
It does not infer impulse, force/body sign or time-synchronous dynamics.
"""
from pathlib import Path
import json,hashlib,sys
import numpy as np
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def verify_arrays(z,meta,packets,frames):
 m=meta['metadata'];S=m['expected_substeps'];M=m['expected_manager_steps']
 assert S==24 and M in (1,8) and S%M==0
 assert m['control_decimation']==8 and m['substeps_per_physics_tick']==3
 assert abs(m['solver_dt_s']-1/360)<1e-12 and len(m['geom_to_shape'])==1
 assert meta['world_count']==1 and meta['world_id']==0 and meta['training_ready'] is False
 assert meta['force_comparison_atol']==1e-5 and meta['force_comparison_rtol']==1e-6 and meta['pose_comparison_atol_m']==2e-6
 labels=m['shape_labels'];ownership=np.asarray(m['shape_body']);body_ids=m['body_ids']
 assert len(ownership)==len(labels) and len(body_ids)==len(set(body_ids))==2 and min(body_ids)>=0
 for name,body in zip(['/parcel_box/','/mailer/'],body_ids):
  indices=[i for i,label in enumerate(labels) if name in label];assert indices and all(ownership[i]==body for i in indices)
 for k,shape in [('body_mass_kg',(2,)),('body_com_local',(2,3)),('body_inertia_local',(2,3,3))]:
  a=np.asarray(m[k]);assert a.shape==shape and np.isfinite(a).all()
 assert min(m['body_mass_kg'])>0
 inertia=np.asarray(m['body_inertia_local']);np.testing.assert_allclose(inertia,inertia.transpose(0,2,1),rtol=0,atol=1e-7);assert np.linalg.eigvalsh(inertia).min()>0
 n=frames*(S+M);c=int(meta['contact_records'])
 expected_shapes={'action_step':(n,),'kind':(n,),'substep_tick':(n,),'body_q':(n,2,7),'body_qd':(n,2,6),'solved_contact_count':(n,),'contact_offsets':(n+1,),'contact_id':(c,),'shape_ids':(c,2),'position_world':(c,3),'force_torque_world':(c,6)}
 assert set(z)==set(expected_shapes) and meta['action_intervals']==frames and meta['sample_records']==n
 integer={'action_step','kind','substep_tick','solved_contact_count','contact_offsets','contact_id','shape_ids'}
 for k,shape in expected_shapes.items():
  assert z[k].shape==shape and np.isfinite(z[k]).all(),k
  assert np.issubdtype(z[k].dtype,np.integer if k in integer else np.floating),k
 np.testing.assert_allclose(np.linalg.norm(z['body_q'][:,:,3:],axis=2),1.,rtol=0,atol=1e-4)
 offsets=z['contact_offsets'];assert offsets[0]==0 and offsets[-1]==c and np.all(np.diff(offsets)>=0)
 assert np.all(z['solved_contact_count']>=0) and np.all(z['contact_id']>=0)
 assert np.all(z['shape_ids']>=0) and np.all(z['shape_ids']<len(labels))
 kinds=[];ticks=[]
 for start in range(0,S,S//M):kinds.extend([0]*(S//M)+[1]);ticks.extend(range(start,start+S//M));ticks.append(start+S//M)
 np.testing.assert_array_equal(z['action_step'],np.repeat(np.arange(frames),S+M))
 np.testing.assert_array_equal(z['kind'],np.tile(kinds,frames));np.testing.assert_array_equal(z['substep_tick'],np.tile(ticks,frames))
 selected=np.array([('/parcel_box/' in s or '/mailer/' in s) for s in labels])
 assert np.all(np.any(selected[z['shape_ids']],axis=1))
 # Every row's original contact IDs must be unique, ordered, inside its count.
 for j in range(n):
  ids=z['contact_id'][offsets[j]:offsets[j+1]]
  assert (len(ids)<2 or np.all(np.diff(ids)>0)) and (not len(ids) or ids[-1]<z['solved_contact_count'][j])
 assert len(packets)==frames and [p['after_action_step'] for p in packets]==list(range(frames))
 max_force=0.;max_pose=0.
 for t,p in enumerate(packets):
  j=(t+1)*(S+M)-1;sl=slice(offsets[j],offsets[j+1]);ids=z['contact_id'][sl];contacts=p['parcel_contacts']
  lookup={x['contact_id']:x for x in contacts};assert len(lookup)==len(contacts) and set(ids.tolist())==set(lookup)
  assert z['solved_contact_count'][j]==p['solved_contact_count'] and p['solver_force_buffer_unchanged'] is True
  for index,contact_id in enumerate(ids):
   k=int(offsets[j])+index;contact=lookup[int(contact_id)]
   assert contact['world_id']==0 and [labels[i] for i in z['shape_ids'][k]]==contact['shapes']
   np.testing.assert_array_equal(z['position_world'][k],np.asarray(contact['position_world'],dtype=np.float32))
   local=np.asarray(contact['force_torque_contact']);rotation=np.asarray(contact['contact_frame'])
   reference=np.concatenate((local[:3].dot(rotation),local[3:].dot(rotation)))
   np.testing.assert_allclose(z['force_torque_world'][k],reference,atol=1e-5,rtol=1e-6)
   np.testing.assert_allclose(z['force_torque_world'][k,:3],contact['force_world_N'],atol=1e-5,rtol=1e-6)
   max_force=max(max_force,float(np.max(abs(z['force_torque_world'][k]-reference))))
  reference=np.asarray([p['post_action_pose']['box'],p['post_action_pose']['mailer']])
  np.testing.assert_allclose(z['body_q'][j,:,:3],reference,atol=2e-6,rtol=0)
  max_pose=max(max_pose,float(np.max(abs(z['body_q'][j,:,:3]-reference))))
 return dict(passed=True,action_intervals=frames,substeps_per_action=S,records=n,contact_records=c,max_last_tick_force_torque_error=max_force,max_last_tick_pose_error_m=max_pose,independent_last_tick_comparison=True,training_ready=False)

def audit(ep):
 from joint_transport_reserve_stage_source_binding_v1 import verify_observation_binding
 ep=Path(ep).resolve();binding=verify_observation_binding(ep)
 meta=json.loads((ep/'SUBSTEP_CONTACT_RECORDING.json').read_text());quality=json.loads((ep/'quality.json').read_text());packets=json.loads((ep/'solved_contact_forces.json').read_text())['rows']
 assert meta['recording_sha256']==sha(ep/'substep_contacts.npz')
 with np.load(ep/'substep_contacts.npz',allow_pickle=False) as z:out=verify_arrays({k:z[k] for k in z.files},meta,packets,quality['frames'])
 files=['SUBSTEP_CONTACT_RECORDING.json','substep_contacts.npz','solved_contact_forces.json','quality.json']
 out.update(scope=__doc__,source_binding=binding,source_sha256={n:sha(ep/n) for n in files},auditor_sha256=sha(__file__))
 return out
if __name__=='__main__':
 ep=Path(sys.argv[1]);out=audit(ep);p=ep/'JOINT_TRANSPORT_RESERVE_R1_V1_STAGE_CONTACT_AUDIT.json';assert not p.exists();p.write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k not in ['source_binding','source_sha256','scope']})
