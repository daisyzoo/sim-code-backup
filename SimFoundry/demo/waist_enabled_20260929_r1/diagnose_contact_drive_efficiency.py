"""Describe same-phase command/support/object movement; no counterfactual physics.
Support reference is a controller virtual point, not necessarily the contact COP.
The front/rear episodes have different layouts/controllers: no causal attribution.
"""
from pathlib import Path
import datetime,json,hashlib,sys
import numpy as np
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inspect(ep):
 ep=Path(ep).resolve();migration=json.loads((ep/'CONTACT_MIGRATION.json').read_text())
 for p,h in migration['source_sha256'].items():assert sha(p)==h
 fr=json.loads((ep/'frontal_bypass.json').read_text());rows={x['step']:x for x in fr['rows']};direction=fr['plan']['direction'];out=[]
 for bout in migration['bouts']:
  frames=[t for t in range(bout['start'],bout['end']) if t in rows and t+1 in rows and rows[t]['mode']==rows[t+1]['mode']=='top_push']
  if not frames:continue
  now=[rows[t] for t in frames];after=[rows[t+1] for t in frames]
  def arr(rs,key):return np.asarray([x[key] for x in rs],float)
  obj=arr(now,'observed_target');obj_next=arr(after,'observed_target');sup=arr(now,'observed_support_xyz');sup_next=arr(after,'observed_support_xyz');cmd=arr(now,'target_xyz');cmd_next=arr(after,'target_xyz');offset=arr(now,'observed_support_offset_local');offset_next=arr(after,'observed_support_offset_local')
  def stats(v):return dict(mean=float(np.mean(v)),median=float(np.median(v)),min=float(np.min(v)),max=float(np.max(v)))
  object_step=(obj_next[:,1]-obj[:,1])*direction*1000;support_step=(sup_next[:,1]-sup[:,1])*direction*1000;command_step=(cmd_next[:,1]-cmd[:,1])*direction*1000
  out.append(dict(start=bout['start'],end=bout['end'],exit_reason=bout['exit_reason'],paired_intervals=len(frames),object_forward_mm_per_action=stats(object_step),support_forward_mm_per_action=stats(support_step),command_forward_mm_per_action=stats(command_step),current_command_ahead_of_observed_support_mm=stats((cmd[:,1]-sup[:,1])*direction*1000),support_forward_relative_to_object_mm_per_action=stats(support_step-object_step),support_reference_offset_change_max_mm=float(np.max(np.linalg.norm(offset_next-offset,axis=1))*1000),hand_contact_local_y_migration_mm=bout['hand_contact_y_change_mm'],object_forward_total_mm=float(object_step.sum()),support_forward_total_mm=float(support_step.sum()),command_forward_total_mm=float(command_step.sum())))
 return dict(episode=str(ep),quality=json.loads((ep/'quality.json').read_text()),bouts=out,source_sha256={str(p):sha(p) for p in [ep/'CONTACT_MIGRATION.json',ep/'frontal_bypass.json',ep/'quality.json',Path(__file__)]})
def main(paths,out):
 result=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=[inspect(p) for p in paths],training_ready=False)
 with Path(out).open('x') as f:json.dump(result,f,indent=2)
 for row in result['rows']:
  print(Path(row['episode']).name)
  for b in row['bouts']:
   print(b['start'],b['end'],'object/support/command mean mm',*[round(b[k]['mean'],3) for k in ['object_forward_mm_per_action','support_forward_mm_per_action','command_forward_mm_per_action']],'lead',round(b['current_command_ahead_of_observed_support_mm']['mean'],3),'refchange',round(b['support_reference_offset_change_max_mm'],6))
if __name__=='__main__':main(sys.argv[2:],sys.argv[1])
