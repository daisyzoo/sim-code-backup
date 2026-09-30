"""Read-only dataset/rollout coverage diagnostics; geometry is not contact proof."""
import argparse, json
from pathlib import Path
import numpy as np

p=argparse.ArgumentParser()
p.add_argument('--experiment',type=Path,required=True)
p.add_argument('--variants',nargs='+',default=['baseline','ordinary','recovery'])
args=p.parse_args()
WS=Path(__file__).resolve().parents[2]

def stats(x):
 x=np.asarray(x)
 return {'median':float(np.median(x)), 'p95':float(np.quantile(x,.95)), 'max':float(np.max(x))} if x.size else None

def nearest(q, bank):
 return np.concatenate([np.abs(q[i:i+16,None]-bank[None]).max(2).min(1) for i in range(0,len(q),16)])

banks={};experts={};positions={}
for v,folder in [('baseline','lerobot_sim_paired_zero_pilot32_b_20260924'),('ordinary','lerobot_sim_paired_ordinary_pilot40_20260928'),('recovery','lerobot_sim_paired_recovery_pilot40_20260928')]:
 root=WS/'lerobot'/folder
 records=json.loads((root/'meta/paired_provenance.json').read_text())['records']
 train=json.loads((root/'meta/train_validation_split.json').read_text())['train']
 banks[v]={};positions[v]={};experts[v]=[]
 for idx in train:
  rec=records[idx];task=rec['task_id'];path=WS/rec['path']
  with np.load(path) as d:q=d['q'][:,13:23].copy()
  banks[v].setdefault(task,[]).append(q)
  with np.load(path.parent/'trace.npz') as tr:
   if task!='wait_no_package':
    target='box' if task=='push_box_to_bin' else 'mailer';side='right' if target=='box' else 'left';sign=-1 if target=='box' else 1
    obj=tr[target];palm=tr['palm_'+side];progress=sign*(obj[:,1]-obj[0,1]);moving=np.r_[False,np.diff(progress)>.001]
    positions[v].setdefault(task,[]).append(np.r_[tr['box'][0,:2],tr['mailer'][0,:2]])
    experts[v].append({'layout':rec['layout_id'],'task':task,'moving_frames':int(moving.sum()),'palm_z_when_target_moves_m':stats(palm[moving,2]),'palm_z_frames30_100_m':stats(palm[30:101,2])})
 banks[v]={k:np.concatenate(a) for k,a in banks[v].items()}
 positions[v]={k:np.stack(a) for k,a in positions[v].items()}

rows=[]
for variant in args.variants:
 for folder in sorted(args.experiment.glob(f'{variant}_seed*/rollouts/layout_*')):
  if not (folder/'quality.json').exists():continue
  with np.load(folder/'raw.npz') as d:q=d['q'][:,13:23].copy();task=str(d['task_id'])
  quality=json.loads((folder/'quality.json').read_text())
  row={'path':str(folder),'variant':variant,'task':task,'passed':quality['passed'],'nearest_train_arm_Linf_rad':{}}
  for v in banks:
   dist=nearest(q,banks[v][task])
   row['nearest_train_arm_Linf_rad'][v]={'all':stats(dist),'first10':stats(dist[:10]),'frames10_30':stats(dist[10:31]),'frames30_end':stats(dist[30:])}
  with np.load(folder/'trace.npz') as tr:
   if task!='wait_no_package':
    target='box' if task=='push_box_to_bin' else 'mailer';side='right' if target=='box' else 'left';sign=-1 if target=='box' else 1
    obj=tr[target];palm=tr['palm_'+side];progress=sign*(obj[:,1]-obj[0,1]);moving=np.r_[False,np.diff(progress)>.001]
    initial=np.r_[tr['box'][0,:2],tr['mailer'][0,:2]]
    row.update({'progress_m':float(progress[-1]),'moving_frames':int(moving.sum()),'palm_z_when_target_moves_m':stats(palm[moving,2]),'palm_z_frames30_100_m':stats(palm[30:101,2]),'initial_pair_XY_nearest_Linf_m':{v:float(abs(positions[v][task]-initial).max(1).min()) for v in positions}})
  rows.append(row)
result={'method':'10 arm joints physical-radian L-infinity nearest TRAIN state; validation excluded. Initial pair XY uses both objects. Palm heights are geometric summaries, not contact-force evidence. State coverage is correlational, not a failure classifier or proof of recovery efficacy.','train_frames':{v:{k:len(a) for k,a in b.items()} for v,b in banks.items()},'expert_geometry':experts,'rows':rows}
output=args.experiment/('COVERAGE_'+ '-'.join(args.variants)+'.json')
output.write_text(json.dumps(result,indent=2))
print(output,'rollouts',len(rows))
for v in args.variants:
 for task in banks['baseline']:
  rs=[r for r in rows if r['variant']==v and r['task']==task]
  if rs:print(v,task,'passes',sum(r['passed'] for r in rs),'/',len(rs),'median nearest distance to baseline/ordinary/recovery', [round(float(np.median([r['nearest_train_arm_Linf_rad'][b]['all']['median'] for r in rs])),5) for b in banks])
