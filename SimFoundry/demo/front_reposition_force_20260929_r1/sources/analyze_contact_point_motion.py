#!/usr/bin/env python3
"""Advect sampled contact material points across recorded consecutive rigid poses."""
import argparse,json
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from probe_sorting_kinematics import ArmFK
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();results=[]
for lid,task,side,obj,start in [(66009,'nudge_mailer_to_bin','left','mailer',13),(66010,'push_box_to_bin','right','box',18)]:
 ep=a.root/f'case_{lid}/layout_{lid}_{task}';fk=ArmFK(side);f=json.loads((ep/'solved_contact_forces.json').read_text())['rows'];c=json.loads((ep/'expert_control.json').read_text());tag='/mailer/' if obj=='mailer' else '/parcel_box/';samples=[]
 with np.load(ep/'raw.npz') as z,np.load(ep/'trace.npz') as tr,np.load(ep/'parcel_orientation.npz') as ori:
  transforms=[fk.pose(q[start:start+5],q[12]) for q in z['q']];rot=Rotation.from_quat(ori[obj]).as_matrix();errors=[np.linalg.norm(fk.palm(q[start:start+5],q[12])-tr['palm_'+side][t]) for t,q in enumerate(z['q'])];assert max(errors)<1e-4
  for t in range(158):
   if c[t]['mode']!='retreat_x' or c[t+1]['mode']!='retreat_x':continue
   # Contact after action t is pose at pre-action t+1; advect to t+2.
   T,U=transforms[t+1:t+3];entries=[]
   for k in f[t]['parcel_contacts']:
    if not(any(tag in n for n in k['shapes']) and any(side+'_wrist_roll' in n for n in k['shapes'])):continue
    w=abs(k['force_torque_contact'][0])
    if w<=.01:continue
    point=np.asarray(k['position_world']);local=T[:3,:3].T@(point-T[:3,3]);hand_next=U[:3,:3]@local+U[:3,3]
    parcel_local=rot[t+1].T@(point-tr[obj][t+1]);parcel_next=rot[t+2]@parcel_local+tr[obj][t+2]
    entries.append((w,hand_next-point,parcel_next-point))
   if not entries:continue
   weights=np.asarray([x[0] for x in entries]);hd=np.average([x[1] for x in entries],axis=0,weights=weights);od=np.average([x[2] for x in entries],axis=0,weights=weights)
   samples.append(dict(after_action=t,hand_material_delta=hd.tolist(),object_material_delta=od.tolist(),relative_material_delta=(hd-od).tolist(),palm_delta=(tr['palm_'+side][t+2]-tr['palm_'+side][t+1]).tolist()))
  sums={key:np.sum([x[key] for x in samples],axis=0).tolist() for key in ['hand_material_delta','object_material_delta','relative_material_delta','palm_delta']}
  result=dict(layout_id=lid,samples=samples,summed_per_interval_weighted_displacements=sums,fk_max_error=max(errors));results.append(result);print(lid,sums,flush=True)
a.out.write_text(json.dumps(dict(rows=results,training_ready=False,goal_complete=False,limits='Kinematic advection of last-tick loaded contact points over next control interval (1/15s), using recorded q and object quaternion. Points may cease contact within interval; this is not instantaneous slip velocity or integrated contact force. Weighted points can differ between intervals, so sums are not a single material-point trajectory.'),indent=2))
