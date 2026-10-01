"""Independently reconstruct region X waypoints; original audits still required."""
from pathlib import Path
import sys,json,subprocess,hashlib
import numpy as np

def reconstruct(rows, target, handover):
 by={x['step']:x for x in rows};records=[];errors=[];anchor=None;object_x=None
 for t,row in sorted(by.items()):
  if t<=handover or row['mode']!='top_push':anchor=object_x=None;continue
  prev=by.get(t-1)
  if prev is None:errors.append([t,'missing_previous_command']);continue
  if anchor is None:
   if prev['mode']!='top_press':errors.append([t,'push_without_load_confirmation_transition']);continue
   anchor=float(prev['target_xyz'][0]);object_x=float(target[t,0])
  previous=float(prev['target_xyz'][0]);desired=anchor+float(target[t,0])-object_x
  expected=previous+float(np.clip(desired-previous,-.002,.002));actual=float(row['target_xyz'][0]);error=abs(expected-actual)
  if error>2e-6:errors.append([t,'x_translation_following',error])
  if row.get('push_x_anchor_m') is None or abs(row['push_x_anchor_m']-anchor)>2e-6:errors.append([t,'per_bout_anchor'])
  records.append(dict(step=t,first_push_target_x_m=object_x,press_command_anchor_x_m=anchor,target_x_m=float(target[t,0]),expected_command_x_m=expected,actual_command_x_m=actual,reconstruction_error_m=error))
 return records,errors

if __name__=='__main__':
 w=Path(__file__).resolve().parent;p=Path(sys.argv[1]).resolve();sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
 subprocess.run([sys.executable,str(w/'audit_region_continuity_live.py'),str(p)],check=True,stdout=subprocess.DEVNULL)
 log=json.loads((p/'frontal_bypass.json').read_text());region=p/'region_approach.json';records=[];errors=[]
 if region.exists():
  assert log['plan']['region_approach']['region_push_x_reference']=='per_bout_previous_command_plus_measured_object_translation'
  rows=json.loads(region.read_text())['rows'];handover=next((r['step'] for r in rows if r['solver'] and r['solver'].get('handover')),None)
  if handover is not None:
   with np.load(p/'trace.npz') as z:target=z['box' if 'push_box' in p.name else 'mailer']
   records,errors=reconstruct(log['rows'],target,handover)
 report=dict(passed=not errors,errors=errors,records=records,region_push_steps_checked=len(records),raw_sha256=sha(p/'raw.npz'),continuity_audit_sha256=sha(p/'REGION_CONTINUITY_LIVE_AUDIT.json'),auditor_sha256=sha(__file__),scope='Independent trace/previous-press waypoint reconstruction of per-bout X anchor and measured object-X translation with original2mm slew. Original action/residual/press-switch audit required; no contact quality or task success implied.',training_ready=False)
 (p/'REGION_X_FOLLOW_LIVE_AUDIT.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='records'},indent=2));sys.exit(0 if report['passed'] else 1)
