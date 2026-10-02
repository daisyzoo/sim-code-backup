"""Legacy full-report equivalence and rejection checks for the separate supplement."""
from pathlib import Path
import json,hashlib,datetime,tempfile,os,copy
from audit_terminal_margin_contact_stability_supplement import audit_files
W=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();rows=[]
for root in ['fresh_closed_peak_trials_r1','rear_transport_retry_physical_r1','joint_edge_intersection_physical_r1','terminal_margin_physical_r1']:
 for ep in sorted((W/root).glob('case_*/layout_*')):
  parent=ep/'CONTACT_STABILITY_CONTROL_AUDIT.json'
  if not parent.exists():continue
  expected=json.loads(parent.read_text());actual=audit_files(ep,margin_enabled=False);assert actual==expected,(str(ep),'legacy changed')
  rows.append(dict(episode=str(ep),legacy_full_report_identical=True,report_sha256=sha(parent)))
assert len(rows)>=64
source=W/'terminal_margin_physical_r1/case_840014/layout_840014_push_box_to_bin';f=json.loads((source/'frontal_bypass.json').read_text());fixture=Path(tempfile.mkdtemp(prefix='terminal_margin_stability_NEGATIVE_'))
for name in ['raw.npz','trace.npz','parcel_orientation.npz']:os.link(source/name,fixture/name)
checks=[]
for kind in ['confirmation','release_xy','unload_bias','unjustified_tilt']:
 d=copy.deepcopy(f)
 if kind=='confirmation':
  row=next(r for r in d['rows'] if r.get('terminal_position_confirmed') is True);row['terminal_position_confirmed']=False
 elif kind=='release_xy':
  row=next(r for r in d['rows'] if r['mode']=='top_release');row['target_xyz'][0]+=.001
 elif kind=='unload_bias':
  row=next(r for r in d['rows'] if r['mode']=='top_release');row['contact_load']['applied_z_bias_m']=.001
 else:
  row=next(r for r in d['rows'] if 'observed_parcel_tilt_rad' in r and r['observed_parcel_tilt_rad']<.03);row['recontacts']+=1;row['last_recontact_reason']='incipient_tilt_independent'
 (fixture/'frontal_bypass.json').write_text(json.dumps(d));out=audit_files(fixture,margin_enabled=True);assert out['control_checks_passed'] is False
 expected={'confirmation':'position_confirmation_mismatch','release_xy':'release_pose_changed','unload_bias':'load_bias_while_unloading','unjustified_tilt':'unjustified_tilt_withdrawal'}[kind];assert any(e['kind']==expected for e in out['errors'])
 checks.append(dict(kind=kind,step=row['step'],expected_error=expected,rejected=True))
result=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,legacy_reports_compared=len(rows),rows=rows,negative_checks=checks,source_sha256={str(p):sha(p) for p in [Path(__file__),W/'audit_terminal_margin_contact_stability_supplement.py',W/'audit_contact_stability_control.py']},fixture_scope='Synthetic mutated log only, no new trajectory or admission.',training_ready=False)
(W/'TERMINAL_MARGIN_STABILITY_SUPPLEMENT_CHECK.json').write_text(json.dumps(result,indent=2));print('passed',len(rows),'legacy exact reports,',len(checks),'negative classes')
