"""First-intervention probe on recorded histories; no post-intervention rollout.
Only the unchanged prefix and first modified command are causally comparable.
Recorded later states cannot be used as outcomes for this unwired candidate.
"""
from pathlib import Path
import sys,json,hashlib,datetime
import numpy as np
W=Path(__file__).resolve().parent;sys.path.insert(0,str(W));from front_initial_loaded_reference_cap import cap_loaded_reference
R=W/'front_initial_physical_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();records=[];sources={str(p):sha(p) for p in [Path(__file__),W/'front_initial_loaded_reference_cap.py',W/'FRONT_INITIAL_LOADED_REFERENCE_CAP_CHECK.json']}
for seed,task in [(840022,'push_box_to_bin'),(840022,'nudge_mailer_to_bin'),(840023,'push_box_to_bin'),(840023,'nudge_mailer_to_bin'),(840020,'push_box_to_bin')]:
 ep=R/f'case_{seed}'/f'layout_{seed}_{task}';fr=json.loads((ep/'frontal_bypass.json').read_text());ev=json.loads((ep/'front_initial_center.json').read_text());handover=next((r['step'] for r in ev['rows'] if r['kind']=='handover'),None)
 moment=ep/'FRONT_INITIAL_CONTACT_MOMENT_DIAGNOSTIC.json';mom={r['step']:r for r in json.loads(moment.read_text())['rows']} if moment.exists() else {};by={r['step']:r for r in fr['rows']};unchanged=0;intervention=None
 for row in fr['rows']:
  t=row['step'];captured=handover is not None and t>handover;cop=mom.get(t,{}).get('cop');normal=cop['normal_load_N'] if cop else 0.
  if captured and row['mode']=='top_push':assert t in mom,'Independent observed force reconstruction required'
  previous=by[t-1]['target_xyz'][:2] if t-1 in by else row['target_xyz'][:2]
  advice=cap_loaded_reference(enabled=True,capture_complete=captured,mode=row['mode'],parent_xy=row['target_xyz'][:2],previous_xy=previous,reference_xy=row.get('observed_support_xyz',[0,0])[:2],surface_xy=row.get('parcel_top_xyz',[0,0])[:2],normal_load_n=normal)
  if advice['changed'] or advice['requires_recontact']:
   intervention=dict(step=t,mode=row['mode'],original_command_xyz=row['target_xyz'],advice=advice,observed_normal_load_N=normal,observed_vertical_load_N=row['contact_load']['observed_vertical_load_n'],original_z_bias_m=row['contact_load']['applied_z_bias_m'],original_control_z_preserved=True);break
  assert advice['command_xy']==row['target_xyz'][:2];unchanged+=1
 records.append(dict(episode=ep.name,recorded_first_capture=handover,front_selected=ev['selected'],unchanged_prefix_rows=unchanged,first_intervention=intervention,full_unchanged_history=intervention is None,native_capture_full_audit_required_before_wiring=True,no_new_outcome_claim=True))
 for p in [ep/'raw.npz',ep/'frontal_bypass.json',ep/'front_initial_center.json']+([moment] if moment.exists() else []):sources[str(p)]=sha(p)
assert sum(r['first_intervention'] is not None for r in records)==2
assert all(r['full_unchanged_history'] for r in records if not r['front_selected'])
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,status='offline_first_interventions_only',records=records,source_sha256=sources,simulation_started=False,training_ready=False,required_next_checks=['Independent native capture/control audits on these physical inputs','Real state-class command history and empty-intersection recontact semantics','Causal full-source/audit integration with unchanged Z/pressure/guard priority','Matched complete-group physics, including explicit stall detection and all original gates'])
p=W/'FRONT_INITIAL_LOADED_REFERENCE_CAP_PROBE.json';assert not p.exists();p.write_text(json.dumps(out,indent=2));print(json.dumps(records,indent=2))
