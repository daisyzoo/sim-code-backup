"""Toy quasi-static single sticking point under uniform-pressure table friction.
Prescribes HAND point path for an80degree rotation, solves unconstrained parcel twist
from planar force/torque equilibrium, and checks point friction demand. No rigid-body
simulator, pressure redistribution, hand patch, torsion/rolling, inertia or joint tracking.
Use only to detect missing physical assumptions in prescribed-object pose planning.
"""
from pathlib import Path
import json,hashlib
import numpy as np
from numpy.polynomial.legendre import leggauss
from scipy.optimize import brentq
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();file=w/'ROTATION_LEVER_CONTACT_SCREEN.json';report=json.loads(file.read_text());size=np.array(report['episodes'][0]['actual_core']['collision_core_size_xyz']);old=json.loads((w/'ROTATED_ROUTE_STICKING_CONTINUATION.json').read_text());contacts={'prior_selected':np.array(old['fixed_parcel_material_point'][:2]),'near_edge':np.array([-size[0]/2+.010,0.]),'near_positive_corner':np.array([-size[0]/2+.010,size[1]/2-.010])};J=np.array([[0.,-1.],[1.,0.]]);mass=.18;Nhand=3.;mu_table=.550000011920929;mu_hand=1.;normal=mass*9.81+Nhand
R=lambda a:np.array([[np.cos(a),-np.sin(a)],[np.sin(a),np.cos(a)]])
reports=[]
for n in [24,48]:
 u,wt=leggauss(n);X,Y=np.meshgrid(u*size[0]/2,u*size[1]/2,indexing='ij');points=np.c_[X.ravel(),Y.ravel()];weights=np.outer(wt,wt).ravel()/4
 for label,local_contact in contacts.items():
  theta=0.;center=np.zeros(2);angle=0.;step=np.deg2rad(.25);rows=[]
  def twist(a,theta):
   B=R(theta);r=B@local_contact;p=points@B.T;vhand=R(a)@J@local_contact
   def wrench(omega):
    velocity=vhand-omega*(J@r);vp=velocity+omega*(p@J.T);norm=np.linalg.norm(vp,axis=1);f=-mu_table*normal*weights[:,None]*vp/np.maximum(norm[:,None],1e-14);F=f.sum(0);tau=float(np.sum(p[:,0]*f[:,1]-p[:,1]*f[:,0]));return velocity,F,tau
   def residual(omega):v,F,tau=wrench(omega);return float(r[0]*F[1]-r[1]*F[0]-tau)
   omega=brentq(residual,-20.,20.,xtol=1e-11);velocity,F,tau=wrench(omega);return velocity,omega,float(np.linalg.norm(F)),abs(residual(omega))
  for k in range(321):
   a=k*step;v,omega,force,residual=twist(a,theta);point=center+R(theta)@local_contact;planned=R(a)@local_contact
   rows.append(dict(commanded_rotation_deg=float(np.rad2deg(a)),predicted_rotation_deg=float(np.rad2deg(theta)),predicted_center_xy_m=center.tolist(),hand_force_demand_n=force,hand_point_slip_required=bool(force>mu_hand*Nhand),point_path_error_m=float(np.linalg.norm(point-planned)),wrench_equilibrium_residual_nm=residual))
   if k==320:break
   v1,o1,_,_=twist(a,theta);v2,o2,_,_=twist(a+step/2,theta+o1*step/2);v3,o3,_,_=twist(a+step/2,theta+o2*step/2);v4,o4,_,_=twist(a+step,theta+o3*step);center+=step*(v1+2*v2+2*v3+v4)/6;theta+=step*(o1+2*o2+2*o3+o4)/6
  row=dict(quadrature_order=n,contact=label,parcel_material_xy=local_contact.tolist(),final=rows[-1],max_force_demand_n=max(x['hand_force_demand_n'] for x in rows),max_point_path_error_m=max(x['point_path_error_m'] for x in rows),rows=rows);reports.append(row);print(n,label,'predicteddeg',rows[-1]['predicted_rotation_deg'],'center mm',1000*center,'maxF',row['max_force_demand_n'],flush=True)
out=dict(scope=__doc__,mass_kg=mass,hand_normal_load_n=Nhand,hand_mu=mu_hand,table_mu=mu_table,source_sha256={file.name:sha(file),'ROTATION_WRENCH_BUDGET.json':sha(w/'ROTATION_WRENCH_BUDGET.json'),'ROTATED_ROUTE_STICKING_CONTINUATION.json':sha(w/'ROTATED_ROUTE_STICKING_CONTINUATION.json')},checker_sha256=sha(Path(__file__)),reports=reports,physical_validation=False,training_ready=False)
(w/'SINGLE_CONTACT_ROTATION_MECHANICS.json').write_text(json.dumps(out,indent=2))
