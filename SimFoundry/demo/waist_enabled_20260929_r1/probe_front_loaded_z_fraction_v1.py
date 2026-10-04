"""Unissued single-observation reduced-Z task probe at three archived failures.
For fractions .25/.5/.75/1, interpolate the linear Z target from the original
parent-achieved linear displacement to its requested displacement. This changes
both the Z objective and equality deliberately; all original nominal attitude,
elbow, table, joint/slew, and non-target separation checks are retained.
NOT a closed-loop replay, certified original task solution, or force prediction.
"""
from pathlib import Path
import sys,json,copy,hashlib,datetime
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_corridor_lateral_v1';sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from loaded_z_priority_solver import solve
from loaded_z_priority_checks import NativeCertificateGeometry,check,support_point,nominal_separation_path
from audit_unloaded_wrist_prior_live import HandModel
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_text())
D=W/'front_loaded_z_fraction_probe_r1';D.mkdir(exist_ok=False)
guard=ClearanceGuard(ROOT,S);geometry=NativeCertificateGeometry(guard)
independent=HandModel(ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',ROOT/'assets/robots/g1_hand_support_vertices.json')
axis=np.linalg.eigh(np.cov(independent.vertices['left'].T))[1][:,-1]
def independent_support(q,n,center):
 M=independent.fk(q,'left');local=M[:3,:3].T@n;ref=center+local*(min(independent.vertices['left']@local)-center@local)
 return M[:3,3]+M[:3,:3]@ref,M
def heading(M):v=M[:3,:3]@axis;return np.arctan2(v[1],v[0])
rows=[];sources={}
for run,t in [('joint_transport_reserve_physical_r1',592),('rear_trailing_physical_r1',648),('front_corridor_lateral_physical_r1',648)]:
 ep=W/run/'case_840023/layout_840023_nudge_mailer_to_bin';coord=next(r for r in read(ep/'coordination.json') if r['step']==t);p=coord['front_loaded_z_priority'];ctx=p['context'];assert p['applied']
 a=coord['task_inputs'];q=np.asarray(ctx['current']);previous=np.asarray(ctx['previous']);parent=np.asarray(ctx['parent_command']);J=np.asarray(a['jacobian']);e=np.asarray(a['error']);zr=2
 np.testing.assert_allclose(q,a['current'],atol=1e-7,rtol=0)
 with np.load(ep/'raw.npz') as z:
  np.testing.assert_allclose(q,z['q'][t,12:23],atol=1e-7,rtol=0);np.testing.assert_array_equal(previous,z['action'][t-1,12:23])
 n=np.asarray(ctx['target_rotation'])[:,2];center=np.asarray(ctx['center_local']);actual,M0=independent_support(q,n,center);base,MP=independent_support(parent,n,center)
 start=float(J[zr]@(parent-q));requested=float(e[zr]);assert start>requested
 for fraction in [.25,.5,.75,1.]:
  task=copy.deepcopy(a);task['error'][zr]=start+fraction*(requested-start)
  x,solver=solve(task,parent=parent,side='left',target_up=coord['contact_normal_tracking']['target_local_up'],hand=guard.model,elbows=geometry)
  verification=check(guard,geometry,task,coord,parent,x,'left');final=guard.command(x,q,previous)
  paths={s:nominal_separation_path(guard.model,q,x,s,np.asarray(ctx['other_xyz']),np.asarray(ctx['other_rotation']),np.asarray(ctx['conservative_other_size'])) for s in ['left','right']}
  ip,IM=independent_support(x,n,center);np.testing.assert_allclose(ip,support_point(guard.model,x,'left',n,center),atol=2e-9,rtol=0)
  turn=heading(IM)-heading(M0);turn=float(np.degrees(np.arctan2(np.sin(turn),np.cos(turn))))
  accepted=bool(verification['passed'] and final['accepted'] and all(v['certified'] for v in paths.values()) and ip[2]<actual[2] and abs(ip[2]-actual[2]-requested)<abs(base[2]-actual[2]-requested))
  row=dict(run=run,step=t,fraction=fraction,original_requested_z_mm=requested*1000,modified_linear_z_target_mm=task['error'][zr]*1000,parent_nominal_support_dz_mm=float(1000*(base[2]-actual[2])),candidate_nominal_support_dz_mm=float(1000*(ip[2]-actual[2])),nominal_heading_change_deg=turn,accepted_nominal_modified_task=accepted,command=x.tolist(),solver=solver,verification=verification,final_guard=final,paths=paths)
  rows.append(row);print(json.dumps({k:v for k,v in row.items() if k not in ['command','solver','verification','final_guard','paths']}),flush=True)
  (D/'PROGRESS.json').write_text(json.dumps(dict(rows=rows,expected=12,physical_validation=False,training_ready=False),indent=2))
 for name in ['coordination.json','raw.npz']:sources[str(ep/name)]=sha(ep/name)
for mod in list(sys.modules.values()):
 f=getattr(mod,'__file__',None)
 if f:
  p=Path(f).resolve()
  if p.is_file() and p.suffix=='.py' and p.is_relative_to(ROOT):sources[str(p)]=sha(p)
for p in [Path(__file__),S/'elbow_torso_hulls.json',ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',ROOT/'assets/robots/g1_hand_support_vertices.json']:sources[str(p)]=sha(p)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,source_sha256=sources,controller_changed=False,physics_started=False,training_ready=False,limitations=['Fractions are exploratory declared design parameters, not new quality gates or selected production settings.','No force or bag yaw response prediction is justified by this static probe.','Prior action/history remain actual; candidate outputs never become synthetic later observations.','A reduced Z target deliberately differs from the original equality; approval here covers the modified nominal task only.','Transport after the Z stage is not recomputed in this probe; no claim of a valid final full controller command.'])
with (D/'RESULT.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(complete=True,rows=len(rows),accepted=sum(r['accepted_nominal_modified_task'] for r in rows))),flush=True)
