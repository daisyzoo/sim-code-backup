"""Supplement only: bind float32 runtime rotation representation to raw quaternions.
Original failed reports/logs and frozen auditors are never replaced. This applies
all original record/final-guard checks, changing only reconstruction of rotation
INPUTS from normalized SciPy doubles to the actual recorded scalar arithmetic,
and the runtime matrix-to-rigid-rotation step for non-target path reporting.
Direct-matrix non-target path certification is additionally retained.
It does not change a tolerance, action, quality gate, or training admission.
"""
from pathlib import Path
import datetime,hashlib,json,math,sys
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W.parents[1])]
from front_loaded_z_priority_episode_inputs import EpisodeInputs,indexed
from front_drive_1mm_v2_stage_source_binding import verify_observation_binding
from audit_front_loaded_z_priority_record import verify_record
from audit_front_loaded_z_priority_parent import near
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def recorded_rotation(q):
    # Deliberately retain NumPy float32 scalars. Converting them to Python floats
    # before squaring/dividing implements a different recorded representation.
    q=np.asarray(q)
    if q.shape!=(4,) or q.dtype!=np.dtype('float32') or not np.isfinite(q).all():
        raise ValueError('Expected finite original float32 quaternion')
    norm=math.sqrt(sum(v*v for v in q))
    if abs(norm-1)>1e-6:raise ValueError('Quaternion not normalized within original rotation gate')
    a,b,c,d=(v/norm for v in q)
    r=np.array([[1-2*(b*b+c*c),2*(a*b-c*d),2*(a*c+b*d)],
                [2*(a*b+c*d),1-2*(a*a+c*c),2*(b*c-a*d)],
                [2*(a*c-b*d),2*(b*c+a*d),1-2*(a*a+b*b)]],dtype=float)
    if np.max(abs(r.T@r-np.eye(3)))>1e-6 or np.linalg.det(r)<=.999999:
        raise ValueError('Rotation outside original orthogonality gate')
    return r

class RuntimeGapRepresentation:
    """Independent face geometry with runtime's matrix-to-rigid-rotation step.
    The original direct-matrix path is ALSO checked separately below.
    """
    def __init__(self,original):self.original=original
    def __getattr__(self,name):return getattr(self.original,name)
    def hand_box_gap(self,poses,side,xyz,rotation,size):
        rigid=Rotation.from_matrix(rotation).as_matrix()
        return self.original.hand_box_gap(poses,side,xyz,rigid,size)

def inspect(ep,*,allow_source_fixture=False):
    ep=Path(ep).resolve();fixture=(ep.parent/'SOURCE_CONTRACT_FIXTURE.json').exists()
    assert not fixture or allow_source_fixture,'Synthetic contract fixture is not physical evidence'
    binding=verify_observation_binding(ep);e=EpisodeInputs(ep);records=indexed(e.read('front_loaded_z_priority.json')['rows'],e.n)
    assert set(records)==set(range(e.n))
    representation=[]
    if e.front['selected']:
        with np.load(ep/'parcel_orientation.npz',allow_pickle=False) as z:
            tq=z[e.key].copy();oq=z[e.other].copy()
        assert tq.shape==oq.shape==(e.n,4)
        e.R=np.array([recorded_rotation(q) for q in tq]);e.OR=np.array([recorded_rotation(q) for q in oq])
        # Independent normalized SciPy matrices remain a diagnostic; no source
        # value is patched and equality to runtime metadata is still bit exact.
        ref=Rotation.from_quat(tq).as_matrix();oref=Rotation.from_quat(oq).as_matrix()
        for t,m in records.items():
            if 'target_rotation' not in m['context']:continue
            near(m['context']['target_rotation'],e.R[t]);near(m['context']['other_rotation'],e.OR[t])
            representation.append(dict(step=t,applied=m['applied'],raw_float32_representation_exact=True,
                target_normalized_reference_difference=float(np.max(abs(e.R[t]-ref[t]))),
                other_normalized_reference_difference=float(np.max(abs(e.OR[t]-oref[t])))))
    raw_geometry=e.geometry;e.geometry=RuntimeGapRepresentation(raw_geometry)
    from front_loaded_z_priority_audit_geometry import sweep
    rows=[];dual_paths=[]
    for t in range(e.n):
        m=records[t];c=e.coords.get(t)
        if c is not None:
            assert c['front_loaded_z_priority']==m
            if m['applied']:
                assert 'unexecuted_parent_waist_target_rad' in c;near(c['waist_target_rad'],e.u[t,0])
            else:assert 'unexecuted_parent_waist_target_rad' not in c
        e.verify_actual_final_guard(t)
        rows.append(verify_record(**e.arguments(t,m)))
        if m['applied']:
            size=np.asarray(m['context']['conservative_other_size'])
            paths={side:sweep(raw_geometry,e.hand,e.q[t],e.u[t],side,e.oxy[t],e.OR[t],size) for side in ['left','right']}
            assert all(v['certified'] for v in paths.values())
            dual_paths.append(dict(step=t,original_direct_matrix_paths=paths))
    sources=dict(binding['source_sha256'],**e.sources)
    sources[str(Path(__file__))]=sha(Path(__file__))
    for name in ['audit_front_z_priority_rotation_representation_v2.py','audit_front_z_priority_rotation_representation.py','audit_front_z_priority_execution.py','front_z_priority_stage_source_binding.py','front_loaded_z_priority_episode_inputs.py','audit_front_loaded_z_priority_record.py','audit_front_loaded_z_priority_applied_row.py','audit_front_loaded_z_priority_parent.py','front_loaded_z_priority_audit_geometry.py','support_vertex_stationarity.py','audit_unloaded_wrist_prior_live.py','audit_self_clearance_task_optimality.py','screen_bag_vertical_priority_geometry.py']:
        sources[str(W/name)]=sha(W/name)
    for name in ['audit_front_z_priority_execution.py.log','audit_front_z_priority_stage_self_clearance.py.log']:
        if (ep/name).exists():sources[str(ep/name)]=sha(ep/name)
    return dict(passed=True,scope=__doc__,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        episode=ep.name,frames=e.n,applied=sum(r['applied'] for r in rows),representation_binding=representation,
        records=rows,additional_direct_matrix_paths=dual_paths,source_sha256=sources,fixture_only=fixture,physical_execution_evidence=not fixture,original_failures_retained=True,original_self_clearance_bridge_not_rerun=True,
        full_audit_closure=False,training_ready=False)

if __name__=='__main__':
    ep=Path(sys.argv[1]);out=inspect(ep)
    with (ep/'FRONT_DRIVE_1MM_V2_Z_EXECUTION_AUDIT.json').open('x') as f:json.dump(out,f,indent=2)
    print(json.dumps({k:v for k,v in out.items() if k not in ['records','representation_binding','source_sha256','scope']},indent=2))
