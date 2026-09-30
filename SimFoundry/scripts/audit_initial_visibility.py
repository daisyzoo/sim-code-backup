#!/usr/bin/env python3
"""Project initial parcel cuboids using frozen camera calibration. No occlusion claim."""
import argparse,json,itertools,sys,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from simfoundry.calibration.sorting_station import SORTING_ROBOT_POS,SORTING_D435I_POS,SORTING_D435I_ROT_XYZW,PARCEL_BOX_SIZE,MAILER_SIZE_XYH
from simfoundry.embodiment import D435I_INTRINSICS as K

def project_layout(d):
 urdf=ET.parse(ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf').getroot()
 j=next(j for j in urdf.findall('joint') if j.get('name')=='waist_yaw_joint')
 origin=np.fromstring(j.find('origin').get('xyz'),sep=' ')
 cam=np.array(SORTING_ROBOT_POS)+origin+SORTING_D435I_POS;R=Rotation.from_quat(SORTING_D435I_ROT_XYZW).as_matrix();rows=[]
 for name,size in [('box',PARCEL_BOX_SIZE),('mailer',MAILER_SIZE_XYH)]:
  p=np.array(list(itertools.product(*[[-x/2,x/2] for x in size])));p=Rotation.from_euler('z',d.get(name+'_yaw',0.)).apply(p)+d[name+'_xyz'];c=(p-cam)@R
  assert (c[:,2]>0).all()
  uv=c[:,:2]/c[:,2:3]*[K.fx,K.fy]+[K.cx,K.cy];lo=uv.min(0);hi=uv.max(0);clip_lo=np.maximum(lo,[0,0]);clip_hi=np.minimum(hi,[K.width,K.height]);area=np.prod(hi-lo);fraction=np.prod(np.maximum(0,clip_hi-clip_lo))/area
  rows.append({'object':name,'bbox_px':[lo.tolist(),hi.tolist()],'bbox_in_frame_fraction':float(fraction),'projected_center_px':uv.mean(0).tolist()})
 return rows

def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();rows=[]
 for f in sorted(a.root.glob('layout_*.json')):
  d=json.loads(f.read_text());rows.append({'layout_id':d['layout_id'],'objects':project_layout(d)})
 assert rows
 a.output.write_text(json.dumps({'method':'Frozen zero-waist URDF torso transform and configured ROS optical intrinsics. Cuboid projected bounding boxes, before clipping.','limitations':'BBox fraction is not visible surface area; excludes self/object occlusion, rounded bag outline, renderer errors. Verify overlay against actual initial RGB. No automatic training admission.','rows':rows},indent=2));print('min bbox in-frame fraction',min(o['bbox_in_frame_fraction'] for r in rows for o in r['objects']))
if __name__=='__main__':main()
