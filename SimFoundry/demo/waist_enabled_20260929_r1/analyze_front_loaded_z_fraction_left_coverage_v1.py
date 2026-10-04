"""Describe quarter versus full nominal commands at the same archived left states.
Changes in acceptance frequency matter: smaller Z interpolation does NOT imply
less executed contact force or less downward correction at every observation.
No sum of these independent proposals is treated as a physical trajectory.
"""
from pathlib import Path
import sys,json,hashlib,datetime,collections
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path[:0]=[str(W),str(ROOT)]
from audit_unloaded_wrist_prior_live import HandModel
from front_loaded_z_priority_audit_geometry import point
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();D=W/'front_loaded_z_fraction_stream_check_r2';summary=read(D/'840023_nudge_mailer_to_bin_SUMMARY.json');assert summary['steps_checked']==1199
ep=W/'front_corridor_lateral_physical_r1/case_840023/layout_840023_nudge_mailer_to_bin';co={r['step']:r for r in read(ep/'coordination.json')};hand=HandModel(ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',ROOT/'assets/robots/g1_hand_support_vertices.json');sources={};counts=collections.Counter();rows=[]
for r in summary['rows']:
 t=r['step'];old=co[t]['front_loaded_z_priority'];counts[f"full_{old['applied']}_quarter_{r['quarter_applied']}"]+=1
 if not r['changed_from_full']:continue
 p=D/f'840023_nudge_mailer_to_bin_{t:04d}.json';m=read(p)['priority'];sources[str(p)]=sha(p);ctx=m['context'] if 'target_rotation' in m['context'] else old['context'];n=np.asarray(ctx['target_rotation'])[:,2];center=np.asarray(ctx['center_local']);q=np.asarray(ctx['current']);base=point(hand,q,'left',n,center)
 full=point(hand,np.asarray(old['output_command']),'left',n,center)-base;quarter=point(hand,np.asarray(m['output_command']),'left',n,center)-base
 rows.append(dict(step=t,full_applied=old['applied'],quarter_applied=m['applied'],full_nominal_dz_mm=float(full[2]*1000),quarter_nominal_dz_mm=float(quarter[2]*1000),quarter_minus_full_nominal_dz_mm=float((quarter[2]-full[2])*1000),quarter_moves_more_down=bool(quarter[2]<full[2]-1e-7)))
assert len(rows)==summary['changed'];assert sum(1 for r in summary['rows'] if r['quarter_applied'])==181
for p in [Path(__file__),D/'840023_nudge_mailer_to_bin_SUMMARY.json',ep/'coordination.json',W/'audit_unloaded_wrist_prior_live.py',W/'front_loaded_z_priority_audit_geometry.py',ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',ROOT/'assets/robots/g1_hand_support_vertices.json']:sources[str(p)]=sha(p)
result=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,observations=1199,acceptance_counts=dict(counts),changed_observations=len(rows),quarter_more_down_than_full=sum(r['quarter_moves_more_down'] for r in rows),rows=rows,source_sha256=sources,physics_started=False,training_ready=False,required_followup='Compare actual force bursts, loss of load, bag yaw and full paired task success in a new physical trial; fraction size alone cannot establish lower-force operation.')
with (W/'front_loaded_z_fraction_candidate_v1/LEFT_ACCEPTANCE_COVERAGE.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps({k:v for k,v in result.items() if k not in ['scope','rows','source_sha256','required_followup']}),flush=True)
