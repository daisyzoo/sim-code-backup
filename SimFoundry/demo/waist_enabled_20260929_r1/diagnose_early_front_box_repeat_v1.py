"""Read-only repeat comparison: front-box task does not select rear early-edge.
Descriptive divergence only; no claim that a specific numerical subsystem caused
it, no success/admission inference, and actual visual review remains pending.
"""
from pathlib import Path
import json,hashlib,datetime
import numpy as np
W=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={}
def read(p):sources[str(p)]=sha(p);return json.loads(p.read_text())
def arr(p,keys):
 sources[str(p)]=sha(p)
 with np.load(p) as z:return {k:z[k].copy() for k in keys}
runs=['front_box_trailing_physical_r2','rear_early_edge_physical_r1'];episodes=[W/r/'case_840020/layout_840020_push_box_to_bin' for r in runs];data=[]
for ep in episodes:
 quality=read(ep/'quality.json');assert quality['frames']==1200
 raw=arr(ep/'raw.npz',['q','action','collect_meta']);meta=json.loads(str(raw['collect_meta']));trace=arr(ep/'trace.npz',['box','mailer']);fr=read(ep/'frontal_bypass.json');pressure=read(ep/'peak_load_updates.json')['rows'];args=read(ep.parent/'provenance.json')['args'];data.append(dict(quality=quality,raw=raw,meta=meta,trace=trace,fr=fr,pressure=pressure,args=args))
a,b=data;assert b['meta']['rear_early_edge_selected'] is False and b['meta']['rear_early_edge_candidate_selected_frames']==0;assert 'rear_early_edge' not in b['fr']['plan']
assert all('early_edge' not in r.get('rear_joint_xy_progress',{}) for r in b['fr']['rows'])
args_diff={k:[a['args'].get(k),b['args'].get(k)] for k in a['args'].keys()|b['args'].keys() if a['args'].get(k)!=b['args'].get(k)}
allowed={'out_dir','rear_early_edge','front_box_trailing_landing'};assert set(args_diff)<=allowed,args_diff
thresholds=[0.,1e-7,1e-6,1e-4,1e-3,1e-2]
def difference(x,y):
 assert x.shape==y.shape;delta=np.max(np.abs(np.asarray(x,float)-np.asarray(y,float)).reshape(len(x),-1),axis=1)
 return dict(initial_max_difference=float(delta[0]),max_difference=float(max(delta)),first_step_above={str(t):int(np.flatnonzero(delta>t)[0]) if np.any(delta>t) else None for t in thresholds})
diffs={k:difference(a['raw'][k][:,12:23],b['raw'][k][:,12:23]) for k in ['q','action']};diffs.update({k:difference(a['trace'][k],b['trace'][k]) for k in ['box','mailer']})
phases=[(r1['step'],r1['mode'],r2['mode']) for r1,r2 in zip(a['fr']['rows'],b['fr']['rows']) if r1['mode']!=r2['mode']]
pa={r['action_step']:r['observed_vertical_load_n'] for r in a['pressure']};pb={r['action_step']:r['observed_vertical_load_n'] for r in b['pressure']};force=[dict(step=t,parent_n=pa[t],new_n=pb[t],difference_n=abs(pa[t]-pb[t])) for t in sorted(pa.keys()&pb.keys()) if abs(pa[t]-pb[t])>1e-5]
rows=[dict(run=run,passed=d['quality']['passed'],progress_mm=1000*d['quality']['metrics']['target_final_progress_m'],non_target_max_xy_mm=1000*d['quality']['metrics']['mailer_max_xy_m']) for run,d in zip(runs,data)]
sources[str(Path(__file__))]=sha(__file__)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,episodes=rows,rear_early_edge_selected=False,rear_early_edge_applied_frames=0,argument_differences=args_diff,stream_differences=diffs,first_phase_difference=phases[0] if phases else None,phase_difference_count=len(phases),first_force_difference_over_1e5_n=force[0] if force else None,force_difference_frames=len(force),source_sha256=sources,actual_visual_review_pending=True,cause_established=False,training_ready=False)
with (W/'rear_early_edge_physical_r1/FRONT_BOX_REPEAT_DIVERGENCE_V1.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps({k:v for k,v in out.items() if k not in ['source_sha256','scope']}))
