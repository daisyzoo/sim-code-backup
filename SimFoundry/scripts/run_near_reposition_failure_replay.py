#!/usr/bin/env python3
from pathlib import Path
import json,hashlib,subprocess
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'demo/near_reposition_failure_rtx_20260929_r1';p=json.loads((out/'PROTOCOL.json').read_text());script=Path(p['collector']);assert hashlib.sha256(script.read_bytes()).hexdigest()==p['collector_sha256'];rows=[]
for c in p['cases']:
 lid=c['layout_id'];dest=out/f'case_{lid}'
 command=['./isaaclab.sh','-p',str(script),'--device','cuda','--viz','none','--newton-contacts','--role','diagnostic','--layout-start',str(lid),'--layouts','1','--steps','640','--diagnostic-layout-json',c['layout'],'--frozen-actions',c['source'],'--frozen-sha256',c['sha256'],'--diagnostic-task',c['task'],'--out-dir',str(dest)]
 with (out/f'case_{lid}.log').open('w') as log:r=subprocess.run(command,cwd=ROOT.parent/'IsaacLab',stdout=log,stderr=subprocess.STDOUT,timeout=900)
 quality=dest/f"layout_{lid}_{c['task']}"/'quality.json'
 if not quality.exists():raise RuntimeError(f'No quality for{lid},exit{r.returncode}')
 rows.append(dict(case=c,report=json.loads(quality.read_text()),returncode=r.returncode));(out/'RESULT.json').write_text(json.dumps(dict(rows=rows,complete=False,training_ready=False),indent=2));print('COMPLETE',lid,flush=True)
(out/'RESULT.json').write_text(json.dumps(dict(rows=rows,complete=True,training_ready=False,goal_complete=False),indent=2))
