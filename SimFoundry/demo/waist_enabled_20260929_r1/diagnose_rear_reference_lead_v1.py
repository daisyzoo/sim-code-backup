"""Check incremental reference protection versus accumulated tracking lead.

Uses recorded nominal Cartesian references, not counterfactual physics. Later
joint guards may further modify commands. No production change or admission.
"""
from pathlib import Path
import datetime
import hashlib
import json
import numpy as np
from scipy.spatial.transform import Rotation

W=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
sources={};results={}
for version in ['r1','r2']:
    ep=W/('front_box_trailing_physical_'+version)/'case_840023/layout_840023_push_box_to_bin'
    files=[ep/'frontal_bypass.json',ep/'trace.npz',ep/'parcel_orientation.npz']
    for p in files:sources[str(p)]=sha(p)
    fr=json.loads(files[0].read_text())['rows']
    with np.load(files[1]) as z:xyz=z['box'].copy()
    with np.load(files[2]) as z:quat=z['box'].copy()
    records=[]
    for row in fr:
        g=row.get('rear_joint_xy_progress',{})
        if not g.get('override'):continue
        assert g['reason']=='joint_XY_nonoutward_reference'
        t=row['step'];rot=Rotation.from_quat(quat[t]).as_matrix()
        command=np.array(g['command_xyz']);ref=np.array(row['observed_support_xyz'])
        delta=np.array(g['reference_delta_xyz_m']);local_delta=rot.T@delta
        np.testing.assert_allclose(local_delta[:2],g['projected_local_xy_delta_m'],rtol=0,atol=1e-10)
        feedback=row['rear_cop_centering'];cop=rot.T@(np.array(feedback['cop_world'])-xyz[t])
        lead=rot.T@(command-ref);axes=g['near_axes'];sign=np.sign(cop[axes])
        outward_delta=sign*local_delta[axes];outward_lead=sign*lead[axes]
        assert max(outward_delta)<=2e-10
        final_ref_lead=rot.T@(np.array(row['target_xyz'])-ref)
        records.append(dict(step=t,near_axes=axes,cop_local_mm=(cop*1000).tolist(),outward_increment_mm=(outward_delta*1000).tolist(),outward_governor_lead_mm=(outward_lead*1000).tolist(),outward_final_row_reference_lead_mm=(sign*final_ref_lead[axes]*1000).tolist(),governor_to_final_row_difference_mm=float(np.linalg.norm(np.array(row['target_xyz'])-command)*1000),scale=g['scale']))
    assert records
    results[version]=dict(applied_records=len(records),nonoutward_increment_recomputed=True,records_with_outward_governor_lead_above1mm=sum(max(r['outward_governor_lead_mm'])>1 for r in records),max_outward_governor_lead_mm=max(max(r['outward_governor_lead_mm']) for r in records),records=records)
for p,h in sources.items():assert sha(p)==h,p
sources[str(Path(__file__).resolve())]=sha(__file__)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,results=results,source_sha256=sources,limitations=['1mm is a descriptive reporting threshold, not a quality gate.','Observed COP uses controller-recorded preceding-force observation; not exact force/state synchronization.','Nonoutward increments are correctly enforced, but do not imply zero previously accumulated Cartesian lead.','A causal fix requires full guarded command generation and physical paired tests; this report does not prove reducing lead improves sorting.'],training_ready=False)
dest=W/'front_box_trailing_physical_r2/REAR_REFERENCE_LEAD_DIAGNOSIS_V1.json'
with dest.open('x') as f:json.dump(out,f,indent=2)
print(json.dumps({v:{k:x for k,x in r.items() if k!='records'} for v,r in results.items()},indent=2))
