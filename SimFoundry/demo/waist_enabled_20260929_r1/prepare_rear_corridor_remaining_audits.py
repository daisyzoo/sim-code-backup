"""Prepare full original inventory plus explicit recovery branch adapters.
Reversible changes preserve raw action history, original gates and source binding.
Generation is not runtime verification; launch remains disabled until checked.
"""
from pathlib import Path
import re,ast,json,hashlib,datetime
W=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
initial=['normal_live','terminal_inputs','initial_near_half','region_continuity','region_bounds','rear_xy','pose_height','micro_clearance','contacts','pressure','loaded_parent','pose_loaded_execution','source_contract']
fixed={'audit_closed_peak_trial_pose_live':'audit_rear_corridor_stage_pose_live','audit_closed_peak_trial_pose_task_optimality':'audit_rear_corridor_stage_pose_task_optimality','audit_closed_peak_trial_pose_self_clearance':'audit_rear_corridor_stage_pose_self_clearance','closed_peak_trial_source_binding':'rear_corridor_stage_source_binding','audit_front_diagonal_entry_live':'audit_rear_corridor_diagonal_live','audit_terminal_hold_live':'audit_rear_corridor_terminal_hold_live'}
names=set();queue=['audit_closed_peak_trial_'+s for s in initial]+['closed_peak_trial_audit_context']
while queue:
 n=queue.pop()
 if n in names:continue
 names.add(n);text=(W/(n+'.py')).read_text()
 for ref in set(re.findall(r'(?:audit_closed_peak_trial_[a-z_]+|closed_peak_trial_audit_context|closed_peak_trial_source_binding)',text)):
  if ref not in fixed and ref!='audit_closed_peak_trial_refinement' and ref not in names:queue.append(ref)
mapping={n:n.replace('audit_closed_peak_trial_','audit_rear_corridor_stage_').replace('closed_peak_trial_audit_context','rear_corridor_stage_audit_context') for n in names};mapping.update(fixed)
parents={mapping[n]:n for n in names};parents.update(rear_corridor_stage_run_contract='closed_peak_trial_run_contract',audit_rear_corridor_terminal_hold_live='audit_terminal_hold_live',audit_rear_corridor_diagonal_live='audit_front_diagonal_entry_live')
outputs={};manifest=[]
for dest,parent in sorted(parents.items()):
 original=(W/(parent+'.py')).read_text();text=original;edits=[]
 def replace(old,new,required=False):
  global text
  count=text.count(old)
  if required:assert count,(dest,old)
  if count:
   assert new not in text,(dest,'ambiguous inverse',new);text=text.replace(old,new);edits.append(dict(old=old,new=new,count=count))
 for old,new in sorted(mapping.items(),key=lambda x:-len(x[0])):replace(old,new)
 replace('verify_closed_peak_trial_source','verify_rear_corridor_stage_source')
 replace('staged_closed_peak_trial','staged_rear_corridor_recovery_guarded')
 replace("['role']=='pilot'","['role']=='diagnostic'")
 for old in sorted(set(re.findall(r'CLOSED_PEAK_TRIAL_[A-Z_]+',text))):replace(old,old.replace('CLOSED_PEAK_TRIAL_','REAR_CORRIDOR_STAGE_'))
 replace('FRONT_DIAGONAL_ENTRY_LIVE_AUDIT.json','REAR_CORRIDOR_DIAGONAL_LIVE_AUDIT.json')
 replace('TERMINAL_HOLD_LIVE_AUDIT.json','REAR_CORRIDOR_TERMINAL_HOLD_LIVE_AUDIT.json')
 if parent=='audit_closed_peak_trial_rear_xy':
  # Use the separately tested exact parent math + actual state reconstruction.
  prefix=text.split('def main():')[0]
  replace(prefix,"from pathlib import Path\nimport ast,json,hashlib,sys,subprocess\nimport numpy as np\nfrom rear_corridor_xy_reconstruction import reconstruct\n\n",True)
  replace('    ep=Path(sys.argv[1]).resolve();',"    ep=Path(sys.argv[1]).resolve();",False) if False else None
  # At first reconstruction bind full native record map. Original main scope has w.
  replace("packets={r['after_action_step']:r for r in json.loads((ep/'solved_contact_forces.json').read_text())['rows']};report=reconstruct(fr['rows'],plan,xyz,quat,packets,key,handover)","packets={r['after_action_step']:r for r in json.loads((ep/'solved_contact_forces.json').read_text())['rows']}\n        from rear_corridor_audit_inputs import verify_inputs\n        recovery=verify_inputs(ep,w.parents[1],w/'staged_rear_corridor_recovery_guarded')\n        report=reconstruct(fr['rows'],plan,xyz,quat,packets,key,handover,recovery.overrides);recovery.assert_unchanged()",True)
 if parent=='audit_closed_peak_trial_pose_height':
  prefix=text.split('def audit(ep):')[0]
  replace(prefix,"from pathlib import Path\nimport sys,json,hashlib\nfrom rear_corridor_height_reconstruction import verify_rows\nsha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()\n\n",True)
  replace(" result=verify_rows(fr['rows'],control,fr['plan'],True,events)"," from rear_corridor_audit_inputs import verify_inputs\n w=Path(__file__).resolve().parent;recovery=verify_inputs(ep,w.parents[1],w/'staged_rear_corridor_recovery_guarded')\n result=verify_rows(fr['rows'],control,fr['plan'],True,events,recovery.overrides);recovery.assert_unchanged()",True)
 if parent=='audit_closed_peak_trial_pose_loaded_execution':
  replace('from audit_rear_corridor_stage_rear_xy import reconstruct','from rear_corridor_xy_reconstruction import reconstruct',True)
  replace(' verify_rear_corridor_stage_source(ep)'," verify_rear_corridor_stage_source(ep)\n from rear_corridor_audit_inputs import verify_inputs\n recovery=verify_inputs(ep,repo,expected_collector.parent)",True)
  replace("reconstruct(fr['rows'],plan,xyz,quat,packets,key,handover)","reconstruct(fr['rows'],plan,xyz,quat,packets,key,handover,recovery.overrides)",True)
  replace("  t=f['step'];c=cs[t];", "  t=f['step'];f=recovery.parent_row(t,f);parent_expert=recovery.parent_expert(t,ex[t]);edge_actual=np.asarray(recovery.parent_command(t,u[t]),dtype=np.float32);c=cs[t];",True)
  replace("near(trace['final_upper_command'],u[t],0)","near(trace['final_upper_command'],edge_actual,0)",True)
  replace('else:assert trace is None;parent=u[t]','else:assert trace is None;parent=edge_actual',True)
  replace('loaded_parent(c,f,ex[t],q[t],u[t-1],parent,side,solver)','loaded_parent(c,f,parent_expert,q[t],u[t-1],parent,side,solver)',True)
  replace('near(u[t],parent,0)','near(edge_actual,parent,0)',True)
  replace('verify_refinement(trace,parent,u[t],u[t-1],','verify_refinement(trace,parent,edge_actual,u[t-1],',True)
  replace(' return dict(passed=True,selected=selected,nonlinear_task_execution=', ' recovery.assert_unchanged()\n return dict(passed=True,recovery_overrides=len(recovery.overrides),selected=selected,nonlinear_task_execution=',True)
 if parent in ['audit_closed_peak_trial_terminal_inputs','audit_terminal_hold_live']:
  token='records=[];errors=[]' if parent.endswith('terminal_inputs') else "key='box' if 'push_box' in p.name else 'mailer'"
  variable='ctrl' if parent.endswith('terminal_inputs') else 'control'
  insertion="from rear_corridor_audit_inputs import verify_inputs\nw=Path(__file__).resolve().parent;recovery=verify_inputs(p,w.parents[1],w/'staged_rear_corridor_recovery_guarded')\n"+variable+'={t:recovery.parent_expert(t,x) for t,x in '+variable+'.items()}\n'
  replace(token,insertion+token,True)
  output="(p/'REAR_CORRIDOR_STAGE_TERMINAL_INPUT_AUDIT.json')" if parent.endswith('terminal_inputs') else "(p/'REAR_CORRIDOR_TERMINAL_HOLD_LIVE_AUDIT.json')"
  replace(output,'recovery.assert_unchanged()\n'+output,True)
 if parent=='audit_closed_peak_trial_region_continuity':
  replace('from box_inward_step_contract import declared_step',"from rear_corridor_audit_inputs import verify_inputs\nrecovery=verify_inputs(p,w.parents[1],w/'staged_rear_corridor_recovery_guarded')\nfrom box_inward_step_contract import declared_step",True)
  replace('   prev=rows.get(t-1)', '   row=recovery.parent_row(t,row);prev=rows.get(t-1)',True)
  replace('report=dict(passed=', 'recovery.assert_unchanged()\nreport=dict(passed=',True)
 if parent=='audit_closed_peak_trial_pressure':
  replace('    out=verify_stream(p,fr,loads,frames=n,wait=wait)',"    from rear_corridor_audit_inputs import verify_inputs\n    w=Path(__file__).resolve().parent;recovery=verify_inputs(ep,w.parents[1],w/'staged_rear_corridor_recovery_guarded')\n    out=verify_stream(p,fr,loads,frames=n,wait=wait)\n    unloads={t for t,r in recovery.overrides.items() if r['kind']=='unload'}\n    if not wait:\n        resets=out['original_zero_resets_after_update']\n        out['verified_recovery_zero_resets_after_update']=[t for t in resets if t in unloads]\n        out['original_zero_resets_after_update']=[t for t in resets if t not in unloads]\n    out['verified_recovery_unload_steps']=sorted(unloads)\n    recovery.assert_unchanged()",True)
 ast.parse(text);recovered=text
 for e in reversed(edits):assert recovered.count(e['new'])==e['count'],(dest,e['new']);recovered=recovered.replace(e['new'],e['old'])
 assert recovered==original
 p=W/(dest+'.py');assert not p.exists(),p;outputs[p]=text;manifest.append(dict(parent=parent+'.py',parent_sha256=sha(W/(parent+'.py')),new=p.name,new_sha256=hashlib.sha256(text.encode()).hexdigest(),edits=edits,reverse_matches=True))
for p,text in outputs.items():
 with p.open('x') as f:f.write(text)
with (W/'REAR_CORRIDOR_REMAINING_AUDITS_PREPARATION.json').open('x') as f:json.dump(dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=manifest,preparer_sha256=sha(__file__),scope=__doc__,runtime_checks_pending=True,physical_launch_allowed=False,training_ready=False),f,indent=2)
print('prepared',len(outputs),[p.name for p in outputs])
