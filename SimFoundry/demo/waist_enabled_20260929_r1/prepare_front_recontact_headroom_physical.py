"""Prepare original matched8push2wait headroom trial; no physics or admission.
Keep all original controls, task gates, source checks and parent closure checks.
"""
from pathlib import Path
import ast,datetime,hashlib,json,re
W=Path(__file__).resolve().parent;H=W/'staged_front_recontact_headroom';P=W/'front_recontact_headroom_preparation_r1';P.mkdir(exist_ok=False);sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
family=json.loads((H/'AUDIT_FAMILY_PREPARATION.json').read_text());mapping=dict(family['replacements']);names=['review_front_recontact_v1_stage_episode.py','review_front_recontact_incomplete_episode.py','watch_front_recontact_numeric_reviews_r1.py','watch_front_recontact_physical_audits_r1.py','close_front_recontact_physical.py','queue_front_recontact_physical_r1_closure.py','summarize_front_recontact_actual_reviews.py','run_front_recontact_physical_r1.py','check_front_recontact_physical_configuration_v2.py']
for n in names:mapping[n[:-3]]=n[:-3].replace('front_recontact_','front_recontact_headroom_',1)
mapping.update(front_recontact_preparation_r1='front_recontact_headroom_preparation_r1',front_recontact_physical_r1='front_recontact_headroom_physical_r1',FRONT_RECONTACT_INCOMPLETE='FRONT_RECONTACT_HEADROOM_INCOMPLETE',FRONT_RECONTACT_REVIEW='FRONT_RECONTACT_HEADROOM_REVIEW')
pattern=re.compile('|'.join(re.escape(k) for k in sorted(mapping,key=len,reverse=True)))
def rename(s):return pattern.sub(lambda m:mapping[m.group()],s)
plan=json.loads((W/'front_recontact_preparation_r1/PLAN.json').read_text());plan['created_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();plan['collector']=str(H/'collect_paired_sorting.py');plan['collector_sha256']=sha(plan['collector']);plan['scope']=__doc__
for c in plan['commands']:c['args'][c['args'].index('--out-dir')+1]=str(W/'front_recontact_headroom_physical_r1'/f"case_{c['layout_id']}")
plan['planning_headroom']=json.loads((H/'COLLECTOR_PREPARATION.json').read_text())['planning_headroom']
with (P/'PLAN.json').open('x') as f:json.dump(plan,f,indent=2)
records=[]
for n in names:
 p=W/n;s=rename(p.read_text());changes=[]
 def change(a,b):
  global s
  assert a in s,(n,a[:100]);s=s.replace(a,b);changes.append(dict(old=a,new=b))
 if n=='run_front_recontact_physical_r1.py':
  original=ast.parse(p.read_text());lists={t.id:ast.literal_eval(node.value) for node in original.body if isinstance(node,ast.Assign) for t in node.targets if isinstance(t,ast.Name) and t.id in ['CHECKS','MANIFESTS']}
  checks=lists['CHECKS']+[str(H.relative_to(W)/x) for x in ['SOURCE_BINDING_CHECK.json','INDEPENDENT_STREAM_CHECK.json','WAIT_STREAM_CHECK.json','AUDIT_FAMILY_IMPORT_CHECK.json','LOADED_INPUT_CHECK.json','NATIVE_WAIT_CHECK.json','NATIVE_JOINT_BRANCH_CHECK.json']]+['front_bag_recontact_headroom_draft_r1/GUARD_CHECK.json','front_bag_recontact_headroom_draft_r1/PROBE_RESULT.json','front_recontact_headroom_preparation_r1/CONFIGURATION_SOURCE_AUDIT_CHECK.json']
  manifests=lists['MANIFESTS']+['staged_front_recontact_headroom/AUDIT_FAMILY_PREPARATION.json','front_recontact_headroom_preparation_r1/PHYSICAL_PREPARATION.json']
  begin=s.index('CHECKS=');end=s.index('_cache={}',begin);change(s[begin:end],'CHECKS='+repr(checks)+'\nMANIFESTS='+repr(manifests)+'\n')
  # Old check stage digests belong to their declared old stage, not new sources.
  change("if 'stage_sha256' in r:bound({str(S/k):h for k,h in r['stage_sha256'].items()})","if 'stage_sha256' in r:bound({str((W/n).parent/k):h for k,h in r['stage_sha256'].items()})")
 if n=='check_front_recontact_physical_configuration_v2.py':
  change("['audit_front_recontact_v1_','audit_front_recontact_v2_','audit_front_recontact_v3_',","['audit_front_recontact_headroom_v1_','audit_front_recontact_headroom_v2_','audit_front_recontact_headroom_v3_',")
 ast.parse(s);dest=W/(mapping[p.stem]+'.py');assert not dest.exists()
 with dest.open('x') as f:f.write(s)
 records.append(dict(parent=str(p),parent_sha256=sha(p),path=str(dest),sha256=sha(dest),edits=changes))
with (P/'PHYSICAL_PREPARATION.json').open('x') as f:json.dump(dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,files=records,replacements=mapping,source_sha256={str(p):sha(p) for p in [Path(__file__),H/'AUDIT_FAMILY_PREPARATION.json',P/'PLAN.json']},physics_started=False,training_ready=False),f,indent=2)
# Bind all reachable local audit imports, including literal file references.
roots=[W/Path(r['path']).name for r in family['adapters']]+[W/'audit_front_recontact_headroom_stream.py',W/'front_recontact_headroom_v2_stage_source_binding.py'];queue=list(roots);seen={};missing=[]
while queue:
 p=queue.pop()
 if str(p) in seen:continue
 seen[str(p)]=sha(p);tree=ast.parse(p.read_text())
 for node in ast.walk(tree):
  modules=([node.module] if isinstance(node,ast.ImportFrom) and node.module else [a.name for a in node.names] if isinstance(node,ast.Import) else [])
  for module in modules:
   q=W/(module+'.py')
   if q.is_file():queue.append(q)
  if isinstance(node,ast.Constant) and isinstance(node.value,str) and node.value.endswith('.py') and '/' not in node.value:
   q=W/node.value
   if q.is_file():queue.append(q)
with (P/'AUDIT_DEPENDENCIES.json').open('x') as f:json.dump(dict(source_sha256=seen,missing=missing,training_ready=False),f,indent=2)
print(json.dumps(dict(files=len(records),local_dependencies=len(seen),conditions=10,physics_started=False)))
