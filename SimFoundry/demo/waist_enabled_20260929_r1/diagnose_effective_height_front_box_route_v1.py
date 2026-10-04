"""Compare actual front-box routing; no counterfactual physics or admission."""
from pathlib import Path
import collections,datetime,hashlib,json,sys
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;R=W/'front_effective_height_physical_r1'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def inspect(run):
    ep=W/run/'case_840020/layout_840020_push_box_to_bin';sources={}
    def read(n):
        p=ep/n;sources[str(p)]=sha(p);return json.loads(p.read_text())
    fr=read('frontal_bypass.json');q=read('quality.json');b=read('OBSERVED24_CONTACT_BOUT_DIAGNOSTIC.json');transport=read('joint_transport_clearance.json')
    with np.load(ep/'trace.npz') as z:target=z['box'].astype(float);other=z['mailer'].astype(float)
    with np.load(ep/'parcel_orientation.npz') as z:rt=Rotation.from_quat(z['box']).as_matrix();ro=Rotation.from_quat(z['mailer']).as_matrix()
    # Independent projected half widths, rather than importing runtime geometry.
    tr=np.abs(rt)@np.array([.14,.09,.045])/2
    oth=np.abs(ro)@np.array([.15,.145,.04])/2
    rows={r['step']:r for r in fr['rows']};events=[];stage='front_x';safe=0;recoveries=0;gap_errors=[]
    for t,row in rows.items():
        cp=row.get('clearance_progress')
        if cp is None:continue
        gap=other[t,0]-target[t,0]-oth[t,0]-tr[t,0]
        np.testing.assert_allclose(gap,row['measured_front_gap_m'],rtol=0,atol=2e-8)
        gap_errors.append(abs(gap-row['measured_front_gap_m']))
        margin=row['front_corridor_midpoint']['original_planning_margin_m']
        old=stage;entered=False;resume=None
        if stage=='front_x':
            safe=safe+1 if gap>=margin else 0
            if gap>=margin+.0005:stage='lateral_y';resume='reserve_met'
            elif cp['nominal_clearance_confirmation'] and safe>=3:stage='lateral_y';resume='nominal_clearance_confirmed_3'
        elif gap<margin-cp['recovery_hysteresis_m']:
            stage='front_x';recoveries+=1;safe=0;entered=True
        assert (stage,recoveries,entered,safe,resume)==(cp['route_stage'],cp['clearance_recovery_count'],cp['clearance_recovery_entered'],cp['safe_clearance_observations'],cp['clearance_resume_reason']),t
        if old!=stage:
            transition=row['direction_change_recontact'];prev=rows.get(t-1,{})
            deltas=dict(target_translation_mm=float(-(target[t,0]-target[t-1,0])*1000),obstacle_translation_mm=float((other[t,0]-other[t-1,0])*1000),target_rotation_width_mm=float(-(tr[t,0]-tr[t-1,0])*1000),obstacle_rotation_width_mm=float(-(oth[t,0]-oth[t-1,0])*1000))
            np.testing.assert_allclose(sum(deltas.values()),1000*(gap-(other[t-1,0]-target[t-1,0]-oth[t-1,0]-tr[t-1,0])),rtol=0,atol=1e-10)
            following=next((s for s in range(t,1200) if rows[s]['mode']=='top_push'),None)
            events.append(dict(step=t,old_stage=old,new_stage=stage,mode=row['mode'],restarted=transition['restarted'],gap_mm=gap*1000,gap_change_components_mm=deltas,previous_mode=prev.get('mode'),measured_load_n=row['contact_load']['observed_vertical_load_n'],actual_axis_gap_mm=row['front_corridor_midpoint']['current_parcel_axis_gap_m']*1000,table_margin_mm=row['front_corridor_midpoint']['current_table_margin_m']*1000,nominal_x_error_mm=(row['route_goal_x']-target[t,0])*1000,micro_retention=transition.get('micro_repair_retention'),next_push_step=following,nonpush_frames_to_next_push=None if following is None else following-t))
    exits=[]
    for bout in b['bouts']:
        t=bout['end']+1;row=rows.get(t)
        reason='episode_end' if row is None else ('normal_release' if row['mode']=='top_release' else row.get('route_stop_reason') or row.get('last_recontact_reason'))
        exits.append(dict(bout=bout['bout'],start=bout['start'],end=bout['end'],reason=reason,push_frames=bout['push_frames'],progress_mm=bout['target_signed_y_progress_mm']))
    for n in ['trace.npz','parcel_orientation.npz']:sources[str(ep/n)]=sha(ep/n)
    return dict(episode=str(ep),original_quality_passed=q['passed'],progress_mm=q['metrics']['target_final_progress_m']*1000,non_target_max_xy_mm=float(np.linalg.norm(other[:,:2]-other[0,:2],axis=1).max()*1000),push_frames=b['top_push_frames'],loaded_tick_fraction=sum(x['previous24_loaded_tick_count'] for x in b['bouts'])/sum(x['previous24_tick_count'] for x in b['bouts']),transport_applied=sum(bool(x['applied']) for x in transport['rows']),independently_recomputed_route_frames=len(gap_errors),max_gap_recompute_error_m=max(gap_errors),events=events,corrected_bouts=exits,corrected_exit_counts=dict(collections.Counter(x['reason'] for x in exits)),source_sha256=sources)

if __name__=='__main__':
    out=R/'FRONT_BOX_ROUTE_REGRESSION_V1.json';assert not out.exists()
    parent=inspect('front_loaded_z_quarter_physical_r2');current=inspect('front_effective_height_physical_r1')
    result=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,parent=parent,current=current,source_sha256={str(Path(__file__)):sha(__file__),**parent['source_sha256'],**current['source_sha256']},findings=['Route transitions are reconstructed from actual translation and rotated envelopes under unchanged original thresholds.','More transport applications did not establish successful sorting; actual late corrective route changes coincide with fewer pushing frames.','Component decomposition distinguishes target translation from rotation-driven envelope changes; it does not prove solver intervention caused the trajectory.','Do not remove direction-change recontact or relax clearance thresholds. A new proposal must preserve original guards and prove complete command chain before separate physics.'],training_ready=False,original_failures_preserved=True)
    with out.open('x') as f:json.dump(result,f,indent=2)
    for label,d in [('parent',parent),('current',current)]:print(json.dumps(dict(label=label,**{k:v for k,v in d.items() if k not in ['source_sha256','corrected_bouts']}),indent=2))
