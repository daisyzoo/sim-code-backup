"""Check independent task binding on completed saved one-step proposals.
Does not rerun candidate code or turn static proposal checks into physical data.
"""
from pathlib import Path
import json,sys,copy,hashlib,datetime
W=Path(__file__).resolve().parent;sys.path.insert(0,str(W))
from audit_front_loaded_z_fraction_task_v1 import verified_task
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
ep=W/'front_corridor_lateral_physical_r1/case_840023/layout_840023_nudge_mailer_to_bin';co={r['step']:r for r in read(ep/'coordination.json')};paths=sorted((W/'front_loaded_z_fraction_stream_check_r2').glob('840023_nudge_mailer_to_bin_*.json'))[:40];assert len(paths)==40
rows=[];sources={str(ep/'coordination.json'):sha(ep/'coordination.json')}
for p in paths:
 record=read(p);m=record['priority'];t=record['step'];task=co[t]['task_inputs'];out=verified_task(task,m,.25);assert out==m['reduced_z_task']['modified_task'];assert record['independent_nominal']['passed']==m['nominal_verification']['passed'];rows.append(dict(step=t,passed=True));sources[str(p)]=sha(p)
ref=read(paths[0])['priority'];original=co[ref['step']]['task_inputs'];negative=[]
for name in ['fraction','parent_linear_z','requested_original','modified_z','non_z_error','altered_original','context_current']:
 m=copy.deepcopy(ref);b=m['reduced_z_task']
 if name=='fraction':b['fraction']=.5
 elif name=='parent_linear_z':b['parent_linear_z_m']+=.0001
 elif name=='requested_original':b['original_requested_z_m']+=.0001
 elif name=='modified_z':b['modified_task']['error'][2]+=.0001
 elif name=='non_z_error':b['modified_task']['error'][0]+=.0001
 elif name=='altered_original':b['original_task']['error'][0]+=.0001
 elif name=='context_current':m['context']['current'][0]+=.001
 try:verified_task(original,m,.25)
 except AssertionError:negative.append(dict(case=name,rejected=True))
 else:raise AssertionError(('tampered task accepted',name))
for p in [Path(__file__),W/'audit_front_loaded_z_fraction_task_v1.py']:sources[str(p)]=sha(p)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,negative_rejections=negative,source_sha256=sources,passed=True,full_record_auditor_complete=False,collector_integrated=False,physics_started=False,training_ready=False)
dest=W/'front_loaded_z_fraction_candidate_v1/TASK_BINDING_CHECK.json'
with dest.open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(passed=True,records=len(rows),negative_rejections=len(negative))))
