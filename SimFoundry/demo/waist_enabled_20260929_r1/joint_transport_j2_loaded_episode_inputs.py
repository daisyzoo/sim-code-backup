"""Read immutable episode observations without replacing any action history."""
from pathlib import Path
import json,hashlib,importlib.util
import numpy as np
from scipy.spatial.transform import Rotation
from audit_front_loaded_z_priority_parent import near
from audit_self_clearance_task_optimality import IndependentElbows
from audit_unloaded_wrist_prior_live import HandModel
from screen_bag_vertical_priority_geometry import Geometry
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
W=Path(__file__).resolve().parent;ROOT=W.parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()


def indexed(rows,count):
 assert all(type(r['step']) is int and 0<=r['step']<count for r in rows)
 result={r['step']:r for r in rows};assert len(result)==len(rows),'duplicate step'
 return result


class EpisodeInputs:
 def __init__(self,episode,*,allow_source_fixture=False):
  self.ep=Path(episode).resolve();self.sources={};self.provenance=json.loads((self.ep.parent/'provenance.json').read_text());self.sources[str(self.ep.parent/'provenance.json')]=sha(self.ep.parent/'provenance.json');self.snapshot=self.ep.parent/'source_snapshot'
  def source(name):
   keys=[n for n in self.provenance['source_sha256'] if n.endswith('/'+name)];assert len(keys)==1
   p=self.snapshot/keys[0];assert sha(p)==self.provenance['source_sha256'][keys[0]];self.sources[str(p)]=sha(p);return p
  self.source=source
  with np.load(self.ep/'raw.npz',allow_pickle=False) as z:
   self.q=z['q'][:,12:23].astype(float);self.u=z['action'][:,12:23].astype(float);self.task=str(z['task_id']);self.meta=json.loads(str(z['collect_meta']))
  self.sources[str(self.ep/'raw.npz')]=sha(self.ep/'raw.npz');self.n=len(self.q)
  from joint_transport_command_ledger_v1 import load_transport_ledger
  self.transport_parent,self.transport_proof=load_transport_ledger(self.ep,allow_source_fixture=allow_source_fixture)
  self.sources[str(self.ep/'JOINT_TRANSPORT_STREAM_V1_AUDIT.json')]=sha(self.ep/'JOINT_TRANSPORT_STREAM_V1_AUDIT.json')
  self.sources[str(W/'joint_transport_command_ledger_v1.py')]=sha(W/'joint_transport_command_ledger_v1.py')
  self.sources[str(W/'joint_transport_parent_coordinate_v1.py')]=sha(W/'joint_transport_parent_coordinate_v1.py')
  assert self.task in ['push_box_to_bin','nudge_mailer_to_bin','wait_no_package'];self.wait=self.task=='wait_no_package'
  assert self.n==self.provenance['args']['wait_steps' if self.wait else 'steps'] and self.n==(70 if self.wait else 1200)
  assert self.q.shape==self.u.shape==(self.n,11) and np.isfinite(self.q).all() and np.isfinite(self.u).all()
  assert np.max(abs(self.q[0]))<1e-4;near(self.u[0],np.zeros(11))
  self.side='right' if self.task=='push_box_to_bin' else 'left';self.key='box' if self.side=='right' else 'mailer';self.other='mailer' if self.key=='box' else 'box'
  self.front=self.read('front_initial_center.json');assert type(self.front['selected']) is bool and self.front['training_ready'] is False
  self.capture=indexed(self.front['rows'],self.n)
  if self.front['selected']:assert set(self.capture)==set(range(1,self.n))
  else:assert not self.capture
  self.initial_capture=self.capture
  self.recovery=self.read('front_recontact_center.json');recovery_rows=indexed(self.recovery['rows'],self.n)
  assert type(self.recovery['selected']) is bool and self.recovery['training_ready'] is False
  from audit_joint_transport_front_recovery_stream_v1 import verify_files as verify_recovery_files
  self.recovery_proof=verify_recovery_files(self.ep)
  assert self.recovery_proof['selected']==self.recovery['selected']
  if self.recovery['selected']:
   assert self.front['selected'] and all(r.get('context',{}).get('scene',{}).get('side',self.side)==self.side for r in recovery_rows.values()) and set(recovery_rows)==set(range(1,self.n))
  else:assert not recovery_rows
  self.capture=dict(self.initial_capture)
  for t,r in recovery_rows.items():
   if r['center_local_after'] is not None:self.capture[t]=r
  for name in ['audit_joint_transport_front_recovery_stream_v1.py','audit_front_recontact_center_events.py','audit_front_initial_center_planning_v2.py','audit_front_initial_center_preflight.py']:
   self.sources[str(W/name)]=sha(W/name)
  self.coords=indexed(self.read('coordination.json'),self.n) if (self.ep/'coordination.json').exists() else {}
  self.frontal=None if self.wait else self.read('frontal_bypass.json')
  self.rows={} if self.wait else indexed(self.frontal['rows'],self.n)
  self.experts={} if self.wait else indexed(self.read('expert_control.json'),self.n)
  if self.wait:assert not self.front['selected']
  else:assert set(self.rows)==set(range(1,self.n))
  self.packets=self.read('solved_contact_forces.json')['rows'];assert len(self.packets)==self.n and [p['after_action_step'] for p in self.packets]==list(range(self.n))
  clear=self.read('self_clearance.json');assert clear['failure'] is None and clear['requested_frames']==clear['recorded_frames']==self.n and clear['training_ready'] is False
  self.final=indexed([r for r in clear['rows'] if r['phase']=='final_command'],self.n);assert set(self.final)==set(range(self.n))
  self.geometry=Geometry(self.ep.parent);self.sources.update(self.geometry.sources)
  self.hand=HandModel(source('g1_23dof_rev_1_0_u1_black.urdf'),source('g1_hand_support_vertices.json'));self.elbows=IndependentElbows(source('elbow_torso_hulls.json'),source('g1_23dof_rev_1_0_u1_black.urdf'))
  assert sha(source('g1_assets.py'))==sha(ROOT/'simfoundry/robots/g1_assets.py')
  spec=importlib.util.spec_from_file_location('archived_bounded_original',source('bounded_ik.py'));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);self.solver=module.bounded_damped_step
  self.xyz=self.oxy=self.R=self.OR=self.size=None
  if self.front['selected']:
   with np.load(self.ep/'trace.npz') as z:self.xyz=z[self.key].copy();self.oxy=z[self.other].copy()
   with np.load(self.ep/'parcel_orientation.npz') as z:self.R=Rotation.from_quat(z[self.key]).as_matrix();self.OR=Rotation.from_quat(z[self.other]).as_matrix()
   self.size=next(r['context']['scene']['other_size'] for r in self.front['rows']+self.recovery['rows'] if r.get('context',{}).get('scene'))
   for name in ['trace.npz','parcel_orientation.npz']:self.sources[str(self.ep/name)]=sha(self.ep/name)
 def read(self,name):
  p=self.ep/name;self.sources[str(p)]=sha(p);return json.loads(p.read_text())
 def arguments(self,t,metadata,*,unissued_output=None):
  assert type(t) is int and 0<=t<self.n
  # Test-only override affects this single output; previous always comes from
  # the original actual u[t-1], never from any earlier candidate proposal.
  selected=bool(self.front['selected'] and self.capture.get(t,{}).get('center_local_after') is not None)
  from joint_transport_parent_coordinate_v1 import parent_coordinate
  coordinate=parent_coordinate(self.coords.get(t),self.transport_parent[t],self.u[t])
  return dict(step=t,selected=selected,metadata=metadata,coordinate=coordinate,row=self.rows.get(t),expert=self.experts.get(t),current=self.q[t],previous_actual=self.u[t-1] if t else np.zeros(11),output=self.transport_parent[t] if unissued_output is None else unissued_output,side=self.side,elbows=self.elbows,bounded_solver=self.solver,hand=self.hand,geometry=self.geometry,capture_row=self.capture.get(t),previous_packet=self.packets[t-1] if t else None,target_xyz=self.xyz[t] if selected else None,target_rotation=self.R[t] if selected else None,other_xyz=self.oxy[t] if selected else None,other_rotation=self.OR[t] if selected else None,other_size=self.size)
 def verify_actual_final_guard(self,t):
  record=self.final[t];command=self.u[t];q=self.q[t];previous=self.u[t-1] if t else np.zeros(11);lo=np.asarray(U1_JOINT_LIMIT_LO)[12:23].copy();hi=np.asarray(U1_JOINT_LIMIT_HI)[12:23].copy();lo[0]=-.98;hi[0]=.98;limits=np.r_[.015,np.full(10,.04)];gaps=self.elbows.gap(command)
  checks=dict(joint_bounds=bool(np.all(command>=lo-2e-7) and np.all(command<=hi+2e-7)),measured_step=bool(np.all(abs(command-q)<=limits+2e-7)),previous_slew=bool(np.max(abs(command-previous))<=.0550002),nominal_margin=bool(min(gaps)>=.005-2e-7),first_zero=bool(t!=0 or (np.array_equal(command,np.zeros(11)) and np.array_equal(previous,np.zeros(11)) and np.max(abs(q))<1e-4)))
  assert record['accepted'] is True and record['first'] is (t==0) and record['checks']==checks and all(checks.values())
  for name,value in [('command',command),('current',q),('previous',previous)]:near(record[name],value)
  near(record['gaps_m'],gaps,2e-10)
  return dict(step=t,passed=True)
