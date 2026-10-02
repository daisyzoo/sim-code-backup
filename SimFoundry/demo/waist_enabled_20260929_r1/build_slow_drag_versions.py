"""Explicit isolated rear-only 1.5mm candidate; preserve all frozen predecessors."""
from pathlib import Path
import json,hashlib,ast
w=Path(__file__).resolve().parent;oldstage=w/'staged_minimum_motion_recontact';stage=w/'staged_rear_slow_drag';assert not stage.exists();stage.mkdir()
changes={}
for p in oldstage.iterdir():
 if p.suffix not in ['.py','.json'] or p.name.endswith('CHECK.json'):continue
 s=p.read_text();original=s
 if p.name=='collect_paired_sorting.py':
  s=s.replace("parser.add_argument('--minimum-motion-recontact'", "parser.add_argument('--rear-slow-drag', action='store_true', help='Diagnostic rear-region only 1.5mm drag; original front and initial routes preserved.')\nparser.add_argument('--minimum-motion-recontact'",1)
  s=s.replace('if args.minimum_motion_recontact and not (',"if args.rear_slow_drag and not (args.minimum_motion_recontact and args.rear_cop_centering and args.expert_frontal_top_drag_step_m==.003 and args.expert_frontal_top_continuous_drag and args.role=='diagnostic'):\n    parser.error('Rear slow drag requires complete minimum-motion diagnostic, original global3mm continuous drag and rear COP')\nif args.minimum_motion_recontact and not (",1)
  s=s.replace('top_extra.update(rear_cop_enabled=True,', 'top_extra.update(rear_slow_drag=args.rear_slow_drag, rear_cop_enabled=True,',1)
  needle='                frontal_state = top_cls(frontal_state,side,contact_size,**top_extra,';assert s.count(needle)==1
  s=s.replace(needle,"                effective_drag_step_m = .0015 if args.rear_slow_drag and frontal_plan.get('rear_cop_centering',{}).get('enabled',False) else args.expert_frontal_top_drag_step_m\n"+needle)
  assert s.count('drag_step_m=args.expert_frontal_top_drag_step_m')==2
  s=s.replace('drag_step_m=args.expert_frontal_top_drag_step_m','drag_step_m=effective_drag_step_m')
  s=s.replace("    rgb_means = episode.rgb.mean", "    if args.rear_slow_drag:\n        episode.collect_meta['rear_slow_drag']=True\n    rgb_means = episode.rgb.mean",1)
 elif p.name=='rear_cop_route.py':
  s=s.replace('    rear_joint_xy_enabled: bool = False','    rear_slow_drag: bool = False\n    rear_joint_xy_enabled: bool = False',1)
  s=s.replace('        if self.rear_cop_enabled and (not self.continuous_drag or self.drag_step_m != .003):',"        if type(self.rear_slow_drag) is not bool or (self.rear_slow_drag and not self.rear_cop_enabled):\n            raise ValueError('Rear slow drag requires enabled rear COP')\n        if self.rear_cop_enabled and (not self.continuous_drag or self.drag_step_m != (.0015 if self.rear_slow_drag else .003)):",1)
  s=s.replace('Rear COP requires original 3mm continuous drag','Rear COP requires declared 3mm or rear-only 1.5mm continuous drag')
 if p.suffix=='.py':compile(s,str(stage/p.name),'exec')
 (stage/p.name).write_text(s)
 if s!=original:changes[p.name]=dict(before_sha256=hashlib.sha256(original.encode()).hexdigest(),after_sha256=hashlib.sha256(s.encode()).hexdigest())
assert set(changes)=={'collect_paired_sorting.py','rear_cop_route.py'}
old=json.loads((w/'MINIMUM_MOTION_AUDIT_VERSION_MAP.json').read_text());mapping={v:v.replace('audit_minimum_motion_','audit_slow_drag_').replace('MINIMUM_MOTION_','SLOW_DRAG_').replace('minimum_motion_audit_context','slow_drag_audit_context').replace('staged_minimum_motion_recontact','staged_rear_slow_drag').replace('verify_minimum_motion_source','verify_slow_drag_source') for v in old.values()}
for a in ['audit_minimum_motion_plan','audit_minimum_motion_events','audit_minimum_motion_loaded_parent']:mapping[a]=a.replace('audit_minimum_motion_','audit_slow_drag_')
(w/'SLOW_DRAG_AUDIT_VERSION_MAP.json').write_text(json.dumps(mapping,indent=2))
def rename(s):
 for a,b in sorted(mapping.items(),key=lambda x:-len(x[0])):s=s.replace(a,b)
 return s
formula='base[1]+np.clip(direction*min(.34,direction*base[1]+.003)-base[1],-.003,.003)'
for a,b in mapping.items():
 if a.endswith('.json') or a.startswith('staged_') or a=='verify_minimum_motion_source':continue
 source=w/(a+'.py');s=source.read_text()
 if a=='audit_minimum_motion_plan':s=(w/'audit_minimum_motion_plan_reentrant.py').read_text()
 s=rename(s)
 if a=='audit_minimum_motion_source_contract':
  s=s.replace(" assert args.get('minimum_motion_recontact') is True", " assert args.get('rear_slow_drag') is True,'rear slow drag flag missing/disabled'\n assert args.get('expert_frontal_top_drag_step_m')==.003\n assert args.get('minimum_motion_recontact') is True",1)
  s=s.replace("'minimum_motion_lifecycle.py'];bound={}","'minimum_motion_lifecycle.py','rear_cop_route.py'];bound={}")
  s=s.replace(" assert meta.get('minimum_motion_recontact') is True", " assert meta.get('rear_slow_drag') is True,'raw rear slow drag flag missing'\n assert meta.get('minimum_motion_recontact') is True",1)
  s=s.replace(" return dict(passed=True,ftol=1e-13", " if (ep/'frontal_bypass.json').exists():\n  from slow_drag_step_contract import verify_declared_step\n  verify_declared_step(args,plan,meta)\n return dict(passed=True,ftol=1e-13",1)
 if a in ['audit_minimum_motion_region_continuity','audit_minimum_motion_rear_xy']:
  assert s.count(formula)==1;s=s.replace(formula,'base[1]+np.clip(direction*min(.34,direction*base[1]+drag_step)-base[1],-drag_step,drag_step)')
  if a.endswith('region_continuity'):
   s=s.replace("records=[];errors=[]", "records=[];errors=[]\nfrom slow_drag_step_contract import declared_step\ndrag_step=declared_step(plan)",1).replace('unchanged X2mm/Y3mm','unchanged X2mm and declared rear Y increment')
  else:
   needle='def reconstruct(rows, plan, xyz, quat, packets, key, handover):\n';assert needle in s;s=s.replace(needle,needle+'    from slow_drag_step_contract import declared_step\n    drag_step=declared_step(plan)\n',1)
 if a=='audit_minimum_motion_pose_loaded_execution':s=s.replace('from audit_rear_joint_xy_live import reconstruct','from audit_slow_drag_rear_xy import reconstruct')
 p=w/(b+'.py');assert not p.exists();compile(s,str(p),'exec');p.write_text(s)
for a,b in {'minimum_motion_run_contract':'slow_drag_run_contract','run_minimum_motion_groups':'run_slow_drag_groups','watch_minimum_motion_audits':'watch_slow_drag_audits','close_minimum_motion_groups':'close_slow_drag_groups'}.items():
 s=rename((w/(a+'.py')).read_text()).replace('minimum_motion_run_contract','slow_drag_run_contract')
 if a.startswith(('run_','close_')):s=s.replace("assert prov['args']['minimum_motion_recontact'] is True", "assert prov['args']['rear_slow_drag'] is True and prov['args']['minimum_motion_recontact'] is True")
 if a.startswith('close_'):s=s.replace("assert meta['minimum_motion_recontact'] is True", "assert meta['rear_slow_drag'] is True and meta['minimum_motion_recontact'] is True")
 p=w/(b+'.py');assert not p.exists();compile(s,str(p),'exec');p.write_text(s)
(stage/'CHANGE_MANIFEST.json').write_text(json.dumps(dict(changes=changes,scope='Rear selected route only1.5mm; original global3mm/front/initial unchanged; no physical admission.'),indent=2))
print('created isolated stage, auditors and drivers; not launched')
