"""Independent contact-window observable reconstruction. No controller imports.
Original instantaneous force comes from solved JSON; preceding24 solved ticks
from the separately recorded NPZ. Physical supporting vertex is independently
selected from actual collision vertices and measured hand/object transforms.
"""
import math
import numpy as np

def near(a,b,tol=1e-8):
 a,b=np.asarray(a,dtype=float),np.asarray(b,dtype=float)
 assert a.shape==b.shape and np.isfinite(a).all() and np.isfinite(b).all()
 assert np.max(np.abs(a-b),initial=0)<=tol,('observation mismatch',float(np.max(np.abs(a-b),initial=0)))

def same(actual,expected):
 if isinstance(expected,dict):
  assert isinstance(actual,dict) and actual.keys()==expected.keys()
  for k,v in expected.items():same(actual[k],v)
 elif isinstance(expected,bool):assert type(actual) is bool and actual==expected
 elif isinstance(expected,(str,int)) or expected is None:assert type(actual) is type(expected) and actual==expected
 else:near(actual,expected)

def rotation(quat):
 assert len(quat)==4 and all(math.isfinite(float(v)) for v in quat)
 x,y,z,w=(float(v) for v in quat);n=math.sqrt(x*x+y*y+z*z+w*w);assert abs(n-1)<1e-4
 x,y,z,w=x/n,y/n,z/n,w/n
 return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])

def force_interval(arrays,metadata,packet,step,side,actor):
 assert type(step) is int and step>0 and packet['after_action_step']==step-1
 assert (side,actor) in [('left','mailer'),('right','parcel_box')]
 m=metadata;managers=m['expected_manager_steps'];assert m['expected_substeps']==24 and managers in (1,8)
 width=24+managers;begin=(step-1)*width;end=begin+width;ticks=[];kinds=[]
 for k in range(managers):ticks+=list(range(k*24//managers,(k+1)*24//managers))+[(k+1)*24//managers];kinds += [0]*(24//managers)+[1]
 assert arrays['action_step'][begin:end].tolist()==[step-1]*width
 assert arrays['kind'][begin:end].tolist()==kinds and arrays['substep_tick'][begin:end].tolist()==ticks
 labels=m['shape_labels'];offsets=arrays['contact_offsets'];assert np.issubdtype(offsets.dtype,np.integer) and np.all(np.diff(offsets[begin:end+1])>=0)
 def selected(names):return any(side+'_wrist_roll' in s for s in names) and any('/'+actor+'/' in s for s in names)
 values=[]
 for tick in range(1,25):
  sample=begin+ticks.index(tick);lo,hi=int(offsets[sample]),int(offsets[sample+1]);value=0.
  for ids,f in zip(arrays['shape_ids'][lo:hi],arrays['force_torque_world'][lo:hi]):
   assert len(ids)==2 and all(0<=s<len(labels) for s in ids) and np.isfinite(f).all()
   if selected([labels[int(s)] for s in ids]):value+=abs(float(f[2]))
  values.append(value)
 current=sum(abs(float(c['force_world_N'][2])) for c in packet['parcel_contacts'] if selected(c['shapes']))
 assert math.isfinite(current) and current>=0;near(current,values[-1],1e-5)
 return values,current

def expected_evidence(step,values,current,margin):
 assert len(values)==24 and all(math.isfinite(x) and x>=0 for x in values) and math.isfinite(margin)
 count=sum(x>=.2 for x in values);original=current>=.2;extra=bool(not original and margin>=.010 and count>=12)
 return dict(observation=dict(version='previous24_interior_half_contact_evidence_v2',action_step=step,after_action_step=step-1,solver_substeps=24,instantaneous_load_n=current,mean_abs_vertical_load_n=sum(values)/24,peak_abs_vertical_load_n=max(values),ticks_at_or_above_loss_threshold=count,majority_contact_evidence=count>=12,entire_interval_below_threshold=count==0,original_loss_threshold_n=.2,training_ready=False),original_contact_evidence=original,contact_evidence_for_loss_counter=original or extra,additional_intermittent_evidence=extra,enabled=True,selected_front=True,mode='top_push',current_support_core_margin_m=margin,minimum_core_margin_m=.010,current_support_interior=margin>=.010,current_force_preserved=True,current_cop_available_from_window=False,phase_or_command_modified=False,training_ready=False)

def verify_interval(*,interval,step,values,current,target_xyz,target_quat,core,vertices,fk_pose,original_row):
 assert interval['action_step']==step and type(interval['action_step']) is int and interval['training_ready'] is False
 g=interval['geometry'];near(g['target_xyz'],target_xyz,0);near(g['target_quat_xyzw'],target_quat,0);near(g['actual_core_xyz'],core,0)
 rh=rotation(g['measured_hand_quat_xyzw']);rt=rotation(target_quat);hand=np.asarray(g['measured_hand_xyz'],float);near(hand,fk_pose[:3,3],1e-4);near(rh,fk_pose[:3,:3],1e-4)
 vertices=np.asarray(vertices,float);assert vertices.ndim==2 and vertices.shape[1]==3 and np.isfinite(vertices).all()
 scores=vertices@(rh.T@rt[:,2]);vertex=vertices[int(np.argmin(scores))];physical=hand+rh@vertex;local=rt.T@(physical-target_xyz);margin=float(min(np.asarray(core)[:2]/2-np.abs(local[:2])))
 near(g['physical_support_local'],vertex,0);near(g['physical_support_xyz'],physical);near(g['support_local_xyz'],local);near(g['current_support_core_margin_m'],margin)
 near(physical,original_row['observed_physical_support_xyz'],2e-6);near(vertex,original_row['physical_support_offset_local'],0)
 # The incoming offset survives collector downstream planner overrides; the
 # final row's observed_support_xyz may already refer to the newly captured point.
 virtual=hand+rh@np.asarray(original_row['observed_support_offset_local'])
 near(g['virtual_control_reference_xyz'],virtual,2e-6)
 expected=expected_evidence(step,values,current,margin)
 if interval['evidence'] is not None:same(interval['evidence'],expected)
 return dict(step=step,current_load_n=current,contact_ticks=expected['observation']['ticks_at_or_above_loss_threshold'],core_margin_m=margin,additional=expected['additional_intermittent_evidence'],evidence_recorded=interval['evidence'] is not None,physical_vs_virtual_distance_m=float(np.linalg.norm(physical-virtual)),training_ready=False)
