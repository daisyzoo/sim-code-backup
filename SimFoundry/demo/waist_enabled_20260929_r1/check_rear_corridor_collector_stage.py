"""Real parser and command boundary checks for isolated rear recovery stage.
Historical measured streams are fixed input fixtures, not counterfactual physics.
"""
from pathlib import Path
from types import SimpleNamespace
import sys,json,hashlib,datetime,copy,pickle,contextlib,io,os
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_rear_corridor_recovery';sys.path[:0]=[str(S),str(W),str(ROOT)]
from rear_corridor_collector_adapter import propose,commit,complete_handover
from rear_cop_route import RearCopRouteState
from clearance_runtime import ClearanceGuard
from prepare_closed_peak_trial import parser_namespace
from audit_self_clearance_task_optimality import IndependentElbows
from audit_unloaded_wrist_prior_live import HandModel
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
prep=json.loads((S/'PREPARATION.json').read_text());assert all(sha(S/n)==h for n,h in prep['stage_sha256'].items())
DEST=S/'CHECK.json';assert not DEST.exists();guard=ClearanceGuard(ROOT,S)
urdf=ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf';verts=ROOT/'assets/robots/g1_hand_support_vertices.json';ind=IndependentElbows(S/'elbow_torso_hulls.json',urdf);hand=HandModel(urdf,verts);vertices=json.loads(verts.read_text())['vertices']
base=list(json.loads((W/'peak_guard_groups_r1/PROTOCOL.json').read_text())['commands'][0]['args'])+['--out-dir','/tmp/rear_corridor_CLI_NO_SIMULATION'];cli_tests=[];negative=[];episodes=[];sources={};counts=dict(loaded_recovery=0,unload=0,stop=0,unchanged=0,default_off_rows=0);handover_count=0
frozen={str(p):sha(p) for p in [Path(__file__),S/'PREPARATION.json',*[S/n for n in prep['stage_sha256']],urdf,verts,W/'audit_self_clearance_task_optimality.py',W/'audit_unloaded_wrist_prior_live.py',W/'REAR_CORRIDOR_RECOVERY_DIRECTION_SCREEN.json',W/'REAR_TRANSPORT_LIFECYCLE_CHECK.json']}
def save(status,**extra):
 d=dict(status=status,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,cli_tests=cli_tests,counts=counts,episodes=episodes,negative_checks=negative,measured_handover_checks=handover_count,source_sha256=sources,frozen_sha256=frozen,simulation_started=False,training_ready=False,**extra)
 temp=DEST.with_suffix('.tmp');temp.write_text(json.dumps(d,indent=2));temp.replace(DEST)
def cli(name,args,expect):
 settings=None
 try:
  with contextlib.redirect_stderr(io.StringIO()):settings,_=parser_namespace(S/'collect_paired_sorting.py',args,full=True)
  passed=True
 except SystemExit as e:passed=e.code==0
 assert passed==expect,(name,passed);cli_tests.append(dict(name=name,accepted=passed));return settings

def state_for(row,coord,plan):
 st=RearCopRouteState(rear=SimpleNamespace(plan=plan),side=coord['active_side'],size=tuple([.14,.09,.045] if coord['active_side']=='right' else [.15,.145,.04]),hold_established_x=True)
 st.top_mode=st.mode=row['mode'];st.command=tuple(row['target_xyz']);st.last_waypoint_xy=tuple(row['target_xyz'][:2]);st.push_x_anchor=row.get('push_x_anchor_m');st.recontacts=row['recontacts'];st.load.bias_m=row['contact_load']['stored_z_bias_m'];st.load.filtered_n=row['contact_load']['filtered_vertical_load_n'];return st
try:
 save('running')
 off=cli('default_off',base,True);on=cli('enabled_original_diagnostic',base+['--rear-corridor-recovery'],True)
 assert off['rear_corridor_recovery'] is False and on['rear_corridor_recovery'] is True and {k:v for k,v in off.items() if k!='rear_corridor_recovery'}=={k:v for k,v in on.items() if k!='rear_corridor_recovery'}
 for flag in ['--peak-load-bias-guard','--rear-joint-xy-progress','--rear-cop-centering','--rear-joint-edge-command','--rear-box-inward-correction','--self-clearance-task-ik','--minimum-motion-recontact','--unloaded-recontact-pose','--trace-substep-contacts']:
  a=base.copy();a.remove(flag);cli('reject_missing_'+flag,a+['--rear-corridor-recovery'],False)
 for flag in ['--idle','--waist-probe']:cli('reject_'+flag,base+['--rear-corridor-recovery',flag],False)
 a=base.copy();a[a.index('--role')+1]='pilot';cli('reject_pilot',a+['--rear-corridor-recovery'],False)
 a=base.copy();a[a.index('--waist-limit-rad')+1]='.9';cli('reject_changed_waist_bound',a+['--rear-corridor-recovery'],False)
 # parser_namespace prepends paths; explicitly restore candidate modules for the runtime checks.
 sys.path[:0]=[str(S),str(W),str(ROOT)]
 screen=json.loads((W/'REAR_CORRIDOR_RECOVERY_DIRECTION_SCREEN.json').read_text());sizes={'box':[.14,.09,.045],'mailer':[.15,.145,.04]}
 for item in screen['episodes']:
  ep=W/item['episode'];f=json.loads((ep/'frontal_bypass.json').read_text());fs={x['step']:x for x in f['rows']};cs={x['step']:x for x in json.loads((ep/'coordination.json').read_text())};side='right' if 'push_box' in ep.name else 'left';key='box' if side=='right' else 'mailer';other='mailer' if key=='box' else 'box'
  with np.load(ep/'trace.npz') as z:pos={k:z[k].copy() for k in sizes}
  with np.load(ep/'parcel_orientation.npz') as z:rot={k:Rotation.from_quat(z[k]).as_matrix() for k in sizes}
  with np.load(ep/'raw.npz') as z:actions=z['action'].copy()
  for n in ['trace.npz','parcel_orientation.npz','raw.npz','frontal_bypass.json','coordination.json']:sources[str(ep/n)]=sha(ep/n)
  er=dict(episode=item['episode'],requests=len(item['rows']),rows=[]);episodes.append(er)
  # Disabled truly bypasses every action, including initial, approach and terminal rows.
  for t,act in enumerate(actions):
   parent=act[12:23];x,tr=propose(enabled=False,step=t,selected=True,parent_command=parent)
   assert x is parent and np.array_equal(x,parent) and tr['kind']=='unchanged';counts['default_off_rows']+=1
  for selected in item['rows']:
   t=selected['step'];row=fs[t];coord=cs[t];q=np.array(coord['upper_q']);prev=actions[t-1,12:23];parent=actions[t,12:23]
   args=dict(enabled=True,step=t,selected=True,parent_command=parent,guard=guard,row=row,coordinate=coord,current=q,previous=prev,target_xyz=pos[key][t],obstacle_xyz=pos[other][t],target_rotation=rot[key][t],obstacle_rotation=rot[other][t],target_size=sizes[key],obstacle_size=sizes[other],core_size=f['plan']['rear_cop_centering']['actual_core_size_xyz'])
   before=pickle.dumps((row,coord));x,tr=propose(**args);assert pickle.dumps((row,coord))==before;counts[tr['kind']]+=1
   check=None
   if tr['kind'] in ('loaded_recovery','unload'):
    assert x is not None;T=hand.fk(x,side);T0=hand.fk(q,side);offp=np.array(row['control_offset_local']);delta=T[:3,3]+T[:3,:3]@offp-T0[:3,3]-T0[:3,:3]@offp;gap=ind.gap(x)
    assert min(gap)>=.005-2e-7 and np.all(x>=guard.lower-2e-7) and np.all(x<=guard.upper+2e-7) and np.all(abs(x-q)<=guard.limits+2e-7) and max(abs(x-prev))<=.0550002
    if tr['kind']=='loaded_recovery':
     rr=tr['recovery'];assert abs(delta[1])<=1e-7 and rr['minimum_x_m']-1e-7<=delta[0]<=rr['requested_x_m']+1e-7
     cop=rot[key][t].T@(np.array(row['rear_cop_centering']['cop_world'])-pos[key][t]);core=np.array(args['core_size']);axes=[k for k in [0,1] if core[k]/2-abs(cop[k])<=.01]
     assert axes==rr['near_core_axes'];edge=[float(-np.sign(cop[k])*rot[key][t][:,k]@delta-rr['inward_requirement_m']) for k in axes];assert not edge or min(edge)>=-1e-7
    else:
     v=np.array(vertices[side]);low=float(np.min((v@T[:3,:3].T+T[:3,3])[:,2])-np.min((v@T0[:3,:3].T+T0[:3,3])[:,2]));assert max(abs(delta[:2]))<=1e-7 and .0005-1e-7<=delta[2]<=.003+1e-7 and low>=.0005-1e-7
    st=state_for(row,coord,f['plan']);st_before=copy.deepcopy(st)
    kw=dict(state=st,guard=guard,row=row,coordinate=coord,current=q,previous=prev,command=x,record=tr)
    updated=commit(**kw);assert np.allclose(updated['target_xyz'],T[:3,3]+T[:3,:3]@offp,atol=1e-12,rtol=0)
    assert pickle.dumps((row,coord))==before and st.load.filtered_n==st_before.load.filtered_n
    if tr['kind']=='unload':
     assert updated['mode']=='top_lift' and st.top_mode=='top_lift' and st.load.bias_m==0. and updated['contact_load']['applied_z_bias_m']==0. and st.recontacts==st_before.recontacts+1 and st.rear_corridor_recontact_pending
    else:assert st.command==tuple(updated['target_xyz']) and st.last_waypoint_xy==st.command[:2] and st.load.bias_m==st_before.load.bias_m and st.recontacts==st_before.recontacts
    label='reject_duplicate_'+tr['kind']
    if label not in negative:
     state_bytes=pickle.dumps(st)
     try:commit(**kw)
     except ValueError:assert pickle.dumps(st)==state_bytes;negative.append(label)
     else:raise AssertionError('Duplicate commit accepted')
     for mutation in ['command','row']:
      nt=copy.deepcopy(tr);nt.pop('commit');nt.pop('emitted_command');fresh=copy.deepcopy(st_before);bad=dict(kw,state=fresh,record=nt)
      if mutation=='command':bad['command']=x+.001
      else:bad['row']=dict(row,step=t+1)
      state_bytes=pickle.dumps(fresh)
      try:commit(**bad)
      except ValueError:assert pickle.dumps(fresh)==state_bytes;negative.append('reject_changed_'+mutation+'_'+tr['kind'])
      else:raise AssertionError('Changed emission evidence accepted')
    check=dict(delta_xyz_m=delta.tolist(),independent_gaps_m=gap.tolist(),state_mode=st.mode,recontacts=st.recontacts,reference_state_synced=True)
   elif x is None:assert tr['kind']=='stop'
   else:assert np.array_equal(x,parent)
   er['rows'].append(dict(step=t,kind=tr['kind'],result=tr.get('unload',tr['recovery']),independent=check))
   if 'original_guards_preserved' not in negative:
    for label,mutate in [('non_push',lambda a:a['row'].update(mode='top_release')),('route_stop',lambda a:a['row'].update(route_stop_reason='guard')),('terminal',lambda a:a['coordinate'].update(terminal_joint_hold=True)),('region',lambda a:a['coordinate'].update(region_joint_override=True)),('first_loaded',lambda a:a['row'].update(rear_cop_centering={'override':False}))]:
     bad=dict(args,row=copy.deepcopy(row),coordinate=copy.deepcopy(coord));mutate(bad);xx,tt=propose(**bad);assert np.array_equal(xx,parent) and tt['kind']=='unchanged';negative.append('preserve_'+label)
    for change in [dict(enabled=1),dict(step=t+1),dict(current=q+.001),dict(target_rotation=np.zeros((3,3)))]:
     try:propose(**dict(args,**change))
     except ValueError:pass
     else:raise AssertionError('Invalid enabled context accepted')
    xx,tt=propose(**dict(args,step=0));assert xx is parent and tt['kind']=='unchanged'
    negative.append('original_guards_preserved')
   if len(er['rows'])%50==0:save('running');print(json.dumps(dict(episode=ep.name,completed=len(er['rows']),expected=er['requests'])),flush=True)
  save('running')
 # Use actual measured historical handovers with their freshly checked witness.
 history=json.loads((W/'REAR_TRANSPORT_LIFECYCLE_CHECK.json').read_text());cache={}
 for entry in history['rows']:
  if entry['case']!='actual_measured_handover':continue
  ep=W/entry['episode'];path=ep/'recontact_pose.json';sources[str(path)]=sha(path)
  if str(path) not in cache:cache[str(path)]=json.loads(path.read_text())['rows']
  event=copy.deepcopy(next(x for x in cache[str(path)] if x['step']==entry['step']));assert event['kind']=='handover'
  event['rear_transport_handover_witness']=entry['measured_witness'];st=SimpleNamespace(rear_corridor_recontact_pending=True,recontacts=event['context']['recontacts'])
  complete_handover(st,event);assert not st.rear_corridor_recontact_pending;handover_count+=1
  if 'handover_rejects_incomplete_measurement' not in negative:
   for change in [dict(kind='command'),dict(measured_ready_count=2),dict(rear_transport_handover_witness={'accepted':False}),dict(context=dict(event['context'],observed_load_n=1.))]:
    fresh=SimpleNamespace(rear_corridor_recontact_pending=True,recontacts=st.recontacts)
    try:complete_handover(fresh,dict(event,**change))
    except ValueError:assert fresh.rear_corridor_recontact_pending
    else:raise AssertionError('Incomplete handover accepted')
   negative.append('handover_rejects_incomplete_measurement')
 assert counts['loaded_recovery']==1693 and counts['unload']==250 and counts['stop']==0 and handover_count==45,(counts,handover_count)
 for p,h in {**sources,**frozen}.items():assert sha(p)==h,p
 save('complete',passed=True)
except BaseException as e:save('check_failed',error=repr(e));raise
