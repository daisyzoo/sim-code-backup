"""Recorded angular momentum and contact moment diagnostic, not a new gate.
Use delta(R I_body R^T omega_world), with force on geometry slot1 positive.
Torque is signed contact couple plus (contact point - world COM) cross force.
Both start- and end-of-solve COM references are reported; the force/pose timing
and unrecorded passive/integration effects prevent claiming exact balance.
"""
from pathlib import Path
import sys,json,hashlib,datetime
import numpy as np
from scipy.spatial.transform import Rotation
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def inspect(ep):
    ep=Path(ep).resolve();history_path=ep/'INSTANT_GUARD_LOAD_HISTORY.json'
    history=json.loads(history_path.read_text());assert history['independent_audit']['passed']
    for name,h in history['source_sha256'].items():assert sha(ep/name)==h
    rec=json.loads((ep/'SUBSTEP_CONTACT_RECORDING.json').read_text());m=rec['metadata'];assert rec['recording_sha256']==sha(ep/'substep_contacts.npz')
    with np.load(ep/'substep_contacts.npz') as z:a={k:z[k] for k in z.files}
    n=history['action_intervals'];stride=24+m['expected_manager_steps'];assert n==1200 and len(a['action_step'])==n*stride
    chosen=[]
    for step in range(n):
        base=step*stride;ticks=a['substep_tick'][base:base+stride]
        chosen.append([base+int(np.flatnonzero(ticks==t)[0]) for t in range(25)])
    chosen=np.array(chosen);previous=np.arange(n*stride)
    previous[chosen[:,1:].ravel()]=chosen[:,:-1].ravel()
    q=a['body_q'].astype(float);qd=a['body_qd'].astype(float)
    rot=Rotation.from_quat(q[:,:,3:].reshape(-1,4)).as_matrix().reshape(n*stride,2,3,3)
    inertia=np.asarray(m['body_inertia_local']);assert inertia.shape==(2,3,3) and np.allclose(inertia,inertia.transpose(0,2,1)) and np.all(np.linalg.eigvalsh(inertia)>0)
    world_i=rot@inertia@rot.transpose(0,1,3,2)
    angular_momentum=np.einsum('sbjk,sbk->sbj',world_i,qd[:,:,3:])
    com=q[:,:,:3]+np.einsum('sbjk,bk->sbj',rot,np.asarray(m['body_com_local']))
    bodies=np.asarray(m['shape_body'])[a['shape_ids']];labels=m['shape_labels'];sid=np.repeat(np.arange(n*stride),np.diff(a['contact_offsets']))
    categories=['hand','table','other_parcel','other'];torques={ref:np.zeros((n*stride,2,4,3)) for ref in ['start_com','end_com']}
    force=np.zeros((n*stride,2,3));couple_max=float(np.abs(a['force_torque_world'][:,3:]).max())
    for b,body in enumerate(m['body_ids']):
        sign=(bodies[:,1]==body).astype(float)-(bodies[:,0]==body).astype(float);mask=sign!=0;sample=sid[mask]
        f=sign[mask,None]*a['force_torque_world'][mask,:3];couple=sign[mask,None]*a['force_torque_world'][mask,3:]
        np.add.at(force[:,b],sample,f)
        indices=a['shape_ids'][mask];bodypairs=bodies[mask];other_shapes=np.where(bodypairs[:,0]==body,indices[:,1],indices[:,0]);group=[]
        for s in other_shapes:
            label=labels[int(s)]
            if 'wrist_roll' in label:g=0
            elif 'table' in label.lower():g=1
            elif '/parcel_box/' in label or '/mailer/' in label:g=2
            else:g=3
            group.append(g)
        group=np.asarray(group,dtype=int)
        for ref,idx in [('start_com',previous[sample]),('end_com',sample)]:
            moment=couple+np.cross(a['position_world'][mask]-com[idx,b],f)
            np.add.at(torques[ref][:,b],(sample,group),moment)
    dt=m['solver_dt_s'];measured=np.diff(angular_momentum[chosen],axis=1);pred={ref:tau[chosen[:,1:]].sum(axis=3)*dt for ref,tau in torques.items()}
    def stats(v):
        x=np.linalg.norm(v,axis=-1);return dict(rms=float(np.sqrt(np.mean(x*x))),median=float(np.median(x)),p95=float(np.quantile(x,.95)),maximum=float(x.max()))
    summary={}
    for b,label in enumerate(m['body_labels']):
        summary[label]=dict(measured_angular_impulse_Nms=stats(measured[:,:,b]),start_com_residual_Nms=stats(measured[:,:,b]-pred['start_com'][:,:,b]),end_com_residual_Nms=stats(measured[:,:,b]-pred['end_com'][:,:,b]),initial_action_max_angular_speed_rad_s=float(np.linalg.norm(qd[chosen[0],b,3:],axis=-1).max()),initial_mean_contact_force_N=force[chosen[0,1:],b].mean(axis=0).tolist())
    key=0 if 'push_box' in ep.name else 1;fr=json.loads((ep/'frontal_bypass.json').read_text())['rows'];exit_actions={f['step']-1 for prev,f in zip(fr,fr[1:]) if prev['mode']=='top_push' and f['mode']!='top_push'}
    selected={x['action_step'] for x in history['rows'] if max(x['vertical_load_n'])>10}|exit_actions
    events=[]
    for step in sorted(selected):
        row=history['rows'][step];peak=int(np.argmax(row['vertical_load_n']));end=chosen[step,peak+1]
        events.append(dict(action_step=step,followed_by_push_exit=step in exit_actions,hand_vertical_peak_N=max(row['vertical_load_n']),peak_tick=peak+1,peak_max_target_tilt_rad=row['max_target_tilt_rad'],target_angular_speed_peak_tick_rad_s=qd[end,key,3:].tolist(),measured_angular_impulse_peak_tick_Nms=measured[step,peak,key].tolist(),predicted_start_com_peak_tick_Nms=pred['start_com'][step,peak,key].tolist(),start_com_residual_peak_tick_Nms=(measured[step,peak,key]-pred['start_com'][step,peak,key]).tolist(),per_contact_group_peak_tick_torque_Nm={group:torques['start_com'][end,key,i].tolist() for i,group in enumerate(categories)},whole_action_measured_angular_impulse_Nms=measured[step,:,key].sum(axis=0).tolist(),whole_action_predicted_start_com_Nms=pred['start_com'][step,:,key].sum(axis=0).tolist()))
    state=Path('/home/user/miniconda3/envs/env_isaaclab/lib/python3.12/site-packages/newton/_src/sim/state.py')
    decoder=Path('/home/user/miniconda3/envs/env_isaaclab/lib/python3.12/site-packages/mujoco_warp/_src/support.py')
    runtime=json.loads((ep.parent/'SUBSTEP_RUNTIME_BINDING.json').read_text());assert runtime['source_files'][str(decoder)]['sha256']==sha(decoder)
    files=[history_path,ep/'SUBSTEP_CONTACT_RECORDING.json',ep/'substep_contacts.npz',ep/'frontal_bypass.json',ep.parent/'SUBSTEP_RUNTIME_BINDING.json',Path(__file__)]
    return dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,body_results=summary,contact_couple_max_abs_Nm=couple_max,events=events,source_sha256={str(p):sha(p) for p in files},current_state_definition=dict(path=str(state),sha256=sha(state),attribution='Current installed definition inspected prospectively; not historical runtime provenance.'),runtime_decoder_sha256=sha(decoder),limitations=['Force-slot sign previously checked by quiet support and linear impulse; not independent solver derivation.','COM reference alternatives expose pose timing sensitivity, not a fitted correction.','World inertia transformation assumes recorded model inertia is body-local and unchanged; angular balance is an observation, not task causality.','Absolute hand load alone is not net parcel torque. No controller or threshold is changed.'],training_ready=False)

if __name__=='__main__':
    ep=Path(sys.argv[1]);p=ep/'INSTANT_GUARD_ANGULAR_BALANCE_DIAGNOSIS.json';assert not p.exists();out=inspect(ep);p.write_text(json.dumps(out,indent=2));print(json.dumps(dict(episode=ep.name,body_results=out['body_results'],events=len(out['events'])),indent=2))
