"""Replay three actual-start hypothetical plan-selection proofs independently.
No candidate control imports, no simulated contact or physical task claim.
"""
from pathlib import Path
import json,sys,hashlib,datetime,copy
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];S=W/'staged_front_box_trailing_v1';sys.path[:0]=[str(D),str(S),str(W),str(ROOT)]
from audit_trailing_planning import SelectionAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();src=W/'front_box_trailing_runtime_preparation_r2/MOVING_RUNTIME_CHECK.json';data=json.loads(src.read_text());assert data['complete']
for p,h in data['source_sha256'].items():assert sha(p)==h,p
prep=json.loads((D/'SELECTION_AUDITOR_PREPARATION.json').read_text())
for record in prep['derivations']:
 for k in ['parent','candidate']:assert sha(record[k])==record[k+'_sha256']
rows=[]
for case in data['rows']:
 planning=case['trace'][0]['event']['planning'];ctx=planning['transport_preflight']['initial_context'];kwargs=dict(current=ctx['current'],previous_q=ctx['previous_q'],previous_command=ctx['previous_command'],decay=ctx['decay'],scene=planning['scene'],step=ctx['step']);audit=SelectionAudit(ROOT,S);actual=audit.verify_selection(planning,**kwargs);neg=[]
 for label in ['planning_reserve','predicted_ready','predicted_ticks']:
  bad=copy.deepcopy(planning)
  if label=='planning_reserve':bad['planning_xy_reserve_m']=0.
  if label=='predicted_ready':bad['transport_preflight']['trials'][0]['events'][0]['measured_ready_count']=3
  if label=='predicted_ticks':bad['transport_preflight']['trials'][-1]['predicted_ticks']+=1
  try:audit.verify_selection(bad,**kwargs)
  except AssertionError:neg.append(label)
  else:raise AssertionError('Bad plan accepted:'+label)
 r=dict(step=ctx['step'],result=actual,negative_rejections=neg);rows.append(r);(D/'SELECTION_AUDIT_PROGRESS.json').write_text(json.dumps(dict(completed=len(rows),expected=3,rows=rows,training_ready=False),indent=2));print(json.dumps(r),flush=True)
sources={str(p):sha(p) for p in [Path(__file__),src,D/'SELECTION_AUDITOR_PREPARATION.json',S/'elbow_torso_hulls.json',ROOT/'assets/robots/g1_hand_support_vertices.json',ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf']}
for mod in list(sys.modules.values()):
 f=getattr(mod,'__file__',None)
 if f:
  p=Path(f).resolve()
  if p.is_file() and p.suffix=='.py' and p.is_relative_to(ROOT):sources[str(p)]=sha(p)
assert not any(x.startswith('trailing_') for x in sys.modules)
with (D/'SELECTION_AUDIT_CHECK.json').open('x') as f:json.dump(dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,rows=rows,source_sha256=sources,candidate_imports=False,physical_started=False,training_ready=False),f,indent=2)
print('COMPLETE3',flush=True)
