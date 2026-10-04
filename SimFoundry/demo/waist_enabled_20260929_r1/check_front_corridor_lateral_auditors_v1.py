"""Independent audits of recorded old stream and one unissued594 boundary.
No physical response after new command is supplied or certified.
"""
from pathlib import Path
import sys,json,hashlib,datetime,copy
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];D=W/'front_corridor_lateral_preparation_r1';sys.path[:0]=[str(W),str(ROOT)]
from audit_front_corridor_midpoint_cop import reconstruct as original
from audit_front_corridor_lateral_cop_v1 import reconstruct
from audit_front_corridor_lateral_record_v1 import verify
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={}
def read(p):sources[str(p)]=sha(p);return json.loads(p.read_text())
prep=read(D/'AUDITOR_PREPARATION.json')
for x in prep['adapters']:
 assert sha(x['parent'])==x['parent_sha256'] and sha(x['path'])==x['sha256'];s=Path(x['path']).read_text()
 for e in reversed(x['edits']):assert s.count(e['new'])==1;s=s.replace(e['new'],e['old'])
 assert s==Path(x['parent']).read_text();sources[x['path']]=x['sha256'];sources[x['parent']]=x['parent_sha256']
ep=W/'joint_transport_reserve_physical_r1/case_840023/layout_840023_nudge_mailer_to_bin';fr=read(ep/'frontal_bypass.json');n=read(D/'INTEGRATED_NATIVE_BOUNDARY_CHECK.json')
for p,h in n['source_sha256'].items():assert sha(p)==h,p
with np.load(ep/'trace.npz') as z:tr={k:z[k].copy() for k in z.files}
with np.load(ep/'parcel_orientation.npz') as z:ori={k:z[k].copy() for k in z.files}
packets={x['after_action_step']:x for x in read(ep/'solved_contact_forces.json')['rows']}
old=original(fr['rows'],fr['plan'],tr,ori,packets,'mailer',midpoint_enabled=True,expected_steps=range(1,1200));off=reconstruct(fr['rows'],fr['plan'],tr,ori,packets,'mailer',midpoint_enabled=True,expected_steps=range(1,1200));assert old==off and off['passed'],off['errors']
# Prefix1..593 was executed;594 is explicitly an unissued Cartesian proposal.
rows=copy.deepcopy(fr['rows'][:593])+[dict(n['candidate_row'],step=594)];plan=copy.deepcopy(fr['plan']);plan['front_corridor_midpoint']['phase']='front_x_and_lateral_y'
tr={k:v[:595] for k,v in tr.items()};ori={k:v[:595] for k,v in ori.items()};packets={k:v for k,v in packets.items() if k<=593}
on=reconstruct(rows,plan,tr,ori,packets,'mailer',midpoint_enabled=True,expected_steps=range(1,595),lateral_y_enabled=True);assert on['passed'],on['errors'];assert 594 in on['observation_binding']['changed_steps']
negative=[]
for name in ['undeclared_phase','wrong_goal','wrong_stage','missed_replacement','weakened_table_margin','invented_stop_clearance','wrong_cop_previous','wrong_594_waypoint']:
 rr=copy.deepcopy(rows);pp=copy.deepcopy(plan)
 if name=='undeclared_phase':pp['front_corridor_midpoint']['phase']='front_x_only'
 elif name=='wrong_goal':rr[-1]['front_corridor_midpoint']['goal_x']+=.001
 elif name=='wrong_stage':rr[-1]['front_corridor_midpoint']['route_stage']='front_x'
 elif name=='missed_replacement':rr[-1]['front_corridor_midpoint']['changed']=False
 elif name=='weakened_table_margin':rr[-1]['front_corridor_midpoint']['original_table_margin_m']=.004
 elif name=='invented_stop_clearance':rr[-1]['front_corridor_midpoint']['prior_stop_reason']='front_corridor_no_table_margin'
 elif name=='wrong_cop_previous':next(x for x in rr if x.get('cop_slip_following',{}).get('override'))['cop_slip_following']['previous_command_xy'][0]+=.001
 else:rr[-1]['target_xyz'][0]+=.001
 # The geometry/COP checker intentionally does not verify non-push lift output.
 # Its boundary must be explicit rather than falsely claim coverage.
 if name=='wrong_594_waypoint':
  unchecked=reconstruct(rr,pp,tr,ori,packets,'mailer',midpoint_enabled=True,expected_steps=range(1,595),lateral_y_enabled=True)
  assert unchecked['passed'];negative.append(dict(case=name,covered=False,required_audit='Original native lift/height/reference command audits in full versioned family'));continue
 try:
  result=reconstruct(rr,pp,tr,ori,packets,'mailer',midpoint_enabled=True,expected_steps=range(1,595),lateral_y_enabled=True);rejected=not result['passed']
 except (AssertionError,KeyError,ValueError):rejected=True
 assert rejected,name;negative.append(dict(case=name,rejected=True))
for p in [Path(__file__),ep/'trace.npz',ep/'parcel_orientation.npz']:sources[str(p)]=sha(p)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,original_full_stream_rows=1199,default_off_exact_old_auditor=True,actual_prefix_rows=593,unissued_proposal_rows=1,enabled_observation_rows=on['observation_binding']['rows'],cop_loaded_rows=len(on['records']),negative=negative,source_sha256=sources,full_native_audit_family_integrated=False,non_push_waypoint_check_not_in_this_layer=True,physics_started=False,training_ready=False)
with (D/'INDEPENDENT_AUDITOR_CHECK.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps({k:v for k,v in report.items() if k not in ['source_sha256','scope']},indent=2))
