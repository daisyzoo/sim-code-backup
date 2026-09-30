#!/usr/bin/env python3
"""Offline URDF point IK: validate FK on recorded q before reachability probes.
No simulator state changes. IK is not collision-aware or a demonstration.
"""
import json,argparse,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.optimize import least_squares
ROOT=Path(__file__).resolve().parents[1]
URDF=ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf'
class ArmFK:
 def __init__(self,side):
  root=ET.parse(URDF).getroot();bychild={j.find('child').get('link'):j for j in root.findall('joint')};chain=[];link=side+'_wrist_roll_rubber_hand'
  while link in bychild:
   j=bychild[link];chain.append(j);link=j.find('parent').get('link')
  self.joints=[];self.names=[];self.bounds=[]
  for j in chain[::-1]:
   M=np.eye(4);o=j.find('origin')
   if o is not None:
    M[:3,3]=np.fromstring(o.get('xyz','0 0 0'),sep=' ');M[:3,:3]=Rotation.from_euler('xyz',np.fromstring(o.get('rpy','0 0 0'),sep=' ')).as_matrix()
   axis=np.fromstring(j.find('axis').get('xyz'),sep=' ') if j.get('type')=='revolute' else None
   self.joints.append((j.get('name'),M,axis))
   if axis is not None and j.get('name')!='waist_yaw_joint':
    self.names.append(j.get('name'));lim=j.find('limit');self.bounds.append((float(lim.get('lower')),float(lim.get('upper'))))
 def pose(self,q,waist=0):
  values=dict(zip(self.names,q));values['waist_yaw_joint']=waist;T=np.eye(4);T[:3,3]=[.08,0,.793]
  for name,M,axis in self.joints:
   T=T@M
   if axis is not None:
    A=np.eye(4);A[:3,:3]=Rotation.from_rotvec(axis*values[name]).as_matrix();T=T@A
  return T
 def palm(self,q,waist=0):
  return (self.pose(q,waist)@np.array([.2,0,.007,1]))[:3]
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();models={s:ArmFK(s) for s in ['left','right']};errors=[]
 for lid in [50000,50001,51000,51001]:
  root=ROOT/'demo/approach_geometry_20260928_r1'/f'lower_closer_{lid}'
  for raw in sorted(root.glob('layout_*/raw.npz')):
   with np.load(raw) as d,np.load(raw.parent/'trace.npz') as tr:
    for side,start in [('left',13),('right',18)]:
     for t in [0,30,60,90,120,159]:
      pred=models[side].palm(d['q'][t,start:start+5],d['q'][t,12]);errors.append(float(np.linalg.norm(pred-tr['palm_'+side][t])))
 assert errors and max(errors)<1e-4, f'FK mismatch: {max(errors)}'
 rows=[];rng=np.random.default_rng(20260928)
 for side,model in models.items():
  lo,hi=np.array(model.bounds).T
  for name,x,y in [('normal',.46,.14 if side=='left' else -.14),('cross_body',.46,-.14 if side=='left' else .14),('far_center',.591,.005),('compact_center',.535,.005)]:
   for phase,z in [('stage',.92),('contact',.84 if side=='left' else .845)]:
    goal=np.array([x,y+(-.07 if side=='left' else .07),z]);best=None
    for q0 in [np.zeros(5)]+[rng.uniform(lo,hi) for _ in range(5)]:
     sol=least_squares(lambda q:model.palm(q)-goal,q0,bounds=(lo,hi),max_nfev=400,gtol=1e-10,ftol=1e-10,xtol=1e-10);err=float(np.linalg.norm(sol.fun))
     if best is None or err<best['position_error_m']:best={'q':sol.x.tolist(),'position_error_m':err,'palm':model.palm(sol.x).tolist()}
    row={'side':side,'layout':name,'phase':phase,'target':goal.tolist(),**best};rows.append(row);print(side,name,phase,round(best['position_error_m'],6),flush=True)
 result={'urdf':str(URDF),'fk_validation_samples':len(errors),'fk_max_error_m':max(errors),'rows':rows,'limitations':'Point IK under URDF joint limits only. No self/table/object collision, palm orientation, effort, trajectory smoothness, or dynamic feasibility guarantee. Diagnostic results cannot train.'};a.out.write_text(json.dumps(result,indent=2))
if __name__=='__main__':main()
