"""Three isolated positive trailing-recovery streams with independent binding.
First recovery includes219unchanged real historical observations; later recoveries
start at an explicitly bounded counter/step boundary, not a fabricated prefix.
Candidate commands, small yaw and one post-capture endpoint are hypothetical;
no native full-horizon or physical task success is claimed.
"""
from pathlib import Path
import sys,json,copy,hashlib,datetime
import numpy as np
from scipy.spatial.transform import Rotation
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];S=W/'staged_front_box_trailing_v1';sys.path[:0]=[str(W),str(ROOT)]
from audit_front_box_trailing_front_recovery_stream_v2 import RecoveryStreamAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();src=W/'front_box_trailing_runtime_preparation_r2/MOVING_RUNTIME_CHECK.json';data=json.loads(src.read_text());assert data['complete']
for p,h in data['source_sha256'].items():assert sha(p)==h,p
family=json.loads((D/'AUDIT_FAMILY_PREPARATION.json').read_text())
for x in [*family['adapters'],*family['helpers'],family['source_binding']]:assert sha(x['path'])==x['sha256']
ep=W/'joint_transport_reserve_physical_r1/case_840020/layout_840020_push_box_to_bin';fr=json.loads((ep/'frontal_bypass.json').read_text());oldrows={r['step']:r for r in fr['rows']};coords={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};old_events={r['step']:r for r in json.loads((ep/'front_recontact_center.json').read_text())['rows']};packets={r['after_action_step']:r for r in json.loads((ep/'solved_contact_forces.json').read_text())['rows']}
with np.load(ep/'raw.npz') as z:realq=z['q'][:,12:23].astype(float);realu=z['action'][:,12:23].astype(float)
with np.load(ep/'trace.npz') as z:trace={k:z[k].copy() for k in ['box','mailer']}
with np.load(ep/'parcel_orientation.npz') as z:ori={k:z[k].copy() for k in ['box','mailer']}
results=[]
def observe(checker,e,r,c,k):return checker.observe(e,r,c,**k)
def reject(label,checker,e,r,c,k,mutate,neg):
 ch=copy.deepcopy(checker);ee,rr,cc,kk=copy.deepcopy((e,r,c,k));mutate(ee,rr,cc,kk)
 try:observe(ch,ee,rr,cc,kk)
 except (AssertionError,ValueError,KeyError):neg.append(label)
 else:raise AssertionError('Invalid stream accepted: '+label)
for ix,case in enumerate(data['rows']):
 checker=RecoveryStreamAudit(ROOT,S,'right',trailing_landing=True);first=case['trace'][0]['event'];cc=first['context'];counter=cc['recontacts'];start=cc['step'];prefix=0;neg=[];records=[]
 if ix==0:
  assert counter==1 and not any(r.get('planning') for t,r in old_events.items() if t<start);filtered=0.
  for t in range(1,start):
   row=oldrows[t];coordinate=coords[t];event={k:v for k,v in old_events[t].items() if k!='step'};assert event['kind']=='unchanged';event=dict(event,front_box_recenter_version='front_box_trailing_20mm_reserve_05mm_v1')
   measured=sum(abs(float(c['force_world_N'][2])) for c in packets[t-1]['parcel_contacts'] if any('right_wrist_roll' in n for n in c['shapes']) and any('/parcel_box/' in n for n in c['shapes']))
   if 'contact_load' in row:
    filtered=.25*measured+.75*filtered;np.testing.assert_allclose(row['contact_load']['filtered_vertical_load_n'],filtered,atol=1e-10,rtol=0)
   scene=dict(side='right',target_xyz=trace['box'][t].tolist(),target_quat=ori['box'][t].tolist(),core_size=cc['scene']['core_size'],other_xyz=trace['mailer'][t].tolist(),other_quat=ori['mailer'][t].tolist(),other_size=cc['scene']['other_size'])
   checker.observe(event,row,coordinate,step=t,current=realq[t],previous_q=realq[t-1],previous_command=realu[t-1],final_command=realu[t],scene=scene,decay=cc['decay'],observed_load_n=measured,filtered_load_n=filtered);prefix+=1
 else:
  checker.last_step=start-1;checker.counter=counter-1
 for n,entry in enumerate(case['trace']):
  event=copy.deepcopy(entry['event']);c=event['context'];handover=event['kind']=='handover';row=dict(step=c['step'],mode='top_press' if handover else 'top_cross',recontacts=counter,contact_load=dict(observed_vertical_load_n=c['observed_load_n'],filtered_vertical_load_n=c['filtered_load_n'],applied_z_bias_m=0.,stored_z_bias_m=0.),front_recontact_center_phase='measured_handover' if handover else 'tracking',target_xyz=c['scene']['target_xyz'])
  if handover:row.update(front_recontact_captured_center_local=event['captured_center_local'],projected_support_reference=event['reference'],control_offset_local=event['reference']['reference_local'],target_xyz=event['observed_support_xyz'])
  co=dict(step=c['step'],controller_kind='verified_unloaded_front_recontact_joint_path',front_recontact_center_override=event,active_side='right',bounded_solver=True,upper_q=c['current'],task_inputs=None,contact_normal_tracking=None,contact_bout_yaw_tracking=None,inactive_anchor=event['captured_inactive_anchor_world'] if handover else event['old_inactive_anchor'])
  kw=dict(step=c['step'],current=c['current'],previous_q=c['previous_q'],previous_command=c['previous_command'],final_command=event['command'],scene=c['scene'],decay=c['decay'],observed_load_n=c['observed_load_n'],filtered_load_n=c['filtered_load_n'])
  if n==0:
   for label,fn in [('skipped_step',lambda e,r,co,k:k.update(step=k['step']+1)),('counter_jump',lambda e,r,co,k:r.update(recontacts=counter+1)),('wrong_version',lambda e,r,co,k:e.update(front_box_recenter_version='front_box_recenter_v1')),('loaded_override',lambda e,r,co,k:k.update(observed_load_n=1.)),('parent_guard',lambda e,r,co,k:r.update(route_stop_reason='guard'))]:reject(label,checker,event,row,co,kw,fn,neg)
  observe(checker,event,row,co,kw);records.append(dict(step=c['step'],kind=event['kind']))
  if n==0:
   bad=copy.deepcopy(checker)
   try:bad.finish()
   except AssertionError:neg.append('unfinished_path')
   else:raise AssertionError('Unfinished path accepted')
 # After actual-shaped capture, all references must remain bound to the new
 # hypothetical endpoint. No older recorded future response is substituted.
 end=event;c=end['context'];q=np.asarray(end['proposal']['predicted_q']);scene=c['scene'];pose=checker.selection.hand.fk(q,'right');R=pose[:3,:3];normal=Rotation.from_quat(scene['target_quat']).as_matrix()[:,2];nl=R.T@normal;verts=checker.selection.hand.vertices['right'];center=np.asarray(end['captured_center_local']);ref=center+nl*(min(verts@nl)-center@nl)
 after=dict(front_box_recenter_version='front_box_trailing_20mm_reserve_05mm_v1',kind='unchanged',reason='recovery_handover_already_complete',real_recontact_index=counter,center_local_after=center.tolist());row=dict(step=c['step']+1,mode='top_press',recontacts=counter,contact_load=dict(filtered_vertical_load_n=0.),front_recontact_captured_center_local=center.tolist(),projected_support_reference=dict(center_local=center.tolist(),reference_local=ref.tolist()),control_offset_local=ref.tolist());co=dict(inactive_anchor=end['captured_inactive_anchor_world'],contact_normal_tracking=dict(target_local_up=end['captured_normal_local_up']));kw=dict(step=c['step']+1,current=q,previous_q=c['current'],previous_command=end['command'],final_command=end['command'],scene=scene,decay=c['decay'],observed_load_n=0.,filtered_load_n=0.)
 for label,fn in [('stale_center',lambda e,r,co,k:r.update(front_recontact_captured_center_local=[0.,0.,0.])),('stale_inactive_anchor',lambda e,r,co,k:co.update(inactive_anchor=[0.,0.,0.])),('stale_normal',lambda e,r,co,k:co.update(contact_normal_tracking=dict(target_local_up=[0.,0.,0.]))),('missing_reference',lambda e,r,co,k:r.pop('projected_support_reference'))]:reject(label,checker,after,row,co,kw,fn,neg)
 observe(checker,after,row,co,kw);r=checker.finish();assert r['verified_commands']==len(case['trace']) and r['handovers']==1;out=dict(start_step=start,counter=counter,unchanged_actual_prefix_frames=prefix,isolated_counter_boundary=ix!=0,commands=r['verified_commands'],handovers=r['handovers'],predicted_preflight_trials=r['preflights'][0]['trials'],post_capture_reference_checked=True,negative_rejections=neg,records=records);results.append(out);(D/'RECOVERY_STREAM_PROGRESS.json').write_text(json.dumps(dict(completed=len(results),expected=3,rows=results,training_ready=False),indent=2));print(json.dumps({k:v for k,v in out.items() if k!='records'}),flush=True)
sources={str(p):sha(p) for p in [Path(__file__),src,D/'AUDIT_FAMILY_PREPARATION.json',ep/'frontal_bypass.json',ep/'coordination.json',ep/'front_recontact_center.json',ep/'solved_contact_forces.json',ep/'raw.npz',ep/'trace.npz',ep/'parcel_orientation.npz',S/'elbow_torso_hulls.json',ROOT/'assets/robots/g1_hand_support_vertices.json',ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf']}
for mod in list(sys.modules.values()):
 f=getattr(mod,'__file__',None)
 if f:
  p=Path(f).resolve()
  if p.is_file() and p.suffix=='.py' and p.is_relative_to(ROOT):sources[str(p)]=sha(p)
assert not any(n.startswith('trailing_') for n in sys.modules)
with (D/'RECOVERY_STREAM_CHECK.json').open('x') as f:json.dump(dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,streams=3,commands=sum(x['commands'] for x in results),rows=results,source_sha256=sources,candidate_imports=False,full_native_push_fixture=False,physical_started=False,training_ready=False),f,indent=2)
print('COMPLETE3',flush=True)
