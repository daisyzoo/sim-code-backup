"""Measured approach errors and repeat-run prefix divergence; no thresholds changed."""
from pathlib import Path
import json,sys
import numpy as np
run=Path(sys.argv[1]).resolve();results=[]
for ep in sorted(run.glob('case_*/layout_*')):
 if not (ep/'frontal_bypass.json').exists():continue
 rows=json.loads((ep/'frontal_bypass.json').read_text())['rows'];desc=[];segments=[];backtracks=[]
 for i,r in enumerate(rows):
  if r['mode']!='top_descend':continue
  tip=np.array(r['observed_support_xyz']);surface=np.array(r['parcel_top_xyz']);err=float(max(abs(tip[:2]-surface[:2])));height=float(tip[2]-surface[2]);record=dict(step=r['step'],xy_error_m=err,height_above_surface_m=height,bias=r['approach_xy_bias_m'],recontacts=r['recontacts'])
  desc.append(record)
  if not segments or r['step']!=segments[-1][-1]['step']+1:segments.append([])
  segments[-1].append(record)
  if i and rows[i-1]['mode']=='top_press':backtracks.append(record)
 near=[r for r in desc if r['height_above_surface_m']<.025]
 summary=dict(episode=ep.name,descend_frames=len(desc),near_surface_descend_frames=len(near),near_error_bins={name:sum(lo<=r['xy_error_m']<hi for r in near) for name,lo,hi in [('under3mm',0,.003),('3to4mm',.003,.004),('4to5mm',.004,.005),('5to10mm',.005,.01),('over10mm',.01,1e6)]},press_to_descend_backtracks=backtracks,segments=[dict(first_step=s[0]['step'],last_step=s[-1]['step'],frames=len(s),xy_error_quantiles_m=np.quantile([x['xy_error_m'] for x in s],[0,.5,.9,1]).tolist(),last_height_m=s[-1]['height_above_surface_m']) for s in segments])
 results.append(summary);print(json.dumps({k:v for k,v in summary.items() if k not in ('segments','press_to_descend_backtracks')}),'backtracks',len(backtracks))
(run/'TOP_ALIGNMENT_STALL_AUDIT.json').write_text(json.dumps(dict(rows=results,scope='Actual support point vs desired parcel surface XY and height in top_descend; bins are diagnostic, not changed controller or quality tolerances. Backtracks from press need force/footprint context; this does not prove relaxed alignment is safe or a unique cause.',training_ready=False),indent=2))
