"""Physical recovery coverage vs matched no-force control and model failures."""
from pathlib import Path
import json,hashlib,argparse
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'demo/recovery_protocol_20260928_r1'
parser=argparse.ArgumentParser();parser.add_argument('--bilateral',action='store_true');args=parser.parse_args()
forces=(0,8,20,40,80) if args.bilateral else (0,8,20)
suffix='_bilateral' if args.bilateral else ''
base=ROOT/'demo/recovery_scale_20260928_f0_r1/layout_30001_wait_no_package'
b=np.load(base/'raw.npz');bq=b['q'][:,13:23];bt=np.load(base/'trace.npz')
models=json.loads((out/'failure_onset.json').read_text())
fail_states=np.concatenate([np.load(ROOT/r['path']/'raw.npz')['q'][:,13:23] for r in models if r['task']=='wait_no_package'])
def distance(states,bank):return np.array([np.abs(bank-q).max(1).min() for q in states])
before=distance(fail_states,bq);bank=[bq];rows=[]
sheet=Image.new('RGB',(1600,260*len(forces)),'white');draw=ImageDraw.Draw(sheet)
for i,force in enumerate(forces):
 kind='bilateral' if force>=40 else 'scale'
 root=ROOT/f'demo/recovery_{kind}_20260928_f{force}_r1';p=root/'layout_30001_wait_no_package'
 d=np.load(p/'raw.npz');q=d['q'][:,13:23];tr=np.load(p/'trace.npz');quality=json.loads((p/'quality.json').read_text());delta=q-bq
 row={'force_parameter_N_per_hand':force,'side':'both' if force>=40 else 'left','quality':quality,'raw_sha256':hashlib.sha256((p/'raw.npz').read_bytes()).hexdigest(),'q_difference_peak_rad':float(abs(delta).max()),'q_difference_peak_per_joint_rad':abs(delta).max(0).tolist(),'shoulder_pitch_delta_minmax_rad':[[float(delta[:,j].min()),float(delta[:,j].max())] for j in (0,5)],'final10_q_error_from_control_rad':float(abs(delta[-10:]).max()),'first_upper_q_max_rad':float(abs(d['q'][0,12:]).max()),'first_upper_action_max_rad':float(abs(d['action'][0,12:]).max()),'palms':{}}
 for side in ('left','right'):
  diff=np.linalg.norm(tr[f'palm_{side}']-bt[f'palm_{side}'],axis=1)
  row['palms'][side]={'peak_control_difference_m':float(diff.max()),'final10_control_difference_m':float(diff[-10:].max())}
 bank.append(q)
 for col,t in enumerate([0,20,25,35,69]):
  sheet.paste(Image.fromarray(d['rgb'][t].transpose(1,2,0)).resize((320,240)),(col*320,i*260+20));draw.text((col*320+2,i*260+2),f'{force}N t{t}',fill='black')
 rows.append(row)
after=distance(fail_states,np.concatenate(bank))
early=np.concatenate([np.load(ROOT/r['path']/'raw.npz')['q'][1:10,13:23] for r in models if r['task']=='wait_no_package'])
early_before=distance(early,bq);early_after=distance(early,np.concatenate(bank))
report={'early_frames1_9_coverage':{'baseline_median_rad':float(np.median(early_before)),'augmented_median_rad':float(np.median(early_after))},'rows':rows,'matched_model_wait_coverage':{'baseline_distance_median_rad':float(np.median(before)),'augmented_distance_median_rad':float(np.median(after)),'fraction_model_frames_improved_over_1mrad':float(np.mean(before-after>.001))},'training_ready':False,'note':'Nearest-state similarity only; no model retraining or success claim. Direction and amplitude must both be considered.'}
(out/f'recovery_scale{suffix}.json').write_text(json.dumps(report,indent=2));sheet.save(out/f'recovery_scale{suffix}.jpg');print(json.dumps(report,indent=2))
