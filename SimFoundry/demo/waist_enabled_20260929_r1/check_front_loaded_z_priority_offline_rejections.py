"""Targeted independent rejection checks on original archived nominal inputs.
Exercise exact attitude, feasible-but-nonstationary commands, and the previously
observed4.333mm elbow violation. No solver imports, generated trajectories or
relaxation of the original5mm/1e-6 stationarity conditions.
"""
from pathlib import Path
import json,hashlib,datetime,ast,sys
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path[:0]=[str(W),str(ROOT)]
from screen_bag_vertical_priority_geometry import Geometry
from audit_unloaded_wrist_prior_live import HandModel
from audit_self_clearance_task_optimality import IndependentElbows
from support_vertex_stationarity import certificate
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();auditfile=W/'audit_front_loaded_z_priority_offline_geometry.py';tree=ast.parse(auditfile.read_text());function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='evaluate');namespace=dict(np=np,certificate=certificate);exec(compile(ast.Module(body=[function],type_ignores=[]),str(auditfile),'exec'),namespace);evaluate=namespace['evaluate'];P=W/'FRONT_LOADED_Z_PRIORITY_CLEARANCE_FULL_OBSERVATIONS_PROBE.json';data=json.loads(P.read_text());rows=[];sources={str(P):sha(P),str(auditfile):sha(auditfile),str(Path(__file__)):sha(__file__)}
for epdata in data['episodes']:
 if not epdata['selected']:continue
 ep=next((W/'front_initial_physical_r1').glob('case_*/'+epdata['episode']));coords={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};g=Geometry(ep.parent);sources.update(g.sources)
 def archived(name):return next(Path(p) for p in g.sources if p.endswith('/'+name))
 hand=HandModel(archived('g1_23dof_rev_1_0_u1_black.urdf'),archived('g1_hand_support_vertices.json'));elbows=IndependentElbows(archived('elbow_torso_hulls.json'),archived('g1_23dof_rev_1_0_u1_black.urdf'));side='right' if 'push_box' in ep.name else 'left';r=epdata['rows'][0];t=r['step'];c=coords[t];a=c['task_inputs'];x=np.array(r['candidate_command']);parent=np.array(r['parent_command']);base=evaluate(a,c,x,parent,hand,elbows,g,side);assert base['passed']
 index=1 if side=='right' else 6;bad=x.copy();bad[index]+=.001;out=evaluate(a,c,bad,parent,hand,elbows,g,side);assert out['certificate']['primal_feasible'] and not out['passed'] and out['certificate']['reason']=='stationarity_failure'
 rows.append(dict(episode=ep.name,step=t,mutation='inactive_joint_feasible_but_nonstationary',rejected=True,result=out))
 zrow=np.array(a['jacobian'])[5 if side=='right' else 2];dq=np.eye(11)[10 if side=='right' else 5];dq-=zrow*(dq@zrow)/(zrow@zrow);witness=None
 for sign in [1.,-1.]:
  bad=x+sign*.01*dq;out=evaluate(a,c,bad,parent,hand,elbows,g,side)
  if not out['passed'] and out['certificate']['extra_values'][3]<-1e-7:witness=out;break
 assert witness is not None
 rows.append(dict(episode=ep.name,step=t,mutation='exact_attitude_worse_with_same_linear_z',rejected=True,result=witness))
 if side=='right':
  oldfile=W/'FRONT_LOADED_Z_ATTITUDE_PRIORITY_NONLINEAR_ONE_STEP_PROBE.json';old=json.loads(oldfile.read_text());er=next(e for e in old['episodes'] if e['episode']==ep.name);unsafe=next(r for r in er['rows'] if r['step']==352);c=coords[352];out=evaluate(c['task_inputs'],c,np.array(unsafe['candidate_command']),np.array(unsafe['parent_command']),hand,elbows,g,side)
  assert not out['passed'] and min(out['certificate']['elbow_gaps_m'])<.005-2e-7
  rows.append(dict(episode=ep.name,step=352,mutation='actual_prior_draft_elbow_violation',rejected=True,result=out));sources[str(oldfile)]=sha(oldfile)
 sources[str(ep/'coordination.json')]=sha(ep/'coordination.json')
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,checks=rows,all_rejected=True,source_sha256=sources,training_ready=False)
p=W/'FRONT_LOADED_Z_PRIORITY_OFFLINE_REJECTIONS.json'
with p.open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(checks=len(rows),all_rejected=True)))
