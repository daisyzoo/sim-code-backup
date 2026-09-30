#!/usr/bin/env python3
"""Prepare fresh pilot layouts only after complete short-first RGB feasibility."""
import argparse,hashlib,json,sys,tempfile
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from simfoundry.data.diverse_layouts import validate_diagnostic_layout
from simfoundry.data.short_first_twopass_protocol import EXPERT,validate_twopass_contract
p=argparse.ArgumentParser();p.add_argument('--evidence',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--seed',type=int,default=2026092937);p.add_argument('--layout-start',type=int,default=70000);a=p.parse_args();evidence=a.evidence.resolve();out=a.out.resolve()
if out.exists():raise FileExistsError(out)
result=json.loads((evidence/'RESULT.json').read_text())
if not result.get('complete'):raise ValueError('Feasibility batch is incomplete; no pilot artifacts created')
audit=json.loads((evidence/'FINAL_AUDIT.json').read_text());review=json.loads((evidence/'visual_review.json').read_text());protocol=json.loads((evidence/'PROTOCOL.json').read_text())
if not audit.get('complete') or not review.get('complete') or not review.get('reviewed') or not all(g['numeric_and_pair_passed'] for g in audit['groups']):raise ValueError('Feasibility failed or visual review incomplete')
if protocol.get('first_far_exit_y')!=.28:raise ValueError('Wrong feasibility expert')
base=json.loads((ROOT/'demo/natural_coverage24_20260929_r1/layouts/layout_66000.json').read_text());rng=np.random.default_rng(a.seed);layouts=[];groups=[]
existing=[]
for group in protocol['groups']:
 for c in group['layouts']:
  d=json.loads(Path(c['path']).read_text());existing.append(np.array(sorted([d['box_xyz'][:2],d['mailer_xyz'][:2]])))
for g in range(8):
 kind='front_back' if g<2 else 'positive_diagonal' if g%2==0 else 'negative_diagonal';split='train' if g<6 else 'validation' if g==6 else 'test';name=f'short_first_fresh_{a.seed}_{g}'
 for attempt in range(1000):
  cy=rng.uniform(-.012,.012);dy=rng.uniform(-.005,.005) if g<2 else (1 if g%2==0 else -1)*rng.uniform(.01,.025)
  near=[float(base['box_xyz'][0]+rng.uniform(-.003,.003)),float(cy-dy/2)];far=[float(base['mailer_xyz'][0]+rng.uniform(-.003,.003)),float(cy+dy/2)]
  slots=np.array(sorted([near,far]))
  if any(np.max(np.abs(slots-x))<.001 for x in existing):continue
  pair=[]
  for j in range(2):
   b,m=(near,far) if j==0 else (far,near);lid=a.layout_start+g*2+j
   pair.append(dict(layout_id=lid,seed=a.seed,geometry_group=name,assignment='normal' if j==0 else 'swapped',box_xyz=b+[.7725],mailer_xyz=m+[.77],box_yaw=base['box_yaw'],mailer_yaw=base['mailer_yaw']))
  try:
   for d in pair:validate_diagnostic_layout(d,d['layout_id'])
  except ValueError:continue
  break
 else:raise RuntimeError('Could not sample fresh valid geometry')
 existing.append(slots);layouts.extend(pair);groups.append(dict(group=name,split=split,kind=kind,layout_ids=[d['layout_id'] for d in pair],sampling_attempts=attempt+1))
collector=ROOT/'scripts/collect_short_first_twopass_pilot.py'
contract=dict(version=1,approved_for_pilot=True,expert=EXPERT,layouts=layouts,groups=groups,pilot_collector=str(collector),pilot_collector_sha256=hashlib.sha256(collector.read_bytes()).hexdigest(),feasibility=[dict(root=str(evidence),audit_sha256=hashlib.sha256((evidence/'FINAL_AUDIT.json').read_bytes()).hexdigest(),visual_review_sha256=hashlib.sha256((evidence/'visual_review.json').read_bytes()).hexdigest(),protocol_sha256=hashlib.sha256((evidence/'PROTOCOL.json').read_bytes()).hexdigest())],scope='Fresh paired pilot in verified local position distribution; fixed canonical yaw. Test group remains excluded from training. Broad geometry/model generalization remains unproven.',training_ready=False)
# Validate actual bound evidence and every complete geometry pair before publishing a contract.
with tempfile.TemporaryDirectory(prefix='short_first_contract_') as td:
 temp=Path(td)/'candidate.json';temp.write_text(json.dumps(contract,indent=2));validate_twopass_contract(temp,layout_id=layouts[0]['layout_id'],steps=320);payload=temp.read_bytes()
out.mkdir();(out/'twopass_pilot_contract.json').write_bytes(payload);(out/'SPLIT.json').write_text(json.dumps(dict(groups=groups,frozen_before_collection=True),indent=2));(out/'PROTOCOL.json').write_text(json.dumps(dict(contract=str(out/'twopass_pilot_contract.json'),contract_sha256=hashlib.sha256(payload).hexdigest(),collector=str(collector),collector_sha256=contract['pilot_collector_sha256'],groups=groups,training_ready=False,goal_complete=False),indent=2));(out/'STATUS.json').write_text(json.dumps(dict(status='fresh_pilot_prepared_not_collected',training_ready=False),indent=2));print('Prepared16 fresh layouts/8groups/32tasks; no trajectories collected')
