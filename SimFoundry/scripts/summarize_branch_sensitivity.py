#!/usr/bin/env python3
import argparse,json,itertools
from pathlib import Path
import numpy as np

def main():
 p=argparse.ArgumentParser();p.add_argument('--audit',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 if a.out.exists():raise FileExistsError(a.out)
 r=json.loads((a.audit/'REPORT.json').read_text());out=[]
 with np.load(a.audit/'predictions.npz') as z:
  for part in ['train','validation']:
   for task in ['nudge_mailer_to_bin','push_box_to_bin']:
    active=slice(0,5) if task=='nudge_mailer_to_bin' else slice(5,10);rows=[x for x in r['trials'] if x['partition']==part and x['task']==task];noise=[];vision=[]
    def prediction(g,d,s):return z[next(x['prediction_key'] for x in rows if x['group']==g and x['target_distance']==d and x['seed']==s)][:50,active]
    for g in sorted({x['group'] for x in rows}):
     for d in ['near','far']:noise.extend(float(np.sqrt(np.mean((x-y)**2))) for x,y in itertools.combinations([prediction(g,d,s) for s in range(3)],2))
     for s in range(3):vision.append(float(np.sqrt(np.mean((prediction(g,'near',s)-prediction(g,'far',s))**2))))
    out.append({'partition':part,'task':task,'mean_action_rmse_image_swap_rad':float(np.mean(vision)),'mean_action_rmse_noise_change_rad':float(np.mean(noise)),'noise_to_image_ratio':float(np.mean(noise)/np.mean(vision))})
 report={'groups':out,'method':'Active-arm first50 action RMS differences. Same-seed swapped images versus same-image different noise seeds. Observational diagnostic, not physical success.'};a.out.write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
