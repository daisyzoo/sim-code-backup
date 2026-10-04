"""Source provenance and structural fixtures; no new physical episode claim."""
from pathlib import Path
import sys,json,copy,hashlib,datetime,tempfile,os,collections
W=Path(__file__).resolve().parent;ROOT=W.parents[1];D=W/'front_contact_window_preparation_r2';sys.path[:0]=[str(W),str(ROOT)]
import front_contact_window_stage_source_binding_v2 as binding
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
used,bound=binding.verify_preparation();real=binding.verify_preparation
# Each generated fixture reuses the already hash-verified preparation map.
# Restore verifier before exit; no production files change.
binding.verify_preparation=lambda:(dict(used),dict(bound))
source=W/'front_loaded_z_quarter_physical_r2';cases=sorted(source.glob('case_*/provenance.json'));positive=[];negative=[]
def reject(name,call):
 try:call()
 except (AssertionError,KeyError,ValueError,FileNotFoundError):negative.append(name)
 else:raise AssertionError('Accepted negative '+name)
with tempfile.TemporaryDirectory(prefix='window-provenance-fixture-') as td:
 for p in cases:
  prov=json.loads(p.read_text())
  for enabled in [False,True]:
   args=dict(prov['args'],front_contact_window=enabled);binding.verify_settings(args);positive.append(dict(case=p.parent.name,window=enabled,settings_valid=True))
   fake=copy.deepcopy(prov);fake['args']=args;fake['fixture_only']=True
   old_prefix=str((W/'staged_front_loaded_z_quarter_v1').relative_to(ROOT))+'/';prefix=str(binding.S.relative_to(ROOT))+'/'
   files={n:h for n,h in fake['source_sha256'].items() if not n.startswith(old_prefix)}
   selected=dict(used)
   if not enabled:
    for name in binding.WINDOW_HELPERS:selected.pop(name)
   files.update({prefix+n:h for n,h in selected.items()});fake['source_sha256']=files
   case=Path(td)/(p.parent.name+str(enabled));case.mkdir()
   for n in files:
    dest=case/'source_snapshot'/n;dest.parent.mkdir(parents=True,exist_ok=True);os.link(ROOT/n,dest)
   path=case/'provenance.json';path.write_text(json.dumps(fake));binding.verify_trial_provenance(case)
   if enabled and p==cases[0]:
    def damaged(name,mutate):
     obj=copy.deepcopy(fake);mutate(obj);path.write_text(json.dumps(obj));reject(name,lambda:binding.verify_trial_provenance(case));path.write_text(json.dumps(fake))
    damaged('missing_window_helper',lambda obj:obj['source_sha256'].pop(prefix+binding.WINDOW_HELPERS[0]))
    damaged('wrong_window_hash',lambda obj:obj['source_sha256'].__setitem__(prefix+binding.WINDOW_HELPERS[0],'0'*64))
    damaged('wrong_collector_origin',lambda obj:obj['source_sha256'].__setitem__(old_prefix+'collect_paired_sorting.py',sha(W/'staged_front_loaded_z_quarter_v1/collect_paired_sorting.py')))
    for k,v in [('front_contact_window',1),('front_loaded_z_quarter',False),('front_initial_center_landing',False),('peak_load_bias_guard',False),('trace_substep_contacts',False),('expert_frontal_top_support_hysteresis_m',.001),('role','train'),('policy_port',8000),('idle',True),('waist_probe',True),('waist_pilot_contract','invalid')]:
     a=dict(args);a[k]=v;reject('invalid_'+k,lambda a=a:binding.verify_settings(a))
record=json.loads((D/'NATIVE_LOADED_BOUT_CHECK_V4.json').read_text())['bouts'][0]['records'][0]['candidate_interval'];record=copy.deepcopy(record);record['step']=1;record['action_step']=1;record['evidence']['observation'].update(action_step=1,after_action_step=0)
fixtures=[]
for enabled,selected,task in [(False,True,'nudge_mailer_to_bin'),(False,False,'push_box_to_bin'),(False,False,'wait_no_package'),(True,False,'push_box_to_bin'),(True,False,'wait_no_package'),(True,True,'nudge_mailer_to_bin')]:
 plan={} if task=='wait_no_package' else dict(front_route_selected=selected);meta={};log=None
 if enabled:
  if selected:plan['front_contact_window']=copy.deepcopy(binding.WINDOW_PLAN)
  rows=[copy.deepcopy(record)] if selected else []
  meta['front_contact_window']=dict(version='front_window_native_v4',enabled=True,selected_front=selected,recorded_intervals=len(rows),training_ready=False)
  log=dict(version='front_window_native_v4',enabled=True,selected_front=selected,rows=rows,executed_frames=2,training_ready=False)
 inp=dict(enabled=enabled,task=task,frames=2,meta=meta,plan=plan,log=log);result=binding.verify_window_structure(**inp);fixtures.append(dict(enabled=enabled,selected=selected,task=task,result=result))
 if enabled and selected:
  for name,mutate in [('missing_record',lambda x:x['log']['rows'].clear()),('duplicate_record',lambda x:x['log']['rows'].append(copy.deepcopy(record))),('wrong_action',lambda x:x['log']['rows'][0].update(action_step=2)),('wrong_previous',lambda x:x['log']['rows'][0]['evidence']['observation'].update(after_action_step=8)),('metadata_count',lambda x:x['meta']['front_contact_window'].update(recorded_intervals=0)),('wrong_selection',lambda x:x['log'].update(selected_front=False)),('wrong_tick_schedule',lambda x:x['log']['rows'][0]['evidence']['observation'].update(solver_substeps=23))]:
   modified=copy.deepcopy(inp);mutate(modified);reject(name,lambda:binding.verify_window_structure(**modified))
 if enabled and not selected:
  modified=copy.deepcopy(inp);modified['log']['rows']=[copy.deepcopy(record)];reject('unselected_rows_'+task,lambda:binding.verify_window_structure(**modified))
# Actual first native interval starts with None, independently reproduced.
lifecycle_path=D/'NATIVE_LIFECYCLE_CHECK_V2.json';lifecycle=json.loads(lifecycle_path.read_text());assert lifecycle['passed'] and lifecycle['actual_constructor_initial_phase_none']
for p,h in lifecycle['source_sha256'].items():assert sha(p)==h
first=dict(step=1,**copy.deepcopy(lifecycle['first_native_interval']))
meta=dict(front_contact_window=dict(version='front_window_native_v4',enabled=True,selected_front=True,recorded_intervals=1,training_ready=False));log=dict(version='front_window_native_v4',enabled=True,selected_front=True,rows=[first],executed_frames=2,training_ready=False);plan=dict(front_route_selected=True,front_contact_window=binding.WINDOW_PLAN)
inputs=dict(enabled=True,task='nudge_mailer_to_bin',frames=2,meta=meta,log=log,plan=plan);binding.verify_window_structure(**inputs);fixtures.append(dict(actual_first_none=True))
bad=copy.deepcopy(inputs);bad['frames']=3;bad['meta']['front_contact_window']['recorded_intervals']=2;bad['log']['executed_frames']=3;second=copy.deepcopy(first);second.update(step=2,action_step=2);bad['log']['rows'].append(second);reject('null_phase_after_first',lambda:binding.verify_window_structure(**bad))
for label,value in [('blank',''),('integer',1),('list',[])]:
 bad=copy.deepcopy(inputs);bad['log']['rows'][0]['observed_phase']=value;reject('invalid_observed_phase_'+label,lambda:binding.verify_window_structure(**bad))
bound[str(lifecycle_path)]=sha(lifecycle_path)
binding.verify_preparation=real
for p,h in bound.items():assert sha(p)==h
bound[str(Path(__file__))]=sha(__file__)
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,active_sources_enabled=len(used),settings_and_provenance_fixtures=positive,structural_fixtures=fixtures,negative_rejections=negative,source_sha256=bound,full_observation_binding_executed=False,full_stream_audit_ready=False,physical_launch_ready=False,training_ready=False)
with (D/'SOURCE_BINDING_CHECK_V2.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps({k:v for k,v in out.items() if k!='source_sha256'}))
