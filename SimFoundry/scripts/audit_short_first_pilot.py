#!/usr/bin/env python3
"""Audit fresh pilot groups independently; visual approval is a later step."""
import argparse, hashlib, json, sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from simfoundry.data.schema import load_episode
from simfoundry.data.paired_sorting import audit_pair
from simfoundry.data.short_first_pilot_audit import audit_pilot_episode
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--allow-partial',action='store_true');a=p.parse_args()
root=a.root.resolve();protocol=json.loads((root/'PROTOCOL.json').read_text());rows=[];groups=[]
assert hashlib.sha256(Path(protocol['contract']).read_bytes()).hexdigest()==protocol['contract_sha256']
for group in protocol['groups']:
    expected=[root/f'case_{lid}/layout_{lid}_{task}/quality.json' for lid in group['layout_ids'] for task in ['push_box_to_bin','nudge_mailer_to_bin']]
    if a.allow_partial and not all(x.exists() for x in expected):continue
    pairs=[]
    for lid in group['layout_ids']:
        case=root/f'case_{lid}';provenance=json.loads((case/'provenance.json').read_text());episodes=[]
        for task in ['push_box_to_bin','nudge_mailer_to_bin']:
            path=case/f'layout_{lid}_{task}/raw.npz';ep=load_episode(path)
            report=audit_pilot_episode(path,ep,provenance)
            assert report['planned_split']==group['split']
            rows.append(dict(group=group['group'],layout_id=lid,task=task,path=str(path.parent),**report,training_ready=False))
            episodes.append(SimpleNamespace(collect_meta=ep.collect_meta,rgb=ep.rgb[:1].copy(),q=ep.q[:1].copy(),task_id=ep.task_id,instruction=ep.instruction))
            del ep
        pair=audit_pair(*episodes)
        if not pair['passed']:raise ValueError(f'Pilot pair failed: {lid}: {pair}')
        pairs.append(dict(layout_id=lid,**pair))
    groups.append(dict(group=group['group'],split=group['split'],numeric_and_pair_passed=True,pairs=pairs,training_ready=False))
a.out.write_text(json.dumps(dict(rows=rows,groups=groups,complete=len(groups)==len(protocol['groups']),expected_groups=len(protocol['groups']),training_ready=False,goal_complete=False,scope='Fresh pilot numeric/source/contract/phase/geometry audits; visual review is separate.'),indent=2))
print('Independently audited',len(rows),'episodes;',len(groups),'complete groups')
