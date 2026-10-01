"""Nonlinear URDF one-step screen; static nominal geometry, not execution proof."""
from pathlib import Path
import json,hashlib,sys,importlib.util
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path.insert(0,str(repo));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def module(p,name):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
ip=w/'REAR_JOINT_XY_IK_SCREEN.json';sp=w/'REAR_JOINT_XY_DIRECTION_SCREEN.json';ik=json.loads(ip.read_text());screen=json.loads(sp.read_text());assert ik['screen_sha256']==sha(sp);reports=[]
for case in ik['episodes']:
 ep=w/'rear_coupled_progress_groups_r1'/('case_'+case['episode'].split('_')[1])/case['episode']
 for n,h in case['source_sha256'].items():assert sha(ep/n)==h
 prov=json.loads((ep.parent/'provenance.json').read_text());snap=ep.parent/'source_snapshot';gr=next(n for n in prov['source_sha256'] if n.endswith('/articulated_hand_geometry.py'));pr='simfoundry/data/projected_support_reference.py'
 for n in [gr,pr]:assert sha(snap/n)==prov['source_sha256'][n]
 model=module(snap/gr,'nonlinear_xy_geometry').ArticulatedHandGeometry(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json');pm=module(snap/pr,'nonlinear_xy_support');cs={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};side='right' if 'push_box' in ep.name else 'left';ai=list(range(3,6)) if side=='right' else list(range(3));direction=-1 if side=='right' else 1
 with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float)
 rows=[]
 for r in case['rows']:
  t=r['step'];c=cs[t];ref=c['active_support_reference'];normal=np.asarray(ref['world_normal']);center=np.asarray(ref['center_local']);up=np.asarray(c['contact_normal_tracking']['target_local_up'])
  def evaluate(cmd):
   T,_,_=model.fk(side,cmd);support=pm.projected_support_reference(model.vertices[side],T[:3,:3],normal,center_local=center);return T[:3,3]+T[:3,:3]@support['reference_local'],T,support['support_index']
  current,T,index=evaluate(q[t]);variants=[]
  for v in r['variants']:
   endpoint,Ts,idx=evaluate(np.asarray(v['command']));motion=endpoint-current;linear=np.asarray(v['active_predicted_step_xyz_mm'])/1000
   variants.append(dict(name=v['name'],nonlinear_point_step_mm=(motion*1000).tolist(),linear_step_error_mm=float(np.linalg.norm(motion-linear)*1000),nominal_normal_angle_rad=float(np.arccos(np.clip((Ts[:3,:3].T@np.array([0.,0.,1.]))@up,-1,1))),support_vertex_changed=bool(idx!=index)))
  rows.append(dict(step=t,loaded=r['loaded'],current_nominal_vs_measured_reference_mm=float(np.linalg.norm(current-np.asarray(c['control_point_positions'][side]))*1000),variants=variants))
 summaries=[]
 for j in range(2):
  rr=[r for r in rows if r['loaded']];v=[r['variants'][j] for r in rr];base=[r['variants'][0] for r in rr];gain=[direction*(a['nonlinear_point_step_mm'][1]-b['nonlinear_point_step_mm'][1]) for a,b in zip(v,base)]
  summaries.append(dict(name=v[0]['name'],loaded_frames=len(v),median_nonlinear_forward_point_step_mm=float(np.median([direction*a['nonlinear_point_step_mm'][1] for a in v])),median_forward_point_gain_mm=float(np.median(gain)),median_linear_step_error_mm=float(np.median([a['linear_step_error_mm'] for a in v])),max_linear_step_error_mm=max(a['linear_step_error_mm'] for a in v),median_nominal_normal_angle_rad=float(np.median([a['nominal_normal_angle_rad'] for a in v])),normal_angle_worse_over_0_001rad_frames=sum(a['nominal_normal_angle_rad']>b['nominal_normal_angle_rad']+.001 for a,b in zip(v,base)),support_vertex_changed_frames=sum(a['support_vertex_changed'] for a in v),max_nominal_vs_measured_reference_mm=max(r['current_nominal_vs_measured_reference_mm'] for r in rr)))
 reports.append(dict(episode=case['episode'],summary=summaries,rows=rows,archived_geometry_sha256={n:sha(snap/n) for n in [gr,pr]},current_asset_sha256=model.source_sha256));print(case['episode'],summaries)
out=dict(episodes=reports,ik_screen_sha256=sha(ip),checker_sha256=sha(Path(__file__)),training_ready=False,scope='Static nominal URDF FK/support-plane reference delta at recorded q and candidate joint command. Compares linearized point displacement to nonlinear point displacement and nominal hand normal. Nominal-to-measured residual reported, not calibrated away or proof of scene pose. No object motion, forces, full-arm collision, support-COP evolution, state rollout or physics. Assets bound to current bytes, not a new runtime safety certificate.')
p=w/'REAR_JOINT_XY_NONLINEAR_SCREEN.json';assert not p.exists();p.write_text(json.dumps(out,indent=2))
