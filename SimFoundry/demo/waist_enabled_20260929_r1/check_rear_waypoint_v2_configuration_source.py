"""Full214 inventory, exact config/source binding and explicit70-frame wait fixture.
Only fixture metadata and declared provenance change. Original physical arrays
are identical; fixture is removed and cannot establish new physical execution.
"""
from pathlib import Path
import ast,copy,datetime,hashlib,importlib,json,os,shutil,sys,tempfile
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];P=W/'rear_waypoint_preparation_r1';R=W/'front_corridor_midpoint_physical_r1';S=W/'staged_rear_waypoint_reconciliation';sys.path[:0]=[str(W),str(ROOT)]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={};negative=[]
def reject(label,fn):
 try:fn()
 except (AssertionError,KeyError,ValueError):negative.append(label)
 else:raise AssertionError(('unexpected acceptance',label))
manifest=json.loads((W/'REAR_WAYPOINT_V2_AUDIT_FAMILY_PREPARATION.json').read_text())
def renamed(s):
 for a,b in manifest['global_replacements']:s=s.replace(a,b)
 return s
for row in manifest['adapters']:
 p=Path(row['path']);parent=Path(row['parent']);assert sha(p)==row['sha256'] and sha(parent)==row['parent_sha256'];s=p.read_text()
 for e in reversed(row['edits']):s=s.replace(e['new'],e['old'])
 assert s==renamed(parent.read_text());sources[str(p)]=sha(p);sources[str(parent)]=sha(parent)
from prepare_closed_peak_trial import parser_namespace
from simfoundry.data.waist_pilot_protocol import semantic_settings
parent_protocol=R/'PROTOCOL.json';old=json.loads(parent_protocol.read_text())['plan'];profile=json.loads((W/'staged_closed_peak_trial/TRIAL_PROFILE.json').read_text());commands=[]
from rear_waypoint_v2_stage_run_contract import primary,controls,ADDITIONAL,REPORTS
from front_drive_1mm_v2_stage_run_contract import primary as primary_old,controls as controls_old,ADDITIONAL as ADD_OLD
inventory=[]
for orig in old['commands']:
 args=list(orig['args']);assert args[args.index('--front-cop-drive-step-m')+1]=='.002';args[args.index('--out-dir')+1]=str(P/f"case_{orig['layout_id']}");args+=['--rear-waypoint-reconciliation'];c=dict(orig,args=args);commands.append(c)
 parsed,_=parser_namespace(S/'collect_paired_sorting.py',args,full=True);settings=semantic_settings(parsed)
 for name in ['rear_waypoint_reconciliation','front_corridor_midpoint_replan','front_loaded_z_priority','front_initial_center_landing','terminal_release_margin','edge_clearance_intersection']:assert settings.pop(name) is True
 assert settings==profile['prelaunch_settings']
 for task in c['tasks']:
  ep=R/f"case_{c['layout_id']}"/f"layout_{c['layout_id']}_{task}";front={} if c['wait'] else json.loads((ep/'frontal_bypass.json').read_text())['plan']
  new=primary(c['wait'])+['audit_rear_waypoint_v2_stage_contacts.py','audit_rear_waypoint_v2_stage_pressure.py']+(controls(front)+ADDITIONAL if not c['wait'] else [])+['audit_rear_waypoint_v2_stage_release.py'];new=list(dict.fromkeys(new))
  prev=primary_old(c['wait'])+['audit_front_drive_1mm_v2_stage_contacts.py','audit_front_drive_1mm_v2_stage_pressure.py']+(controls_old(front)+ADD_OLD if not c['wait'] else [])+['audit_front_drive_1mm_v2_stage_release.py'];prev=list(dict.fromkeys(prev));expected=[renamed(n) for n in prev];expected.insert(1,'audit_rear_waypoint_v2_commit.py');assert new==expected;assert all(n in REPORTS for n in new);inventory.append(dict(episode=ep.name,scripts=new))
assert len(inventory)==10 and sum(len(r['scripts']) for r in inventory)==214
imported=[];cli=[]
for row in manifest['adapters']:
 p=Path(row['path']);tree=ast.parse(p.read_text());top=[n for n in tree.body if not isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)) and not (isinstance(n,ast.If) and '__name__' in ast.unparse(n.test))]
 if any(isinstance(n,ast.Attribute) and n.attr in ('argv','parse_args','parse_known_args') for node in top for n in ast.walk(node)):cli.append(p.name);continue
 importlib.import_module(p.stem);imported.append(p.name)
from rear_waypoint_v2_stage_source_binding import verify_trial_provenance,verify_observation_binding
from audit_rear_waypoint_v2_execution import inspect
from audit_rear_waypoint_v2_commit import inspect_episode
for c in commands:reject('original_source_'+str(c['layout_id']),lambda c=c:verify_trial_provenance(R/f"case_{c['layout_id']}"))
original=R/'case_841010';name='layout_841010_wait_no_package';original_raw=sha(original/name/'raw.npz')
with tempfile.TemporaryDirectory(prefix='rear_cursor_declared_wait_') as tmp:
 case=Path(tmp)/original.name;shutil.copytree(original,case,copy_function=os.link);ep=case/name;provpath=case/'provenance.json';prov=json.loads(provpath.read_text());provpath.unlink();prov['args']['rear_waypoint_reconciliation']=True
 oldstage=W/'staged_front_corridor_midpoint_integrated';oldprefix=str(oldstage.relative_to(ROOT))+'/';newprefix=str(S.relative_to(ROOT))+'/'
 prov['source_sha256']={k:v for k,v in prov['source_sha256'].items() if not k.startswith(oldprefix)}
 prepared=json.loads((S/'COLLECTOR_PREPARATION.json').read_text())
 for fname,h in prepared['stage_sha256'].items():
  key=newprefix+fname;dest=case/'source_snapshot'/key;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(S/fname,dest);assert sha(dest)==h;prov['source_sha256'][key]=h
 provpath.write_text(json.dumps(prov));runtimepath=case/'SUBSTEP_RUNTIME_BINDING.json';runtime=json.loads(runtimepath.read_text());runtimepath.unlink();runtime['source_files']={str(S/Path(k).name) if Path(k).parent==oldstage else k:v for k,v in runtime['source_files'].items()};runtimepath.write_text(json.dumps(runtime))
 (case/'SOURCE_CONTRACT_FIXTURE.json').write_text(json.dumps(dict(fixture_only=True,physical_candidate=False,scope=__doc__)))
 with np.load(ep/'raw.npz',allow_pickle=False) as z:arrays={k:z[k].copy() for k in z.files}
 meta=json.loads(str(arrays['collect_meta']));meta.update(rear_waypoint_reconciliation=True,rear_waypoint_reconciliation_applied_frames=0);arrays['collect_meta']=np.array(json.dumps(meta));(ep/'raw.npz').unlink();np.savez_compressed(ep/'raw.npz',**arrays)
 with np.load(original/name/'raw.npz',allow_pickle=False) as z:
  for key,value in arrays.items():
   if key!='collect_meta':assert np.array_equal(z[key],value),key
 clear=json.loads((ep/'self_clearance.json').read_text());steps=[r['step'] for r in clear['rows'] if r['phase']=='post' and r['accepted']];assert steps==list(range(70));logs=[dict(step=t,version='rear_box_post_commit_adapter_draft_v1',applied=False,current_action_changed=False,training_ready=False,reason='first_zero_frame_preserved' if t==0 else 'not_rear_box') for t in steps]
 (ep/'rear_waypoint_reconciliation.json').write_text(json.dumps(dict(rows=logs,training_ready=False)))
 verify_trial_provenance(case);binding=verify_observation_binding(ep);assert binding['passed'];commit=inspect_episode(ep);assert commit['passed'] and not commit['selected'] and commit['complete_event_rows']==70
 fixture=inspect(ep,allow_source_fixture=True);assert fixture['passed'] and fixture['fixture_only'] and not fixture['physical_execution_evidence'] and fixture['frames']==70
 reject('execution_rejects_fixture_by_default',lambda:inspect(ep))
 for key,value in [('rear_waypoint_reconciliation',False),('rear_waypoint_reconciliation',1),('front_cop_drive_step_m',.001),('front_cop_drive_step_m',.0015),('steps',1199),('push_assist',True),('expert_frontal_top_load_n',6.)]:
  bad=copy.deepcopy(prov);bad['args'][key]=value;provpath.write_text(json.dumps(bad));reject('changed_'+key+'_'+str(value),lambda:verify_trial_provenance(case))
 provpath.write_text(json.dumps(prov));assert sha(original/name/'raw.npz')==original_raw
P.mkdir(exist_ok=False)
plan=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='prepared_not_launched',collector=str(S/'collect_paired_sorting.py'),collector_sha256=sha(S/'collect_paired_sorting.py'),parent_protocol=str(parent_protocol),parent_protocol_sha256=sha(parent_protocol),parent_run=str(R),groups=old['groups'],commands=commands,comparison='post_commit_rear_cursor_against_original2mm_midpoint_parent',scope='Same full8push2wait with original2mm front drive. Only new post-successful-action rear-box next-Y-cursor reconciliation; all original guards remain. This does not fix front bag route geometry.',expected_audit_invocations=214,simulation_started=False,training_ready=False)
with (P/'PLAN.json').open('x') as f:json.dump(plan,f,indent=2)
for p in [Path(__file__),P/'PLAN.json',W/'REAR_WAYPOINT_V2_AUDIT_FAMILY_PREPARATION.json',W/'audit_rear_waypoint_v2_commit.py',original/'provenance.json',original/name/'raw.npz']:sources[str(p)]=sha(p)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,exact_module_diffs=len(manifest['adapters']),configuration_count=6,condition_count=10,expected_audits=214,original_204_preserved=True,inventory=inventory,imported=imported,cli_static_only=cli,negative=negative,wait_fixture_frames=70,original_physical_arrays_identical=True,fixture_metadata_changed_only=True,fixture_removed=True,source_sha256=sources,new_physics=False,training_ready=False)
with (P/'CONFIGURATION_SOURCE_AUDIT_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(dict(passed=True,configurations=6,conditions=10,audits=214,imported=len(imported),cli_static=len(cli),negative_cases=len(negative),wait_fixture_frames=70))
