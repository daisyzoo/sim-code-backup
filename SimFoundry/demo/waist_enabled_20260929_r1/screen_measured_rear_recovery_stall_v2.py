"""Causal trigger screen on closed trajectories, not a rollout or policy result.
Requires30 actually emitted loaded recovery commands in one phase/contact bout.
Progress means reduction in independently measured remaining corridor distance;
rotation and obstacle movement therefore count, not just target X displacement.
The conservative cap is0.1mm total over30 commands (the original nominal
minimum for just one command), rather than0.5mm which triggered while the
second recovery phase was still progressing. The V1 screen stays recorded.
Only the FIRST trigger per episode is a valid candidate counterfactual boundary.
"""
from pathlib import Path
import sys,json,hashlib,datetime
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ep=Path(sys.argv[1]).resolve();dest=ep/'MEASURED_REAR_RECOVERY_STALL_SCREEN_V2.json';assert not dest.exists();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();rr=json.loads((ep/'rear_corridor_recovery.json').read_text())['rows'];rs={r['step']:r for r in rr};side='right' if 'push_box' in ep.name else 'left';key='box' if side=='right' else 'mailer';other='mailer' if key=='box' else 'box';sizes={'box':np.array([.14,.09,.045]),'mailer':np.array([.15,.145,.04])}
with np.load(ep/'raw.npz') as z:u=z['action'][:,12:23].astype(float)
with np.load(ep/'trace.npz') as z:pos={k:z[k].astype(float) for k in sizes}
with np.load(ep/'parcel_orientation.npz') as z:rad={k:abs(Rotation.from_quat(z[k]).as_matrix())@sizes[k]/2 for k in sizes}
remaining=pos[other][:,0]+rad[other][:,0]+rad[key][:,0]+.022-pos[key][:,0];rows=[];trigger=None
for t,r in sorted(rs.items()):
 if t>=len(u) or t<31 or r['kind']!='loaded_recovery' or not r.get('phase',{}).get('after',{}).get('active'):continue
 phase=r['phase']['after'];row=r['parent_row'];history=[rs.get(j) for j in range(t-30,t)]
 # Only previous actual emissions decide eligibility; current r is used solely
 # to select an observed candidate request, never current post-action success.
 eligible=all(p is not None and p['kind']=='loaded_recovery' and p.get('phase_committed',{}).get('active') and p['phase_committed']['entry_step']==phase['entry_step'] and p['parent_row']['recontacts']==row['recontacts'] and p['parent_coordinate']['active_side']==side and p.get('commit',{}).get('final_guard',{}).get('accepted') is True and np.array_equal(u[p['step']],p['emitted_command']) for p in history)
 if not eligible or remaining[t]<=0:continue
 old=float(remaining[t-30]);progress=float(remaining[t-30]-remaining[t]);required=min(.0001,.5*max(0.,old));stalled=progress<required
 record=dict(step=t,phase_entry=phase['entry_step'],previous_actual_recovery_steps=[t-30,t-1],remaining_before_mm=old*1000,remaining_now_mm=float(remaining[t]*1000),progress_mm=progress*1000,required_progress_mm=required*1000,stalled=bool(stalled),target_x_gain_mm=float((pos[key][t,0]-pos[key][t-30,0])*1000),target_radius_x_change_mm=float((rad[key][t,0]-rad[key][t-30,0])*1000),other_x_change_mm=float((pos[other][t,0]-pos[other][t-30,0])*1000))
 rows.append(record)
 if stalled:trigger=record;break
sources={str(ep/n):sha(ep/n) for n in ['raw.npz','rear_corridor_recovery.json','trace.npz','parcel_orientation.npz']}
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,observed_episode=str(ep),window_actions=30,minimum_progress_cap_mm=.1,remaining_fraction=.5,first_trigger=trigger,evaluated_prefix=rows,source_sha256=sources,analyzer_sha256=sha(__file__),next='First verify an original guarded vertical unload at this actual request and independent KKT; then explicit state lifecycle/native audit and full paired physics. No old solver failure is fabricated.',physics=False,training_ready=False)
with dest.open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(episode=ep.name,first_trigger=trigger,requests_checked=len(rows)),indent=2))
