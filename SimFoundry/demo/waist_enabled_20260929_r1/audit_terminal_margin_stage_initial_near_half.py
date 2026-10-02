"""Independent actual near/far contact fraction metadata and surface reconstruction."""
from pathlib import Path
import sys,json,hashlib,math
import numpy as np
from scipy.spatial.transform import Rotation

def audit_log(log,quats,expected_near_fraction,verified_region_surfaces=None):
 plan=log['plan'];errors=[];meta=plan.get('initial_top_contact_location');near=bool(plan.get('initial_top_selected') and plan['initial_target_xyz'][0]<.48);contact=plan['top_recontact'];fraction=contact['effective_top_fraction']
 if meta is None:return dict(passed=False,errors=[dict(kind='missing_recorded_location')],checked_frames=0)
 if meta['configured_near_fraction']!=expected_near_fraction or meta['near_x_threshold_m']!=.48 or meta['override_applied']!=near:errors.append(dict(kind='location_metadata'))
 if meta['effective_top_fraction']!=fraction or (near and fraction!=expected_near_fraction):errors.append(dict(kind='effective_fraction'))
 size=np.asarray(contact['contact_size_xyz'],dtype=float);max_error=0.;checked=0
 assert not contact['visible_corner'] and not plan['contact_center_calibration']['enabled']
 for row in log['rows']:
  if 'parcel_top_xyz' not in row:continue
  r=Rotation.from_quat(quats[row['step']]).as_matrix();axis=int(np.argmax(np.abs(r[0,:2])));inset=.02 if fraction is None else fraction*size[axis]/2;local=np.array([0.,0.,size[2]/2]);local[axis]=(-1 if r[0,axis]>=0 else 1)*(size[axis]/2-inset);
  if verified_region_surfaces and row['step'] in verified_region_surfaces:local[:2]=verified_region_surfaces[row['step']]
  expected=np.asarray(row['observed_target'])+r@local;error=float(np.max(abs(expected-np.asarray(row['parcel_top_xyz']))));max_error=max(max_error,error);checked+=1
  if not math.isfinite(error) or error>1e-7:errors.append(dict(step=row['step'],kind='surface_geometry',error_m=error))
 return dict(passed=not errors,errors=errors,checked_frames=checked,max_surface_error_m=max_error,near_override_expected=near,effective_fraction=fraction)

def main():
 ep=Path(sys.argv[1]).resolve();log=json.loads((ep/'frontal_bypass.json').read_text());key='box' if 'push_box' in ep.name else 'mailer'
 with np.load(ep/'parcel_orientation.npz') as z:quat=z[key]
 from audit_terminal_margin_stage_region_reference import audit as audit_region_reference
 region=audit_region_reference(ep);assert region['passed']
 report=audit_log(log,quat,.5,region['surface_local_by_step']);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();report.update(raw_sha256=sha(ep/'raw.npz'),frontal_sha256=sha(ep/'frontal_bypass.json'),scope='Original rotated-top surface independently reconstructed from actual recorded pose and effective contact fraction; near-only selection/configuration checked. Physical contact patch, original task/pose and actual image review remain separate.',training_ready=False)
 report['region_reference_auditor_sha256']=sha(Path(__file__).resolve().parent/'audit_terminal_margin_stage_region_reference.py')
 (ep/'TERMINAL_MARGIN_STAGE_INITIAL_NEAR_HALF_V2_AUDIT.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='errors'}));return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
