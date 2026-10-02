"""Compare real fresh bag loss events and loaded tracking, no controller change.
Absolute vertical contact magnitudes are not signed net forces. Command/support
Z is a virtual control-reference error, not contact penetration or force causality.
"""
from pathlib import Path
import sys,json,hashlib,datetime
import numpy as np
W=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def describe(ep):
 ep=Path(ep);hp=ep/'CLOSED_PEAK_TRIAL_LOAD_HISTORY.json';h=json.loads(hp.read_text());assert h['independent_audit']['passed']
 for name,digest in h['source_sha256'].items():assert sha(ep/name)==digest
 fr=json.loads((ep/'frontal_bypass.json').read_text());rows={x['step']:x for x in fr['rows']};loads=np.asarray([x['vertical_load_n'] for x in h['rows']]);assert loads.shape==(1200,24)
 loaded=[t for t,row in rows.items() if row['mode']=='top_push' and loads[t].mean()>=.3]
 def stats(values):
  a=np.asarray(values);return dict(min=float(a.min()),median=float(np.median(a)),mean=float(a.mean()),max=float(a.max()))
 result=dict(episode=ep.name,loaded_top_push_actions=len(loaded),mean_substep_abs_vertical_n=stats(loads[loaded].mean(axis=1)),final_substep_abs_vertical_n=stats(loads[loaded,-1]),applied_z_bias_mm=stats([rows[t]['contact_load']['applied_z_bias_m']*1000 for t in loaded]),observed_support_above_command_mm=stats([(rows[t]['observed_support_xyz'][2]-rows[t]['target_xyz'][2])*1000 for t in loaded]),lost_contact_events=[])
 for ev in h['exit_events']:
  if ev['reason']!='lost_contact':continue
  t=ev['controller_step'];start=next(b['start'] for b in json.loads((ep/'CONTACT_MIGRATION.json').read_text())['bouts'] if b['end']==t-1)
  # Last loaded action and whether its final boundary already lost normal load.
  loaded_before=[j for j in range(start,t) if loads[j].mean()>=.3];last=loaded_before[-1] if loaded_before else None
  events=[]
  for j in range(max(start,t-6),t):
   row=rows[j];events.append(dict(step=j,mode=row['mode'],peak_vertical_n=float(loads[j].max()),final_vertical_n=float(loads[j,-1]),mean_vertical_n=float(loads[j].mean()),command_xyz=row['target_xyz'],observed_support_xyz=row['observed_support_xyz'],controller_observed_vertical_n=row['contact_load']['observed_vertical_load_n'],controller_filtered_vertical_n=row['contact_load']['filtered_vertical_load_n'],applied_z_bias_m=row['contact_load']['applied_z_bias_m']))
  result['lost_contact_events'].append(dict(controller_exit_step=t,push_start=start,last_action_mean_above_point3=last,preceding_zero_load_actions=int(sum(loads[j].max()==0 for j in range(max(start,t-6),t))),last6_actions=events))
 migration=json.loads((ep/'CONTACT_MIGRATION.json').read_text());result['contact_migration_bouts']=migration['bouts'];result['quality_passed']=json.loads((ep/'quality.json').read_text())['passed'];result['source_sha256']={str(p):sha(p) for p in [hp,ep/'frontal_bypass.json',ep/'CONTACT_MIGRATION.json',ep/'quality.json',Path(__file__)]}
 return result
if __name__=='__main__':
 run=Path(sys.argv[1]).resolve();out=run/'BAG_LOSS_EVENT_COMPARISON.json';assert not out.exists();rows=[describe(run/f'case_{i}/layout_{i}_nudge_mailer_to_bin') for i in [840002,840003]];report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,training_ready=False);out.write_text(json.dumps(report,indent=2))
 for r in rows:print(json.dumps({k:v for k,v in r.items() if k not in ['source_sha256','contact_migration_bouts','lost_contact_events']},indent=2));print('loss exits',[(x['controller_exit_step'],x['last_action_mean_above_point3'],x['preceding_zero_load_actions']) for x in r['lost_contact_events']])
