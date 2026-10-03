"""Check unchanged collector1mm config, original204 inventory and explicit wait fixture.
No push dynamics claimed. All original wait raw arrays remain byte-identical;
only fixture provenance declares the alternative parameter, never real physics.
"""
from pathlib import Path
import ast,copy,datetime,hashlib,importlib,json,os,shutil,sys,tempfile
W=Path(__file__).resolve().parent;ROOT=W.parents[1];P=W/'front_drive_1mm_preparation_r1';R=W/'front_corridor_midpoint_physical_r1';S=W/'staged_front_corridor_midpoint_integrated';sys.path[:0]=[str(W),str(ROOT)]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={};negative=[]
def reject(label,fn):
 try:fn()
 except (AssertionError,KeyError,ValueError):negative.append(label)
 else:raise AssertionError(('unexpected acceptance',label))
manifest=json.loads((W/'FRONT_DRIVE_1MM_AUDIT_FAMILY_PREPARATION.json').read_text())
def renamed(s):
 for a,b in manifest['global_replacements']:s=s.replace(a,b)
 return s
for row in manifest['adapters']:
 p=Path(row['path']);parent=Path(row['parent']);assert sha(p)==row['sha256'] and sha(parent)==row['parent_sha256'];s=p.read_text()
 for e in reversed(row['edits']):s=s.replace(e['new'],e['old'])
 assert s==renamed(parent.read_text());sources[str(p)]=sha(p);sources[str(parent)]=sha(parent)
from prepare_closed_peak_trial import parser_namespace
from simfoundry.data.waist_pilot_protocol import semantic_settings
plan=json.loads((P/'PLAN.json').read_text());old=json.loads((R/'PROTOCOL.json').read_text())['plan'];profile=json.loads((P/'TRIAL_PROFILE.json').read_text());oldprofile=json.loads((W/'staged_closed_peak_trial/TRIAL_PROFILE.json').read_text());assert plan['groups']==old['groups']
for key in ['prelaunch_settings','resolved_settings']:assert profile[key]==dict(oldprofile[key],front_cop_drive_step_m=.001)
from front_drive_1mm_stage_run_contract import primary,controls,ADDITIONAL,REPORTS
from front_corridor_midpoint_stage_run_contract import primary as primary_old,controls as controls_old,ADDITIONAL as ADD_OLD
inventory=[]
for c,orig in zip(plan['commands'],old['commands']):
 args=list(orig['args']);args[args.index('--front-cop-drive-step-m')+1]='.001';args[args.index('--out-dir')+1]=c['args'][c['args'].index('--out-dir')+1];assert c==dict(orig,args=args)
 parsed,_=parser_namespace(S/'collect_paired_sorting.py',args,full=True);settings=semantic_settings(parsed)
 for name in ['front_corridor_midpoint_replan','front_loaded_z_priority','front_initial_center_landing','terminal_release_margin','edge_clearance_intersection']:assert settings.pop(name) is True
 assert settings==profile['prelaunch_settings']
 for task in c['tasks']:
  ep=R/f"case_{c['layout_id']}"/f"layout_{c['layout_id']}_{task}";front={} if c['wait'] else json.loads((ep/'frontal_bypass.json').read_text())['plan']
  new=primary(c['wait'])+['audit_front_drive_1mm_stage_contacts.py','audit_front_drive_1mm_stage_pressure.py']+(controls(front)+ADDITIONAL if not c['wait'] else [])+['audit_front_drive_1mm_stage_release.py'];new=list(dict.fromkeys(new))
  prev=primary_old(c['wait'])+['audit_front_corridor_midpoint_stage_contacts.py','audit_front_corridor_midpoint_stage_pressure.py']+(controls_old(front)+ADD_OLD if not c['wait'] else [])+['audit_front_corridor_midpoint_stage_release.py'];prev=list(dict.fromkeys(prev));assert new==[renamed(n) for n in prev];assert all(n in REPORTS for n in new);inventory.append(dict(episode=ep.name,scripts=new))
assert len(inventory)==10 and sum(len(r['scripts']) for r in inventory)==204
imported=[];cli=[]
for row in manifest['adapters']:
 p=Path(row['path']);tree=ast.parse(p.read_text());top=[n for n in tree.body if not isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)) and not (isinstance(n,ast.If) and '__name__' in ast.unparse(n.test))]
 if any(isinstance(n,ast.Attribute) and n.attr in ('argv','parse_args','parse_known_args') for node in top for n in ast.walk(node)):cli.append(p.name);continue
 importlib.import_module(p.stem);imported.append(p.name)
from front_drive_1mm_stage_source_binding import verify_trial_provenance,verify_observation_binding
from audit_front_drive_1mm_execution import inspect
for c in plan['commands']:reject('original2mm_'+str(c['layout_id']),lambda c=c:verify_trial_provenance(R/f"case_{c['layout_id']}"))
original=R/'case_841010';name='layout_841010_wait_no_package'
with tempfile.TemporaryDirectory(prefix='front_1mm_unchanged_wait_') as tmp:
 case=Path(tmp)/original.name;shutil.copytree(original,case,copy_function=os.link);ep=case/name;provpath=case/'provenance.json';prov=json.loads(provpath.read_text());provpath.unlink();prov['args']['front_cop_drive_step_m']=.001;provpath.write_text(json.dumps(prov))
 (case/'SOURCE_CONTRACT_FIXTURE.json').write_text(json.dumps(dict(fixture_only=True,physical_candidate=False,scope=__doc__)))
 assert sha(ep/'raw.npz')==sha(original/name/'raw.npz');verify_trial_provenance(case);binding=verify_observation_binding(ep);assert binding['passed']
 fixture=inspect(ep,allow_source_fixture=True);assert fixture['passed'] and fixture['fixture_only'] and not fixture['physical_execution_evidence'] and fixture['frames']==70
 reject('default_rejects_fixture',lambda:inspect(ep))
 for value in [.002,.0015,.0005,None]:
  bad=copy.deepcopy(prov);bad['args']['front_cop_drive_step_m']=value;provpath.write_text(json.dumps(bad));reject('wrong_fixed_step_'+str(value),lambda:verify_trial_provenance(case))
 for key,value in [('steps',1199),('push_assist',True),('expert_frontal_top_load_n',6.)]:
  bad=copy.deepcopy(prov);bad['args'][key]=value;provpath.write_text(json.dumps(bad));reject('changed_original_'+key,lambda:verify_trial_provenance(case))
 provpath.write_text(json.dumps(prov));assert sha(ep/'raw.npz')==sha(original/name/'raw.npz')
for p in [Path(__file__),P/'PLAN.json',P/'TRIAL_PROFILE.json',W/'FRONT_DRIVE_1MM_AUDIT_FAMILY_PREPARATION.json',original/'provenance.json',original/name/'raw.npz']:sources[str(p)]=sha(p)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,exact_module_diffs=len(manifest['adapters']),collector_changed=False,configuration_count=6,condition_count=10,expected_audits=204,inventory=inventory,imported=imported,cli_static_only=cli,negative=negative,unchanged_wait_fixture_frames=70,fixture_removed=True,source_sha256=sources,new_physics=False,training_ready=False)
with (P/'CONFIGURATION_SOURCE_AUDIT_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps({k:v for k,v in out.items() if k not in ['inventory','source_sha256','scope']},indent=2))
