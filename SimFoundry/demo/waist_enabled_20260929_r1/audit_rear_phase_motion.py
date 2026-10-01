# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
"""Account for every measured target displacement by actual commanded phase."""
from pathlib import Path
import sys,json,hashlib
from collections import defaultdict
import numpy as np
p=Path(sys.argv[1]).resolve();fr=json.loads((p/'frontal_bypass.json').read_text());rows={r['step']:r for r in fr['rows']};key='box' if 'push_box' in p.name else 'mailer';other='mailer' if key=='box' else 'box';direction=-1 if key=='box' else 1
with np.load(p/'trace.npz') as z:target=z[key].astype(float);obstacle=z[other].astype(float)
packets={r['after_action_step']:r for r in json.loads((p/'solved_contact_forces.json').read_text())['rows']}
bins={};bouts=[];current=None;alignment=0.;records=[]
for t in range(len(target)-1):
 row=rows.get(t);mode=row['mode'] if row is not None else 'unlogged_initial';recontact=row.get('recontacts',0) if row else 0
 packet=packets.get(t)
 if packet:
  err=float(np.max(abs(np.asarray(packet['post_action_pose'][key])-target[t+1])));alignment=max(alignment,err);assert err<2e-6
 delta=target[t+1,:2]-target[t,:2]
 record=dict(step=t,mode=mode,recontacts=recontact,delta_xy_m=delta.tolist(),signed_sort_delta_m=direction*delta[1],observed_prior_load_n=row.get('contact_load',{}).get('observed_vertical_load_n') if row else None)
 records.append(record)
 if current is None or current['mode']!=mode or current['recontacts']!=recontact:
  if current is not None:bouts.append(current)
  current=dict(mode=mode,recontacts=recontact,start_step=t,end_step=t,frames=0,delta_xy_m=[0.,0.])
 current['end_step']=t;current['frames']+=1;current['delta_xy_m']=(np.asarray(current['delta_xy_m'])+delta).tolist()
 b=bins.setdefault(mode,dict(frames=0,delta_xy_m=[0.,0.],positive_x_m=0.,negative_x_m=0.,signed_sort_delta_m=0.,positive_sort_m=0.,negative_sort_m=0.));b['frames']+=1;b['delta_xy_m']=(np.asarray(b['delta_xy_m'])+delta).tolist();b['positive_x_m']+=max(0.,delta[0]);b['negative_x_m']+=min(0.,delta[0]);b['signed_sort_delta_m']+=direction*delta[1];b['positive_sort_m']+=max(0.,direction*delta[1]);b['negative_sort_m']+=min(0.,direction*delta[1])
if current is not None:bouts.append(current)
actual=target[-1,:2]-target[0,:2];accounted=np.sum([b['delta_xy_m'] for b in bins.values()],axis=0);assert np.max(abs(actual-accounted))<1e-12
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest();out=dict(episode=p.name,bins=bins,bouts=bouts,records=records,total_delta_xy_m=actual.tolist(),accounting_residual_m=(actual-accounted).tolist(),max_post_action_pose_alignment_error_m=alignment,source_sha256={f:sha(p/f) for f in ['raw.npz','trace.npz','frontal_bypass.json','solved_contact_forces.json']},auditor_sha256=sha(__file__),scope='All1199 observed frame-to-next-frame transitions, grouped by actually issued pre-action mode. Last action has no next trace observation and is excluded. Post-action force-packet pose aligned where available. Phase motion association is not a force integral or proof of unique cause; no gate/data admission change.',training_ready=False)
(p/'REAR_PHASE_MOTION_AUDIT.json').write_text(json.dumps(out,indent=2))
print(p.parent.parent.name,p.name,'total mm',actual*1000)
for mode,b in bins.items():print(mode,b['frames'],'netXYmm',np.asarray(b['delta_xy_m'])*1000,'+Xmm',b['positive_x_m']*1000,'-Xmm',b['negative_x_m']*1000)
