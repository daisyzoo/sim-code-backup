#!/usr/bin/env python3
import json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from simfoundry.data.pi05_rpc import request
out=ROOT/'demo/search_failure_rtx_20260929_r1';protocol=json.loads((out/'PROTOCOL.json').read_text())
for case in protocol['cases']:
 lid=case['layout_id'];server_out=out/f'server_{lid}';port=None
 with (out/f'server_{lid}.log').open('w') as log:
  server=subprocess.Popen([sys.executable,str(ROOT/'scripts/frozen_action_replay_server.py'),'--manifest',case['manifest'],'--out',str(server_out)],stdout=log,stderr=subprocess.STDOUT)
  try:
   for _ in range(150):
    if (server_out/'READY.json').exists():port=json.loads((server_out/'READY.json').read_text())['port'];break
    if server.poll() is not None:raise RuntimeError('Replay server exited')
    time.sleep(.1)
   if port is None:raise RuntimeError('Replay server readiness timeout')
   command=['./isaaclab.sh','-p',str(ROOT/'scripts/collect_paired_sorting.py'),'--device','cuda','--viz','none','--newton-contacts','--role','diagnostic','--layout-start',str(lid),'--layouts','1','--wait-episodes','0','--steps','160','--diagnostic-layout-json',case['layout'],'--policy-port',str(port),'--eval-seed','0','--horizon','10','--policy-max-action-step','0','--out-dir',str(out/f'case_{lid}')]
   with (out/f'case_{lid}.log').open('w') as simlog:result=subprocess.run(command,cwd=ROOT.parent/'IsaacLab',stdout=simlog,stderr=subprocess.STDOUT,timeout=300)
   if result.returncode:raise RuntimeError(f'Collector exit {result.returncode}; inspect saved log')
   print('COMPLETE',lid,flush=True)
  finally:
   if server.poll() is None:
    if port is not None:request('127.0.0.1',port,{'cmd':'shutdown'})
    else:server.terminate()
    server.wait(timeout=20)
(out/'STATUS.json').write_text(json.dumps(dict(status='replay_complete_pending_integrity_and_actual_visual_review',training_ready=False,goal_complete=False),indent=2))
