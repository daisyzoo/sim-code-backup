"""Check isolated stage CLI and actual recorded adapter inputs; no simulation."""
from pathlib import Path
import sys,json,hashlib,datetime,contextlib,io
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_joint_edge_clearance_intersection';R=W/'fresh_closed_peak_trials_r1';sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from joint_edge_clearance_adapter_candidate import repair_record
from prepare_closed_peak_trial import parser_namespace
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
prep=json.loads((S/'PREPARATION.json').read_text());assert all(sha(S/n)==h for n,h in prep['stage_sha256'].items());out=S/'CHECK.json';assert not out.exists();guard=ClearanceGuard(ROOT,S)
# Exact parent diagnostic settings, with the new switch as the sole addition.
parent=json.loads((W/'peak_guard_groups_r1/PROTOCOL.json').read_text());base=list(parent['commands'][0]['args']);base+=['--out-dir','/tmp/edge_intersection_CLI_NO_SIMULATION'];tests=[]
def cli(name,args,expect):
 try:
  with contextlib.redirect_stderr(io.StringIO()):settings,launcher=parser_namespace(S/'collect_paired_sorting.py',args,full=True)
  success=True
 except SystemExit as ex:
  success=ex.code==0
 assert success==expect,(name,success);tests.append(dict(name=name,accepted=success))
 return settings if success else None
before=cli('default_off',base,True);on=cli('enabled_original_diagnostic',base+['--edge-clearance-intersection'],True);assert before['edge_clearance_intersection'] is False and on['edge_clearance_intersection'] is True
assert {k:v for k,v in before.items() if k!='edge_clearance_intersection'}=={k:v for k,v in on.items() if k!='edge_clearance_intersection'}
for flag in ['--rear-joint-edge-command','--rear-box-inward-correction','--self-clearance-task-ik','--trace-substep-contacts']:
 a=base.copy();a.remove(flag);cli('reject_missing_'+flag,a+['--edge-clearance-intersection'],False)
a=base.copy();a[a.index('--role')+1]='pilot';cli('reject_pilot',a+['--edge-clearance-intersection'],False)
for flag in ['--idle','--waist-probe']:
 cli('reject_'+flag,base+['--edge-clearance-intersection',flag],False)
records=[];count=unchanged=0;changes=[];sources={}
for layout in range(840000,840016):
 for ep in sorted((R/f'case_{layout}').glob('layout_*')):
  coords=json.loads((ep/'coordination.json').read_text());fr=json.loads((ep/'frontal_bypass.json').read_text());fs={v['step']:v for v in fr['rows']};qual=json.loads((ep/'quality.json').read_text());side='right' if 'push_box' in ep.name else 'left';key='box' if side=='right' else 'mailer';ec=eu=0;changed=[]
  with np.load(ep/'parcel_orientation.npz') as z:rotations=Rotation.from_quat(z[key]).as_matrix()
  for c in coords:
   tr=c.get('joint_edge_refinement')
   if not tr or not tr.get('override'):continue
   t=c['step'];f=fs[t];core=fr['plan']['region_causal_response']['actual_core']['collision_core_size_xyz']
   if t<len(rotations):rot=rotations[t]
   else:
    with np.load(ep/'substep_contacts.npz') as z:
     i=int(np.flatnonzero(z['action_step']==t-1)[-1]);rot=Rotation.from_quat(z['body_q'][i,0 if side=='right' else 1,3:]).as_matrix()
    sources[str(ep/'substep_contacts.npz')]=sha(ep/'substep_contacts.npz')
   inputs=dict(guard=guard,row=f,coordinate=c,current=c['upper_q'],previous=tr['previous_upper_command'],command=tr['final_upper_command'],object_rotation=rot,object_xyz=f['observed_target'],core_size=core)
   x,trace=repair_record(**inputs);assert x is not None,(ep,t,trace);count+=1;ec+=1
   if trace['changed']:
    changes.append(dict(episode=ep.name,step=t,output=x.tolist(),trace=trace));changed.append(t);failure_inputs=inputs
   else:assert np.array_equal(x,np.asarray(tr['final_upper_command']));unchanged+=1;eu+=1
  records.append(dict(episode=ep.name,overrides=ec,unchanged=eu,changed_steps=changed))
  for name in ['coordination.json','frontal_bypass.json','quality.json','parcel_orientation.npz']:sources[str(ep/name)]=sha(ep/name)
 assert len([x for x in records if x['episode'].startswith(f'layout_{layout}_')])==2
assert len(records)==32 and count==352 and unchanged==351 and len(changes)==1
probe=R/'case_840015/layout_840015_push_box_to_bin/JOINT_EDGE_CLEARANCE_INTERSECTION_PROBE.json';pr=json.loads(probe.read_text());assert all(np.array_equal(changes[0]['output'],a['candidate_q']) and a['passed'] for a in pr['records'])
# A mislabeled/shifted record must not be used to certify a repair.
neg=[]
for key,value in [('command',np.zeros(11)),('previous',np.zeros(11)),('current',np.zeros(11)),('object_rotation',np.zeros((3,3)))]:
 bad=dict(failure_inputs);bad[key]=value
 try:repair_record(**bad)
 except ValueError:neg.append(key)
 else:raise AssertionError(('bad record accepted',key))
for p in [Path(__file__),S/'PREPARATION.json',probe,*[S/n for n in prep['stage_sha256']]]:sources[str(p)]=sha(p)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,cli_tests=tests,episodes=records,edge_overrides=count,unchanged_commands=unchanged,changes=changes,negative_record_checks=neg,independent_probe_command_matches=True,source_sha256=sources,simulation_started=False,training_ready=False)
with out.open('x') as f:json.dump(report,f,indent=2)
print(json.dumps({k:v for k,v in report.items() if k not in ['episodes','changes','source_sha256']},indent=2))
