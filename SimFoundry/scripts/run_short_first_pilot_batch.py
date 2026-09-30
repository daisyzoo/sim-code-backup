#!/usr/bin/env python3
"""Collect fresh approved paired pilots; stop after a failed complete swap group."""
import argparse,hashlib,json,subprocess,sys,traceback
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from simfoundry.data.search_reward import terminal_search_scores
from simfoundry.data.short_first_twopass_protocol import validate_twopass_contract
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args();root=a.root.resolve();protocol=json.loads((root/'PROTOCOL.json').read_text());script=Path(protocol['collector']).resolve();contract=Path(protocol['contract']).resolve()
assert script==ROOT/'scripts/collect_short_first_twopass_pilot.py'
assert hashlib.sha256(script.read_bytes()).hexdigest()==protocol['collector_sha256']
assert hashlib.sha256(contract.read_bytes()).hexdigest()==protocol['contract_sha256']
validate_twopass_contract(contract,layout_id=protocol['groups'][0]['layout_ids'][0],steps=320)
rows=[];groups=[]
try:
 for group in protocol['groups']:
  group_rows=[]
  for lid in group['layout_ids']:
   assert hashlib.sha256(script.read_bytes()).hexdigest()==protocol['collector_sha256']
   dest=root/f'case_{lid}'
   if dest.exists():raise FileExistsError(f'Refusing to overwrite or silently retry {dest}')
   command=['./isaaclab.sh','-p',str(script),'--device','cuda','--viz','none','--newton-contacts','--role','pilot','--layout-start',str(lid),'--layouts','1','--steps','320','--twopass-pilot-contract',str(contract),'--expert-staging-z','.92','--expert-far-contact-offset','-.11','--expert-contact-offset','-.13','--out-dir',str(dest)]
   with (root/f'case_{lid}.log').open('w') as log:process=subprocess.run(command,cwd=ROOT.parent/'IsaacLab',stdout=log,stderr=subprocess.STDOUT,timeout=900)
   reports=[]
   for task in ['push_box_to_bin','nudge_mailer_to_bin']:
    ep=dest/f'layout_{lid}_{task}';quality=json.loads((ep/'quality.json').read_text())
    if quality['frames']!=320 or quality['training_ready']:raise ValueError('Incomplete or improperly released pilot')
    with np.load(ep/'trace.npz') as trace,np.load(ep/'parcel_orientation.npz') as ori:
     _,fit=terminal_search_scores([quality],[0 if task=='push_box_to_bin' else 1],{k:trace[k][:,None] for k in trace.files},{k:ori[k][:,None] for k in ori.files})
    reports.append(dict(task=task,quality=quality,fitness=fit[0],raw_sha256=hashlib.sha256((ep/'raw.npz').read_bytes()).hexdigest()))
   manifest=json.loads((dest/'manifest.json').read_text());assert len(manifest)==1
   row=dict(group=group['group'],split=group['split'],layout_id=lid,returncode=process.returncode,reports=reports,pair=manifest[0]['pair'],training_ready=False);rows.append(row);group_rows.append(row)
   (root/'RESULT.json').write_text(json.dumps(dict(rows=rows,groups=groups,complete=False,training_ready=False),indent=2));print('COLLECTED',lid,'strict',sum(r['fitness']['search_success'] for r in reports),'/2',flush=True)
  passed=all(r['pair']['passed'] and all(x['fitness']['search_success'] for x in r['reports']) for r in group_rows)
  groups.append(dict(group=group['group'],split=group['split'],passed=passed))
  (root/'RESULT.json').write_text(json.dumps(dict(rows=rows,groups=groups,complete=False,training_ready=False),indent=2))
  if not passed:raise RuntimeError('Complete pilot group failed; retain both assignments and stop without retries or release')
 (root/'RESULT.json').write_text(json.dumps(dict(rows=rows,groups=groups,complete=True,training_ready=False,goal_complete=False),indent=2));(root/'STATUS.json').write_text(json.dumps(dict(status='pilot_collected_pending_independent_audit_and_visual_review',training_ready=False),indent=2))
except BaseException:
 (root/'ERROR.json').write_text(json.dumps(dict(traceback=traceback.format_exc(),training_ready=False),indent=2));raise
