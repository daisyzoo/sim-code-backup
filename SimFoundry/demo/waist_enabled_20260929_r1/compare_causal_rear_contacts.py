"""Closed rear episodes: original quality, actual handover and loaded push bouts."""
from pathlib import Path
import json,hashlib,collections
import numpy as np
w=Path(__file__).resolve().parent;reports=[];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for run in ['front_cop_route_axis_groups_r1','region_causal_response_groups_r1']:
 for cid,task in [(840001,'push_box_to_bin'),(840004,'nudge_mailer_to_bin')]:
  ep=w/run/f'case_{cid}/layout_{cid}_{task}';log=json.loads((ep/'frontal_bypass.json').read_text());rows=log['rows'];region=json.loads((ep/'region_approach.json').read_text())['rows'];key='box' if task=='push_box_to_bin' else 'mailer';direction=-1 if key=='box' else 1
  with np.load(ep/'trace.npz') as z:xyz=z[key].astype(float)
  bouts=[];last=None;events=[];last_recontact=0
  for r in rows:
   if r.get('recontacts',0)>last_recontact:events.append(dict(step=r['step'],count=r['recontacts'],reason=r.get('last_recontact_reason')));last_recontact=r['recontacts']
   if r['mode']=='top_push':
    if last is None or r['step']!=last+1:bouts.append(dict(start=r['step'],end=r['step'],steps=0,loaded_steps=0,loads=[]))
    b=bouts[-1];b['end']=r['step'];b['steps']+=1;load=r.get('contact_load',{}).get('observed_vertical_load_n',0);b['loads'].append(load);b['loaded_steps']+=int(load>=.2);last=r['step']
   else:last=None
  for b in bouts:
   b['observed_progress_mm']=float(direction*(xyz[min(b['end']+1,len(xyz)-1),1]-xyz[b['start'],1])*1000);b['median_recorded_previous_vertical_load_n']=float(np.median(b.pop('loads')))
  quality=json.loads((ep/'quality.json').read_text());report=dict(run=run,episode=ep.name,quality=quality,handover_steps=[r['step'] for r in region if r['solver'] and r['solver'].get('handover')],mode_counts=dict(collections.Counter(r['mode'] for r in rows)),recontact_events=events,push_bouts=bouts,loaded_push_steps=sum(b['loaded_steps'] for b in bouts),raw_sha256=sha(ep/'raw.npz'),source_sha256={f:sha(ep/f) for f in ['frontal_bypass.json','region_approach.json','trace.npz','quality.json']});reports.append(report)
  print(run,ep.name,'handover',report['handover_steps'],'loaded',report['loaded_push_steps'],'bouts',[(b['steps'],b['loaded_steps'],round(b['observed_progress_mm'],3)) for b in bouts],'recontacts',len(events),flush=True)
out=dict(rows=reports,script_sha256=sha(Path(__file__)),scope='Complete real rear box/bag in parent and child. Bouts use recorded top_push modes and previous last-substep vertical load>=0.2N; not full-interval integrated force or exclusive causal attribution. Raw task failures remain failures.',training_ready=False);(w/'region_causal_response_groups_r1/REAR_CONTACT_COMPARISON.json').write_text(json.dumps(out,indent=2))
