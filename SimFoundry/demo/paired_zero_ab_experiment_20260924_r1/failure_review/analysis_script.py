from pathlib import Path
import json,numpy as np
from PIL import Image,ImageDraw
root=Path('SimFoundry/demo/paired_zero_ab_experiment_20260924_r1');out=root/'failure_review';out.mkdir(exist_ok=True)
rows=[]
for variant in ('a','b'):
 for seed in range(3):
  dirs=sorted((root/f'{variant}_seed{seed}/rollouts').glob('layout_*'))
  sheet=Image.new('RGB',(1600,len(dirs)*260),'white');draw=ImageDraw.Draw(sheet)
  for row,p in enumerate(dirs):
   with np.load(p/'raw.npz') as d:
    q=d['q'];a=d['action'];rgb=d['rgb']
    ts=[0,30,60,90,159] if len(q)>100 else [0,10,25,45,69]
    for col,t in enumerate(ts):
     sheet.paste(Image.fromarray(rgb[t].transpose(1,2,0)).resize((320,240)),(col*320,row*260+20))
     draw.text((col*320+2,row*260+2),f'{variant} s{seed} {p.name[7:]} t{t}',fill='black')
    steps=np.abs(np.diff(a[:,12:],axis=0)).max(1);jump=np.flatnonzero(steps>.08)+1
    inf=json.loads((p/'policy_inferences.json').read_text());bounds=[x['step'] for x in inf[1:]]
    tr=np.load(p/'trace.npz');task=p.name.split('_',2)[2]
    r={'variant':variant,'seed':seed,'episode':p.name,'jump_steps':jump.tolist(),'boundary_jumps':sum(int(t in bounds) for t in jump),'max_step':float(steps.max()),'argmax_step':int(steps.argmax()+1),'initial_action_max_rad':float(np.abs(a[0,12:]).max()),'max_q_action_error_rad':float(np.abs(q[:,12:]-a[:,12:]).max()),'final_arm_action':a[-1,13:].tolist(),'q_max_rad':np.abs(q[:,12:]).max(0).tolist()}
    if task!='wait_no_package':
     side='right' if task=='push_box_to_bin' else 'left';obj='box' if side=='right' else 'mailer';sgn=-1 if side=='right' else 1
     target=tr[obj];palm=tr[f'palm_{side}'];r['landmarks']=[{'t':t,'target':target[t].tolist(),'palm':palm[t].tolist(),'progress_m':float(sgn*(target[t,1]-target[0,1]))} for t in ts]
    else:r['landmarks']=[{'t':t,'left':tr['palm_left'][t].tolist(),'right':tr['palm_right'][t].tolist(),'action_max_rad':float(np.abs(a[t,12:]).max())} for t in ts]
    rows.append(r)
  sheet.save(out/f'{variant}_seed{seed}.jpg')
(out/'trace_analysis.json').write_text(json.dumps(rows,indent=2))
for v in ('a','b'):
 rs=[r for r in rows if r['variant']==v]
 print(v,'jumps',sum(len(r['jump_steps']) for r in rs),'at_boundary',sum(r['boundary_jumps'] for r in rs),'first_action_max_range',[min(r['initial_action_max_rad'] for r in rs),max(r['initial_action_max_rad'] for r in rs)])
for r in rows:
 if r['variant']=='b':print(r['episode'],r['seed'],'jumps',r['jump_steps'],'firstact',round(r['initial_action_max_rad'],4),'landmarks',r['landmarks'])
