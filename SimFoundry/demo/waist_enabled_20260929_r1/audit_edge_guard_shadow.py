"""Check proposed loaded-contact edge guard timing on recorded pre-action observations."""
from pathlib import Path
import sys,json
import numpy as np
from scipy.spatial.transform import Rotation
root=Path(__file__).resolve().parent;sys.path.insert(0,str(root.parents[1]))
from simfoundry.data.top_contact_load_geometry import loaded_forward_margin
run=Path(sys.argv[1]).resolve();rows=[]
for ep in sorted(run.glob('case_*/layout_*')):
 side='right' if 'push_box' in ep.name else 'left';key='box' if side=='right' else 'mailer';actor='parcel_box' if side=='right' else 'mailer';direction=-1 if side=='right' else 1
 tr=np.load(ep/'trace.npz');ori=np.load(ep/'parcel_orientation.npz');log=json.loads((ep/'frontal_bypass.json').read_text());size=log['plan']['top_recontact']['contact_size_xyz'];force={r['after_action_step']:r for r in json.loads((ep/'solved_contact_forces.json').read_text())['rows']};tilts=np.arccos(np.clip(Rotation.from_quat(ori[key]).as_matrix()[:,2,2],-1,1));segments=[]
 for r in log['rows']:
  if r['mode']!='top_push':continue
  t=r['step'];obs=loaded_forward_margin(force.get(t-1),side,actor,tr[key][t],ori[key][t],size,direction)
  if not segments or t!=segments[-1][-1]['step']+1:segments.append([])
  edge=obs['valid'] and obs['normal_load_n']>.3 and obs['weighted_forward_edge_distance_m']<.012
  segments[-1].append(dict(step=t,observed_tilt_rad=float(tilts[t]),edge_trigger=bool(edge),tilt_trigger=bool(tilts[t]>.03),loaded_contact=obs))
 summaries=[]
 for seg in segments:
  trigger=next((x for x in seg if x['edge_trigger'] or x['tilt_trigger']),None);hard=next((x['step'] for x in seg if x['observed_tilt_rad']>.2),None)
  summaries.append(dict(first_step=seg[0]['step'],last_step=seg[-1]['step'],first_guard=trigger,first_tilt_over_02_rad=hard,records=seg))
 row=dict(episode=ep.name,segments=summaries);rows.append(row);print(ep.name,[(s['first_step'],None if s['first_guard'] is None else s['first_guard']['step'],s['first_tilt_over_02_rad']) for s in summaries])
(run/'EDGE_GUARD_SHADOW.json').write_text(json.dumps(dict(rows=rows,scope='No controller change or action executed. Uses previous solved contact packet with current pre-action parcel pose, as live observer would. Edge<12mm with normal load>0.3N or tilt>0.03rad. Timing lead does not prove removal of force is fast enough or task success; contact lifetime and recovery path will change under control.',training_ready=False),indent=2))
