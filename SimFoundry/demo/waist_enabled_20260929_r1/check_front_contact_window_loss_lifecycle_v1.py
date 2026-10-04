"""Complete recorded parent episodes test independent loss-phase reconstruction.
Parents lack window extension; records are original observations, not new window
physics. Explicit interval fixtures below test stream binding and missing evidence.
"""
from pathlib import Path
import sys,json,hashlib,datetime,copy,collections
import numpy as np
W=Path(__file__).resolve().parent;sys.path.insert(0,str(W));D=W/'front_contact_window_preparation_r2'
from front_contact_window_loss_lifecycle_v1 import verify_stream
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={};results=[];negative=[]
def read(p):sources[str(p)]=sha(p);return json.loads(p.read_text())
for run in ['front_loaded_z_quarter_physical_r2','front_corridor_lateral_physical_r1']:
 for case,task,side,key,actor in [(840023,'nudge_mailer_to_bin','left','mailer','mailer'),(840020,'push_box_to_bin','right','box','parcel_box')]:
  ep=W/run/f'case_{case}'/f'layout_{case}_{task}';args=read(ep.parent/'provenance.json')['args'];fr=read(ep/'frontal_bypass.json');pressure={r['action_step']:r for r in read(ep/'peak_load_updates.json')['rows']};initial={r['step']:r for r in read(ep/'front_initial_center.json')['rows']};recovery={r['step']:r for r in read(ep/'front_recontact_center.json')['rows']};packets=read(ep/'solved_contact_forces.json')['rows'];assert [p['after_action_step'] for p in packets]==list(range(1200))
  loads={p['after_action_step']+1:sum(abs(float(c['force_world_N'][2])) for c in p['parcel_contacts'] if any(side+'_wrist_roll' in s for s in c['shapes']) and any('/'+actor+'/' in s for s in c['shapes'])) for p in packets[:-1]}
  arrays=[]
  for name in ['trace.npz','parcel_orientation.npz']:
   p=ep/name;sources[str(p)]=sha(p)
   with np.load(p) as z:arrays.append(z[key].copy())
  kwargs=dict(rows=fr['rows'],pressure=pressure,initial=initial,recovery=recovery,xyz=arrays[0],quats=arrays[1],loads=loads,args=args,plan=fr['plan']);history=verify_stream(**kwargs)
  counts={k:sum(bool(r[k]) for r in history) for k in ['loss_invoked','outer_guard','route_restart','tilt_guard','confirmed_release','adapter']}
  row=dict(episode=str(ep.relative_to(W)),frames=len(history),counts=counts,native_output_modes=dict(collections.Counter(r['native_output_mode'] for r in history)),records=history);results.append(row);print(json.dumps({k:v for k,v in row.items() if k!='records'}),flush=True)
  # Derived fixtures only, never written under the physical episode directory.
  intervals={r['step']:dict(action_step=r['step'],observed_phase=r['observed_phase'],final_phase=r['native_final_phase'],output_mode=r['native_output_mode'],evidence={} if r['loss_invoked'] else None,disposition='loss_counter_evaluated' if r['loss_invoked'] else 'original_guard_or_nonpush_no_loss_update') for r in history}
  fixture=dict(kwargs,intervals=intervals,additional={t:False for t in intervals});verify_stream(**fixture)
  t=next(r['step'] for r in history if r['loss_invoked']);mut=copy.deepcopy(intervals);mut[t].update(evidence=None,disposition='original_guard_or_nonpush_no_loss_update')
  try:verify_stream(**dict(fixture,intervals=mut))
  except AssertionError:negative.append(dict(episode=ep.name,case='loss_evidence_omitted',step=t))
  else:raise AssertionError('Missing loss evidence accepted')
  t=next(r['step'] for r in history if r['adapter']=='handover')+1;mut=copy.deepcopy(intervals);mut[t]['observed_phase']='top_cross'
  try:verify_stream(**dict(fixture,intervals=mut))
  except AssertionError:negative.append(dict(episode=ep.name,case='handover_phase_ignored',step=t))
  else:raise AssertionError('Stale pre-handover phase accepted')
for p in [Path(__file__),W/'front_contact_window_loss_lifecycle_v1.py']:sources[str(p)]=sha(p)
for p,h in sources.items():assert sha(p)==h
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,episodes=results,frames=sum(r['frames'] for r in results),negative_rejections=negative,source_sha256=sources,full_window_force_geometry_audit=False,unloaded_planner_reconstruction=False,physics_verified=False,training_ready=False)
with (D/'FULL_PARENT_LOSS_LIFECYCLE_CHECK_V1.json').open('x') as f:json.dump(out,f,indent=2)
print('PASSED',out['frames'])
