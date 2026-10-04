"""Plot existing recorded-parent diagnostics; no new physics or controller fit."""
from pathlib import Path
import datetime,hashlib,json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
W=Path(__file__).resolve().parent
source=W/'front_box_recenter_physical_r2/INACTIVE_NEXT_STATE_RESPONSE_DIAGNOSIS.json'
out=W/'inactive_transport_physical_preparation_r1'
data=json.loads(source.read_text());fig,axes=plt.subplots(1,2,figsize=(12,4.8),sharey=True)
for ax,episode,label in zip(axes,data['episodes'],['Bag task | inactive right hand','Box task | inactive left hand']):
 rows=episode['rows'][:41];ts=[r['step'] for r in rows]
 ax.plot(ts,[r['nominal_lowest_mm'] for r in rows],color='#2878B5',lw=2,label='Nominal command pose')
 ax.plot(ts,[r['actual_next_lowest_mm'] for r in rows],color='#C43D3D',lw=2.5,label='Next recorded state (FK)')
 ax.plot(ts,[r['predicted_next_lowest_mm'] for r in rows],color='#222222',lw=1,ls=':',marker='.',ms=3,label='Causal next-state forecast')
 ax.axhline(840,color='#8B4513',lw=1.5,ls='--',label='Original entry floor: 840 mm')
 ax.axhline(841.5,color='#909090',lw=1,ls='--',label='Candidate forecast margin: 841.5 mm')
 first=episode['first_actual_floor_loss'];t=first['step'];height=first['actual_next_lowest_mm']
 ax.scatter([t],[height],s=40,facecolor='#C43D3D',edgecolor='white',zorder=5)
 ax.annotate(f"First recorded loss: state {t+1}\n{height:.3f} mm",xy=(t,height),xytext=(t+6,838.9),fontsize=9,arrowprops=dict(arrowstyle='->',color='#C43D3D'))
 ax.set_title(label,fontsize=11);ax.set_xlabel('Issued command step t (next state is t+1)');ax.set_ylim(838.5,845);ax.grid(alpha=.18)
axes[0].set_ylabel('Inactive-hand lowest support point, world Z (mm)')
handles,labels=axes[0].get_legend_handles_labels();fig.legend(handles,labels,loc='lower center',ncol=2,fontsize=9,bbox_to_anchor=(.5,.005))
fig.suptitle('Historical parent: nominal clearance does not ensure next-state clearance',fontsize=13)
fig.text(.5,.89,'All curves use original issued commands. The new candidate has not been rolled out.',ha='center',fontsize=10)
fig.subplots_adjust(top=.81,bottom=.28,wspace=.15)
outputs=[]
for ext in ['png','svg']:
 path=out/f'PARENT_INACTIVE_HEIGHT_EARLY.{ext}';assert not path.exists();fig.savefig(path,dpi=160);outputs.append(path)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,command_step_axes=True,actual_curve_uses_next_recorded_q_with_independent_fk=True,frames_per_episode=41,episodes=[e['episode'] for e in data['episodes']],physical_collision_claim=False,new_candidate_effect_demonstrated=False,source_sha256={str(p):sha(p) for p in [Path(__file__),source]},output_sha256={str(p):sha(p) for p in outputs},training_ready=False)
with (out/'PARENT_INACTIVE_HEIGHT_EARLY.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(outputs=[str(p) for p in outputs],new_physics=False)))
