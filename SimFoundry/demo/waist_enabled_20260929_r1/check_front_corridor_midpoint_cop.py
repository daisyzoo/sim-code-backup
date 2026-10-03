"""Full real front streams and explicitly unissued first-changed-row prefix.
The prefix contains no hypothesized future physical observations.
"""
from pathlib import Path
import ast,copy,datetime,hashlib,json,sys
import numpy as np
W=Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W.parents[1])]
from audit_front_corridor_midpoint_cop import reconstruct
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={};actual=[]
for run in ['front_initial_physical_r1','front_z_priority_physical_r1']:
 for case,key,task in [(840020,'box','push_box_to_bin'),(840023,'mailer','nudge_mailer_to_bin')]:
  ep=W/run/f'case_{case}/layout_{case}_{task}';log=json.loads((ep/'frontal_bypass.json').read_text());tr=dict(np.load(ep/'trace.npz'));ori=dict(np.load(ep/'parcel_orientation.npz'));packets={r['after_action_step']:r for r in json.loads((ep/'solved_contact_forces.json').read_text())['rows']};r=reconstruct(log['rows'],log['plan'],tr,ori,packets,key,midpoint_enabled=False,expected_steps=range(1,len(tr[key])));assert r['passed'],r['errors'];actual.append(dict(run=run,episode=ep.name,observed_rows=len(log['rows']),loaded_cop_rows=len(r['records']),guard_rows=r['observation_binding']['guard_rows']))
  for name in ['frontal_bypass.json','trace.npz','parcel_orientation.npz','solved_contact_forces.json']:sources[str(ep/name)]=sha(ep/name)
# Reuse the explicitly-labelled observation fixture setup only, no report write.
p=W/'check_front_corridor_midpoint_observations.py';bound=json.loads((W/'staged_front_corridor_midpoint_integrated/CONTINUOUS_OBSERVATION_CHECK.json').read_text())
for name,h in bound['source_sha256'].items():assert sha(name)==h,name
s=ast.parse(p.read_text());cut=next(i for i,n in enumerate(s.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='result' for t in n.targets));ns={'__file__':str(p),'__name__':'midpoint_cop_prefix_fixture'};exec(compile(ast.Module(body=s.body[:cut],type_ignores=[]),str(p),'exec'),ns)
rows,plan,tr,ori,ep=[ns[k] for k in ['rows','plan','tr','ori','ep']];packets={r['after_action_step']:r for r in json.loads((ep/'solved_contact_forces.json').read_text())['rows']}
result=reconstruct(rows,plan,tr,ori,packets,'mailer',midpoint_enabled=True,expected_steps=range(1,174));assert result['passed'],result['errors'];assert result['observation_binding']['changed_steps']==[173]
negative=[]
for label,edit in [('waypoint',lambda rr:rr[-1]['target_xyz'].__setitem__(0,rr[-1]['target_xyz'][0]+.001)),('feedback_command',lambda rr:rr[-1]['cop_slip_following']['command_xy'].__setitem__(0,rr[-1]['cop_slip_following']['command_xy'][0]+.001)),('packet_force',None),('phase_reset',lambda rr:rr[-1]['cop_slip_following'].__setitem__('route_anchor_reset',True))]:
 bad=copy.deepcopy(rows);bad[-1]['target_xyz']=list(bad[-1]['target_xyz']);pk=packets
 if edit:edit(bad)
 else:
  pk=copy.deepcopy(packets)
  for c in pk[172]['parcel_contacts']:
   if any('left_wrist' in name for name in c['shapes']):c['force_world_N']=[0.,0.,0.]
 try:r=reconstruct(bad,plan,tr,ori,pk,'mailer',midpoint_enabled=True,expected_steps=range(1,174));failed=not r['passed']
 except (AssertionError,ValueError,KeyError):failed=True
 assert failed,'accepted corrupted '+label;negative.append(label)
sources.update(bound['source_sha256'])
for p in [Path(__file__),W/'audit_front_corridor_midpoint_cop.py',W/'FRONT_CORRIDOR_MIDPOINT_COP_AUDIT_PATCH.json',W/'staged_front_corridor_midpoint_integrated/CONTINUOUS_OBSERVATION_CHECK.json']:sources[str(p)]=sha(p)
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,actual_trajectory_checks=actual,total_real_front_observations=sum(r['observed_rows'] for r in actual),total_real_loaded_cop_rows=sum(r['loaded_cop_rows'] for r in actual),unissued_prefix_fixture=dict(rows=173,changed_steps=[173],loaded_cop_rows=len(result['records']),last_waypoint_error_m=result['records'][-1]['waypoint_error_m'],future_observations_after_change_used=False),negative_cases_rejected=negative,source_sha256=sources,source_contract_complete=False,joint_execution_binding_complete=False,training_ready=False)
with (W/'staged_front_corridor_midpoint_integrated/CONTINUOUS_COP_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps({k:v for k,v in out.items() if k not in ['source_sha256','actual_trajectory_checks','scope']},indent=2))
