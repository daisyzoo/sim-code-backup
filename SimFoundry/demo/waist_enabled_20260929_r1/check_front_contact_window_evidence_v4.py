"""Read-only completed-interval replay: all8reserve and first4quarter pushes.
No native phase/controller rollout: observations remain recorded. Phase comes
from actual pressure-mutation boundary, not post-update output mode.
V2 additionally requires current measured support reference >=10mm inside core;
this eligibility is not a whole-hand collision or force-bearing COP certificate.
Disabled, rear, nonpush preserve the original instantaneous loss predicate.
"""
from pathlib import Path
import sys,json,hashlib,datetime,importlib.util,copy
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;C=W/'front_contact_window_candidate_v1';sys.path.insert(0,str(C))
from contact_window_evidence_v2 import loss_counter_observation,summarize
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text());reports=[];sources={};negative=[]
paths=[]
for name,cases in [('joint_transport_reserve_physical_r1',[840022,840023,840020,840021]),('front_loaded_z_quarter_physical_r2',[840022,840023])]:
 for case in cases:
  for task in ['push_box_to_bin','nudge_mailer_to_bin']:paths.append(W/name/f'case_{case}'/f'layout_{case}_{task}')
assert len(paths)==12
for ep in paths:
 print(json.dumps(dict(starting=str(ep.relative_to(W)))),flush=True)
 prov=read(ep.parent/'provenance.json');matches=[k for k in prov['source_sha256'] if k.endswith('/peak_load_observation.py')];assert len(matches)==1
 source=ep.parent/'source_snapshot'/matches[0];assert sha(source)==prov['source_sha256'][matches[0]];spec=importlib.util.spec_from_file_location('archived_peak_observation',source);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 meta=read(ep/'SUBSTEP_CONTACT_RECORDING.json');assert meta['recording_sha256']==sha(ep/'substep_contacts.npz');m=meta['metadata'];stride=24+m['expected_manager_steps'];fr=read(ep/'frontal_bypass.json');front=fr['plan'].get('front_route_selected',False);assert type(front) is bool;side='right' if 'push_box' in ep.name else 'left';target='parcel_box' if side=='right' else 'mailer'
 with np.load(ep/'substep_contacts.npz') as z:a={k:z[k].copy() for k in z.files}
 labels=m['shape_labels'];shapes=a['shape_ids'];is_target=np.array([f'/{target}/' in x for x in labels]);is_hand=np.array([f'{side}_wrist_roll' in x for x in labels]);pair=(is_target[shapes[:,0]]&is_hand[shapes[:,1]])|(is_target[shapes[:,1]]&is_hand[shapes[:,0]]);samples=np.repeat(np.arange(len(a['contact_offsets'])-1),np.diff(a['contact_offsets']));independent=np.bincount(samples[pair],weights=abs(a['force_torque_world'][pair,2]),minlength=len(a['action_step']))
 pressure={x['action_step']:x for x in read(ep/'peak_load_updates.json')['rows']};records=[];changed=[];original_count=candidate_count=0
 if front:
  with np.load(ep/'parcel_orientation.npz') as z:rotations=Rotation.from_quat(z['box' if side=='right' else 'mailer']).as_matrix()
  half=np.asarray(fr['plan']['front_cop_slip_following']['edge_speed']['actual_core_size_xyz'])[:2]/2
 for row in fr['rows']:
  t=row['step'];step=t-1;lo=step*stride;hi=lo+stride;begin=int(a['contact_offsets'][lo]);end=int(a['contact_offsets'][hi]);packed={k:a[k][lo:hi] for k in ['action_step','substep_tick','kind']};packed.update(contact_offsets=a['contact_offsets'][lo:hi+1]-begin,shape_ids=a['shape_ids'][begin:end],force_torque_world=a['force_torque_world'][begin:end]);obs=module.extract(packed,m,after_action_step=step,side=side,target_name=target)
  ticks=a['substep_tick'][lo:hi];indices=[lo+int(np.flatnonzero(ticks==v)[0]) for v in range(1,25)];np.testing.assert_allclose(obs['vertical_load_n'],independent[indices],atol=1e-10,rtol=0)
  # Extractor and existing pressure both use original absolute-Z last tick.
  load=float(row.get('contact_load',{}).get('observed_vertical_load_n',obs['final_vertical_load_n']));assert row['mode']!='top_push' or 'contact_load' in row;phase=pressure[t]['phase_at_update'] if t in pressure else row['mode'];
  if t in pressure:assert pressure[t]['observed_vertical_load_n']==load
  core_margin=None
  if front:
   local=rotations[t].T@(np.asarray(row['observed_physical_support_xyz'])-np.asarray(row['observed_target']));core_margin=float(np.min(half-abs(local[:2])))
  args=dict(current_support_core_margin_m=core_margin,action_step=t,after_action_step=step,vertical_load_n=obs['vertical_load_n'],instantaneous_load_n=load,mode=phase)
  off=loss_counter_observation(enabled=False,selected_front=front,**args);on=loss_counter_observation(enabled=True,selected_front=front,**args);rear=loss_counter_observation(enabled=True,selected_front=False,**args)
  assert off['contact_evidence_for_loss_counter']==rear['contact_evidence_for_loss_counter']==(load>=.2)
  if phase!='top_push':assert on['contact_evidence_for_loss_counter']==off['contact_evidence_for_loss_counter'];original_count=candidate_count=0
  else:
   original_count=0 if off['contact_evidence_for_loss_counter'] else original_count+1;candidate_count=0 if on['contact_evidence_for_loss_counter'] else candidate_count+1
  if on['observation']['entire_interval_below_threshold']:assert not on['contact_evidence_for_loss_counter']
  if on['additional_intermittent_evidence']:changed.append(t)
  records.append(dict(step=t,current_support_core_margin_m=core_margin,mode_after_update=row['mode'],mode_at_pressure_update=phase,phase_bound_to_native_pressure_trace=t in pressure,additional_intermit=on['additional_intermittent_evidence'],original_counter=original_count,candidate_counter=candidate_count,observation=on['observation']))
 assert len(records)==1199
 reports.append(dict(episode=str(ep.relative_to(W)),selected_front=front,checked_intervals=len(records),changed_steps=changed,records=records))
 for p in [source,ep.parent/'provenance.json',ep/'SUBSTEP_CONTACT_RECORDING.json',ep/'substep_contacts.npz',ep/'frontal_bypass.json',ep/'peak_load_updates.json',ep/'parcel_orientation.npz']:sources[str(p)]=sha(p)
base=dict(action_step=10,after_action_step=9,vertical_load_n=[1.]*23+[0.],instantaneous_load_n=0.)
for label,delta in [('future',dict(after_action_step=10)),('stale',dict(after_action_step=8)),('short',dict(vertical_load_n=[0.]*23)),('nan',dict(vertical_load_n=[float('nan')]*24)),('negative',dict(vertical_load_n=[-1.]*23+[0.])),('wrong_final',dict(instantaneous_load_n=.1)),('bool_step',dict(action_step=True)),('negative_instant',dict(instantaneous_load_n=-1.))]:
 try:summarize(**dict(base,**delta))
 except ValueError:negative.append(label)
 else:raise AssertionError(label)
for count in [0,1,11,12,23]:
 a=dict(base,vertical_load_n=[1.]*count+[0.]*(24-count));o=loss_counter_observation(enabled=True,selected_front=True,mode='top_push',current_support_core_margin_m=.02,**a);assert o['additional_intermittent_evidence'] is (count>=12)
for p in [Path(__file__),C/'contact_window_evidence_v2.py']:sources[str(p)]=sha(p)
report=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,episodes=reports,intervals=sum(r['checked_intervals'] for r in reports),negative_rejections=negative,boundary_counts_checked=[0,1,11,12,23],source_sha256=sources,native_phase_replay=False,collector_modified=False,physics_verified=False,training_ready=False)
serialized=json.dumps(report,indent=2)
with (C/'RECORDED_INTERVAL_EVIDENCE_CHECK_V4.json').open('x') as f:f.write(serialized)
print(json.dumps(dict(passed=True,episodes=len(reports),intervals=report['intervals'],changed=[dict(episode=r['episode'],frames=len(r['changed_steps'])) for r in reports],negative_rejections=len(negative))),flush=True)
