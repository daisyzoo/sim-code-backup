"""Verify reverse command-view composition on actual old contexts and saved candidates.
Does not alter histories or certify any candidate physical episode.
"""
from pathlib import Path
import copy,datetime,gzip,hashlib,json,sys
import numpy as np
W=Path(__file__).resolve().parent;D=W/'front_normal_parent_coordinate_r1';D.mkdir(exist_ok=False);sys.path.insert(0,str(W))
from front_normal_parent_coordinate_v1 import parent_coordinate
from joint_transport_parent_coordinate_v1 import parent_coordinate as original
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
counts=dict(frames=0,coordinate_frames=0,normal_applied=0,transport_applied=0);negative=[];sources={}
for item in read(W/'front_cross_track_full_stream_probe_r1/CENSUS.json')['episodes']:
 ep=Path(item['episode']);cs={} if item['wait'] else {r['step']:r for r in read(ep/'coordination.json')};trs=read(ep/'joint_transport_clearance.json')['rows'];f=W/'front_normal_command_records_r1'/(ep.name+'.json.gz')
 with gzip.open(f,'rt') as z:nrs=json.load(z)['rows']
 for t,tr in enumerate(trs):
  c=cs.get(t);nr=nrs[t];mid=tr['output_command'];parent=tr['parent_command'];final=nr['output_command'];expected=original(c,parent,mid)
  off=parent_coordinate(c,parent,mid,normal_enabled=False);assert off==expected
  new=copy.deepcopy(c)
  if new is not None:
   new['front_normal_nondegradation']=copy.deepcopy(nr)
   if nr['applied']:new['normal_planning_unexecuted_parent_waist_target_rad']=new['waist_target_rad'];new['waist_target_rad']=final[0]
   before=copy.deepcopy(new)
  on=parent_coordinate(new,parent,final,normal_enabled=True)
  if c is not None:
   assert new==before and on['waist_target_rad']==expected['waist_target_rad']
   assert all(on[k]==expected[k] for k in expected)
   assert all(on[k] is new[k] for k in new if k!='waist_target_rad')
   counts['coordinate_frames']+=1
  else:assert on is None
  counts['frames']+=1;counts['normal_applied']+=nr['applied'];counts['transport_applied']+=tr['applied']
  if ep.name=='layout_840020_push_box_to_bin' and t==1009:
   for label in ['missing_record','wrong_step','wrong_parent','wrong_final','wrong_parent_waist','wrong_final_waist','not_bool','disabled_with_record']:
    bad=copy.deepcopy(new);enabled=True
    if label=='missing_record':bad.pop('front_normal_nondegradation')
    elif label=='wrong_step':bad['front_normal_nondegradation']['step']+=1
    elif label=='wrong_parent':bad['front_normal_nondegradation']['parent_command'][0]+=.001
    elif label=='wrong_final':bad['front_normal_nondegradation']['output_command'][0]+=.001
    elif label=='wrong_parent_waist':bad['normal_planning_unexecuted_parent_waist_target_rad']+=.001
    elif label=='wrong_final_waist':bad['waist_target_rad']+=.001
    elif label=='not_bool':bad['front_normal_nondegradation']['applied']=1
    else:enabled=False
    try:parent_coordinate(bad,parent,final,normal_enabled=enabled)
    except (AssertionError,KeyError):negative.append(dict(case=label,rejected=True))
    else:raise AssertionError(label)
 for p in [f,ep/'joint_transport_clearance.json']+([] if item['wait'] else [ep/'coordination.json']):sources[str(p)]=sha(p)
assert counts['frames']==9740 and counts['normal_applied']==34 and len(negative)==8
for p in [Path(__file__),W/'front_normal_parent_coordinate_v1.py',W/'joint_transport_parent_coordinate_v1.py']:sources[str(p)]=sha(p)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,**counts,negative=negative,source_sha256=sources,training_ready=False,physical_rollout_verified=False)
(D/'RESULT.json').write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k not in ['source_sha256','scope']})
