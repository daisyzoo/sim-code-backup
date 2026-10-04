"""Compare all planned candidate conditions to same2mm parent without admission.
Can report partial progress explicitly; recorded event counts are not audited
command correctness. Quality/audit failures and missing images remain visible.
"""
from pathlib import Path
import argparse,collections,datetime,hashlib,json
W=Path(__file__).resolve().parent;R=W/'front_recontact_physical_r1';BASE=W/'front_corridor_midpoint_physical_r1'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def compare():
 sources={};rows=[]
 def read(p):
  sources[str(p)]=sha(p);return json.loads(p.read_text())
 protocol=read(R/'PROTOCOL.json')
 for c in protocol['plan']['commands']:
  for task in c['tasks']:
   ep=R/f"case_{c['layout_id']}"/f"layout_{c['layout_id']}_{task}";parent=BASE/ep.parent.name/ep.name
   row=dict(episode=ep.name,group=c['group'],wait=c['wait'],quality_available=(ep/'quality.json').exists(),expected_frames=70 if c['wait'] else 1200,training_admitted=False)
   if not row['quality_available']:row['status']='pending_collection';rows.append(row);continue
   quality=read(ep/'quality.json');old=read(parent/'quality.json');row.update(frames=quality['frames'],quality_passed=quality['passed'],parent_quality_passed=old['passed'],status='collected_independent_evidence_pending')
   if not c['wait']:
    for label,data in [('candidate',quality),('parent',old)]:row[label+'_progress_mm']=1000*data['metrics']['target_final_progress_m']
    row['progress_difference_mm']=row['candidate_progress_mm']-row['parent_progress_mm']
    fr=read(ep/'frontal_bypass.json');row['modes']=dict(collections.Counter(x['mode'] for x in fr['rows']));row['guard_reasons']=dict(collections.Counter(x['route_stop_reason'] for x in fr['rows'] if x.get('route_stop_reason')))
   data=read(ep/'front_recontact_center.json');events=data['rows'];row.update(recontact_selected=data['selected'],recorded_event_kinds=dict(collections.Counter(x['kind'] for x in events)),recorded_handovers=[dict(step=x['step'],counter=x['real_recontact_index']) for x in events if x['kind']=='handover'],unchanged_reasons=dict(collections.Counter(x['reason'] for x in events if x['kind']=='unchanged')),event_counts_not_control_certification=True)
   if (ep/'AUDIT_EXECUTION.json').exists():
    a=read(ep/'AUDIT_EXECUTION.json');row.update(audits_complete=a['completed'],audit_count=len(a['rows']),failed_audits=[x['script'] for x in a['rows'] if x['returncode']!=0])
   else:row.update(audits_complete=False,audit_count=0,failed_audits=[])
   row['actual_images_bound']=(ep/'ACTUAL_REVIEW_BINDING.json').exists()
   if row['actual_images_bound']:read(ep/'ACTUAL_REVIEW_BINDING.json')
   rows.append(row)
 groups=[]
 for g in protocol['plan']['groups']:
  rs=[x for x in rows if x['group']==g['group']];push=[x for x in rs if not x['wait']];groups.append(dict(group=g['group'],completed_pushes=sum(x['quality_available'] for x in push),quality_passed_pushes=sum(x.get('quality_passed',False) for x in push),planned_pushes=4,training_admitted=False))
 return dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,planned_conditions=10,completed_conditions=sum(r['quality_available'] for r in rows),rows=rows,groups=groups,source_sha256=sources,training_ready=False,model_goal_achieved=False)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path);args=p.parse_args();result=compare()
 if args.out:
  with args.out.open('x') as f:json.dump(result,f,indent=2)
 print(json.dumps({k:v for k,v in result.items() if k!='source_sha256'},indent=2))
