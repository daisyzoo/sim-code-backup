"""Observed full-episode recovery/loaded duty cycles; not predicted time savings.
Compare unchanged original gates and fixed step budget. Physics traces are inputs,
not training admission. Track actual support height as well as commanded height.
"""
from pathlib import Path
import json,hashlib,collections
import numpy as np
w=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
specs=[(run,layout,task) for run in ['front_diagonal_entry_groups_r1','micro_clearance_groups_r1'] for layout,task in [(840001,'push_box_to_bin'),(840001,'nudge_mailer_to_bin'),(840004,'nudge_mailer_to_bin')]]
out=[]
for run,layout,task in specs:
 ep=w/run/f'case_{layout}/layout_{layout}_{task}'
 if not (ep/'quality.json').exists():continue
 quality=json.loads((ep/'quality.json').read_text());assert quality['frames']==1200
 fr=json.loads((ep/'frontal_bypass.json').read_text());rows=fr['rows'];assert [r['step'] for r in rows]==list(range(1,1200))
 target='box' if task=='push_box_to_bin' else 'mailer';direction=-1 if target=='box' else 1
 with np.load(ep/'trace.npz') as tr:pos=tr[target].copy()
 ev=[];prev=0
 for i,r in enumerate(rows):
  n=r.get('recontacts',0)
  if n>prev:
   assert n==prev+1
   nxt=next((v['step'] for v in rows[i+1:] if v['mode']=='top_push'),1200)
   subset=rows[i:nxt-1]
   assert len(subset)==nxt-r['step'] and all(v.get('recontacts',0)==n for v in subset), 'Overlapping recovery events require separate accounting'
   ev.append(dict(step=r['step'],reason=r['last_recontact_reason'],next_push_step=None if nxt==1200 else nxt,recovery_frames=nxt-r['step'],modes=dict(collections.Counter(v['mode'] for v in subset)),travel_heights_m=sorted(set(v.get('travel_height_m',0) for v in subset)),max_actual_support_z_m=max(v['observed_support_xyz'][2] for v in subset),start_y_mm=float(pos[r['step'],1]*1000)))
  prev=n
 active=[r for r in rows if r['mode']=='top_push'];loaded=[r for r in active if r['contact_load']['observed_vertical_load_n']>.3]
 bouts=[];start=None
 for i,r in enumerate(rows):
  if r['mode']=='top_push' and start is None:start=i
  if start is not None and (r['mode']!='top_push' or i==len(rows)-1):
   end=i if r['mode']!='top_push' else i+1;seg=rows[start:end];lo=seg[0]['step'];hi=min(seg[-1]['step']+1,1199)
   bouts.append(dict(first=lo,last=seg[-1]['step'],frames=len(seg),loaded_frames=sum(s['contact_load']['observed_vertical_load_n']>.3 for s in seg),signed_progress_mm=float(direction*(pos[hi,1]-pos[lo,1])*1000),end_reason=r.get('last_recontact_reason') if r['mode']!='top_push' else 'horizon'));start=None
 item=dict(run=run,episode=ep.name,front=bool(fr['plan'].get('front_route_selected')),quality_passed=quality['passed'],progress_mm=quality['metrics']['target_final_progress_m']*1000,final_signed_y_mm=float(direction*pos[-1,1]*1000),modes=dict(collections.Counter(r['mode'] for r in rows)),loaded_push_frames=len(loaded),push_frames=len(active),recovery_frames=sum(e['recovery_frames'] for e in ev),recontacts=ev,bouts=bouts,source_sha256={n:sha(ep/n) for n in ['frontal_bypass.json','quality.json','trace.npz']})
 item['by_reason']={reason:dict(events=sum(e['reason']==reason for e in ev),frames=sum(e['recovery_frames'] for e in ev if e['reason']==reason)) for reason in sorted({e['reason'] for e in ev})}
 out.append(item)
result=dict(scope=__doc__,rows=out,checker_sha256=sha(Path(__file__)),training_ready=False)
(w/'CURRENT_RECOVERY_BUDGET.json').write_text(json.dumps(result,indent=2))
for r in out:print(json.dumps({k:v for k,v in r.items() if k not in ['source_sha256','recontacts','bouts']}))
