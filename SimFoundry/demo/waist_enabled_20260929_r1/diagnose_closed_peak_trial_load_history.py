"""Observed within-action vertical-load history, not a causal dynamics proof.
Uses one earliest completed-solve boundary per tick1..24; excludes tick0 and
later duplicate manager boundaries. Force/body sign remains uninterpreted.
"""
from pathlib import Path
import sys,json,hashlib,datetime
import numpy as np
from audit_closed_peak_trial_contacts import audit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inspect(ep):
 ep=Path(ep).resolve();validated=audit(ep);m=json.loads((ep/'SUBSTEP_CONTACT_RECORDING.json').read_text())['metadata'];labels=m['shape_labels'];key='box' if 'push_box' in ep.name else 'mailer';actor='/parcel_box/' if key=='box' else '/mailer/';hand='right_wrist_roll' if key=='box' else 'left_wrist_roll'
 with np.load(ep/'substep_contacts.npz') as z:arrays={k:z[k] for k in z.files}
 a=arrays;intervals=validated['action_intervals'];R=24+m['expected_manager_steps'];off=a['contact_offsets'];rows=[];loads=[];peaktilts=[];duplicate_changes=[]
 for step in range(intervals):
  base=step*R;stamps=a['substep_tick'][base:base+R];chosen=[base+int(np.flatnonzero(stamps==tick)[0]) for tick in range(1,25)];values=[];tilts=[];pair=[]
  def sample(j):
   ids=range(int(off[j]),int(off[j+1]));vertical=0.;cross=0.
   for k in ids:
    names=[labels[i] for i in a['shape_ids'][k]];f=a['force_torque_world'][k,:3]
    if any(actor in n for n in names) and any(hand in n for n in names):vertical+=abs(float(f[2]))
    if any('/parcel_box/' in n for n in names) and any('/mailer/' in n for n in names):cross+=float(np.linalg.norm(f))
   return vertical,cross
  for j in chosen:
   value,cross=sample(j);values.append(value);pair.append(cross)
   q=a['body_q'][j,0 if key=='box' else 1,3:];tilts.append(float(np.arccos(np.clip(1-2*(float(q[0])**2+float(q[1])**2),-1,1))))
  for tick in set(stamps.tolist()):
   indices=np.flatnonzero(stamps==tick)+base
   if len(indices)>1:
    differences=abs(sample(int(indices[0]))[0]-sample(int(indices[-1]))[0])
    if differences>1e-5:duplicate_changes.append(dict(step=step,tick=int(tick),vertical_load_difference_n=differences))
  loads.append(values);peaktilts.append(tilts);rows.append(dict(action_step=step,vertical_load_n=values,absolute_vertical_load_time_sum_Ns=float(sum(values)*m['solver_dt_s']),pair_force_magnitude_n=pair,max_target_tilt_rad=max(tilts),final_target_tilt_rad=tilts[-1]))
 v=np.asarray(loads);t=np.asarray(peaktilts);fr=json.loads((ep/'frontal_bypass.json').read_text())['rows'];events=[]
 for before,after in zip(fr,fr[1:]):
  if before['mode']=='top_push' and after['mode']!='top_push':
   k=after['step']-1;events.append(dict(controller_step=after['step'],reason=after.get('last_recontact_reason'),preceding_action=k,substeps=rows[k]))
 report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,independent_audit=validated,action_intervals=intervals,summary=dict(actions_with_peak_load_gt_point3=int(np.sum(v.max(axis=1)>.3)),actions_with_final_load_gt_point3=int(np.sum(v[:,-1]>.3)),actions_with_peak_gt_point3_but_final_le_point3=int(np.sum((v.max(axis=1)>.3)&(v[:,-1]<=.3))),max_peak_vertical_load_n=float(v.max()),max_final_vertical_load_n=float(v[:,-1].max()),actions_with_peak_tilt_gt_point03_but_final_le_point03=int(np.sum((t.max(axis=1)>.03)&(t[:,-1]<=.03)))),duplicate_boundary_load_changes=duplicate_changes,exit_events=events,rows=rows,training_ready=False,source_sha256={n:sha(ep/n) for n in ['substep_contacts.npz','SUBSTEP_CONTACT_RECORDING.json','solved_contact_forces.json','frontal_bypass.json']},inspector_sha256=sha(__file__),limitations=['Absolute contact vertical magnitude time-sum is not signed net impulse.','End-solve state is not presumed synchronous with force evaluation.','Single observed run does not prove instrumentation leaves numerical trajectory unchanged.'])
 return report
if __name__=='__main__':
 ep=Path(sys.argv[1]);out=inspect(ep);p=ep/'CLOSED_PEAK_TRIAL_LOAD_HISTORY.json';assert not p.exists();p.write_text(json.dumps(out,indent=2));print(json.dumps(out['summary'],indent=2))
