#!/usr/bin/env python3
"""Select complete reviewed geometry groups using the preregistered order/quotas.
No numeric-only approval. Failed collector STATUS and raw files remain untouched.
"""
import argparse,hashlib,json
from pathlib import Path


def group_state(root, group, verify_images=False):
    sources=[root/f'case_{i}' for i in group['layout_ids']]
    if not all((r/'candidate_result.json').is_file() for r in sources):
        return {**group,'status':'pending','sources':list(map(str,sources))}
    results=[json.loads((r/'candidate_result.json').read_text()) for r in sources]
    paths=sorted(p for r in sources for p in r.glob('layout_*/raw.npz'))
    if len(paths)!=4:raise ValueError('Completed group does not contain exactly four episodes')
    failed=[]
    for p in paths:
        q=json.loads((p.parent/'quality.json').read_text())
        if not q['passed']:failed.append({'episode':str(p.parent.relative_to(root)),'reasons':q['reasons']})
    numeric=all(r['candidate_numeric_pass'] for r in results) and not failed
    row={**group,'status':'numeric_pass_visual_pending' if numeric else 'rejected_numeric','sources':list(map(str,sources)),'failures':failed}
    review_file=root/'visual_groups'/group['group']/'review.json'
    if numeric and review_file.is_file():
        review=json.loads(review_file.read_text())
        if review.get('reviewed') is not True or not review.get('method'):
            raise ValueError('Invalid actual image review record')
        expected={str(p.relative_to(root)) for p in paths}
        if set(review.get('episodes',{}))!=expected:raise ValueError('Review must bind exactly the complete four-episode group')
        if verify_images:
            for p in paths:
                if hashlib.sha256(p.read_bytes()).hexdigest()!=review['episodes'][str(p.relative_to(root))]:
                    raise ValueError('Reviewed raw file changed')
        row['status']='approved_group' if review.get('approved') is True else 'rejected_visual'
        row['review']=str(review_file)
    return row


def choose_groups(rows):
    # Registered input order is preserved; never rank by progress/margin/model result.
    chosen=[];shortfalls={}
    for stratum in ('negative','center','positive'):
        eligible=[r for r in rows if r['partition']=='train' and r['stratum']==stratum and r['status']=='approved_group']
        if len(eligible)<2:shortfalls['train_'+stratum]=2-len(eligible)
        chosen+=eligible[:2]
    val=[r for r in rows if r['partition']=='validation' and r['status']=='approved_group']
    if not val:shortfalls['validation']=1
    chosen+=val[:1]
    if shortfalls:raise ValueError(f'Incomplete preregistered group quotas: {shortfalls}')
    return chosen


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--select-out',type=Path);a=p.parse_args();root=a.root.resolve()
    c=json.loads((root/'contract.json').read_text());assert c['collection_kind']=='pre_registered_candidate_pool'
    rows=[group_state(root,g,verify_images=bool(a.select_out)) for g in c['candidate_groups']]
    summary={s:sum(r['status']==s for r in rows) for s in sorted({r['status'] for r in rows})}
    print(json.dumps({'groups':summary,'completed_cases':len(list(root.glob('case_*/candidate_result.json')))},indent=2))
    if not a.select_out:return
    if json.loads((root/'STATUS.json').read_text())['stage']!='numeric_complete_group_selection_and_visual_review_required':
        raise ValueError('Candidate pool has not completed its registered coverage')
    chosen=choose_groups(rows);wait=root/'waits';wr=json.loads((wait/'review.json').read_text())
    if wr.get('approved') is not True or not wr.get('method'):raise ValueError('Wait trajectories require actual review')
    waits=sorted(wait.glob('layout_*/raw.npz'))
    if len(waits)!=12 or set(wr.get('episodes',{}))!={str(p.relative_to(wait)) for p in waits}:raise ValueError('Incomplete wait review')
    for pth in waits:
        if hashlib.sha256(pth.read_bytes()).hexdigest()!=wr['episodes'][str(pth.relative_to(wait))]:raise ValueError('Wait data changed')
    from check_collection_quality import check
    check(wait,12)
    sources=[]
    for g in chosen:
        group_review=json.loads(Path(g['review']).read_text())
        for value in g['sources']:
            src=Path(value);check(src,2);paths=sorted(src.glob('layout_*/raw.npz'))
            translated={'approved':True,'method':f"Actual complete geometry review at {g['review']}; exact hashes verified; chosen by preregistered stratum/order quota.",'episodes':{str(p.relative_to(src)):group_review['episodes'][str(p.relative_to(root))] for p in paths}}
            dest=src/'review.json'
            if dest.exists() and json.loads(dest.read_text())!=translated:raise ValueError('Refusing to overwrite different source approval')
            if not dest.exists():dest.write_text(json.dumps(translated,indent=2))
            sources.append(value)
    validation=next(g for g in chosen if g['partition']=='validation')
    result={'training_ready':False,'stage':'selected_raw_requires_conversion_audit','candidate_pool':str(root),'contract_sha256':hashlib.sha256((root/'contract.json').read_bytes()).hexdigest(),'all_groups':rows,'selected_groups':[g['group'] for g in chosen],'selected_train_groups':[g['group'] for g in chosen if g['partition']=='train'],'selected_validation_group':validation['group'],'source_roots':sources+[str(wait)],'validation_layouts':validation['layout_ids']+c['admission_policy']['wait_validation'],'selected_episodes':40,'selected_frames':5320,'generation_budget':{'push_candidates':60,'wait_candidates':12},'selection_bias_note':'Whole-group physical/visual curation retains both categories in each XY slot and both prompts. Geometry acceptance may still bias workspace coverage; all candidate failures are retained here.'}
    if a.select_out.exists():raise FileExistsError(a.select_out)
    a.select_out.write_text(json.dumps(result,indent=2));print('Selected40 reviewed episodes; conversion must still recheck raw gates, roles, contracts and splits.')
if __name__=='__main__':main()
