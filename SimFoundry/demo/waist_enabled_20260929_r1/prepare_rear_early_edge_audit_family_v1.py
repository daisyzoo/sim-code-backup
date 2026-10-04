"""Derive original224 audits with independent early-Cartesian selection verification.
Parent motion, force, pose, guard, optimality and quality mathematics retained.
Preparation alone does not certify native integration or physical benefit.
"""
from pathlib import Path
import ast,json,hashlib,re,datetime
W=Path(__file__).resolve().parent;D=W/'rear_early_edge_preparation_r1';S=W/'staged_rear_early_edge_v1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text())
proof=read(D/'COLLECTOR_WIRING_CHECK.json');assert proof['passed'];selection=read(D/'INDEPENDENT_SELECTION_AUDITOR_CHECK_V1.json');assert selection['selection_auditor_eligible_checks']==2571 and len(selection['selection_auditor_mutation_rejections'])==5
for p,h in {**proof['source_sha256'],**selection['source_sha256']}.items():assert sha(p)==h,p
oldfile=W/'front_box_trailing_admission_preparation_r2/AUDIT_FAMILY_PREPARATION.json';old=read(oldfile);parents=old['adapters'];assert len(parents)==42
mapping={Path(r['path']).stem:Path(r['path']).stem.replace('front_box_trailing_r2_','rear_early_edge_r1_') for r in parents};assert len(set(mapping.values()))==42
mapping.update(front_box_trailing_stage_source_binding_v2='rear_early_edge_stage_source_binding_v1',staged_front_box_trailing_v2='staged_rear_early_edge_v1',FRONT_BOX_TRAILING_R2_='REAR_EARLY_EDGE_R1_')
pat=re.compile('|'.join(map(re.escape,sorted(mapping,key=len,reverse=True))));inverse={v:k for k,v in mapping.items()};rev=re.compile('|'.join(map(re.escape,sorted(inverse,key=len,reverse=True))));entries=[]
spec=read(D/'STAGE_PREPARATION.json')['spec']
for record in parents:
 parent=Path(record['path']);assert sha(parent)==record['sha256'];dest=W/(mapping[parent.stem]+'.py');text=pat.sub(lambda m:mapping[m.group()],parent.read_text());edits=[]
 def change(a,b):
  global text
  assert text.count(a)==1,(dest.name,a[:70],text.count(a));text=text.replace(a,b);edits.append(dict(old=a,new=b))
 if parent.name=='audit_front_box_trailing_r2_v1_stage_rear_xy.py':
  change('    slice_enabled=cfg.get(\'core_slice_feedback\',False)',"    early_spec="+repr(spec)+"\n    early_enabled=plan.get('rear_early_edge') is not None\n    if early_enabled:assert key=='box' and xy_enabled and plan['rear_early_edge']==early_spec\n    slice_enabled=cfg.get('core_slice_feedback',False)")
  a="                            expected_joint_xy=independent_joint_xy(base,command,ref,rot,size,local,plan['direction'])\n                            if expected_joint_xy['override']:emitted=np.array(expected_joint_xy['command_xyz'])"
  b="""                            expected_joint_xy=independent_joint_xy(base,command,ref,rot,size,local,plan['direction'])
                            if early_enabled:
                                from audit_rear_early_edge_selection_v1 import verify_selection,_independent_xy
                                verify_selection(observed=row['rear_joint_xy_progress'],early_enabled=True,side=side,enabled=True,mode=row['mode'],previous_xyz=base,parent_xyz=command,reference_xyz=ref,object_rotation=rot,core_size=size,cop_local=local,normal_load_n=sum(weights),direction=plan['direction'])
                                candidate_xy=_independent_xy(base,command,ref,rot,size,local,plan['direction'],.020)
                                if candidate_xy['override']:expected_joint_xy=candidate_xy
                            if expected_joint_xy['override']:emitted=np.array(expected_joint_xy['command_xyz'])"""
  change(a,b)
  change("        got_xy=row.get('rear_joint_xy_progress')", "        got_xy=row.get('rear_joint_xy_progress')\n        if not (early_enabled and f.get('override')):\n            assert not isinstance(got_xy,dict) or 'early_edge' not in got_xy")
  change("    declared_xy=prov['args'].get('rear_joint_xy_progress',False)","    from rear_early_edge_stage_source_binding_v1 import verify_observation_binding\n    verify_observation_binding(ep)\n    declared_xy=prov['args'].get('rear_joint_xy_progress',False)")
 restored=text
 for e in reversed(edits):assert restored.count(e['new'])==1;restored=restored.replace(e['new'],e['old'])
 assert rev.sub(lambda m:inverse[m.group()],restored)==parent.read_text();ast.parse(text)
 with dest.open('x') as f:f.write(text)
 entries.append(dict(parent=str(parent),parent_sha256=sha(parent),path=str(dest),sha256=sha(dest),edits=edits))
parent=W/'front_box_trailing_stage_source_binding_v2.py';dest=W/'rear_early_edge_stage_source_binding_v1.py';text=parent.read_text();edits=[]
def edit(a,b):
 global text
 assert text.count(a)==1,(a[:100],text.count(a));text=text.replace(a,b);edits.append(dict(old=a,new=b))
edit("S=W/'staged_front_box_trailing_v2'","S=W/'staged_rear_early_edge_v1'")
a=text.index('def verify_preparation():');b=text.index('\ndef verify_settings',a)
edit(text[a:b],'''EARLY_HELPERS=['rear_cop_route_early.py','rear_early_edge_governor.py']

def verify_preparation():
 from front_box_trailing_stage_source_binding_v2 import verify_preparation as verify_parent
 parent_used,bound=verify_parent();D=W/'rear_early_edge_preparation_r1';prep=json.loads((D/'STAGE_PREPARATION.json').read_text());parent=Path(prep['parent'])
 assert parent==W/'staged_front_box_trailing_v2' and Path(prep['stage'])==S
 assert prep['only_existing_file_changed']=='collect_paired_sorting.py' and prep['new_helpers']==EARLY_HELPERS
 for n,h in prep['parent_source_sha256'].items():assert sha(parent/n)==h,n
 for n,h in prep['stage_sha256'].items():assert sha(S/n)==h,n
 restored=(S/'collect_paired_sorting.py').read_text()
 for e in reversed(prep['collector_edits']):assert restored.count(e['new'])==1;restored=restored.replace(e['new'],e['old'])
 assert restored==(parent/'collect_paired_sorting.py').read_text()
 for n,h in prep['parent_source_sha256'].items():
  if n!='collect_paired_sorting.py':assert sha(S/n)==h,n
 assert set(prep['stage_sha256'])==set(prep['parent_source_sha256'])|set(EARLY_HELPERS)
 for name in EARLY_HELPERS:assert sha(S/name)==sha(W/'rear_early_edge_candidate_v1'/name)
 for name in ['COLLECTOR_WIRING_CHECK.json','INDEPENDENT_SELECTION_AUDITOR_CHECK_V1.json']:
  p=D/name;proof=json.loads(p.read_text())
  for f,h in proof['source_sha256'].items():assert sha(f)==h,f;bound[f]=h
  bound[str(p)]=sha(p)
 used={n:sha(S/n) for n in [*parent_used,*EARLY_HELPERS]};assert len(used)==100
 for p in [D/'STAGE_PREPARATION.json',Path(__file__),W/'audit_rear_early_edge_selection_v1.py']:bound[str(p)]=sha(p)
 return used,bound
''')
a=text.index('def verify_settings(args):');b=text.index('\ndef verify_trial_provenance',a)
edit(text[a:b],'''def verify_settings(args):
 from front_box_trailing_stage_source_binding_v2 import verify_settings as verify_parent
 args=dict(args);assert type(args['rear_early_edge']) is bool
 enabled=args.pop('rear_early_edge')
 if enabled:
  assert all(args.get(k) is True for k in ['rear_joint_xy_progress','rear_box_inward_correction','precise_clearance_task_ik','edge_clearance_intersection','peak_load_bias_guard','trace_substep_contacts'])
  assert args['role']=='diagnostic' and not args.get('policy_port') and not args.get('waist_probe') and not args.get('idle')
 return verify_parent(args)
''')
edit(" if not args['front_box_trailing_landing']:expected={k:v for k,v in expected.items() if k not in TRAILING_HELPERS}"," if not args['front_box_trailing_landing']:expected={k:v for k,v in expected.items() if k not in TRAILING_HELPERS}\n if not args['rear_early_edge']:expected={k:v for k,v in expected.items() if k not in EARLY_HELPERS}")
append='''

_verify_pre_early_observation_binding=verify_observation_binding

def verify_observation_binding(ep):
 ep=Path(ep).resolve();result=_verify_pre_early_observation_binding(ep)
 args=json.loads((ep.parent/'provenance.json').read_text())['args'];enabled=args['rear_early_edge'];assert type(enabled) is bool
 with np.load(ep/'raw.npz',allow_pickle=False) as z:meta=json.loads(str(z['collect_meta']));task=str(z['task_id'])
 fr={} if task=='wait_no_package' else json.loads((ep/'frontal_bypass.json').read_text());plan=fr.get('plan',{});rows=fr.get('rows',[])
 selected=bool(enabled and task=='push_box_to_bin' and plan.get('rear_cop_centering',{}).get('enabled'))
 spec=json.loads((W/'rear_early_edge_preparation_r1/STAGE_PREPARATION.json').read_text())['spec']
 if enabled:
  assert meta['rear_early_edge']==spec and all(type(meta['rear_early_edge'][k]) is type(v) for k,v in spec.items())
  assert type(meta['rear_early_edge_selected']) is bool and meta['rear_early_edge_selected']==selected
  assert type(meta['rear_early_edge_candidate_selected_frames']) is int
  count=0
  for row in rows:
   event=row.get('rear_joint_xy_progress',{}).get('early_edge')
   if event is not None:
    assert selected and row['mode']=='top_push' and row.get('rear_cop_centering',{}).get('override') is True
    assert type(event['candidate_selected']) is bool and event['version']==spec['version']
    count+=int(event['candidate_selected'])
  assert meta['rear_early_edge_candidate_selected_frames']==count
 else:assert not any(k.startswith('rear_early_edge') for k in meta)
 if selected:
  assert plan['rear_early_edge']==spec and meta['frontal_bypass_plan']['rear_early_edge']==spec
 else:
  assert 'rear_early_edge' not in plan and all('early_edge' not in r.get('rear_joint_xy_progress',{}) for r in rows)
 result['source_sha256'][str(Path(__file__))]=sha(Path(__file__));result['early_cartesian_selection_independent_audit_required']=selected
 return result
'''
text+=append;edits.append(dict(old='',new=append,append=True));restored=text
for e in reversed(edits):
 if e.get('append'):assert restored.endswith(e['new']);restored=restored[:-len(e['new'])]
 else:assert restored.count(e['new'])==1;restored=restored.replace(e['new'],e['old'])
assert restored==parent.read_text();ast.parse(text)
with dest.open('x') as f:f.write(text)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,adapters=entries,helpers=old['helpers'],replacements=mapping,source_binding=dict(parent=str(parent),parent_sha256=sha(parent),path=str(dest),sha256=sha(dest),edits=edits),expected_full_invocations=224,source_sha256={str(p):sha(p) for p in [Path(__file__),oldfile,D/'STAGE_PREPARATION.json',D/'COLLECTOR_WIRING_CHECK.json',D/'INDEPENDENT_SELECTION_AUDITOR_CHECK_V1.json',W/'audit_rear_early_edge_selection_v1.py']},native_integration_checks_pending=True,physical_started=False,training_ready=False)
with (D/'AUDIT_FAMILY_PREPARATION.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(adapters=len(entries),changed_math_consumers=1,source_binding=str(dest),expected_full_invocations=224)))
