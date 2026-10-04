"""Compare same-seed matched rear-box condition with finite-preload unselected.
A task score change on this branch is not evidence for finite-preload efficacy.
First array divergence localizes chronology; it does not establish its cause.
"""
from pathlib import Path
import datetime,hashlib,json,sys
import numpy as np
W=Path(__file__).resolve().parent;sys.path.insert(0,str(W.parents[1]));from simfoundry.data.waist_pilot_protocol import semantic_settings
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();names=['front_corridor_midpoint_physical_r1','front_box_material_physical_r1'];eps=[W/n/'case_840023/layout_840023_push_box_to_bin' for n in names];rows=[];arrays=[];sources={}
for ep in eps:
 prov=json.loads((ep.parent/'provenance.json').read_text());fr=json.loads((ep/'frontal_bypass.json').read_text());quality=json.loads((ep/'quality.json').read_text());assert not fr['plan'].get('front_route_selected') and 'front_box_material_preload' not in fr['plan'];assert not any('front_box_material_preload' in r for r in fr['rows'])
 with np.load(ep/'raw.npz') as z:q=z['q'].copy();u=z['action'].copy();meta=json.loads(str(z['collect_meta']))
 with np.load(ep/'trace.npz') as z:tr={k:z[k].copy() for k in ['box','mailer','palm_left','palm_right']}
 assert q.shape==u.shape==(1200,23)
 arrays.append(dict(q=q,action=u,**tr));rows.append(dict(run=ep.parent.parent.name,quality_passed=quality['passed'],progress_mm=quality['metrics']['target_final_progress_m']*1000,environment_seed=prov['args']['environment_seed'],front_selected=False,finite_preload_frames=meta.get('front_box_material_preload_applied_frames',0),settings=semantic_settings(prov['args'])))
 for p in [ep/'raw.npz',ep/'trace.npz',ep/'frontal_bypass.json',ep/'quality.json',ep.parent/'provenance.json']:sources[str(p)]=sha(p)
a,b=[x['settings'] for x in rows];diff={k:[a.get(k),b.get(k)] for k in set(a)|set(b) if a.get(k)!=b.get(k)};assert diff=={'front_box_material_preload':[None,True]},diff
comparisons={}
for k in arrays[0]:
 a,b=arrays[0][k],arrays[1][k];assert a.shape==b.shape;delta=np.max(abs(a.astype(float)-b.astype(float)),axis=1)
 first={}
 for tol in [0.,1e-8,1e-6,1e-4,.001]:
  ids=np.flatnonzero(delta>tol);first[str(tol)]=None if not len(ids) else dict(step=int(ids[0]),max_abs=float(delta[ids[0]]))
 comparisons[k]=dict(first_frame_exact_equal=bool(np.array_equal(a[0],b[0])),first_above_tolerance=first,maximum_absolute_difference=float(delta.max()))
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,runs=rows,only_semantic_difference=diff,array_differences=comparisons,conclusion='Same declared seed and inactive new branch produced different outcome. Preserve both results; do not attribute rear-box success to front-box material preload. Repeated seeds/trials remain necessary before claiming robustness; exact physical/runtime source of divergence is not established by this comparison.',source_sha256=dict(sources,**{str(Path(__file__)):sha(__file__)}),training_ready=False,model_goal_achieved=False)
with (W/'front_box_material_physical_r1/UNSELECTED_REAR_BOX_VARIATION.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(runs=[{k:v for k,v in r.items() if k!='settings'} for r in rows],array_differences=comparisons),indent=2))
