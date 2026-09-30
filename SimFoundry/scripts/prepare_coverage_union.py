#!/usr/bin/env python3
"""Freeze an exact union of previously reviewed sources, preserving both splits."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from prepare_paired_sorting_lerobot import checked_sources,make_split


def main():
 p=argparse.ArgumentParser();p.add_argument('--workspace',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();w=a.workspace.resolve()
 if a.out.exists():raise FileExistsError(a.out)
 expected={};sources=set();val=set();bindings={}
 for label in ['ordinary','spatial']:
  ds=w/f'lerobot/lerobot_sim_paired_{label}_pilot40_20260928';meta=ds/'meta';records=json.loads((meta/'paired_provenance.json').read_text())['records'];split=json.loads((meta/'train_validation_split.json').read_text());assert json.loads((meta/'paired_export_audit.json').read_text())['training_ready'];val.update(split['validation_layouts'])
  for name in ['paired_provenance.json','train_validation_split.json','paired_export_audit.json']:bindings[str(meta/name)]=hashlib.sha256((meta/name).read_bytes()).hexdigest()
  for eid,row in enumerate(records):
   raw=Path(row['path']);raw=(raw if raw.is_absolute() else w/raw).resolve();digest=hashlib.sha256(raw.read_bytes()).hexdigest();assert digest==row['hash'] and digest not in expected;sources.add(raw.parent.parent);expected[digest]={'source_dataset':label,'source_episode_index':eid,'partition':'train' if eid in split['train'] else 'validation','raw_path':str(raw)}
 records=checked_sources(sorted(sources));assert len(records)==80 and {r['hash'] for r in records}==set(expected);split=make_split(records,val);mapped=[];frames={'train':0,'validation':0}
 for eid,row in enumerate(records):
  part='train' if eid in split['train'] else 'validation';original=expected[row['hash']];assert original['partition']==part
  with np.load(row['path'],allow_pickle=False) as z:n=len(z['q'])
  frames[part]+=n;mapped.append({'episode_index':eid,**original,'sha256':row['hash'],'frames':n,'task':row['task_id'],'layout_id':row['layout_id'],'geometry_group':row.get('geometry_group')})
 assert len(split['train'])==68 and len(split['validation'])==12 and frames=={'train':9080,'validation':1560}
 a.out.mkdir(parents=True);(a.out/'selected_sources.txt').write_text('\n'.join(str(x) for x in sorted(sources))+'\n');(a.out/'selected_validation_ids.txt').write_text(','.join(map(str,sorted(val)))+'\n')
 result={'approved_for_conversion':True,'approved_for_training':False,'episodes':80,'frames':10640,'train_episodes':68,'validation_episodes':12,'frames_by_partition':frames,'source_metadata_sha256':bindings,'source_roots':[str(x) for x in sorted(sources)],'validation_layouts':sorted(val),'split':split,'records':mapped,'method':'Exact union of80 previously approved raw hashes. Re-run current numeric,visual-hash,paired-reset and spatial-contract gates. Preserve original partition by raw hash and full spatial4-episode groups.','limitations':['Ordinary subset retains category-position correlation; union is not globally category-position balanced.','No new layouts are created. This adds known original-layout coverage only.','No training begins from this conversion approval; new export audit and explicit experiment design required.']};(a.out/'SELECTION.json').write_text(json.dumps(result,indent=2));(a.out/'STATUS.json').write_text(json.dumps({'stage':'raw_union_validated_requires_conversion','goal_complete':False},indent=2));print(json.dumps({k:v for k,v in result.items() if k not in ['records','source_metadata_sha256','source_roots','split']},indent=2))
if __name__=='__main__':main()
