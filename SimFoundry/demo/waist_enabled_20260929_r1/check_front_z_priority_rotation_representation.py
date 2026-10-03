"""Check representation fix on full raw inputs and deliberate record corruption.
No physics or training; retains the original failed audits and first supplement.
"""
from pathlib import Path
import ast,copy,datetime,hashlib,json,math,sys
import numpy as np
W=Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W.parents[1])]
from audit_front_z_priority_rotation_representation_v2 import recorded_rotation,RuntimeGapRepresentation
from front_loaded_z_priority_episode_inputs import EpisodeInputs
from audit_front_loaded_z_priority_record import verify_record
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
Z=W/'front_z_priority_physical_r1';records=[];sources={};sample=None
for ep in sorted(Z.glob('case_*/layout_*')):
    p=ep/'parcel_orientation.npz'
    if not p.exists():continue
    prov=json.loads((ep.parent/'provenance.json').read_text());keys=[k for k in prov['source_sha256'] if k.endswith('/top_contact_bypass.py')];assert len(keys)==1
    archived=ep.parent/'source_snapshot'/keys[0];assert sha(archived)==prov['source_sha256'][keys[0]]
    tree=ast.parse(archived.read_text());fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='rotation_xyzw');ns={'math':math};exec(compile(ast.Module(body=[fn],type_ignores=[]),str(archived),'exec'),ns)
    count=0
    with np.load(p,allow_pickle=False) as z:
        for key in ['box','mailer']:
            for q in z[key]:
                r=recorded_rotation(q);assert np.array_equal(r,np.asarray(ns['rotation_xyzw'](q),float));count+=1
    records.append(dict(episode=ep.name,raw_quaternions_exact=count));sources[str(p)]=sha(p);sources[str(archived)]=sha(archived)
    if ep.name=='layout_840023_nudge_mailer_to_bin':sample=ep
assert sample is not None
e=EpisodeInputs(sample)
with np.load(sample/'parcel_orientation.npz') as z:e.R=np.array([recorded_rotation(q) for q in z[e.key]]);e.OR=np.array([recorded_rotation(q) for q in z[e.other]])
e.geometry=RuntimeGapRepresentation(e.geometry);m=next(r for r in e.read('front_loaded_z_priority.json')['rows'] if r['applied']);t=m['step'];base=e.arguments(t,m);assert verify_record(**base)['passed']
negative=[]
for label,edit in [('rotation_field',lambda a:a['metadata']['context']['target_rotation'][0].__setitem__(0,a['metadata']['context']['target_rotation'][0][0]+1e-8)),('previous_history',lambda a:a['previous_actual'].__setitem__(0,a['previous_actual'][0]+1e-4)),('actual_output',lambda a:a['output'].__setitem__(0,a['output'][0]+1e-4)),('path_gap_log',lambda a:a['metadata']['nominal_hands_non_target_paths']['left'].__setitem__('minimum_certified_gap_lower_bound_m',0.0))]:
    a=dict(base)
    for k in ['metadata','coordinate','row','expert','previous_actual','output']:a[k]=copy.deepcopy(base[k])
    edit(a)
    # Keep the duplicate coordinate log in sync: corruption must be rejected by
    # reconstruction, not merely by duplicate-log equality.
    a['coordinate']['front_loaded_z_priority']=copy.deepcopy(a['metadata'])
    try:verify_record(**a)
    except (AssertionError,ValueError):negative.append(label)
    else:raise AssertionError('Accepted corrupted '+label)
for label,q in [('wrong_dtype',np.array([0,0,0,1],float)),('nonunit',np.array([0,0,0,2],np.float32)),('nan',np.array([0,0,np.nan,1],np.float32)),('shape',np.zeros(3,np.float32))]:
    try:recorded_rotation(q)
    except ValueError:negative.append(label)
    else:raise AssertionError('Accepted '+label)
sources.update(e.sources)
for name in ['check_front_z_priority_rotation_representation.py','audit_front_z_priority_rotation_representation.py','audit_front_z_priority_rotation_representation_v2.py','audit_front_loaded_z_priority_record.py','audit_front_loaded_z_priority_applied_row.py','front_loaded_z_priority_audit_geometry.py','FRONT_Z_PRIORITY_SELF_CLEARANCE_ROTATION_PATCH.json']:sources[str(W/name)]=sha(W/name)
for p in [Path('/tmp/front_z_rotation_supplement_bag.log'),sample/'audit_front_z_priority_execution.py.log',sample/'audit_front_z_priority_stage_self_clearance.py.log']:sources[str(p)]=sha(p)
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,episodes=records,total_raw_quaternions=sum(r['raw_quaternions_exact'] for r in records),negative_cases_rejected=negative,source_sha256=sources,training_ready=False)
with (Z/'ROTATION_REPRESENTATION_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps({k:v for k,v in out.items() if k not in ['source_sha256','episodes','scope']},indent=2))
