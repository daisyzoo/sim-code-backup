"""Measured previous-substep vertical wrist/target loads in all four front/back conditions.
Read-only episode-specific observational comparison. Different trajectories and
sample durations confound pooled quantiles; not continuous integrated force or
randomized/multiseed causal evidence. Never data admission.
"""
from pathlib import Path
import json,hashlib,datetime,collections
import numpy as np
w=Path(__file__).resolve().parent;outdir=w/'recontact_interior_load3_groups_r1';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();reports=[]
for run in ['recontact_interior_groups_r1','recontact_interior_load3_groups_r1']:
 for cid,task in [(c,t) for c in [840001,840004] for t in ['push_box_to_bin','nudge_mailer_to_bin']]:
  ep=w/run/f'case_{cid}'/f'layout_{cid}_{task}';fr=json.loads((ep/'frontal_bypass.json').read_text());packets={p['after_action_step']:p for p in json.loads((ep/'solved_contact_forces.json').read_text())['rows']};side='right' if task=='push_box_to_bin' else 'left';actor='parcel_box' if side=='right' else 'mailer';samples=[]
  for row in fr['rows']:
   if 'contact_load' not in row:continue
   t=row['step'];packet=packets[t-1];measured=sum(abs(float(c['force_world_N'][2])) for c in packet['parcel_contacts'] if any(side+'_wrist_roll' in s for s in c['shapes']) and any('/'+actor+'/' in s for s in c['shapes']));assert abs(measured-row['contact_load']['observed_vertical_load_n'])<1e-10
   if row['mode']=='top_push':samples.append(dict(step=t,measured_vertical_n=measured,filtered_vertical_n=row['contact_load']['filtered_vertical_load_n'],z_bias_mm=row['contact_load']['applied_z_bias_m']*1000))
  loaded=[s for s in samples if s['measured_vertical_n']>=.3];assert loaded
  summary=dict(configured_n=fr['plan']['top_recontact']['desired_vertical_load_n'],push_samples=len(samples),loaded_push_samples=len(loaded),push_below_0_2N=sum(s['measured_vertical_n']<.2 for s in samples),loaded_vertical_quantiles_n=np.quantile([s['measured_vertical_n'] for s in loaded],[0,.5,.9,1]).tolist(),push_frames_at_minus6mm=sum(s['z_bias_mm']<=-5.999 for s in samples))
  report=dict(run=run,episode=ep.name,summary=summary,records=samples,source_sha256={n:sha(ep/n) for n in ['frontal_bypass.json','solved_contact_forces.json']});reports.append(report);print(run,ep.name,summary,flush=True)
(outdir/'FOUR_TASKS_MEASURED_LOADS.json').write_text(json.dumps(dict(scope=__doc__,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),episodes=reports,script_sha256=sha(Path(__file__)),training_ready=False),indent=2))
