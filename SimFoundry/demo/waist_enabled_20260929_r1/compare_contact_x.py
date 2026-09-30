from pathlib import Path
import json,hashlib
import numpy as np
root=Path(__file__).resolve().parent/'contact_x_ablation_r1'
rows=[];near=[]
for variant in ['capped','uncapped']:
 audit=json.loads((root/variant/'CONTACT_AUDIT.json').read_text())
 for rec in audit['rows']:
  task=rec['episode'].split('62004_')[1];side='right' if task=='push_box_to_bin' else 'left';target='parcel_box' if side=='right' else 'mailer'
  contacts=[v for k,v in rec['contacts'].items() if f'{side}_wrist_roll' in k and f'/{target}/geometry/' in k]
  ep=root/variant/rec['episode']
  rows.append(dict(variant=variant,task=task,quality=rec['quality'],target_last_tick_max_force_N=max([v['max_force_N'] for v in contacts],default=0),first_target_force_above_1N=min([v['first_above_1N_after_action_step'] for v in contacts if v['first_above_1N_after_action_step'] is not None],default=None),motion_onset=rec['first_motion_pre_action_frame'],raw_sha256=hashlib.sha256((ep/'raw.npz').read_bytes()).hexdigest()))
  if side=='right':
   with np.load(ep/'raw.npz') as z,np.load(ep/'trace.npz') as tr:near.append(dict(q=z['q'].copy(),action=z['action'].copy(),box=tr['box'].copy()))
near_diff={k:float(abs(near[0][k]-near[1][k]).max()) for k in near[0]}
out=dict(rows=rows,unchanged_near_control_max_abs_difference=near_diff,scope='Single development layout, one run per variant, matched force observer and frozen settings except X cap. Near-object cap is inactive in both; control differences expose rollout repeatability limits. Last-tick force does not exclude unsampled substep contact. Not a model evaluation or training release.',training_ready=False)
(root/'COMPARISON.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
