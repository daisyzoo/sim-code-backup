"""Compare first actual applied path record with bounded conservative certificate.
Read-only diagnostic of a failed source/metadata fixture, not new trajectory proof.
"""
from pathlib import Path
import sys,json,hashlib,datetime
import numpy as np
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];S=W/'staged_rear_trailing_contact_v1';sys.path[:0]=[str(S),str(W),str(ROOT)]
from joint_transport_paths import JointTransportPaths
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();ep=W/'joint_transport_physical_r1/case_840023/layout_840023_nudge_mailer_to_bin';data=json.loads((ep/'joint_transport_clearance.json').read_text());r=next(x for x in data['rows'] if x['applied']);p=r['proposal'];paths=JointTransportPaths(ROOT,S);rows=[]
for name,end in [('nominal',r['output_command']),('predicted',p['predicted_q'])]:
 old=r['paths'][name];new=paths.certify(p['current'],end,p['scene']);assert old['passed'] and new['passed'];assert [x['interval'] for x in old['leaves']]==[x['interval'] for x in new['leaves']]
 delta=np.asarray([x['lower_bounds_m'] for x in new['leaves']])-np.asarray([x['lower_bounds_m'] for x in old['leaves']]);rows.append(dict(path=name,old_keys=sorted(old),new_keys=sorted(new),same_pass_and_intervals=True,minimum_margin_delta_m=new['minimum_certified_margin_m']-old['minimum_certified_margin_m'],leaf_delta_min_m=float(delta.min()),leaf_delta_max_m=float(delta.max()),old=old,new=new))
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,failed_script='check_rear_trailing_native_front_stream_v1.py',failed_session=55283,step=r['step'],rows=rows,reason='Fixture retained old full-projection path certificates while new stage correctly requires conservative cached certificates, including1e-10 bounds and explicit cache metadata. No action/quality tolerance failure inferred.',next_action='NewV2 metadata-only fixture must independently regenerate and bind every changed path certificate, prove same accept/reject on each actual recorded context, leave original actual files untouched, and never call it new physics.',source_sha256={str(f):sha(f) for f in [Path(__file__),ep/'raw.npz',ep/'joint_transport_clearance.json',S/'joint_transport_paths.py',S/'bounded_support_paths_v1.py',W/'check_rear_trailing_native_front_stream_v1.py']},training_ready=False)
with (D/'FRONT_CERTIFICATE_FORMAT_DIAGNOSIS.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(step=r['step'],paths=[{k:v for k,v in x.items() if k not in ['old','new']} for x in rows])),flush=True)
