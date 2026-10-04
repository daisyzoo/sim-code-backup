"""Unwired whole-refinement replay: all8 historical contexts, no physical commands.
Outer measured-margin calls use ORIGINAL full projections exactly. Only the
continuous certify method uses bounded cache/fallback. Same solver, contact
certificate, precedence and returned commands. First context has paired timing.
"""
from pathlib import Path
import sys,json,hashlib,datetime,time
import numpy as np
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];S=W/'staged_joint_transport_v1';sys.path[:0]=[str(D),str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from joint_transport_runtime import JointTransportRuntime
from joint_transport_paths import JointTransportPaths
from bounded_support_paths_v1 import BoundedSupportPaths
class PathsProxy:
 def __init__(self):self.original=JointTransportPaths(ROOT,S);self.bounded=BoundedSupportPaths(ROOT,S)
 def margins(self,*args):return self.original.margins(*args)
 def certify(self,*args):return self.bounded.certify(*args)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={};rows=[];guard=ClearanceGuard(ROOT,S);runtime=JointTransportRuntime(guard,ROOT,S,enabled=True);runtime.paths=PathsProxy();original=JointTransportRuntime(guard,ROOT,S,enabled=True)
def read(p):sources[str(p)]=sha(p);return json.loads(p.read_text())
checks=read(D/'BOUNDED_SUPPORT_PATH_CHECK.json');assert checks['passed']
for p,h in checks['source_sha256'].items():assert sha(p)==h,p
refs=read(W/'joint_transport_runtime_preparation_r1/RUNTIME_CONTEXT_CHECK.json')
for i,item in enumerate(refs['contexts']):
 reference=read(Path(item['record']));t=item['step'];ep=W/'inactive_transport_physical_r1'/('case_840023/layout_840023_nudge_mailer_to_bin' if item['side']=='left' else 'case_840020/layout_840020_push_box_to_bin');p=read(ep/'inactive_transport_clearance.json')['rows'][t]['proposal'];coordinate={r['step']:r for r in read(ep/'coordination.json')}[t];front={r['step']:r for r in read(ep/'frontal_bypass.json')['rows']}[t];scene=RecontactScene(guard,**p['scene']);args=dict(step=t,selected=True,side=p['scene']['side'],row=front,coordinate=coordinate,scene=scene,**{k:p[k] for k in ['current','previous_q','previous_command','parent_command','decay']})
 original_time=None
 if i==0:
  start=time.perf_counter();oc,orr=original.refine(**args);original_time=time.perf_counter()-start;np.testing.assert_array_equal(oc,reference['output_command']);assert orr['certificate']==reference['certificate'] and orr['paths']==reference['paths']
 start=time.perf_counter();command,record=runtime.refine(**args);elapsed=time.perf_counter()-start;assert record['applied'];np.testing.assert_array_equal(command,reference['output_command']);assert record['proposal']==reference['proposal'] and record['certificate']==reference['certificate']
 for kind in ['nominal','predicted']:
  a,b=record['paths'][kind],reference['paths'][kind];assert a['passed']==b['passed']==True and a['nodes']==b['nodes'] and a['max_depth']==b['max_depth'] and [r['interval'] for r in a['leaves']]==[r['interval'] for r in b['leaves']]
 file=D/f"BOUNDED_CONTEXT_{item['side']}_{t}.json"
 with file.open('x') as f:json.dump(record,f,indent=2)
 row=dict(side=item['side'],step=t,command_bit_identical=True,solver_proposal_and_contact_certificate_exact=True,outer_measured_geometry_original=True,bounded_refinement_elapsed_s=elapsed,paired_original_elapsed_s=original_time,paired_speedup=None if original_time is None else original_time/elapsed,record=str(file),record_sha256=sha(file));rows.append(row);print(json.dumps(row),flush=True)
for mod in list(sys.modules.values()):
 f=getattr(mod,'__file__',None)
 if f:
  p=Path(f).resolve()
  if p.is_file() and p.suffix=='.py' and p.is_relative_to(ROOT):sources[str(p)]=sha(p)
for p in [Path(__file__),D/'SUPPORT_ERROR_BOUND.md',S/'elbow_torso_hulls.json',ROOT/'assets/robots/g1_hand_support_vertices.json',ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf']:sources[str(p)]=sha(p)
assert len(rows)==8
with (D/'BOUNDED_REFINEMENT_CHECK.json').open('x') as f:json.dump(dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,contexts=rows,source_sha256=sources,physical_execution=False,production_integrated=False,training_ready=False),f,indent=2)
print('ALL8_UNWIRED_REFINEMENTS_COMPLETE',flush=True)
