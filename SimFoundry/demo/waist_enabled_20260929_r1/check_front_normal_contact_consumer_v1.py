"""Unchanged contact verifier on all10actual archived original conditions.
New file/source wrapper remains prospective; this is not new candidate physics.
"""
from pathlib import Path
import ast,datetime,hashlib,json,sys
import numpy as np
W=Path(__file__).resolve().parent;D=W/'front_normal_contact_consumer_r1';D.mkdir(exist_ok=False);sys.path.insert(0,str(W))
from audit_front_normal_contacts_v1 import verify_arrays
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def fn(p,name):return next(n for n in ast.parse(p.read_text()).body if isinstance(n,ast.FunctionDef) and n.name==name)
old=W/'audit_front_effective_height_r1_v1_stage_contacts.py';new=W/'audit_front_normal_contacts_v1.py'
assert ast.dump(fn(old,'verify_arrays'),include_attributes=False)==ast.dump(fn(new,'verify_arrays'),include_attributes=False)
rows=[];sources={str(p):sha(p) for p in [Path(__file__),old,new,W/'audit_front_normal_stage_contract_v1.py']}
for item in read(W/'front_cross_track_full_stream_probe_r1/CENSUS.json')['episodes']:
 ep=Path(item['episode']);meta=read(ep/'SUBSTEP_CONTACT_RECORDING.json');packets=read(ep/'solved_contact_forces.json')['rows'];n=item['frames']
 assert meta['recording_sha256']==sha(ep/'substep_contacts.npz')
 with np.load(ep/'substep_contacts.npz',allow_pickle=False) as z:r=verify_arrays({k:z[k] for k in z.files},meta,packets,n)
 rows.append(dict(episode=str(ep),**r))
 for name in ['SUBSTEP_CONTACT_RECORDING.json','substep_contacts.npz','solved_contact_forces.json']:sources[str(ep/name)]=sha(ep/name)
 print(json.dumps(dict(episode=ep.name,passed=r['passed'],frames=n)),flush=True)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,original_verifier_ast_equal=True,episodes=rows,frames=sum(r['action_intervals'] for r in rows),source_sha256=sources,prospective_wrapper_tested=False,physics_started=False,training_ready=False)
(D/'RESULT.json').write_text(json.dumps(report,indent=2));print(json.dumps(dict(passed=True,episodes=len(rows),frames=report['frames'])),flush=True)
