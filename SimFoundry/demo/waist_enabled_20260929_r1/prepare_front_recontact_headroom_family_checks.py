"""Adapt existing integration fixtures to independently audited headroom events."""
from pathlib import Path
import ast,json,re,hashlib,datetime
W=Path(__file__).resolve().parent;H=W/'staged_front_recontact_headroom';p=json.loads((H/'AUDIT_FAMILY_PREPARATION.json').read_text());mapping=p['replacements'];pattern=re.compile('|'.join(re.escape(k) for k in sorted(mapping,key=len,reverse=True)));records=[]
for old in ['check_front_recontact_native_wait.py','check_front_recontact_native_joint_branches.py','check_front_recontact_loaded_inputs.py']:
 src=W/old;s=pattern.sub(lambda m:mapping[m.group()],src.read_text());edits=[]
 def change(a,b):
  global s
  assert a in s,(old,a);s=s.replace(a,b);edits.append(dict(old=a,new=b))
 change("S/'AUDIT_V3_PREPARATION.json'","S/'AUDIT_FAMILY_PREPARATION.json'") if 'native_' in old else None
 if old.endswith('native_wait.py'):
  change('front_recontact_center_handovers=0)','front_recontact_center_handovers=0,front_recontact_planning_headroom=prep[\'planning_headroom\'])')
 else:
  change("front_bag_recontact_center_draft_r4","front_bag_recontact_headroom_draft_r1")
  change("D/'LIFECYCLE_CHECK.json'","D/'PROBE_RESULT.json'")
  change("f['recontacts']","f['counter']")
  if old.endswith('native_joint_branches.py'):change("bound['affine_events']==223","bound['affine_events']==143")
  else:
   change("S/'LOADED_INPUT_PREPARATION.json'","S/'AUDIT_FAMILY_PREPARATION.json'")
   change("for r in prep['records']:","for r in prep['adapters']:")
   change(" for e in reversed(r['edits']):assert back.count(e['new'])==1;back=back.replace(e['new'],e['old'],1)\n assert back==p.read_text();m=", " import re\n inv={v:k for k,v in prep['replacements'].items()}\n back=re.sub('|'.join(re.escape(k) for k in sorted(inv,key=len,reverse=True)),lambda m:inv[m.group()],back)\n assert back==p.read_text()\n tree0=ast.parse(t.read_text());executable=[n for n in tree0.body if not isinstance(n,(ast.Import,ast.ImportFrom,ast.FunctionDef,ast.ClassDef))]\n if any('sys.argv[' in ast.unparse(n) and not (isinstance(n,ast.If) and '__name__' in ast.unparse(n.test)) for n in executable):continue\n m=")
 ast.parse(s);dest=W/old.replace('front_recontact_','front_recontact_headroom_',1)
 with dest.open('x') as f:f.write(s)
 records.append(dict(parent=str(src),path=str(dest),edits=edits,sha256=hashlib.sha256(dest.read_bytes()).hexdigest()))
with (H/'FAMILY_CHECK_PREPARATION.json').open('x') as f:json.dump(dict(scope=__doc__,records=records),f,indent=2)
print('prepared3 integration checks')
