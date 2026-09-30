"""CPU diagnostic of actual nonzero-waist processor values, never training admission."""
from pathlib import Path
import importlib.util,sys,json,hashlib,os
os.environ['HF_HUB_OFFLINE']='1';os.environ['OMP_NUM_THREADS']='1'
root=Path(__file__).resolve().parent;sim=root.parents[1];workspace=sim.parent
repo=workspace/'lerobot/unitree_lerobot_yth_repro_20260908/unitree_lerobot_yth/unitree_lerobot/lerobot/src'
sys.path[:0]=[str(sim),str(repo)]
import numpy as np
import torch
torch.set_num_threads(1)
from lerobot.processor import NormalizerProcessorStep,UnnormalizerProcessorStep
from lerobot.processor.core import TransitionKey
from lerobot.configs.types import FeatureType,NormalizationMode,PolicyFeature
from lerobot.policies.pi05.joint_relative import QueryRelativeArm10,joint_action_transform
from simfoundry.data.schema import load_episode
spec=importlib.util.spec_from_file_location('paired_converter',sim/'scripts/prepare_paired_sorting_lerobot.py');converter=importlib.util.module_from_spec(spec);spec.loader.exec_module(converter)
run=root/'frontal_top_drag_fast_r1';records=[];chunks=[];states=[];valids=[]
for path in sorted(run.glob('case_*/layout_*/raw.npz')):
 ep=load_episode(path);q=ep.q[:,converter.INDICES].astype(np.float32);a=ep.action[:,converter.INDICES].astype(np.float32)
 assert ep.collect_meta['motion_protocol']=='waist_yaw_enabled_v1' and ep.collect_meta['collection_role']=='diagnostic'
 assert np.max(abs(q[0]))<1e-4 and np.max(abs(a[0]))<1e-4
 t=np.arange(len(a))[:,None]+np.arange(10)[None,:];valid=t<len(a);chunks.append(a[np.minimum(t,len(a)-1)]);states.append(q);valids.append(valid)
 records.append(dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),frames=len(a)))
absolute=torch.from_numpy(np.concatenate(chunks));state=torch.from_numpy(np.concatenate(states));valid=np.concatenate(valids)
encoded=QueryRelativeArm10()({TransitionKey.ACTION:absolute,TransitionKey.OBSERVATION:{'observation.state':state}})
relative=encoded[TransitionKey.ACTION];assert torch.equal(relative[:,:,-1],absolute[:,:,-1])
# Diagnostic-only statistics from these two failed developer trajectories. Not training stats.
stats={'action':converter.stats([relative.numpy()[valid]]),'observation.state':converter.stats([state.numpy()])}
features={'action':PolicyFeature(type=FeatureType.ACTION,shape=(11,)),'observation.state':PolicyFeature(type=FeatureType.STATE,shape=(11,))};norm_map={FeatureType.ACTION:NormalizationMode.QUANTILES,FeatureType.STATE:NormalizationMode.QUANTILES}
normalizer=NormalizerProcessorStep(features=features,norm_map=norm_map,stats=stats,device='cpu');inverse=UnnormalizerProcessorStep(features=features,norm_map=norm_map,stats=stats,device='cpu')
normalized=normalizer(encoded);decoded=inverse(normalized);restored=joint_action_transform(decoded[TransitionKey.ACTION],state,inverse=True)
# Exercise the same safetensors state-dict storage used by saved processors.
import tempfile
from safetensors.torch import save_file,load_file
with tempfile.TemporaryDirectory(prefix='waist_processor_audit_') as tmp:
 saved=Path(tmp)/'diagnostic_stats.safetensors';save_file(normalizer.state_dict(),str(saved))
 reloaded_norm=NormalizerProcessorStep(features=features,norm_map=norm_map,device='cpu')
 reloaded_inv=UnnormalizerProcessorStep(features=features,norm_map=norm_map,device='cpu')
 reloaded_norm.load_state_dict(load_file(str(saved)));reloaded_inv.load_state_dict(load_file(str(saved)))
 loaded_encoded=reloaded_norm(encoded);loaded_restored=joint_action_transform(reloaded_inv(loaded_encoded)[TransitionKey.ACTION],state,inverse=True)
 assert torch.equal(loaded_encoded[TransitionKey.ACTION],normalized[TransitionKey.ACTION])
 assert torch.equal(loaded_restored,restored)
 serialized_sha256=hashlib.sha256(saved.read_bytes()).hexdigest()
error=float(torch.max(torch.abs(restored-absolute)));state_error=float(torch.max(torch.abs(decoded[TransitionKey.OBSERVATION]['observation.state']-state)));assert error<1e-6 and state_error<1e-6
# Independent 11D -> raw23 order check uses the collector's documented index assignment.
raw23=np.zeros((len(restored),10,23),dtype=np.float32);raw23[:,:,converter.INDICES]=restored.numpy();assert np.max(abs(raw23[:,:,12]-absolute.numpy()[:,:,-1]))<1e-6
old_path=sim/'demo/state_relative_chunk10_20260929_r1/label_preflight/train_only_relative_stats.json';old=json.loads(old_path.read_text());old_normalizer=NormalizerProcessorStep(features=features,norm_map=norm_map,stats={k:old[k] for k in features},device='cpu');old_result=old_normalizer(encoded)
old_waist=float(torch.max(torch.abs(old_result[TransitionKey.ACTION][:,:,-1])));new_waist=float(torch.max(torch.abs(normalized[TransitionKey.ACTION][:,:,-1])))
report=dict(passed=True,serialized_processor_state_parity=True,serialized_diagnostic_stats_sha256=serialized_sha256,training_ready=False,source_records=records,frames=len(state),horizon=10,valid_action_vectors=int(valid.sum()),first_state_action_zero=True,waist_stays_absolute=True,max_action_roundtrip_error_rad=error,max_state_roundtrip_error_rad=state_error,actual_waist_state_range_rad=[float(state[:,-1].min()),float(state[:,-1].max())],actual_waist_action_range_rad=[float(absolute[:,:,-1].min()),float(absolute[:,:,-1].max())],diagnostic_normalized_waist_abs_max=new_waist,old_stats_negative_control=dict(path=str(old_path),sha256=hashlib.sha256(old_path.read_bytes()).hexdigest(),waist_action_q01=old['action']['q01'][-1],waist_action_q99=old['action']['q99'][-1],normalized_waist_abs_max=old_waist),scope='Actual converter INDICES and stats function, real QueryRelativeArm10 and QUANTILES normalization/unnormalization, inverse action codec with SAME query state. CPU only; failed development episodes never admitted/exported as training dataset. Processor state saved/reloaded via safetensors with exact output equality. No model prediction, full pipeline config reload, video conversion/dataloader, or simulator execution parity claim. Diagnostic stats intentionally not published as training stats; future stats must use admitted training split only.',source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [sim/'scripts/prepare_paired_sorting_lerobot.py',repo/'lerobot/policies/pi05/joint_relative.py',repo/'lerobot/processor/normalize_processor.py',sim/'scripts/pi05_policy_server.py']})
(root/'WAIST_PROCESSOR_ROUNDTRIP_AUDIT.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ['source_records','source_sha256']},indent=2))
