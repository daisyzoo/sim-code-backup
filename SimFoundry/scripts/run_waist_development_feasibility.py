#!/usr/bin/env python3
"""Complete all class/task pairs on frozen development geometries; no training."""
import argparse,json,subprocess,os,sys,hashlib,time,shutil
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from simfoundry.data.search_reward import terminal_search_scores
p=argparse.ArgumentParser();p.add_argument('--manifest',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
a.out.mkdir(parents=True,exist_ok=False)
manifest=json.loads(a.manifest.read_text());layouts=manifest['rows']
# Prioritize front/back and diagonals; retain lateral/swap failures in scope.
layouts=sorted(layouts,key=lambda r:(0 if r['geometry_group'].startswith('depth') else 2 if r['geometry_group'].startswith('lateral') else 1,r['layout_id']))
script=ROOT/'scripts/collect_paired_sorting.py'
watched=[script,ROOT/'simfoundry/data/waist_coordination.py',ROOT/'simfoundry/data/bounded_ik.py',ROOT/'simfoundry/data/paired_sorting.py',ROOT/'simfoundry/data/sorting_cartesian_expert.py']
hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in watched}
shutil.copy2(a.manifest,a.out/'LAYOUT_MANIFEST.json')
settings=['--device','cuda','--viz','none','--newton-contacts','--role','diagnostic','--layouts','1','--steps','160','--motion-protocol','waist_yaw_enabled_v1','--waist-limit-rad','.65','--waist-coordinated-expert','--bounded-coupled-ik','--inactive-retract-m','.10','--expert-staging-z','.92','--expert-contact-offset','-.13','--expert-crossed-contact-offset','-.04','--expert-far-contact-offset','-.11','--expert-max-contact-x','.50']
(a.out/'PROTOCOL.json').write_text(json.dumps(dict(settings=settings,source_sha256=hashes,training_ready=False,purpose='32 development push conditions; teacher feasibility across natural geometry, not a controlled waist-only ablation or model evaluation.'),indent=2))
env=os.environ.copy();env['PATH']='/home/user/miniconda3/envs/env_isaaclab/bin:'+env['PATH'];env['CONDA_PREFIX']='/home/user/miniconda3/envs/env_isaaclab';env['OMNI_KIT_ACCEPT_EULA']='yes';env.setdefault('DISPLAY',':1')
rows=[]
try:
 for layout in layouts:
  if shutil.disk_usage(a.out).free<30*2**30:raise RuntimeError('Less than 30GiB free; stop before next episode pair')
  for path,sha in hashes.items():
   if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=sha:raise RuntimeError('Collector source changed during frozen batch')
  path=Path(layout['path']);assert hashlib.sha256(path.read_bytes()).hexdigest()==layout['sha256']
  lid=layout['layout_id'];dest=a.out/f'case_{lid}'
  (a.out/'STATUS.json').write_text(json.dumps(dict(stage='collecting_diagnostics',layout_id=lid,completed_pairs=len(rows),total_pairs=len(layouts),training_ready=False)))
  cmd=['./isaaclab.sh','-p',str(script),*settings,'--layout-start',str(lid),'--diagnostic-layout-json',str(path),'--out-dir',str(dest.resolve())]
  start=time.time()
  with (a.out/f'case_{lid}.log').open('w') as log:proc=subprocess.run(cmd,cwd=ROOT.parent/'IsaacLab',env=env,stdout=log,stderr=subprocess.STDOUT,timeout=900)
  reports=[]
  for task,tid in [('push_box_to_bin',0),('nudge_mailer_to_bin',1)]:
   ep=dest/f'layout_{lid:04d}_{task}'
   report=json.loads((ep/'quality.json').read_text())
   with np.load(ep/'trace.npz') as trace,np.load(ep/'parcel_orientation.npz') as ori:
    _,fit=terminal_search_scores([report],[tid],{k:trace[k][:,None] for k in trace.files},{k:ori[k][:,None] for k in ori.files})
   assert report['frames']==160 and not report['training_ready']
   reports.append(dict(task=task,quality=report,pose=fit[0],raw_sha256=hashlib.sha256((ep/'raw.npz').read_bytes()).hexdigest()))
  paired=json.loads((dest/'manifest.json').read_text())[0]['pair']
  rows.append(dict(layout_id=lid,geometry_group=layout['geometry_group'],assignment=layout['assignment'],seconds=time.time()-start,returncode=proc.returncode,pair=paired,reports=reports))
  groups={}
  for row in rows:groups.setdefault(row['geometry_group'],[]).append(row)
  complete_good=[g for g,rs in groups.items() if len(rs)==2 and all(r['pair']['passed'] and all(p['pose']['search_success'] for p in r['reports']) for r in rs)]
  (a.out/'RESULT.json').write_text(json.dumps(dict(rows=rows,complete_numeric_pose_groups=complete_good,actual_visual_review='pending',training_ready=False),indent=2))
  print(lid,[r['quality']['reasons'] for r in reports],'complete_groups',complete_good,flush=True)
 (a.out/'STATUS.json').write_text(json.dumps(dict(stage='numeric_pose_complete_actual_visual_review_pending',completed_pairs=len(rows),training_ready=False)))
except BaseException as exc:
 (a.out/'STATUS.json').write_text(json.dumps(dict(stage='runtime_failed',error=str(exc),completed_pairs=len(rows),training_ready=False)));raise
