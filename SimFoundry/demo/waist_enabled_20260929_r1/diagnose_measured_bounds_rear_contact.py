"""Read-only complete rear episode comparison; no causal claim from repeat variance."""
from pathlib import Path
import json,sys,hashlib,collections
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path.insert(0,str(repo))
from simfoundry.data.top_contact_load_geometry import loaded_forward_margin
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();reports=[]
for run in ['region_causal_xy_groups_r2','region_measured_bounds_groups_r1']:
 for cid,task in [(840001,'push_box_to_bin'),(840004,'nudge_mailer_to_bin')]:
  ep=w/run/f'case_{cid}/layout_{cid}_{task}';fr=json.loads((ep/'frontal_bypass.json').read_text());rows=fr['rows'];key='box' if 'push_box' in task else 'mailer';actor='parcel_box' if key=='box' else 'mailer';side='right' if key=='box' else 'left';direction=-1 if side=='right' else 1
  size=np.array(fr['plan']['top_recontact']['contact_size_xyz']);core=np.array(fr['plan']['region_causal_response']['actual_core']['collision_core_size_xyz'])
  with np.load(ep/'trace.npz') as z:xyz=z[key].astype(float)
  with np.load(ep/'parcel_orientation.npz') as z:quat=z[key].astype(float)
  packets={r['after_action_step']:r for r in json.loads((ep/'solved_contact_forces.json').read_text())['rows']}
  bouts=[];active=[]
  for row in rows:
   if row['mode']=='top_push':active.append(row)
   elif active:
    last_loaded=None
    for x in active:
     t=x['step'];c=loaded_forward_margin(packets.get(t-1),side,actor,xyz[t],quat[t],size,direction)
     if c['valid'] and c['normal_load_n']>=.3:
      local=np.array(c['weighted_contact_local']);last_loaded=dict(step=t,normal_load_n=c['normal_load_n'],core_xy_margins_mm=((core[:2]/2-abs(local[:2]))*1000).tolist())
    bouts.append(dict(start=active[0]['step'],end=active[-1]['step'],steps=len(active),loaded_steps=sum(x['contact_load']['observed_vertical_load_n']>=.2 for x in active),exit_step=row['step'],exit_mode=row['mode'],reason=row.get('last_recontact_reason'),last_loaded_cop=last_loaded));active=[]
  if active:bouts.append(dict(start=active[0]['step'],end=active[-1]['step'],steps=len(active),loaded_steps=sum(x['contact_load']['observed_vertical_load_n']>=.2 for x in active),exit_mode='episode_ended',reason=None,last_loaded_cop=None))
  q=json.loads((ep/'quality.json').read_text());report=dict(run=run,episode=ep.name,quality_passed=q['passed'],progress_mm=q['metrics']['target_final_progress_m']*1000,min_final10_signed_y_mm=float(np.min(direction*xyz[-10:,1])*1000),non_target_max_xy_mm=q['metrics'][('mailer' if key=='box' else 'box')+'_max_xy_m']*1000,bouts=bouts,loaded_push_steps=sum(b['loaded_steps'] for b in bouts),exit_counts=dict(collections.Counter(b['reason'] for b in bouts)),source_sha256={n:sha(ep/n) for n in ['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','solved_contact_forces.json','quality.json']})
  if (ep/'MEASURED_BOUNDS_LIVE_AUDIT.json').exists():
   a=json.loads((ep/'MEASURED_BOUNDS_LIVE_AUDIT.json').read_text());assert a['passed'];report['domain_audit']=dict(solver_records_checked=a['solver_records_checked'],outside_command_domain=sum(c['outside_command_domain'] for c in a['checks']),inward_recovery_commands=a['inward_recovery_commands'],sha256=sha(ep/'MEASURED_BOUNDS_LIVE_AUDIT.json'))
  reports.append(report)
out=dict(rows=reports,training_ready=False,scope='Complete rear raw histories; prior last-solved-substep vertical load>=.2N counts versus prior normalCOP>=.3N last contact are distinct measures, not impulses. Core margins use actual collision size without inset. Same-seed repeats vary; unchanged-domain trials cannot establish causal gains from unused recovery branch.',checker_sha256=sha(Path(__file__)))
p=w/'region_measured_bounds_groups_r1/REAR_CONTACT_COMPARISON.json';p.write_text(json.dumps(out,indent=2))
for r in reports:print({k:v for k,v in r.items() if k not in ['source_sha256','bouts']})
