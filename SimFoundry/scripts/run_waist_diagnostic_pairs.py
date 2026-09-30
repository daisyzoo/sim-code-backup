#!/usr/bin/env python3
"""Finite development comparison, no dataset release or automatic training."""
import argparse,json,os,subprocess,sys,time,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from simfoundry.data.paired_sorting import sample_layout
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
a.out.mkdir(parents=True,exist_ok=False)
rows=[]
base=sample_layout(61000)
source=ROOT/'scripts/collect_paired_sorting.py'
snapshot=a.out/'source_snapshot';snapshot.mkdir()
for path in (source,ROOT/'simfoundry/data/waist_coordination.py',ROOT/'simfoundry/data/paired_sorting.py',ROOT/'simfoundry/data/sorting_cartesian_expert.py'):
 (snapshot/path.name).write_bytes(path.read_bytes())
(a.out/'PROTOCOL.json').write_text(json.dumps(dict(steps=160,waist_limit_rad=.20,waist_command_margin_rad=.02,training_ready=False,base=base,source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in snapshot.iterdir()},purpose='Development paired comparison: fixed geometry, class swap, locked vs coupled IK. Not independent generalization test.'),indent=2))
env=os.environ.copy();env['PATH']='/home/user/miniconda3/envs/env_isaaclab/bin:'+env['PATH'];env['CONDA_PREFIX']='/home/user/miniconda3/envs/env_isaaclab';env['OMNI_KIT_ACCEPT_EULA']='yes';env.setdefault('DISPLAY',':1')
try:
 for assignment in ('normal','swapped'):
  lid=61000 if assignment=='normal' else 61001
  layout=dict(base,layout_id=lid,geometry_group='waist_dev_61000',assignment=assignment,planned_split='train')
  if assignment=='swapped':
   layout['box_xyz']=[*base['mailer_xyz'][:2],base['box_xyz'][2]]
   layout['mailer_xyz']=[*base['box_xyz'][:2],base['mailer_xyz'][2]]
  layout_file=a.out/f'{assignment}.json';layout_file.write_text(json.dumps(layout))
  for variant in ('coupled','locked'):
   name=f'{assignment}_{variant}';dest=a.out/name
   (a.out/'STATUS.json').write_text(json.dumps(dict(stage='running',case=name,completed=len(rows),training_ready=False)))
   cmd=['./isaaclab.sh','-p',str(source),'--device','cuda','--viz','none','--newton-contacts','--role','diagnostic','--layouts','1','--layout-start',str(lid),'--steps','160','--diagnostic-layout-json',str(layout_file.resolve()),'--out-dir',str(dest.resolve())]
   if variant=='coupled':cmd+=['--motion-protocol','waist_yaw_enabled_v1','--waist-coordinated-expert']
   start=time.time()
   with (a.out/f'{name}.log').open('w') as log:
    result=subprocess.run(cmd,cwd=ROOT.parent/'IsaacLab',env=env,stdout=log,stderr=subprocess.STDOUT,timeout=900)
   reports=[]
   for task in ('push_box_to_bin','nudge_mailer_to_bin'):
    ep=dest/f'layout_{lid:04d}_{task}'
    if not (ep/'quality.json').exists():raise RuntimeError(f'Incomplete runtime: {name}/{task}; see log')
    reports.append(dict(task=task,quality=json.loads((ep/'quality.json').read_text()),raw_sha256=hashlib.sha256((ep/'raw.npz').read_bytes()).hexdigest()))
   rows.append(dict(case=name,returncode=result.returncode,seconds=time.time()-start,reports=reports))
   (a.out/'RESULT.json').write_text(json.dumps(dict(rows=rows,training_ready=False),indent=2))
   print(name,[(x['task'],x['quality']['passed'],x['quality']['reasons']) for x in reports],flush=True)
 (a.out/'STATUS.json').write_text(json.dumps(dict(stage='numeric_complete_visual_review_pending',completed=len(rows),training_ready=False)))
except BaseException as exc:
 (a.out/'STATUS.json').write_text(json.dumps(dict(stage='runtime_failed',error=str(exc),completed=len(rows),training_ready=False)));raise
