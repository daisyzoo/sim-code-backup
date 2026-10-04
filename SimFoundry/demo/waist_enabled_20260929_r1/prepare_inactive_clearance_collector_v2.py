"""Prepare isolated default-off inactive-clearance collector; no physical launch.
Parent77 sources retained except explicit collector/runtime dispatch changes.
Original final command branch remains byte-identical; new preparation proposals
are mapped to its existing field contract without changing commands or checks.
"""
from pathlib import Path
import ast,json,hashlib,datetime
W=Path(__file__).resolve().parent;P=W/'staged_front_recontact_headroom';S=W/'staged_front_inactive_clearance';D=W/'inactive_hand_headroom_draft_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert not S.exists()
for name in ['LIFECYCLE_CHECK.json','FULL_HYPOTHESIS_CHECK.json']:
 d=json.loads((D/name).read_text());assert d['passed']
 for p,h in d['source_sha256'].items():assert sha(p)==h,p
parent=json.loads((P/'COLLECTOR_PREPARATION.json').read_text());hashes=parent['stage_sha256'];assert len(hashes)==77
spec=dict(version='front_inactive_clearance_v1',enabled=True,task='left_front_bag_recovery',original_measured_gate_m=.84,recovery_measured_entry_m=.841,preparation_nominal_predicted_height_m=.8415,original_recovery_nominal_predicted_height_m=.8405,shared_command_budget=240,preparation_commits_path=True,measured_only_recovery_entry=True,unloaded_only=True,training_ready=False)
edits={}
def replace(name,old,new):
 text=texts[name];assert text.count(old)==1,(name,old[:100]);texts[name]=text.replace(old,new);edits.setdefault(name,[]).append(dict(old=old,new=new))
texts={n:(P/n).read_text() for n in hashes}
for n,h in hashes.items():assert sha(P/n)==h,n
n='front_recontact_center_runtime.py'
replace(n,'from recontact_scene import RecontactScene','from recontact_scene import RecontactScene\nfrom inactive_clearance_lifecycle import InactiveClearanceLifecycle')
replace(n,'*, enabled=False):','*, enabled=False, inactive_clearance=False):')
replace(n,'        self.enabled=enabled;self.guard=guard;self.side=side',"        if type(inactive_clearance) is not bool or (inactive_clearance and not enabled):raise ValueError('Explicit enabled recovery required for clearance preparation')\n        self.inactive_clearance=inactive_clearance\n        self.enabled=enabled;self.guard=guard;self.side=side")
replace(n,'            event=dict(event)',"            event=dict(event)\n            if event.get('phase')=='inactive_clearance_preparation':\n                p=dict(event['proposal'])\n                if not self.inactive_clearance or event['kind']!='command' or not p['applied']:raise ValueError('Undeclared clearance preparation')\n                # Existing final joint branch checks these exact aliases.\n                p.update(candidate_command=p['command'],command_check=p['original_command_check'],nominal_scene=p['nominal'],predicted_scene=p['predicted'])\n                event['proposal']=p")
replace(n,'self.lifecycle=FrontRecontactCenterLifecycle(enabled=True,recontact_index=counter)','self.lifecycle=(InactiveClearanceLifecycle if self.inactive_clearance else FrontRecontactCenterLifecycle)(enabled=True,recontact_index=counter)')
n='collect_paired_sorting.py';line=next(x for x in texts[n].splitlines() if x.startswith("parser.add_argument('--front-recontact-center-landing'"))
replace(n,line,line+"\nparser.add_argument('--front-recontact-inactive-clearance',action='store_true',help='Default-off measured unloaded inactive-arm clearance preparation; shares original recovery240-command budget.')")
line=next(x for x in texts[n].splitlines() if x.startswith('if args.front_recontact_center_landing and not '))
replace(n,line,"if args.front_recontact_inactive_clearance and not args.front_recontact_center_landing:\n    parser.error('Inactive clearance requires original front recontact center landing')\n"+line)
old="front_recontact_runtime=FrontRecontactCenterRuntime(clearance_guard,side,edge_size,obstacle_size,parameters['tasks'][task_id]['decay'],enabled=True)"
replace(n,old,old[:-1]+',inactive_clearance=args.front_recontact_inactive_clearance)')
line=next(x for x in texts[n].splitlines() if "frontal_plan['front_recontact_center_landing']=dict(" in x)
replace(n,line,line+"\n                            if args.front_recontact_inactive_clearance:frontal_plan['front_inactive_clearance']="+repr(spec))
line="        episode.collect_meta['front_recontact_center_landing']=True"
replace(n,line,line+"\n        if args.front_recontact_inactive_clearance:episode.collect_meta['front_inactive_clearance']="+repr(spec))
line=next(x for x in texts[n].splitlines() if "paths.extend(STAGE/name for name in ['front_recontact_center_tracking.py'" in x)
replace(n,line,line+"\n        paths.extend(STAGE/name for name in ['inactive_clearance_lifecycle.py','inactive_clearance_proposal.py'])")
S.mkdir()
for name,text in texts.items():
 if name.endswith('.py'):ast.parse(text)
 with (S/name).open('x') as f:f.write(text)
for name in ['inactive_clearance_lifecycle.py','inactive_clearance_proposal.py']:
 with (S/name).open('x') as f:f.write((D/name).read_text())
for name,ee in edits.items():
 restored=(S/name).read_text()
 for e in reversed(ee):assert restored.count(e['new'])==1;restored=restored.replace(e['new'],e['old'])
 assert restored==(P/name).read_text()
newnames=list(hashes)+['inactive_clearance_lifecycle.py','inactive_clearance_proposal.py'];changed=[n for n in hashes if sha(S/n)!=hashes[n]];assert set(changed)=={'collect_paired_sorting.py','front_recontact_center_runtime.py'}
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,parent=str(P),parent_manifest_sha256=sha(P/'COLLECTOR_PREPARATION.json'),stage_sha256={n:sha(S/n) for n in newnames},changed_parent_files=changed,unchanged_parent_files=sorted(set(hashes)-set(changed)),edits=edits,inactive_clearance=spec,source_sha256={str(p):sha(p) for p in [Path(__file__),P/'COLLECTOR_PREPARATION.json',D/'LIFECYCLE_CHECK.json',D/'FULL_HYPOTHESIS_CHECK.json',D/'inactive_clearance_lifecycle.py',D/'inactive_clearance_proposal.py']},collector_integrated=True,independent_native_audit_ready=False,simulation_started=False,training_ready=False)
with (S/'COLLECTOR_PREPARATION.json').open('x') as f:json.dump(out,f,indent=2)
print(dict(stage=str(S),sources=len(newnames),changed=changed,unchanged=len(hashes)-len(changed),physical_started=False))
