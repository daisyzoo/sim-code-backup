"""Actual staged parser and hold measurement/output AST on recorded CPU fixtures."""
from pathlib import Path
import sys,types,json,hashlib,ast,copy,io,contextlib
import numpy as np,torch
from scipy.spatial.transform import Rotation
from types import SimpleNamespace as NS
root=Path(__file__).resolve().parent;repo=root.parents[1];stage=root/'staged_terminal_hold';sys.path[:0]=[str(root),str(repo)]
from simfoundry.data.confirmed_position_release import ConfirmedPositionRelease
from terminal_joint_hold_candidate import TerminalJointHold
manifest=json.loads((stage/'MANIFEST.json').read_text())
for name,digest in manifest['candidate_sha256'].items():assert hashlib.sha256((stage/name).read_bytes()).hexdigest()==digest,name
assert (stage/'terminal_joint_hold.py').read_bytes()==(root/'terminal_joint_hold_candidate.py').read_bytes()
source=(stage/'collect_paired_sorting.py').read_text();tree=ast.parse(source);blocks=[n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='terminal_hold is not None'];assert len(blocks)==1
block=compile(ast.Module(body=blocks,type_ignores=[]),'actual_hold_block','exec')
class AppLauncher:
 @staticmethod
 def add_app_launcher_args(parser):
  parser.add_argument('--device',default='cuda');parser.add_argument('--headless',action='store_true');parser.add_argument('--viz',default='none')
app=types.ModuleType('isaaclab.app');app.AppLauncher=AppLauncher;sys.modules['isaaclab.app']=app
base=json.loads((root/'contact_stability_groups_r1/PROTOCOL.json').read_text())['settings']+['--out-dir','/tmp/terminal_hold_no_output'];cli=[]
pilot=list(base);pilot[pilot.index('--role')+1]='pilot'
for label,args,expected in [('default_off',base,True),('on',base+['--expert-terminal-joint-hold'],True),('missing_force',[v for v in base if v!='--trace-solved-contact-forces']+['--expert-terminal-joint-hold'],False),('missing_bounded',[v for v in base if v!='--bounded-coupled-ik']+['--expert-terminal-joint-hold'],False),('pilot',pilot+['--expert-terminal-joint-hold'],False)]:
 sys.argv=['candidate',*args];accepted=True;err=io.StringIO();scope={'__file__':str(repo/'scripts/collect_paired_sorting.py')}
 try:
  with contextlib.redirect_stderr(err):exec(compile(source.split('app = AppLauncher(args, enable_cameras=True).app')[0],'parser_prefix','exec'),scope)
 except SystemExit as exc:assert exc.code==2;accepted=False
 assert accepted==expected,(label,err.getvalue());cli.append(dict(case=label,accepted=accepted))
# Cached independent URDF FK, no Isaac or commands executed.
src=(root/'audit_terminal_reach.py').read_text();exec(compile(src.split("p=root/'contact_x_ablation")[0],'<cached_fk>','exec'))
def transform(side,q):
 m=np.eye(4);m[:3,3]=[.08,0,.793]
 for name,origin,axis in chains[side]:
  m=m@origin
  if axis is not None:
   a=np.eye(4);a[:3,:3]=Rotation.from_rotvec(axis*q.get(name,0)).as_matrix();m=m@a
 return m
results=[];run=root/'contact_stability_groups_r1'
for identifier,task,expected in [(62012,'push_box_to_bin',79),(62005,'push_box_to_bin',758),(62013,'nudge_mailer_to_bin',None)]:
 ep=run/f'case_{identifier}/layout_{identifier}_{task}';side='right' if 'push_box' in task else 'left';key='box' if side=='right' else 'mailer';direction=-1 if side=='right' else 1
 with np.load(ep/'raw.npz') as z,np.load(ep/'trace.npz') as tr,np.load(ep/'parcel_orientation.npz') as ori:
  control=json.loads((ep/'expert_control.json').read_text());coordinates={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};forces={r['after_action_step']:r for r in json.loads((ep/'solved_contact_forces.json').read_text())['rows']}
  initial={k:v[0].tolist() for k,v in tr.items()};scope=dict(np=np,terminal_hold=TerminalJointHold(),terminal_goal=ConfirmedPositionRelease(tr[key][0,1],direction),terminal_hold_log=[],terminal_other_max_xy=0.,side=side,hands={'left':0,'right':1},initial=initial,default=np.zeros(23),ordered_ids=list(range(23)))
  first=None;guard_revocation=False
  for t in range(1,len(z['q'])):
   q=dict(zip(names,z['q'][t,12:23]));ms=[transform(s,q) for s in ['left','right']]
   robot=NS(data=NS(body_pos_w=NS(torch=torch.tensor(np.array([[m[:3,3] for m in ms]]))),body_quat_w=NS(torch=torch.tensor(np.array([[Rotation.from_matrix(m[:3,:3]).as_quat() for m in ms]]))),joint_pos=NS(torch=torch.tensor(z['q'][t:t+1]))))
   env=NS(scene={actor:NS(data=NS(root_quat_w=NS(torch=torch.tensor(ori[k][t:t+1])))) for k,actor in [('box','parcel_box'),('mailer','mailer')]})
   observed={k:v[t].tolist() for k,v in tr.items()};proposal=z['action'][t].copy();coord=copy.deepcopy(coordinates[t])
   scope.update(step=t,robot=robot,env=env,snap=lambda *unused:observed,expert=NS(mode=control[t]['mode'],last_target_xyz=control[t]['target_xyz']),coordination_log=[coord],solved_contact_forces=[forces[t-1]],previous=z['action'][t-1].copy(),action=proposal.copy())
   exec(block,scope)
   np.testing.assert_array_equal(scope['action'][:12],proposal[:12])
   if scope['terminal_hold_log'][-1]['held']:
    first=t;np.testing.assert_array_equal(scope['action'][12:],z['action'][t-1,12:]);assert coord['waist_target_rad']==float(z['action'][t-1,12])
    # A new front guard must revoke the held action instead of masking it.
    scope['expert'].mode='front_guard_lift';scope['action']=proposal.copy();exec(block,scope)
    assert not scope['terminal_hold_log'][-1]['held'];np.testing.assert_array_equal(scope['action'],proposal);guard_revocation=True
    break
  assert first==expected,(ep.name,first,expected)
  results.append(dict(episode=ep.name,first_hold_frame=first,guard_revocation_checked=guard_revocation,raw_sha256=hashlib.sha256((ep/'raw.npz').read_bytes()).hexdigest()))
manifest=json.loads((stage/'MANIFEST.json').read_text())
for p,h in manifest['source_sha256'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,p
(stage/'CLI_AND_REPLAY_CHECK.json').write_text(json.dumps(dict(cli=cli,recorded_replays=results,candidate_sha256=manifest['candidate_sha256'],live_source_unchanged=True,scope='Actual isolated parser/hold measurement and command-override AST; CPU torch + independent URDF FK with measured raw/trace/force/coordination. Tests first trigger, exact previous command, lower12 unchanged, and emergency revocation. No Isaac or executed held dynamics.',training_ready=False),indent=2));print(json.dumps(dict(cli=cli,recorded_replays=results),indent=2))
