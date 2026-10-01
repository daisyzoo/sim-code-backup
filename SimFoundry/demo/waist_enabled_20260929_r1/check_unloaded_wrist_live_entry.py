"""Actual collector/coordinator AST and independent CLI on counterfactual fixtures.
Recorded q/previous-action inputs remain historical; proposed next actions DO NOT
feed later states. These fixtures are not rollouts, task successes or training.
"""
from pathlib import Path
import sys,ast,json,copy,types,hashlib,tempfile,subprocess
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_unloaded_wrist_prior';sys.path[:0]=[str(stage),str(w),str(repo)]
from task_ik import solve
from clearance_runtime import ClearanceGuard
from audit_unloaded_wrist_prior_live import HandModel,verify_record
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();guard=ClearanceGuard(repo,stage);independent=HandModel(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json')
tree=ast.parse((stage/'collect_paired_sorting.py').read_text());b=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test).startswith('args.unloaded_wrist_prior and frontal_plan'));collect=compile(ast.Module(body=[b],type_ignores=[]),'<actual collector context>','exec')
tree=ast.parse((stage/'waist_coordination_clearance.py').read_text());b=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='wrist_prior_context is not None');coordinate=compile(ast.Module(body=[b],type_ignores=[]),'<actual coordinator>','exec')
class Tensor:
 def __init__(self,x):self.x=np.asarray(x)
 def __getitem__(self,i):return Tensor(self.x[i])
 def detach(self):return self
 def cpu(self):return self
 def numpy(self):return self.x
root=Path(tempfile.mkdtemp(prefix='unloaded_wrist_counterfactual_'));(root/'FIXTURE_SCOPE.md').write_text(__doc__);out=[];negative_sample=None
parent=w/'rear_short_recovery_groups_r1'
for original in sorted(parent.glob('case_*/layout_*')):
 if 'wait' in original.name:continue
 case=root/original.parent.name;ep=case/original.name;ep.mkdir(parents=True,exist_ok=False);prov=json.loads((original.parent/'provenance.json').read_text());oldstage='demo/waist_enabled_20260929_r1/staged_rear_short_recovery';newstage='demo/waist_enabled_20260929_r1/staged_unloaded_wrist_prior';source={}
 for n,h in prov['source_sha256'].items():
  new=n.replace(oldstage,newstage);path=(repo/new) if n.startswith(oldstage+'/') else original.parent/'source_snapshot'/n;dst=case/'source_snapshot'/new;dst.parent.mkdir(parents=True,exist_ok=True)
  if not dst.exists():dst.symlink_to(path.resolve())
  source[new]=sha(path)
 for name in ['unloaded_wrist_prior.py','unloaded_wrist_task.py']:
  new=newstage+'/'+name;dst=case/'source_snapshot'/new
  if not dst.exists():dst.symlink_to((stage/name).resolve())
  source[new]=sha(stage/name)
 prov['source_sha256']=source;prov['args']['unloaded_wrist_prior']=True;(case/'provenance.json').write_text(json.dumps(prov))
 with np.load(original/'raw.npz') as z:q=z['q'].copy();u=z['action'].copy();task=str(z['task_id']);meta=json.loads(str(z['collect_meta']))
 meta['unloaded_wrist_prior']=True;meta['counterfactual_fixture_not_physics']=True;np.savez_compressed(ep/'raw.npz',q=q,action=u,task_id=task,collect_meta=json.dumps(meta))
 for name in ['frontal_bypass.json','expert_control.json','self_clearance.json']:(ep/name).symlink_to((original/name).resolve())
 fr=json.loads((ep/'frontal_bypass.json').read_text());coords=json.loads((original/'coordination.json').read_text());cs={c['step']:c for c in coords};side='right' if 'push_box' in original.name else 'left';selected=bool(fr['plan'].get('rear_joint_xy_progress',{}).get('enabled'));applied=0;eligible=0
 for f in fr['rows']:
  t=f['step'];c=cs[t];inp=c['task_inputs'];T=guard.model.fk(side,np.array(inp['current']))[0];quat=Rotation.from_matrix(T[:3,:3]).as_quat().astype(np.float32);xyz=T[:3,3].astype(np.float32);robot=types.SimpleNamespace(data=types.SimpleNamespace(body_pos_w=types.SimpleNamespace(torch=Tensor([[xyz]])),body_quat_w=types.SimpleNamespace(torch=Tensor([[quat]]))))
  ns=dict(args=types.SimpleNamespace(unloaded_wrist_prior=False),frontal_plan=fr['plan'],frontal_log=[f],robot=robot,hands={side:0},side=side,np=np,support_mesh=lambda:guard.model.vertices,expert=types.SimpleNamespace(mode=f['mode']),clearance_kwargs={});exec(collect,ns);assert not ns['clearance_kwargs'];ns['args'].unloaded_wrist_prior=True;exec(collect,ns);context=ns['clearance_kwargs'].get('wrist_prior_context')
  candidate_eligible=context is not None and selected and f['mode'] in ['top_lift','top_cross'] and f['recontacts']>0 and context['observed_load_n']==0 and 0<=context['filtered_load_n']<=.05 and context['min_hand_z_m']>=.84
  baseline=solve(enabled=True,geometry=guard.geometry,**inp) if candidate_eligible else (np.array(inp['previous']),copy.deepcopy(c['self_clearance_task']))
  ns=dict(wrist_prior_context=context,target=baseline[0],clearance_record=baseline[1],task_inputs=copy.deepcopy(inp),clearance_geometry=guard.geometry);exec(coordinate,ns);c['self_clearance_task']=ns['clearance_record'];c['task_inputs']=ns['task_inputs'];verified=verify_record(q[t,12:23].astype(float),c,f,selected,side,independent);eligible+=verified['eligible'];applied+=verified['applied']
  if verified['applied'] and negative_sample is None:negative_sample=copy.deepcopy((q[t,12:23].astype(float),c,f,selected,side))
 (ep/'coordination.json').write_text(json.dumps(coords));call=subprocess.run([sys.executable,str(w/'audit_unloaded_wrist_prior_live.py'),str(ep)],capture_output=True,text=True);(ep/'audit_cli.log').write_text(call.stdout+call.stderr);assert call.returncode==0,(ep,call.stderr);report=json.loads((ep/'UNLOADED_WRIST_PRIOR_LIVE_AUDIT.json').read_text());assert report['frames']==1199 and report['applied_frames']==applied
 out.append(dict(episode=ep.name,frames=1199,eligible=eligible,applied=applied,cli_passed=True,fixture=str(ep),original_sha256={n:sha(original/n) for n in ['raw.npz','coordination.json','frontal_bypass.json']},fixture_report_sha256=sha(ep/'UNLOADED_WRIST_PRIOR_LIVE_AUDIT.json')));print(ep.name,eligible,applied,flush=True)
negatives=[]
for name in ['height','position','loaded','mode','initial','prior','other_joint_prior','task_error','false_fallback','command']:
 q,c,f,selected,side=copy.deepcopy(negative_sample);c=json.loads(json.dumps(c));f=json.loads(json.dumps(f));r=c['self_clearance_task']['unloaded_wrist_prior'];ctx=r['context']
 if name=='height':ctx['min_hand_z_m']+=.01
 if name=='position':ctx['hand_position_world'][0]+=.01
 if name=='loaded':ctx['observed_load_n']=1.
 if name=='mode':ctx['mode']='top_push'
 if name=='initial':ctx['recontacts']=0
 if name=='prior':c['task_inputs']['preferred_step'][r['wrist_index']]=0.
 if name=='other_joint_prior':c['task_inputs']['preferred_step'][1]=.01
 if name=='task_error':r['attempted_task_inputs']['error'][0]+=.01
 if name=='false_fallback':r['applied']=False
 if name=='command':r['attempted_command'][r['wrist_index']]+=.1
 rejected=False
 try:verify_record(q,c,f,selected,side,independent)
 except (AssertionError,ValueError):rejected=True
 assert rejected,name;negatives.append(dict(case=name,rejected=True))
report=dict(passed=True,scope=__doc__,episodes=out,total_frames=sum(x['frames'] for x in out),eligible_frames=sum(x['eligible'] for x in out),applied_frames=sum(x['applied'] for x in out),negative_checks=negatives,fixtures=str(root),source_sha256={str(p):sha(p) for p in [Path(__file__),w/'audit_unloaded_wrist_prior_live.py',stage/'collect_paired_sorting.py',stage/'waist_coordination_clearance.py',stage/'unloaded_wrist_prior.py',stage/'unloaded_wrist_task.py',stage/'INTEGRATION_CHECK.json',stage/'RECORDED_WRAPPER_REPLAY.json']},physical_validation=False,training_ready=False)
(stage/'LIVE_ENTRY_CHECK.json').write_text(json.dumps(report,indent=2));print('passed8CLIpositive10negative; actual collector/coordinator contexts all9592')
