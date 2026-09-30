"""Plot strict task counts and every wait drift; no independence/CI claim."""
from pathlib import Path
import argparse,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=argparse.ArgumentParser();p.add_argument('--experiment',type=Path,required=True);args=p.parse_args()
d=json.loads((args.experiment/'COMPARISON.json').read_text());vs=['baseline','ordinary','recovery'];labels=['Frozen baseline (rerun)','Ordinary additions','Push + wait recovery'];colors=['#697386','#2470bc','#d77829'];tasks=['push_box_to_bin','nudge_mailer_to_bin','wait_no_package'];names=['Box / 9','Bag / 9','Wait / 3']
fig,axes=plt.subplots(1,3,figsize=(13,4.7),gridspec_kw={'width_ratios':[1.45,1,1]});ax=axes[0];x=np.arange(3)
for j,v in enumerate(vs):
 y=[next(r[v] for r in d['summary'] if r['task']==t) for t in tasks]
 bars=ax.bar(x+(j-1)*.24,y,.24,color=colors[j],label=labels[j]);ax.bar_label(bars,padding=3,fontsize=10)
ax.set_xticks(x,names);ax.set_ylim(0,10);ax.set_ylabel('Strict passes');ax.set_title('Task outcomes');ax.legend(fontsize=8,loc='upper right');ax.spines[['top','right']].set_visible(False)
wait=[r for r in d['rows'] if r['task']=='wait_no_package']
for side,ax in zip(['left','right'],axes[1:]):
 for j,v in enumerate(vs):
  vals=[r[v][side+'_drift_m']*100 for r in wait];ax.scatter(j+np.array([-.09,0,.09]),vals,color=colors[j],s=45,zorder=3)
 ax.axhline(1.5,color='#a92727',linestyle='--',linewidth=1,label='1.5 cm limit');ax.set_xticks(range(3),['Baseline','Ordinary','Recovery'],rotation=20);ax.set_ylabel('Maximum palm drift (cm)');ax.set_ylim(bottom=0);ax.set_title(side.title()+' palm, all 3 seeds');ax.legend(fontsize=8);ax.spines[['top','right']].set_visible(False)
fig.suptitle('Same-budget data comparison: h10, fixed strict gates',fontsize=14)
fig.text(.5,.015,'3 push layouts reused across inference seeds; one training seed. Regression evidence, not independent confirmation.',ha='center',fontsize=9,color='#555555')
fig.tight_layout(rect=[0,.055,1,.94]);fig.savefig(args.experiment/'comparison.png',dpi=160);fig.savefig(args.experiment/'comparison.svg');print(args.experiment/'comparison.png')
