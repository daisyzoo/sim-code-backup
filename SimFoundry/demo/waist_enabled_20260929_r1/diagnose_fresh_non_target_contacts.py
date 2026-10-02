"""Full24-substep non-target contact diagnosis for a recorded fresh push.
Summed contact magnitudes are not signed net forces or causal counterfactuals.
"""
from pathlib import Path
import argparse,collections,datetime,hashlib,json,sys
import numpy as np
W=Path(__file__).resolve().parent;sys.path.insert(0,str(W))
from audit_closed_peak_trial_contacts import audit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def diagnose(ep):
 ep=Path(ep).resolve();validated=audit(ep);meta=json.loads((ep/'SUBSTEP_CONTACT_RECORDING.json').read_text())['metadata'];labels=meta['shape_labels'];target='box' if 'push_box' in ep.name else 'mailer';other='mailer' if target=='box' else 'box';actor='/mailer/' if other=='mailer' else '/parcel_box/'
 with np.load(ep/'substep_contacts.npz') as z:a={k:z[k] for k in z.files}
 with np.load(ep/'trace.npz') as z:xyz=z[other].astype(float)
 post=json.loads((ep/'episode_contacts.json').read_text())['rows'];observed=np.array([x['post_action_pose'][other] for x in post]);err=float(abs(observed[:-1]-xyz[1:]).max());assert err<1e-7
 control=json.loads((ep/'expert_control.json').read_text());steps=validated['action_intervals'];assert steps==len(xyz)==len(control)
 R=24+meta['expected_manager_steps'];off=a['contact_offsets'];norm=np.linalg.norm(a['force_torque_world'][:,:3],axis=1);categories=[]
 for label in labels:
  categories.append('non_target' if actor in label else 'table' if '/table/' in label else 'other_parcel' if '/parcel_box/' in label or '/mailer/' in label else 'left_hand' if 'left_wrist_roll' in label else 'right_hand' if 'right_wrist_roll' in label else 'other_robot_or_scene')
 cats=np.array(categories);pair=cats[a['shape_ids']];touch=(pair=='non_target').any(axis=1);partner=np.where(pair[:,0]=='non_target',pair[:,1],pair[:,0]);selected_categories=sorted(set(partner[touch])-{'table','non_target'});rows=[];summary={};body_index=1 if other=='mailer' else 0;max_sub=(0.,None,None)
 for step in range(steps):
  base=step*R;ticks=a['substep_tick'][base:base+R];chosen=[base+int(np.flatnonzero(ticks==tick)[0]) for tick in range(1,25)];magnitudes={k:[] for k in selected_categories}
  for tick,j in enumerate(chosen,1):
   sl=slice(int(off[j]),int(off[j+1]));d=float(np.linalg.norm(a['body_q'][j,body_index,:2]-xyz[0,:2]))
   if d>max_sub[0]:max_sub=(d,step,tick)
   for category in selected_categories:magnitudes[category].append(float(norm[sl][touch[sl]&(partner[sl]==category)].sum()))
  row=dict(action_step=step,mode=control[step]['mode'],trace_pre_displacement_mm=float(np.linalg.norm(xyz[step,:2]-xyz[0,:2])*1000),recorded_post_displacement_mm=float(np.linalg.norm(observed[step,:2]-xyz[0,:2])*1000),partners={})
  for category,values in magnitudes.items():
   v=np.array(values);active=np.flatnonzero(v>1e-6)
   row['partners'][category]=dict(peak_sum_contact_magnitude_n=float(v.max()),positive_substeps=int(len(active)),absolute_contact_magnitude_time_sum_ns=float(v.sum()*meta['solver_dt_s']))
   if category not in summary:summary[category]=dict(positive_actions=0,positive_substeps=0,first_positive=None,last_positive=None,peak_sum_contact_magnitude_n=0.,absolute_contact_magnitude_time_sum_ns=0.)
   s=summary[category];s['positive_actions']+=int(len(active)>0);s['positive_substeps']+=len(active);s['absolute_contact_magnitude_time_sum_ns']+=row['partners'][category]['absolute_contact_magnitude_time_sum_ns']
   if len(active):
    if s['first_positive'] is None:s['first_positive']=[step,int(active[0])+1]
    s['last_positive']=[step,int(active[-1])+1]
   if v.max()>s['peak_sum_contact_magnitude_n']:s['peak_sum_contact_magnitude_n']=float(v.max());s['peak_action_tick']=[step,int(v.argmax())+1]
  rows.append(row)
 disp=np.linalg.norm(xyz[:,:2]-xyz[0,:2],axis=1)*1000;first=np.flatnonzero(disp>1.);quality=json.loads((ep/'quality.json').read_text())
 report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,episode=ep.name,target=target,non_target=other,quality_passed=quality['passed'],original_limit_mm=15.,trace_max_xy_mm=float(disp.max()),trace_max_frame=int(disp.argmax()),first_trace_frame_above1mm=int(first[0]) if len(first) else None,post_action_to_next_trace_max_error_m=err,substep_max_xy_mm=max_sub[0]*1000,substep_max_action_tick=list(max_sub[1:]),summary=summary,rows=rows,independent_audit=validated,source_sha256={n:sha(ep/n) for n in ['substep_contacts.npz','SUBSTEP_CONTACT_RECORDING.json','trace.npz','episode_contacts.json','expert_control.json','quality.json']},inspector_sha256=sha(__file__),training_ready=False)
 out=ep/'NON_TARGET_SUBSTEP_CONTACT_DIAGNOSIS.json'
 with out.open('x') as f:json.dump(report,f,indent=2)
 print(json.dumps({k:v for k,v in report.items() if k not in ['rows','independent_audit','source_sha256']},indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('episode');a=p.parse_args();diagnose(a.episode)
