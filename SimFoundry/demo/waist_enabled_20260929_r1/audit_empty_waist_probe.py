from pathlib import Path
import sys,json,numpy as np
from PIL import Image,ImageDraw
r=Path(sys.argv[1]);ep=r/'case/layout_10000_wait_no_package';settings=json.loads((r/'PROTOCOL.json').read_text())['settings'];bound=float(settings[settings.index('--waist-limit-rad')+1]);z=np.load(ep/'raw.npz');q=z['q'];a=z['action'];quality=json.loads((ep/'quality.json').read_text());err=float(abs(q[1:,12]-a[:-1,12]).max());initial=float(abs(q[0,12:]).max());initial_a=float(abs(a[0,12:]).max())
assert initial<1e-4 and initial_a<1e-4 and err<.02 and max(abs(q[:,12]))<bound
assert quality['metrics']['max_action_step_rad']<=.08 and quality['metrics']['left_table_pen_frames']==quality['metrics']['right_table_pen_frames']==0
assert not quality['passed'] and not quality['training_ready']
j=dict(waist_range_rad=[float(q[:,12].min()),float(q[:,12].max())],one_step_tracking_max_error_rad=err,initial_upper_state_max_abs_rad=initial,initial_upper_action_max_abs_rad=initial_a,quality=quality,preflight_numeric_passed=True,actual_visual_review='pending',scope='Empty-table motion preflight only. Intentionally invalid wait sample. No full-body/self-collision certification; not deployment range approval.',training_ready=False);(r/'RESULT.json').write_text(json.dumps(j,indent=2));print({k:v for k,v in j.items() if k!='quality'})
can=Image.new('RGB',(1280,500));d=ImageDraw.Draw(can)
for i,t in enumerate([0,45,90,135]):
 can.paste(Image.fromarray(z['rgb'][t].transpose(1,2,0)).resize((320,240)),(i*320,0));d.text((i*320,241),f'frame{t} waist{q[t,12]:.3f}')
for i,t in enumerate([0,40,90,130]):
 f=r/'case/viewer_layout_10000_wait_no_package'/f'pre_{t:04d}.jpg';can.paste(Image.open(f).resize((320,180)),(i*320,270));d.text((i*320,451),f'viewer {t}')
can.save(r/'REVIEW.jpg')
