"""Full pressure stream on marked fixed-observation fork fixtures, not physics.
Loads come from an independently recomputed original24substep stream. Candidate
observations are not claimed: branches intentionally retain original q/contact.
"""
from pathlib import Path
import copy,datetime,hashlib,json,sys
W=Path(__file__).resolve().parent;D=W/'front_normal_pressure_fork_audit_r1';D.mkdir(exist_ok=False);sys.path.insert(0,str(W))
from audit_front_normal_pressure_stream_v1 import verify_stream
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
parent=W/'front_normal_pressure_parent_stream_r1';proof=read(parent/'RESULT.json');assert proof['passed']
for p,h in proof['source_sha256'].items():assert sha(p)==h,p
loadfile=parent/'layout_840020_push_box_to_bin_loads.json';all_loads={int(k):v for k,v in read(loadfile).items()}
rows=[];negative=[]
for t in [682,683]:
 path=W/f'front_normal_prefix_recovery_r4/PRESSURE_FORK_{t}.json';f=read(path);n=f['frames'];loads={k:v for k,v in all_loads.items() if k<n}
 def run(x,ld=loads):
  return verify_stream(x['pressure'],x['frontal'],ld,frames=n,wait=False,enabled=True,normal_records=x['normal_records'],current=x['current'],actions=x['actions'],side='right',final_guards=x['final_guards'])
 r=run(f);assert r['passed'] and len(r['final_recovery_transitions'])==1 and r['final_recovery_transitions'][0]['step']==t
 rows.append(dict(fork=t,frames=n,pressure_updates=r['pressure_updates'],control_frames=r['control_frames'],transition=r['final_recovery_transitions'][0]))
 for case in ['missing_record','duplicate_record','unsorted_record','missing_commit','orphan_final_transition','stale_final_phase','wrong_held_action','wrong_next_previous','next_still_push','next_count_not_incremented','next_filter_reset','modified_substep_peak','nan_final_filter','missing_final_guard','rejected_final_guard','enabled_record_false']:
  x=copy.deepcopy(f);ld=copy.deepcopy(loads)
  if case=='missing_record':x['normal_records'].pop(t)
  elif case=='duplicate_record':x['normal_records'].append(copy.deepcopy(x['normal_records'][t]))
  elif case=='unsorted_record':x['normal_records'][t],x['normal_records'][t-1]=x['normal_records'][t-1],x['normal_records'][t]
  elif case=='missing_commit':x['normal_records'][t]['recovery_committed']=False
  elif case=='orphan_final_transition':x['normal_records'][t]['requires_recovery']=False
  elif case=='stale_final_phase':x['pressure']['final_control_states'][t-1]['top_mode']='top_push'
  elif case=='wrong_held_action':x['actions'][t][0]+=.001
  elif case=='wrong_next_previous':x['final_guards'][t+1]['previous'][0]+=.001
  elif case=='next_still_push':x['pressure']['rows'][t]['phase_at_update']='top_push';x['pressure']['rows'][t]['active']=True
  elif case=='next_count_not_incremented':x['frontal']['rows'][t]['recontacts']-=1
  elif case=='next_filter_reset':x['pressure']['rows'][t]['before']['filtered_n']=0.
  elif case=='modified_substep_peak':ld[t-1][0]+=100.
  elif case=='nan_final_filter':x['pressure']['final_control_states'][t-1]['filtered_n']=float('nan')
  elif case=='missing_final_guard':x['final_guards'].pop(t)
  elif case=='rejected_final_guard':x['final_guards'][t]['accepted']=False
  else:x['normal_records'][t]['enabled']=False
  try:run(x,ld)
  except (AssertionError,KeyError,ValueError):negative.append(dict(fork=t,case=case,rejected=True))
  else:raise AssertionError(('bad full stream accepted',t,case))
 print(json.dumps(rows[-1]),flush=True)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,rows=rows,negative=negative,source_sha256={str(p):sha(p) for p in [Path(__file__),W/'audit_front_normal_pressure_stream_v1.py',W/'audit_front_normal_pressure_finalization_v1.py',parent/'RESULT.json',loadfile,*[W/f'front_normal_prefix_recovery_r4/PRESSURE_FORK_{t}.json' for t in [682,683]]]},physical_stream=False,training_ready=False)
(D/'RESULT.json').write_text(json.dumps(report,indent=2));print(json.dumps(dict(passed=True,forks=len(rows),negative=len(negative))),flush=True)
