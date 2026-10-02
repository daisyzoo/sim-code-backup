"""CPU production-processor check on real raw data; no dataset or training approval."""
from pathlib import Path
import json,hashlib,datetime,sys
import numpy as np
import torch
from lerobot.policies.pi05.configuration_pi05 import PI05Config
from lerobot.configs.policies import PreTrainedConfig
from lerobot.policies.pi05.joint_relative import joint_action_transform
from waist_relative_label_roundtrip import roundtrip,verify_restored
W=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 checkpoint=Path((W.parent/'short_first_model40_20260929_r1/checkpoint.txt').read_text().strip());pc=PreTrainedConfig.from_pretrained(checkpoint);assert pc.chunk_size==10 and tuple(pc.input_features['observation.state'].shape)==(11,)
 names=[('840000','push_box_to_bin'),('840001','nudge_mailer_to_bin'),('841000','wait_no_package')];rows=[];hashes={str(checkpoint/'config.json'):sha(checkpoint/'config.json')};checks=[]
 for layout,task in names:
  ep=W/f'fresh_closed_peak_trials_r1/case_{layout}/layout_{layout}_{task}';path=ep/'raw.npz'
  with np.load(path) as z:
   ix=[*range(13,23),12];q=z['q'][:,ix].copy();u=z['action'][:,ix].copy()
  assert np.max(abs(q[0]))==0 and np.max(abs(u[0]))==0
  n=len(q);indices=np.minimum(np.arange(n)[:,None]+np.arange(10),n-1);padding=np.arange(n)[:,None]+np.arange(10)>=n
  actions=torch.from_numpy(u[indices]);states=torch.from_numpy(q);relative=joint_action_transform(actions,states);valid=relative[~torch.from_numpy(padding)].double().numpy()
  def stats(x):
   return {k:torch.tensor(v,dtype=torch.float32) for k,v in dict(min=x.min(0),max=x.max(0),mean=x.mean(0),std=x.std(0),q01=np.quantile(x,.01,axis=0),q99=np.quantile(x,.99,axis=0)).items()}
  result=roundtrip(actions,states,{'action':stats(valid),'observation.state':stats(q.astype(float))},{**pc.input_features,**pc.output_features},pc.normalization_mapping)
  result.update(episode=ep.name,query_frames=n,valid_future_steps=int((~padding).sum()),terminal_padding_steps=int(padding.sum()),legacy_zero_waist_assertion_would_pass=bool(torch.all(actions[...,-1]==0)))
  if task!='wait_no_package':
   assert result['waist_nonzero_label_count']>0 and not result['legacy_zero_waist_assertion_would_pass']
   corrupted=actions.clone();corrupted[...,-1]=0
   try:verify_restored(actions,states,corrupted)
   except ValueError:checks.append(dict(episode=ep.name,case='incorrect_zeroing_of_recorded_waist',rejected=True))
   else:raise AssertionError('Zeroed nonzero waist was accepted')
  else:assert result['waist_nonzero_label_count']==0 and result['legacy_zero_waist_assertion_would_pass']
  for label,corrupted in [('changed_arm',actions.clone()),('nonfinite',actions.clone())]:
   corrupted[0,0,0]+=0.01 if label=='changed_arm' else float('nan')
   try:verify_restored(actions,states,corrupted)
   except ValueError:checks.append(dict(episode=ep.name,case=label,rejected=True))
   else:raise AssertionError(label+' accepted')
  rows.append(result);hashes[str(path)]=sha(path)
 for p in [Path(__file__),W/'waist_relative_label_roundtrip.py',W/'prepare_closed_peak_trial_relative_stats.py']:hashes[str(p)]=sha(p)
 report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,rows=rows,negative_checks=checks,source_sha256=hashes,scope=__doc__,statistics_scope='Temporary per-episode diagnostic ranges used only to exercise production processors; no train normalization file written. Actual prepared dataset loader/statistics path not yet run.',training_ready=False)
 with (W/'WAIST_RELATIVE_LABEL_ROUNDTRIP_CHECK.json').open('x') as f:json.dump(report,f,indent=2)
 print(json.dumps({k:v for k,v in report.items() if k!='source_sha256'},indent=2))
if __name__=='__main__':main()
