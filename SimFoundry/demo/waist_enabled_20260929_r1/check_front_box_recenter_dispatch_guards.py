"""Execute native final command branch; right opt-in marker and all original guards."""
from pathlib import Path
from types import SimpleNamespace as NS
import ast,copy,json,hashlib,datetime,sys
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_box_recenter_v3';D=W/'front_box_recenter_draft_r1';sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();guard=ClearanceGuard(ROOT,S)
src=S/'waist_coordination_clearance.py';tree=ast.parse(src.read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='coordinated_step');branches=[n for n in fn.body if isinstance(n,ast.If) and (ast.unparse(n.test).startswith('sum(') or ast.unparse(n.test)=='front_recontact_override is not None')]
f=ast.FunctionDef(name='dispatch',args=ast.arguments(posonlyargs=[],args=[],kwonlyargs=[],kw_defaults=[],defaults=[]),body=copy.deepcopy(branches)+[ast.Return(value=ast.Constant(None))],decorator_list=[]);code=compile(ast.fix_missing_locations(ast.Module(body=[f],type_ignores=[])),str(src),'exec')
class Tensor:
 def __init__(self,v):self.v=np.asarray(v)
 def __getitem__(self,k):return Tensor(self.v[k])
 def detach(self):return self
 def cpu(self):return self
 def numpy(self):return self.v
right=copy.deepcopy(read(D/'ALL_ELIGIBLE_LIFECYCLE_PROBE.json')['records'][0]['events'][0]);right.update(real_recontact_index=right['context']['recontacts'],front_box_recenter_version='front_box_recenter_v1')
def namespace(e):
 c=e['context'];return dict(np=np,front_recontact_override=copy.deepcopy(e),front_initial_override=None,recontact_override=None,indices=list(range(12,23)),robot=NS(data=NS(joint_pos=NS(torch=Tensor([np.r_[np.zeros(12),c['current']]])))),joint_ids=list(range(12,23)),bounded=True,clearance_geometry=guard.geometry,default=np.zeros(23),previous_command=np.array(c['previous_command']),state=NS(side=c['scene']['side']),action=np.zeros(23),palms={},points={},active_point_offset=None,anchor={'left':[0,0,0],'right':[0,0,0]},active_support_reference={})
def call(ns):exec(code,ns);return ns['dispatch']()
base=namespace(right);r=call(base);assert r['active_side']=='right';np.testing.assert_array_equal(base['action'][12:23],np.array(right['command'],np.float32))
neg=[]
def reject(label,mutate):
 ns=namespace(right);mutate(ns)
 try:call(ns)
 except ValueError:assert not np.any(ns['action']);neg.append(label)
 else:raise AssertionError('Accepted bad command: '+label)
reject('missing_right_opt_in',lambda n:n['front_recontact_override'].pop('front_box_recenter_version'))
reject('wrong_right_version',lambda n:n['front_recontact_override'].update(front_box_recenter_version='wrong'))
reject('wrong_arm',lambda n:setattr(n['state'],'side','left'))
for k,v in [('selected',False),('guard_stop',True),('recontacts',0),('observed_load_n',.001),('filtered_load_n',.051),('parent_mode','top_push')]:reject('context_'+k,lambda n,k=k,v=v:n['front_recontact_override']['context'].update({k:v}))
reject('counter_binding',lambda n:n['front_recontact_override'].update(real_recontact_index=99))
reject('wrong_scene_side',lambda n:n['front_recontact_override']['context']['scene'].update(side='left'))
reject('unbounded',lambda n:n.update(bounded=False))
reject('missing_geometry',lambda n:n.update(clearance_geometry=None))
reject('nonzero_default',lambda n:n['default'].__setitem__(12,.1))
reject('wrong_previous',lambda n:n['previous_command'].__setitem__(0,n['previous_command'][0]+.1))
reject('nonfinite_command',lambda n:n['front_recontact_override']['command'].__setitem__(0,float('nan')))
reject('wrong_command',lambda n:n['front_recontact_override']['command'].__setitem__(0,n['front_recontact_override']['command'][0]+.001))
reject('unapproved_proposal',lambda n:n['front_recontact_override']['proposal'].update(applied=False))
for k in ['command_check','nominal_scene','predicted_scene']:reject('failed_'+k,lambda n,k=k:n['front_recontact_override']['proposal'][k].update(accepted=False))
reject('competing_initial',lambda n:n.update(front_initial_override={}))
reject('competing_rear',lambda n:n.update(recontact_override={}))
oldpath=W/'front_bag_recontact_center_draft_r4/LIFECYCLE_CHECK.json';old=read(oldpath)['records'][0]['events'][0];old=copy.deepcopy(old);old['real_recontact_index']=old['context']['recontacts'];assert old['context']['scene']['side']=='left';left=namespace(old);assert call(left)['active_side']=='left';np.testing.assert_array_equal(left['action'][12:23],np.array(old['command'],np.float32))
prep=read(S/'COLLECTOR_PREPARATION.json')
for p,ee in prep['edits'].items():
 txt=(S/p).read_text()
 for e in reversed(ee):assert txt.count(e['new'])==1;txt=txt.replace(e['new'],e['old'])
 assert txt==(Path(prep['parent'])/p).read_text()
for p,ee in prep['new_source_edits'].items():
 txt=(S/p).read_text()
 for e in reversed(ee):txt=txt.replace(e['new'],e['old'])
 assert txt==(D/p).read_text()
result=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,valid_right_marked=True,original_left_unmarked_valid=True,negative=neg,exact_inverse_source_changes_verified=True,source_sha256={str(p):sha(p) for p in [Path(__file__),src,S/'COLLECTOR_PREPARATION.json',D/'ALL_ELIGIBLE_LIFECYCLE_PROBE.json',oldpath]},physical_started=False,training_ready=False)
with (S/'DISPATCH_GUARD_CHECK.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps(dict(passed=True,negative=len(neg),original_left_preserved=True)))
