"""Saved-context runtime validation only. Proposals never sent to physics.
Actual historical states are inputs; historical next states are never claimed
as responses to these new commands. Includes control precedence and stale-input
rejection before the positive left/right contexts.
"""
from pathlib import Path
import sys,json,hashlib,datetime,copy,ast
import numpy as np
W=Path(__file__).resolve().parent;S=W/'staged_joint_transport_v1';ROOT=W.parents[1];D=W/'joint_transport_runtime_preparation_r1'
sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from joint_transport_runtime import JointTransportRuntime
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
sources={str(p):sha(p) for p in S.iterdir() if p.suffix in ['.py','.json']}
sources[str(Path(__file__))]=sha(__file__)
def read(p):sources[str(p)]=sha(p);return json.loads(p.read_text())
def main():
 D.mkdir(exist_ok=True);assert not (D/'RUNTIME_CONTEXT_CHECK.json').exists()
 ref=read(W/'joint_transport_feasibility_probe_r4/RESULT.json')
 for p,h in ref['source_sha256'].items():assert sha(p)==h
 G=ClearanceGuard(ROOT,S);runtime=JointTransportRuntime(G,ROOT,S,enabled=True);disabled=JointTransportRuntime(G,ROOT,S)
 contexts=[]
 for result in ref['results']:
  t=result['step'];ep=W/'inactive_transport_physical_r1'/('case_'+result['episode'].split('_')[1])/result['episode'];p=read(ep/'inactive_transport_clearance.json')['rows'][t]['proposal'];coordinate={r['step']:r for r in read(ep/'coordination.json')}[t];row={r['step']:r for r in read(ep/'frontal_bypass.json')['rows']}[t];z=p['scene'];scene=RecontactScene(G,z['side'],z['target_xyz'],z['target_quat'],z['core_size'],z['other_xyz'],z['other_quat'],z['other_size'])
  with np.load(ep/'raw.npz') as raw:
   np.testing.assert_allclose(raw['q'][t,12:23],p['current'],atol=1e-7,rtol=0);np.testing.assert_allclose(raw['q'][t-1,12:23],p['previous_q'],atol=1e-7,rtol=0);np.testing.assert_array_equal(raw['action'][t-1,12:23],p['previous_command'])
  sources[str(ep/'raw.npz')]=sha(ep/'raw.npz')
  args=dict(step=t,selected=True,side=z['side'],row=row,coordinate=coordinate,scene=scene,current=p['current'],previous_q=p['previous_q'],previous_command=p['previous_command'],parent_command=p['parent_command'],decay=p['decay']);contexts.append((result,args))
 controls=[];base=contexts[0][1]
 for name,controller,changes,expected in [
  ('default_off',disabled,{},'disabled'),('not_captured',runtime,{'selected':False},'not_captured_front_transport'),('first_frame',runtime,{'step':0},'not_captured_front_transport'),
  ('path_precedence',runtime,{'coordinate':dict(base['coordinate'],front_initial_center_override={})},'original_joint_path_has_precedence'),
  ('terminal_precedence',runtime,{'coordinate':dict(base['coordinate'],terminal_joint_hold=True)},'terminal_hold_has_precedence'),
  ('route_stop_precedence',runtime,{'row':dict(base['row'],route_stop_reason='fixture_original_stop')},'parent_stop_or_guard')]:
  out,record=controller.refine(**dict(base,**changes));assert not record['applied'] and record['reason']==expected;np.testing.assert_array_equal(out,base['parent_command']);controls.append(dict(name=name,passed=True,reason=record['reason']))
 for name,changes in [('stale_current',{'current':(np.array(base['current'])+.001).tolist()}),('stale_previous_action',{'previous_command':(np.array(base['previous_command'])+.001).tolist()}),('wrong_side',{'side':'right'}),('unbound_parent',{'parent_command':(np.array(base['parent_command'])+.001).astype(np.float32).tolist()}),('missing_previous_state',{'previous_q':None}),('invalid_decay',{'decay':[1.0]*11})]:
  try:runtime.refine(**dict(base,**changes))
  except (ValueError,AssertionError) as e:controls.append(dict(name=name,passed=True,rejected=type(e).__name__))
  else:raise AssertionError('Expected rejection: '+name)
 tree=ast.parse((S/'collect_paired_sorting.py').read_text());hook=[n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='args.joint_transport_clearance'];assert len(hook)==4
 # Check the original final guard still occurs immediately after the new hook.
 src=(S/'collect_paired_sorting.py').read_text();pos=src.index('        if args.joint_transport_clearance:\n');end=src.index('        if clearance_guard is not None:\n',pos);assert 'joint_transport_unexecuted_parent_waist_target_rad' in src[pos:end] and "coordination_log[-1]['waist_target_rad']=float(transport_command[0])" in src[pos:end]
 print(json.dumps(dict(controls_passed=len(controls),collector_hook_checked=True)),flush=True)
 rows=[]
 for reference,args in contexts:
  command,record=runtime.refine(**args);assert record['applied'],(args['step'],record['reason'])
  np.testing.assert_array_equal(command,reference['command'])
  assert record['certificate']['passed'] and all(v['passed'] for v in record['paths'].values())
  record.update(scope='Unissued proposal on an actual historical context only; no physical response inferred.',physical_command_issued=False)
  file=D/f"CONTEXT_{args['side']}_{args['step']}.json"
  with file.open('x') as f:json.dump(record,f,indent=2)
  rows.append(dict(step=args['step'],side=args['side'],passed=True,reference_command_bit_identical=True,record=str(file),record_sha256=sha(file),stationarity=record['certificate']['certificate']['stationarity_residual']))
  print(json.dumps(rows[-1]),flush=True)
 for p,h in sources.items():assert sha(p)==h,p
 report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,contexts=rows,controls=controls,source_sha256=sources,physical_commands_issued=False,full_stream_audit_ready=False,training_ready=False)
 with (D/'RUNTIME_CONTEXT_CHECK.json').open('x') as f:json.dump(report,f,indent=2)
if __name__=='__main__':main()
