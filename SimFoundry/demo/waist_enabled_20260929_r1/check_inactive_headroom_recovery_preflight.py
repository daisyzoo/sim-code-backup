"""Causal-hypothesis recovery planning after two UNISSUED inactive lift proposals.
Inputs at405/528 are actual; the next q is a declared affine prediction, parcels
held at the observed pose. Planning/preflight success is NOT actual transport,
recovery handover, new trajectory, accepted episode, or training evidence.
"""
from pathlib import Path
import datetime,hashlib,json,sys
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_recontact_headroom';D=W/'inactive_hand_headroom_draft_r1';sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from front_recontact_center_selection import plan
from audit_front_initial_center_planning_v2 import SelectionAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();bound=json.loads((D/'ACTUAL_CONTEXT_PROPOSAL_CHECK.json').read_text());assert bound['passed']
for p,h in bound['source_sha256'].items():assert sha(p)==h,p
R=W/'front_recontact_headroom_physical_r1';ep=R/'case_840023/layout_840023_nudge_mailer_to_bin';events={e['step']:e for e in json.loads((ep/'front_recontact_center.json').read_text())['rows']};guard=ClearanceGuard(ROOT,S);audit=SelectionAudit(ROOT,S)
out=D/'RECOVERY_PREFLIGHT_CHECK.json';assert not out.exists();report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,status='running',records=[],source_sha256=dict(bound['source_sha256'],**{str(D/'ACTUAL_CONTEXT_PROPOSAL_CHECK.json'):sha(D/'ACTUAL_CONTEXT_PROPOSAL_CHECK.json'),str(Path(__file__)):sha(__file__)}),collector_integrated=False,physical_started=False,training_ready=False)
def save():out.write_text(json.dumps(report,indent=2))
save()
try:
 for v in bound['records']:
  if not v['proposal']['applied']:continue
  t=v['step'];c=events[t]['context'];s=c['scene'];scene=RecontactScene(guard,s['side'],s['target_xyz'],s['target_quat'],s['core_size'],s['other_xyz'],s['other_quat'],s['other_size']);p=v['proposal'];pred=np.asarray(p['predicted_q']);geom,_=audit.geometry(pred,s);assert geom['accepted'] and geom['inactive_lowest_z_m']>=.841
  result=plan(scene,pred,step=t+1,previous_q=c['current'],previous_command=p['command'],decay=c['decay'],recontact_index=c['recontacts'])
  report['records'].append(dict(original_step=t,counter=c['recontacts'],hypothetical_next_geometry=geom,planning=result));save();print(t,result['accepted'],result.get('reason'),flush=True)
 report.update(status='complete',accepted_hypothetical_plans=sum(r['planning']['accepted'] for r in report['records']));save()
except Exception as e:report.update(status='failed',error=repr(e));save();raise
