#!/usr/bin/env python3
"""Render only frozen complete screen groups; retain all failures, no admission."""
import argparse,json,hashlib,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args();out=a.root.resolve();protocol=json.loads((out/'PROTOCOL.json').read_text());script=ROOT/'scripts/collect_twopass_sorting_diagnostic.py'
assert hashlib.sha256(script.read_bytes()).hexdigest()==protocol['collector_sha256'];rows=[]
for group in protocol['groups']:
 for case in group['layouts']:
  lid=case['layout_id'];dest=out/f'case_{lid}';layout=Path(case['path']);assert hashlib.sha256(layout.read_bytes()).hexdigest()==case['sha256']
  command=['./isaaclab.sh','-p',str(script),'--device','cuda','--viz','none','--newton-contacts','--role','diagnostic','--layout-start',str(lid),'--layouts','1','--wait-episodes','0','--steps','320','--diagnostic-layout-json',str(layout),'--expert-staging-z','.92','--expert-far-contact-offset','-.11','--expert-contact-offset','-.13','--out-dir',str(dest)]
  with (out/f'case_{lid}.log').open('w') as log:result=subprocess.run(command,cwd=ROOT.parent/'IsaacLab',stdout=log,stderr=subprocess.STDOUT,timeout=600)
  reports=[]
  for task in ['push_box_to_bin','nudge_mailer_to_bin']:
   path=dest/f'layout_{lid}_{task}'/'quality.json'
   if not path.exists():raise RuntimeError(f'Missing quality for{lid}/{task}; exit{result.returncode}, inspect log')
   q=json.loads(path.read_text());assert q['frames']==320 and not q['training_ready'];reports.append(q)
  manifest=json.loads((dest/'manifest.json').read_text());assert len(manifest)==1
  rows.append(dict(group=group['group'],split=group['split'],layout_id=lid,returncode=result.returncode,reports=reports,pair=manifest[0]['pair'],training_ready=False));(out/'RESULT.json').write_text(json.dumps(dict(rows=rows,complete=False,training_ready=False),indent=2));print('COMPLETE',lid,'numeric',sum(x['passed'] for x in reports),'/2','pair',manifest[0]['pair']['passed'],flush=True)
(out/'RESULT.json').write_text(json.dumps(dict(rows=rows,complete=True,training_ready=False,goal_complete=False),indent=2))
