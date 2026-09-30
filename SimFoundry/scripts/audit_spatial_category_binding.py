#!/usr/bin/env python3
"""Audit metadata support, not learned model behavior or physical feasibility."""
import json,argparse
from pathlib import Path
import numpy as np

def main():
 p=argparse.ArgumentParser();p.add_argument('--provenance',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 data=json.loads(a.provenance.read_text());layouts={}
 for r in data['records']:
  if r['task_id']=='wait_no_package':continue
  with np.load(r['path']) as raw:m=json.loads(str(raw['collect_meta']))
  lid=r['layout_id'];xy={k:m[k][:2] for k in ['box_xyz','mailer_xyz']}
  if lid in layouts:
   assert all(np.allclose(layouts[lid][k],xy[k],atol=1e-5) for k in xy),'Paired initial placement mismatch'
  layouts[lid]=xy
 result={'unique_push_layouts':len(layouts),'position_only_rule':'box iff world Y<0, bag iff world Y>0; descriptive support audit, NOT model accuracy','position_only_rule_accuracy':sum(v['box_xyz'][1]<0 for v in layouts.values())/len(layouts)/2+sum(v['mailer_xyz'][1]>0 for v in layouts.values())/len(layouts)/2,'ranges':{},'layouts':layouts}
 for key in ['box_xyz','mailer_xyz']:
  xy=np.array([r[key] for r in layouts.values()]);result['ranges'][key]={'min_xy':xy.min(0).tolist(),'max_xy':xy.max(0).tolist()}
 a.out.write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='layouts'},indent=2))
if __name__=='__main__':main()
