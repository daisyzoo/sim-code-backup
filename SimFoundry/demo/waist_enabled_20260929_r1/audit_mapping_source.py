from pathlib import Path
import json,sys,hashlib
import numpy as np
import torch
sys.path.insert(0,str(Path('SimFoundry').resolve()))
sys.path.insert(0,str(Path('lerobot/unitree_lerobot_yth_repro_20260908/unitree_lerobot_yth/unitree_lerobot/lerobot/src').resolve()))
# Execute exact pure mapping definitions without importing simulator runtime.
import ast
source=Path('SimFoundry/simfoundry/data/unitree_json.py')
tree=ast.parse(source.read_text())
nodes=[n for n in tree.body if (isinstance(n,ast.FunctionDef) and n.name in ('_qpos_group','_split_23')) or (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ('_LEFT_ARM','_RIGHT_ARM','_WAIST_YAW') for t in n.targets))]
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(source),'exec'))
from lerobot.policies.pi05.joint_relative import joint_action_transform
root=Path('SimFoundry/demo/waist_enabled_20260929_r1')
raw=root/'empty_probe/layout_10000_wait_no_package/raw.npz'
with np.load(raw) as z:q=z['q'].copy();a=z['action'].copy()
ix=[*range(13,23),12]
exported=[]
for row in a:
 g=_split_23(row);exported.append(g['left_arm']['qpos']+g['right_arm']['qpos']+[g['body']['qpos'][0]])
exported=np.array(exported)
action=torch.from_numpy(a[:,ix])[:,None,:].repeat(1,10,1)
state=torch.from_numpy(q[:,ix]);encoded=joint_action_transform(action,state)
decoded=joint_action_transform(encoded,state,inverse=True)
out=dict(raw_sha256=hashlib.sha256(raw.read_bytes()).hexdigest(),frames=len(q),unitree_mapping_max_error=float(abs(exported-a[:,ix]).max()),relative_roundtrip_max_error=float(abs(decoded-action).max()),relative_waist_preservation_max_error=float(abs(encoded[:,:,10]-action[:,:,10]).max()),mapping_method='Exact AST source definitions; simulator export I/O not executed',limitations='Actual nonzero waist raw mapping and relative encoding only; dataset processor normalization and model inference remain unverified.',training_ready=False)
assert max(out[k] for k in ('unitree_mapping_max_error','relative_roundtrip_max_error','relative_waist_preservation_max_error'))<1e-6
(root/'WAIST_MAPPING_AUDIT.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
