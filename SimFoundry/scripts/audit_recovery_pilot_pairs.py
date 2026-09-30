"""Compare fresh ordinary/recovery pilot inputs and final return to control."""
from pathlib import Path
import json,numpy as np
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'demo/recovery_training_protocol_20260928_r1';rows=[]
ordinary=ROOT/'demo/ordinary_pilot8_20260928_r1'
for op in sorted(ordinary.glob('layout_*/raw.npz')):
 lid=int(op.parent.name.split('_')[1]);rp=(ROOT/'demo'/('recovery_push4_20260928_r1' if lid<10000 else f'recovery_wait_{lid}_20260928_r1')/op.parent.name/'raw.npz')
 a=np.load(op);b=np.load(rp);qa=a['q'];qb=b['q'];delta=qb[:,13:]-qa[:,13:];rgb_a=a['rgb'][0];rgb_b=b['rgb'][0];tr_a=np.load(op.parent/'trace.npz');tr_b=np.load(rp.parent/'trace.npz')
 row={'layout':lid,'task':str(a['task_id']),'frames':len(qa),'initial_q_max_diff':float(abs(qa[0]-qb[0]).max()),'first_rgb_mae':float(abs(rgb_a.astype(float)-rgb_b.astype(float)).mean()),'max_state_difference_rad':float(abs(delta).max()),'last10_state_difference_rad':float(abs(delta[-10:]).max()),'initial_parcel_max_diff_m':max(float(abs(tr_a[k][0]-tr_b[k][0]).max()) for k in ('box','mailer'))}
 assert a['instruction']==b['instruction'] and a['q'].shape==b['q'].shape
 assert row['initial_q_max_diff']<1e-4 and row['first_rgb_mae']<=2 and row['initial_parcel_max_diff_m']<=.001
 if lid>=10000:assert row['last10_state_difference_rad']<.001 and abs(b['action'][:,12:]).max()==0
 rows.append(row)
assert len(rows)==8
(out/'cross_variant_audit.json').write_text(json.dumps({'passed':True,'rows':rows,'note':'Same layouts and initial observations within predeclared pair tolerance; data differs after physical perturbation. Wait end-state return checked against matched ordinary control.'},indent=2))
print(json.dumps(rows,indent=2))
