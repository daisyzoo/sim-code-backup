"""Freeze unseen evaluation geometry without invoking simulation or success filtering."""
from pathlib import Path
import sys,json,hashlib,math,datetime
import numpy as np
root=Path(__file__).resolve().parent;sys.path.insert(0,str(root.parents[1]))
from simfoundry.data.diverse_layouts import validate_diagnostic_layout,validate_geometry_split
from simfoundry.calibration.sorting_station import TABLE_TOP_BOX_Z,TABLE_TOP_MAILER_Z
out=root/'independent_geometry_r1'
if out.exists():raise FileExistsError('Frozen holdout must never be regenerated in place')
rng=np.random.default_rng(202609291731);groups=[];layouts=[];counts={k:0 for k in ['lateral','depth','diagonal_positive','diagonal_negative']};attempts=0;invalid=0;overquota=0
while len(groups)<16:
 attempts+=1
 if attempts>200000:raise RuntimeError('Unable to fill predefined geometry strata')
 slots=rng.uniform([.36,-.18],[.62,.18],size=(2,2));delta=slots[1]-slots[0]
 if abs(delta[0])<.35*abs(delta[1]):kind='lateral'
 elif abs(delta[1])<.35*abs(delta[0]):kind='depth'
 else:kind='diagonal_positive' if delta[0]*delta[1]>0 else 'diagonal_negative'
 if counts[kind]>=4:overquota+=1;continue
 yaw=rng.uniform(-.35,.35,2);seed=int(rng.integers(1,2**31-1));i=len(groups);name=f'waist_independent_r1_{kind}_{counts[kind]:02d}';pair=[]
 for swap in (0,1):
  box=slots[swap];bag=slots[1-swap];layout=dict(layout_id=900000+2*i+swap,seed=seed,geometry_group=name,assignment='swapped' if swap else 'normal',planned_split='test',box_xyz=[float(box[0]),float(box[1]),TABLE_TOP_BOX_Z],mailer_xyz=[float(bag[0]),float(bag[1]),TABLE_TOP_MAILER_Z],box_yaw=float(yaw[0]),mailer_yaw=float(yaw[1]))
  try:validate_diagnostic_layout(layout,layout['layout_id'])
  except ValueError:invalid+=1;break
  pair.append(layout)
 if len(pair)!=2:continue
 layouts.extend(pair);counts[kind]+=1;groups.append(dict(geometry_group=name,stratum=kind,layout_ids=[x['layout_id'] for x in pair]))
records=[dict(layout_id=x['layout_id'],geometry_group=x['geometry_group'],assignment=x['assignment'],task_id=task) for x in layouts for task in ['push_box_to_bin','nudge_mailer_to_bin']]
assert len(validate_geometry_split(records,{r['layout_id'] for r in records}))==16
# Category swap must preserve the same two slots, per-category yaw and physics seed.
for a,b in zip(layouts[::2],layouts[1::2]):
 assert a['box_xyz'][:2]==b['mailer_xyz'][:2] and b['box_xyz'][:2]==a['mailer_xyz'][:2]
 assert a['seed']==b['seed'] and a['box_yaw']==b['box_yaw'] and a['mailer_yaw']==b['mailer_yaw']
# Reject accidental exact duplicates of current development geometry (without test outcomes).
dev=[]
for p in (root/'development_layouts').glob('[0-9]*.json'):
 d=json.loads(p.read_text());dev.append(sorted([d['box_xyz'][:2],d['mailer_xyz'][:2]]))
assert all(sorted([x['box_xyz'][:2],x['mailer_xyz'][:2]]) not in dev for x in layouts)
out.mkdir();hashes={}
for x in layouts:
 p=out/f"{x['layout_id']}.json";p.write_text(json.dumps(x,indent=2)+'\n');hashes[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
manifest=dict(version=1,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),purpose='Final independent model h10 evaluation only; no controller/hyperparameter tuning, no training conversion',geometry_frozen=True,evaluation_ready=False,training_ready=False,generator_seed=202609291731,generator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),groups=groups,layout_sha256=hashes,strata_counts=counts,geometry_groups=16,assignments=32,push_tasks_per_assignment=2,pushing_conditions_per_inference_seed=64,inference_seeds=[0,1,2],planned_pushing_rollouts=192,wait_seeds=[0,1,2],planned_wait_rollouts=3,horizon=10,motion_protocol='waist_yaw_enabled_v1',initial_upper11_state_zero=True,object_assist_frames=0,nontarget_max_xy_m=.015,original_quality_gates_preserved=True,original_action_step_limit_rad=.08,require_pose_and_actual_visual_review=True,planned_split='test',evaluation_episode_budget_frames=None,waiting_budget_frames=None,checkpoint_and_processor_hashes=None,release_requirement='Freeze trained candidate, state/action codec, saved train-only normalization, waist work range, push/wait budgets and evaluation command BEFORE running any of these layouts. Refuse evaluation_ready until release configuration is completed; no outcome-based removal or replacement.',sampling=dict(slot_xy_independent_uniform_bounds=[[.36,-.18],[.62,.18]],category_yaw_uniform_rad=[-.35,.35],per_category_yaw_and_physics_seed_fixed_across_assignment_swap=True,strata_definition='abs(dx)<.35abs(dy):lateral; abs(dy)<.35abs(dx):depth; remainder by sign(dx*dy)',attempts=attempts,rejections_invalid_initial_geometry=invalid,rejections_filled_stratum=overquota,filter='Only existing initial-footprint/table/20mm AABB-clearance validation for BOTH assignments plus fixed stratum quotas. No reachability, expert success, model score or camera-outcome filtering.'),scope='Random continuous poses within documented diagnostic table bounds; stratified for coverage, not arbitrary tabletops/object types/occlusions. Some layouts may remain unsolved; report failures and never drop them to redefine success.')
(out/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
(out/'README.md').write_text('''# 冻结独立几何：尚未执行\n\n16个几何组，左右/前后/正斜/反斜各4组；每组2种类别交换、各2个任务，共64个推动条件。推理种子0/1/2共192条推动，另3条等待。h10、零位、无助推、非目标1.5cm及原其余门保留。\n\n位置连续随机抽样；仅用原初始桌面/两物体几何合法性检查，未按可达性或任务成败筛选。每个交换组共用物理seed、类别自身朝向，槽位完全互换。源JSON逐文件SHA256已冻结。\n\n**不用于当前专家/模型调参，不准训练转换。** 不删除难例后声称通过。推理结果必须按类别、布局层、种子分别报告。已有开发布局和空间39继续只作开发/回归。\n\n当前evaluation_ready=false；须在首次执行前冻结候选checkpoint/处理器、腰工作范围、推送/等待预算与完整评测命令。当前更长专家诊断预算不是已发布的模型评测预算，也没有统一成功率阈值已被用户确认的声明。\n''')
print(json.dumps({k:manifest[k] for k in ['geometry_groups','assignments','strata_counts','planned_pushing_rollouts','planned_wait_rollouts','evaluation_ready','training_ready']},indent=2))
