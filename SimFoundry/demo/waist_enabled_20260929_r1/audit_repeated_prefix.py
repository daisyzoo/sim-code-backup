"""Read-only repeatability evidence; do not attribute trajectory differences to budget alone."""
from pathlib import Path
import json,sys
import numpy as np
base=Path(sys.argv[1]).resolve();candidate=Path(sys.argv[2]).resolve();rows=[]
for ep in sorted(candidate.glob('case_*/layout_*')):
 if not (ep/'raw.npz').exists():continue
 old=next(base.glob('case_*/'+ep.name));a=np.load(old/'raw.npz');b=np.load(ep/'raw.npz');ta=np.load(old/'trace.npz');tb=np.load(ep/'trace.npz');n=min(len(a['q']),len(b['q']));target='box' if 'push_box' in ep.name else 'mailer';direction=-1 if target=='box' else 1
 def first(values,threshold):
  idx=np.flatnonzero(values>threshold);return int(idx[0]) if len(idx) else None
 qdelta=np.max(abs(a['q'][:n,12:23]-b['q'][:n,12:23]),axis=1);adelta=np.max(abs(a['action'][:n,12:23]-b['action'][:n,12:23]),axis=1);objdelta=np.linalg.norm(ta[target][:n]-tb[target][:n],axis=1)
 ma={r['step']:r['mode'] for r in json.loads((old/'frontal_bypass.json').read_text())['rows']};mb={r['step']:r['mode'] for r in json.loads((ep/'frontal_bypass.json').read_text())['rows']}
 firstmode=next((t for t in range(n) if ma.get(t)!=mb.get(t)),None)
 row=dict(episode=ep.name,common_prefix_frames=n,first_state_delta_over_1e6_rad=first(qdelta,1e-6),first_action_delta_over_1e6_rad=first(adelta,1e-6),first_action_delta_over_1e3_rad=first(adelta,.001),first_target_position_delta_over_1um=first(objdelta,1e-6),first_target_position_delta_over_1mm=first(objdelta,.001),first_mode_difference=firstmode,mode_difference_at_first=None if firstmode is None else [ma[firstmode],mb[firstmode]],initial_upper_state_equal=bool(np.array_equal(a['q'][0,12:23],b['q'][0,12:23])),initial_target_position_delta_m=float(objdelta[0]),base_progress_at_common_end_m=float(direction*(ta[target][n-1,1]-ta[target][0,1])),candidate_progress_at_common_end_m=float(direction*(tb[target][n-1,1]-tb[target][0,1])),candidate_final_progress_m=float(direction*(tb[target][-1,1]-tb[target][0,1])))
 rows.append(row);print(json.dumps(row))
pa=json.loads((base/'PROTOCOL.json').read_text());pb=json.loads((candidate/'PROTOCOL.json').read_text())
report=dict(rows=rows,source_hashes_identical=pa['source_sha256']==pb['source_sha256'],base_settings=pa['settings'],candidate_settings=pb['settings'],scope='Matched recorded prefix, not deterministic replay guarantee. Layout seed explicitly controls numpy parcel-reset RNG; collector env.reset has no explicit per-episode physics seed. Sources fixed and horizon differs, but numerical/stochastic runtime variation can change threshold crossings. First divergence and score differences do not identify a unique cause. Report equal-budget prefix separately from longer final budget.',training_ready=False)
(candidate/'REPEATED_PREFIX_AUDIT.json').write_text(json.dumps(report,indent=2))
