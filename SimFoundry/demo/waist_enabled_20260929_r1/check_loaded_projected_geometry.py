"""Audit recorded virtual-reference Jacobians; compare static allocations consistently."""
from pathlib import Path
import sys,json,hashlib,importlib.util
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path.insert(0,str(repo))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def module(p,name):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
priorpath=w/'loaded_coupled_allocation_probe_r1/RESULT.json';lppath=priorpath.with_name('X_FEASIBILITY.json');prior=json.loads(priorpath.read_text());lp=json.loads(lppath.read_text());reports=[]
for case,lc in zip(prior['episodes'],lp['episodes']):
 assert case['episode']==lc['episode'];ep=w/case['run']/('case_'+case['episode'].split('_')[1])/case['episode'];src=json.loads((ep.parent/'provenance.json').read_text())['source_sha256'];snap=ep.parent/'source_snapshot'
 for name,h in case['source_sha256'].items():assert sha(ep/name)==h
 for name,h in case['asset_sha256'].items():assert sha(repo/name)==h
 gr=next(x for x in src if x.endswith('/articulated_hand_geometry.py'));pr='simfoundry/data/projected_support_reference.py'
 for rel in [gr,pr]:assert sha(snap/rel)==src[rel]
 gm=module(snap/gr,'geom');pm=module(snap/pr,'proj');model=gm.ArticulatedHandGeometry(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json');side='right' if 'push_box' in ep.name else 'left';inactive='left' if side=='right' else 'right'
 cs={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};fs={r['step']:r for r in json.loads((ep/'frontal_bypass.json').read_text())['rows']};lps={r['step']:r for r in lc['rows']};rows=[]
 for sample in case['rows']:
  if not sample['loaded']:continue
  t=sample['step'];c=cs[t];f=fs[t];q=np.array(c['upper_q']);ref=c['active_support_reference'];normal=np.array(ref['world_normal']);center=np.array(ref['center_local'])
  def point(hand,qv):
   T,_,_=model.fk(hand,qv)
   off=pm.projected_support_reference(model.vertices[hand],T[:3,:3],normal,center_local=center)['reference_local'] if hand==side else np.array([.2,0,.007])
   return T[:3,3]+T[:3,:3]@off
  def both(qv):return np.r_[point('left',qv),point('right',qv)]
  observed=np.r_[c['control_point_positions']['left'],c['control_point_positions']['right']];point_error=float(max(abs(both(q)-observed)));eps=1e-5;fd=np.column_stack([(both(q+np.eye(11)[j]*eps)-both(q-np.eye(11)[j]*eps))/(2*eps) for j in range(11)]);jac_error=float(np.max(abs(fd-np.array(c['control_jacobian_world']))))
  assert point_error<2e-6,(t,point_error)
  assert jac_error<2e-4,(t,jac_error)
  probes=[]
  cmds=[('y_scale_'+str(p['y_error_scale']),np.array(p['command'])) for p in sample['probes']]
  if lps[t]['success']:cmds.append(('linear_lp',np.array(lps[t]['candidate_command'])))
  for kind,cmd in cmds:
   T,_,_=model.fk(side,cmd);up=T[:3,:3].T@np.array([0.,0.,1.]);angle=float(np.arccos(np.clip(up@c['contact_normal_tracking']['target_local_up'],-1,1)))
   probes.append(dict(kind=kind,goal_minus_projected_fk_mm=((np.array(f['target_xyz'])-point(side,cmd))*1000).tolist(),inactive_anchor_error_mm=float(np.linalg.norm(point(inactive,cmd)-c['inactive_anchor'])*1000),normal_angle_error_rad=angle))
  rows.append(dict(step=t,current_reference_max_error_m=point_error,jacobian_max_error_m_per_rad=jac_error,probes=probes))
 reports.append(dict(run=case['run'],episode=case['episode'],rows=rows,projected_source_sha256=src[pr]))
out=dict(passed=True,episodes=reports,loaded_samples=sum(len(r['rows']) for r in reports),source_replay_sha256=sha(priorpath),source_lp_sha256=sha(lppath),checker_sha256=sha(Path(__file__)),training_ready=False,scope='Uses recorded calibrated center_local and fixed current object normal, recomputes orientation-dependent virtual support reference for each FK. Central finite difference checks recorded Jacobian. Static geometry only; not actual future contact or dynamics. Earlier fixed-offset FK reports describe a different material reference and remain preserved.')
p=priorpath.with_name('PROJECTED_GEOMETRY_CHECK.json');assert not p.exists();p.write_text(json.dumps(out,indent=2));print('passed',out['loaded_samples'])
for case in reports:
 print(case['episode'],case['run'],'maxJ',max(r['jacobian_max_error_m_per_rad'] for r in case['rows']))
 for r in case['rows']:print(r['step'],[(p['kind'],round(p['goal_minus_projected_fk_mm'][0],3),round(p['inactive_anchor_error_mm'],3)) for p in r['probes']])
