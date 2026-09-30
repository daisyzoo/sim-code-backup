#!/usr/bin/env python3
"""Audit isolated shared-preparation diagnostics; never authorize training export."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np

def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 if a.out.exists():raise FileExistsError(a.out)
 protocol=json.loads((a.root/'DIAGNOSTIC_PROTOCOL.json').read_text());rows=[];qprefix=[];aprefix=[]
 for item in protocol['layouts']:
  f=Path(item['path']);assert hashlib.sha256(f.read_bytes()).hexdigest()==item['sha256'];layout=json.loads(f.read_text());lid=layout['layout_id'];case=a.root/f'case_{lid}';files=sorted(case.glob('layout_*/raw.npz'));assert len(files)==2
  tasks=set()
  for raw in files:
   with np.load(raw,allow_pickle=False) as z:
    q=z['q'];act=z['action'];task=str(z['task_id'].item());meta=json.loads(str(z['collect_meta'].item()))
    assert len(q)==len(act)==160 and task in {'push_box_to_bin','nudge_mailer_to_bin'};tasks.add(task)
    assert np.abs(q[0,12:23]).max()<1e-4 and np.abs(act[0,12:23]).max()<1e-4 and np.abs(act[:,12]).max()<1e-4
    assert meta['collection_role']=='diagnostic' and meta['assist_frames']==0 and not meta['push_assist'] and meta['shared_preparation_frames']==20
    assert meta['shared_preparation_source_sha256']==protocol['source_collector_sha256']
    expected=(.5-.5*np.cos(np.pi*np.arange(20)/19))[:,None]*np.array(protocol['target_q'])[None,:]
    assert np.max(np.abs(act[:20,13:23]-expected))<1e-6
    qprefix.append(q[:20,12:23]);aprefix.append(act[:20,12:23])
   quality=json.loads((raw.parent/'quality.json').read_text());trace=np.load(raw.parent/'trace.npz');target='box' if task=='push_box_to_bin' else 'mailer';sign=-1 if target=='box' else 1
   stability={k:float(np.linalg.norm(trace[k][:20,:2]-trace[k][0,:2],axis=1).max()) for k in ['box','mailer']};assert max(stability.values())<1e-5
   rows.append({'layout_id':lid,'geometry_group':layout['geometry_group'],'task':task,'passed':quality['passed'],'reasons':quality['reasons'],'target_final10_min_signed_y_m':float(np.min(sign*trace[target][-10:,1])),'target_zone_margin_m':float(np.min(sign*trace[target][-10:,1])-.20),'target_progress_m':quality['metrics']['target_final_progress_m'],'first20_object_xy_motion_m':stability,'raw':str(raw.resolve()),'raw_sha256':hashlib.sha256(raw.read_bytes()).hexdigest()})
  assert len(tasks)==2
 assert len(rows)==protocol['total_episodes']
 qs=max(float(np.abs(q-qprefix[0]).max()) for q in qprefix);acts=max(float(np.abs(q-aprefix[0]).max()) for q in aprefix);assert qs<1e-5 and acts<1e-6
 groups={g:[x for x in rows if x['geometry_group']==g] for g in {x['geometry_group'] for x in rows}};assert all(len(v)==4 for v in groups.values())
 result={'passed_numeric':sum(x['passed'] for x in rows),'total':len(rows),'complete_groups_passed':sum(all(x['passed'] for x in v) for v in groups.values()),'complete_groups_total':len(groups),'first20_q_max_difference_rad':qs,'first20_action_max_difference_rad':acts,'initial_zero_waist_zero_assist_zero_verified':True,'rows':rows,'training_ready':False,'visual_review':'required separately','limitations':'Same known training geometries. Numeric physical feasibility only; does not establish learned behavior or final independent generalization.'}
 a.out.write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2))
if __name__=='__main__':main()
