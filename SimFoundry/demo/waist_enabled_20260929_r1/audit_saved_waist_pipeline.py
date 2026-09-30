"""CPU replay of saved processor configuration with diagnostic nonzero-waist stats."""
from pathlib import Path
import sys,os,json,hashlib,tempfile,shutil,importlib.util
os.environ.update(HF_HUB_OFFLINE='1',OMP_NUM_THREADS='1',TOKENIZERS_PARALLELISM='false')
root=Path(__file__).resolve().parent;sim=root.parents[1]
repo=sim.parent/'lerobot/unitree_lerobot_yth_repro_20260908/unitree_lerobot_yth/unitree_lerobot/lerobot/src'
sys.path[:0]=[str(sim),str(repo)]
import numpy as np
import torch
from safetensors.torch import save_file
from lerobot.policies.factory import make_pre_post_processors
from lerobot.configs.policies import PreTrainedConfig
from lerobot.configs.types import FeatureType,NormalizationMode
from lerobot.processor import NormalizerProcessorStep,UnnormalizerProcessorStep
from lerobot.policies.pi05.joint_relative import joint_action_transform,validate_relative_pipeline
from lerobot.utils.constants import OBS_LANGUAGE_TOKENS,OBS_LANGUAGE_ATTENTION_MASK
from simfoundry.data.schema import load_episode
torch.set_num_threads(1)
spec=importlib.util.spec_from_file_location('converter',sim/'scripts/prepare_paired_sorting_lerobot.py');converter=importlib.util.module_from_spec(spec);spec.loader.exec_module(converter)
ckpt=sim.parent/'lerobot/outputs/paired_relative_chunk10_20260929/package_sorting_pi05_1gpu_20260929_015655/checkpoints/014480/pretrained_model'
cfg=PreTrainedConfig.from_pretrained(str(ckpt));cfg.device='cpu'
pre_json=json.loads((ckpt/'policy_preprocessor.json').read_text());post_json=json.loads((ckpt/'policy_postprocessor.json').read_text())
pre_norm=next(s for s in pre_json['steps'] if s['registry_name']=='normalizer_processor')
post_norm=next(s for s in post_json['steps'] if s['registry_name']=='unnormalizer_processor')
assert pre_norm['config']['norm_map']==post_norm['config']['norm_map']
norm_map={FeatureType(k):NormalizationMode(v) for k,v in pre_norm['config']['norm_map'].items()}
assert norm_map==cfg.normalization_mapping
assert norm_map[FeatureType.ACTION]==NormalizationMode.MIN_MAX and norm_map[FeatureType.STATE]==NormalizationMode.QUANTILES
sources=[];q_all=[];a_all=[];valid_all=[];samples=[]
for p in sorted((root/'frontal_top_drag_fast_r1').glob('case_*/layout_*/raw.npz')):
 ep=load_episode(p);assert ep.collect_meta['collection_role']=='diagnostic'
 q=ep.q[:,converter.INDICES];a=ep.action[:,converter.INDICES];t=np.arange(len(a))[:,None]+np.arange(10)[None,:]
 q_all.append(q);a_all.append(a[np.minimum(t,len(a)-1)]);valid_all.append(t<len(a))
 for i in [0,1,80,159,240,310,319]:samples.append(dict(state=q[i].copy(),action=a[np.minimum(np.arange(i,i+10),len(a)-1)].copy(),image=ep.rgb[i].copy(),task=ep.instruction,frame=i))
 sources.append(dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),frames=len(q)))
q=torch.from_numpy(np.concatenate(q_all));a=torch.from_numpy(np.concatenate(a_all));valid=np.concatenate(valid_all)
relative=joint_action_transform(a,q)
stats={'observation.state':converter.stats([q.numpy()]),'action':converter.stats([relative.numpy()[valid]])}
normalizer=NormalizerProcessorStep(features={**cfg.input_features,**cfg.output_features},norm_map=norm_map,stats=stats,device='cpu')
inverse=UnnormalizerProcessorStep(features=cfg.output_features,norm_map=norm_map,stats=stats,device='cpu')
with tempfile.TemporaryDirectory(prefix='waist_saved_processors_') as temp:
 dest=Path(temp)
 for name in ['config.json','policy_preprocessor.json','policy_postprocessor.json']:shutil.copy2(ckpt/name,dest/name)
 save_file(normalizer.state_dict(),str(dest/pre_norm['state_file']));save_file(inverse.state_dict(),str(dest/post_norm['state_file']))
 overrides={'device_processor':{'device':'cpu'},'tokenizer_processor':{'tokenizer_name':str(sim.parent/'lerobot/models/paligemma-3b-pt-224'),'local_files_only':True}}
 pre,post=make_pre_post_processors(policy_cfg=cfg,pretrained_path=str(dest),preprocessor_overrides=overrides)
 validate_relative_pipeline(cfg,pre)
 raw_state=torch.from_numpy(np.stack([s['state'] for s in samples]));raw_action=torch.from_numpy(np.stack([s['action'] for s in samples]))
 def batch(with_action=True):
  b={'observation.state':raw_state.clone(),'observation.images.color_0':torch.from_numpy(np.stack([s['image'] for s in samples])).float()/255.,'task':[s['task'] for s in samples],'robot_type':['']*len(samples)}
  if with_action:b['action']=raw_action.clone()
  return b
 pre.reset();processed=pre(batch());post.reset();restored=joint_action_transform(post(processed['action']),raw_state,inverse=True)
 error=float(torch.max(abs(restored-raw_action)));assert error<1e-6
 np.testing.assert_allclose(processed['observation.images.color_0'].numpy(),np.stack([s['image'] for s in samples])/255.,rtol=0,atol=1e-7)
 assert processed[OBS_LANGUAGE_TOKENS].shape==(len(samples),200) and processed[OBS_LANGUAGE_ATTENTION_MASK].any(dim=1).all()
 pre.reset();infer=pre(batch(False))
 assert torch.equal(infer[OBS_LANGUAGE_TOKENS],processed[OBS_LANGUAGE_TOKENS])
 assert torch.equal(infer['observation.state'],processed['observation.state'])
 pre.save_pretrained(dest/'resaved');post.save_pretrained(dest/'resaved')
 reload_pre,reload_post=make_pre_post_processors(policy_cfg=cfg,pretrained_path=str(dest/'resaved'),preprocessor_overrides=overrides)
 validate_relative_pipeline(cfg,reload_pre);again=reload_pre(batch());decoded=joint_action_transform(reload_post(again['action']),raw_state,inverse=True)
 assert torch.equal(again['action'],processed['action']) and torch.equal(again[OBS_LANGUAGE_TOKENS],processed[OBS_LANGUAGE_TOKENS]) and torch.equal(decoded,restored)
 # The same factory loading an old checkpoint retains old stats even if dataset_stats is supplied.
 old_pre,old_post=make_pre_post_processors(policy_cfg=cfg,pretrained_path=str(ckpt),dataset_stats=stats,preprocessor_overrides=overrides)
 old=old_pre(batch());old_max=float(old['action'][:,:,-1].abs().max());assert old_max>1e6
 # Match lerobot_train.py: explicit processor overrides, not only dataset_stats.
 train_overrides={**overrides,'normalizer_processor':{'stats':stats,'features':{**cfg.input_features,**cfg.output_features},'norm_map':cfg.normalization_mapping}}
 train_pre,train_post=make_pre_post_processors(policy_cfg=cfg,pretrained_path=str(ckpt),dataset_stats=stats,preprocessor_overrides=train_overrides,postprocessor_overrides={'unnormalizer_processor':{'stats':stats,'features':cfg.output_features,'norm_map':cfg.normalization_mapping}})
 trained=train_pre(batch());train_decoded=joint_action_transform(train_post(trained['action']),raw_state,inverse=True)
 assert torch.equal(trained['action'],processed['action']) and torch.equal(train_decoded,restored)
 train_pre.save_pretrained(dest/'train_saved');train_post.save_pretrained(dest/'train_saved')
 server_pre,server_post=make_pre_post_processors(policy_cfg=cfg,pretrained_path=str(dest/'train_saved'),preprocessor_overrides=overrides)
 server_batch=server_pre(batch());server_decoded=joint_action_transform(server_post(server_batch['action']),raw_state,inverse=True)
 assert torch.equal(server_batch['action'],processed['action']) and torch.equal(server_decoded,restored)
 report=dict(passed=True,training_ready=False,sources=sources,checkpoint_config=str(ckpt),normalization_map=pre_norm['config']['norm_map'],statistics_scope='Diagnostic only; never published as training statistics',queries=len(samples),horizon=10,max_action_roundtrip_error_rad=error,serialized_full_pipeline_exact_parity=True,existing_training_explicit_stats_overrides_work=True,training_style_save_to_server_style_reload_parity=True,train_infer_state_token_parity=True,image_identity=True,old_checkpoint_dataset_stats_argument_does_not_replace_saved_stats=True,old_saved_stats_normalized_waist_max=old_max,new_diagnostic_stats_normalized_waist_max=float(processed['action'][:,:,-1].abs().max()),scope='Actual saved pre/post JSON, processor registry/factory, local tokenizer, relative-before-normalization validation, MIN_MAX action and QUANTILES state. Temporary nonzero-waist diagnostic stats files replace copied stats only. Label roundtrip is not a model prediction test; no model weights loaded and no simulator action executed. Production admission still pending. Prior QUANTILES-action standalone audit did not cover the saved configuration.',source_sha256={str(ckpt/n):hashlib.sha256((ckpt/n).read_bytes()).hexdigest() for n in ['config.json','policy_preprocessor.json','policy_postprocessor.json']})
(root/'SAVED_WAIST_PIPELINE_AUDIT.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ('sources','source_sha256')},indent=2))
