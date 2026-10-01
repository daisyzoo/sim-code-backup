# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
"""Bind complete physical parent/candidate rear results without selecting successes."""
from pathlib import Path
from collections import Counter
import json,hashlib
import numpy as np
w=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rows=[]
for case,task,key,other in [(840001,'push_box_to_bin','box','mailer'),(840004,'nudge_mailer_to_bin','mailer','box')]:
 record=dict(episode=f'layout_{case}_{task}')
 for label,name in [('parent','region_continuity_groups_r1'),('candidate','region_x_follow_groups_r1')]:
  ep=w/name/f'case_{case}'/record['episode'];d=json.loads((ep/'TOP_CONTACT_BOUT_DIAGNOSIS.json').read_text());q=json.loads((ep/'quality.json').read_text());review=json.loads((ep/'EARLY_REVIEW.json').read_text())
  for f,h in d['source_sha256'].items():assert sha(ep/f)==h
  with np.load(ep/'trace.npz') as z:delta=(z[key][-1,:2].astype(float)-z[key][0,:2])*1000
  loaded=[s for s in d['series'] if 'cop_local_xyz_m' in s]
  record[label]=dict(task_passed=q['passed'],task_and_pose_passed=review['pose']['search_success'],support=review['pose']['support'],upright=review['pose']['upright'],progress_mm=q['metrics']['target_final_progress_m']*1000,target_delta_xy_mm=delta.tolist(),non_target_max_xy_mm=q['metrics'][other+'_max_xy_m']*1000,max_target_tilt_rad=review['pose']['max_tilt_rad'][key],top_push_frames=len(d['series']),loaded_last_substep_samples=len(loaded),cop_local_x_median_mm=float(np.median([s['cop_local_xyz_m'][0] for s in loaded]))*1000,push_bout_lengths=[b['frames'] for b in d['bouts']],recovery_reasons=dict(Counter(b['recontact_reason'] for b in d['bouts'] if b['recontact_reason'])),source_sha256={f:sha(ep/f) for f in ['TOP_CONTACT_BOUT_DIAGNOSIS.json','quality.json','EARLY_REVIEW.json','trace.npz']})
 rows.append(record)
out=dict(rows=rows,scope='Exact two original difficult rear conditions in full8push+2wait physical runs; failed conditions retained. Loaded counts are last-substep COP samples, not contact duration over every physics substep. Does not establish unique causality, training admission or model performance.',training_ready=False)
(w/'region_x_follow_groups_r1/REAR_CONTACT_COMPARISON.json').write_text(json.dumps(out,indent=2))
for r in rows:print(r['episode'],{k:{n:v for n,v in r[k].items() if n!='source_sha256'} for k in ['parent','candidate']})
