"""Check unwired fraction candidate against native original and archived contexts.
No simulation, full-episode replay, or final downstream transport is claimed.
"""
from pathlib import Path
import sys,json,copy,hashlib,datetime
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_corridor_lateral_v1';D=W/'front_loaded_z_fraction_candidate_v1';sys.path[:0]=[str(D),str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from front_loaded_z_priority import FrontLoadedZPriority
from front_loaded_z_fraction import FrontLoadedZFraction
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
guard=ClearanceGuard(ROOT,S);native=FrontLoadedZPriority(guard);full=FrontLoadedZFraction(guard);quarter=FrontLoadedZFraction(guard,.25);rows=[];sources={}
probe=read(W/'front_loaded_z_fraction_probe_r1/RESULT.json')
for r in probe['rows']:
 if r['fraction']!=.25:continue
 ep=W/r['run']/'case_840023/layout_840023_nudge_mailer_to_bin';t=r['step'];co=next(c for c in read(ep/'coordination.json') if c['step']==t);fr=next(c for c in read(ep/'frontal_bypass.json')['rows'] if c['step']==t);ctx=co['front_loaded_z_priority']['context'];co['front_loaded_z_priority_side']='left'
 args=dict(step=t,selected=True,row=fr,coordinate=co,**{k:ctx[k] for k in ['current','previous','parent_command','target_rotation','other_xyz','other_rotation','other_size']});before=copy.deepcopy(args)
 x0,m0=native.refine(**args);x1,m1=full.refine(**args);np.testing.assert_array_equal(x0,x1);assert m0==m1;np.testing.assert_array_equal(x0,co['front_loaded_z_priority']['output_command'])
 xq,mq=quarter.refine(**args);assert mq['applied'];np.testing.assert_array_equal(xq,r['command']);assert args==before;assert mq['reduced_z_task']['original_task']==co['task_inputs'];assert mq['context']['requested_z_m']==ctx['requested_z_m']
 off=copy.deepcopy(args);off['selected']=False;xo,mo=quarter.refine(**off);xn,mn=native.refine(**off);np.testing.assert_array_equal(xo,xn);assert mo==mn
 rows.append(dict(run=r['run'],step=t,default_exact_command_and_metadata=True,quarter_exact_probe_match=True,disabled_exact_native=True,input_not_mutated=True));print(json.dumps(rows[-1]),flush=True)
 for n in ['coordination.json','frontal_bypass.json']:sources[str(ep/n)]=sha(ep/n)
rejected=0
for value in [True,False,0.,-.1,1.1,float('nan'),float('inf')]:
 try:FrontLoadedZFraction(guard,value)
 except ValueError:rejected+=1
 else:raise AssertionError('invalid fraction accepted')
for mod in list(sys.modules.values()):
 f=getattr(mod,'__file__',None)
 if f:
  p=Path(f).resolve()
  if p.is_file() and p.suffix=='.py' and p.is_relative_to(ROOT):sources[str(p)]=sha(p)
for p in [Path(__file__),W/'front_loaded_z_fraction_probe_r1/RESULT.json',S/'elbow_torso_hulls.json',ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',ROOT/'assets/robots/g1_hand_support_vertices.json']:sources[str(p)]=sha(p)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,invalid_parameters_rejected=rejected,source_sha256=sources,passed=True,collector_integrated=False,full_controller_audited=False,physics_started=False,training_ready=False)
with (D/'NATIVE_CONTEXT_CHECK.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(passed=True,contexts=len(rows),invalid_parameters_rejected=rejected)),flush=True)
