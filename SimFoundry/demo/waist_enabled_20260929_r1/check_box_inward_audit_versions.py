"""AST regression: unchanged inventory and full native loop; explicit loaded changes only."""
from pathlib import Path
import ast,json,hashlib,sys
w=Path(__file__).resolve().parent;sys.path[:0]=[str(w),str(w.parents[1])]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((w/'BOX_INWARD_AUDIT_VERSION_MAP.json').read_text())
def rename(s):
 for a,b in sorted(m.items(),key=lambda x:-len(x[0])):s=s.replace(a,b)
 return s.replace('BOX_ENTRY_','BOX_INWARD_')
files=[Path(__file__),w/'BOX_INWARD_AUDIT_VERSION_MAP.json',w/'build_box_inward_audits.py',w/'audit_box_inward_refinement.py'];same=[]
for a,b in m.items():
 p=w/(a+'.py');q=w/(b+'.py')
 if not p.exists():continue
 if a=='audit_box_entry_lift_events':p=w/'audit_box_entry_lift_events_measured.py'
 s=q.read_text();old=rename(p.read_text())
 if a=='audit_box_entry_pose_loaded_execution':
  s=s.replace('def verify_original_refinement(', 'def verify_refinement(')
  s=s.replace('from audit_box_inward_refinement import verify_refinement,normalized_trace\n\n','')
  s=s.replace("  if selected:normalized_trace(trace,inward_enabled)\n",'')
  s=s.replace(" inward_enabled=bool(plan.get('rear_box_inward_correction',{}).get('enabled'))\n",'')
  s=s.replace(',inward_enabled=inward_enabled);records.append',');records.append')
 elif a in ['close_box_entry_groups','run_box_entry_groups']:
  s=s.replace("prov['args']['rear_box_inward_correction'] is True and ",'').replace("meta['rear_box_inward_correction'] is True and ",'')
 elif a=='audit_box_entry_source_contract':
  s=s.replace(" assert args.get('rear_box_inward_correction') is True,'inward option missing'\n",'').replace(" assert meta.get('rear_box_inward_correction') is True,'raw inward option missing'\n",'')
  s=s.replace(",'joint_edge_inward_command.py','joint_edge_inward_adapter.py'",'').replace('  from audit_box_inward_refinement import verify_plan\n  verify_plan(args,plan,meta)','')
 assert ast.dump(ast.parse(s))==ast.dump(ast.parse(old)),a
 same.append(b);files.extend([p,q])
from audit_box_inward_source_contract import verify_box_inward_source
rejected=[]
for ep in sorted((w/'box_entry_lift_groups_r1').glob('case_*/layout_*')):
 if not (ep/'raw.npz').exists():continue
 try:verify_box_inward_source(ep)
 except AssertionError as e:assert str(e)=='inward option missing';rejected.append(ep.name)
 else:raise AssertionError('old source admitted')
assert len(rejected)==10
out=dict(passed=True,scope=__doc__,regressed_versions=same,old_source_rejections=rejected,source_sha256={str(p):sha(p) for p in files},physical_validation=False,training_ready=False)
(w/'staged_box_inward_correction/AUDIT_VERSION_CHECK.json').write_text(json.dumps(out,indent=2));print('PASS',len(same),'AST versions and10 legacy source rejections')
