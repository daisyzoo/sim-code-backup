"""Isolated rear-box-only1mm follow-up; no running/frozen source changes."""
from pathlib import Path
import json,hashlib
w=Path(__file__).resolve().parent;old=w/'staged_rear_slow_drag';stage=w/'staged_rear_box_rate';assert not stage.exists();stage.mkdir();changed={};sha=lambda s:hashlib.sha256(s.encode()).hexdigest()
for p in old.iterdir():
 if p.suffix not in ['.py','.json'] or p.name.endswith('CHECK.json') or p.name=='CHANGE_MANIFEST.json':continue
 s=p.read_text();original=s
 if p.name in ['collect_paired_sorting.py','rear_cop_route.py']:
  s=s.replace('rear_slow_drag','rear_box_slow_drag').replace('--rear-slow-drag','--rear-box-slow-drag')
  if p.name=='collect_paired_sorting.py':
   s=s.replace('Diagnostic rear-region only 1.5mm drag; original front and initial routes preserved.','Diagnostic rear-box-only1mm drag; rear bag and front/initial routes retain3mm.')
   needle='rear_box_slow_drag=args.rear_box_slow_drag, rear_cop_enabled=True';assert s.count(needle)==1;s=s.replace(needle,"rear_box_slow_drag=bool(args.rear_box_slow_drag and side=='right'), rear_cop_enabled=True")
   needle=".0015 if args.rear_box_slow_drag and frontal_plan.get('rear_cop_centering',{}).get('enabled',False)";assert s.count(needle)==1;s=s.replace(needle,".001 if args.rear_box_slow_drag and side=='right' and frontal_plan.get('rear_cop_centering',{}).get('enabled',False)")
  else:
   assert s.count('.0015 if self.rear_box_slow_drag else .003')==1;s=s.replace('.0015 if self.rear_box_slow_drag else .003','.001 if self.rear_box_slow_drag else .003').replace('rear-only 1.5mm','rear-box-only1mm')
 if p.suffix=='.py':compile(s,str(stage/p.name),'exec')
 (stage/p.name).write_text(s)
 if s!=original:changed[p.name]=dict(before_sha256=sha(original),after_sha256=sha(s))
assert set(changed)=={'collect_paired_sorting.py','rear_cop_route.py'}
mapping={v:v.replace('slow_drag','box_rate').replace('SLOW_DRAG','BOX_RATE') for v in json.loads((w/'SLOW_DRAG_AUDIT_VERSION_MAP.json').read_text()).values()}
mapping['slow_drag_step_contract']='box_rate_step_contract'
(w/'BOX_RATE_AUDIT_VERSION_MAP.json').write_text(json.dumps(mapping,indent=2))
def rename(s):
 for a,b in sorted(mapping.items(),key=lambda x:-len(x[0])):s=s.replace(a,b)
 return s.replace('rear_slow_drag','rear_box_slow_drag')
for a,b in mapping.items():
 if not (w/(a+'.py')).is_file():continue
 s=rename((w/(a+'.py')).read_text())
 if a=='slow_drag_step_contract':
  s=s.replace('step in (.0015,.003)','step in (.001,.003)')
  s=s.replace(' expected=.0015 if rear else .003'," assert plan['direction'] in (-1,1)\n expected=.001 if rear and plan['direction']==-1 else .003")
 p=w/(b+'.py');assert not p.exists();compile(s,str(p),'exec');p.write_text(s)
for a,b in {'slow_drag_run_contract':'box_rate_run_contract','run_slow_drag_groups':'run_box_rate_groups','watch_slow_drag_audits':'watch_box_rate_audits','close_slow_drag_groups':'close_box_rate_groups'}.items():
 s=rename((w/(a+'.py')).read_text()).replace('slow_drag_run_contract','box_rate_run_contract');p=w/(b+'.py');assert not p.exists();compile(s,str(p),'exec');p.write_text(s)
(stage/'CHANGE_MANIFEST.json').write_text(json.dumps(dict(changes=changed,scope='Relative to original minimum-motion3mm baseline, only selected rear box uses1mm. Rear bag and all front/initial routes3mm. No automatic launch/admission.'),indent=2));print('created isolated rear box1mm candidate; pending checks and full predecessor closure')
