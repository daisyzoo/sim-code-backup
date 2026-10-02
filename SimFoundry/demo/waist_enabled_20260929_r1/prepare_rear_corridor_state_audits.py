"""Adapt independent parent XY and height reconstruction to explicit recovery.
Validate original pre-override math; propagate actual final reference, phase and
COP reset into following steps. Never rewrite native observations or commands.
"""
from pathlib import Path
import json,hashlib,datetime,ast
W=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();manifest=[]
def write(parent,dest,cut,changes):
 original=(W/parent).read_text().split(cut)[0];source=original;edits=[]
 for before,after in changes:
  assert source.count(before)==1,(parent,before,source.count(before));source=source.replace(before,after);edits.append(dict(old=before,new=after))
 ast.parse(source);reverse=source
 for e in reversed(edits):assert reverse.count(e['new'])==1;reverse=reverse.replace(e['new'],e['old'])
 assert reverse==original;p=W/dest;assert not p.exists();p.write_text(source);manifest.append(dict(parent=parent,parent_sha256=sha(W/parent),parent_prefix_before=cut,new=dest,new_sha256=sha(p),edits=edits,reverse_prefix_matches=True))
write('audit_closed_peak_trial_rear_xy.py','rear_corridor_xy_reconstruction.py','\ndef main():',[ 
 ('def reconstruct(rows, plan, xyz, quat, packets, key, handover):','def reconstruct(rows, plan, xyz, quat, packets, key, handover, recovery_records=None):\n    recovery_records={} if recovery_records is None else recovery_records'),
 ("    for row in rows:\n        t=row['step'];f=row.get('rear_cop_centering');actual=np.asarray(row['target_xyz'],float);ref=np.asarray(row['observed_support_xyz'],float)","""    for final_row in rows:
        t=final_row['step'];recovery=recovery_records.get(t)
        row=final_row if recovery is None else recovery['parent_row']
        if recovery is not None:
            assert recovery['kind'] in ('loaded_recovery','unload') and row['step']==t and row['mode']=='top_push'
            assert final_row['rear_corridor_override']==dict(kind=recovery['kind'],step=t,parent_evidence='rear_corridor_recovery.json')
        f=row.get('rear_cop_centering');actual=np.asarray(row['target_xyz'],float);ref=np.asarray(row['observed_support_xyz'],float)"""),
 ("        previous=actual;previous_mode=row['mode']", """        # Parent computations used their original waypoint. The next step must
        # start from the reference actually committed after the final guard.
        if recovery is not None:
            committed=np.asarray(final_row['target_xyz'],float)
            if recovery['kind']=='loaded_recovery':
                assert final_row['mode']=='top_push' and final_row['recontacts']==row['recontacts']
                near(t,'committed_loaded_reference',committed,recovery['commit']['new']['command'])
                near(t,'committed_loaded_last_xy',committed[:2],recovery['commit']['new']['last_waypoint_xy'])
                near(t,'committed_loaded_anchor',final_row['push_x_anchor_m'],committed[0])
            else:
                assert final_row['mode']=='top_lift' and final_row['recontacts']==row['recontacts']+1
                near(t,'committed_first_lift',committed,recovery['commit']['verified_first_lift_reference'])
                assert final_row['contact_load']['applied_z_bias_m']==final_row['contact_load']['stored_z_bias_m']==0.
                anchor=last_world=None
            previous=committed;previous_mode=final_row['mode']
        else:previous=actual;previous_mode=row['mode']"""),
])
write('audit_closed_peak_trial_pose_height.py','rear_corridor_height_reconstruction.py','\ndef audit(ep):',[
 ('def verify_rows(rows,controls,plan,enabled,verified_events=None):','def verify_rows(rows,controls,plan,enabled,verified_events=None,recovery_records=None):\n recovery_records={} if recovery_records is None else recovery_records'),
 (" for row in rows:\n  t=row['step'];control=controls[t];target=np.asarray(row['target_xyz'],float);tip=np.asarray(row['observed_support_xyz'],float);assert target.shape==tip.shape==(3,) and np.isfinite(target).all() and np.isfinite(tip).all()", """ for final_row in rows:
  t=final_row['step'];recovery=recovery_records.get(t);row=final_row if recovery is None else recovery['parent_row']
  control=controls[t]
  if recovery is not None:
   assert recovery['kind'] in ('loaded_recovery','unload') and row['mode']=='top_push' and row['step']==t
   assert final_row['rear_corridor_override']==dict(kind=recovery['kind'],step=t,parent_evidence='rear_corridor_recovery.json')
   assert control['mode']==final_row['mode'] and np.max(abs(np.asarray(control['target_xyz'])-np.asarray(final_row['target_xyz'])))<=2e-6
   control=dict(control,mode=row['mode'],target_xyz=row['target_xyz'])
  target=np.asarray(row['target_xyz'],float);tip=np.asarray(row['observed_support_xyz'],float);assert target.shape==tip.shape==(3,) and np.isfinite(target).all() and np.isfinite(tip).all()"""),
 ("  checked+=1;count=n;last_mode=mode", """  checked+=1;count=n;last_mode=mode
  if recovery is not None and recovery['kind']=='unload':
   assert final_row['mode']=='top_lift' and final_row['recontacts']==n+1
   assert final_row['last_recontact_reason']=='rear_corridor_no_verified_loaded_step'
   assert final_row['contact_load']['applied_z_bias_m']==final_row['contact_load']['stored_z_bias_m']==0.
   assert recovery['commit']['kind']=='started_original_recontact_lift'
   assert np.max(abs(np.asarray(final_row['target_xyz'])-recovery['commit']['verified_first_lift_reference']))<=2e-6
   start=tip.copy();count=n+1;last_mode='top_lift'
   recoveries.append(dict(step=t,reason=final_row['last_recontact_reason'],verified_first_lift=True))"""),
])
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,files=manifest,component_fixtures_pending=True,full_native_dependency_required='audit_rear_corridor_native_commands_v2.verify_files must verify every recovery record before invoking these reconstructions',physical_launched=False,training_ready=False)
(W/'REAR_CORRIDOR_STATE_AUDITS_PREPARATION.json').write_text(json.dumps(out,indent=2));print('Prepared independent parent-math + actual next-state reconstruction')
