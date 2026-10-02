"""Additional final-sample hold propagation into same-state height commands.
Local comparison removes only the final-load hold, retaining the original peak
stage. It is not a simulated alternate joint/object trajectory. Unsupported
phase transitions are explicitly listed instead of counted as verified effects.
"""
from pathlib import Path
import sys,json,hashlib,datetime,collections
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
ep=Path(sys.argv[1]).resolve();w=Path(__file__).resolve().parent
proof=json.loads((ep/'PRESSURE_STREAM_DIAGNOSIS.json').read_text());assert proof['pressure_verification']['passed']
for p,h in proof['source_sha256'].items():assert sha(p)==h
fr={x['step']:x for x in json.loads((ep/'frontal_bypass.json').read_text())['rows']}
p=json.loads((ep/'peak_load_updates.json').read_text());final={x['step']:x for x in p['final_control_states']};rows=[]
for e in p['rows']:
    g=e['returned']['instantaneous_load_guard'];peak=e['returned']['peak_bias_guard']
    if not (g['held_by_final_sample'] and not g['held_by_peak']):continue
    t=e['action_step'];r=fr[t];prev=fr.get(t-1);actual_bias=e['after']['bias_m'];parent_bias=peak['guarded_bias_m']
    assert actual_bias>=parent_bias
    row=dict(step=t,actual_mode=r['mode'],pressure_phase=e['phase_at_update'],stored_bias_difference_mm=(actual_bias-parent_bias)*1000)
    if prev and r['mode']==prev['mode']=='top_push' and final[t]['bias_m']==actual_bias and r['contact_load']['applied_z_bias_m']==actual_bias:
        z0=prev['target_xyz'][2];surface=r['parcel_top_xyz'][2]
        def command(bias):return z0+max(-.001,min(.001,surface+.002+bias-z0))
        expected=command(actual_bias);actual=r['target_xyz'][2]
        if abs(expected-actual)<1e-12:
            alternate=command(parent_bias);effect=actual-alternate;assert effect>=-1e-12
            row.update(classification='changed_height_waypoint' if effect>1e-12 else 'held_bias_but_slew_clipped_height',actual_z_m=actual,local_peak_only_z_m=alternate,local_height_difference_mm=effect*1000)
        else:row.update(classification='additional_original_waypoint_override_not_derived',height_formula_residual_m=actual-expected)
    elif final[t]['bias_m']==0. and r['contact_load']['applied_z_bias_m']==0.:
        row.update(classification='original_outer_guard_cleared_bias',reason=r.get('last_recontact_reason'))
    else:row.update(classification='phase_transition_not_locally_derived',previous_mode=prev['mode'] if prev else None)
    rows.append(row)
assert len(rows)==proof['pressure_verification']['additional_final_holds']
files=[ep/'PRESSURE_STREAM_DIAGNOSIS.json',ep/'peak_load_updates.json',ep/'frontal_bypass.json',w/'staged_instant_load_guard/region_top_contact.py',Path(__file__)]
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,episode=ep.name,rows=rows,summary=dict(collections.Counter(r['classification'] for r in rows)),source_sha256={str(f):sha(f) for f in files},training_ready=False)
dest=ep/'INSTANT_GUARD_WAYPOINT_EFFECT.json';assert not dest.exists();dest.write_text(json.dumps(out,indent=2));print(json.dumps(out['summary']))
