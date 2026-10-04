"""Actual loaded-input capture-view block and arguments on explicit fixtures.
Independent recovery verification is mocked only for this bookkeeping unit;
its full native/affine verification is separately bound by INDEPENDENT_STREAM_CHECK.
No modified physical trajectory or full-family admission is claimed.
"""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import ast,copy,datetime,hashlib,importlib,json,sys
import numpy as np
W=Path(__file__).resolve().parent;S=W/'staged_front_box_recenter_v3';D=W/'front_box_recenter_draft_r1';sys.path[:0]=[str(W),str(W.parents[1])]
from front_box_recenter_a2_loaded_episode_inputs import EpisodeInputs,indexed
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();prep=json.loads((S/'AUDIT_FAMILY_V2_PREPARATION.json').read_text());sources={}
for r in prep['adapters']:
 p=Path(r['parent']);t=Path(r['path']);assert sha(p)==r['parent_sha256'] and sha(t)==r['sha256'];back=t.read_text()
 for a,b in reversed(r.get('side_edits',[])):
  assert back.count(b)==1;back=back.replace(b,a)
 import re
 inv={v:k for k,v in prep['replacements'].items()}
 back=re.sub('|'.join(re.escape(k) for k in sorted(inv,key=len,reverse=True)),lambda m:inv[m.group()],back)
 assert back==p.read_text()
 tree0=ast.parse(t.read_text());executable=[n for n in tree0.body if not isinstance(n,(ast.Import,ast.ImportFrom,ast.FunctionDef,ast.ClassDef))]
 if any('sys.argv[' in ast.unparse(n) and not (isinstance(n,ast.If) and '__name__' in ast.unparse(n.test)) for n in executable):continue
 m=importlib.import_module(t.stem);assert Path(m.__file__).resolve()==t;sources[str(p)]=sha(p);sources[str(t)]=sha(t)
p=W/'front_box_recenter_a2_loaded_episode_inputs.py';tree=ast.parse(p.read_text());cls=next(n for n in tree.body if isinstance(n,ast.ClassDef));init=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='__init__');start=next(i for i,n in enumerate(init.body) if isinstance(n,ast.Assign) and ast.unparse(n.targets[0])=='self.initial_capture');end=next(i for i,n in enumerate(init.body) if isinstance(n,ast.Assign) and ast.unparse(n.targets[0])=='self.coords');code=compile(ast.fix_missing_locations(ast.Module(body=copy.deepcopy(init.body[start:end]),type_ignores=[])),str(p),'exec')
base=json.loads((D/'ALL_ELIGIBLE_LIFECYCLE_PROBE.json').read_text());records=[];negative=[]
for original_fixture in base['records']:
 if original_fixture['counter'] not in (2,6,12):continue
 f=dict(original_fixture,run='front_corridor_midpoint_physical_r1')
 ep=W/f['run']/'case_840020/layout_840020_push_box_to_bin';original=json.loads((ep/'front_initial_center.json').read_text());initial=indexed(original['rows'],1200);ev=f['events'][-1];t=ev['context']['step'];center=ev['captured_center_local'];recovery=dict(selected=True,training_ready=False,rows=[dict(step=i,kind='handover' if i==t else 'unchanged',context=dict(scene=dict(side='right')),center_local_after=center if i>=t else None) for i in range(1,1200)])
 with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].copy();u=z['action'][:,12:23].copy()
 for fallback in [False,True]:
  self=EpisodeInputs.__new__(EpisodeInputs);self.capture=copy.deepcopy(initial)
  if fallback:
   for row in self.capture.values():row['center_local_after']=None
  saved=copy.deepcopy(self.capture);self.front=original;self.side='right';self.n=1200;self.ep=Path('/tmp/explicit_bookkeeping_fixture');self.sources={};self.read=lambda name:copy.deepcopy(recovery)
  with patch('audit_front_box_recenter_stream.verify_files',return_value=dict(passed=True,selected=True)) as verify:
   exec(code,dict(self=self,indexed=indexed,W=W,sha=sha));verify.assert_called_once_with(self.ep)
  assert self.initial_capture==saved
  self.coords={};self.rows={};self.experts={};self.q=q;self.u=u;self.elbows=self.solver=self.hand=self.geometry=None;self.packets=[{}]*1200;self.xyz=self.oxy=np.zeros((1200,3));self.R=self.OR=np.tile(np.eye(3),(1200,1,1));self.size=[.14,.09,.045]
  for j in [0,t-1,t,t+1,1199]:
   out=self.arguments(j,{})
   expected=center if j>=t else saved.get(j,{}).get('center_local_after');assert out['selected']==(expected is not None)
   if expected is not None:assert out['capture_row']['center_local_after']==expected
   np.testing.assert_array_equal(out['current'],q[j]);np.testing.assert_array_equal(out['previous_actual'],u[j-1] if j else np.zeros(11));np.testing.assert_array_equal(out['output'],u[j])
  records.append(dict(run=f['run'],counter=f['counter'],initial_capture_fallback=fallback,unchanged_raw_q_action_and_previous=True,latest_independently_verified_capture_view=True))
  if len(records)==1:
   for label in ['failed_independent_stream','wrong_selection','wrong_context_side','missing_recovery_frame']:
    obj=EpisodeInputs.__new__(EpisodeInputs);obj.capture=copy.deepcopy(initial);obj.front=original;obj.side='left' if label=='wrong_context_side' else 'right';obj.n=1200;obj.ep=self.ep;obj.sources={};rr=copy.deepcopy(recovery)
    if label=='missing_recovery_frame':rr['rows'].pop(30)
    obj.read=lambda name:copy.deepcopy(rr)
    with patch('audit_front_box_recenter_stream.verify_files',side_effect=AssertionError('independent failure') if label=='failed_independent_stream' else None,return_value=dict(passed=True,selected=label!='wrong_selection')):
     try:exec(code,dict(self=obj,indexed=indexed,W=W,sha=sha))
     except AssertionError:negative.append(label)
     else:raise AssertionError('bad capture reader accepted '+label)
from front_box_recenter_a2_v4_stage_run_contract import primary,controls,ADDITIONAL,REPORTS
plan=json.loads((W/'front_corridor_midpoint_physical_r1/PROTOCOL.json').read_text())['plan'];total=0
for c in plan['commands']:
 for task in c['tasks']:
  ep=W/'front_corridor_midpoint_physical_r1'/f"case_{c['layout_id']}"/f"layout_{c['layout_id']}_{task}";scripts=primary(c['wait'])+['audit_front_box_recenter_a2_v1_stage_contacts.py','audit_front_box_recenter_a2_v1_stage_pressure.py']
  if not c['wait']:scripts+=controls(json.loads((ep/'frontal_bypass.json').read_text())['plan'])+ADDITIONAL
  scripts+=['audit_front_box_recenter_a2_v1_stage_release.py'];scripts=list(dict.fromkeys(scripts));assert scripts[0]=='audit_front_box_recenter_a2_v2_execution.py';assert all(x in REPORTS and (W/x).is_file() for x in scripts);total+=len(scripts)
assert total==214
for p in [Path(__file__),S/'AUDIT_FAMILY_V2_PREPARATION.json',S/'INDEPENDENT_STREAM_CHECK.json',D/'ALL_ELIGIBLE_LIFECYCLE_PROBE.json']:sources[str(p)]=sha(p)
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,records=records,negative_cases=negative,full_inventory=214,source_sha256=sources,full_audit_family_ready=False,native_new_episode_not_available=True,simulation_started=False,training_ready=False)
with (S/'LOADED_INPUT_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,fixtures=len(records),negative=len(negative),audit_inventory=total)))
