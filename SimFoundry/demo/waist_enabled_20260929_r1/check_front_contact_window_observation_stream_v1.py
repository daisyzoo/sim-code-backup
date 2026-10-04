"""New observable verifier against actual native candidate and full parent fixtures.
817 native loaded updates are genuine candidate outputs under fixed observations.
Complete1199-row fixtures are derived from original parent records and explicitly
not new candidate episodes; front-bag incompatibility must be rejected.
"""
from pathlib import Path
import sys,json,hashlib,datetime,copy
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_contact_window_v2';D=W/'front_contact_window_preparation_r2';sys.path[:0]=[str(S),str(W),str(ROOT)]
from front_contact_window_observation_audit_v1 import force_interval,verify_interval,expected_evidence
from front_contact_window_loss_lifecycle_v2 import verify_stream
from clearance_runtime import ClearanceGuard
from audit_substep_contacts import verify_arrays
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={};cache={};guard=ClearanceGuard(ROOT,S)
def read(p):sources[str(p)]=sha(p);return json.loads(p.read_text())
def arrays(p,keys=None):
 sources[str(p)]=sha(p)
 with np.load(p,allow_pickle=False) as z:return {k:z[k].copy() for k in (z.files if keys is None else keys)}
mesh=read(ROOT/'assets/robots/g1_hand_support_vertices.json');assert sha(ROOT/mesh['source_path'])==mesh['source_sha256'];sources[str(ROOT/mesh['source_path'])]=sha(ROOT/mesh['source_path'])
def episode(name):
 if name in cache:return cache[name]
 case=int(name.split('_')[1]);ep=W/'front_loaded_z_quarter_physical_r2'/f'case_{case}'/name;side,key,actor=('left','mailer','mailer') if name.endswith('nudge_mailer_to_bin') else ('right','box','parcel_box')
 fr=read(ep/'frontal_bypass.json');raw=arrays(ep/'raw.npz',['q']);trace=arrays(ep/'trace.npz',[key]);ori=arrays(ep/'parcel_orientation.npz',[key]);record=read(ep/'SUBSTEP_CONTACT_RECORDING.json');assert record['recording_sha256']==sha(ep/'substep_contacts.npz');sub=arrays(ep/'substep_contacts.npz');packets=read(ep/'solved_contact_forces.json')['rows'];proof=verify_arrays(sub,record,packets,len(raw['q']))
 cache[name]=dict(ep=ep,fr=fr,rowmap={r['step']:r for r in fr['rows']},q=raw['q'],xyz=trace[key],quat=ori[key],record=record,sub=sub,packets=packets,side=side,key=key,actor=actor,core=fr['plan']['front_cop_slip_following']['edge_speed']['actual_core_size_xyz'],substep_proof=proof)
 return cache[name]
def context(e,t):
 values,current=force_interval(e['sub'],e['record']['metadata'],e['packets'][t-1],t,e['side'],e['actor']);T,_,_=guard.model.fk(e['side'],e['q'][t,12:23])
 return dict(step=t,values=values,current=current,target_xyz=e['xyz'][t],target_quat=e['quat'][t],core=e['core'],vertices=mesh['vertices'][e['side']],fk_pose=T,original_row=e['rowmap'][t])
native=read(D/'NATIVE_LOADED_BOUT_CHECK_V4.json');native_rows=[];negative=[];sample=None
for bout in native['bouts']:
 e=episode(bout['episode'])
 for rec in bout['records']:
  ctx=context(e,rec['step']);r=verify_interval(interval=rec['candidate_interval'],**ctx);native_rows.append(r)
  if rec['candidate_interval']['evidence'] and rec['candidate_interval']['evidence']['additional_intermittent_evidence'] and sample is None:sample=(copy.deepcopy(rec['candidate_interval']),ctx)
assert len(native_rows)==817 and sum(r['additional'] and r['evidence_recorded'] for r in native_rows)==35
base,ctx=sample
for name,edit in [('false_current_force',lambda i:i['evidence']['observation'].update(instantaneous_load_n=1.)),('wrong_tick_count',lambda i:i['evidence']['observation'].update(ticks_at_or_above_loss_threshold=0)),('false_contact',lambda i:i['evidence'].update(contact_evidence_for_loss_counter=False)),('physical_replaced_by_virtual',lambda i:i['geometry'].update(physical_support_xyz=i['geometry']['virtual_control_reference_xyz'])),('inflated_core',lambda i:i['geometry']['actual_core_xyz'].__setitem__(0,1.)),('wrong_hand',lambda i:i['geometry']['measured_hand_xyz'].__setitem__(0,0.)),('wrong_previous_step',lambda i:i['evidence']['observation'].update(after_action_step=0))]:
 bad=copy.deepcopy(base);edit(bad)
 try:verify_interval(interval=bad,**ctx)
 except (AssertionError,ValueError):negative.append(name)
 else:raise AssertionError('Accepted '+name)
# Complete synthetic log fixtures use full original parent phase reconstruction.
history_report=read(D/'FULL_PARENT_LOSS_LIFECYCLE_CHECK_V2.json');full=[]
for name,e in cache.items():
 ep=e['ep'];original=next(r for r in history_report['episodes'] if r['episode']==str(ep.relative_to(W)));history={r['step']:r for r in original['records']};intervals={};loads={};additional={};observations=[]
 for t in range(1,len(e['q'])):
  ctx=context(e,t);T=ctx['fk_pose'];rh=T[:3,:3];rt=Rotation.from_quat(e['quat'][t]).as_matrix();verts=np.array(mesh['vertices'][e['side']]);vertex=verts[np.argmin(verts@(rh.T@rt[:,2]))];physical=T[:3,3]+rh@vertex;local=rt.T@(physical-e['xyz'][t]);margin=float(min(np.array(e['core'])[:2]/2-abs(local[:2])));h=history[t];virtual=T[:3,3]+rh@np.array(e['rowmap'][t]['observed_support_offset_local'])
  geometry=dict(target_xyz=e['xyz'][t].tolist(),target_quat_xyzw=e['quat'][t].tolist(),actual_core_xyz=e['core'],measured_hand_xyz=T[:3,3].tolist(),measured_hand_quat_xyzw=Rotation.from_matrix(rh).as_quat().tolist(),physical_support_local=vertex.tolist(),physical_support_xyz=physical.tolist(),support_local_xyz=local.tolist(),current_support_core_margin_m=margin,virtual_control_reference_xyz=virtual.tolist())
  i=dict(action_step=t,observed_phase=h['observed_phase'],final_phase=h['native_final_phase'],output_mode=h['native_output_mode'],geometry=geometry,evidence=expected_evidence(t,ctx['values'],ctx['current'],margin) if h['loss_invoked'] else None,disposition='loss_counter_evaluated' if h['loss_invoked'] else 'original_guard_or_nonpush_no_loss_update',training_ready=False)
  r=verify_interval(interval=i,**ctx);observations.append(r);intervals[t]=i;loads[t]=ctx['current'];additional[t]=r['additional']
 kwargs=dict(rows=e['fr']['rows'],pressure={r['action_step']:r for r in read(ep/'peak_load_updates.json')['rows']},initial={r['step']:r for r in read(ep/'front_initial_center.json')['rows']},recovery={r['step']:r for r in read(ep/'front_recontact_center.json')['rows']},xyz=e['xyz'],quats=e['quat'],loads=loads,args=read(ep.parent/'provenance.json')['args'],plan=e['fr']['plan'],intervals=intervals,additional=additional)
 try:result=verify_stream(**kwargs)
 except AssertionError as exc:
  assert name.endswith('nudge_mailer_to_bin') and exc.args[0]==('loss result phase',790,'top_lift','top_push'),str(exc)
  result=None;full.append(dict(episode=name,fixture_only=True,observables=len(observations),expected_rejection='Original trajectory cannot impersonate window candidate: step790 original lift conflicts with new retained-contact loss counter.',rejection_detail=exc.args[0]));negative.append('old_bag_trajectory_falsely_claimed_as_window')
 else:
  assert name.endswith('push_box_to_bin');full.append(dict(episode=name,fixture_only=True,observables=len(observations),loss_stream_passed=True,extra_loss_frames=sum(r['additional_contact'] for r in result)))
 print(json.dumps(full[-1]),flush=True)
for module in list(sys.modules.values()):
 path=getattr(module,'__file__',None)
 if path:
  p=Path(path).resolve()
  if p.is_file() and p.suffix=='.py' and p.is_relative_to(ROOT):sources[str(p)]=sha(p)
sources[str(Path(__file__))]=sha(__file__)
assert 'front_window_native_v4' not in sys.modules and 'contact_window_evidence_v2' not in sys.modules
for p,h in sources.items():assert sha(p)==h
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,native_candidate_updates=len(native_rows),native_extra_loss_frames=35,complete_parent_fixtures=full,negative_rejections=negative,substep_proofs={k:e['substep_proof'] for k,e in cache.items()},source_sha256=sources,actual_new_window_episode_audited=False,training_ready=False)
with (D/'OBSERVATION_STREAM_CHECK_V1.json').open('x') as f:json.dump(out,f,indent=2)
print('PASSED',len(native_rows),len(negative))
