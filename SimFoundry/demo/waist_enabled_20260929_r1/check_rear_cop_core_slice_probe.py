"""Frozen-history parity, independent force COP and LP core-slice validation."""
from pathlib import Path
import json,sys,hashlib,importlib.util,ast
import numpy as np
from scipy.optimize import linprog
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path.insert(0,str(repo));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def module(p,n):
 spec=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(spec);sys.modules[n]=m;spec.loader.exec_module(m);return m
stage=w/'staged_rear_cop_core_slice_probe';old=module(w/'staged_rear_cop_measured_bounds/rear_cop_centering.py','old_core_probe');new=module(stage/'rear_cop_centering.py','new_core_probe')
def independent_interval(cop,R,size):
 h=size[:2]/2-.01;a=R[0,:2];A=np.r_[a,-a][:,None];b=np.r_[h-cop[:2],h+cop[:2]]
 lo=linprog([1.],A_ub=A,b_ub=b,bounds=[(None,None)],method='highs');hi=linprog([-1.],A_ub=A,b_ub=b,bounds=[(None,None)],method='highs')
 if lo.status==2 or hi.status==2:return None
 assert lo.success and hi.success
 return float(lo.x[0]),float(hi.x[0])
reports=[]
for run in ['region_continuity_groups_r1','region_causal_response_groups_r1','region_causal_xy_groups_r2','region_measured_bounds_groups_r1','rear_cop_measured_bounds_groups_r1']:
 for cid,task in [(840001,'push_box_to_bin'),(840004,'nudge_mailer_to_bin')]:
  ep=w/run/f'case_{cid}/layout_{cid}_{task}';fr=json.loads((ep/'frontal_bypass.json').read_text());key='box' if cid==840001 else 'mailer';side='right' if key=='box' else 'left';actor='parcel_box' if key=='box' else 'mailer';src=json.loads((ep.parent/'provenance.json').read_text())['source_sha256'];cfg=ep.parent/'source_snapshot/simfoundry/scene_bridge/isaac_cfg.py';assert sha(cfg)==src['simfoundry/scene_bridge/isaac_cfg.py'];node=next(n for n in ast.walk(ast.parse(cfg.read_text())) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='core_scale' for t in n.targets));assert ast.unparse(node.value.test)=="obj.semantic == 'mailer'";scale=np.array(ast.literal_eval(node.value.orelse if key=='box' else node.value.body));size=np.array(fr['plan']['top_recontact']['contact_size_xyz'])*scale
  with np.load(ep/'trace.npz') as z:xyz=z[key].astype(float)
  with np.load(ep/'parcel_orientation.npz') as z:R=Rotation.from_quat(z[key]).as_matrix()
  packets={p['after_action_step']:p for p in json.loads((ep/'solved_contact_forces.json').read_text())['rows']};a=old.RearCopCentering();b=new.RearCopCentering();c=new.RearCopCentering(core_slice_feedback=True);previous=None;rows=[];actual=[];parity=0
  for f in fr['rows']:
   t=f['step'];packet=packets.get(t-1);points=[];weights=[]
   if packet is not None:
    assert max(abs(np.array(packet['post_action_pose'][key])-xyz[t]))<1e-6
    for k in packet['parcel_contacts']:
     slots=[i for i,s in enumerate(k['shapes']) if '/'+actor+'/' in s]
     if len(slots)!=1 or not any(side+'_wrist' in s for s in k['shapes']):continue
     force=np.array(k['force_world_N'])*(1 if slots[0]==1 else -1);normal=-float(force@R[t,:,2])
     if normal>.05:points.append(k['position_world']);weights.append(normal)
   normal=sum(weights);cop=R[t].T@(np.average(points,axis=0,weights=weights)-xyz[t]) if weights else None;reference=np.array(f['observed_support_xyz']);parent=np.array(f['target_xyz']);prev=reference if previous is None else previous
   kw=dict(mode=f['mode'],parent_xyz=parent,previous_xyz=prev,reference_xyz=reference,object_xyz=xyz[t],object_rotation=R[t],core_size=size,cop_local=cop,normal_load_n=normal)
   oa=a.update(**kw);ob=b.update(**kw);assert oa==ob;parity+=1;oc=c.update(**kw);iv=None
   if f['mode']=='top_push' and cop is not None and normal>=.3:
    iv=independent_interval(cop,R[t],size);got=new.world_x_core_interval(cop,R[t],size);assert (iv is None)==(got is None)
    if iv is not None:assert max(abs(np.array(iv)-got))<1e-8
   if oc['override']:
    assert iv is not None;error=float(np.clip(0,*iv));wanted=prev[0]+oc['feed_x_m']+.05*error;expected=np.clip(wanted,max(prev[0]-.002,reference[0]-.030),min(prev[0]+.002,reference[0]+.030));assert abs(oc['error_x_m']-error)<1e-8 and abs(oc['command_xyz'][0]-expected)<1e-10;assert np.array_equal(np.array(oc['command_xyz'])[1:],parent[1:]);assert abs(expected-prev[0])<=.002+1e-12 and abs(expected-reference[0])<=.03+1e-12
   recorded=f.get('rear_cop_centering',{})
   if recorded.get('override'):
    assert np.max(abs(xyz[t]+R[t]@cop-recorded['cop_world']))<1e-6
    needed=float(np.clip(0,*iv)) if iv is not None else None
    actual.append(dict(step=t,needed_world_x_displacement_m=needed,recorded_feedback_error_m=recorded['error_x_m'],recorded_command_delta_x_m=recorded['command_delta_x_m'],feedback_opposes_interior=bool(needed is not None and abs(needed)>.0001 and needed*recorded['error_x_m']<0),command_opposes_interior=bool(needed is not None and abs(needed)>.0001 and needed*recorded['command_delta_x_m']<0)))
   rows.append(dict(step=t,candidate=oc));previous=parent
  report=dict(run=run,episode=ep.name,default_exact_frames=parity,counterfactual_overrides=sum(x['candidate']['override'] for x in rows),empty_slice_fallbacks=sum(x['candidate']['reason']=='no_world_x_core_interior_slice' for x in rows),actual_recorded_overrides=len(actual),actual_outside_inset_with_x_solution=sum(x['needed_world_x_displacement_m'] is not None and abs(x['needed_world_x_displacement_m'])>.0001 for x in actual),actual_feedback_opposes_interior=sum(x['feedback_opposes_interior'] for x in actual),actual_command_opposes_interior=sum(x['command_opposes_interior'] for x in actual),actual_directions=actual,rows=rows,source_sha256={n:sha(ep/n) for n in ['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','solved_contact_forces.json']},collision_source_sha256=sha(cfg));reports.append(report);print({k:v for k,v in report.items() if k not in ['rows','actual_directions','source_sha256']},flush=True)
# Cases independent of historic layout yaw; exact 90deg can have no X-only recovery.
fixtures=0
for angle in [0,30,-45,90,135,180]:
 rot=Rotation.from_euler('z',angle,degrees=True).as_matrix()
 for cop in [np.array([-.059,0,.02]),np.array([0.,0.,.02]),np.array([.07,.06,.02])]:
  size=np.array([.12,.1,.04]);expected=independent_interval(cop,rot,size);got=new.world_x_core_interval(cop,rot,size);assert (expected is None)==(got is None)
  if got is not None:
   assert max(abs(np.array(got)-expected))<1e-8;dx=np.clip(0,*got);assert np.all(abs((cop+rot.T@np.array([dx,0.,0.]))[:2])<=size[:2]/2-.01+1e-10)
  fixtures+=1
for flag in [1,0,None,'yes']:
 try:new.RearCopCentering(core_slice_feedback=flag)
 except ValueError:pass
 else:raise AssertionError('Nonbool flag accepted')
out=dict(passed=True,episodes=reports,geometry_fixtures=fixtures,nonbool_negative_cases=4,total_default_exact_frames=sum(r['default_exact_frames'] for r in reports),total_counterfactual_overrides=sum(r['counterfactual_overrides'] for r in reports),candidate_sha256=sha(stage/'rear_cop_centering.py'),parent_sha256=sha(w/'staged_rear_cop_measured_bounds/rear_cop_centering.py'),checker_sha256=sha(Path(__file__)),collector_wired=False,physical_started=False,training_ready=False,scope='Independent prior raw-force weighted COP and archived collision scale; LP in world-X holding worldYZ fixed checks rotated core interval. Ten frozen streams, default exact against old helper, optional one-step counterfactual only. Feedforward unchanged, so no claim that full command is always inward, contact follows a geometric shift, or success improves.')
p=stage/'CHECK.json';assert not p.exists();p.write_text(json.dumps(out,indent=2));print('PASSED',out['total_default_exact_frames'],out['total_counterfactual_overrides'],flush=True)
