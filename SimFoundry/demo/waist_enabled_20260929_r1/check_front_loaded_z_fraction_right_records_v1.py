"""Independent record checks for unissued fractional-Z proposals on a saved episode.
Use actual raw observations/history and merged recorded initial/recontact anchors.
This tests the per-record interface; lifecycle/source and full collector audits
remain separate. Neither proposal output nor altered metadata replaces raw data.
"""
from pathlib import Path
import json,sys,copy,hashlib,datetime,importlib.util,collections
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_corridor_lateral_v1';D=W/'front_loaded_z_fraction_right_record_check_r1';D.mkdir(exist_ok=False);sys.path[:0]=[str(W),str(ROOT)]
from audit_front_loaded_z_fraction_record_v1 import verify_record
from audit_unloaded_wrist_prior_live import HandModel
from audit_self_clearance_task_optimality import IndependentElbows
from screen_bag_vertical_priority_geometry import Geometry
from audit_front_corridor_lateral_r1_v2_z_execution import recorded_rotation,RuntimeGapRepresentation
from joint_transport_parent_coordinate_v1 import parent_coordinate
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();ep=W/'front_corridor_lateral_physical_r1/case_840020/layout_840020_push_box_to_bin';indexed=lambda rows:{r['step']:r for r in rows}
co=indexed(read(ep/'coordination.json'));fr=indexed(read(ep/'frontal_bypass.json')['rows']);ex=indexed(read(ep/'expert_control.json'));packets=read(ep/'solved_contact_forces.json')['rows'];original=indexed(read(ep/'front_loaded_z_priority.json')['rows']);capture=indexed(read(ep/'front_initial_center.json')['rows'])
for t,r in indexed(read(ep/'front_recontact_center.json')['rows']).items():
 if r['center_local_after'] is not None:capture[t]=r
with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
with np.load(ep/'trace.npz') as z:xyz=z['box'].copy();oxy=z['mailer'].copy()
with np.load(ep/'parcel_orientation.npz') as z:R=np.asarray([recorded_rotation(x) for x in z['box']]);OR=np.asarray([recorded_rotation(x) for x in z['mailer']])
hand=HandModel(ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',ROOT/'assets/robots/g1_hand_support_vertices.json');elbows=IndependentElbows(S/'elbow_torso_hulls.json',ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf');geometry=RuntimeGapRepresentation(Geometry(ep.parent));provenance=read(ep.parent/'provenance.json');names=[n for n in provenance['source_sha256'] if n.endswith('/bounded_ik.py')];assert len(names)==1;source=ep.parent/'source_snapshot'/names[0];assert sha(source)==provenance['source_sha256'][names[0]];spec=importlib.util.spec_from_file_location('original_bound_solver',source);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
def arguments(t,m):
 selected=bool(capture.get(t,{}).get('center_local_after') is not None);c=None
 if t:
  c=copy.deepcopy(parent_coordinate(co[t],original[t]['output_command'],u[t]));c['front_loaded_z_priority']=copy.deepcopy(m);c['waist_target_rad']=m['output_command'][0]
  if m['applied']:c['unexecuted_parent_waist_target_rad']=m['context']['parent_command'][0]
  else:c.pop('unexecuted_parent_waist_target_rad',None)
 return dict(step=t,selected=selected,metadata=m,coordinate=c,row=fr.get(t),expert=ex.get(t),current=q[t],previous_actual=u[t-1] if t else np.zeros(11),output=np.asarray(m['output_command']),side='right',elbows=elbows,bounded_solver=mod.bounded_damped_step,hand=hand,geometry=geometry,capture_row=capture.get(t),previous_packet=packets[t-1] if t else None,target_xyz=xyz[t] if selected else None,target_rotation=R[t] if selected else None,other_xyz=oxy[t] if selected else None,other_rotation=OR[t] if selected else None,other_size=next(m['context']['other_size'] for m in original.values() if 'other_size' in m['context']),expected_fraction=.25)
def clone(args):
 return {k:v if k in ['hand','elbows','geometry','bounded_solver'] else copy.deepcopy(v) for k,v in args.items()}
import time
stream_result=W/'front_loaded_z_fraction_stream_check_r2/RESULT.json'
pid=353128
if not stream_result.exists():
 initial=Path(f'/proc/{pid}/stat').read_text().split(') ',1)[1].split()[19]
 while not stream_result.exists():
  proc=Path(f'/proc/{pid}');stat=(proc/'stat').read_text().split(') ',1)[1].split()
  assert stat[0]!='Z' and stat[19]==initial and b'check_front_loaded_z_fraction_stream_v2.py' in (proc/'cmdline').read_bytes(),'original stream ended without report'
  print(json.dumps(dict(status='waiting_for_exact_original_stream',pid=pid)),flush=True);time.sleep(10)
assert read(stream_result)['passed'] is True
paths=sorted((W/'front_loaded_z_fraction_stream_check_r2').glob('840020_push_box_to_bin_[0-9][0-9][0-9][0-9].json'));assert len(paths)>180;rows=[];sources={};example=None
for i,p in enumerate(paths):
 record=read(p);m=record['priority'];t=record['step'];args=arguments(t,m);proof=verify_record(**args);rows.append(proof);sources[str(p)]=sha(p)
 if example is None and m['applied']:example=clone(args)
 if i%20==0:
  progress=dict(checked=len(rows),expected=len(paths),last_step=t,reason_counts=dict(collections.Counter(r['reason'] for r in rows)));(D/'PROGRESS.json').write_text(json.dumps(progress,indent=2));print(json.dumps(progress),flush=True)
for t in [0,1,120]+[t for t,m in sorted(original.items()) if m['reason']=='not_top_push'][:3]:
 m=original[t];assert not m['applied'] and 'solver' not in m;proof=verify_record(**arguments(t,m));rows.append(proof)
negative=[]
for name in ['declared_fraction','changed_non_z_task','false_fallback','wrong_previous_actual','altered_output','wrong_capture','forged_success_reason']:
 a=clone(example);m=a['metadata']
 if name=='declared_fraction':m['reduced_z_task']['fraction']=.5
 elif name=='changed_non_z_task':m['reduced_z_task']['modified_task']['error'][0]+=.001
 elif name=='false_fallback':m['applied']=False
 elif name=='wrong_previous_actual':a['previous_actual'][0]+=.001
 elif name=='altered_output':a['output'][0]+=.001
 elif name=='wrong_capture':a['capture_row']['center_local_after'][0]+=.001
 elif name=='forged_success_reason':m['reason']='unverified_success'
 a['coordinate']['front_loaded_z_priority']=m
 try:verify_record(**a)
 except AssertionError:negative.append(dict(case=name,rejected=True))
 else:raise AssertionError(('tampered record accepted',name))
for n in ['coordination.json','frontal_bypass.json','expert_control.json','solved_contact_forces.json','front_loaded_z_priority.json','front_initial_center.json','front_recontact_center.json','raw.npz','trace.npz','parcel_orientation.npz']:sources[str(ep/n)]=sha(ep/n)
for module in list(sys.modules.values()):
 f=getattr(module,'__file__',None)
 if f:
  p=Path(f).resolve()
  if p.is_file() and p.suffix=='.py' and p.is_relative_to(ROOT):sources[str(p)]=sha(p)
for p in [Path(__file__),source,S/'elbow_torso_hulls.json',ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',ROOT/'assets/robots/g1_hand_support_vertices.json']:sources[str(p)]=sha(p)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,negative_rejections=negative,source_sha256=sources,passed=True,physics_started=False,full_collector_audit_complete=False,training_ready=False)
with (D/'RESULT.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(passed=True,records=len(rows),negative_rejections=len(negative),reason_counts=dict(collections.Counter(r['reason'] for r in rows)))),flush=True)
