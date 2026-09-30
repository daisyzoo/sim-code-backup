#!/usr/bin/env python3
"""Verify actual LeRobot training action queries against every source-frame window."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from lerobot.policies.pi05.configuration_pi05 import PI05Config  # Register policy type.
from lerobot.configs.policies import PreTrainedConfig
from lerobot.datasets.lerobot_dataset import LeRobotDataset,LeRobotDatasetMetadata
from lerobot.datasets.factory import resolve_delta_timestamps


def main():
 p=argparse.ArgumentParser();p.add_argument('--checkpoint',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 if a.out.exists():raise FileExistsError(a.out)
 cfg=json.loads((a.checkpoint/'train_config.json').read_text());dc=cfg['dataset'];root=Path(dc['root']);split=json.loads((root/'meta/train_validation_split.json').read_text());assert dc['episodes']==split['train']
 pc=PreTrainedConfig.from_pretrained(a.checkpoint);meta=LeRobotDatasetMetadata(dc['repo_id'],root=str(root));delta=resolve_delta_timestamps(pc,meta);assert pc.action_delta_indices==list(range(50));ds=LeRobotDataset(dc['repo_id'],root=str(root),episodes=dc['episodes'],delta_timestamps=delta,video_backend=dc['video_backend'],tolerance_s=dc['tolerance_s']);ds._ensure_hf_dataset_loaded()
 records=json.loads((root/'meta/paired_provenance.json').read_text())['records'];ep=np.asarray(ds.hf_dataset['episode_index']).reshape(-1);fr=np.asarray(ds.hf_dataset['frame_index']).reshape(-1);raw={};ix=[*range(13,23),12]
 for eid in dc['episodes']:
  row=records[eid];path=Path(row['path']);assert hashlib.sha256(path.read_bytes()).hexdigest()==row['hash']
  with np.load(path,allow_pickle=False) as z:raw[eid]=z['action'][:,ix].copy()
 assert len(ds)==sum(len(v) for v in raw.values())
 assert len(set(zip(ep.tolist(),fr.tolist())))==len(ds)
 maxerr=0.;padded=0
 for i,(eid,fi) in enumerate(zip(ep,fr)):
  eid,fi=int(eid),int(fi);indices,pad=ds._get_query_indices(i,eid);assert set(ep[indices['action']])=={eid};pred=ds._query_hf_dataset({'action':indices['action']})['action'].numpy();expected=raw[eid][np.minimum(fi+np.arange(50),len(raw[eid])-1)];error=float(np.max(np.abs(pred-expected)));maxerr=max(maxerr,error);assert error<1e-7,(eid,fi,error);expected_pad=fi+np.arange(50)>=len(raw[eid]);assert np.array_equal(pad['action_is_pad'].numpy(),expected_pad);padded+=int(expected_pad.any())
  if (i+1)%1000==0:print('CHUNKS_VERIFIED',i+1,flush=True)
 out={'passed':True,'checkpoint_train_config':str((a.checkpoint/'train_config.json').resolve()),'dataset':str(root),'training_frames_checked':len(ds),'action_chunks_checked':len(ds),'labels_per_chunk':50,'scalar_action_labels_checked':len(ds)*50*11,'max_abs_label_error':maxerr,'chunks_with_correct_terminal_padding':padded,'cross_episode_queries':0,'validation_episodes_queried':[],'method':'Invoke the actual dataset _get_query_indices and _query_hf_dataset for every selected training frame using delta_timestamps resolved from saved policy config. Compare each50x11 target and pad mask with raw source actions, clamped within that same episode. No image decoding or model inference.'};a.out.write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
if __name__=='__main__':main()
