"""Recorded front-bag Z chain: pressure target, pre-Z, post-Z, post-transport,
actual emitted servo target and next measured support. Kinematic target motion
is not a force prediction or guaranteed one-frame movement. No gate/admission.
"""
from pathlib import Path
import datetime,hashlib,json,sys
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_effective_height_v1';sys.path[:0]=[str(S),str(W),str(ROOT)]
from articulated_hand_geometry import ArticulatedHandGeometry
model=ArticulatedHandGeometry(ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',ROOT/'assets/robots/g1_hand_support_vertices.json')
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
sources={str(Path(__file__)):sha(Path(__file__)),str(S/'articulated_hand_geometry.py'):sha(S/'articulated_hand_geometry.py'),**model.source_sha256};versions=[]
def point(q,normal,center):
 T=model.fk('left',q)[0];n=T[:3,:3].T@normal;offset=center+n*(min(model.vertices['left']@n)-center@n);return T[:3,3]+T[:3,:3]@offset

def stats(vals):
 return None if not vals else dict(n=len(vals),min=float(min(vals)),median=float(np.median(vals)),mean=float(np.mean(vals)),max=float(max(vals)))
for run in ['front_loaded_z_quarter_physical_r2','front_effective_height_physical_r1']:
 ep=W/run/'case_840023/layout_840023_nudge_mailer_to_bin';fr=read(ep/'frontal_bypass.json');coords={r['step']:r for r in read(ep/'coordination.json')};press={r['action_step']:r for r in read(ep/'peak_load_updates.json')['rows']};trans={r['step']:r for r in read(ep/'joint_transport_clearance.json')['rows']};observed=read(ep/'OBSERVED24_CONTACT_BOUT_DIAGNOSTIC.json');loads={r['step']:r for r in observed['rows']}
 for p,h in observed['source_sha256'].items():assert sha(p)==h,p
 with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
 with np.load(ep/'parcel_orientation.npz') as z:rot=Rotation.from_quat(z['mailer']).as_matrix()
 records=[]
 for r in fr['rows']:
  t=r['step']
  if r['mode']!='top_push':continue
  c=coords[t];a=c['task_inputs'];z=c['front_loaded_z_priority'];tp=trans[t];p=press[t];ctx=z['context'];normal=rot[t,:,2];center=np.array(c['active_support_reference']['center_local']);current=point(q[t],normal,center)
  np.testing.assert_allclose(current,r['observed_support_xyz'],rtol=0,atol=2e-6);np.testing.assert_allclose(a['current'],q[t],rtol=0,atol=1e-7);np.testing.assert_array_equal(a['previous'],u[t-1]);np.testing.assert_array_equal(tp['parent_command'],z['output_command']);assert c['joint_transport_clearance']==tp
  desired=np.array(r['target_xyz']);np.testing.assert_allclose(a['error'][:3],np.clip(.72*(desired-current),-.035,.035),rtol=0,atol=2e-6)
  base=np.array(ctx['parent_command']);zcmd=np.array(z['output_command']);tcmd=np.array(tp['output_command']);assert p['before']['desired_n']==5. and p['before']['min_bias_m']==-.006
  commands={'before_z':base,'after_z':zcmd,'after_transport':tcmd,'emitted':u[t]};nom={k:float((point(v,normal,center)[2]-current[2])*1000) for k,v in commands.items()};J=np.array(a['jacobian']);active=[0,1,2,3,4,5];lo=np.array(a['lower']);hi=np.array(a['upper']);lim=np.array(a['step_limits'])
  record=dict(step=t,z_applied=z['applied'],transport_applied=tp['applied'],transport_equals_emitted=bool(np.array_equal(tcmd,u[t])),desired_support_error_z_mm=float((desired[2]-current[2])*1000),full_linear_requested_z_mm=float(a['error'][2]*1000),effective_linear_requested_z_mm=float(z.get('reduced_z_task',{}).get('modified_requested_z_m',a['error'][2])*1000),nominal_dz_mm=nom,final_linear_z_mm=float(J[2]@(u[t]-q[t])*1000),next_actual_frozen_support_dz_mm=None if t+1==len(q) else float((point(q[t+1],normal,center)[2]-current[2])*1000),bias_m=r['contact_load']['applied_z_bias_m'],pressure_guard_held=p['returned']['peak_bias_guard']['held_negative_increment'],load_lasttick_n=loads[t]['last_tick_load_n'],mean24_load_n=loads[t]['previous24_load']['mean'],peak24_load_n=loads[t]['previous24_load']['max'],active_absolute_limit_margin_rad=float(np.min(np.minimum(u[t]-lo,hi-u[t])[active])),active_current_step_limit_margin_rad=float(np.min((lim-abs(u[t]-q[t]))[active])),active_tracking_error_rad=float(np.max(abs(u[t-1,active]-q[t,active]))))
  records.append(record)
 def summarize(rs):
  keys=['desired_support_error_z_mm','full_linear_requested_z_mm','effective_linear_requested_z_mm','next_actual_frozen_support_dz_mm','load_lasttick_n','mean24_load_n','peak24_load_n','active_tracking_error_rad']
  return dict(frames=len(rs),bias_at_min=sum(abs(r['bias_m']+.006)<1e-10 for r in rs),peak_guard_held=sum(r['pressure_guard_held'] for r in rs),transport_applied=sum(r['transport_applied'] for r in rs),final_emission_mismatches=sum(not r['transport_equals_emitted'] for r in rs),active_absolute_limit_near=sum(r['active_absolute_limit_margin_rad']<1e-5 for r in rs),active_current_step_limit_near=sum(r['active_current_step_limit_margin_rad']<1e-5 for r in rs),values={k:stats([r[k] for r in rs if r[k] is not None]) for k in keys},nominal_dz_mm={k:stats([r['nominal_dz_mm'][k] for r in rs]) for k in ['before_z','after_z','after_transport','emitted']})
 versions.append(dict(run=run,summary=summarize(records),first_bout=summarize([r for r in records if observed['bouts'][0]['start']<=r['step']<=observed['bouts'][0]['end']]),records=records))
 for n in ['raw.npz','coordination.json','frontal_bypass.json','parcel_orientation.npz','joint_transport_clearance.json','peak_load_updates.json','OBSERVED24_CONTACT_BOUT_DIAGNOSTIC.json']:sources[str(ep/n)]=sha(ep/n)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,versions=versions,source_sha256=sources,training_ready=False,limitations=['Joint velocity/actuator torque are not recorded; no motor saturation identification.','Loaded contact blocks free-space motion: negative nominal Z does not imply actual penetration should occur.','Bias-min and low-load correlations also occur in historical successes; not a sufficient failure classifier.','Whole control audits remain independent and required.'])
encoded=json.dumps(report,indent=2)
with (W/'front_effective_height_physical_r1/FRONT_BAG_LOADED_COMMAND_CHAIN_V1.json').open('x') as f:f.write(encoded)
print(json.dumps([dict(run=v['run'],summary=v['summary']) for v in versions]))
