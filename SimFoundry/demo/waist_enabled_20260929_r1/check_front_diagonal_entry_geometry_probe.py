"""Independent LP separation check and recorded initial contact lever screen.
Assuming force aligns with a proposed path is only an algebraic hypothesis.
"""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy.optimize import linprog
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;sys.path.insert(0,str(w));from front_diagonal_entry_geometry_probe import segment_gap,propose
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();rng=np.random.default_rng(426);checks=[]
for i in range(120):
 a=rng.uniform([.3,-.3],[.8,.3]);b=rng.uniform([.3,-.3],[.8,.3]);o=rng.uniform([.4,-.2],[.7,.2]);rad=rng.uniform(.05,.18,2);d=b-a;s=a-o
 A=np.array([[d[0],-1],[-d[0],-1],[d[1],-1],[-d[1],-1]]);rhs=np.array([-s[0]+rad[0],s[0]+rad[0],-s[1]+rad[1],s[1]+rad[1]])
 fit=linprog([0,1],A_ub=A,b_ub=rhs,bounds=[(0,1),(None,None)],method='highs');assert fit.success;out=segment_gap(a,b,o,rad);assert abs(fit.fun-out['minimum_axis_gap_m'])<1e-9;checks.append(abs(fit.fun-out['minimum_axis_gap_m']))
reports=[]
for cid in [840000,840001,840004,840005]:
 for task in ['push_box_to_bin','nudge_mailer_to_bin']:
  ep=w/'self_clearance_groups_r1'/f'case_{cid}/layout_{cid}_{task}';key='box' if task=='push_box_to_bin' else 'mailer';other='mailer' if key=='box' else 'box';size=np.array([.14,.09,.045] if key=='box' else [.15,.145,.04]);osize=np.array([.15,.145,.04] if key=='box' else [.14,.09,.045])
  with np.load(ep/'trace.npz') as z:target=z[key][0];obstacle=z[other][0]
  with np.load(ep/'parcel_orientation.npz') as z:quat=z[key][0];oquat=z[other][0]
  plan=propose(target,obstacle,size,osize,quat,oquat,-1 if key=='box' else 1)
  tr=abs(Rotation.from_quat(quat).as_matrix())@size/2;orr=abs(Rotation.from_quat(oquat).as_matrix())@osize/2
  for row in plan['routes']:
   for a,b in zip(row['points'],row['points'][1:]):
    samples=np.array(a)[None]+np.linspace(0,1,1001)[:,None]*(np.array(b)-a);g=np.max(abs(samples-obstacle[:2])-tr[:2]-orr[:2],axis=1)
    if row['eligible']:assert g.min()>=.012-1e-9
  fr=json.loads((ep/'frontal_bypass.json').read_text());reports.append(dict(episode=ep.name,original_front_selected=bool(fr['plan'].get('front_route_selected')),proposal=plan,source_sha256={n:sha(ep/n) for n in ['trace.npz','parcel_orientation.npz','frontal_bypass.json']}))
# Use measured pre-action COP at first push for the two front-route episodes.
levers=[]
for run in ['self_clearance_groups_r1','front_direction_recontact_groups_r1']:
 for cid,task in [(840001,'nudge_mailer_to_bin'),(840004,'push_box_to_bin')]:
  ep=w/run/f'case_{cid}/layout_{cid}_{task}'
  if not (ep/'quality.json').exists():continue
  key='box' if task=='push_box_to_bin' else 'mailer';other='mailer' if key=='box' else 'box';side='right' if key=='box' else 'left';actor='parcel_box' if key=='box' else 'mailer';size=[.14,.09,.045] if key=='box' else [.15,.145,.04];osize=[.15,.145,.04] if key=='box' else [.14,.09,.045]
  fr=json.loads((ep/'frontal_bypass.json').read_text());t=next(x['step'] for x in fr['rows'] if x['mode']=='top_push');packet=next(x for x in json.loads((ep/'solved_contact_forces.json').read_text())['rows'] if x['after_action_step']==t-1)
  with np.load(ep/'trace.npz') as z:target=z[key][t];obstacle=z[other][t]
  with np.load(ep/'parcel_orientation.npz') as z:quat=z[key][t];oquat=z[other][t]
  R=Rotation.from_quat(quat).as_matrix();points=[];weights=[]
  for c in packet['parcel_contacts']:
   slots=[i for i,s in enumerate(c['shapes']) if '/'+actor+'/' in s]
   if len(slots)!=1 or not any(side+'_wrist' in s for s in c['shapes']):continue
   f=np.array(c['force_world_N'])*(1 if slots[0]==1 else -1);weight=-float(f@R[:,2])
   if weight>.05:points.append(c['position_world']);weights.append(weight)
  assert sum(weights)>.3;cop=np.average(points,axis=0,weights=weights);proposal=propose(target,obstacle,size,osize,quat,oquat,-1 if key=='box' else 1);vals=[]
  for row in proposal['routes']:
   direction=np.array(row['points'][1])-target[:2];direction/=np.linalg.norm(direction);lever=(cop[0]-target[0])*direction[1]-(cop[1]-target[1])*direction[0];vals.append(dict(route=row['route'],force_direction_hypothesis=direction.tolist(),signed_unit_force_lever_mm=float(lever*1000),eligible=row['eligible'],length_m=row['length_m']))
  levers.append(dict(run=run,episode=ep.name,step=t,current_cop_relative_mm=((cop-target)*1000).tolist(),routes=vals,source_sha256={n:sha(ep/n) for n in ['trace.npz','parcel_orientation.npz','frontal_bypass.json','solved_contact_forces.json']}))
out=dict(passed=True,independent_random_lp_checks=120,max_lp_error=max(checks),original_eight_proposals=reports,initial_contact_force_line_hypotheses=levers,scope=__doc__,source_sha256={str(p):sha(p) for p in [Path(__file__),w/'front_diagonal_entry_geometry_probe.py']},collector_wired=False,physical_validation=False,training_ready=False);(w/'FRONT_DIAGONAL_ENTRY_GEOMETRY_PROBE.json').write_text(json.dumps(out,indent=2));print(json.dumps(dict(lpchecks=120,max_lp_error=max(checks),initial_contact_force_line_hypotheses=levers),indent=2))
