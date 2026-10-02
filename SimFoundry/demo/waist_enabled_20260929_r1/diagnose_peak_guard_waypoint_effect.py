"""Local pressure-hold propagation into the original height waypoint.
Same observed pre-state and surface only, not a counterfactual rollout or joint
tracking prediction. Bias persistence after a slew-clipped action is retained.
"""
from pathlib import Path
import sys,json,hashlib,datetime
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
ep=Path(sys.argv[1]).resolve();w=Path(__file__).resolve().parent
proof=json.loads((ep/'PRESSURE_STREAM_DIAGNOSIS.json').read_text())
for path,digest in proof['source_sha256'].items():assert sha(path)==digest
assert proof['pressure_verification']['passed']
f={x['step']:x for x in json.loads((ep/'frontal_bypass.json').read_text())['rows']}
p=json.loads((ep/'peak_load_updates.json').read_text());final={x['step']:x for x in p['final_control_states']}
rows=[]
for e in p['rows']:
    g=e['returned']['peak_bias_guard']
    if not g['held_negative_increment']:continue
    t=e['action_step'];r=f[t];prev=f[t-1]
    row=dict(step=t,actual_mode=r['mode'],pressure_phase=e['phase_at_update'],local_stored_bias_difference_mm=(g['guarded_bias_m']-g['proposed_bias_m'])*1000)
    if r['mode']==prev['mode']=='top_push':
        z0=prev['target_xyz'][2];surface=r['parcel_top_xyz'][2]
        def command(bias):return z0+max(-.001,min(.001,surface+.002+bias-z0))
        expected=command(g['guarded_bias_m']);actual=r['target_xyz'][2];assert abs(expected-actual)<1e-12
        alternate=command(g['proposed_bias_m']);effect=actual-alternate;assert effect>=-1e-12
        row.update(classification='changed_height_waypoint' if effect>1e-12 else 'held_bias_but_slew_clipped_height',actual_z_m=actual,local_parent_z_m=alternate,local_height_difference_mm=effect*1000)
    else:
        assert r['mode']=='top_lift' and r['last_recontact_reason']=='incipient_tilt_independent'
        assert r['contact_load']['applied_z_bias_m']==0 and final[t]['bias_m']==0
        row.update(classification='original_tilt_guard_cleared_bias_and_replaced_waypoint',local_height_difference_mm=0.)
    rows.append(row)
summary={c:sum(x['classification']==c for x in rows) for c in ['changed_height_waypoint','held_bias_but_slew_clipped_height','original_tilt_guard_cleared_bias_and_replaced_waypoint']}
sources=[ep/'PRESSURE_STREAM_DIAGNOSIS.json',ep/'peak_load_updates.json',ep/'frontal_bypass.json',w/'staged_peak_load_guard/region_top_contact.py',Path(__file__)]
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,episode=ep.name,rows=rows,summary=summary,source_sha256={str(p):sha(p) for p in sources},training_ready=False)
p=ep/'PEAK_GUARD_WAYPOINT_EFFECT.json';assert not p.exists();p.write_text(json.dumps(out,indent=2));print(json.dumps(out['summary']))
