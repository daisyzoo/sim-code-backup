"""Independent raw-force/timing audit of bounded robot X correction; no physics writes."""
from pathlib import Path
import json, sys
import numpy as np
from scipy.spatial.transform import Rotation

run=Path(sys.argv[1]).resolve()
assert json.loads((run/'STATUS.json').read_text())['stage']=='numeric_complete_actual_visual_review_pending'
rows=[]
for ep in sorted(run.glob('case_*/layout_*')):
    log=json.loads((ep/'frontal_bypass.json').read_text())
    assert log['plan']['top_recontact']['cross_axis_admittance']
    limits=log['plan']['top_recontact']['cross_axis_limits']
    assert limits==dict(gain_m_per_n=.0008,max_step_m=.0005,max_bias_m=.01)
    side='right' if 'push_box' in ep.name else 'left'
    actor='parcel_box' if side=='right' else 'mailer'
    key='box' if side=='right' else 'mailer'
    force={r['after_action_step']:r for r in json.loads((ep/'solved_contact_forces.json').read_text())['rows']}
    ori=np.load(ep/'parcel_orientation.npz')[key]
    previous_recontacts=0;filtered=0.;bias=0.;samples=[];errors=[];resets=[]
    for r in log['rows']:
        t=r['step'];count=r.get('recontacts',0)
        if count>previous_recontacts:
            filtered=0.;bias=0.;resets.append(t)
            if r.get('push_x_anchor_m') is not None:errors.append([t,'uncleared_anchor'])
        previous_recontacts=count
        c=r.get('cross_axis_admittance')
        if r['mode']!='top_push':
            if c is not None:errors.append([t,'correction_outside_push'])
            continue
        if c is None:
            errors.append([t,'missing_push_correction']);continue
        if t-1 not in force:
            errors.append([t,'missing_previous_tick_force']);continue
        # Reconstruct from raw prior solved packet and current pre-action orientation.
        # Do not call the production force observer or correction class.
        net=np.zeros(3);normal=0.;patches=0
        top_normal=Rotation.from_quat(ori[t]).as_matrix()[:,2]
        for contact in force[t-1]['parcel_contacts']:
            labels=contact['shapes'];slots=[i for i,label in enumerate(labels) if '/'+actor+'/' in label]
            if len(slots)!=1 or not any(side+'_wrist' in label for label in labels):continue
            on_target=np.asarray(contact['force_world_N'])*(1 if slots[0]==1 else -1)
            net+=on_target;compression=-float(on_target@top_normal)
            if compression>.05:normal+=compression;patches+=1
        active=patches>0 and normal>.3
        fx=float(net[0]) if active else 0.
        filtered=.75*filtered+.25*fx
        before=bias
        if active:bias=float(np.clip(bias+np.clip(-.0008*filtered,-.0005,.0005),-.01,.01))
        observed=r['loaded_contact_geometry']
        residuals=dict(force_vector=float(np.max(np.abs(net-np.asarray(observed['force_on_target_world_n'])))),normal=abs(normal-observed['normal_load_n']),input_force=abs(fx-c['observed_force_x_on_target_n']),filtered=abs(filtered-c['filtered_force_x_on_target_n']),bias=abs(bias-c['command_bias_x_m']))
        if any(v>1e-7 for v in residuals.values()) or c['active']!=active:errors.append([t,'raw_replay_mismatch',residuals])
        if abs(c['command_bias_x_m'])>.010000001 or abs(c['command_bias_x_m']-before)>.000500001:errors.append([t,'bias_bound'])
        samples.append(dict(step=t,active=active,raw_previous_force_x_n=float(net[0]),bias_m=bias,replay_residuals=residuals))
    passed=bool(samples) and not errors
    row=dict(episode=ep.name,passed=passed,errors=errors,samples=samples,reset_steps=resets,max_abs_bias_m=max((abs(s['bias_m']) for s in samples),default=0.),active_samples=sum(s['active'] for s in samples))
    rows.append(row);print(ep.name,'passed',passed,'samples',len(samples),'maxbias',row['max_abs_bias_m'],'errors',errors[:5])
report=dict(rows=rows,passed=len(rows)==2 and all(r['passed'] for r in rows),scope='Independent raw previous-tick force shape sign/current orientation, contact activation, filter, bias bounds and reset replay. Robot command only; reference slew is separately audited. Does not certify full substep forces, causal benefit, visual quality or model success.',training_ready=False)
(run/'CROSS_AXIS_ADMITTANCE_AUDIT.json').write_text(json.dumps(report,indent=2))
if not report['passed']:raise SystemExit(1)
