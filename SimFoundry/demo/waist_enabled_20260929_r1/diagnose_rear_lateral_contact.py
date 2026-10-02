"""Unsigned actual solved hand/target forces during all completed rear routes.
Use only the24 earliest solved substeps per action; exclude manager duplicates.
Force/body sign is unverified, so component absolute-time sums are NOT impulses
or signed resultant forces. This is observational diagnosis, not causality.
"""
from pathlib import Path
import argparse,datetime,hashlib,json,sys
import numpy as np
W=Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W.parents[1])]
from audit_closed_peak_trial_contacts import audit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(run):
 run=Path(run).resolve();records=[];sources={str(Path(__file__)):sha(__file__),str(W/'audit_closed_peak_trial_contacts.py'):sha(W/'audit_closed_peak_trial_contacts.py')}
 for f in sorted(run.glob('case_*/*/frontal_bypass.json')):
  ep=f.parent
  if not (ep/'quality.json').exists():continue
  data=json.loads(f.read_text());p=data['plan']
  if not p['required'] or p.get('front_route_selected') or p.get('initial_top_selected'):continue
  valid=audit(ep);assert valid['passed'];isbox=ep.name.endswith('push_box_to_bin');target='box' if isbox else 'mailer';actor='/parcel_box/' if isbox else '/mailer/';hand='right' if isbox else 'left';direction=p['direction'];m=json.loads((ep/'SUBSTEP_CONTACT_RECORDING.json').read_text())['metadata'];labels=m['shape_labels'];R=24+m['expected_manager_steps'];dt=m['solver_dt_s']
  with np.load(ep/'substep_contacts.npz') as z:a={k:z[k] for k in z.files}
  with np.load(ep/'trace.npz') as z:xyz=z[target].copy()
  ids=a['shape_ids'];target_mask=np.array([actor in s for s in labels])[ids].any(axis=1);hand_mask=np.array([hand+'_wrist_roll' in s for s in labels])[ids].any(axis=1);mask=target_mask&hand_mask;forces=a['force_torque_world'][:,:3].astype(float);off=a['contact_offsets'];rows=[]
  for fr in data['rows']:
   if fr['mode']!='rear_push':continue
   t=fr['step'];base=t*R;ticks=a['substep_tick'][base:base+R];chosen=[base+int(np.flatnonzero(ticks==tick)[0]) for tick in range(1,25)];components=[];norms=[]
   for j in chosen:
    sl=slice(int(off[j]),int(off[j+1]));F=forces[sl][mask[sl]];components.append(abs(F).sum(0));norms.append(np.linalg.norm(F,axis=1).sum())
   c=np.array(components);v=np.array(norms);rows.append(dict(step=t,positive_substeps=int(np.sum(v>1e-6)),unsigned_xyz_time_sum_ns=(c.sum(0)*dt).tolist(),peak_sum_force_magnitude_n=float(v.max()),target_xy=xyz[t,:2].tolist(),next_trace_delta_xy_mm=((xyz[min(t+1,len(xyz)-1),:2]-xyz[t,:2])*1000).tolist()))
  summed=np.sum([x['unsigned_xyz_time_sum_ns'] for x in rows],axis=0);contact=[x for x in rows if x['positive_substeps']];start,end=rows[0]['step'],min(rows[-1]['step']+1,len(xyz)-1)
  row=dict(episode=ep.name,task_passed=json.loads((ep/'quality.json').read_text())['passed'],rear_frames=len(rows),rear_frames_with_positive_contact=len(contact),unsigned_xyz_time_sum_ns=summed.tolist(),unsigned_Y_over_X=float(summed[1]/summed[0]) if summed[0]>0 else None,rear_target_delta_xy_mm=((xyz[end,:2]-xyz[start,:2])*1000).tolist(),rear_signed_task_y_progress_mm=float(direction*(xyz[end,1]-xyz[start,1])*1000),first_contact_action=contact[0]['step'] if contact else None,last_contact_action=contact[-1]['step'] if contact else None,rows=rows,independent_audit=valid);records.append(row)
  for path in [f,ep/'quality.json',ep/'trace.npz',ep/'substep_contacts.npz',ep/'SUBSTEP_CONTACT_RECORDING.json']:sources[str(path)]=sha(path)
  print(json.dumps({k:v for k,v in row.items() if k not in ['rows','independent_audit']}),flush=True)
 report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,records=records,source_sha256=sources,runtime_changed=False,training_ready=False)
 with (run/'REAR_LATERAL_CONTACT_DIAGNOSIS.json').open('x') as out:json.dump(report,out,indent=2)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('run');a=p.parse_args();main(a.run)
