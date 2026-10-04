"""Compare complete saved rear-box contacts; diagnostic, not admission/review."""
from pathlib import Path
import collections
import datetime
import hashlib
import json
import numpy as np
from scipy.spatial.transform import Rotation

W=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
sources={}
def bound(p):
    sources[str(p)]=sha(p)
    return p
def read(p):
    return json.loads(bound(p).read_text())

results={}
for version in ['r1','r2']:
    ep=W/('front_box_trailing_physical_'+version)/'case_840023/layout_840023_push_box_to_bin'
    meta=read(ep/'SUBSTEP_CONTACT_RECORDING.json');m=meta['metadata']
    assert sha(ep/'substep_contacts.npz')==meta['recording_sha256'] and meta['action_intervals']==1200
    assert m['expected_substeps']==m['control_decimation']*m['substeps_per_physics_tick']==24
    with np.load(bound(ep/'substep_contacts.npz')) as z:
        a={k:z[k].copy() for k in ['shape_ids','contact_offsets','action_step','substep_tick','force_torque_world']}
    labels=m['shape_labels'];objects=np.array([i for i,s in enumerate(labels) if '/parcel_box/' in s]);wrist=np.array([i for i,s in enumerate(labels) if 'right_wrist_roll' in s]);assert len(objects) and len(wrist)
    pairs=a['shape_ids'];selected=np.isin(pairs,objects).any(1)&np.isin(pairs,wrist).any(1)
    observation=np.repeat(np.arange(len(a['action_step'])),np.diff(a['contact_offsets']))
    assert len(observation)==len(pairs)==len(a['force_torque_world'])
    forces=a['force_torque_world'].astype(float)
    values={axis:np.bincount(observation[selected],weights=np.abs(forces[selected,i]),minlength=len(a['action_step'])) for i,axis in enumerate(['x','y','z'])}
    count=np.bincount(observation[selected],minlength=len(a['action_step']))
    interval=m['expected_substeps']+m['expected_manager_steps'];assert len(a['action_step'])==1200*interval
    fr=read(ep/'frontal_bypass.json')['rows'];by_step={x['step']:x for x in fr}
    ctl=read(ep/'expert_control.json');assert len(ctl)==1200
    with np.load(bound(ep/'trace.npz')) as z:box=z['box'].copy()
    with np.load(bound(ep/'parcel_orientation.npz')) as z:euler=Rotation.from_quat(z['box']).as_euler('xyz')
    yaw=np.degrees(np.unwrap(euler[:,2]));yaw-=yaw[0]
    tilt=np.degrees(np.arccos(np.clip(np.cos(euler[:,0])*np.cos(euler[:,1]),-1,1)))
    per=[];bouts=[];current=None
    for step in range(1200):
        start=step*interval;ticks=a['substep_tick'][start:start+interval];assert np.all(a['action_step'][start:start+interval]==step)
        ix=[start+int(np.flatnonzero(ticks==k)[0]) for k in range(1,25)]
        row=by_step.get(step,{});mode=ctl[step]['mode']
        rec=dict(step=step,mode=mode,box_xyz_m=box[step].tolist(),target_progress_mm=float((box[0,1]-box[step,1])*1000),yaw_relative_deg=float(yaw[step]),tilt_deg=float(tilt[step]),peak_abs_component_n={k:float(v[ix].max()) for k,v in values.items()},contact_substeps=int(np.count_nonzero(count[ix])),last_recontact_reason=row.get('last_recontact_reason'))
        per.append(rec)
        if mode=='top_push':
            if current is None:current=dict(start=step,end=step)
            current['end']=step
        elif current is not None:
            current.update(exit_step=step,exit_reason=row.get('last_recontact_reason'));bouts.append(current);current=None
    if current is not None:current.update(exit_step=None,exit_reason='episode_end');bouts.append(current)
    for bout in bouts:
        lo,hi=bout['start'],bout['end'];end=bout['exit_step'] if bout['exit_step'] is not None else hi
        bout.update(frames=hi-lo+1,progress_observation_delta_mm=float((box[lo,1]-box[end,1])*1000),peak_vertical_abs_n=max(per[t]['peak_abs_component_n']['z'] for t in range(lo,hi+1)),yaw_observation_delta_deg=float(yaw[end]-yaw[lo]),max_tilt_deg=float(tilt[lo:end+1].max()))
    phases={}
    for mode in sorted({r['mode'] for r in per}):
        subset=[r for r in per if r['mode']==mode]
        phases[mode]=dict(frames=len(subset),peak_vertical_abs_n=max(r['peak_abs_component_n']['z'] for r in subset),actions_any_wrist_contact=sum(r['contact_substeps']>0 for r in subset),actions_no_wrist_contact=sum(r['contact_substeps']==0 for r in subset))
    results[version]=dict(bouts=bouts,exit_counts=dict(collections.Counter(b['exit_reason'] for b in bouts)),phase_summary=phases,first_wrist_contact_action=next((x['step'] for x in per if x['contact_substeps']),None),whole_episode_peak_vertical_abs_n=max(x['peak_abs_component_n']['z'] for x in per),early_contact_window=per[48:66],first_phase_divergence_window=per[94:102],per_action=per,selected_shapes=dict(object=[labels[i] for i in objects],wrist=[labels[i] for i in wrist]))
for p,h in sources.items():assert sha(p)==h,p
sources[str(Path(__file__).resolve())]=sha(__file__)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,results=results,source_sha256=sources,limitations=['Absolute components sum across target/right-wrist assembly contacts; not signed net object forces.','Completed solver ticks1..24 used once; tick0 and manager-boundary duplicates excluded.','Observed poses and contact forces need not be exactly synchronous; bout progress changes are associations, not causal attribution.','R2 bag partner is still collecting; no complete paired group approval or independent numeric/visual/control review is claimed.'],training_ready=False)
dest=W/'front_box_trailing_physical_r2/REAR_BOX_CONTACT_COMPARISON_V1.json'
with dest.open('x') as f:json.dump(out,f,indent=2)
print(json.dumps({v:{k:x for k,x in r.items() if k not in ['per_action','early_contact_window','first_phase_divergence_window','selected_shapes']} for v,r in results.items()},indent=2))
