#!/usr/bin/env python3
import json,subprocess,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'demo/frontback_inner_group_rtx_20260929_r2';p=json.loads((out/'PROTOCOL.json').read_text());script=ROOT/'scripts/collect_far_recontact_lower_diagnostic.py'
for path,sha in json.loads((out/'SOURCE.json').read_text()).items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==sha
rows=[]
for case in p['cases']:
 name=f"case_{case['layout_id']}_{case['condition']}";dest=out/name
 cmd=['./isaaclab.sh','-p',str(script),'--device','cuda','--viz','none','--newton-contacts','--role','diagnostic','--layout-start',str(case['layout_id']),'--layouts','1','--wait-episodes','0','--steps','320','--diagnostic-layout-json',case['layout'],'--out-dir',str(dest),'--first-pass',case['source'],'--first-pass-sha',case['sha256'],'--diagnostic-task',case['task'],'--second-pass',case['condition'],'--second-contact-z-offset',str(case['height_offset_m'])]
 with (out/(name+'.log')).open('w') as log:result=subprocess.run(cmd,cwd=ROOT.parent/'IsaacLab',stdout=log,stderr=subprocess.STDOUT,timeout=600)
 quality=dest/f"layout_{case['layout_id']}_{case['task']}"/'quality.json'
 if not quality.exists():raise RuntimeError(f'Runtime failure before quality: {name}, exit{result.returncode}')
 q=json.loads(quality.read_text());assert q['frames']==320
 rows.append(dict(case=case,returncode=result.returncode,quality=q,training_ready=False));(out/'RESULT.json').write_text(json.dumps(rows,indent=2));print('COMPLETE',name,'passed',q['passed'],flush=True)
(out/'STATUS.json').write_text(json.dumps(dict(status='completed_pending_integrity_and_visual_review',training_ready=False,goal_complete=False),indent=2))
