"""Actual collector-side dispatch and staged adapter compared to qualified0.5mm probe.
No physical run, recorded scenes are not counterfactual dynamics certification.
"""
from pathlib import Path
import sys,json,hashlib,ast,copy
from types import SimpleNamespace
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_box_inward_correction';sys.path[:0]=[str(stage),str(w),str(repo)]
import joint_edge_adapter as old
import joint_edge_inward_adapter as new
from joint_edge_inward_probe import refine_rear_command as probe
from clearance_runtime import ClearanceGuard
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();r=w/'box_entry_lift_groups_r1';qual=r/'INWARD_COMMAND_INDEPENDENT_CHECK.json';checked=json.loads(qual.read_text());assert checked['summary']['0.0005']['independent_passed']==63
for name,h in checked['source_sha256'].items():assert sha(Path(name))==h,name
source=r/'INWARD_COMMAND_SCREEN.json';screen=json.loads(source.read_text());wanted=[x['step'] for x in screen['rows'] if x['inward_step_m']==.0005];assert len(wanted)==len(set(wanted))==63
tree=ast.parse((stage/'collect_paired_sorting.py').read_text());outer=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and any(isinstance(x,ast.ImportFrom) and x.module=='joint_edge_adapter' for x in n.body));nodes=outer.body[:2];assert isinstance(nodes[0],ast.ImportFrom) and isinstance(nodes[1],ast.If);dispatch=[]
for enabled in [False,True]:
 for side in ['left','right']:
  ctx=dict(args=SimpleNamespace(rear_box_inward_correction=enabled),side=side);exec(compile(ast.Module(body=nodes,type_ignores=[]),'<collector dispatch>','exec'),ctx);expected=new.refine_record if enabled and side=='right' else old.refine_record;assert ctx['refine_record'] is expected;dispatch.append(dict(enabled=enabled,side=side,adapter=ctx['refine_record'].__module__))
ep=r/'case_840001/layout_840001_push_box_to_bin';fr=json.loads((ep/'frontal_bypass.json').read_text());fs={x['step']:x for x in fr['rows']};cs={x['step']:x for x in json.loads((ep/'coordination.json').read_text())};core=fr['plan']['rear_cop_centering']['actual_core_size_xyz'];guard=ClearanceGuard(repo,stage)
with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].copy();u=z['action'][:,12:23].copy()
with np.load(ep/'trace.npz') as z:xyz=z['box'].copy()
with np.load(ep/'parcel_orientation.npz') as z:R=Rotation.from_quat(z['box']).as_matrix()
original=old.refine_rear_command;rows=[]
try:
 old.refine_rear_command=lambda **kw:probe(**kw,inward_step_m=.0005)
 for t in wanted:
  f=fs[t];c=cs[t];tr=c['joint_edge_refinement'];args=dict(enabled=True,row=f,coordinate=c,current=q[t],previous=u[t-1],parent_command=tr['parent_final_upper_command'],object_xyz=xyz[t],object_rotation=R[t],core_size=core,model=guard.model,side='right',analytic_retry=True,parent_seed_retry=True);baseline,b=old.refine_record(**args);cmd,e=new.refine_record(**args);assert np.array_equal(cmd,baseline);assert e['nominal_inward_requirement_m']==.0005 and e['physical_motion_prediction'] is False
  restored=copy.deepcopy(e);restored.pop('nominal_inward_requirement_m');restored.pop('physical_motion_prediction')
  for key,residual in [('parent_nominal_edge_inward_m','parent_edge_constraint_residual_m'),('nominal_edge_inward_m','edge_constraint_residual_m')]:
   if residual in restored:
    assert np.array_equal(np.array(restored[key]),np.array(restored[residual])+.0005);restored[key]=restored.pop(residual)
  assert restored==b;assert guard.command(cmd,q[t],u[t-1])['accepted'];rows.append(dict(step=t,command_exact_to_same_input_probe=True,metadata_consistent=True));print(t,'passed',flush=True)
finally:old.refine_rear_command=original
files=[Path(__file__),qual,source,stage/'collect_paired_sorting.py',stage/'joint_edge_inward_adapter.py',stage/'joint_edge_inward_command.py',stage/'joint_edge_adapter.py',w/'joint_edge_inward_probe.py',stage/'clearance_runtime.py'];(stage/'ADAPTER_CHECK.json').write_text(json.dumps(dict(passed=True,scope=__doc__,actual_dispatch=dispatch,rows=rows,source_sha256={str(p):sha(p) for p in files},physical_validation=False,training_ready=False),indent=2));print('PASS63 and4dispatch')
