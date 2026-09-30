import sys,json,hashlib
from pathlib import Path
import numpy as np,torch
sys.path.insert(0,str(Path('SimFoundry').resolve()))
from simfoundry.data.search_expert_interface import expert_absolute_targets,terminal_batch_audit,TASKS
from simfoundry.robots.g1_assets import u1_sorting_default_qpos_np,U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
root=Path('SimFoundry/demo/vector_reset_probe_20260929_r1');paths=sorted(Path('SimFoundry/demo/natural_coverage24_20260929_r1').glob('case_*/layout_*/raw.npz'));qs=[];actions=[];traces={k:[] for k in ['box','mailer','palm_left','palm_right']};tasks=[];expected=[]
for p in paths:
 task=p.parent.name.split('_',2)[2];tasks.append(TASKS.index(task))
 with np.load(p) as z:qs.append(z['q']);actions.append(z['action'])
 with np.load(p.parent/'trace.npz') as z:
  for k in traces:traces[k].append(z[k])
 expected.append(json.loads((p.parent/'quality.json').read_text()))
reports=terminal_batch_audit(np.array(tasks),np.stack(qs,axis=1),np.stack(actions,axis=1),{k:np.stack(v,axis=1) for k,v in traces.items()})
for got,want in zip(reports,expected):
 assert got['passed']==want['passed'] and got['reasons']==want['reasons'],(got,want)
 for k,v in got['metrics'].items():assert abs(v-want['metrics'][k])<1e-7
assert len(reports)==24 and sum(x['passed'] for x in reports)==10
# Exercise saturation, joint-limit accumulation, first-frame and inactive-arm invariants.
torch.manual_seed(20260929);d=torch.tensor(u1_sorting_default_qpos_np(zero_upper_body=True));lo=torch.tensor(U1_JOINT_LIMIT_LO);hi=torch.tensor(U1_JOINT_LIMIT_HI);tasks=torch.tensor([0,1,2,0,1,2]);prev=d.repeat(6,1);maxstep=0.
for step in range(180):
 raw=torch.randn(6,5)*5;first=torch.full((6,),step==0,dtype=torch.bool);target=expert_absolute_targets(raw,prev,tasks,first,d,lo,hi)
 assert torch.all(target>=lo-1e-6) and torch.all(target<=hi+1e-6) and torch.all(target[:,12]==0)
 assert torch.all(target[tasks==0,13:18]==0) and torch.all(target[tasks==1,18:23]==0) and torch.all(target[tasks==2,12:]==0)
 if step==0:assert torch.all(target[:,12:]==0)
 maxstep=max(maxstep,float((target-prev).abs().max()));prev=target
assert maxstep<=.055001
try:expert_absolute_targets(torch.full((6,5),float('nan')),prev,tasks,torch.zeros(6,dtype=torch.bool),d,lo,hi)
except ValueError:pass
else:raise AssertionError('nonfinite accepted')
result=dict(reference_episodes=len(reports),reference_passed=sum(x['passed'] for x in reports),all_saved_reasons_and_metrics_match=True,action_batches=180,action_rows=1080,max_action_step=maxstep,nan_rejected=True,training_ready=False,goal_complete=False,source_sha256=hashlib.sha256(Path('SimFoundry/simfoundry/data/search_expert_interface.py').read_bytes()).hexdigest())
(root/'INTERFACE_VERIFICATION.json').write_text(json.dumps(result,indent=2));print(result)
