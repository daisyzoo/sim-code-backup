"""Actual recorded top-down paths, excluding any hypothetical planned trajectory."""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
r=Path(__file__).resolve().parent
runs=['frontal_bypass_smoke_r1','frontal_follow_y_smoke_r1','frontal_recontact_smoke_r1']
fig,axs=plt.subplots(3,2,figsize=(10,12),sharex=True,sharey=True)
for i,name in enumerate(runs):
 for k,task in enumerate(['nudge_mailer_to_bin','push_box_to_bin']):
  ep=r/name/'case_62000'/f'layout_62000_{task}';z=np.load(ep/'trace.npz');side='left' if k==0 else 'right';target='mailer' if k==0 else 'box';other='box' if k==0 else 'mailer';ax=axs[i,k]
  for key,c in [(target,'tab:blue'),(other,'tab:orange'),('palm_'+side,'tab:green')]:
   xy=z[key];ax.plot(xy[:,1],xy[:,0],color=c,label=key);ax.scatter(xy[0,1],xy[0,0],color=c,marker='o');ax.scatter(xy[-1,1],xy[-1,0],color=c,marker='x',s=50)
  ax.axvline(.2 if k==0 else -.2,c='grey',ls=':');ax.set_title(name.replace('frontal_','')+' / '+target);ax.set_xlim(-.4,.4);ax.set_ylim(.26,.78);ax.set_aspect('equal');ax.grid(alpha=.25);ax.set_xlabel('world Y (left positive)');ax.set_ylabel('world X (table depth)');ax.legend(fontsize=8)
fig.suptitle('Measured paths: circle=start, cross=end; palm path is not full-hand clearance')
fig.tight_layout();fig.savefig(r/'FRONTAL_PATH_COMPARISON.png',dpi=125)
