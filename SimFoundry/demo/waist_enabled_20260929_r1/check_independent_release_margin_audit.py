"""Independent raw-row arithmetic and forged-confirmation rejection on all56 histories.
Unchanged historical rows may pass an arithmetic gate but are NOT new-source data.
"""
from pathlib import Path
import json,hashlib,datetime,copy,sys
W=Path(__file__).resolve().parent;sys.path.insert(0,str(W));from audit_confirmed_release_margin import verify_rows
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();source=W/'CONFIRMED_RELEASE_MARGIN_HISTORY_CHECK.json';history=json.loads(source.read_text());rows=[];dest=W/'INDEPENDENT_RELEASE_MARGIN_AUDIT_CHECK.json';assert not dest.exists();negatives=[]
for item in history['rows']:
 ep=W/item['run']/('case_'+item['episode'].split('_')[1])/item['episode'];p=ep/'frontal_bypass.json';assert sha(p)==history['source_sha256'][str(p)];fr=json.loads(p.read_text());plan=fr['plan'];kw=dict(initial_y=plan['initial_target_xyz'][1],direction=plan['direction']);proof=verify_rows(fr['rows'],enabled=False,**kw);assert proof['observations']==item['observations_checked'];changed=item['first_changed_confirmation'] is not None
 try:verify_rows(fr['rows'],enabled=True,**kw);rejected=False
 except AssertionError:rejected=True
 assert rejected==changed
 if changed:
  # Minimal declared synthetic row fixture: modify confirmations according to
  # independently screened new observer but leave original early release entry.
  bad=copy.deepcopy(fr['rows']);first=item['first_changed_confirmation']['step'];target=next(r for r in bad if r['step']==first);target['terminal_position_confirmed']=True
  try:verify_rows(bad,enabled=True,**kw)
  except AssertionError:negatives.append(item['run']+'/'+item['episode'])
  else:raise AssertionError('premature confirmation accepted')
 rows.append(dict(run=item['run'],episode=item['episode'],original_rows_reproduced=proof['observations'],new_rule_rejects_unchanged_early_confirmation=rejected))
assert verify_rows([],initial_y=0.,direction=1,enabled=True,wait=True)['passed']
try:verify_rows([],initial_y=0.,direction=1,enabled=True)
except AssertionError:pass
else:raise AssertionError('missing push observations admitted')
out=dict(status='complete',passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,premature_confirmation_rejections=len(negatives),missing_push_rows_rejected=True,source_history_sha256=sha(source),auditor_sha256=sha(W/'audit_confirmed_release_margin.py'),checker_sha256=sha(__file__),physics=False,training_ready=False)
with dest.open('x') as f:json.dump(out,f,indent=2)
print('passed histories',len(rows),'premature rejections',len(negatives))
