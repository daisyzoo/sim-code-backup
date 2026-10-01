"""Actual parcel motion around first new bag edge override, compared with parent.
Small recorded windows, not a randomized causal trial or future-policy proof.
Post-action packet[t] minus trace[t] measures motion after command[t].
"""
from pathlib import Path
import sys,json,hashlib,datetime
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(w),str(repo)]
from audit_unloaded_wrist_prior_live import HandModel
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();urdf=repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf';vertices=repo/'assets/robots/g1_hand_support_vertices.json';hand=HandModel(urdf,vertices);sources={};rows=[]
for run in ['recontact_pose_groups_r1','loaded_edge_coverage_groups_r1']:
 ep=w/run/'case_840004/layout_840004_nudge_mailer_to_bin';fs={r['step']:r for r in json.loads((ep/'frontal_bypass.json').read_text())['rows']};pack={r['after_action_step']:r for r in json.loads((ep/'solved_contact_forces.json').read_text())['rows']};edges={r['step']:r for r in json.loads((ep/'loaded_edge_coverage.json').read_text())['rows']} if (ep/'loaded_edge_coverage.json').exists() else {}
 with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
 with np.load(ep/'trace.npz') as z:obj=z['mailer'].astype(float)
 records=[]
 for t in range(250,min(281,len(q))):
  off=np.array(fs[t]['control_offset_local'])
  def point(x):T=hand.fk(x,'left');return T[:3,3]+T[:3,:3]@off
  commanded=point(u[t])-point(q[t]);actual=np.array(pack[t]['post_action_pose']['mailer'])-obj[t]
  records.append(dict(step=t,mode=fs[t]['mode'],new_override=bool(edges.get(t,{}).get('override')),nominal_reference_forward_mm=float(commanded[1]*1000),actual_parcel_forward_mm=float(actual[1]*1000),actual_parcel_delta_mm=(actual*1000).tolist()))
 windows=[]
 for name,lo,hi in [('before',250,264),('first3edgecommands',265,267),('next_parent_only',268,280)]:
  vals=[r for r in records if lo<=r['step']<=hi]
  if vals:windows.append(dict(name=name,steps=[r['step'] for r in vals],mean_nominal_forward_mm=float(np.mean([r['nominal_reference_forward_mm'] for r in vals])),mean_actual_object_forward_mm=float(np.mean([r['actual_parcel_forward_mm'] for r in vals])),net_actual_object_forward_mm=float(sum(r['actual_parcel_forward_mm'] for r in vals))))
 rows.append(dict(run=run,records=records,windows=windows))
 for name in ['raw.npz','trace.npz','frontal_bypass.json','solved_contact_forces.json','loaded_edge_coverage.json']:
  path=ep/name
  if path.exists():sources[str(path)]=sha(path)
for p in [Path(__file__),w/'audit_unloaded_wrist_prior_live.py',urdf,vertices]:sources[str(p)]=sha(p)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,source_sha256=sources,training_ready=False);(w/'LOADED_EDGE_ONSET_MOTION.json').write_text(json.dumps(out,indent=2))
for r in rows:print(r['run'],r['windows'])
