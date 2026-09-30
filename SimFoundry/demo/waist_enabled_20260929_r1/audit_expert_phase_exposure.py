"""Frame-query exposure for diagnostics; no sampling/training change or admission."""
from pathlib import Path
import json
root=Path(__file__).resolve().parent;rows=[]
for run_name in ['frontal_top_drag_r1','frontal_top_load5_r1','frontal_top_load5_long_r1']:
 for ep in sorted((root/run_name).glob('case_*/layout_*')):
  quality=json.loads((ep/'quality.json').read_text());n=quality['frames'];log=json.loads((ep/'frontal_bypass.json').read_text())['rows'];counts={p:sum(r['mode']==p for r in log) for p in sorted({r['mode'] for r in log})}
  recover=sum(counts.get(p,0) for p in ['top_lift','top_cross','top_descend','top_press']);release=next((r['step'] for r in log if r['mode']=='top_release'),None)
  rows.append(dict(run=run_name,episode=ep.name,frames=n,first30_query_fraction=min(30,n)/n,top_approach_or_recovery_query_fraction=recover/n,top_push_query_fraction=counts.get('top_push',0)/n,phase_counts=counts,first_release_frame=release,original_numeric_passed=quality['passed']))
report=dict(rows=rows,training_ready=False,scope='Assumes uniform sampling of frame query indices. First30 is an explicit illustrative exposure bucket, not the historic startup classifier; do not compare its percentage directly with historic23.4/13.2 figures. Top approach/recovery includes initial top approach. Real future exposure also depends on dataset mixture/sampler and padded windows. No failed/diagnostic frames admitted.',next_training_requirements=['Freeze per-task and layout-group exposure, not episode counts alone.','Match startup/query-phase exposure in controlled training comparison.','Use full successful trajectories; do not cut out failed recovery events and join discontinuous actions.','Compute arm10-relative plus waist-absolute stats from admitted training-only valid h10 labels; exclude terminal padding.'])
(root/'EXPERT_PHASE_EXPOSURE.json').write_text(json.dumps(report,indent=2))
for r in rows:print(r['run'],r['episode'],r['first30_query_fraction'],r['top_approach_or_recovery_query_fraction'])
