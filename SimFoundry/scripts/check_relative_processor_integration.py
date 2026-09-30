#!/usr/bin/env python3
import argparse,json,copy
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import torch
from torch.utils.data._utils.collate import default_collate
from lerobot.configs.policies import PreTrainedConfig
from lerobot.policies.factory import make_pre_post_processors
from lerobot.policies.pi05.joint_relative import install_relative_training_step,validate_relative_pipeline,joint_action_transform
from lerobot.datasets.lerobot_dataset import LeRobotDataset,LeRobotDatasetMetadata
from lerobot.datasets.factory import resolve_delta_timestamps
from lerobot.utils.pi05_training import apply_training_stats
import os

def main():
 p=argparse.ArgumentParser();p.add_argument('--checkpoint',type=Path,required=True);p.add_argument('--stats',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
 tc=json.loads((a.checkpoint/'train_config.json').read_text());dc=tc['dataset'];root=Path(dc['root']);pc=PreTrainedConfig.from_pretrained(a.checkpoint);pc.device='cpu';pc.joint_action_representation='state_relative_arm10'
 meta=LeRobotDatasetMetadata(dc['repo_id'],root=str(root));ds=LeRobotDataset(dc['repo_id'],root=str(root),episodes=dc['episodes'],delta_timestamps=resolve_delta_timestamps(pc,meta),video_backend=dc['video_backend'],tolerance_s=dc['tolerance_s']);ds._ensure_hf_dataset_loaded()
 os.environ['PI05_TRAIN_STATS_FILE']=str(a.stats);os.environ['PI05_SHARED_SPLIT_FILE']=str(root/'meta/train_validation_split.json')
 cfg=SimpleNamespace(policy=pc,dataset=SimpleNamespace(episodes=dc['episodes']));apply_training_stats(cfg,ds)
 overrides={'device_processor':{'device':'cpu'},'tokenizer_processor':{'tokenizer_name':'/home/user/Documents/zoo/sim/lerobot/models/paligemma-3b-pt-224','local_files_only':True},'normalizer_processor':{'features':{**pc.input_features,**pc.output_features},'stats':ds.meta.stats,'norm_map':pc.normalization_mapping}}
 pre,post=make_pre_post_processors(pc,pretrained_path=str(a.checkpoint),preprocessor_overrides=overrides,postprocessor_overrides={'unnormalizer_processor':{'features':pc.output_features,'stats':ds.meta.stats,'norm_map':pc.normalization_mapping}})
 install_relative_training_step(pc,pre);pre.save_pretrained(a.out);post.save_pretrained(a.out);pc.save_pretrained(a.out)
 loaded=PreTrainedConfig.from_pretrained(a.out);lp,lpost=make_pre_post_processors(loaded,pretrained_path=str(a.out),preprocessor_overrides={'device_processor':{'device':'cpu'}});validate_relative_pipeline(loaded,lp)
 legacy=copy.deepcopy(pc);legacy.joint_action_representation='absolute';legacy_pre,_=make_pre_post_processors(legacy,pretrained_path=str(a.checkpoint),preprocessor_overrides={k:v for k,v in overrides.items() if k!='normalizer_processor'})
 ep=np.asarray(ds.hf_dataset['episode_index']).reshape(-1);fr=np.asarray(ds.hf_dataset['frame_index']).reshape(-1);selected=[]
 for eid in dc['episodes']:
  ids=np.flatnonzero(ep==eid);selected.extend([int(ids[0]),int(ids[-1])])
 maxerr=0.;tasks=set()
 for start in range(0,len(selected),16):
  samples=[]
  for i in selected[start:start+16]:
   eid=int(ep[i]);indices,pad=ds._get_query_indices(i,eid);item=dict(ds.hf_dataset[i]);item.update(ds._query_hf_dataset({'action':indices['action']}));item.update(pad)
   item['task']=ds.meta.tasks.iloc[int(item['task_index'])].name
   # Image identity normalization is irrelevant to this numeric representation check.
   samples.append({k:item[k] for k in ['observation.state','action','action_is_pad','task']});tasks.add(item['task'])
  batch=default_collate(samples);b1=pre(batch);b2=lp(batch);old=legacy_pre(batch)
  assert torch.equal(b1['action'],b2['action']);assert torch.equal(b1['observation.language.tokens'],old['observation.language.tokens'])
  assert torch.equal(b1['action_is_pad'],batch['action_is_pad'])
  result=joint_action_transform(lpost(b2['action']),batch['observation.state'],inverse=True);err=float((result-batch['action']).abs().max());maxerr=max(maxerr,err);assert err<1e-6
 # Fail closed when representation and statistics disagree.
 pc.joint_action_representation='absolute'
 try:apply_training_stats(cfg,ds)
 except ValueError:pass
 else:raise AssertionError('Absolute config accepted relative stats')
 pc.joint_action_representation='state_relative_arm10';pc.chunk_size=50
 try:apply_training_stats(cfg,ds)
 except ValueError:pass
 else:raise AssertionError('Wrong horizon accepted residual stats')
 report={'passed':True,'train_episodes':len(dc['episodes']),'samples':len(selected),'tasks':sorted(tasks),'max_roundtrip_error':maxerr,'saved_factory_reload_equal':True,'state_language_tokens_equal_to_legacy':True,'padding_unchanged':True,'representation_and_horizon_mismatch_rejected':True,'method':'Actual numeric dataset query atfirst/last frame of every trainingepisode; complete saved factory preprocessor/tokenizer and postprocessor reload. Images notdecoded because unchanged by numeric representation. Separate all9080labelaudit covers full windows.','goal_complete':False};(a.out/'REPORT.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
