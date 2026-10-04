"""Close completed original trial: audits pass, whole paired task groups fail."""
from pathlib import Path
import datetime,hashlib,json
W=Path(__file__).resolve().parent;R=W/'front_loaded_z_quarter_physical_r2';read=lambda p:json.loads(Path(p).read_text());cache={}
def sha(p):
 p=Path(p)
 if p not in cache:cache[p]=hashlib.sha256(p.read_bytes()).hexdigest()
 return cache[p]
a=read(R/'AUDIT_STATUS.json');v=read(R/'NUMERIC_VISUAL_SUMMARY.json');assert a['status']=='complete' and len(a['rows'])==224;assert v['actual_reviews']==10 and v['push_passed']==6 and v['wait_passed']==2
folders={p.name:p for p in R.glob('case_*/layout_*') if p.is_dir()};bound=[]
for row in a['rows']:
 assert row['process_returncode']==row['returncode']==0 and row['report_passed'] is True
 ep=folders[row['episode']];report=ep/row['report'];assert sha(report)==row['report_sha256'];assert sha(ep/'raw.npz')==row['raw_sha256'];assert sha(W/row['script'])==row['auditor_sha256']
 bound.append(dict(episode=row['episode'],report=str(report),sha256=sha(report)))
for p,h in v['source_sha256'].items():assert sha(p)==h,p
now=datetime.datetime.now(datetime.timezone.utc).isoformat();result=dict(created_at_utc=now,scope=__doc__,audit_rows=224,audit_failures=0,actual_visual_reviews=10,push_passed=6,push_total=8,wait_passed=2,wait_total=2,qualified_groups=0,closed=True,training_ready=False,new_admissions=0,decision='Original controls/geometry audits complete; retain task failure and reject both whole groups.',bound_reports=bound,source_sha256={str(p):sha(p) for p in [Path(__file__),R/'AUDIT_STATUS.json',R/'NUMERIC_VISUAL_SUMMARY.json']},goal_complete=False)
with (R/'CLOSED_ORIGINAL_AUDITS_AND_TASK_DECISION_V1.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps({k:result[k] for k in ['audit_rows','audit_failures','actual_visual_reviews','push_passed','wait_passed','qualified_groups','closed','training_ready']}),flush=True)
