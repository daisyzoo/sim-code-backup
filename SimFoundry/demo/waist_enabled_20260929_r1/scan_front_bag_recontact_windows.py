"""Scan every recorded unloaded cross/descend frame in six recoveries.
Find the earliest original-geometry-qualified frame, independently of any
optimizer result. This is a temporal eligibility screen, not a new controller.
"""
from pathlib import Path
import sys,json,hashlib,datetime
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_rear_waypoint_reconciliation';sys.path[:0]=[str(S),str(W),str(ROOT)]
from audit_front_initial_center_events import EventAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();ind=EventAudit(ROOT,S);D=W/'front_bag_recontact_center_draft_r2';base=json.loads((D/'STATIC_CONTEXT_PROBE.json').read_text());sources=dict(base['source_sha256']);sources[str(__file__)]=sha(__file__);records=[]
for record in base['records']:
 ep=W/record['run']/'case_840023'/record['episode'];fr=json.loads((ep/'frontal_bypass.json').read_text())['rows'];stop=next(r['step'] for r in fr if r['mode']=='front_guard_lift');scene0=record['planning']['scene'];counter=record['recontacts']
 with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23]
 with np.load(ep/'trace.npz') as z:pos={k:z[k] for k in ['box','mailer']}
 with np.load(ep/'parcel_orientation.npz') as z:quat={k:z[k] for k in ['box','mailer']}
 rows=[]
 for r in fr:
  if r['step']>=stop or r.get('recontacts')!=counter or r['mode'] not in ['top_cross','top_descend']:continue
  t=r['step'];load=r['contact_load'];unloaded=load['observed_vertical_load_n']==0 and 0<=load['filtered_vertical_load_n']<=.05
  if not unloaded:continue
  scene=dict(scene0,target_xyz=pos['mailer'][t].tolist(),target_quat=quat['mailer'][t].tolist(),other_xyz=pos['box'][t].tolist(),other_quat=quat['box'][t].tolist());g,_=ind.geometry(q[t].astype(float),scene);rows.append(dict(step=t,mode=r['mode'],geometry=g))
 accepted=[r['step'] for r in rows if r['geometry']['accepted']];v=dict(run=record['run'],recontacts=counter,eligible_frames=accepted,first_eligible=accepted[0] if accepted else None,unloaded_frames=len(rows),maximum_inactive_lowest_z_m=max(r['geometry']['inactive_lowest_z_m'] for r in rows),rows=rows);records.append(v);print(json.dumps({k:v for k,v in v.items() if k!='rows'}),flush=True)
with (D/'UNLOADED_RECOVERY_WINDOWS.json').open('x') as f:json.dump(dict(scope=__doc__,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),records=records,source_sha256=sources,simulation_started=False,training_ready=False),f,indent=2)
