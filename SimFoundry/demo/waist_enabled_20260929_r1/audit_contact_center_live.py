"""Independent force/FK reconstruction of initial contact center and reference switch.
Does not import the controller or approve data. No physics success implied.
"""
from pathlib import Path
import json,sys,hashlib
import numpy as np
from scipy.spatial.transform import Rotation
ROOT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def measure(packet,t,mode,side,key,origin,rotation,position,normal,vertices):
    if mode!='top_press':return None
    if packet is None or packet['after_action_step']!=t-1:return None
    if np.max(abs(np.asarray(packet['post_action_pose'][key])-position))>1e-5:return None
    actor='parcel_box' if key=='box' else 'mailer';points=[];weights=[]
    for c in packet['parcel_contacts']:
        slots=[i for i,s in enumerate(c['shapes']) if '/'+actor+'/' in s]
        if len(slots)!=1 or not any(side+'_wrist' in s for s in c['shapes']):continue
        force=np.asarray(c['force_world_N'])*(1 if slots[0]==1 else -1)
        point=np.asarray(c['position_world']);assert np.isfinite(force).all() and np.isfinite(point).all()
        weight=-float(force@normal)
        if weight>.05:points.append(point);weights.append(weight)
    load=sum(weights)
    if not .3<load<30:return None
    world=np.average(points,axis=0,weights=weights);local=rotation.T@(world-origin)
    low=vertices.min(0);high=vertices.max(0)
    if np.any(local<low-.003) or np.any(local>high+.003):return None
    shift=rotation@(local-(low+high)/2);shift-=normal*(normal@shift)
    if np.linalg.norm(shift)>.08:return None
    return dict(local=local,world=world,load=load)

def audit(folder):
    p=Path(folder).resolve();side='right' if 'push_box' in p.name else 'left';key='box' if side=='right' else 'mailer'
    env={'__file__':str(ROOT/'audit_terminal_reach.py')}
    text=(ROOT/'audit_terminal_reach.py').read_text();exec(compile(text.split("p=root/'contact_x_ablation")[0],'<independent URDF>','exec'),env)
    def hand(q):
        m=np.eye(4);m[:3,3]=[.08,0,.793]
        for name,origin,axis in env['chains'][side]:
            m=m@origin
            if axis is not None:
                a=np.eye(4);a[:3,:3]=Rotation.from_rotvec(axis*(q[env['names'].index(name)] if name in env['names'] else 0.)).as_matrix();m=m@a
        return m
    geom=ROOT.parents[1]/'assets/robots/g1_hand_support_vertices.json'
    vertices=np.array(json.loads(geom.read_text())['vertices'][side]);base=(vertices.min(0)+vertices.max(0))/2
    with np.load(p/'raw.npz') as z:qs=z['q'].copy()
    with np.load(p/'trace.npz') as z:positions=z[key].copy()
    with np.load(p/'parcel_orientation.npz') as z:rotations=Rotation.from_quat(z[key]).as_matrix()
    packets={x['after_action_step']:x for x in json.loads((p/'solved_contact_forces.json').read_text())['rows']}
    frontal=json.loads((p/'frontal_bypass.json').read_text())['rows'];rows={x['step']:x for x in frontal}
    logs=json.loads((p/'contact_center_calibration.json').read_text())['rows'];assert logs
    assert [r['step'] for r in logs]==sorted(set(r['step'] for r in logs))
    projected={r['step'] for r in frontal if 'projected_support_reference' in r}
    assert {r['step'] for r in logs}==projected,'Missing/extra reference lifecycle records'
    samples=[];center=None;commit=None;last=None;observed=[];prior_mode=None
    before={}
    for r in frontal:
        before[r['step']]=prior_mode
        if r['mode'].startswith('top_'):prior_mode=r['mode']
    for log in logs:
        t=log['step'];row=rows[t];m=hand(qs[t,12:23]);normal=rotations[t,:,2]
        if before[t] is not None:assert log['mode_before_update']==before[t],(t,'mode lifecycle')
        if last is None or t!=last+1:samples=[]
        last=t
        if center is None:
            value=measure(packets.get(t-1),t,log['mode_before_update'],side,key,m[:3,3],m[:3,:3],positions[t],normal,vertices)
            if value is None:samples=[]
            else:
                samples=(samples+[value['local']])[-3:]
                assert abs(value['load']-log['normal_load_n'])<1e-5
                assert np.max(abs(value['local']-log['centroid_local']))<1e-6
            median=np.median(samples,axis=0) if samples else None
            scatter=max(np.linalg.norm(s-median) for s in samples) if samples else None
            ready=len(samples)==3 and scatter<=.001
            assert log['ready']==ready,(t,'measurement readiness')
            if samples:
                assert log['sample_count']==len(samples)
                assert np.max(abs(median-log['candidate_center_local']))<1e-6
                assert abs(scatter-log['scatter_m'])<1e-6
            if log['committed_now']:
                assert ready and row['mode']=='top_lift' and not row.get('route_stop_reason')
                assert row['last_recontact_reason']=='initial_contact_center_reposition'
                assert np.arccos(np.clip(normal[2],-1,1))<=row['tilt_recontact_threshold_rad']+1e-7
                center=median.copy();commit=t
                assert row['contact_load']['applied_z_bias_m']==0 and row['contact_load']['stored_z_bias_m']==0
                assert row['push_x_anchor_m'] is None and log['effective_top_fraction']==1.
                assert not any(k.startswith('object_relative_') for k in row)
            else:
                assert row['mode']!='top_push','Uncalibrated top push'
                if ready:assert row['mode'] not in ('top_press','top_push'),'Ready safe proposal not committed'
        else:
            assert not log['committed_now'] and not log['ready'] and log['latched']
        expected=base if center is None else center
        assert log['calibrated_after']==(center is not None)
        assert log['mode']==row['mode']
        assert np.max(abs(expected-log['reference_center_local']))<1e-6
        assert np.max(abs(expected-row['projected_support_reference']['center_local']))<1e-6
        if t==commit:
            w=vertices@m[:3,:3].T+m[:3,3];c=m[:3,:3]@center+m[:3,3];point=c+normal*((w@normal).min()-c@normal)
            assert np.max(abs(point-row['observed_support_xyz']))<1e-6
            assert np.max(abs(point[:2]-row['target_xyz'][:2]))<1e-6,'Reference switch introduced lateral command'
            assert abs(row['target_xyz'][2]-max(row['travel_height_m'],point[2]))<1e-6
        observed.append(dict(step=t,center_local=expected.tolist()))
    files=['raw.npz','trace.npz','parcel_orientation.npz','solved_contact_forces.json','frontal_bypass.json','contact_center_calibration.json']
    out=dict(passed=True,commit_step=commit,center_local=None if center is None else center.tolist(),frames=len(logs),centers=observed,source_sha256={str(p/f):sha(p/f) for f in files},geometry_sha256=sha(geom),urdf_sha256=sha(env['urdf']),auditor_sha256=sha(__file__),scope='Independent force centroid, URDF hand pose, three-sample calibration, latch and reference switch checks. Original guard precedence separately checked in staged actual state test. No full-state replay or physical success/data admission.',training_ready=False)
    (p/'CONTACT_CENTER_LIVE_AUDIT.json').write_text(json.dumps(out,indent=2));return out

if __name__=='__main__':
    d=audit(sys.argv[1]);print(json.dumps({k:v for k,v in d.items() if k not in ('centers','source_sha256')},indent=2))
