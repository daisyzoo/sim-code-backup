#!/usr/bin/env python3
"""Freeze evaluation on the pilot's preassigned test geometry before model training."""
import argparse,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from simfoundry.data.short_first_twopass_protocol import validate_twopass_contract
p=argparse.ArgumentParser();p.add_argument('--pilot',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();pilot=a.pilot.resolve();out=a.out.resolve()
if out.exists():raise FileExistsError(out)
protocol=json.loads((pilot/'PROTOCOL.json').read_text());contract_path=Path(protocol['contract']);payload=contract_path.read_bytes();assert hashlib.sha256(payload).hexdigest()==protocol['contract_sha256'];contract=json.loads(payload)
assert json.loads((pilot/'SPLIT.json').read_text())['groups']==contract['groups']==protocol['groups']
tests=[g for g in contract['groups'] if g['split']=='test'];assert len(tests)==1 and len(tests[0]['layout_ids'])==2
layout_ids=tests[0]['layout_ids'];assert not set(layout_ids)&{lid for g in contract['groups'] if g['split']!='test' for lid in g['layout_ids']}
layouts=[validate_twopass_contract(contract_path,layout_id=lid,steps=320)[0] for lid in layout_ids]
out.mkdir();files=[]
for layout in layouts:
 path=out/f"layout_{layout['layout_id']}.json";path.write_text(json.dumps(layout,indent=2));files.append(dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
wait_id=73000;assert wait_id not in {d['layout_id'] for d in contract['layouts']}
report=dict(scope='fresh_short_first_test_group',horizon=10,policy_action_step_cap=0,solver_steps=10,push_steps=320,wait_steps=320,eval_seeds=[0,1,2],layout_files=files,wait_layout_id=wait_id,pilot_contract_sha256=protocol['contract_sha256'],geometry_group=tests[0]['group'],training_layout_ids=[lid for g in contract['groups'] if g['split']=='train' for lid in g['layout_ids']],comparison='Use identical layouts/seeds/320-frame budget for frozen baseline and new checkpoint. Original160-frame benchmark remains separate.',limitations='Local fixed-yaw geometry; does not establish broad layout generalization.',goal_complete=False)
(out/'heldout_protocol.json').write_text(json.dumps(report,indent=2));print('Frozen one held-out swap group,3seeds,320frames,h10,cap0,solver10')
