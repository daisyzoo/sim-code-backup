"""One-step constant-angular-velocity screen on real recorded trajectories.
Not a closed-loop rollout or a controller. Future substeps are evaluation labels
only: prediction uses the preceding completed action's pose and angular velocity.
Predicted versus actual 0.03 tilt excursions are descriptive, not a new gate.
"""
from pathlib import Path
import json,hashlib,datetime
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def inspect(ep):
    hp=ep/('PEAK_GUARD_LOAD_HISTORY.json' if (ep/'PEAK_GUARD_LOAD_HISTORY.json').exists() else 'SUBSTEP_LOAD_HISTORY.json')
    h=json.loads(hp.read_text());assert h['independent_audit']['passed']
    for name,digest in h['source_sha256'].items():assert sha(ep/name)==digest
    m=json.loads((ep/'SUBSTEP_CONTACT_RECORDING.json').read_text())['metadata'];stride=24+m['expected_manager_steps'];dt=24*m['solver_dt_s'];assert abs(dt-1/15)<1e-12
    fr={f['step']:f for f in json.loads((ep/'frontal_bypass.json').read_text())['rows']};b=0 if 'push_box' in ep.name else 1
    with np.load(ep/'substep_contacts.npz') as a:
        indices=[t*stride+int(np.flatnonzero(a['substep_tick'][t*stride:(t+1)*stride]==24)[0]) for t in range(1200)]
        q=a['body_q'][indices,b,3:].astype(float);omega=a['body_qd'][indices,b,3:].astype(float)
    rot=Rotation.from_quat(q);up=rot.as_matrix()[:,:,2];actual=np.arccos(np.clip(up[:,2],-1,1));pred=(Rotation.from_rotvec(omega*dt)*rot).as_matrix()[:,:,2];theta=np.arccos(np.clip(pred[:,2],-1,1));events=[]
    # Controller action t+1 sees final state from action t. Restrict to cases
    # where that actual next action stayed in top_push and current tilt <=.03.
    for t in range(1199):
        if t+1 not in fr or fr[t+1]['mode']!='top_push' or actual[t]>.03:continue
        item=dict(observed_after_action=t,decision_action=t+1,current_tilt_rad=float(actual[t]),angular_speed_world_rad_s=omega[t].tolist(),predicted_next_final_tilt_rad=float(theta[t]),actual_next_final_tilt_rad=float(actual[t+1]),actual_next_max_tilt_rad=h['rows'][t+1]['max_target_tilt_rad'])
        item.update(predicted_excursion=bool(theta[t]>.03),actual_final_excursion=bool(actual[t+1]>.03),actual_any_substep_excursion=bool(item['actual_next_max_tilt_rad']>.03));events.append(item)
    def confusion(label):
        return {name:sum((e['predicted_excursion']==p) and (e[label]==a) for e in events) for name,p,a in [('true_positive',True,True),('false_positive',True,False),('false_negative',False,True),('true_negative',False,False)]}
    errors=[abs(e['predicted_next_final_tilt_rad']-e['actual_next_final_tilt_rad']) for e in events]
    q=json.loads((ep/'quality.json').read_text());files=[hp,ep/'substep_contacts.npz',ep/'SUBSTEP_CONTACT_RECORDING.json',ep/'frontal_bypass.json',ep/'quality.json']
    return dict(run=ep.parent.parent.name,episode=ep.name,task_passed=q['passed'],events=len(events),against_next_final=confusion('actual_final_excursion'),against_next_any_substep=confusion('actual_any_substep_excursion'),angle_error_rad=dict(median=float(np.median(errors)),p95=float(np.quantile(errors,.95)),maximum=max(errors)),flagged_or_actual_events=[e for e in events if e['predicted_excursion'] or e['actual_any_substep_excursion']],source_sha256={str(p):sha(p) for p in files},training_ready=False)

if __name__=='__main__':
    eps=sorted((W/'substep_reference03_groups_r1').glob('case_*/layout_*/SUBSTEP_LOAD_HISTORY.json'))+sorted((W/'peak_guard_groups_r1').glob('case_*/layout_*/PEAK_GUARD_LOAD_HISTORY.json'));assert len(eps)==10
    rows=[inspect(p.parent) for p in eps];out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,script_sha256=sha(__file__),training_ready=False,limitations=['Forecast freezes angular velocity and does not model next contact forces.','A forecast false positive can alter successful behavior; effects of stopping, lifting or pressure changes are not simulated.','No thresholds or source controls are changed.'])
    p=W/'peak_guard_groups_r1/ANGULAR_FORECAST_FIRST_TWO_SCREEN.json';assert not p.exists();p.write_text(json.dumps(out,indent=2))
    for r in rows:print(json.dumps({k:v for k,v in r.items() if k not in ['flagged_or_actual_events','source_sha256']}))
