"""Minimal explicit software corruption fixtures; no physical demonstration."""
from pathlib import Path
import json,sys,tempfile,subprocess,copy,hashlib
import numpy as np
w=Path(__file__).resolve().parent
results=[]
with tempfile.TemporaryDirectory(prefix='region_auditor_fixtures_') as td:
 p=Path(td);q=np.zeros((2,23));act=q.copy();act[1,12:]=.001
 solver=dict(accepted=True,inside_10mm_inset=True,next_q=[.001]*11,reached=False,top_gap_m=.04,joint_override=True,handover=False,runtime_fk_check={k:dict(position_max_error_m=0.,rotation_max_error=0.) for k in ['left','right']})
 for kind in ['valid','wrong_action','over_step','false_handover','nan_action','nan_nextq','excluded_route','missing_region_record']:
  a=act.copy();ss=copy.deepcopy(solver);plan={'region_approach':{'enabled':True}}
  if kind=='wrong_action':a[1,13]=.01
  if kind=='over_step':ss['next_q'][1]=.06;a[1,13]=.055
  if kind=='false_handover':ss.update(reached=True,handover=True)
  if kind=='nan_action':a[1,13]=float('nan')
  if kind=='nan_nextq':ss['next_q'][1]=float('nan')
  if kind=='excluded_route':plan['front_route_selected']=True
  np.savez(p/'raw.npz',q=q,action=a,collect_meta=json.dumps({'assist_frames':0}))
  (p/'frontal_bypass.json').write_text(json.dumps({'plan':plan,'rows':[{'step':1,'projected_support_reference':{'fixture':True}}]}))
  (p/'coordination.json').write_text(json.dumps([dict(step=1,region_joint_override=ss,terminal_joint_hold=False)]))
  (p/'region_approach.json').write_text(json.dumps({'rows':[] if kind=='missing_region_record' else [dict(step=1,solver=ss,selected_surface_local_xy=None,mode='top_descend',abort_reason=None)]}))
  ret=subprocess.run([sys.executable,str(w/'audit_region_action_live_r2.py'),str(p)],capture_output=True,text=True)
  assert (ret.returncode==0)==(kind=='valid'),(kind,ret.stdout,ret.stderr)
  results.append(dict(fixture=kind,passed_or_rejected_as_expected=True,returncode=ret.returncode))
report=dict(rows=results,auditor_sha256=hashlib.sha256((w/'audit_region_action_live_r2.py').read_bytes()).hexdigest(),scope='Explicit software fixtures verify actual auditor rejection of wrong action, oversized step, false handover, NaNs and excluded routes. Does not prove physical correctness or success.',training_ready=False)
(w/'region_patch_groups_r1/ACTION_AUDITOR_CHECK_R2.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
