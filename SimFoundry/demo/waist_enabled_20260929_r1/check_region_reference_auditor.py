from pathlib import Path
import sys,json,copy,hashlib
w=Path(__file__).resolve().parent;sys.path.insert(0,str(w))
from audit_region_reference_live import audit
from audit_initial_near_half_live import audit_log
import numpy as np
p=w/'tracking_region_groups_r1/case_840004/layout_840004_nudge_mailer_to_bin';rows=json.loads((p/'region_approach.json').read_text())['rows'];base=audit(p);assert base['passed'];idx=next(i for i,r in enumerate(rows) if r['step']==base['handover_step']);tests=[]
for label in ['wrong_hand_vertex','wrong_parcel_capture','premature_center','missing_post_capture','second_handover']:
 v=copy.deepcopy(rows)
 if label=='wrong_hand_vertex':v[idx]['center_local'][0]+=.002
 if label=='wrong_parcel_capture':v[idx]['selected_surface_local_xy'][1]+=.002
 if label=='premature_center':v[idx-1]['center_local']=v[idx]['center_local']
 if label=='missing_post_capture':v.pop(idx+1)
 if label=='second_handover':v[idx+1]['solver']=dict(v[idx]['solver'])
 try:audit(p,rows_override=v)
 except (AssertionError,TypeError,ValueError):tests.append(dict(case=label,rejected=True))
 else:raise AssertionError(label+' accepted')
log=json.loads((p/'frontal_bypass.json').read_text())
with np.load(p/'parcel_orientation.npz') as z:quat=z['mailer']
a=audit_log(log,quat,.5,base['surface_local_by_step']);assert a['passed']
wrong=copy.deepcopy(log);next(x for x in wrong['rows'] if x['step']==base['handover_step'])['parcel_top_xyz'][0]+=.002;assert not audit_log(wrong,quat,.5,base['surface_local_by_step'])['passed'];tests.append(dict(case='wrong_recorded_surface',rejected=True))
r=dict(passed=True,real_capture_passed=True,negative_fixtures=tests,auditor_sha256=hashlib.sha256((w/'audit_region_reference_live.py').read_bytes()).hexdigest(),near_auditor_sha256=hashlib.sha256((w/'audit_initial_near_half_live.py').read_bytes()).hexdigest(),scope='Real measured capture plus six explicit corrupt log fixtures. No raw file mutated; original tolerances retained.',training_ready=False);(p.parent.parent/'REGION_REFERENCE_AUDITOR_CHECK.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
