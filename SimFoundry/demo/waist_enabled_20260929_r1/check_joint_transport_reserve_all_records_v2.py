"""Independently audit all27 runtime contexts, including all3 rejected proposals.
Unissued fixtures only. Never reinterpret observed future as new command response.
"""
from pathlib import Path
import json,hashlib,datetime,sys,copy
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_joint_transport_reserve_v1';D=W/'joint_transport_reserve_preparation_r1';sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from audit_joint_transport_reserve_records_v2 import JointRecordAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={};cache={};rows=[];negative=[]
def read(p):sources[str(p)]=sha(p);return json.loads(p.read_text())
proof=read(D/'RUNTIME_CONTEXT_CHECK.json');assert proof['passed'];audit=JointRecordAudit(ROOT,S,ClearanceGuard(ROOT,S))
for item in proof['contexts']:
 ep=W/item['source_run']/('case_'+item['episode'].split('_')[1])/item['episode'];t=item['step'];r=read(Path(item['record']));assert sha(item['record'])==item['record_sha256']
 if ep not in cache:cache[ep]=({r['step']:r for r in read(ep/'coordination.json')},{r['step']:r for r in read(ep/'frontal_bypass.json')['rows']})
 c=copy.deepcopy(cache[ep][0][t]);fr=cache[ep][1][t];p=r['proposal'];ctx=r['collector_context'];c['joint_transport_clearance']=r
 c.pop('joint_transport_unexecuted_parent_waist_target_rad',None)
 c['waist_target_rad']=r['output_command'][0]
 if r['applied']:c['joint_transport_unexecuted_parent_waist_target_rad']=r['parent_command'][0]
 kw=dict(step=t,selected=True,side=item['side'],row=fr,coordinate=c,scene=ctx['scene'],current=ctx['current'],previous_q=ctx['previous_q'],previous_command=ctx['previous_command'],parent_command=r['parent_command'],final_command=r['output_command'],decay=ctx['decay'])
 result=audit.verify(r,**kw);assert result['applied']==item['applied'];rows.append(dict(side=item['side'],**result));print(json.dumps(dict(step=t,applied=result['applied'],reason=result['reason'])),flush=True)
 if t in [225,233]:
  for key,value in [('elbow_reserve_m',0.),('nominal_predicted_elbow_floor_m',.005),('solver_maxiter',120),('solver_ftol',1e-11),('objective_scale',1.)]:
   bad=copy.deepcopy(r);args=copy.deepcopy(kw);bad['proposal'][key]=value;args['coordinate']['joint_transport_clearance']=bad
   try:audit.verify(bad,**args)
   except (AssertionError,ValueError):negative.append(dict(step=t,field=key,rejected=True))
   else:raise AssertionError('policy mutation accepted')
assert len(rows)==27 and sum(r['applied'] for r in rows)==24 and len(negative)==10
for p in [Path(__file__),W/'audit_joint_transport_reserve_records_v2.py',S/'COLLECTOR_PREPARATION.json',*[S/n for n in json.loads((S/'COLLECTOR_PREPARATION.json').read_text())['stage_sha256']]]:sources[str(p)]=sha(p)
for p,h in sources.items():assert sha(p)==h,p
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,rows=rows,negative=negative,source_sha256=sources,physical_execution=False,training_ready=False)
with (D/'ALL_RECORDS_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print('ALL27_INDEPENDENT_RECORDS_PASS_10POLICY_REJECTIONS',flush=True)
