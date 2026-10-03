"""Independent audit fixtures ending at the first counterfactual command.
Only observed unchanged prefixes are reused. The changed endpoint is synthetic;
no old later observation is represented as an outcome of the new controller.
Requires a completed source-bound original native capture report for each case.
"""
from pathlib import Path
from types import SimpleNamespace
import copy,datetime,hashlib,json,sys
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_loaded_reference';sys.path[:0]=[str(S),str(W),str(ROOT)]
from front_loaded_reference_adapter import admit
from simfoundry.data.top_contact_load_geometry import loaded_forward_margin
from audit_front_loaded_material_cap import MaterialCapAudit
from audit_front_loaded_reference_cop_math import reconstruct
from audit_unloaded_wrist_prior_live import HandModel
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();out=W/'FRONT_LOADED_MATERIAL_AUDIT_CHECK.json';assert not out.exists()
report=dict(status='running',scope=__doc__,positive=[],negative=[],pending=[],simulation_started=False,training_ready=False,source_sha256={str(p):sha(p) for p in [Path(__file__),W/'audit_front_loaded_material_cap.py',W/'audit_front_loaded_reference_cop_math.py',S/'front_loaded_reference_adapter.py',S/'front_initial_loaded_reference_cap.py']})
def save():report['updated_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();out.write_text(json.dumps(report,indent=2))
hand=HandModel(ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',ROOT/'assets/robots/g1_hand_support_vertices.json')
try:
 save();probe=json.loads((W/'FRONT_INITIAL_LOADED_REFERENCE_CAP_PROBE.json').read_text())
 for case in probe['records']:
  if case['first_intervention'] is None:continue
  ep=next((W/'front_initial_physical_r1').glob('case_*/'+case['episode']));native=ep/'FRONT_INITIAL_STAGE_POSE_LIVE_V2_AUDIT.json'
  if not native.exists():report['pending'].append(dict(episode=ep.name,reason='original native capture report not yet complete'));continue
  native_result=json.loads(native.read_text());assert native_result['passed'] is True and native_result['front_result']['passed'] is True
  for n,h in native_result['source_sha256'].items():assert sha(ep/n)==h
  for n,h in native_result['dependent_auditors_sha256'].items():assert sha(W/n)==h
  assert sha(W/'audit_front_initial_stage_pose_live.py')==native_result['auditor_sha256']
  assert sha(ep.parent/'provenance.json')==native_result['provenance_sha256']
  with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float)
  with np.load(ep/'trace.npz') as z:tr={k:z[k] for k in z.files}
  with np.load(ep/'parcel_orientation.npz') as z:ori={k:z[k] for k in z.files}
  fr=json.loads((ep/'frontal_bypass.json').read_text());key='box' if 'push_box' in ep.name else 'mailer';side='right' if key=='box' else 'left';actor='parcel_box' if key=='box' else 'mailer'
  packets={r['after_action_step']:r for r in json.loads((ep/'solved_contact_forces.json').read_text())['rows']};all_events=json.loads((ep/'front_initial_center.json').read_text())['rows'];verified={r['step']:{k:v for k,v in r.items() if k!='step'} for r in all_events if r['kind'] in ('command','handover')}
  assert set(verified)=={r['step'] for r in native_result['front_records']}
  end=case['first_intervention']['step'];original=copy.deepcopy(fr['rows'][:end]);assert original[-1]['step']==end
  generated=[];runtime=SimpleNamespace(center_local=None,rows=[])
  for row in original:
   t=row['step'];runtime.rows=[r for r in all_events if r['step']<=t];capture=next((r for r in runtime.rows if r['kind']=='handover'),None);runtime.center_local=None if capture is None else np.array(capture['captured_center_local'])
   state=SimpleNamespace(command=tuple(row['target_xyz']),last_emitted_xy=tuple(row['target_xyz'][:2]));previous=original[t-2]['target_xyz'][:2] if t>1 else None
   contact=loaded_forward_margin(packets[t-1],side,actor,tr[key][t],ori[key][t],fr['plan']['top_recontact']['contact_size_xyz'],-1 if key=='box' else 1)
   normal=contact['normal_load_n'] if contact['valid'] else 0.
   result,stop=admit(enabled=True,row=row,state=state,runtime=runtime,previous_xy=previous,normal_load_n=normal,step=t)
   assert stop is None
   if t<end:assert list(result['target_xyz'])==list(row['target_xyz'])
   generated.append(result)
  assert generated[-1]['loaded_reference_cap']['changed'] is True
  assert sum(r['loaded_reference_cap']['changed'] for r in generated)==1
  events={t:r for t,r in verified.items() if t<=end}
  def check(rows,trace=tr,events_override=events):
   audit=MaterialCapAudit(rows,fr['plan'],trace[key],ori[key],packets,key,q,hand,events_override,enabled=True)
   records,errors=reconstruct(rows,fr['plan'],trace,ori,packets,key,material_cap_audit=audit)
   assert not errors,errors
   return audit.finish(),records
  accepted,records=check(generated);assert accepted['changed_rows']==1 and accepted['loaded_rows']>0
  report['positive'].append(dict(episode=ep.name,unchanged_prefix=end-1,synthetic_first_command=end,loaded_rows=accepted['loaded_rows'],parent_COP_rows=len(records),passed=True,no_post_intervention_outcomes=True))
  for label in ['emitted_xy','old_command_history','material_surface','hand_reference','force_value','cap_bound','missing_capture','future_capture','parent_COP_forgery']:
   rows=copy.deepcopy(generated);ev=copy.deepcopy(events);r=rows[-1];a=r['loaded_reference_cap']
   if label=='emitted_xy':r['target_xyz']=list(r['target_xyz']);r['target_xyz'][0]+=.001
   elif label=='old_command_history':a['previous_command_xy'][0]+=.001
   elif label=='material_surface':r['parcel_top_xyz'][0]+=.001;a['material_surface_xy'][0]+=.001
   elif label=='hand_reference':r['observed_support_xyz'][0]+=.001;a['reference_xy'][0]+=.001
   elif label=='force_value':a['normal_load_n']+=.1
   elif label=='cap_bound':a['cap_xy_m']=.011
   elif label=='missing_capture':ev={t:e for t,e in ev.items() if e['kind']!='handover'}
   elif label=='future_capture':a['capture_step']=end+1
   else:
    parent=copy.deepcopy(original[-1]);parent['target_xyz']=list(parent['target_xyz']);parent['target_xyz'][0]+=.0001
    state=SimpleNamespace(command=tuple(parent['target_xyz']),last_emitted_xy=tuple(parent['target_xyz'][:2]));rows[-1],stop=admit(enabled=True,row=parent,state=state,runtime=runtime,previous_xy=original[-2]['target_xyz'][:2],normal_load_n=normal,step=end);assert stop is None
   rejected=False
   try:check(rows,events_override=ev)
   except (AssertionError,KeyError,ValueError):rejected=True
   assert rejected,label
   report['negative'].append(dict(episode=ep.name,case=label,rejected=True))
  for p in [native,ep/'raw.npz',ep/'trace.npz',ep/'parcel_orientation.npz',ep/'frontal_bypass.json',ep/'front_initial_center.json',ep/'solved_contact_forces.json']:report['source_sha256'][str(p)]=sha(p)
 assert report['positive'],'At least one source-bound actual native capture required'
 report.update(status='complete_available_native_prefix_fixtures',passed=True);save();print(json.dumps({k:v for k,v in report.items() if k not in ['source_sha256','scope']},indent=2))
except Exception as e:report.update(status='failed',error=repr(e));save();raise
