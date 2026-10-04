"""All eight failed quarter-Z bag contact bouts, including three interior losses.
Validate all recorded substeps against original final force packets; use absolute
vertical force magnitudes, not signed impulse or synchronous collision proof.
"""
from pathlib import Path
import sys,json,hashlib,datetime
import numpy as np
W=Path(__file__).resolve().parent;sys.path.insert(0,str(W))
from audit_substep_contacts import verify_arrays
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text());ep=W/'front_loaded_z_quarter_physical_r2/case_840023/layout_840023_nudge_mailer_to_bin'
meta=read(ep/'SUBSTEP_CONTACT_RECORDING.json');assert meta['recording_sha256']==sha(ep/'substep_contacts.npz')
with np.load(ep/'substep_contacts.npz') as z:a={k:z[k].copy() for k in z.files}
packets=read(ep/'solved_contact_forces.json')['rows'];audit=verify_arrays(a,meta,packets,1200)
m=meta['metadata'];labels=m['shape_labels'];stride=24+m['expected_manager_steps'];offs=a['contact_offsets'];shape=a['shape_ids'];isbag=np.array(['/mailer/' in x for x in labels]);ishand=np.array(['left_wrist_roll' in x for x in labels]);mask=(isbag[shape[:,0]]&ishand[shape[:,1]])|(isbag[shape[:,1]]&ishand[shape[:,0]])
contact_sample=np.repeat(np.arange(len(offs)-1),np.diff(offs));vertical=np.bincount(contact_sample[mask],weights=abs(a['force_torque_world'][mask,2]),minlength=len(offs)-1)
loads=[]
for step in range(1200):
 base=step*stride;stamps=a['substep_tick'][base:base+stride];indices=[base+int(np.flatnonzero(stamps==tick)[0]) for tick in range(1,25)];loads.append(vertical[indices])
loads=np.array(loads);fr={r['step']:r for r in read(ep/'frontal_bypass.json')['rows']};z={r['step']:r for r in read(ep/'front_loaded_z_priority.json')['rows']};diag=read(ep.parent.parent/'FRONT_BAG_CONTACT_LOSS_DIAGNOSIS_V2.json');bouts=diag['versions'][1]['bouts'];losses=[]
for b in bouts:
 if b['exit_reason']!='lost_contact':continue
 s=b['exit_step'];cop=b['last_valid_cop'];window=[]
 for t in range(max(b['start'],s-8),s):
  r=fr[t];v=loads[t];load=r['contact_load'];window.append(dict(action_step=t,mode=r['mode'],peak_abs_vertical_n=float(v.max()),mean_abs_vertical_n=float(v.mean()),last_abs_vertical_n=float(v[-1]),ticks_gt_point3=int(np.sum(v>.3)),observed_previous_load_n=load['observed_vertical_load_n'],filtered_previous_load_n=load['filtered_vertical_load_n'],stored_z_bias_mm=load['stored_z_bias_m']*1000,z_refinement_applied=z[t]['applied'],z_refinement_reason=z[t]['reason'],support_vs_top_z_mm=(r['observed_physical_support_xyz'][2]-r['parcel_top_xyz'][2])*1000))
 losses.append(dict(exit_step=s,last_valid_cop=cop,last_valid_cop_within1mm_of_core_edge=cop['minimum_axis_margin_mm']<=1,window=window))
assert len(losses)==8
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,independent_substep_array_audit=audit,losses=losses,near_core_edge_losses=sum(r['last_valid_cop_within1mm_of_core_edge'] for r in losses),interior_losses=sum(not r['last_valid_cop_within1mm_of_core_edge'] for r in losses),training_ready=False,source_sha256={str(p):sha(p) for p in [Path(__file__),W/'audit_substep_contacts.py',ep/'SUBSTEP_CONTACT_RECORDING.json',ep/'substep_contacts.npz',ep/'solved_contact_forces.json',ep/'frontal_bypass.json',ep/'front_loaded_z_priority.json',ep.parent.parent/'FRONT_BAG_CONTACT_LOSS_DIAGNOSIS_V2.json']},interpretation='Do not attribute all failures to edge slip: five last COPs are within1mm of an edge; three retain17.8–30.7mm margin. Both tangential slip and interior loss require investigation. No controller/gate change.')
p=ep.parent.parent/'FRONT_BAG_SUBSTEP_LOSS_DIAGNOSIS_V1.json';serialized=json.dumps(out,indent=2)
with p.open('x') as f:f.write(serialized)
print(json.dumps(dict(near_edge=out['near_core_edge_losses'],interior=out['interior_losses'],events=[dict(step=r['exit_step'],margin_mm=r['last_valid_cop']['minimum_axis_margin_mm'],last_actions=[{k:x[k] for k in ['action_step','peak_abs_vertical_n','last_abs_vertical_n','ticks_gt_point3','z_refinement_applied']} for x in r['window'][-4:]]) for r in losses])))
