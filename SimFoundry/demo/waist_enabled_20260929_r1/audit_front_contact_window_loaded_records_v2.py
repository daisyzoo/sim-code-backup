"""Independent audit of fixed-observation native loaded-bout records only.
No candidate observer, supporting-vertex helper or controller decision is called.
Current instantaneous force is independently read from original solved-packet
JSON, while the 24-tick history is from substep NPZ. Original 1e-5N consistency
is checked separately; the two arithmetic paths are not silently substituted.
Recomputes original 24 solved-tick absolute-Z force and support geometry from
archived contacts, collision vertices, orientations and raw-joint FK. This is not
an episode auditor, full-prefix lifecycle proof or fresh physical validation.
"""
from pathlib import Path
import sys,json,hashlib,datetime,copy,collections
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_contact_window_v2';D=W/'front_contact_window_preparation_r2'
sys.path[:0]=[str(S),str(ROOT)]
from clearance_runtime import ClearanceGuard
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
sources={}
def read(p):
 sources[str(p)]=sha(p);return json.loads(p.read_text())
def close(a,b,tol=1e-8):
 assert np.isfinite(np.asarray(a,dtype=float)).all()
 np.testing.assert_allclose(a,b,rtol=0,atol=tol)
def check(actual,expected):
 if isinstance(expected,dict):
  assert isinstance(actual,dict) and actual.keys()==expected.keys(),('keys',actual.keys(),expected.keys())
  for k,v in expected.items():check(actual[k],v)
 elif isinstance(expected,bool):assert type(actual) is bool and actual==expected
 elif isinstance(expected,(int,str)) or expected is None:assert type(actual) is type(expected) and actual==expected,(actual,expected)
 elif isinstance(expected,list):
  assert len(actual)==len(expected)
  for a,b in zip(actual,expected):check(a,b)
 else:close(actual,expected)

def original_ticks(a,m,t,side,actor):
 managers=m['expected_manager_steps'];assert m['expected_substeps']==24 and managers in (1,8)
 width=24+managers;start=(t-1)*width;end=start+width
 ticks=[];kinds=[]
 for manager in range(managers):
  for tick in range(manager*24//managers,(manager+1)*24//managers):ticks.append(tick);kinds.append(0)
  ticks.append((manager+1)*24//managers);kinds.append(1)
 assert a['action_step'][start:end].tolist()==[t-1]*width
 assert a['substep_tick'][start:end].tolist()==ticks and a['kind'][start:end].tolist()==kinds
 offsets=a['contact_offsets'];assert np.issubdtype(offsets.dtype,np.integer) and np.all(np.diff(offsets[start:end+1])>=0)
 labels=m['shape_labels'];values=[]
 for tick in range(1,25):
  sample=start+ticks.index(tick);lo,hi=int(offsets[sample]),int(offsets[sample+1]);total=0.
  for shapes,force in zip(a['shape_ids'][lo:hi],a['force_torque_world'][lo:hi]):
   assert len(shapes)==2 and all(0<=int(s)<len(labels) for s in shapes) and np.isfinite(force).all()
   names=[labels[int(s)] for s in shapes]
   if any(f'{side}_wrist_roll' in n for n in names) and any('/'+actor+'/' in n for n in names):total+=abs(float(force[2]))
  values.append(total)
 return values

report=read(D/'NATIVE_LOADED_BOUT_CHECK_V4.json');assert report['passed'] and report['total_native_updates']==817
for p,h in report['source_sha256'].items():assert sha(p)==h,('changed source',p)
mesh=read(ROOT/'assets/robots/g1_hand_support_vertices.json');asset=ROOT/mesh['source_path'];assert sha(asset)==mesh['source_sha256'];sources[str(asset)]=sha(asset)
guard=ClearanceGuard(ROOT,S);cache={};contexts=[];counts=collections.Counter();max_support_error=0.
for bout in report['bouts']:
 name=bout['episode'];case=int(name.split('_')[1]);side,key,actor=('left','mailer','mailer') if name.endswith('nudge_mailer_to_bin') else ('right','box','parcel_box')
 if name not in cache:
  ep=W/'front_loaded_z_quarter_physical_r2'/f'case_{case}'/name
  fr=read(ep/'frontal_bypass.json');rows={r['step']:r for r in fr['rows']};m=read(ep/'SUBSTEP_CONTACT_RECORDING.json');assert sha(ep/'substep_contacts.npz')==m['recording_sha256']
  arrays=[]
  for file in ['raw.npz','trace.npz','parcel_orientation.npz','substep_contacts.npz']:
   p=ep/file;sources[str(p)]=sha(p)
   with np.load(p) as z:arrays.append({k:z[k].copy() for k in z.files if file!='raw.npz' or k=='q'})
  packets={r['after_action_step']:r for r in read(ep/'solved_contact_forces.json')['rows']}
  cache[name]=(fr,rows,m['metadata'],*arrays,packets)
 fr,rows,m,raw,trace,ori,a,packets=cache[name];core=np.array(fr['plan']['front_cop_slip_following']['edge_speed']['actual_core_size_xyz']);verts=np.array(mesh['vertices'][side]);previous_counter=0;previous_mode='top_push';previous_recontacts=rows[bout['start_state_after_step']]['recontacts']
 steps=[r['step'] for r in bout['records']];assert steps==list(range(bout['start_state_after_step']+1,bout['last_action']+1)) and len(steps)==bout['native_updates']
 for record in bout['records']:
  t=record['step'];native=record['candidate_native_row'];values=original_ticks(a,m,t,side,actor);instant=sum(abs(float(c['force_world_N'][2])) for c in packets[t-1]['parcel_contacts'] if any(f'{side}_wrist_roll' in n for n in c['shapes']) and any('/'+actor+'/' in n for n in c['shapes']));close(instant,values[-1],1e-5);count=sum(v>=.2 for v in values);q=raw['q'][t,12:23];T,_,_=guard.model.fk(side,q);R=Rotation.from_quat(ori[key][t]).as_matrix();vertex=verts[np.argmin(verts@(T[:3,:3].T@R[:,2]))];point=T[:3,3]+T[:3,:3]@vertex;local=R.T@(point-trace[key][t]);margin=float(np.min(core[:2]/2-np.abs(local[:2])))
  max_support_error=max(max_support_error,float(np.max(np.abs(point-rows[t]['observed_physical_support_xyz']))));close(point,rows[t]['observed_physical_support_xyz'],1e-4)
  tilt=float(np.arccos(np.clip(R[2,2],-1,1)));route=rows[t]['direction_change_recontact'];route_restart=bool(route['stage_changed'] and route['restarted']);tilt_guard=tilt>rows[t]['tilt_recontact_threshold_rad']
  # In these 19 loaded bouts there are exactly two original pre-loss guards.
  # Reject unsupported branch families rather than guess their lifecycle.
  no_loss=tilt_guard or route_restart
  if no_loss:assert native['last_recontact_reason'] in ('incipient_tilt_independent','front_route_direction_change')
  original=instant>=.2;extra=not original and margin>=.010 and count>=12;present=original or extra
  if no_loss:expected_counter=0;expected_mode='top_lift'
  else:
   expected_counter=0 if present else previous_counter+1
   if expected_counter>=3:expected_counter=0;expected_mode='top_lift'
   else:expected_mode='top_push'
  expected_recontacts=previous_recontacts+(expected_mode=='top_lift')
  evidence=None if no_loss else dict(observation=dict(version='previous24_interior_half_contact_evidence_v2',action_step=t,after_action_step=t-1,solver_substeps=24,instantaneous_load_n=instant,mean_abs_vertical_load_n=sum(values)/24,peak_abs_vertical_load_n=max(values),ticks_at_or_above_loss_threshold=count,majority_contact_evidence=count>=12,entire_interval_below_threshold=count==0,original_loss_threshold_n=.2,training_ready=False),original_contact_evidence=original,contact_evidence_for_loss_counter=present,additional_intermittent_evidence=extra,enabled=True,selected_front=True,mode='top_push',current_support_core_margin_m=margin,minimum_core_margin_m=.010,current_support_interior=margin>=.010,current_force_preserved=True,current_cop_available_from_window=False,phase_or_command_modified=False,training_ready=False)
  ctx=dict(step=t,previous_mode=previous_mode,expected_mode=expected_mode,counter=expected_counter,recontacts=expected_recontacts,instant=instant,evidence=evidence,no_loss=no_loss,geometry=dict(target_xyz=trace[key][t].tolist(),physical_support_xyz=point.tolist(),virtual_control_reference_xyz=rows[t]['observed_support_xyz'],physical_support_local=vertex.tolist(),measured_hand_xyz=T[:3,3].tolist(),target_quat_xyzw=ori[key][t].tolist(),actual_core_xyz=core.tolist(),support_local_xyz=local.tolist(),current_support_core_margin_m=margin),hand_rotation=T[:3,:3],record=record,episode=name)
  contexts.append(ctx);counts['records']+=1;counts['no_loss_guards']+=no_loss;counts['loss_evaluated']+=not no_loss;counts['extra_contact_evidence']+=bool(extra and not no_loss)
  previous_counter=expected_counter;previous_mode=expected_mode;previous_recontacts=expected_recontacts

def verify_record(record,ctx):
 assert record['step']==ctx['step'] and type(record['step']) is int
 i=record['candidate_interval'];native=record['candidate_native_row'];assert native['contact_window_interval']==i
 assert i['action_step']==ctx['step'] and type(i['action_step']) is int
 assert i['observed_phase']==ctx['previous_mode'] and i['final_phase']==ctx['expected_mode'] and i['output_mode']==ctx['expected_mode']
 assert native['mode']==record['candidate_mode']==ctx['expected_mode'];assert record['candidate_counter']==ctx['counter'] and type(record['candidate_counter']) is int
 assert native['recontacts']==ctx['recontacts'];close(native['contact_load']['observed_vertical_load_n'],ctx['instant'],1e-5)
 assert i['training_ready'] is False
 assert i['disposition']==('original_guard_or_nonpush_no_loss_update' if ctx['no_loss'] else 'loss_counter_evaluated')
 check(i['evidence'],ctx['evidence'])
 for k,v in ctx['geometry'].items():close(i['geometry'][k],v)
 close(Rotation.from_quat(i['geometry']['measured_hand_quat_xyzw']).as_matrix(),ctx['hand_rotation'])
 # The synthetic native output must retain its actual virtual reference.
 close(native['observed_support_xyz'],ctx['geometry']['virtual_control_reference_xyz'])

for ctx in contexts:verify_record(ctx['record'],ctx)
# Counterexamples share the same verified raw context; never recompute expected
# values from edited candidate records. Mutate both serialized copies to avoid
# rejecting merely because one duplicate changed.
base=next(c for c in contexts if c['evidence'] and c['evidence']['additional_intermittent_evidence']);negative=[]
def rejected(name,edit,ctx=base):
 r=copy.deepcopy(ctx['record']);edit(r);r['candidate_native_row']['contact_window_interval']=copy.deepcopy(r['candidate_interval'])
 try:verify_record(r,ctx)
 except (AssertionError,ValueError,TypeError,KeyError):negative.append(name)
 else:raise AssertionError('Mutation accepted: '+name)
rejected('stale_action',lambda r:r['candidate_interval'].update(action_step=r['step']-1))
rejected('missing_evidence_with_consistent_disposition',lambda r:r['candidate_interval'].update(evidence=None,disposition='original_guard_or_nonpush_no_loss_update'))
rejected('incorrect_observed_phase',lambda r:r['candidate_interval'].update(observed_phase='top_press'))
rejected('false_early_exit',lambda r:r['candidate_interval'].update(final_phase='top_lift'))
rejected('incorrect_counter',lambda r:r.update(candidate_counter=2))
rejected('wrong_tick_count',lambda r:r['candidate_interval']['evidence']['observation'].update(ticks_at_or_above_loss_threshold=0))
rejected('stale_previous_action',lambda r:r['candidate_interval']['evidence']['observation'].update(after_action_step=r['step']-2))
rejected('changed_current_force',lambda r:r['candidate_interval']['evidence']['observation'].update(instantaneous_load_n=.3))
rejected('invented_current_cop',lambda r:r['candidate_interval']['evidence'].update(current_cop_available_from_window=True))
rejected('wrong_hand_geometry',lambda r:r['candidate_interval']['geometry']['measured_hand_xyz'].__setitem__(0,0.))
rejected('virtual_as_physical',lambda r:r['candidate_interval']['geometry'].update(physical_support_xyz=r['candidate_interval']['geometry']['virtual_control_reference_xyz']))
rejected('inflated_core',lambda r:r['candidate_interval']['geometry']['actual_core_xyz'].__setitem__(0,1.))
rejected('fabricated_margin',lambda r:r['candidate_interval']['geometry'].update(current_support_core_margin_m=.04))
rejected('admission_claim',lambda r:r['candidate_interval'].update(training_ready=True))
ctx=next(c for c in contexts if c['no_loss']);rejected('guard_fabricates_loss_evidence',lambda r:r['candidate_interval'].update(evidence=base['evidence'],disposition='loss_counter_evaluated'),ctx)
for kind in ['missing','duplicate','reordered']:
 rs=copy.deepcopy(report['bouts'][0]['records']);expected=list(range(report['bouts'][0]['start_state_after_step']+1,report['bouts'][0]['last_action']+1))
 if kind=='missing':rs.pop()
 elif kind=='duplicate':rs.append(rs[-1])
 else:rs[:2]=reversed(rs[:2])
 assert [r['step'] for r in rs]!=expected;negative.append(kind+'_update')
for module in list(sys.modules.values()):
 p=getattr(module,'__file__',None)
 if p:
  p=Path(p).resolve()
  if p.is_file() and p.suffix=='.py' and p.is_relative_to(ROOT):sources[str(p)]=sha(p)
sources[str(Path(__file__).resolve())]=sha(__file__)
assert not any(n in sys.modules for n in ['contact_window_evidence_v2','front_window_native_v4','peak_load_observation'])
for p,h in sources.items():assert sha(p)==h
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,bouts=len(report['bouts']),counts=dict(counts),max_independent_support_error_m=max_support_error,negative_cases_rejected=negative,candidate_decision_imported=False,source_sha256=sources,limitations=['Fixed historical observations; no new physics','Loaded bouts seeded at original top_push entry, not whole episode','Only original tilt and route pre-loss guards appear; other branch families need independent full-stream coverage','Pending/active in-memory ownership and exceptions require separate runtime fixtures','Full original audit family and source-binding still required'],training_ready=False)
with (D/'INDEPENDENT_LOADED_RECORD_AUDIT_V2.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps({k:v for k,v in out.items() if k!='source_sha256'}))
