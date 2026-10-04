"""Isolated right-box recovery collector on frozen headroom parent, default off.
Only collector dispatch/metadata changes; parent left-bag behavior unchanged.
No inactive-clearance preparation or finite-material preload is combined.
"""
from pathlib import Path
import ast,json,hashlib,datetime
W=Path(__file__).resolve().parent;P=W/'staged_front_recontact_headroom';D=W/'front_box_recenter_draft_r1';S=W/'staged_front_box_recenter_v3';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert not S.exists();check=json.loads((D/'ALL_ELIGIBLE_LIFECYCLE_PROBE.json').read_text());assert check['passed'] and len(check['records'])==12 and all(r['outcome']=='handover' for r in check['records'])
for p,h in check['source_sha256'].items():assert sha(p)==h,p
parent=json.loads((P/'COLLECTOR_PREPARATION.json').read_text());hashes=parent['stage_sha256'];assert len(hashes)==77
for n,h in hashes.items():assert sha(P/n)==h,n
texts={n:(P/n).read_text() for n in hashes};edits=[];n='collect_paired_sorting.py'
def replace(a,b):
 assert texts[n].count(a)==1,a[:100];texts[n]=texts[n].replace(a,b);edits.append(dict(old=a,new=b))
spec=dict(version='front_box_recenter_v1',enabled=True,side='right',real_positive_recontact_counter=True,maximum_ticks=240,actual_ready_frames=3,center_xy_m=.002,precontact_height_m=[.006,.007],measured_height_m=[.004,.010],alignment_abs_min=.8,entry_inactive_height_m=.841,nominal_predicted_inactive_height_m=.8405,original_measured_inactive_height_m=.84,unloaded_only=True,measured_capture_only=True,predicted_capture_discarded=True,training_ready=False)
line=next(x for x in texts[n].splitlines() if x.startswith("parser.add_argument('--front-recontact-center-landing'"));replace(line,line+"\nparser.add_argument('--front-box-recenter',action='store_true',help='Default-off right-box unloaded recovery centering with real positive counters and measured capture.')")
line=next(x for x in texts[n].splitlines() if x.startswith('if args.front_recontact_center_landing and not '));replace(line,"if args.front_box_recenter and not args.front_recontact_center_landing:\n    parser.error('Right box recovery requires original front recovery profile')\n"+line)
line=next(x for x in texts[n].splitlines() if "frontal_plan['front_recontact_center_landing']=dict(" in x)
replace(line,line+"\n                        if args.front_box_recenter and side=='right':\n                            from front_box_recenter_runtime import FrontRecontactCenterRuntime as BoxRecenterRuntime\n                            front_recontact_runtime=BoxRecenterRuntime(clearance_guard,side,edge_size,obstacle_size,parameters['tasks'][task_id]['decay'],enabled=True)\n                            frontal_plan['front_box_recenter']="+repr(spec))
line="        episode.collect_meta['front_recontact_center_landing']=True";replace(line,line+"\n        if args.front_box_recenter:episode.collect_meta['front_box_recenter']="+repr(spec))
newnames=['front_box_recenter_'+s+'.py' for s in ['lifecycle_static','selection','lifecycle','runtime']]
line=next(x for x in texts[n].splitlines() if "paths.extend(STAGE/name for name in ['front_recontact_center_tracking.py'" in x);replace(line,line+'\n        paths.extend(STAGE/name for name in '+repr(newnames)+')')
replace("selected=bool(frontal_plan.get('front_route_selected') and side=='left'),step=step,current=center_q,","selected=bool(frontal_plan.get('front_route_selected') and side==front_recontact_runtime.side),step=step,current=center_q,")
coord_name='waist_coordination_clearance.py'
coord_old="state.side!='left'"
coord_new="(context['scene']['side']!=state.side or not (state.side=='left' or (state.side=='right' and front_recontact_override.get('front_box_recenter_version')=='front_box_recenter_v1')))"
assert texts[coord_name].count(coord_old)==1
texts[coord_name]=texts[coord_name].replace(coord_old,coord_new)
runtime_old='            event=dict(event)'
runtime_new="            event=dict(event)\n            event['front_box_recenter_version']='front_box_recenter_v1'"
S.mkdir()
for name,text in texts.items():
 if name.endswith('.py'):ast.parse(text)
 with (S/name).open('x') as f:f.write(text)
for name in newnames:
 text=(D/name).read_text()
 if name=='front_box_recenter_runtime.py':
  assert text.count(runtime_old)==1;text=text.replace(runtime_old,runtime_new)
 with (S/name).open('x') as f:f.write(text)
restored=(S/n).read_text()
for e in reversed(edits):assert restored.count(e['new'])==1;restored=restored.replace(e['new'],e['old'])
assert restored==(P/n).read_text();unchanged=[name for name in hashes if sha(S/name)==hashes[name]];assert len(unchanged)==75
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,parent=str(P),parent_manifest_sha256=sha(P/'COLLECTOR_PREPARATION.json'),stage_sha256={name:sha(S/name) for name in list(hashes)+newnames},edits={n:edits,coord_name:[dict(old=coord_old,new=coord_new)]},new_source_edits={'front_box_recenter_runtime.py':[dict(old=runtime_old,new=runtime_new)]},box_recenter=spec,changed_parent_files=[n,coord_name],unchanged_parent_files=unchanged,source_sha256={str(p):sha(p) for p in [Path(__file__),P/'COLLECTOR_PREPARATION.json',D/'ALL_ELIGIBLE_LIFECYCLE_PROBE.json',D/'LIFECYCLE_PREPARATION.json',*[D/name for name in newnames]]},collector_integrated=True,independent_native_audit_ready=False,simulation_started=False,training_ready=False)
with (S/'COLLECTOR_PREPARATION.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(sources=len(report['stage_sha256']),unchanged_parent=75,changed_parent=report['changed_parent_files'],physical_started=False)))
