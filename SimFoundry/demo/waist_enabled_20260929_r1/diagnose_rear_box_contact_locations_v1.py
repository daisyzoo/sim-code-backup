"""Observed contact-location association; no causal or admission certificate."""
from pathlib import Path
import ast
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
def read(p):return json.loads(bound(p).read_text())
comparison=read(W/'front_box_trailing_physical_r2/REAR_BOX_CONTACT_COMPARISON_V2.json')
outrows={}
for version in ['r1','r2']:
    case=W/('front_box_trailing_physical_'+version)/'case_840023'
    ep=case/'layout_840023_push_box_to_bin'
    provenance=read(case/'provenance.json')
    calibration=case/'source_snapshot/simfoundry/calibration/sorting_station.py'
    assert sha(calibration)==provenance['source_sha256']['simfoundry/calibration/sorting_station.py']
    assignments=[n for n in ast.parse(bound(calibration).read_text()).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PARCEL_BOX_SIZE' for t in n.targets)]
    assert len(assignments)==1
    size=np.asarray(ast.literal_eval(assignments[0].value),float);assert size.shape==(3,) and np.all(size>0)
    meta=read(ep/'SUBSTEP_CONTACT_RECORDING.json');m=meta['metadata']
    assert meta['recording_sha256']==sha(ep/'substep_contacts.npz') and meta['action_intervals']==1200 and m['expected_substeps']==24
    with np.load(bound(ep/'substep_contacts.npz')) as z:a={k:z[k].copy() for k in z.files}
    with np.load(bound(ep/'trace.npz')) as z:xyz=z['box'].copy()
    with np.load(bound(ep/'parcel_orientation.npz')) as z:quat=z['box'].copy()
    body=next(i for i,label in enumerate(m['body_labels']) if label.endswith('/parcel_box'))
    labels=m['shape_labels'];object_ids=np.array([i for i,s in enumerate(labels) if '/parcel_box/' in s]);hand_ids=np.array([i for i,s in enumerate(labels) if 'right_wrist_roll' in s])
    selected=np.isin(a['shape_ids'],object_ids).any(1)&np.isin(a['shape_ids'],hand_ids).any(1)
    interval=24+m['expected_manager_steps'];offset=a['contact_offsets'];per=[]
    for step in range(1200):
        ids=np.arange(step*interval,(step+1)*interval);assert np.all(a['action_step'][ids]==step)
        ticks=a['substep_tick'][ids];initial=int(ids[np.flatnonzero(ticks==0)[0]]);chosen=[int(ids[np.flatnonzero(ticks==t)[0]]) for t in range(1,25)]
        np.testing.assert_allclose(a['body_q'][initial,body,:3],xyz[step],rtol=0,atol=2e-6)
        assert (Rotation.from_quat(a['body_q'][initial,body,3:])*Rotation.from_quat(quat[step]).inv()).magnitude()<2e-6
        if step<1199:np.testing.assert_allclose(a['body_q'][ids[-1],body,:3],xyz[step+1],rtol=0,atol=2e-6)
        samples=[];previous=initial
        for tick,j in enumerate(chosen,1):
            contacts=np.arange(offset[j],offset[j+1]);contacts=contacts[selected[contacts]]
            weights=np.abs(a['force_torque_world'][contacts,2].astype(float));load=float(weights.sum())
            if load>.05:
                point=np.average(a['position_world'][contacts].astype(float),axis=0,weights=weights)
                local={ref:Rotation.from_quat(a['body_q'][index,body,3:]).inv().apply(point-a['body_q'][index,body,:3]) for ref,index in [('start',previous),('end',j)]}
                samples.append(dict(tick=tick,absolute_vertical_load_n=load,start_pose_local_mm=(local['start']*1000).tolist(),end_pose_local_mm=(local['end']*1000).tolist(),pose_reference_difference_mm=float(np.linalg.norm(local['end']-local['start'])*1000),end_pose_nominal_xy_margin_mm=((size[:2]/2-np.abs(local['end'][:2]))*1000).tolist()))
            previous=j
        per.append(dict(step=step,loaded_samples=samples))
    bouts=[]
    for bout in comparison['results'][version]['bouts']:
        lo,hi=bout['start'],bout['end'];samples=[s for row in per[lo:hi+1] for s in row['loaded_samples']]
        assert samples
        local=np.array([s['end_pose_local_mm'] for s in samples]);margins=np.array([s['end_pose_nominal_xy_margin_mm'] for s in samples])
        before=[s for row in per[max(lo,hi-2):hi+1] for s in row['loaded_samples']]
        bouts.append(dict(start=lo,end=hi,exit_reason=bout['exit_reason'],progress_mm=bout['progress_observation_delta_mm'],loaded_ticks=len(samples),median_contact_local_mm=np.median(local,axis=0).tolist(),contact_local_p05_mm=np.percentile(local,5,axis=0).tolist(),contact_local_p95_mm=np.percentile(local,95,axis=0).tolist(),minimum_nominal_xy_margin_mm=margins.min(axis=0).tolist(),median_nominal_xy_margin_mm=np.median(margins,axis=0).tolist(),pose_reference_max_difference_mm=max(s['pose_reference_difference_mm'] for s in samples),last_three_actions_median_contact_local_mm=np.median([s['end_pose_local_mm'] for s in before],axis=0).tolist() if before else None,observed_yaw_start_deg=float(np.degrees(Rotation.from_quat(quat[lo]).as_euler('xyz')[2])),observed_yaw_end_deg=float(np.degrees(Rotation.from_quat(quat[hi]).as_euler('xyz')[2]))))
    outrows[version]=dict(nominal_box_size_m=size.tolist(),body_index=body,bouts=bouts,per_action=per)
for p,h in sources.items():assert sha(p)==h,p
sources[str(Path(__file__).resolve())]=sha(__file__)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,results=outrows,source_sha256=sources,limitations=['Absolute vertical-force-weighted wrist/box contact centroid, not a signed center of pressure or net tipping moment.','Start/end body poses bracket timing sensitivity; contact geometry need not be simultaneous with recorded end pose.','Bounds use frozen nominal box size; margin is descriptive, not a new collision or task gate.','Original .05N contact filter used descriptively, with every1200 action retained; no training labels changed.','Selected wrist assembly can include forearm shapes.'],training_ready=False)
dest=W/'front_box_trailing_physical_r2/REAR_BOX_CONTACT_LOCATIONS_V1.json'
with dest.open('x') as f:json.dump(report,f,indent=2)
print(json.dumps({v:r['bouts'] for v,r in outrows.items()},indent=2))
