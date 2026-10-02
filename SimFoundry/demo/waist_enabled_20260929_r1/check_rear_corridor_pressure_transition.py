"""Original scalar24-substep pressure stream at explicit synthetic commit boundary.
Real history through one changed final state only; no hypothetical subsequent
forces, no new physical trajectory or training admission. Full native boundary
records were independently verified before their final row is used.
"""
from pathlib import Path
import json,sys,hashlib,datetime,os,copy
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_rear_corridor_recovery_guarded';sys.path[:0]=[str(W),str(ROOT)]
from rear_corridor_audit_inputs import verify_inputs
from audit_rear_corridor_stage_pressure import independent_loads,verify_stream
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();dest=W/'REAR_CORRIDOR_PRESSURE_TRANSITION_CHECK.json';assert not dest.exists();rows=[];negative=[];sources={}
def save(status,**extra):
 p=dest.with_suffix('.tmp');p.write_text(json.dumps(dict(status=status,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,negative_checks=negative,source_sha256=sources,training_ready=False,**extra),indent=2));p.replace(dest)
try:
 save('running');fixtures=json.loads((W/'REAR_CORRIDOR_NATIVE_FIXTURE_CHECK.json').read_text())['cases']
 for case in fixtures:
  if case['kind']=='wait':continue
  ep=W/case['source_episode'];t=case['source_step'];v=verify_inputs(Path(case['fixture']),ROOT,S);assert t in v.overrides
  pressure=json.loads((ep/'peak_load_updates.json').read_text());fr=json.loads((ep/'frontal_bypass.json').read_text());n=pressure['executed_action_count'];task='push_box_to_bin' if case['key']=='box' else 'nudge_mailer_to_bin'
  metadata=json.loads((ep/'SUBSTEP_CONTACT_RECORDING.json').read_text())['metadata']
  with np.load(ep/'substep_contacts.npz') as z:arrays={k:z[k] for k in z.files}
  measured=independent_loads(arrays,metadata,task,n);loads={s:measured[s] for s in range(t+1)}
  pressure['executed_action_count']=t+1;pressure['rows']=[r for r in pressure['rows'] if r['action_step']<=t];pressure['final_control_states']=[r for r in pressure['final_control_states'] if r['step']<=t];fr['rows']=[r for r in fr['rows'] if r['step']<=t]
  baseline=verify_stream(pressure,fr,loads,frames=t+1,wait=False)
  final=copy.deepcopy(next(r for r in json.loads((Path(case['fixture'])/'frontal_bypass.json').read_text())['rows'] if r['step']==t));assert fr['rows'][-1]==v.overrides[t]['parent_row']
  fr['rows'][-1]=final;last=pressure['final_control_states'][-1];assert last['step']==t;before=copy.deepcopy(last)
  last.update(mode=final['mode'],top_mode=final['mode'],bias_m=final['contact_load']['stored_z_bias_m'])
  current=verify_stream(pressure,fr,loads,frames=t+1,wait=False)
  if case['kind']=='unload':
   assert t not in baseline['original_zero_resets_after_update'] and t in current['original_zero_resets_after_update'];assert before['bias_m']!=0. and last['bias_m']==0.
   assert last['filtered_n']==before['filtered_n']>0.
  else:assert current==baseline
  for label,mutate in [('cleared_filter',lambda x:x['final_control_states'][-1].update(filtered_n=0.)),('changed_update_count',lambda x:x['final_control_states'][-1].update(pressure_update_count=-1)),('invented_bias',lambda x:x['final_control_states'][-1].update(bias_m=.024))]:
   bad=copy.deepcopy(pressure);mutate(bad)
   try:verify_stream(bad,fr,loads,frames=t+1,wait=False)
   except AssertionError:negative.append(case['kind']+'_'+case['key']+'_'+label)
   else:raise AssertionError('pressure corruption accepted '+label)
  v.assert_unchanged();rows.append(dict(kind=case['kind'],key=case['key'],through_step=t,scalar_substeps=24*(t+1),reset_preserves_filter=True,original_update_count_preserved=True,synthetic_commit_boundary=True));save('running');print(case['kind'],case['key'],flush=True)
  for name in ['peak_load_updates.json','frontal_bypass.json','SUBSTEP_CONTACT_RECORDING.json','substep_contacts.npz']:sources[str(ep/name)]=sha(ep/name)
 for p in [Path(__file__),W/'audit_rear_corridor_stage_pressure.py',W/'audit_peak_load_update_math.py',W/'REAR_CORRIDOR_NATIVE_FIXTURE_CHECK.json']:sources[str(p)]=sha(p)
 save('complete',passed=True)
except BaseException as e:save('check_failed',error=repr(e));raise
