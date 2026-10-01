"""Execute exact front class selection, real packet hook and actual update AST."""
from pathlib import Path
import ast,types,copy,json,hashlib,sys
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;stage=w/'staged_front_cop_transverse';sys.path[:0]=[str(stage),str(w.parents[1])]
import check_front_cop_transverse_route as fixtures
from front_cop_route import FrontCopRouteState
from simfoundry.data.front_top_route import FrontTopRouteState
source=(stage/'collect_paired_sorting.py').read_text();tree=ast.parse(source)
selection=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='front_route_selected' and 'from simfoundry.data.front_top_route import FrontTopRouteState' in ast.unparse(n))
hook=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='args.front_cop_slip_following and front_route_selected')
call=next(n for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='waypoint' for t in n.targets) and isinstance(n.value,ast.Call) and ast.unparse(n.value.func)=='frontal_state.update')
execute=lambda node,ns:exec(compile(ast.Module(body=[node],type_ignores=[]),str(stage/'collect_paired_sorting.py'),'exec'),ns)
cfg=json.loads((w/'region_continuity_groups_r1/case_840001/provenance.json').read_text())['args'];checks=[]
for enabled in [False,True]:
 ns=dict(args=types.SimpleNamespace(**dict(cfg,front_cop_slip_following=enabled)),front_route_selected=True,obstacle_size=fixtures.osize,frontal_plan={})
 execute(selection,ns);assert ns['top_cls'] is (FrontCopRouteState if enabled else FrontTopRouteState)
 assert bool(ns['top_extra'].get('cop_slip_enabled'))==enabled
 if enabled:assert ns['frontal_plan']['front_cop_slip_following']['feedback_projection']=='orthogonal_to_current_goal_direction'
 checks.append(dict(check='actual_class_selection',enabled=enabled))
state,callargs,kw,expected_contact,t=fixtures.guard_fixture;side=fixtures.side;actor=fixtures.actor;other_actor='mailer' if side=='right' else 'parcel_box';positions={actor:callargs[1],other_actor:callargs[2]};packet=fixtures.packets[t-1]
ns=dict(args=types.SimpleNamespace(front_cop_slip_following=True),front_route_selected=True,solved_contact_forces=[packet],side=side,target_actor=actor,obstacle_actor=other_actor,env=None,parcel_xyz=lambda env,a:positions[a],target_quat=kw['quat'],obstacle_quat=kw['obstacle_quat'],frontal_state=copy.deepcopy(state),point_kwargs=dict(kw),robot=None,hands={side:side},palm_xyz=lambda robot,hand:callargs[0],target_size=fixtures.size,obstacle_size=fixtures.osize,extent_x_from_quat=lambda sz,q:(abs(Rotation.from_quat(q).as_matrix())@np.array(sz)/2)[0])
execute(hook,ns);contact=ns['point_kwargs']['slip_contact'];assert fixtures.encode(contact)==fixtures.encode(expected_contact)
# Independent signed force-weighted centroid from the actual previous packet.
rot=Rotation.from_quat(kw['quat']).as_matrix();points=[];weights=[]
for c in packet['parcel_contacts']:
 slots=[i for i,s in enumerate(c['shapes']) if '/'+actor+'/' in s]
 if len(slots)!=1 or not any(side+'_wrist' in s for s in c['shapes']):continue
 force=np.asarray(c['force_world_N'])*(1 if slots[0]==1 else -1);normal=-float(force@rot[:,2])
 if normal>.05:points.append(c['position_world']);weights.append(normal)
assert weights;local=rot.T@(np.average(points,axis=0,weights=weights)-callargs[1]);error=float(np.max(abs(local-contact['weighted_contact_local'])));print('Independent float64 vs recorded-float32 rotation COP error_m:',error,flush=True);assert error<1e-7
execute(call,ns);assert ns['waypoint']['cop_slip_following']['override'];checks.append(dict(check='actual_previous_packet_hook_and_controller_update',source_step=t,normal_load_n=contact['normal_load_n'],independent_cop_error_m=float(np.max(abs(local-contact['weighted_contact_local'])))))
for enabled,selected in [(False,True),(True,False)]:
 off=dict(ns,args=types.SimpleNamespace(front_cop_slip_following=enabled),front_route_selected=selected,point_kwargs={});execute(hook,off);assert not off['point_kwargs'];checks.append(dict(check='measurement_hook_inactive',enabled=enabled,front_selected=selected))
out=dict(passed=True,checks=checks,collector_sha256=hashlib.sha256((stage/'collect_paired_sorting.py').read_bytes()).hexdigest(),checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Exact collector AST executed with explicit recorded sensor fixtures. Signed COP independently recomputed from actual previous solved packet. No Isaac/physics or new trajectory outcome.',training_ready=False)
(stage/'FRONT_COP_WIRING_CHECK.json').write_text(json.dumps(out,indent=2));print(out)
