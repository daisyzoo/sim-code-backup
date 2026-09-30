"""Read-only reproduction of saved state quantile normalization and256bins."""
from pathlib import Path
import json,numpy as np
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'demo/recovery_training_protocol_20260928_r1';ix=[*range(13,23),12]
dataset=ROOT.parent/'lerobot/lerobot_sim_paired_zero_pilot32_b_20260924'
stats=json.loads((dataset/'meta/train_only_stats.json').read_text())['observation.state'];lo=np.array(stats['q01'],dtype=np.float32);hi=np.array(stats['q99'],dtype=np.float32);den=np.where(hi-lo==0,np.float32(1e-8),hi-lo)
def tokens(q):return np.digitize(2*(q-lo)/den-1,np.linspace(-1,1,257)[:-1])-1
train=[];wait=[]
for source in ('paired_zero_push24_release_20260924_r1','paired_zero_wait8_20260924_r2'):
 for p in sorted((ROOT/'demo'/source).glob('layout_*/raw.npz')):
  lid=int(p.parent.name.split('_')[1])
  if lid not in {*range(10,20),*range(10000,10006)}:continue
  q=np.load(p)['q'][:,ix];train.append(tokens(q))
  if lid==10000:wait=tokens(q)
train=np.concatenate(train);rows=[]
for root,pattern in [('paired_zero_ab_experiment_20260924_r1','b_seed*/rollouts/layout_*'),('paired_c4_experiment_20260924_r1','seed*/rollouts/layout_*')]:
 for p in sorted((ROOT/'demo'/root).glob(pattern)):
  q=np.load(p/'raw.npz')['q'][:,ix];tok=tokens(q)
  rows.append({'path':str(p.relative_to(ROOT)),'token_min_per_joint':tok.min(0).tolist(),'token_max_per_joint':tok.max(0).tolist(),'below_training_token_range_fraction':(tok<train.min(0)).mean(0).tolist(),'above_training_token_range_fraction':(tok>train.max(0)).mean(0).tolist(),'initial_token':tok[0].tolist(),'t1_token':tok[1].tolist()})
report={'method':'Float32 quantile formula from normalize_processor.py, np.digitize256bins from processor_pi05.py; first11real state dimensions, padding omitted. Verify implementation changes before reuse. C4 uses same original B dataset stats. No claim of a tokenizer bug.','q01':lo.tolist(),'q99':hi.tolist(),'training_token_min':train.min(0).tolist(),'training_token_max':train.max(0).tolist(),'wait_initial_tokens':wait[0].tolist(),'wait_settled_tokens':wait[35].tolist(),'wait_changed_joint_count':int((wait[0]!=wait[35]).sum()),'rows':rows}
(out/'state_token_audit.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='rows'},indent=2))
