"""Independent full event coverage and committed-action FK/state-event audit.
This is additional to every original task, physical, source and state audit.
"""
from pathlib import Path
import sys,json,hashlib,datetime
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];D=W/'rear_waypoint_reconciliation_draft_r1';sys.path[:0]=[str(D),str(W),str(ROOT)]
from independent_post_commit_audit import load_context
from independent_commit_log_contract import verify_complete_log
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inspect_episode(ep):
    from rear_waypoint_v2_stage_source_binding import verify_trial_provenance
    ep=Path(ep).resolve();verify_trial_provenance(ep.parent)
    with np.load(ep/'raw.npz',allow_pickle=False) as z:
        task=str(z['task_id']);q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float);meta=json.loads(str(z['collect_meta']))
    assert len(q)==(70 if task=='wait_no_package' else 1200)
    frp=ep/'frontal_bypass.json';fr=json.loads(frp.read_text()) if frp.exists() else None
    if task!='wait_no_package':assert fr['plan']==meta['frontal_bypass_plan']
    urdf=ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf'
    selected=task=='push_box_to_bin' and bool(fr and fr['plan'].get('rear_cop_centering',{}).get('enabled'))
    if selected:
        ctx=load_context(ep,urdf)
    else:
        clear=json.loads((ep/'self_clearance.json').read_text());ctx=dict(q=q,u=u,fr=fr,fg={x['step']:x for x in clear['rows'] if x['phase']=='final_command'},pg={x['step']:x for x in clear['rows'] if x['phase']=='post'})
    log=json.loads((ep/'rear_waypoint_reconciliation.json').read_text());result=verify_complete_log(ctx,log,meta,task,frames=len(q))
    files=[ep/'raw.npz',ep/'self_clearance.json',ep/'rear_waypoint_reconciliation.json',ep.parent/'provenance.json',Path(__file__),W/'rear_waypoint_v2_stage_source_binding.py',D/'independent_commit_log_contract.py',D/'independent_post_commit_audit.py',urdf,ROOT/'simfoundry/calibration/sorting_station.py']
    if frp.exists():files.append(frp)
    if selected:files.extend(ep/n for n in ['trace.npz','parcel_orientation.npz','coordination.json','solved_contact_forces.json'])
    result.update(episode=ep.name,frames=len(q),source_sha256={str(p):sha(p) for p in files},scope=__doc__,continuous_state_replay_required=True,training_ready=False)
    return result
if __name__=='__main__':
    ep=Path(sys.argv[1]).resolve();result=inspect_episode(ep)
    with (ep/'REAR_WAYPOINT_V2_COMMIT_AUDIT.json').open('x') as f:json.dump(result,f,indent=2)
    print({k:result[k] for k in ['passed','episode','frames','selected','complete_event_rows']})
