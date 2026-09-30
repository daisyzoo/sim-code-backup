from pathlib import Path
import json,hashlib,numpy as np
from simfoundry.data.front_top_route import select_front_route
from simfoundry.data.top_contact_visibility import visible_waist_preference
w=Path('demo/waist_enabled_20260929_r1/fresh_lateral_00_pilot_r1');rows=[]
for ep in sorted(w.glob('case_840001/layout_*')):
 target='box' if 'push_box' in ep.name else 'mailer';other='mailer' if target=='box' else 'box';size=(.14,.09,.045) if target=='box' else (.15,.145,.04);other_size=(.15,.145,.04) if target=='box' else (.14,.09,.045);direction=-1 if target=='box' else 1
 with np.load(ep/'trace.npz') as tr,np.load(ep/'parcel_orientation.npz') as ori,np.load(ep/'raw.npz') as raw:
  chosen,routes=select_front_route(tr[target][0],tr[other][0],size,other_size,ori[target][0],ori[other][0],direction,margin=.012)
  log=json.loads((ep/'frontal_bypass.json').read_text());last=log['rows'][-1];rgbshape=raw['rgb'].shape;q=raw['q'];intr=raw['intrinsics'];samples=[]
  for t in [0,60,120,171,342,1199]:
   samples.append(dict(frame=t,**visible_waist_preference(tr[target][t],ori[target][t],size,intr,rgbshape[3],rgbshape[2],float(q[t,12]),1.)))
  rows.append(dict(episode=ep.name,raw_sha256=hashlib.sha256((ep/'raw.npz').read_bytes()).hexdigest(),actual_selected_route='rear',front_candidate_selected_at_original_reset=chosen,routes=routes,final_control=last,visibility_candidates=samples,scope='Read-only counterfactual geometry and projected bbox. Does not prove robot reach, dynamics, contact safety or occlusion-free visibility; original failed episode remains rejected.'))
  print(ep.name,'front',bool(chosen),'camera',samples[-1],flush=True)
(w/'SWAPPED_ROUTE_AND_VISIBILITY_DIAGNOSIS.json').write_text(json.dumps(dict(rows=rows,training_ready=False),indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else x.tolist()))
