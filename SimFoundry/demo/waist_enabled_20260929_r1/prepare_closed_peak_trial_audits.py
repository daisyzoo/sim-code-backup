"""Version original independent audits for explicit fresh pilot source/role.
All numeric math is inherited; admission is separately bound to v2 and archives.
"""
from pathlib import Path
import ast,datetime,hashlib,json
W=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def rename(s):
 return (s.replace('audit_peak_guard','audit_closed_peak_trial').replace('peak_guard_audit_context','closed_peak_trial_audit_context').replace('verify_peak_guard_source','verify_closed_peak_trial_source').replace('peak_guard_source_binding','closed_peak_trial_source_binding').replace('staged_peak_load_guard','staged_closed_peak_trial').replace('PEAK_GUARD_','CLOSED_PEAK_TRIAL_'))

def main():
 rows=[]
 for src in sorted(W.glob('audit_peak_guard*.py'))+[W/'peak_guard_audit_context.py']:
  dst=W/rename(src.name);text=rename(src.read_text())
  changes=[]
  # These six role assertions follow explicit full source admission in their auditors.
  for old,new in [("args['role']=='diagnostic'","args['role']=='pilot'"),("a['role']=='diagnostic'","a['role']=='pilot'")]:
   if old in text:changes.append(dict(old=old,new=new,count=text.count(old)));text=text.replace(old,new)
  ast.parse(text)
  with dst.open('x') as f:f.write(text)
  restored=text
  for c in reversed(changes):restored=restored.replace(c['new'],c['old'])
  assert restored==rename(src.read_text())
  rows.append(dict(parent=str(src),parent_sha256=sha(src),new=str(dst),new_sha256=sha(dst),role_changes=changes,numeric_math_unchanged=True))
 report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,scope='Explicit source/role/report names only; same pressure and control math. No fresh physical validation yet.',rows=rows,source_sha256={str(Path(__file__)):sha(__file__),str(W/'closed_peak_trial_source_binding.py'):sha(W/'closed_peak_trial_source_binding.py')},training_ready=False)
 with (W/'CLOSED_PEAK_TRIAL_AUDIT_VERSION_CHECK.json').open('x') as f:json.dump(report,f,indent=2)
 print('versioned',len(rows),'modules; role assertions',sum(sum(c['count'] for c in r['role_changes']) for r in rows))

if __name__=='__main__':main()
