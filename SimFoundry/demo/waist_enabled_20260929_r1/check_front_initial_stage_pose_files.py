"""Combined rear-parent/front-initial native pose audit, explicitly synthetic.
Actual source/diff checked. Fixtures test file/command/capture/normal interfaces;
no runtime body/substep physics, task quality, images or training admission.
"""
from pathlib import Path
import ast,sys,json,hashlib,datetime,copy,tempfile
from unittest.mock import patch
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_initial_center';sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from front_initial_center_lifecycle_v3 import FrontInitialCenterLifecycle
from audit_front_initial_center_events import EventAudit
from audit_front_initial_stage_pose_live import verify_files
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
guard=ClearanceGuard(ROOT,S);independent=EventAudit(ROOT,S)
builder=W/'check_front_initial_center_native_v2.py';tree=ast.parse(builder.read_text());body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['put','normal_record','make']];assert len(body)==3
exec(compile(ast.Module(body=body,type_ignores=[]),str(builder),'exec'))
out=W/'FRONT_INITIAL_STAGE_POSE_FILES_CHECK.json';assert not out.exists()
preparation=json.loads((W/'FRONT_INITIAL_STAGE_AUDITS_PREPARATION.json').read_text())
report=dict(status='running',scope=__doc__,cases=[],simulation_started=False,training_ready=False,source_sha256={str(p):sha(p) for p in [Path(__file__),builder,W/'FRONT_INITIAL_STAGE_AUDITS_PREPARATION.json']})
def save():report['updated_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();out.write_text(json.dumps(report,indent=2))
try:
 for item in preparation['adapters']:
  text=Path(item['parent']).read_text();assert sha(item['parent'])==item['parent_sha256']
  for old,new in preparation['global_replacements']:text=text.replace(old,new)
  for e in item['edits']:
   if e.get('kind'):continue
   assert text.count(e['old'])==1;text=text.replace(e['old'],e['new'])
  if item['path'].endswith('/front_initial_stage_audit_context.py'):
   assert Path(item['path']).read_text().startswith(text)
  else:assert Path(item['path']).read_text()==text
  assert sha(item['path'])==item['sha256']
 report['all_six_source_diffs_bound']=True;save()
 data=json.loads((W/'FRONT_INITIAL_CENTER_SELECTION_CHECK.json').read_text())
 with tempfile.TemporaryDirectory(prefix='combined-pose-fixture-') as tmp:
  for original in [r for r in data['records'] if '840023' in r['episode'] or '840016' in r['episode']]:
   ep=Path(tmp)/original['episode'];obj=make(ep,original);fr=json.loads((ep/'frontal_bypass.json').read_text());coords=json.loads((ep/'coordination.json').read_text());experts=json.loads((ep/'expert_control.json').read_text())
   with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].copy();u=z['action'][:,12:23].copy()
   put(ep,'recontact_pose.json',dict(rows=[],training_ready=False));holds=[];final=[]
   for t in range(1200):
    final.append(dict(step=t,phase='final_command',accepted=True,command=u[t].tolist(),current=q[t].tolist(),previous=u[max(0,t-1)].tolist()))
    if t==0:continue
    holds.append(dict(step=t,held=False,output_upper_command=u[t].tolist(),previous_upper_command=u[t-1].tolist(),current_upper_q=q[t].tolist()))
    ev=obj['verified'].get(t)
    if ev:
     row=fr['rows'][t-1];row['front_initial_center_phase']='measured_handover' if ev['kind']=='handover' else 'tracking'
     if ev['kind']=='handover':
      row.update(target_xyz=ev['observed_support_xyz'],observed_support_xyz=ev['observed_support_xyz'],projected_support_reference=ev['reference'],control_offset_local=ev['reference']['reference_local'],push_x_anchor_m=None,approach_xy_bias_m=[0.,0.])
      experts[t]['target_xyz']=ev['observed_support_xyz'];coords[t-1]['active_support_reference']=ev['reference'];coords[t-1]['control_point_positions']={obj['side']:ev['observed_support_xyz']}
   put(ep,'frontal_bypass.json',fr);put(ep,'coordination.json',coords);put(ep,'expert_control.json',experts);put(ep,'terminal_joint_hold.json',dict(rows=holds));put(ep,'self_clearance.json',dict(failure=None,requested_frames=1200,recorded_frames=1200,rows=final))
   r=verify_files(ep,S);assert r['passed'] and r['frames']==1200 and r['command_events']==0
   assert len(r['front_records'])==len(obj['verified'])
   report['cases'].append(dict(episode=original['episode'],passed=True,frames=r['frames'],front_commands=len(r['front_records']),front_handovers=r['front_result']['handovers'],original_normal_frames=r['normal']['normal_frames'],jacobian_samples=r['normal']['jacobian_samples'],fixture_only=True));save();print(original['episode'],'combined pose fixture passed',flush=True)
 report.update(status='complete',passed=True);save()
except Exception as e:report.update(status='failed',error=repr(e));save();raise
