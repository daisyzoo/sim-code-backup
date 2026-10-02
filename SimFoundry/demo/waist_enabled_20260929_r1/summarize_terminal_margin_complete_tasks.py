"""Complete original task/pose and actual visual result; control audits still separate."""
from pathlib import Path
import json,hashlib,datetime
W=Path(__file__).resolve().parent;R=W/'terminal_margin_physical_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={}
def read(p):sources[str(p)]=sha(p);return json.loads(p.read_text())
protocol=read(R/'PROTOCOL.json');status=read(R/'STATUS.json');assert status['completed_conditions']==10 and status['status']=='collection_complete_audits_visual_pending'
p=Path('/proc')/str(status['pid']);assert not p.exists() or (p/'stat').read_text().split()[2]=='Z'
for p,h in protocol['frozen_files_sha256'].items():assert sha(p)==h,p
rows=[]
for c in protocol['plan']['commands']:
 for task in c['tasks']:
  ep=R/f"case_{c['layout_id']}"/f"layout_{c['layout_id']}_{task}";q=read(ep/'quality.json');n=read(ep/'TERMINAL_MARGIN_STAGE_NUMERIC_REVIEW.json');v=read(ep/'ACTUAL_REVIEW_BINDING.json')
  assert q['frames']==n['frames']==(70 if c['wait'] else 1200)
  assert sha(ep/'raw.npz')==n['raw_sha256']==v['raw_sha256'];assert v['numeric_review_sha256']==sha(ep/'TERMINAL_MARGIN_STAGE_NUMERIC_REVIEW.json');assert v['review_sheet_sha256']==sha(ep/'TERMINAL_MARGIN_REVIEW.jpg')==n['review_sheet_sha256']
  assert v['actual_visual_review'].startswith('completed_actual_view') and len(v['sampled_rgb_frames'])==8 and len(v['sampled_viewer_frames'])==(0 if c['wait'] else 4)
  assert v['sampled_rgb_frames']==n['sampled_rgb_frames'] and v['sampled_viewer_frames']==n['sampled_viewer_frames']
  for name,h in v['external_source_sha256'].items():assert sha(ep.parent/('viewer_'+ep.name)/name)==h
  assert n['initial11_q_max_abs']==n['initial11_action_max_abs']==n['assist_frames']==0
  assert n['recomputed_quality']['passed']==q['passed']
  rows.append(dict(episode=ep.name,group=c['group'],wait=c['wait'],original_task_and_pose_passed=n['original_task_and_pose_passed'],progress_mm=n.get('progress_mm'),non_target_max_xy_mm=n.get('non_target_max_xy_mm'),end_mode=q['expert_end_mode'],quality_reasons=q['reasons'],actual_visual_review=v['actual_visual_review'],training_admitted=False))
assert len(rows)==10
groups=[]
for group in protocol['plan']['groups']:
 rs=[r for r in rows if r['group']==group['group']];assert len(rs)==5
 groups.append(dict(group=group['group'],push_passed=sum(r['original_task_and_pose_passed'] for r in rs if not r['wait']),push_total=4,wait_passed=all(r['original_task_and_pose_passed'] for r in rs if r['wait']),control_audits_complete=False,training_admitted=False))
result=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='task_and_visual_complete_control_audits_pending',scope=__doc__,push_passed=sum(r['original_task_and_pose_passed'] for r in rows if not r['wait']),push_total=8,wait_passed=sum(r['original_task_and_pose_passed'] for r in rows if r['wait']),wait_total=2,groups=groups,rows=rows,frozen_sources_verified=len(protocol['frozen_files_sha256']),source_sha256=sources,script_sha256=sha(__file__),training_ready=False,model_goal_achieved=False)
dest=R/'TASK_AND_VISUAL_RESULT.json';assert not dest.exists();dest.write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k not in ['rows','source_sha256','scope']},indent=2))
