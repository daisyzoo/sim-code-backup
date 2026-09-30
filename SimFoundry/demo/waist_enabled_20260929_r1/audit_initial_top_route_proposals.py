from pathlib import Path
import sys,json,math,hashlib
root=Path(__file__).resolve().parent;sys.path.insert(0,str(root.parents[1]))
from simfoundry.data.initial_top_route_candidate import initial_top_route_candidate
rows=[]
for identifier in range(62000,62016):
 p=root/f'development_layouts/{identifier}.json';d=json.loads(p.read_text());assert d['layout_id']==identifier and d['planned_split']=='development'
 for key,other,size,osize,direction in [('box','mailer',(.14,.09,.045),(.15,.145,.04),-1),('mailer','box',(.15,.145,.04),(.14,.09,.045),1)]:
  quat=lambda yaw:(0,0,math.sin(yaw/2),math.cos(yaw/2))
  r=initial_top_route_candidate(d[key+'_xyz'],d[other+'_xyz'],size,osize,quat(d[key+'_yaw']),quat(d[other+'_yaw']),direction)
  rows.append(dict(layout_id=d['layout_id'],target=key,layout_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),**r))
out=dict(rows=rows,source_sha256=hashlib.sha256((root.parents[1]/'simfoundry/data/initial_top_route_candidate.py').read_bytes()).hexdigest(),scope='All32 task conditions of16 development layouts only; independent test geometry untouched. Proposal is not wired or simulated, no dataset admission. Retains all rejected candidates.',training_ready=False)
(root/'INITIAL_TOP_ROUTE_PROPOSALS.json').write_text(json.dumps(out,indent=2));print('Proposed:',[(r['layout_id'],r['target'],round(r['transfer_m'],3)) for r in rows if r['proposed']])
