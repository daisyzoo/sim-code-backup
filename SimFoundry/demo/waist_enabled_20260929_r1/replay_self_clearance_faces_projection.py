"""Full8 kinematic replay of recorded final command pose references.
Previous PROJECTED command is next kinematic state. Historical object observations,
forces and images are NOT recomputed; this is not physical/off-policy task success.
Tracks both hand reference positions and active hand up direction, so task-space
cost of eliminating elbow-torso intersections is explicitly retained.
"""
from pathlib import Path
import sys,json,hashlib,time
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_self_clearance_faces_probe';sys.path[:0]=[str(repo),str(stage),str(w/'staged_joint_edge_command')]
from articulated_hand_geometry import ArticulatedHandGeometry
from self_clearance import BilateralElbowClearance
from pose_projection import project
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();model=ArticulatedHandGeometry(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json');g=BilateralElbowClearance(model,stage/'elbow_torso_hulls.json');lo=np.array(U1_JOINT_LIMIT_LO)[12:23];hi=np.array(U1_JOINT_LIMIT_HI)[12:23];lo[0]=-.98;hi[0]=.98
outdir=stage/'kinematic_replay_r1';outdir.mkdir(exist_ok=False);reports=[];tic=time.monotonic()
for cid in [840001,840004,840000,840005]:
 for task in ['push_box_to_bin','nudge_mailer_to_bin']:
  ep=w/f'joint_edge_retry_groups_r1/case_{cid}/layout_{cid}_{task}';side='right' if task=='push_box_to_bin' else 'left'
  with np.load(ep/'raw.npz') as z:parent=z['action'][:,12:23].astype(np.float32)
  fr=json.loads((ep/'frontal_bypass.json').read_text());frames={f['step']:f for f in fr['rows']};previous=np.zeros(11,dtype=np.float32);commands=[];records=[]
  for t,p in enumerate(parent):
   frame=frames.get(t,{});offset=frame.get('control_offset_local') or [.2,0,.007];command,meta=project(enabled=True,parent=p,previous=previous,model=model,geometry=g,lo=lo,hi=hi,side=side,offset=offset,first=t==0);assert np.min(g.constraints(command))>=.005-2e-7;assert np.max(abs(command-previous))<=.0550002
   meta.update(step=t,mode=frame.get('mode'),minimum_gap_m=float(g.constraints(command).min()));commands.append(command);records.append(meta);previous=command
   if t%300==0:print(ep.name,t,'overrides',sum(r['override'] for r in records),'holds',sum(r['reason']=='hold_verified_previous' for r in records),flush=True)
  commands=np.array(commands);np.savez_compressed(outdir/(ep.name+'_commands.npz'),command=commands,parent=parent)
  modified=[r for r in records if r['override']];fallback=[r for r in records if r['reason']=='hold_verified_previous'];errors=[r['point_error_mm'][side] for r in modified if 'point_error_mm' in r];report=dict(episode=ep.name,frames=len(records),overrides=len(modified),failed_solve_holds=len(fallback),active_reference_error_mm_percentiles=None if not errors else np.percentile(errors,[0,50,90,100]).tolist(),minimum_gap_m=min(r['minimum_gap_m'] for r in records),source_sha256={n:sha(ep/n) for n in ['raw.npz','frontal_bypass.json']},records=records)
  (outdir/(ep.name+'.json')).write_text(json.dumps(report,indent=2));reports.append({k:v for k,v in report.items() if k!='records'});print('finished',ep.name,{k:v for k,v in reports[-1].items() if k not in ['source_sha256']},flush=True)
  (outdir/'PROGRESS.json').write_text(json.dumps(dict(completed=len(reports),episodes=reports,scope=__doc__,training_ready=False),indent=2))
summary=dict(scope=__doc__,episodes=reports,elapsed_seconds=time.monotonic()-tic,source_sha256={p.name:sha(p) for p in [stage/'self_clearance.py',stage/'pose_projection.py',stage/'elbow_torso_hulls.json']},checker_sha256=sha(Path(__file__)),training_ready=False,physical_started=False,collector_wired=False)
(outdir/'RESULT.json').write_text(json.dumps(summary,indent=2));print('full replay complete',time.monotonic()-tic,flush=True)
