#!/usr/bin/env python3
"""Generate review sheets as whole groups finish; never approve or train data."""
import argparse,json,subprocess,sys,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--watch',action='store_true');a=p.parse_args();root=a.root.resolve();c=json.loads((root/'contract.json').read_text());maker=Path(__file__).with_name('make_rollout_review.py')
while True:
    ready=0
    for g in c['candidate_groups']:
        out=root/'visual_groups'/g['group']
        if (out/'inventory.json').is_file():ready+=1;continue
        if all((root/f'case_{lid}'/'candidate_result.json').is_file() for lid in g['layout_ids']):
            subprocess.run([sys.executable,str(maker),'--root',str(root),'--out',str(out),'--layout-ids',*map(str,g['layout_ids'])],check=True)
            ready+=1
    wait=root/'waits';out=root/'visual_groups'/'waits'
    if (wait/'STATUS.json').exists() and not out.exists():
        try:s=json.loads((wait/'STATUS.json').read_text())
        except json.JSONDecodeError:s={}
        if s.get('status')=='numeric_pass_visual_review_pending':
            subprocess.run([sys.executable,str(maker),'--root',str(root),'--out',str(out),'--layout-ids',*map(str,c['wait_layouts'])],check=True)
    (root/'REVIEW_MATERIALS_STATUS.json').write_text(json.dumps({'generated_geometry_groups':ready,'wait_materials_generated':(out/'inventory.json').is_file(),'actual_visual_review':'not performed by this script','training_ready':False},indent=2))
    stage=json.loads((root/'STATUS.json').read_text())['stage']
    if not a.watch or (ready==len(c['candidate_groups']) and (out/'inventory.json').is_file()):break
    if stage.startswith('failed_'):raise RuntimeError('Collection failed; material generation stopped')
    time.sleep(10)
