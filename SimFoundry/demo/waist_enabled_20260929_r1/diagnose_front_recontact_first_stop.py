"""Bind first actual recovery command and next measured scene rejection.
Independent URDF/event check; retain short failure. Scan recorded original
eligibility windows for optional planning headroom, never change safety gates.
"""
from pathlib import Path
import datetime,hashlib,json,sys
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_recontact_center';sys.path[:0]=[str(W),str(ROOT)]
from audit_front_recontact_center_events import RecoveryEventAudit
from audit_front_initial_center_planning_v2 import SelectionAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();R=W/'front_recontact_physical_r1';ep=R/'case_840023/layout_840023_nudge_mailer_to_bin';read=lambda p:json.loads(Path(p).read_text())
data=read(ep/'front_recontact_center.json');events=data['rows'];commands=[r for r in events if r['kind']=='command'];stops=[r for r in events if r['kind']=='stop'];assert len(commands)==len(stops)==1
command,stop=commands[0],stops[0];assert command['step']==253 and stop['step']==254 and stop['reason']=='no_verified_initial_front_command'
assert all(r['kind']!='handover' for r in events);context=command['context'];next_context=stop['context'];quality=read(ep/'quality.json');clear=read(ep/'self_clearance.json');assert quality['frames']==254 and not quality['passed'] and clear['recorded_frames']==254 and clear['requested_frames']==1200
with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
for key,expected in [('current',q[253]),('previous_q',q[252]),('previous_command',u[252])]:np.testing.assert_array_equal(context[key],expected)
np.testing.assert_array_equal(command['command'],u[253]);np.testing.assert_array_equal(next_context['previous_command'],u[253]);np.testing.assert_array_equal(next_context['previous_q'],q[253])
pre=next(r for r in clear['rows'] if r['step']==254 and r['phase']=='pre');np.testing.assert_array_equal(pre['upper_q'],next_context['current']);assert pre['accepted'] and pre['model_coherent']
ind=RecoveryEventAudit(ROOT,S);ev={k:v for k,v in command.items() if k!='step'}
verified=ind.verify(ev,step=253,current=q[253],previous_q=q[252],previous_command=u[252],final_command=u[253],scene=context['scene'],decay=context['decay'],selected=True,parent_mode=context['parent_mode'],recontacts=1,guard_stop=False,observed_load_n=context['observed_load_n'],filtered_load_n=context['filtered_load_n'])
geo=SelectionAudit(ROOT,S);before,_=geo.geometry(q[253],context['scene']);predicted,_=geo.geometry(np.array(command['proposal']['predicted_q']),context['scene']);actual,_=geo.geometry(np.array(next_context['current']),next_context['scene']);nominal,_=geo.geometry(u[253],context['scene'])
for got,logged in [(predicted,command['proposal']['predicted_scene']),(actual,stop['proposal']['measured_scene']),(nominal,command['proposal']['nominal_scene'])]:
 for key in ['inactive_lowest_z_m','elbow_gap_m','active_above_top_m']:np.testing.assert_allclose(got[key],logged[key],atol=1e-10,rtol=0)
assert before['accepted'] and predicted['accepted'] and nominal['accepted'] and not actual['accepted']
assert actual['physical_bounds'] and actual['active_above_top_m']>0 and actual['elbow_gap_m']>.012 and min(actual['hand_parcel_gaps_m'].values())>.01
assert actual['inactive_lowest_z_m']<.84-2e-7
window=W/'front_bag_recontact_center_draft_r2/UNLOADED_RECOVERY_WINDOWS.json';windows=read(window);headroom=[]
for rec in windows['records']:
 eligible=[r for r in rec['rows'] if r['geometry']['accepted']];thresholds=[]
 for margin in [0.,.00025,.0005,.001,.002]:
  ts=[r['step'] for r in eligible if r['geometry']['inactive_lowest_z_m']>=.84+margin]
  thresholds.append(dict(additional_entry_headroom_mm=1000*margin,qualified_frames=len(ts),first_step=ts[0] if ts else None))
 headroom.append(dict(run=rec['run'],recontacts=rec['recontacts'],maximum_inactive_lowest_z_m=rec['maximum_inactive_lowest_z_m'],thresholds=thresholds))
files=[Path(__file__),ep/'front_recontact_center.json',ep/'raw.npz',ep/'self_clearance.json',ep/'quality.json',ep/'coordination.json',window,W/'audit_front_recontact_center_events.py',W/'audit_front_initial_center_planning_v2.py']
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,recorded_frames=254,requested_frames=1200,one_executed_recovery_command_step=253,stop_step=254,handovers=0,independent_first_command=verified,original_clearance_precheck_passed=True,original_recovery_geometry_rejected=True,before=before,nominal=nominal,predicted=predicted,actual_next_observation=actual,inactive_height_prediction_error_mm=1000*(actual['inactive_lowest_z_m']-predicted['inactive_lowest_z_m']),predicted_inactive_height_margin_mm=1000*(predicted['inactive_lowest_z_m']-.84),actual_inactive_height_margin_mm=1000*(actual['inactive_lowest_z_m']-.84),original_gate_m=.84,original_numerical_tolerance_m=2e-7,recorded_old_window_headroom=headroom,conclusions=['The first command passes independent logged-command verification; next measured inactive-hand lowest point violates original0.84m recovery-scene gate.','Nominal joint command has positive height margin but affine next-state prediction has only about13micrometres margin. About49micrometres height prediction error consumes that margin.','This is not active-hand contact or parcel obstacle collision, and not a completed re-centering handover. The general self-clearance precheck passes while the stricter recovery-phase gate rejects.','Do not lower the0.84m gate, increase numerical tolerance, drop the stop, or admit this254-frame failure.','Next isolated candidate should reserve measured/predicted inactive-hand headroom before consuming the recovery attempt. Historical windows only show whether waiting has recorded opportunities; they do not prove changed-trajectory feasibility or physical success.'],source_sha256={str(p):sha(p) for p in files},training_ready=False)
with (R/'FIRST_RECONTACT_STOP_DIAGNOSIS.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps({k:out[k] for k in ['recorded_frames','one_executed_recovery_command_step','stop_step','handovers','inactive_height_prediction_error_mm','predicted_inactive_height_margin_mm','actual_inactive_height_margin_mm','recorded_old_window_headroom']},indent=2))
