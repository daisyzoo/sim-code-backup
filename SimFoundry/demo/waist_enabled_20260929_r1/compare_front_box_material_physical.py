"""Compare complete matched diagnostic numeric outcomes; never certify controls.
Keep per-condition/category/group failures and original baseline. No cherry-pick,
training admission or claim that better open-loop score implies model success.
"""
from pathlib import Path
import datetime,hashlib,json
W=Path(__file__).resolve().parent;R=W/'front_box_material_physical_r1';B=W/'front_corridor_midpoint_physical_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={}
def read(p):sources[str(p)]=sha(p);return json.loads(p.read_text())
p=read(R/'PROTOCOL.json');bp=read(B/'PROTOCOL.json');assert p['plan']['groups']==bp['plan']['groups'];rows=[]
for c,bc in zip(p['plan']['commands'],bp['plan']['commands']):
 assert (c['layout_id'],c['tasks'],c['group'],c['wait'])==(bc['layout_id'],bc['tasks'],bc['group'],bc['wait'])
 for task in c['tasks']:
  name=f"layout_{c['layout_id']}_{task}";ep=R/f"case_{c['layout_id']}"/name;old=B/f"case_{c['layout_id']}"/name;marker=read(ep/'READY_FOR_AUDIT.json');short=marker['executed_frames']<marker['requested_frames']
  n=read(ep/('FRONT_BOX_MATERIAL_INCOMPLETE_REVIEW.json' if short else 'FRONT_BOX_MATERIAL_V1_STAGE_NUMERIC_REVIEW.json'));b=read(old/'FRONT_CORRIDOR_MIDPOINT_STAGE_NUMERIC_REVIEW.json')
  assert sha(ep/'raw.npz')==n['raw_sha256'] and sha(old/'raw.npz')==b['raw_sha256']
  row=dict(episode=name,group=c['group'],task=task,wait=c['wait'],frames=n['frames'],baseline_frames=b['frames'],passed=n['original_task_and_pose_passed'],baseline_passed=b['original_task_and_pose_passed'],training_ready=False)
  if not c['wait']:
   for key in ['progress_mm','non_target_max_xy_mm','tilt_exit_count','lost_contact_exit_count']:
    if key in n and key in b:row[key]=n[key];row['baseline_'+key]=b[key];row['delta_'+key]=n[key]-b[key]
   log=read(ep/'frontal_bypass.json');events=[v['front_box_material_preload'] for v in log['rows'] if v.get('front_box_material_preload',{}).get('override')]
   row.update(selected=log['plan'].get('front_box_material_preload',{}).get('enabled',False),material_proposals=len(events),maximum_preload_m=max((v['preload_m'] for v in events),default=0.))
  rows.append(row)
assert len(rows)==10
groups={}
for v in rows:
 g=groups.setdefault(str(v['group']),dict(push_passed=0,push_total=0,wait_passed=0,wait_total=0,baseline_push_passed=0,baseline_wait_passed=0,training_ready=False));kind='wait' if v['wait'] else 'push';g[kind+'_total']+=1;g[kind+'_passed']+=int(v['passed']);g['baseline_'+kind+'_passed']+=int(v['baseline_passed'])
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,groups=groups,push_passed=sum(v['passed'] for v in rows if not v['wait']),wait_passed=sum(v['passed'] for v in rows if v['wait']),source_sha256=sources,all_original_controls_and_actual_images_required=True,model_goal_achieved=False,training_ready=False)
with (R/'NUMERIC_COMPARISON.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(push_passed=report['push_passed'],wait_passed=report['wait_passed'],groups=groups),indent=2))
