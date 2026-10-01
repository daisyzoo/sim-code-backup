"""Original live envelope corridor and force-line evidence, not a new quality gate."""
from pathlib import Path
import json,hashlib
import numpy as np
from scipy.spatial.transform import Rotation
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
w=Path(__file__).resolve().parent;repo=w.parents[1];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();cause=json.loads((w/'FRONT_BAG_MOTION_CAUSE.json').read_text());reports=[];fig,axes=plt.subplots(2,2,figsize=(12,8),constrained_layout=True)
for e,color,label in zip(cause['episodes'],['#8d6b00','#1768ac'],['Original expert','Elbow-constrained expert']):
 ep=w/e['run']/'case_840001/layout_840001_nudge_mailer_to_bin'
 for n,h in e['source_sha256'].items():assert sha(ep/n)==h
 with np.load(ep/'trace.npz') as z:xyz=z['mailer'];other=z['box']
 with np.load(ep/'parcel_orientation.npz') as z:rot=Rotation.from_quat(z['mailer']).as_matrix();orr=Rotation.from_quat(z['box']).as_matrix();yaw=np.unwrap(Rotation.from_quat(z['mailer']).as_euler('xyz')[:,2])
 radius=np.einsum('ij,j->i',abs(rot[:,0,:]),np.array([.15,.145,.04])/2);oradius=np.einsum('ij,j->i',abs(orr[:,0,:]),np.array([.14,.09,.045])/2)
 lower=.28+radius+.005;upper=other[:,0]-oradius-radius-.012;frontmargin=xyz[:,0]-radius-.28;gap=other[:,0]-xyz[:,0]-oradius-radius
 fr=json.loads((ep/'frontal_bypass.json').read_text());switch=next(r['step'] for r in fr['rows'] if r['route_stage']=='lateral_y');guard=next((r['step'] for r in fr['rows'] if r.get('route_stop_reason')=='target_table_margin_5mm'),None);events=[]
 for t in sorted(set([0,switch,guard if guard is not None else len(xyz)-1])):
  events.append(dict(step=t,center_xyz=xyz[t].tolist(),yaw_deg=float(np.rad2deg(yaw[t])),visual_radius_x_mm=float(radius[t]*1000),original_table_margin_mm=float(frontmargin[t]*1000),original_other_x_gap_mm=float(gap[t]*1000),front_corridor_center_min_x_m=float(lower[t]),front_corridor_center_max_x_m=float(upper[t]),available_center_band_mm=float((upper[t]-lower[t])*1000)))
 stats=[]
 for stage in ['front_x','lateral_y']:
  rows=[r for r in e['frames'] if r['mode']=='top_push' and r['stage']==stage and r['current_contact_material'] is not None];force=np.array([r['last_tick_hand_force_on_object_N'] for r in rows]);moment=np.array([r['last_tick_hand_moment_about_object_Nm'] for r in rows]);local=np.array([r['current_contact_material']['current_cop_object_local'] for r in rows]);stats.append(dict(stage=stage,samples=len(rows),median_contact_object_local_mm=(np.median(local,axis=0)*1000).tolist(),median_hand_force_on_object_N=np.median(force,axis=0).tolist(),median_hand_moment_z_Nm=float(np.median(moment[:,2])),negative_z_moment_samples=int((moment[:,2]<-.001).sum())))
 reports.append(dict(run=e['run'],switch_step=switch,guard_step=guard,events=events,force_line_stats=stats))
 axes[0,0].plot(xyz[:,0]*1000,xyz[:,1]*1000,color=color,label=label);axes[0,0].scatter(xyz[switch,0]*1000,xyz[switch,1]*1000,c=color,marker='o');axes[0,0].scatter(xyz[-1,0]*1000,xyz[-1,1]*1000,c=color,marker='x',s=60)
 axes[0,1].plot(np.rad2deg(yaw),color=color,label=label)
 axes[1,0].plot(frontmargin*1000,color=color,label=label)
 axes[1,1].plot((upper-lower)*1000,color=color,label=label)
 for a in [axes[0,1],axes[1,0],axes[1,1]]:
  a.axvline(switch,color=color,ls=':',alpha=.5)
  if guard is not None:a.axvline(guard,color=color,ls='--',alpha=.5)
axes[0,0].axhline(200,color='gray',ls='--',label='Original target zone Y=200 mm');axes[0,0].set(xlabel='Object center X (mm)',ylabel='Object center Y (mm)',title='Measured bag path; circles: first turn, crosses: final');axes[0,0].legend(fontsize=7)
axes[0,1].set(xlabel='Recorded frame',ylabel='Yaw (degrees)',title='Measured orientation; dotted: turn, dashed: guard')
axes[1,0].axhline(5,color='black',ls='--');axes[1,0].set(xlabel='Recorded frame',ylabel='Front table margin (mm)',title='Original visual-envelope table margin; gate=5 mm')
axes[1,1].axhline(0,color='black',ls='--');axes[1,1].set(xlabel='Recorded frame',ylabel='Available object-center X band (mm)',title='12 mm other clearance + original 5 mm table margin')
for a in axes.flat:a.grid(alpha=.2)
fig.savefig(w/'FRONT_BAG_CORRIDOR.jpg',dpi=120);plt.close(fig)
out=dict(scope=__doc__,reports=reports,interpretation=['Most forward X motion is intended front-route motion, not an accidental new IK goal.','Object rotation grows visual footprint; live route therefore requests further frontward X, narrowing the table corridor.','New lateral29 frames have26 positive nominal material-X but negative actual material-X,7.328mm extra frontward target motion, and all29 last-tick hand moments negative Z.','Original and new lateral COP are on opposite local-X sides; torque direction differs. Direction handoff should review unloading/recontact/force line, not only solver convergence.','Single-run/fixed recorded-input evidence, last-tick forces not integrated impulses. No causal treatment estimate and no learned policy claim.'],source_sha256={str(p):sha(p) for p in [Path(__file__),w/'FRONT_BAG_MOTION_CAUSE.json',repo/'simfoundry/data/front_top_route.py',w/'FRONT_BAG_CORRIDOR.jpg']},training_ready=False);(w/'FRONT_BAG_CORRIDOR_RESULT.json').write_text(json.dumps(out,indent=2));print(json.dumps(reports,indent=2))
