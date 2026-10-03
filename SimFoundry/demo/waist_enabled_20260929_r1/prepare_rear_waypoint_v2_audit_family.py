"""Adapt original complete audit family to explicit2mm/post-commit stage.
Keep original audit mathematics/thresholds; replace only independent rear state
reconstruction to incorporate verified next-cursor events, and add one complete
commit-log audit to every condition. Never launches physics or rewrites reports.
"""
from pathlib import Path
import ast,json,hashlib,datetime
W=Path(__file__).resolve().parent;D=W/'rear_waypoint_reconciliation_draft_r1';S=W/'staged_rear_waypoint_reconciliation';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
parent=json.loads((W/'FRONT_DRIVE_1MM_V2_AUDIT_FAMILY_PREPARATION.json').read_text());replacements=[('staged_front_drive_1mm','staged_rear_waypoint_reconciliation'),('front_drive_1mm_v2','rear_waypoint_v2'),('FRONT_DRIVE_1MM_V2','REAR_WAYPOINT_V2')]
def rename(s):
 for a,b in replacements:s=s.replace(a,b)
 return s
records=[]
for item in parent['adapters']:
 p=Path(item['path']);assert sha(p)==item['sha256'];s=rename(p.read_text());edits=[]
 def change(old,new):
  global s
  assert s.count(old)==1,(p.name,old[:100],s.count(old));s=s.replace(old,new);edits.append(dict(old=old,new=new))
 if p.name=='front_drive_1mm_v2_stage_source_binding.py':
  start=s.index('def verify_preparation():');end=s.index('def verify_trial_provenance(case):');old=s[start:end]
  change(old,"""def verify_preparation():
 from front_drive_1mm_v2_stage_source_binding import verify_preparation as verify_parent
 old_sources,parent_bound=verify_parent()
 prep=json.loads((S/'COLLECTOR_PREPARATION.json').read_text());parent=Path(prep['parent']);assert parent==W/'staged_front_drive_1mm'
 for p,h in prep['source_sha256'].items():assert sha(p)==h,p
 expected=prep['stage_sha256'];assert len(expected)==73 and set(expected)-set(old_sources)=={'reconcile_rear_waypoint.py','rear_post_commit_adapter.py'}
 assert set(old_sources)-set(expected)==set()
 for n,h in expected.items():assert sha(S/n)==h,n
 assert {n for n in old_sources if expected[n]!=old_sources[n]}=={'collect_paired_sorting.py'}
 restored=(S/'collect_paired_sorting.py').read_text()
 for e in reversed(prep['changes']):assert restored.count(e['new'])==1;restored=restored.replace(e['new'],e['old'])
 assert restored==(parent/'collect_paired_sorting.py').read_text()
 for a,b in [('reconcile_rear_waypoint.py','reconcile_rear_waypoint.py'),('post_commit_adapter.py','rear_post_commit_adapter.py')]:assert sha(W/'rear_waypoint_reconciliation_draft_r1'/a)==expected[b]
 proofs=[S/'COLLECTOR_WIRING_CHECK_V2.json',W/'rear_waypoint_reconciliation_draft_r1/COMPLETE_COMMIT_LOG_CHECK.json',W/'rear_waypoint_reconciliation_draft_r1/INDEPENDENT_POST_COMMIT_REPLAY_CHECK.json']
 for p in proofs:
  check=json.loads(p.read_text());assert check['passed']
  for name,h in check['source_sha256'].items():assert sha(name)==h,name
  parent_bound[str(p)]=sha(p)
 parent_bound[str(S/'COLLECTOR_PREPARATION.json')]=sha(S/'COLLECTOR_PREPARATION.json')
 return expected,parent_bound

""")
  change("REPORTS=['CLI_PARAMETER_CHECK.json']","REPORTS=['COLLECTOR_WIRING_CHECK_V2.json']")
  change("S / 'CLI_PARAMETER_CHECK.json'","S / 'COLLECTOR_WIRING_CHECK_V2.json'")
  change("W/'front_drive_1mm_preparation_r2/TRIAL_PROFILE.json'","W/'staged_closed_peak_trial/TRIAL_PROFILE.json'")
  change("for n in ['front_corridor_midpoint_replan','front_loaded_z_priority','front_initial_center_landing','terminal_release_margin','edge_clearance_intersection']", "for n in ['rear_waypoint_reconciliation','front_corridor_midpoint_replan','front_loaded_z_priority','front_initial_center_landing','terminal_release_margin','edge_clearance_intersection']")
  change("assert args['front_corridor_midpoint_replan'] is True","assert args['front_corridor_midpoint_replan'] is True\n assert args['rear_waypoint_reconciliation'] is True and args['front_cop_drive_step_m']==.002")
 if p.name=='audit_front_drive_1mm_v2_stage_rear_xy.py':
  old=s[s.index('def reconstruct('):s.index('\n\ndef main():')]
  new=(D/'independent_rear_state_replay.py').read_text();new=new[new.index('def reconstruct('):].rstrip()
  change(old,new)
  change("packets={r['after_action_step']:r for r in json.loads((ep/'solved_contact_forces.json').read_text())['rows']};report=reconstruct(fr['rows'],plan,xyz,quat,packets,key,handover)","packets={r['after_action_step']:r for r in json.loads((ep/'solved_contact_forces.json').read_text())['rows']}\n        from audit_rear_waypoint_v2_commit import inspect_episode\n        commit=inspect_episode(ep);verified=commit['independently_verified_events']['verified_post_commit']\n        report=reconstruct(fr['rows'],plan,xyz,quat,packets,key,handover,verified_post_commit=verified)\n        report['commit_source_sha256']=commit['source_sha256']")
 if p.name=='front_drive_1mm_v2_stage_run_contract.py':
  change("return ['audit_rear_waypoint_v2_execution.py']+", "return ['audit_rear_waypoint_v2_execution.py','audit_rear_waypoint_v2_commit.py']+")
  old="ADDITIONAL=['audit_rear_waypoint_v2_stage_region_continuity.py'"
  change(old,"REPORTS['audit_rear_waypoint_v2_commit.py']=('REAR_WAYPOINT_V2_COMMIT_AUDIT.json',('passed',))\n"+old)
 ast.parse(s);rev=s
 for e in reversed(edits):assert rev.count(e['new'])==1;rev=rev.replace(e['new'],e['old'])
 assert rev==rename(p.read_text())
 dest=W/rename(p.name);assert not dest.exists()
 with dest.open('x') as f:f.write(s)
 records.append(dict(parent=str(p),parent_sha256=sha(p),path=str(dest),sha256=sha(dest),edits=edits,exact_declared_diff=True))
proofs=[D/'COMPLETE_COMMIT_LOG_CHECK.json',D/'INDEPENDENT_POST_COMMIT_REPLAY_CHECK.json',S/'COLLECTOR_WIRING_CHECK_V2.json'];sources=[Path(__file__),W/'FRONT_DRIVE_1MM_V2_AUDIT_FAMILY_PREPARATION.json',W/'audit_rear_waypoint_v2_commit.py',D/'independent_commit_log_contract.py',D/'independent_post_commit_audit.py',D/'independent_rear_state_replay.py',*proofs]
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,adapters=records,global_replacements=replacements,source_sha256={str(p):sha(p) for p in sources},syntax_passed=True,configuration_checks_pending=True,expected_full_invocations=214,parent_invocations=204,physics_started=False,training_ready=False)
with (W/'REAR_WAYPOINT_V2_AUDIT_FAMILY_PREPARATION.json').open('x') as f:json.dump(out,f,indent=2)
print(dict(modules=len(records),additional_commit_auditor=True,expected_full_invocations=214))
