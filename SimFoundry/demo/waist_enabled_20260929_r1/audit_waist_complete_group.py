"""Recompute complete waist-enabled expert feasibility; never promote diagnostics."""
from pathlib import Path
from types import SimpleNamespace
import sys,json,hashlib,zipfile
import numpy as np
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root.parents[1]))
from simfoundry.data.waist_group_audit import validate_complete_swap_layouts
from simfoundry.data.diverse_layouts import validate_diagnostic_layout
from simfoundry.data.paired_sorting import audit_rollout,audit_pair
from simfoundry.data.search_reward import terminal_search_scores
from simfoundry.data.prompts import PAIRED_SORTING_PROMPTS


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def first_rgb(path):
    # Read the first image directly from the NPY stream; no full-video array.
    with zipfile.ZipFile(path) as archive,archive.open('rgb.npy') as f:
        version=np.lib.format.read_magic(f)
        reader={(1,0):np.lib.format.read_array_header_1_0,(2,0):np.lib.format.read_array_header_2_0}.get(version)
        if reader is None:raise ValueError('Unsupported RGB NPY header')
        shape,fortran,dtype=reader(f)
        if fortran or len(shape)!=4 or shape[1]!=3 or dtype!=np.dtype('uint8'):
            raise ValueError('Unsupported RGB storage shape/order/type')
        count=int(np.prod(shape[1:]));data=f.read(count)
        if len(data)!=count:raise ValueError('Truncated first RGB')
        return np.frombuffer(data,dtype=dtype).reshape((1,*shape[1:])),shape[0]


run=Path(sys.argv[1]).resolve()
status=json.loads((run/'STATUS.json').read_text())
if status['stage']!='numeric_complete_actual_visual_review_pending':raise ValueError('Run is not terminal')
protocol=json.loads((run/'PROTOCOL.json').read_text())
review=json.loads((run/'RESULT.json').read_text()) if (run/'RESULT.json').exists() else {'rows':[]}
errors=[];records=[];pairs=[];layouts={};loaded={}
for name,sha in protocol['source_sha256'].items():
    if digest(Path(name))!=sha:errors.append('Frozen source mismatch: '+name)
for ep in sorted(run.glob('case_*/layout_*')):
    path=ep/'raw.npz'
    if not path.exists():continue
    with np.load(path) as z:
        q=z['q'];action=z['action'];meta=json.loads(str(z['collect_meta']));task=str(z['task_id']);instruction=str(z['instruction'])
    if task not in ('push_box_to_bin','nudge_mailer_to_bin'):raise ValueError('Unexpected pushing-group task')
    if q.shape!=(protocol['frames'],23) or action.shape!=q.shape:raise ValueError('State/action shape mismatch')
    if instruction!=PAIRED_SORTING_PROMPTS[task]:raise ValueError('Task instruction mismatch')
    if (meta.get('assist_frames')!=0 or meta.get('push_assist') is not False
        or meta.get('motion_protocol')!='waist_yaw_enabled_v1'
        or meta.get('idle_diagnostic') or meta.get('wait_force_n') or meta.get('push_force_n')
        or meta.get('collision_pipeline')!='newton'):
        raise ValueError('Protocol/no-assistance evidence mismatch')
    settings=json.loads((ep.parent/'provenance.json').read_text())['args']
    for k in ('waist_limit_rad','waist_wait_tolerance_rad','environment_seed','motion_protocol'):
        if meta[k]!=settings[k]:raise ValueError('Recorded setting differs: '+k)
    layout=meta['layout'];identifier=meta['layout_id'];validate_diagnostic_layout(layout,identifier)
    if identifier in layouts and layouts[identifier]!=layout:raise ValueError('Pair layout metadata differs')
    layouts[identifier]=layout
    with np.load(ep/'trace.npz') as tr,np.load(ep/'parcel_orientation.npz') as ori:
        trace={k:tr[k] for k in tr.files};orientation={k:ori[k] for k in ori.files}
        report=audit_rollout(task,q,action,trace,motion_protocol='waist_yaw_enabled_v1',waist_limit_rad=meta['waist_limit_rad'],waist_wait_tolerance_rad=meta['waist_wait_tolerance_rad'])
        _,fits=terminal_search_scores([report],[0 if task=='push_box_to_bin' else 1],{k:v[:,None] for k,v in trace.items()},{k:v[:,None] for k,v in orientation.items()})
    saved=json.loads((ep/'quality.json').read_text());rawhash=digest(path)
    visual=next((r for r in review['rows'] if r['episode']==ep.name),{})
    visual_bound=(visual.get('raw_sha256')==rawhash and str(visual.get('actual_sampled_visual_review','')).startswith('completed'))
    if not report['passed'] or not fits[0]['search_success'] or not saved['passed']:errors.append(ep.name+': task/pose failed')
    if not visual_bound:errors.append(ep.name+': actual visual review pending or hash unbound')
    rgb,frames=first_rgb(path)
    if frames!=len(q):raise ValueError('RGB/state frame count differs')
    loaded.setdefault(identifier,[]).append(SimpleNamespace(q=q,rgb=rgb,collect_meta=meta,task_id=task,instruction=instruction))
    records.append(dict(episode=ep.name,path=str(ep),layout=layout,task_id=task,original_audit=report,pose=fits[0],actual_visual_review_bound=visual_bound,source_role=meta.get('collection_role'),raw_sha256=rawhash,trace_sha256=digest(ep/'trace.npz'),orientation_sha256=digest(ep/'parcel_orientation.npz'),training_ready=False))
for identifier,eps in loaded.items():
    if len(eps)!=2 or {e.task_id for e in eps}!={'push_box_to_bin','nudge_mailer_to_bin'}:
        errors.append(f'{identifier}: missing or duplicate tasks');continue
    result=audit_pair(*eps);pairs.append(dict(layout_id=identifier,**result))
    if not result['passed']:errors.append(f'{identifier}: initial pair/prompt failed')
try:groups=validate_complete_swap_layouts(list(layouts.values()))
except ValueError as exc:groups={};errors.append(str(exc))
expected_ids=set(protocol.get('layout_ids',[protocol.get('layout_id')]))
if set(layouts)!=expected_ids:errors.append('Protocol layout coverage mismatch')
result=dict(complete_group_feasibility_passed=bool(records and groups and not errors),errors=errors,groups=groups,pairs=pairs,rows=records,training_ready=False,scope='Recomputed original task/pose gates, zero start, no-assist metadata, exact source hashes, same-scene paired initial RGB/state/poses/prompts and complete fixed-slot category exchanges. Actual sampled review must bind raw hash. This is expert feasibility only, not pilot admission, all-frame visual/collision certification, training or h10 policy success.')
(run/'COMPLETE_GROUP_READINESS.json').write_text(json.dumps(result,indent=2))
print(json.dumps({k:v for k,v in result.items() if k not in ('rows','scope')},indent=2))
