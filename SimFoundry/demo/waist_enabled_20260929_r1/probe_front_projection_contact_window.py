"""Unwired one-step geometric probe using the CURRENT measured contact centroid.
Each observation retains the actual previous emitted command from the rejected
material-window run. No chained counterfactual history or motion/force prediction.
Tests whether retaining10mm around a moving measured contact could avoid the
observed material-anchor pinning; not proof of physical success or safe expansion.
"""
from pathlib import Path
import json,datetime,hashlib
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;R=W/'front_projection_physical_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={};reports=[]
def stats(x):a=np.asarray(x,float);assert np.isfinite(a).all();return dict(min=float(a.min()),median=float(np.median(a)),max=float(a.max()))
for layout,task,key,side,actor in [(840023,'nudge_mailer_to_bin','mailer','left','mailer'),(840020,'push_box_to_bin','box','right','parcel_box')]:
 ep=R/f'case_{layout}'/f'layout_{layout}_{task}'
 def read(n):sources[str(ep/n)]=sha(ep/n);return json.loads((ep/n).read_text())
 ready=read('READY_FOR_AUDIT.json');assert ready['executed_frames']==ready['requested_frames']==1200
 for name,h in ready['source_sha256'].items():assert sha(name)==h
 fr=read('frontal_bypass.json');quality=read('quality.json');assert not quality['passed'];packets={r['after_action_step']:r for r in read('solved_contact_forces.json')['rows']}
 with np.load(ep/'parcel_orientation.npz') as z:rot=Rotation.from_quat(z[key]).as_matrix()
 with np.load(ep/'trace.npz') as z:xyz=z[key].copy()
 original={r['step']:r for r in fr['rows']};records=[]
 for row in fr['rows']:
  a=row.get('loaded_reference_cap')
  if not a or not a.get('applied'):continue
  t=row['step'];weights=[];positions=[]
  for c in packets[t-1]['parcel_contacts']:
   slots=[i for i,s in enumerate(c['shapes']) if '/'+actor+'/' in s]
   if len(slots)!=1 or not any(side+'_wrist' in s for s in c['shapes']):continue
   force=np.asarray(c['force_world_N'])*(1 if slots[0]==1 else -1);load=-float(force@rot[t,:,2])
   if load>.05:weights.append(load);positions.append(c['position_world'])
  assert weights and sum(weights)>=.3;cop=np.average(positions,axis=0,weights=weights);local=rot[t].T@(cop-xyz[t]);assert np.max(abs(local-row['cop_slip_following']['measured_cop_local']))<=2e-6
  previous=np.asarray(original[t-1]['target_xyz'][:2]);parent=np.asarray(a['parent_xy']);reference=np.asarray(a['reference_xy']);current=np.asarray(a['command_xy']);drive=np.asarray(row['cop_slip_following']['drive_direction_xy']);assert np.max(abs(parent-previous))<=.003+1e-10
  lo=np.maximum.reduce([previous-.003,reference-.030,cop[:2]-.010]);hi=np.minimum.reduce([previous+.003,reference+.030,cop[:2]+.010]);feasible=bool(np.all(lo<=hi));proposed=np.clip(parent,lo,hi) if feasible else None
  if feasible:
   assert np.max(abs(proposed-previous))<=.003+1e-10 and np.max(abs(proposed-reference))<=.030+1e-10 and np.max(abs(proposed-cop[:2]))<=.010+1e-10
  pd=float((parent-previous)@drive);actual=float((current-previous)@drive);potential=None if proposed is None else float((proposed-previous)@drive)
  records.append(dict(step=t,feasible=feasible,current_contact_centroid_world=cop.tolist(),parent_requested_drive_mm=pd*1000,actual_material_capped_drive_mm=actual*1000,unissued_contact_window_drive_mm=None if potential is None else potential*1000,unissued_command_xy=None if proposed is None else proposed.tolist(),actual_previous_command_xy=previous.tolist(),retains90percent_of_parent=potential is not None and potential>=.9*pd,parent_exactly_retained=potential is not None and bool(np.max(abs(proposed-parent))<1e-12),candidate_changed_actual=potential is not None and bool(np.max(abs(proposed-current))>1e-12)))
 summaries={}
 for name,rs in [('all_observed_loaded',records),('late600_1199',[r for r in records if r['step']>=600])]:
  good=[r for r in rs if r['feasible']];summaries[name]=dict(rows=len(rs),feasible=len(good),retains90percent_of_parent=sum(r['retains90percent_of_parent'] for r in rs),parent_exactly_retained=sum(r['parent_exactly_retained'] for r in rs),changed_actual=sum(r['candidate_changed_actual'] for r in rs),actual_drive_mm=stats([r['actual_material_capped_drive_mm'] for r in rs]),unissued_contact_window_drive_mm=stats([r['unissued_contact_window_drive_mm'] for r in good]) if good else None)
 for name in ['trace.npz','parcel_orientation.npz']:sources[str(ep/name)]=sha(ep/name)
 reports.append(dict(episode=ep.name,summaries=summaries,first_changed_actual_step=next((r['step'] for r in records if r['candidate_changed_actual']),None),records=records))
sources[str(Path(__file__))]=sha(__file__);out=W/'FRONT_PROJECTION_CONTACT_WINDOW_ONE_STEP_PROBE.json';assert not out.exists();out.write_text(json.dumps(dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,episodes=reports,source_sha256=sources,controller_implemented=False,collector_integrated=False,physical_success_proven=False,training_ready=False,interpretation='Feasible one-step commands on recorded states are a screening result only. Once a proposed action differs, subsequent actual observations belong to the old policy; none are a valid projected-policy rollout.'),indent=2));print(json.dumps([{k:v for k,v in r.items() if k!='records'} for r in reports],indent=2))
