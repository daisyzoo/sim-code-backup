"""Uninstalled resolver check across all628 affected saved contexts and tampering cases."""
from pathlib import Path
import json,hashlib,datetime,copy
import numpy as np
from effective_loaded_contact_task_v1 import resolve
W=Path(__file__).resolve().parent;R=W/'front_loaded_z_quarter_physical_r2';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={};rows=[];contexts=[]
def read(p):sources[str(p)]=sha(p);return json.loads(p.read_text())
for ep in sorted(R.glob('case_*/layout_*')):
 if not (ep/'joint_transport_clearance.json').exists() or 'wait_no_package' in ep.name:continue
 records=read(ep/'joint_transport_clearance.json')['rows'];coords={c['step']:c for c in read(ep/'coordination.json')}
 for r in records:
  c=coords.get(r['step']);l=None if c is None else c.get('front_loaded_z_priority')
  if not l or not l.get('applied') or 'reduced_z_task' not in l or not r['selected']:continue
  ctx=r['collector_context'];before=copy.deepcopy(c);side=ctx['side'];task,b=resolve(c,side=side,current=ctx['current'],parent_command=r['parent_command'],quarter_enabled=True);assert c==before;assert task==l['reduced_z_task']['modified_task'];assert task is not c['task_inputs']
  row=dict(episode=ep.name,step=r['step'],bound=True,original_inputs_unchanged=True)
  if r.get('proposal'):
   p=r['proposal'];q=np.asarray(ctx['current']);u=np.asarray(p['command']);zr=2 if side=='left' else 5;err=float(np.asarray(task['jacobian'])[zr]@(u-q)-task['error'][zr]);contact=p['original_loaded_contact_check'];height=abs(err)<=2e-7;normal=contact['exact_attitude_delta']<=1e-6 and contact['linear_attitude_delta_mm']<=.0002;table=min(contact['nominal_table_margins_m'])>=0
   row.update(proposal_effective_height_passed=height,proposal_normal_and_table_passed=normal and table,solver_success=p['solver_success'],full_independent_certificate_and_path_still_required=True)
  rows.append(row);contexts.append((c,ctx,r))
assert len(rows)==628
c,ctx,r=next(v for v in contexts if v[0]['step']==190 and v[1]['side']=='left');tests=[]
def reject(name,edit,flag=True):
 d=copy.deepcopy(c);edit(d)
 try:resolve(d,side=ctx['side'],current=ctx['current'],parent_command=r['parent_command'],quarter_enabled=flag)
 except (ValueError,KeyError):tests.append(name)
 else:raise AssertionError('accepted tampering '+name)
reject('quarter_disabled',lambda d:None,False)
reject('wrong_fraction',lambda d:d['front_loaded_z_priority']['reduced_z_task'].__setitem__('fraction',.5))
reject('changed_original_objective',lambda d:d['task_inputs']['error'].__setitem__(0,d['task_inputs']['error'][0]+1e-4))
reject('changed_modified_xy',lambda d:d['front_loaded_z_priority']['reduced_z_task']['modified_task']['error'].__setitem__(0,999.))
reject('changed_modified_height',lambda d:d['front_loaded_z_priority']['reduced_z_task']['modified_task']['error'].__setitem__(2,0.))
reject('changed_reduction_formula',lambda d:d['front_loaded_z_priority']['reduced_z_task'].__setitem__('modified_requested_z_m',0.))
reject('stale_context',lambda d:d['front_loaded_z_priority']['context'].__setitem__('step',189))
reject('wrong_side',lambda d:d['front_loaded_z_priority']['context'].__setitem__('side','right'))
reject('wrong_parent',lambda d:d['front_loaded_z_priority']['output_command'].__setitem__(0,0.))
reject('nonfinite_height',lambda d:d['front_loaded_z_priority']['reduced_z_task'].__setitem__('parent_linear_z_m',float('nan')))
for key in ['lower','upper','step_limits','damping','preferred_step']:
 reject('modified_'+key,lambda d,k=key:d['front_loaded_z_priority']['reduced_z_task']['modified_task'][k].__setitem__(0,999.))
original_contexts=[]
for case,task_name in [(840023,'nudge_mailer_to_bin'),(840020,'push_box_to_bin')]:
 ep=W/'joint_transport_reserve_physical_r1'/f'case_{case}'/f'layout_{case}_{task_name}'
 records=read(ep/'joint_transport_clearance.json')['rows'];coords={v['step']:v for v in read(ep/'coordination.json')}
 chosen=next(v for v in records if v.get('selected') and v.get('collector_context') and coords[v['step']].get('front_loaded_z_priority',{}).get('applied'))
 co=coords[chosen['step']];ct=chosen['collector_context'];assert 'reduced_z_task' not in co['front_loaded_z_priority']
 out,binding=resolve(co,side=ct['side'],current=ct['current'],parent_command=chosen['parent_command'],quarter_enabled=False)
 assert out==co['task_inputs'] and binding['target']=='original_task';original_contexts.append(dict(episode=ep.name,step=chosen['step']))
for p in [Path(__file__),W/'effective_loaded_contact_task_v1.py']:sources[str(p)]=sha(p)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,original_full_task_contexts=original_contexts,previous_check_failure='V1 wrong_side mutation set right on an already-right context; no mutation occurred. V2 uses explicit left context. Resolver unchanged.',affected_contexts=len(rows),proposal_contexts=sum('proposal_effective_height_passed' in x for x in rows),effective_height_passed=sum(x.get('proposal_effective_height_passed',False) for x in rows),negative_cases_rejected=tests,rows=rows,source_sha256=sources,runtime_integrated=False,full_independent_certificate_and_paths_pending=True,physical_benefit_proven=False,training_ready=False)
with (R/'EFFECTIVE_LOADED_CONTACT_TASK_CHECK_V2.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps({k:v for k,v in out.items() if k not in ['rows','source_sha256','scope']},indent=2))
