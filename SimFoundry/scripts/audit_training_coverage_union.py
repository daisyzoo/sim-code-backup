#!/usr/bin/env python3
"""Read-only preflight of existing ordinary/spatial sources; does not merge datasets."""
import argparse,json,hashlib
from pathlib import Path
from collections import defaultdict
import numpy as np


def main():
    p=argparse.ArgumentParser();p.add_argument('--workspace',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();w=a.workspace.resolve()
    if a.out.exists():raise FileExistsError(a.out)
    rows=[];seen={};geometries=defaultdict(set);expected_prompts={'push_box_to_bin':'Push the brown box to the right with your right hand.','nudge_mailer_to_bin':'Push the black bag to the left with your left hand.','wait_no_package':'Keep both arms still and wait.'}
    for label in ['ordinary','spatial']:
        ds=w/f'lerobot/lerobot_sim_paired_{label}_pilot40_20260928';meta=ds/'meta';assert json.loads((meta/'paired_export_audit.json').read_text())['training_ready'];records=json.loads((meta/'paired_provenance.json').read_text())['records'];split=json.loads((meta/'train_validation_split.json').read_text())
        for eid,row in enumerate(records):
            source=Path(row['path']);source=source if source.is_absolute() else w/source;digest=hashlib.sha256(source.read_bytes()).hexdigest();assert digest==row['hash'] and digest not in seen;seen[digest]=(label,eid)
            partition='train' if eid in split['train'] else 'validation';assert eid in split[partition];task=row['task_id'];assert row['exported_prompt']==expected_prompts[task]
            with np.load(source,allow_pickle=False) as z:
                q=z['q'];act=z['action'];m=json.loads(str(z['collect_meta']));assert np.max(np.abs(q[0,12:23]))<1e-4 and np.max(np.abs(act[0,12:23]))<1e-4 and np.max(np.abs(act[:,12]))<1e-4;assert m['assist_frames']==0 and not m['push_assist'];layout=m['layout'];frames=len(q)
            group=f"{label}:{row.get('geometry_group',row['layout_id'])}";geometries[group].add(partition)
            target=None if task=='wait_no_package' else layout['box_xyz' if task=='push_box_to_bin' else 'mailer_xyz']
            rows.append({'source_dataset':label,'episode_index':eid,'partition':partition,'group':group,'layout_id':row['layout_id'],'task':task,'target_xyz':target,'frames':frames,'raw_path':str(source),'sha256':digest})
    assert all(len(v)==1 for v in geometries.values());assert not set(r['layout_id'] for r in rows)&{100,101,102,20000,58000,58001,58002,58003,58004,58005,58010}
    summary=[]
    for label in ['ordinary','spatial']:
        for part in ['train','validation']:
            for task in expected_prompts:
                rs=[r for r in rows if r['source_dataset']==label and r['partition']==part and r['task']==task];xyz=np.array([r['target_xyz'] for r in rs]) if task!='wait_no_package' else None
                summary.append({'dataset':label,'partition':part,'task':task,'episodes':len(rs),'frames':sum(r['frames'] for r in rs),'target_xyz_min':None if xyz is None else xyz.min(0).tolist(),'target_xyz_max':None if xyz is None else xyz.max(0).tolist()})
    result={'read_only_preflight_passed':True,'raw_hashes':len(rows),'summary':summary,'rows':rows,'approved_for_merge_or_training':False,'limitations':['No dataset written or new training authorized by this report.','Existing ordinary layouts retain category-position correlation; a union would not make all positions category-balanced.','Would require fresh merged train-only stats, preserved source splits, full4-episode spatial groups and export audit.','A future union experiment changes coverage and must be separate from the current prefix-only comparison.']};a.out.write_text(json.dumps(result,indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
