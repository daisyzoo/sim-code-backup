"""Diagnostic-only packed substep output and independent last-tick comparison.
No controller imports; no mutation of supplied arrays, packets, or physics state.
"""
from pathlib import Path
import json,hashlib
import numpy as np

def pack_interval(packet,metadata,original,live_body_q,live_body_qd):
    if len(metadata['geom_to_shape'])!=1:
        raise ValueError('Recording protocol is single-world; never infer past world IDs')
    step=packet['action_step'];kinds=np.asarray(packet['kinds']);ticks=np.asarray(packet['substep_stamps']);valid=np.asarray(packet['valid'],bool)
    n=len(kinds)
    if original['after_action_step']!=step or n!=metadata['expected_substeps']+metadata['expected_manager_steps'] or kinds[-1]!=1 or ticks[-1]!=metadata['expected_substeps']:
        raise ValueError('Interval identity/order mismatch')
    # Buffer.finish already checks every callback boundary and finite input.
    np.testing.assert_array_equal(packet['body_q'][-1],live_body_q)
    np.testing.assert_array_equal(packet['body_qd'][-1],live_body_qd)
    if int(packet['solved_contact_counts'][-1])!=original['solved_contact_count'] or original.get('solver_force_buffer_unchanged') is not True:
        raise ValueError('Last-tick count/read-only mismatch')
    contacts=original['parcel_contacts'];indexed={c['contact_id']:c for c in contacts}
    selected=np.flatnonzero(valid[-1])
    if len(indexed)!=len(contacts) or set(indexed)!=set(selected.tolist()):
        raise ValueError('Last-tick parcel contact coverage differs')
    labels=metadata['shape_labels'];max_force=0.;max_position=0.
    for i in selected:
        c=indexed[int(i)];shapes=[labels[int(s)] for s in packet['shapes'][-1,i]]
        if shapes!=c['shapes'] or c['world_id']!=0:
            raise ValueError('Last-tick shape/world mapping differs')
        local=np.asarray(c['force_torque_contact'],float);frame=np.asarray(c['contact_frame'],float)
        expected=np.r_[local[:3]@frame,local[3:]@frame]
        actual=np.asarray(packet['forces_world'][-1,i])
        # New comparison tolerances, not changes to existing quality gates.
        np.testing.assert_allclose(actual,expected,rtol=1e-6,atol=1e-5)
        np.testing.assert_allclose(actual[:3],c['force_world_N'],rtol=1e-6,atol=1e-5)
        np.testing.assert_array_equal(packet['positions'][-1,i],np.asarray(c['position_world'],dtype=np.float32))
        max_force=max(max_force,float(np.max(abs(actual-expected))))
    for j,name in enumerate(['box','mailer']):
        xyz=packet['body_q'][-1,j,:3];expected=np.asarray(original['post_action_pose'][name])
        np.testing.assert_allclose(xyz,expected,rtol=0,atol=2e-6)
        max_position=max(max_position,float(np.max(abs(xyz-expected))))
    offsets=np.r_[0,np.cumsum(valid.sum(axis=1))].astype(np.int64)
    ids=np.broadcast_to(np.arange(valid.shape[1],dtype=np.int32),valid.shape)[valid]
    out=dict(action_step=np.full(n,step,dtype=np.int32),kind=kinds.astype(np.uint8),substep_tick=ticks.astype(np.int16),body_q=np.asarray(packet['body_q'],dtype=np.float32).copy(),body_qd=np.asarray(packet['body_qd'],dtype=np.float32).copy(),solved_contact_count=np.asarray(packet['solved_contact_counts'],dtype=np.int32).copy(),contact_offsets=offsets,contact_id=ids.copy(),shape_ids=np.asarray(packet['shapes'][valid],dtype=np.int32).copy(),position_world=np.asarray(packet['positions'][valid],dtype=np.float32).copy(),force_torque_world=np.asarray(packet['forces_world'][valid],dtype=np.float32).copy())
    return out,dict(action_step=step,records=n,contact_records=int(offsets[-1]),last_tick_contacts=len(selected),max_force_torque_error=max_force,max_pose_xyz_error_m=max_position,live_body_q_qd_exact=True,last_tick_comparison_passed=True)

class EpisodeSubstepRecording:
    def __init__(self,bridge):
        self.bridge=bridge;self.rows=[];self.comparisons=[]
    def record(self,packet,original):
        if packet['action_step']!=len(self.rows):raise ValueError('Nonconsecutive action intervals')
        state=self.bridge.manager.get_state_0();ids=self.bridge.metadata['body_ids']
        packed,comparison=pack_interval(packet,self.bridge.metadata,original,state.body_q.numpy()[ids],state.body_qd.numpy()[ids])
        self.rows.append(packed);self.comparisons.append(comparison)
    def save(self,folder,expected_frames):
        if len(self.rows)!=expected_frames or not self.rows:raise ValueError('Incomplete substep recording')
        folder=Path(folder);path=folder/'substep_contacts.npz';meta_path=folder/'SUBSTEP_CONTACT_RECORDING.json'
        if path.exists() or meta_path.exists():raise ValueError('Never overwrite recorded substeps')
        keys=[k for k in self.rows[0] if k!='contact_offsets'];combined={k:np.concatenate([r[k] for r in self.rows],axis=0) for k in keys}
        chunks=[];offset=0
        for r in self.rows:chunks.append(r['contact_offsets'][:-1]+offset);offset+=int(r['contact_offsets'][-1])
        combined['contact_offsets']=np.r_[np.concatenate(chunks),offset].astype(np.int64)
        np.savez_compressed(path,**combined)
        metadata=dict(scope=__doc__,training_ready=False,recording_role='diagnostic_observer_trace_requires_source_and_runtime_binding',action_intervals=len(self.rows),sample_records=len(combined['kind']),contact_records=offset,metadata=self.bridge.metadata,comparisons=self.comparisons,recording_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),force_comparison_atol=1e-5,force_comparison_rtol=1e-6,pose_comparison_atol_m=2e-6,live_newton_q_qd_comparison='exact',world_id=0,world_count=1,first_tick_excluded_from_current_interval_impulse=True,boundary_duplicates_retained=True,force_body_sign_not_yet_verified=True,force_state_timing_not_assumed_synchronous=True)
        meta_path.write_text(json.dumps(metadata,indent=2))
