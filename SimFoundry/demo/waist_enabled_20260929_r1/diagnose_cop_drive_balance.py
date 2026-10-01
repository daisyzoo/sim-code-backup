# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
"""Measure opposing COP feedback versus intended drive on completed real runs."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
p=Path(sys.argv[1]).resolve();log=json.loads((p/'frontal_bypass.json').read_text());key='box' if 'push_box' in p.name else 'mailer'
with np.load(p/'trace.npz') as z:xyz=z[key].astype(float)
records=[];groups={}
for row in log['rows']:
 f=row.get('cop_slip_following')
 if f is None or not f.get('override'):continue
 t=row['step'];drive=np.asarray(f['drive_xy']);norm=float(np.linalg.norm(drive));axis=drive/norm if norm else np.zeros(2);corr=np.asarray(f['slip_correction_xy']);feed=np.asarray(f['object_anchor_translation_xy']);delta=np.asarray(f['command_delta_xy']);next_move=xyz[t+1,:2]-xyz[t,:2] if t+1<len(xyz) else None
 rec=dict(step=t,route_stage=row['route_stage'],observed_load_n=row['contact_load']['observed_vertical_load_n'],drive_norm_m=norm,parallel_correction_m=float(corr@axis),parallel_feed_m=float(feed@axis),parallel_actual_command_delta_m=float(delta@axis),opposing_correction_over_drive=float(-corr@axis/norm) if norm else None,command_axis_lead_m=float(np.max(abs(np.asarray(f['command_reference_lead_xy'])))),desired_lead_clipped=f['desired_lead_clipped'],next_target_delta_xy_m=None if next_move is None else next_move.tolist(),next_target_move_norm_m=None if next_move is None else float(np.linalg.norm(next_move)))
 records.append(rec);groups.setdefault(row['route_stage'],[]).append(rec)
summaries={}
for name,rows in groups.items():
 still=[r for r in rows if r['next_target_move_norm_m'] is not None and r['next_target_move_norm_m']<1e-6 and r['observed_load_n']>=.3]
 def stats(rs):
  return dict(samples=len(rs),median_observed_load_n=float(np.median([r['observed_load_n'] for r in rs])),median_opposing_correction_over_drive=float(np.median([r['opposing_correction_over_drive'] for r in rs if r['opposing_correction_over_drive'] is not None])),median_abs_command_delta_parallel_um=float(np.median([abs(r['parallel_actual_command_delta_m'])*1e6 for r in rs])),median_reference_axis_lead_mm=float(np.median([r['command_axis_lead_m']*1000 for r in rs])),clipped_steps=sum(r['desired_lead_clipped'] for r in rs)) if rs else dict(samples=0)
 summaries[name]=dict(all_loaded_override=stats(rows),loaded_with_next_motion_below_1um=stats(still))
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest();out=dict(summary=summaries,records=records,source_sha256={f:sha(p/f) for f in ['raw.npz','trace.npz','frontal_bypass.json','solved_contact_forces.json']},auditor_sha256=sha(__file__),scope='Completed real trajectory: reported drive/correction/feed/command decomposed along intended drive, aligned with actual next-frame motion.1um is a descriptive stationary-bin cutoff, never a changed quality gate. Independent COP/command auditor required separately. Association and algebraic cancellation do not prove all physical causes or hypothetical correction success.',training_ready=False)
(p/'COP_DRIVE_BALANCE_DIAGNOSIS.json').write_text(json.dumps(out,indent=2));print(json.dumps(summaries,indent=2))
