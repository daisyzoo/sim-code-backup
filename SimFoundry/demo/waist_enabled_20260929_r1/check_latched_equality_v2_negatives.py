"""Metadata correction still rejects altered task goals, actions and observations."""
from pathlib import Path
import sys,json,copy,hashlib,datetime
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path[:0]=[str(W),str(ROOT)]
from audit_rear_corridor_latched_records_v2 import RecoveryVerifier
S=W/'staged_rear_corridor_latched';ep=W/'rear_latched_physical_r1/case_840004/layout_840004_nudge_mailer_to_bin';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();audit=RecoveryVerifier(ROOT,S);t=301
r=next(x for x in json.loads((ep/'rear_corridor_recovery.json').read_text())['rows'] if x['step']==t);f=next(x for x in json.loads((ep/'frontal_bypass.json').read_text())['rows'] if x['step']==t);c=next(x for x in json.loads((ep/'coordination.json').read_text()) if x['step']==t)
with np.load(ep/'raw.npz') as z:q=z['q'][t,12:23].astype(float);u=z['action'][t,12:23].astype(float);prev=z['action'][t-1,12:23].astype(float)
with np.load(ep/'trace.npz') as z:pos={k:z[k][t].astype(float) for k in ['box','mailer']}
with np.load(ep/'parcel_orientation.npz') as z:rot={k:Rotation.from_quat(z[k][t]).as_matrix() for k in ['box','mailer']}
g=dict(target_xyz=pos['mailer'],obstacle_xyz=pos['box'],target_rotation=rot['mailer'],obstacle_rotation=rot['box'],target_size=[.15,.145,.04],obstacle_size=[.14,.09,.045],core_size=r['geometry']['core_size']);args=dict(row=f,coordinate=c,current=q,previous=prev,action=u,geometry=g);assert audit.verify(r,**args)['passed'];negative=[]
for label,change in [('wrong_recovery_error',lambda x:x['recovery']['recovery_error'].__setitem__(0,x['recovery']['recovery_error'][0]+1e-12)),('wrong_requested_x',lambda x:x['recovery'].__setitem__('requested_x_m',x['recovery']['requested_x_m']+1e-12)),('wrong_other_task_axis',lambda x:x['recovery']['recovery_error'].__setitem__(2,x['recovery']['recovery_error'][2]+1e-12)),('changed_geometry',lambda x:x['geometry']['target_xyz'].__setitem__(0,x['geometry']['target_xyz'][0]+1e-5)),('changed_action',lambda x:x['emitted_command'].__setitem__(0,x['emitted_command'][0]+1e-5)),('wrong_original_error',lambda x:x['recovery']['original_error'].__setitem__(0,x['recovery']['original_error'][0]+1e-12))]:
 bad=copy.deepcopy(r);change(bad)
 try:audit.verify(bad,**args)
 except (AssertionError,ValueError,KeyError):negative.append(label)
 else:raise AssertionError(label)
report=dict(status='complete',passed=True,checked_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_step=t,negative_checks=negative,original_max_metadata_roundoff=8.001412032943023e-17,source_sha256={str(ep/n):sha(ep/n) for n in ['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','coordination.json','rear_corridor_recovery.json']},auditor_sha256=sha(W/'audit_rear_corridor_latched_records_v2.py'),checker_sha256=sha(__file__),training_ready=False);dest=W/'REAR_LATCHED_EQUALITY_V2_NEGATIVE_CHECK.json';assert not dest.exists();dest.write_text(json.dumps(report,indent=2));print('PASSED',negative)
