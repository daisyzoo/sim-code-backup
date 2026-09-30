#!/usr/bin/env python3
"""Watch complete evaluation seeds and create materials only, never approve them."""
import argparse,json,subprocess,sys,time
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--workflow',type=Path,required=True);a=p.parse_args();root=a.root.resolve();maker=Path(__file__).with_name('make_rollout_review.py')
    expected={f'spatial_{kind}_seed{seed}':(kind,13 if kind=='spatial' else 7) for kind in ['spatial','original'] for seed in range(3)}
    while True:
        for status in [root/'STATUS.json',a.workflow/'STATUS.json']:
            if status.exists():
                stage=json.loads(status.read_text()).get('stage','')
                if 'failure' in stage or stage.startswith('failed'):raise RuntimeError(f'Stopping material watcher: {status}: {stage}')
        count=0
        for name,(kind,n) in expected.items():
            source=root/name;out=root/'visual_materials'/name
            if (out/'inventory.json').exists():count+=1;continue
            if kind=='spatial':ready=(source/'EVALUATION.json').exists()
            else:
                status=source/'rollouts/STATUS.json';ready=status.exists() and json.loads(status.read_text()).get('status')=='evaluation_complete'
            if not ready:continue
            paths=list(source.glob('*/layout_*/raw.npz'))
            if len(paths)!=n:raise ValueError(f'Incomplete completed seed: {source}: {len(paths)}/{n}')
            subprocess.run([sys.executable,str(maker),'--root',str(source),'--out',str(out)],check=True)
            inventory=json.loads((out/'inventory.json').read_text());assert len(inventory)==n
            count+=1;print('MATERIALS_READY',name,n,'actual_review_still_required',flush=True)
        if root.exists():(root/'REVIEW_MATERIALS_STATUS.json').write_text(json.dumps({'seed_materials_generated':count,'expected_seeds':6,'actual_visual_review':'not performed by this script','goal_complete':False},indent=2))
        if count==len(expected):return
        time.sleep(15)
if __name__=='__main__':main()
