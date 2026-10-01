"""Read-only recorded command, geometry and original guard precedence audit."""
from pathlib import Path
import json,sys,hashlib,math
import numpy as np
W=Path(__file__).resolve().parent;sys.path.insert(0,str(W.parents[1]))
from simfoundry.data.tabletop_route_candidates import footprint_radii
p=Path(sys.argv[1]);log=json.loads((p/'frontal_bypass.json').read_text());ctrl=json.loads((p/'expert_control.json').read_text());side='right' if 'push_box' in p.name else 'left';target='box' if side=='right' else 'mailer';other='mailer' if side=='right' else 'box';size=(.14,.09,.045) if side=='right' else (.15,.145,.04);other_size=(.15,.145,.04) if side=='right' else (.14,.09,.045)
with np.load(p/'trace.npz') as z:tr={k:z[k] for k in z.files}
with np.load(p/'parcel_orientation.npz') as z:ori={k:z[k] for k in z.files}
errors=[];rows=[];previous_top=None
for r in log['rows']:
 t=r['step'];f=r.get('clearance_feedback')
 if f is None:continue
 if r['mode']!='top_push' and f['eligible']:errors.append(f'feedback applied outside loaded push:{t}')
 if not f['eligible']:continue
 radii=[footprint_radii(s,q) for s,q in [(size,ori[target][t]),(other_size,ori[other][t])]]
 gaps=[abs(tr[target][t,i]-tr[other][t,i])-radii[0][i]-radii[1][i] for i in (0,1)]
 if max(gaps)<.01-1e-7:errors.append(f'original parcel guard bypassed:{t}')
 if float(np.linalg.norm(tr[other][t,:2]-tr[other][0,:2]))>.01+1e-7:errors.append(f'original other motion guard bypassed:{t}')
 if r['hand_obstacle_gap_m']<.005-1e-7:errors.append(f'original hand guard bypassed:{t}')
 if max(abs(a-b) for a,b in zip(gaps,f['axis_gaps_m']))>1e-6:errors.append(f'geometry differs:{t}')
 if max(abs(r['target_xyz'][i]-f['command_xy'][i]) for i in (0,1))>1e-9:errors.append(f'feedback not mapped to waypoint:{t}')
 if max(abs(ctrl[t]['target_xyz'][i]-r['target_xyz'][i]) for i in range(3))>1e-9:errors.append(f'expert waypoint mismatch:{t}')
 prev=ctrl[t-1]['target_xyz'] if t>0 and ctrl[t-1]['mode']=='top_push' else r['observed_support_xyz']
 step=max(abs(f['command_xy'][i]-prev[i]) for i in (0,1))
 if step>.0030001:errors.append(f'command step exceeded:{t}')
 if f['planned_table_margin_m']<.005-1e-7:errors.append(f'planned table corridor unsafe:{t}')
 rows.append(dict(frame=t,stage=f['stage'],command_step_m=step,axis_gaps_m=gaps))
if log['plan'].get('initial_top_selected') and any(r['mode']=='top_push' for r in log['rows']) and not rows:errors.append('missing actual loaded feedback')
report=dict(passed=not errors,errors=errors,feedback_frames=len(rows),clearance_correction_frames=sum(r['stage']=='clearance_x' for r in rows),rows=rows,raw_sha256=hashlib.sha256((p/'raw.npz').read_bytes()).hexdigest(),scope='Recorded pre-action geometry, original outer guards, actual expert waypoint mapping and3mmXY command bound. Does not replace full task/pose, contact, visuals or complete-group checks.',training_ready=False)
(p/'CLEARANCE_FEEDBACK_LIVE_AUDIT.json').write_text(json.dumps(report,indent=2));print({k:v for k,v in report.items() if k!='rows'});assert report['passed']
