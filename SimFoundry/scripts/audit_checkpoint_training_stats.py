#!/usr/bin/env python3
"""Verify saved state/action normalization exactly matches training-only statistics."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from safetensors.numpy import load_file


def main():
    p=argparse.ArgumentParser();p.add_argument('--checkpoint',type=Path,required=True);p.add_argument('--dataset',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--stats',type=Path);a=p.parse_args()
    cp=a.checkpoint.resolve();statsfile=a.stats or a.dataset/'meta/train_only_stats.json';stats=json.loads(statsfile.read_text());rows=[]
    config=json.loads((cp/'config.json').read_text())
    assert config.get('joint_action_representation','absolute')==stats.get('joint_action_representation','absolute'), 'Statistics representation mismatch'
    files=[]
    for filename,registry in [('policy_preprocessor.json','normalizer_processor'),('policy_postprocessor.json','unnormalizer_processor')]:
        entries=[s for s in json.loads((cp/filename).read_text())['steps'] if s.get('registry_name')==registry]
        assert len(entries)==1
        files.append(cp/entries[0]['state_file'])
    for file in files:
        tensors=load_file(str(file))
        for feature in ['action','observation.state']:
            for name,values in stats[feature].items():
                key=f'{feature}.{name}';actual=tensors[key];expected=np.asarray(values,dtype=actual.dtype)
                same=actual.shape==expected.shape and bool(np.array_equal(actual,expected))
                rows.append({'file':file.name,'key':key,'equal':same})
    result={'passed':all(r['equal'] for r in rows),'checkpoint':str(cp),'dataset':str(a.dataset.resolve()),'train_stats_sha256':hashlib.sha256(statsfile.read_bytes()).hexdigest(),'checks':rows}
    if a.out.exists():raise FileExistsError(a.out)
    a.out.write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='checks'}))
    if not result['passed']:raise ValueError('Saved processor statistics do not match training-only statistics')
if __name__=='__main__':main()
