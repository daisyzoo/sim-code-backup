"""Recorded-pose stage-logic shadow; no commands or physical replay."""
from pathlib import Path
import json,sys,hashlib
import numpy as np
from scipy.spatial.transform import Rotation
root=Path(__file__).resolve().parent;sys.path.insert(0,str(root.parents[1]))
from simfoundry.data.front_clearance_progress import FrontClearanceProgress
p=Path(sys.argv[1]);tr=np.load(p/'trace.npz');ori=np.load(p/'parcel_orientation.npz');r=json.loads((p/'frontal_bypass.json').read_text());s=FrontClearanceProgress(.012,float(tr['box'][0,1]));events=[];old=None;history=[]
stop=next(v['step'] for v in r['rows'] if v.get('route_stop_reason'))
for t in range(1,stop+1):
 radii={k:abs(Rotation.from_quat(ori[k][t]).as_matrix())@np.array(size)/2 for k,size in [('box',[.14,.09,.045]),('mailer',[.15,.145,.04])]}
 gap=float(tr['mailer'][t,0]-tr['box'][t,0]-radii['box'][0]-radii['mailer'][0]);row=s.update(gap,float(tr['box'][t,1]));row.update(step=t,gap_m=gap)
 if row['route_stage']!=old:events.append(row.copy());old=row['route_stage']
 history.append(row)
out=dict(actual_stop_step=stop,actual_recovery_threshold_m=.009,actual_emergency_stop_m=.01,shadow_events=events,history=history,raw_sha256=hashlib.sha256((p/'raw.npz').read_bytes()).hexdigest(),scope='Fixed recorded geometry. Shadow resumes at12.5mm and restores clearance below12mm, holding the CURRENT objectY on each correction. It does not prove corrective commands can restore clearance or avoid the unchanged10mm stop in physics.',training_ready=False)
(p/'CLEARANCE_PROGRESS_SHADOW.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k!='history'},indent=2))
