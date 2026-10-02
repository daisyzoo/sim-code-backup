#!/usr/bin/env python3
"""Audit admitted fresh waist-enabled train windows; arm10 relative, waist absolute.
Derived from the locked-waist statistics tool; keeps original10step queries and
all normalization math, replaces locked-zero check with actual waist preservation.
"""
import argparse,copy,hashlib,json
from pathlib import Path
from waist_relative_label_roundtrip import roundtrip
import numpy as np
import torch
from lerobot.policies.factory import make_pre_post_processors
from lerobot.configs.policies import PreTrainedConfig
from lerobot.datasets.lerobot_dataset import LeRobotDataset,LeRobotDatasetMetadata
from lerobot.datasets.factory import resolve_delta_timestamps
from lerobot.policies.pi05.joint_relative import QueryRelativeArm10,joint_action_transform
from lerobot.processor import NormalizerProcessorStep,UnnormalizerProcessorStep,PolicyProcessorPipeline
from lerobot.processor.core import TransitionKey


def main():
    p=argparse.ArgumentParser();p.add_argument('--checkpoint',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--dataset-root',type=Path);p.add_argument('--repo-id');a=p.parse_args()
    if bool(a.dataset_root) != bool(a.repo_id):p.error('--dataset-root and --repo-id must be supplied together')
    cfg=json.loads((a.checkpoint/'train_config.json').read_text());dc=copy.deepcopy(cfg['dataset'])
    root=(a.dataset_root.resolve() if a.dataset_root else Path(dc['root']));split=json.loads((root/'meta/train_validation_split.json').read_text())
    exported=json.loads((root/'meta/paired_export_audit.json').read_text())
    assert exported['training_ready'] is True and not set(split['train']) & set(split['validation'])
    admitted=json.loads((root/'meta/paired_provenance.json').read_text())['records']
    assert set(split['train']) | set(split['validation']) == set(range(len(admitted)))
    assert all(r.get('motion_protocol')=='waist_yaw_enabled_v1' and r.get('waist_pilot_contract_sha256') for r in admitted)
    assert all(admitted[i]['planned_split']=='train' for i in split['train'])
    assert all(admitted[i]['planned_split']=='validation' for i in split['validation'])
    if a.dataset_root:
        dc.update(root=str(root),repo_id=a.repo_id,episodes=split['train'])
    else:assert dc['episodes']==split['train']
    pc=PreTrainedConfig.from_pretrained(a.checkpoint)
    assert pc.chunk_size==10 and pc.joint_action_representation in ('absolute','state_relative_arm10')
    a.out.mkdir(parents=True,exist_ok=False)
    meta=LeRobotDatasetMetadata(dc['repo_id'],root=str(root));ds=LeRobotDataset(dc['repo_id'],root=str(root),episodes=dc['episodes'],delta_timestamps=resolve_delta_timestamps(pc,meta),video_backend=dc['video_backend'],tolerance_s=dc['tolerance_s']);ds._ensure_hf_dataset_loaded()
    records=json.loads((root/'meta/paired_provenance.json').read_text())['records'];ep=np.asarray(ds.hf_dataset['episode_index']).reshape(-1);fr=np.asarray(ds.hf_dataset['frame_index']).reshape(-1);raw={};ix=[*range(13,23),12]
    for eid in dc['episodes']:
        row=records[eid];path=Path(row['path']);assert hashlib.sha256(path.read_bytes()).hexdigest()==row['hash']
        with np.load(path) as z: raw[eid]=(z['q'][:,ix].copy(),z['action'][:,ix].copy())
    actions=[];states=[];pads=[]
    for i,(eid,fi) in enumerate(zip(ep,fr)):
        eid,fi=int(eid),int(fi);indices,pad=ds._get_query_indices(i,eid);assert set(ep[indices['action']])=={eid}
        action=ds._query_hf_dataset({'action':indices['action']})['action'];state=ds.hf_dataset[i]['observation.state']
        q,u=raw[eid];assert np.array_equal(state.numpy(),q[fi]);assert np.array_equal(action.numpy(),u[np.minimum(fi+np.arange(10),len(u)-1)])
        assert np.array_equal(pad['action_is_pad'].numpy(),fi+np.arange(10)>=len(u))
        actions.append(action);states.append(state);pads.append(pad['action_is_pad'])
    actions=torch.stack(actions);states=torch.stack(states);pads=torch.stack(pads)
    relative=joint_action_transform(actions,states);valid=relative[~pads].double().numpy()
    payload=copy.deepcopy(json.loads((root/'meta/train_only_stats.json').read_text()))
    assert payload['episode_indices']==split['train']
    payload['joint_action_representation']='state_relative_arm10';payload['action_chunk_size']=10;payload['action_stats_valid_steps']=len(valid)
    payload['action']={'min':valid.min(0).tolist(),'max':valid.max(0).tolist(),'mean':valid.mean(0).tolist(),'std':valid.std(0).tolist(),'q01':np.quantile(valid,.01,axis=0).tolist(),'q99':np.quantile(valid,.99,axis=0).tolist(),'count':[len(valid)]}
    payload['representation_source']={'dataset':str(root),'source_metadata_sha256':{name:hashlib.sha256((root/'meta'/name).read_bytes()).hexdigest() for name in ['train_only_stats.json','paired_provenance.json','train_validation_split.json']},'method':'Actual training queried10-step windows minus SAME query rawq arm10. Padding excluded; waist absolute. Eachvalid future target contributes once per window occurrence. Original state statistics unchanged.'}
    stats={k:{n:torch.tensor(v) for n,v in payload[k].items()} for k in ['observation.state','action']}
    features={**pc.input_features,**pc.output_features}
    verification=roundtrip(actions,states,stats,features,pc.normalization_mapping)
    error=verification['max_float32_encode_normalize_decode_restore_error']
    (a.out/'train_only_relative_stats.json').write_text(json.dumps(payload,indent=2))
    report={'passed':True,'checkpoint':str(a.checkpoint.resolve()),'dataset':str(root),'repo_id':dc['repo_id'],'dataset_override':bool(a.dataset_root),'training_frames':len(ds),'training_episodes':len(dc['episodes']),'valid_future_steps':len(valid),'total_scalar_labels_including_padding':actions.numel(),'total_chunk_steps_including_padding':int(pads.numel()),'padded_steps':int(pads.sum()),'max_float32_encode_normalize_decode_restore_error':error,'source_action_and_state_max_error':0,'validation_episodes_queried':[],'statistics_file':str((a.out/'train_only_relative_stats.json').resolve()),'state_stats_unchanged':payload['observation.state']==json.loads((root/'meta/train_only_stats.json').read_text())['observation.state'],'limitations':'Actual queried windows, production encode/normalizer/unnormalizer math verified. Does not load newly trained checkpoint, run vision/tokenizer or prove learned improvement; serialized pipeline tests separate. No source dataset changed.','goal_complete':False}
    report.update(verification, motion_protocol='waist_yaw_enabled_v1', statistics_preparer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), roundtrip_checker_sha256=hashlib.sha256((Path(__file__).parent/'waist_relative_label_roundtrip.py').read_bytes()).hexdigest())
    (a.out/'REPORT.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
