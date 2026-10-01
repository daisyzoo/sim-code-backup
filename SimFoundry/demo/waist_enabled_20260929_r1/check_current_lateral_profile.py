"""Actual current collector factory on original failed lateral reset geometry.
No physical simulation, no new task evidence, no training admission.
"""
from pathlib import Path
import sys,ast,types,json,math,hashlib,copy
from types import SimpleNamespace as NS
import torch
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path.insert(0,str(repo))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
class AppLauncher:
 @staticmethod
 def add_app_launcher_args(parser):
  parser.add_argument('--device',default='cuda');parser.add_argument('--headless',action='store_true');parser.add_argument('--viz',default='none')
app=types.ModuleType('isaaclab.app');app.AppLauncher=AppLauncher;sys.modules['isaaclab.app']=app
source=(repo/'scripts/collect_paired_sorting.py').read_text();plan=json.loads((w/'INITIAL_NEAR_CONTACT_PLAN.json').read_text())
for p,h in plan['source_sha256'].items():assert sha(Path(p))==h,p
sys.argv=['collector',*plan['settings'],'--out-dir','/tmp/lateral_factory_only'];scope={'__file__':str(repo/'scripts/collect_paired_sorting.py')}
exec(compile(source.split('app = AppLauncher(args, enable_cameras=True).app')[0],'<actual_parser>','exec'),scope);args=scope['args']
nodes=[n for n in ast.walk(ast.parse(source)) if isinstance(n,ast.If) and ast.unparse(n.test)=="args.expert_frontal_bypass and task_id != 'wait_no_package'"];assert len(nodes)==1
factory=compile(ast.Module(body=nodes,type_ignores=[]),'<actual_factory>','exec')
parent=w/'fresh_lateral_00_pilot_r1';protocol=json.loads((parent/'PROTOCOL.json').read_text());contract=json.loads(Path(protocol['contract_path']).read_text());rows=[]
for layout in contract['layouts']:
 scene={actor:NS(data=NS(root_quat_w=NS(torch=torch.tensor([[0.,0.,math.sin(layout[key+'_yaw']/2),math.cos(layout[key+'_yaw']/2)]],dtype=torch.float64)))) for actor,key in [('parcel_box','box'),('mailer','mailer')]}
 for key,side,task in [('box','right','push_box_to_bin'),('mailer','left','nudge_mailer_to_bin')]:
  ctx=dict(args=copy.deepcopy(args),task_id=task,layout=layout,side=side,target=layout[key+'_xyz'],initial={'box':layout['box_xyz'],'mailer':layout['mailer_xyz']},env=NS(scene=scene),front_route_selected=False,initial_top_selected=False,frontal_state=None,frontal_plan=None,inactive_anchor={'left':[.3,.23,.89],'right':[.3,-.23,.89]});exec(factory,ctx)
  state=ctx['frontal_state'];new=ctx['frontal_plan'];ep=parent/f"case_{layout['layout_id']}"/f"layout_{layout['layout_id']}_{task}";old=json.loads((ep/'frontal_bypass.json').read_text())
  row=dict(layout_id=layout['layout_id'],task=task,parent_raw_sha256=sha(ep/'raw.npz'),current_controller=type(state).__name__,current_initial_top=ctx['initial_top_selected'],current_front=ctx['front_route_selected'],current_fraction=getattr(state,'front_inset_fraction',None),current_alignment=getattr(state,'alignment_tolerance_m',None),current_plan=new,parent_plan=old.get('plan'),original_quality=json.loads((ep/'quality.json').read_text()))
  rows.append(row)
result=dict(rows=rows,collector_sha256=sha(repo/'scripts/collect_paired_sorting.py'),current_plan_sha256=sha(w/'INITIAL_NEAR_CONTACT_PLAN.json'),parent_contract_sha256=sha(Path(protocol['contract_path'])),scope='Actual current parser/factory on frozen original lateral reset geometry. Profile differences are bundled and must not be called one-variable improvement; no physics or success prediction. Parent failed mechanisms apply to legacy profile, not automatically to current routes/support mapping.',training_ready=False)
(w/'CURRENT_LATERAL_PROFILE_PRECHECK.json').write_text(json.dumps(result,indent=2));print(json.dumps([{k:v for k,v in row.items() if k not in ['parent_raw_sha256','current_plan','parent_plan','original_quality']} for row in rows],indent=2))
