"""Version only auditors transitively dependent on corrected compact-plan audit.
Keep original reports and original watcher statuses untouched. No source/physics
change, math change or task/admission change. Separate supplemental evidence.
"""
from pathlib import Path
import ast,json,hashlib,datetime,re
W=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
candidates={p.stem:p for p in W.glob('audit_joint_edge_stage_*.py') if not p.stem.endswith('_v2')};candidates['joint_edge_stage_audit_context']=W/'joint_edge_stage_audit_context.py'
names={'audit_joint_edge_stage_pose_live'}
while True:
 more={n for n,p in candidates.items() if any(old in p.read_text() for old in names)}-names
 if not more:break
 names.update(more)
mapping={n:n+'_v2' for n in names};reports={}
for n in names:
 for label in re.findall(r'JOINT_EDGE_STAGE_[A-Z_]+_AUDIT\.json',candidates[n].read_text()):
  if label.endswith('_V2_AUDIT.json'):continue
  # Only reports produced by one of these copied modules are renamed.
  for owner in names:
   tree=ast.parse(candidates[owner].read_text());s=candidates[owner].read_text()
   if label in s and ("ep/'"+label+"'").replace('ep/','') in s:
    # The definitive output mapping comes from run-contract metadata below.
    pass
import joint_edge_stage_run_contract as contract
for n in names:
 if n+'.py' in contract.REPORTS:
  report=contract.REPORTS[n+'.py'][0];reports[report]=report.replace('_AUDIT.json','_V2_AUDIT.json')
assert reports['JOINT_EDGE_STAGE_POSE_LIVE_AUDIT.json']=='JOINT_EDGE_STAGE_POSE_LIVE_V2_AUDIT.json'
files=[];outputs={}
for n in sorted(names-{'audit_joint_edge_stage_pose_live'}):
 original=candidates[n].read_text();text=original;edits=[]
 for old,new in sorted(list(mapping.items())+list(reports.items()),key=lambda x:-len(x[0])):
  count=text.count(old)
  if count:assert new not in text;text=text.replace(old,new);edits.append(dict(old=old,new=new,count=count))
 restored=text
 for e in reversed(edits):assert restored.count(e['new'])==e['count'];restored=restored.replace(e['new'],e['old'])
 assert restored==original;ast.parse(text);p=W/(mapping[n]+'.py');assert not p.exists();outputs[p]=text;files.append(dict(parent=candidates[n].name,parent_sha256=sha(candidates[n]),new=p.name,new_sha256=hashlib.sha256(text.encode()).hexdigest(),edits=edits,reverse_matches=True))
for p,text in outputs.items():
 with p.open('x') as f:f.write(text)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,module_mapping=mapping,report_mapping=reports,files=files,pose_revision_sha256=sha(W/'COMPACT_SCENE_POSE_AUDIT_PREPARATION.json'),preparer_sha256=sha(__file__),training_ready=False)
with (W/'JOINT_EDGE_COMPACT_DEPENDENT_AUDITS_PREPARATION.json').open('x') as f:json.dump(report,f,indent=2)
print('prepared',len(outputs),'dependent modules')
