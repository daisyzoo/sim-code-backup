"""Independent dense corner projection check of selected diagnostic object routes.
Does not import planner or footprint helper. No claim of robot/dynamic success.
"""
from pathlib import Path
import json,hashlib,itertools,sys
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path.insert(0,str(repo))
from simfoundry.calibration.sorting_station import PARCEL_BOX_SIZE,MAILER_SIZE_XYH
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();source=w/'ROTATED_OBJECT_ROUTE_SCREEN_20MM.json';report=json.loads(source.read_text());rows=[];signs=np.array(list(itertools.product([-1,1],repeat=3)))
for e in report['rows']:
 ep=next((w/'joint_edge_retry_groups_r1').glob('case_*/'+e['episode']));key='box' if 'push_box' in e['episode'] else 'mailer';other='mailer' if key=='box' else 'box';size=np.array(PARCEL_BOX_SIZE if key=='box' else MAILER_SIZE_XYH);osize=np.array(MAILER_SIZE_XYH if key=='box' else PARCEL_BOX_SIZE)
 for n,h in e['source_sha256'].items():assert sha(ep/n)==h
 with np.load(ep/'trace.npz') as z:target=z[key][0].astype(float);obstacle=z[other][0].astype(float)
 with np.load(ep/'parcel_orientation.npz') as z:q=z[key][0].astype(float);oq=z[other][0].astype(float)
 othercorners=signs*osize/2@Rotation.from_quat(oq).as_matrix().T+obstacle;olo=othercorners[:,:2].min(0);ohi=othercorners[:,:2].max(0)
 candidates=[('best_depth',e['best_depth'])]
 if e['least_rotation_front']:candidates.append(('least_rotation_front',e['least_rotation_front']))
 if e['episode']=='layout_840001_push_box_to_bin':candidates.append(('max_table_margin_front',max([r for r in e['all_candidates'] if r['route']=='front'],key=lambda r:(r['target_table_margin_m'],-abs(r['rotation_deg'])))))
 for label,r in candidates:
  if r is None:continue
  checks=[]
  def evaluate(center,orientation):
   corners=signs*size/2@orientation.as_matrix().T+center;low=corners[:,:2].min(0);high=corners[:,:2].max(0);table=min(low[0]-.28,.88-high[0],low[1]+.75,.75-high[1]);gap=np.maximum(olo-high,low-ohi).max();checks.append((table,gap))
  for a in np.linspace(0,r['rotation_deg'],int(abs(r['rotation_deg'])*10)+1):evaluate(target,Rotation.from_rotvec([0,0,np.deg2rad(a)])*Rotation.from_quat(q))
  rot=Rotation.from_rotvec([0,0,np.deg2rad(r['rotation_deg'])])*Rotation.from_quat(q)
  for start,end in zip(r['waypoints_xy'],r['waypoints_xy'][1:]):
   start=np.array(start);end=np.array(end)
   for f in np.linspace(0,1,int(np.ceil(np.linalg.norm(end-start)/.001))+1):c=target.copy();c[:2]=start+(end-start)*f;evaluate(c,rot)
  checks=np.array(checks);assert checks[:,0].min()>=.005-1e-9;assert checks[:,1].min()>=.020-1e-9
  rows.append(dict(episode=e['episode'],candidate=label,rotation_deg=r['rotation_deg'],samples=len(checks),minimum_table_margin_m=float(checks[:,0].min()),minimum_object_aabb_gap_m=float(checks[:,1].min())))
out=dict(scope=__doc__,rows=rows,all_pass=True,planner_report_sha256=sha(source),checker_sha256=sha(Path(__file__)),training_ready=False)
(w/'ROTATED_ROUTE_GEOMETRY_CHECK.json').write_text(json.dumps(out,indent=2));print('passed',len(rows),'candidate paths;',sum(r['samples'] for r in rows),'independent corner samples')
