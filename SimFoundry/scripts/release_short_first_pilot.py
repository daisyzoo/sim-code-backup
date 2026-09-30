#!/usr/bin/env python3
"""Bind a fully audited, actually reviewed fresh pilot to conversion inputs."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args();root=a.root.resolve()
read=lambda path:json.loads(path.read_text())
digest=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
result=read(root/'RESULT.json')
if not result.get('complete') or (root/'ERROR.json').exists():
    raise ValueError('Pilot collection incomplete or failed; no conversion approvals written')
protocol=read(root/'PROTOCOL.json');audit=read(root/'FINAL_AUDIT.json');review=read(root/'visual_review.json')
contract_path=root/'twopass_pilot_contract.json'
if digest(contract_path)!=protocol['contract_sha256']:
    raise ValueError('Pilot contract changed')
if not audit.get('complete') or not review.get('complete') or not review.get('reviewed'):
    raise ValueError('Independent audit or actual image review incomplete')
expected={(lid,task) for g in protocol['groups'] for lid in g['layout_ids'] for task in ('push_box_to_bin','nudge_mailer_to_bin')}
rows=audit['rows']
if len(rows)!=len(expected) or {(r['layout_id'],r['task']) for r in rows}!=expected:
    raise ValueError('Independent audit does not cover all pilot tasks')
if ({g['group'] for g in audit['groups']}!={g['group'] for g in protocol['groups']}
        or len(audit['groups'])!=len(protocol['groups'])
        or not all(g['numeric_and_pair_passed'] for g in audit['groups'])):
    raise ValueError('Missing or failed complete geometry group')
if set(review['raw_sha256'])!={r['raw_sha256'] for r in rows} or review['reviewed_episodes']!=len(rows):
    raise ValueError('Image review does not cover exact audited raw files')
for record in review['source_reviews']:
    path=Path(record['path'])
    if digest(path)!=record['sha256'] or read(path).get('reviewed') is not True:
        raise ValueError('Changed actual image-review record')
prepared=[];sources=[];validation=[];test=[]
for group in protocol['groups']:
    for lid in group['layout_ids']:
        case=root/f'case_{lid}'
        if read(case/'STATUS.json')['status']!='numeric_pass_visual_review_pending':
            raise ValueError('Collector case did not complete normally')
        if digest(case/'twopass_pilot_contract.json')!=protocol['contract_sha256']:
            raise ValueError('Case contract differs from frozen pilot')
        selected=[r for r in rows if r['layout_id']==lid];episodes={}
        for row in selected:
            path=case/f"layout_{lid}_{row['task']}/raw.npz"
            if digest(path)!=row['raw_sha256'] or not row['fitness']['search_success'] or row['planned_split']!=group['split']:
                raise ValueError('Changed or failed trajectory/split')
            episodes[str(path.relative_to(case))]=row['raw_sha256']
        if len(episodes)!=2:raise ValueError('Incomplete paired case')
        output=case/'review.json'
        if output.exists():raise FileExistsError(f'Refusing to overwrite review approval: {output}')
        prepared.append((output,dict(approved=True,method='Actual five-keyframe review of each episode plus independent zero-start/source/contract/phase/original/pair/full-pose audits. Sparse keyframes are not full-video review.',episodes=episodes,planned_split=group['split'],source_image_review=str(root/f'review_layout_{lid}/visual_review.json'),full_pilot_audit_sha256=digest(root/'FINAL_AUDIT.json'),training_allowed=group['split']!='test',training_ready=False)))
        if group['split']=='test':test.append(lid)
        else:
            sources.append(str(case))
            if group['split']=='validation':validation.append(lid)
# Publish only after every group, raw file and review has been checked.
for path,payload in prepared:path.write_text(json.dumps(payload,indent=2))
(root/'CONVERSION_INPUTS.json').write_text(json.dumps(dict(source_roots=sources,validation_push_layout_ids=validation,excluded_test_layout_ids=test,wait_source='SimFoundry/demo/spatial_candidate_pool72_20260928_r1/waits',validation_wait_layout_ids=[63010,63011],expected_push_episodes=len(sources)*2,training_ready=False,next_gate='Convert with exact preassigned splits, verify exports, derive train-only relative statistics before training.'),indent=2))
(root/'STATUS.json').write_text(json.dumps(dict(status='pilot_approved_for_conversion_only',training_ready=False,goal_complete=False),indent=2))
print('Approved complete fresh pilot for conversion; test layouts remain excluded:',test)
