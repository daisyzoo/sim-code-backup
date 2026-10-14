"""Default-off real-history identity, original contact-entry proposals, and
synthetic finite-state admission checks. No changed joint solve or new physics.
"""
from pathlib import Path
from copy import deepcopy
from types import SimpleNamespace
import datetime,hashlib,json,sys
import numpy as np
W=Path(__file__).resolve().parent;sys.path.insert(0,str(W));from front_bag_preload_waypoint_candidate_v1 import FrontBagPreload
R=W/'front_effective_height_physical_r1';D=W/'front_bag_preload_waypoint_r1';D.mkdir(exist_ok=False);read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={str(Path(__file__)):sha(__file__),str(W/'front_bag_preload_waypoint_candidate_v1.py'):sha(W/'front_bag_preload_waypoint_candidate_v1.py')}
identities=[];entries=[];selected_ep=None
for case in read(R/'PROTOCOL.json')['plan']['commands']:
 if case['wait']:continue
 for task in case['tasks']:
  ep=R/f"case_{case['layout_id']}"/f"layout_{case['layout_id']}_{task}";fr=read(ep/'frontal_bypass.json');rows=fr['rows'];side='left' if 'nudge_mailer' in task else 'right';selected=bool(fr['plan'].get('front_route_selected'));core=fr['plan'].get('front_cop_slip_following',{}).get('edge_speed',{}).get('actual_core_size_xyz')
  with np.load(ep/'raw.npz',allow_pickle=False) as z:actions=z['action'][:,12:23].copy()
  guards={x['step']:x for x in read(ep/'self_clearance.json')['rows'] if x['phase']=='final_command'}
  off=FrontBagPreload();count=0;on=FrontBagPreload(enabled=True);unchanged=0
  for row in rows:
   t=row['step'];inp=dict(step=t,selected=selected,side=side,row=row,previous_waypoint_xy=row.get('cop_slip_following',{}).get('previous_command_xy'),core_size=core,desired_n=5.,min_bias_m=-.006)
   p=off.propose(**inp);assert p['record']['kind']=='pass' and p['record']['output_target_xyz']==row['target_xyz'];off.commit_after_final_guard(p,final_guard=guards[t],actual_command=actions[t],expert_state=None);count+=1
   if not (selected and side=='left'):
    p=on.propose(**inp);assert p['record']['kind']=='pass' and p['record']['output_target_xyz']==row['target_xyz'];on.commit_after_final_guard(p,final_guard=guards[t],actual_command=actions[t],expert_state=None);unchanged+=1
  identities.append(dict(episode=ep.name,disabled_frames=count,enabled_outside_front_bag_frames=unchanged))
  if selected and side=='left':
   selected_ep=ep;previous_mode=None
   for row in rows:
    if row['mode']=='top_push' and previous_mode!='top_push':
     p=FrontBagPreload(enabled=True).propose(step=row['step'],selected=True,side='left',row=row,previous_waypoint_xy=row['cop_slip_following']['previous_command_xy'],core_size=core,desired_n=5.,min_bias_m=-.006)
     assert p['record']['kind']=='hold' and p['record']['output_target_xyz'][2]==row['target_xyz'][2]
     assert np.max(abs(np.asarray(p['record']['output_target_xyz'][:2])-row['cop_slip_following']['previous_command_xy']))<=.003000000001
     entries.append(p['record'])
    previous_mode=row['mode']
  for n in ['frontal_bypass.json','raw.npz','self_clearance.json']:sources[str(ep/n)]=sha(ep/n)
assert len(identities)==8 and sum(r['disabled_frames'] for r in identities)==9592 and len(entries)==7
# Deliberately synthetic repeated observation/guard fixtures: bookkeeping only.
fr=read(selected_ep/'frontal_bypass.json');original=next(r for r in fr['rows'] if r['mode']=='top_push');core=fr['plan']['front_cop_slip_following']['edge_speed']['actual_core_size_xyz'];u=np.zeros(11,np.float32);guard=dict(accepted=True,command=u.tolist());negative=[]
class Cop:
 def __init__(self):self.resets=0
 def reset(self):self.resets+=1

def expert(row):return SimpleNamespace(side='left',top_mode='top_push',recontacts=row['recontacts'],command=tuple(row['target_xyz']),last_emitted_xy=tuple(row['target_xyz'][:2]),load=SimpleNamespace(desired_n=5.,min_bias_m=-.006,filtered_n=row['contact_load']['filtered_vertical_load_n'],bias_m=row['contact_load']['stored_z_bias_m']),cop_slip=Cop())
def proposal(ctrl,row):return ctrl.propose(step=row['step'],selected=True,side='left',row=row,previous_waypoint_xy=row['cop_slip_following']['previous_command_xy'],core_size=core,desired_n=5.,min_bias_m=-.006)
for kind in ['final_guard_reject','wrong_command','tampered_proposal','stale_phase','stale_pressure','competing_waypoint']:
 ctrl=FrontBagPreload(enabled=True);row=deepcopy(original);p=proposal(ctrl,row);obj=expert(row);g=deepcopy(guard)
 if kind=='final_guard_reject':g['accepted']=False
 if kind=='wrong_command':g['command'][0]=.1
 if kind=='tampered_proposal':p['next_state']['held_frames']=99
 if kind=='stale_phase':obj.top_mode='top_lift'
 if kind=='stale_pressure':obj.load.filtered_n+=.1
 if kind=='competing_waypoint':obj.command=(99.,99.,99.)
 before=(deepcopy(ctrl.state),deepcopy(obj.__dict__),obj.cop_slip.resets)
 try:ctrl.commit_after_final_guard(p,final_guard=g,actual_command=u,expert_state=obj)
 except ValueError:pass
 else:raise AssertionError(kind+' accepted')
 assert ctrl.state==before[0] and obj.cop_slip.resets==before[2] and obj.command==before[1]['command'] and obj.load.__dict__==before[1]['load'].__dict__;negative.append(kind)
synthetic=[]
for load,expected_holds in [(4.5,3),(1.,24)]:
 ctrl=FrontBagPreload(enabled=True);prev=np.asarray(original['cop_slip_following']['previous_command_xy']);holds=0;resets=0;terminal=None
 for k in range(25):
  row=deepcopy(original);row['step']=original['step']+k;row['contact_load'].update(observed_vertical_load_n=load,filtered_vertical_load_n=load);row['cop_slip_following']['previous_command_xy']=prev.tolist();row['target_xyz'][:2]=(prev+np.array([-.001,.001])).tolist();p=proposal(ctrl,row)
  if p['record']['requires_stop']:
   assert k==24 and load==1.;terminal=p['record']['reason'];break
  obj=expert(row);pressure=deepcopy(obj.load.__dict__);ctrl.commit_after_final_guard(p,final_guard=guard,actual_command=u,expert_state=obj);assert obj.load.__dict__==pressure
  resets+=obj.cop_slip.resets;prev=np.asarray(p['record']['output_target_xyz'][:2]);holds+=p['record']['kind']=='hold'
  try:ctrl.commit_after_final_guard(p,final_guard=guard,actual_command=u,expert_state=obj)
  except ValueError:pass
  else:raise AssertionError('duplicate commit accepted')
  if p['record']['kind']=='pass':terminal=p['record']['reason'];break
 assert holds==expected_holds and resets==(1 if load==4.5 else 0);synthetic.append(dict(load_fixture_n=load,holds=holds,cop_resets=resets,terminal=terminal))
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,identity=identities,isolated_original_entry_proposals=entries,negative_rejected=negative,duplicate_commit_rejected=True,synthetic_state_fixtures=synthetic,changed_joint_solve_verified=False,consecutive_real_changed_history_verified=False,new_physics=False,installed=False,training_ready=False,source_sha256=sources)
(D/'RESULT.json').write_text(json.dumps(out,indent=2));print(dict(passed=True,defaultoff_frames=9592,enabled_unchanged_nonselected_frames=sum(r['enabled_outside_front_bag_frames'] for r in identities),original_contact_proposals=len(entries),negative=len(negative),synthetic=synthetic,new_physics=False))
