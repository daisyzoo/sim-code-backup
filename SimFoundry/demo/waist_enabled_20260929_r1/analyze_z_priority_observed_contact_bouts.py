"""Read-only actual contact bouts, using original 24-substep pressure semantics.
Descriptive evidence only: no counterfactual dynamics, success override, or
training admission. Last-tick Fz sums and 24-tick means are kept distinct.
"""
from pathlib import Path
import argparse,collections,datetime,hashlib,json
import numpy as np
from scipy.spatial.transform import Rotation

def inspect(ep):
    ep=Path(ep).resolve();sources={}
    def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
    def read(name):
        p=ep/name;sources[str(p)]=sha(p);return json.loads(p.read_text())
    quality=read('quality.json');assert quality['frames']==1200
    fr=read('frontal_bypass.json');pressure={r['action_step']:r for r in read('peak_load_updates.json')['rows']}
    metadata=read('SUBSTEP_CONTACT_RECORDING.json')['metadata'];stride=24+metadata['expected_manager_steps'];assert stride in (25,32)
    labels=metadata['shape_labels'];direction=fr['plan']['direction'];key='box' if direction==-1 else 'mailer';other='mailer' if key=='box' else 'box';side='right' if key=='box' else 'left';actor='parcel_box' if key=='box' else 'mailer'
    with np.load(ep/'trace.npz') as z:xyz=z[key].astype(float);other_xyz=z[other].astype(float)
    with np.load(ep/'parcel_orientation.npz') as z:rot=Rotation.from_quat(z[key]).as_matrix()
    tilt=np.arccos(np.clip(rot[:,2,2],-1,1));assert len(xyz)==len(rot)==1200
    with np.load(ep/'substep_contacts.npz') as z:sub={k:z[k].copy() for k in ['action_step','substep_tick','contact_offsets','shape_ids','force_torque_world']}
    assert [r['step'] for r in fr['rows']]==list(range(1,1200))
    newlog=read('front_loaded_z_priority.json') if (ep/'front_loaded_z_priority.json').exists() else None
    newrows=None if newlog is None else {r['step']:r for r in newlog['rows']}
    def stats(v):
        a=np.asarray(v,float);assert len(a) and np.isfinite(a).all();return dict(min=float(a.min()),median=float(np.median(a)),mean=float(a.mean()),max=float(a.max()))
    bouts=[];records=[];active=None;lookup={r['step']:r for r in fr['rows']}
    for row in fr['rows']:
        t=row['step']
        if row['mode']!='top_push':active=None;continue
        if active is None:active=[];bouts.append(active)
        loads=[];base=(t-1)*stride;assert np.all(sub['action_step'][base:base+stride]==t-1)
        for tick in range(1,25):
            hits=np.flatnonzero(sub['substep_tick'][base:base+stride]==tick);assert len(hits);i=base+int(hits[0]);load=0.
            for j in range(int(sub['contact_offsets'][i]),int(sub['contact_offsets'][i+1])):
                names=[labels[int(k)] for k in sub['shape_ids'][j]]
                if any(side+'_wrist_roll' in name for name in names) and any('/'+actor+'/' in name for name in names):load+=abs(float(sub['force_torque_world'][j,2]))
            loads.append(load)
        observed=pressure[t]['preceding_observation'];assert observed['observed_after_action_step']==t-1 and observed['observed_solver_substeps']==24
        np.testing.assert_allclose([max(loads),loads[-1]],[observed['previous_action_peak_n'],observed['final_load_n']],rtol=0,atol=1e-10)
        np.testing.assert_allclose(loads[-1],row['contact_load']['observed_vertical_load_n'],rtol=1e-6,atol=1e-5)
        record=dict(step=t,previous_action_step=t-1,last_tick_load_n=loads[-1],previous24_load=stats(loads),previous24_ticks_loaded=sum(v>=.3 for v in loads),target_tilt_rad=float(tilt[t]),new_command_applied=None if newrows is None else newrows[t]['applied'])
        active.append(record);records.append(record)
    summary=[]
    for index,bout in enumerate(bouts):
        start,end=bout[0]['step'],bout[-1]['step'];next_observation=min(end+1,1199);after=lookup.get(end+1,{})
        summary.append(dict(bout=index+1,start=start,end=end,push_frames=len(bout),exit_mode=after.get('mode'),exit_reason=after.get('route_stop_reason') or after.get('last_recontact_reason') or 'episode_end',observed_displacement_end_step=next_observation,final_action_next_observation_available=end<1199,target_signed_y_progress_mm=float(direction*(xyz[next_observation,1]-xyz[start,1])*1000),target_xy_displacement_mm=((xyz[next_observation,:2]-xyz[start,:2])*1000).tolist(),target_tilt_max_rad=float(tilt[start:next_observation+1].max()),last_tick_load_n=stats([x['last_tick_load_n'] for x in bout]),previous24_mean_load_n=stats([x['previous24_load']['mean'] for x in bout]),previous24_peak_load_n=stats([x['previous24_load']['max'] for x in bout]),previous24_loaded_tick_count=sum(x['previous24_ticks_loaded'] for x in bout),previous24_tick_count=24*len(bout),new_applied_frames=None if newrows is None else sum(x['new_command_applied'] for x in bout)))
    for name in ['trace.npz','parcel_orientation.npz','substep_contacts.npz']:sources[str(ep/name)]=sha(ep/name)
    sources[str(Path(__file__).resolve())]=sha(Path(__file__))
    return dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,episode=ep.name,collector_quality_passed=quality['passed'],progress_mm=quality['metrics']['target_final_progress_m']*1000,non_target_max_xy_mm=float(np.linalg.norm(other_xyz[:,:2]-other_xyz[0,:2],axis=1).max()*1000),top_push_frames=len(records),bout_exit_counts=dict(collections.Counter(x['exit_reason'] for x in summary)),bouts=summary,rows=records,source_sha256=sources,original_full_control_audits_still_required=True,training_ready=False)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('episode');args=parser.parse_args();ep=Path(args.episode).resolve();out=ep/'OBSERVED24_CONTACT_BOUT_DIAGNOSTIC.json';assert not out.exists();report=inspect(ep)
    # A previously completed original residual analysis provides an independent
    # same-episode cross-check of the temporal and force aggregation definitions.
    references=[ep/'FRONT_LOADED_TRACKING_RESIDUAL_V2_DIAGNOSTIC.json',ep/'FRONT_Z_PRIORITY_TRACKING_RESIDUAL_V2_DIAGNOSTIC.json']
    for ref in references:
        if not ref.exists():continue
        older=json.loads(ref.read_text());assert len(older['rows'])==len(report['rows'])
        for old,new in zip(older['rows'],report['rows']):
            assert old['step']==new['step'] and old['substeps_loaded']==new['previous24_ticks_loaded']
            assert old['observed_load_last_tick_N']==new['last_tick_load_n'] and old['previous_action24_load']==new['previous24_load']
        report['existing_residual_rows_exactly_matched']=len(report['rows']);report['source_sha256'][str(ref)]=hashlib.sha256(ref.read_bytes()).hexdigest()
    with out.open('x') as f:json.dump(report,f,indent=2)
    print(json.dumps({k:v for k,v in report.items() if k not in ['rows','source_sha256','scope']},indent=2))
