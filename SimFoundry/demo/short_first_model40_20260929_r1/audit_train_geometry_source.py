import json,hashlib,collections
from pathlib import Path
W=Path('/home/user/Documents/zoo/sim'); result=[]
for name in ['lerobot_sim_paired_coverage80_20260928','lerobot_sim_short_first_pilot40_20260929']:
 meta=W/'lerobot'/name/'meta'; prov=json.loads((meta/'paired_provenance.json').read_text());split=json.loads((meta/'train_validation_split.json').read_text()); rows=[]; cache={}
 for ep in split['train']:
  rec=prov['records'][ep]
  if rec['task_id']=='wait_no_package':continue
  p=Path(rec['path']); p=p if p.is_absolute() else W/p
  mp=p.parent.parent/'manifest.json'
  if mp not in cache:cache[mp]=json.loads(mp.read_text())
  found=[g['layout'] for g in cache[mp] if 'layout' in g and g['layout']['layout_id']==rec['layout_id']];assert len(found)==1,(mp,rec)
  layout=found[0];assert hashlib.sha256(p.read_bytes()).hexdigest()==rec['hash']
  rows.append(dict(episode=ep,task=rec['task_id'],source_sha256=rec['hash'],manifest=str(mp.relative_to(W)),manifest_sha256=hashlib.sha256(mp.read_bytes()).hexdigest(),layout=layout))
 summary={}
 for task in sorted(set(r['task'] for r in rows)):
  rr=[r for r in rows if r['task']==task];obj='box' if task=='push_box_to_bin' else 'mailer'
  ranges={}
  for o in ['box','mailer']:
   for axis,i in [('x',0),('y',1)]:
    v=[r['layout'][o+'_xyz'][i] for r in rr];ranges[o+'_'+axis]=dict(min=min(v),max=max(v),span=max(v)-min(v))
   v=[r['layout'][o+'_yaw'] for r in rr if o+'_yaw' in r['layout']];ranges[o+'_yaw']=dict(min=min(v),max=max(v),span=max(v)-min(v),unique=len(set(v)),missing=len(rr)-len(v)) if v else dict(missing=len(rr))
  positions=collections.Counter('target_near' if r['layout'][obj+'_xyz'][0]<r['layout'][('mailer' if obj=='box' else 'box')+'_xyz'][0] else 'target_far' for r in rr)
  summary[task]=dict(episodes=len(rr),unique_layouts=len(set(r['layout']['layout_id'] for r in rr)),unique_geometry_groups=len(set(r['layout'].get('geometry_group','legacy_'+str(r['layout']['layout_id'])) for r in rr)),position_counts=dict(positions),ranges=ranges,unique_layout_seeds=len(set(r['layout']['seed'] for r in rr)))
 result.append(dict(dataset=name,scope='Training split only; requested initial geometry from source manifests, not settled pose or material binding',provenance_sha256=hashlib.sha256((meta/'paired_provenance.json').read_bytes()).hexdigest(),split_sha256=hashlib.sha256((meta/'train_validation_split.json').read_bytes()).hexdigest(),summary=summary,rows=rows))
out=W/'SimFoundry/demo/short_first_model40_20260929_r1/TRAIN_GEOMETRY_COVERAGE.json';assert not out.exists();out.write_text(json.dumps(dict(datasets=result,not_causal_proof=True,goal_complete=False),indent=2));print(json.dumps([dict(dataset=x['dataset'],summary=x['summary']) for x in result],indent=2))
