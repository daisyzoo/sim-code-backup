"""Original unchanged math/inventory and real unselected native/pose regression.
Old physical files are read-only. This does not rebrand old data as new physics.
"""
from pathlib import Path
import ast,sys,json,hashlib,datetime,os
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path[:0]=[str(W),str(ROOT)]
from rear_corridor_stage_run_contract_v2 import primary as old_primary,controls as old_controls,ADDITIONAL as old_add,REPORTS as old_reports
from rear_latched_run_contract import primary,controls,ADDITIONAL,REPORTS
from audit_rear_corridor_native_commands_v2 import verify_files as old_native
from audit_rear_corridor_latched_native import verify_files as new_native
from audit_rear_corridor_stage_pose_live import verify_files as old_pose
from audit_rear_latched_stage_pose_live import verify_files as new_pose
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();prep=json.loads((W/'REAR_LATCHED_ORIGINAL_AUDIT_PREPARATION.json').read_text());mapping={k+'.py':v+'.py' for k,v in prep['mapping'].items()};dest=W/'REAR_LATCHED_ORIGINAL_AUDIT_V2_CHECK.json';assert not dest.exists();rows=[];sources={};frozen={str(W/'REAR_LATCHED_ORIGINAL_AUDIT_PREPARATION.json'):sha(W/'REAR_LATCHED_ORIGINAL_AUDIT_PREPARATION.json'),str(Path(__file__)):sha(__file__)}
def save(status,**kw):
 tmp=dest.with_suffix('.tmp');tmp.write_text(json.dumps(dict(status=status,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,source_sha256=sources,frozen_sha256=frozen,training_ready=False,**kw),indent=2));tmp.replace(dest)
try:
 save('running')
 for item in prep['files']:
  a=W/(item['parent']+'.py');b=W/(item['output']+'.py');assert sha(a)==item['parent_sha256'] and sha(b)==item['output_sha256'];s=b.read_text()
  for e in reversed(item['edits']):assert s.count(e['new'])==e['count'];s=s.replace(e['new'],e['old'])
  assert s==a.read_text();frozen[str(a)]=sha(a);frozen[str(b)]=sha(b)
 for n,h in prep['external_sha256'].items():assert sha(W/(n+'.py'))==h;frozen[str(W/(n+'.py'))]=h
 for ep in sorted((W/'rear_corridor_physical_r1').glob('case_*/layout_*')):
  if not (ep/'raw.npz').exists():continue
  wait='wait_no_package' in ep.name;fr={} if wait else json.loads((ep/'frontal_bypass.json').read_text());plan=fr.get('plan',{})
  old=list(dict.fromkeys(old_primary(wait)+['audit_rear_corridor_stage_contacts.py','audit_rear_corridor_stage_pressure.py']+([] if wait else old_controls(plan)+old_add)))
  new=list(dict.fromkeys(primary(wait)+['audit_rear_latched_stage_contacts.py','audit_rear_latched_stage_pressure.py']+([] if wait else controls(plan)+ADDITIONAL)))
  assert new==[mapping.get(x,x) for x in old]
  for a,b in zip(old,new):assert old_reports[a][1]==REPORTS[b][1]
  selected=plan.get('rear_joint_xy_progress',{}).get('enabled',False)
  row=dict(episode=ep.name,audit_inventory_count=len(new),all_original_checks_preserved=True,rear_selected=selected)
  if not selected:
   before=old_native(ep,ROOT,W/'staged_rear_corridor_recovery_guarded');after=new_native(ep,ROOT,W/'staged_rear_corridor_latched')
   projection={k:v for k,v in after.items() if k not in ['phase_records','phase_final_state']};assert before==projection
   row['actual_unselected_native_identical']=True
   for n in ['raw.npz','rear_corridor_recovery.json']:sources[str(ep/n)]=sha(ep/n)
  if ep.name in ['layout_840005_push_box_to_bin','layout_840005_nudge_mailer_to_bin']:
   before=old_pose(ep,W/'staged_rear_corridor_recovery_guarded');after=new_pose(ep,W/'staged_rear_corridor_latched');assert after['recovery_boundary'].pop('phase_records')==[];assert after['recovery_boundary'].pop('phase_final_state')==dict(active=False,last_step=0,entry_step=None);assert before==after
   row['actual_full_front_pose_identical']=True
   for p in ep.iterdir():
    if p.is_file() and p.suffix in ['.json','.npz'] and 'AUDIT' not in p.name:sources[str(p)]=sha(p)
  rows.append(row);save('running');print(ep.name,row,flush=True)
 for p,h in {**sources,**frozen}.items():assert sha(p)==h,p
 assert len(rows)==10 and sum(r.get('actual_unselected_native_identical',False) for r in rows)==8
 save('complete',passed=True,adapter_files=len(prep['files']),full_front_pose_regressions=2,actual_unselected_native_regressions=8)
except BaseException as e:save('check_failed',passed=False,error=repr(e));raise
