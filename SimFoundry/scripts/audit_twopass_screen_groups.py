#!/usr/bin/env python3
import argparse,json,hashlib,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from simfoundry.data.diverse_layouts import load_diagnostic_layout
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
protocol=json.loads((a.root/'PROTOCOL.json').read_text());result=json.loads((a.root/'run/RESULT.json').read_text());geometry=json.loads((a.root/'GEOMETRY_PREFLIGHT.json').read_text());rows=result['rows'];tasks={'push_box_to_bin','nudge_mailer_to_bin'};groups=[]
assert len({(r['case']['layout_id'],r['case']['task']) for r in rows})==len(rows)
for r in rows:
 f=a.root/f"run/case_{r['case']['layout_id']}_{r['case']['task']}/trajectory.npz";assert hashlib.sha256(f.read_bytes()).hexdigest()==r['sha256']
 assert r['fitness']['original_numeric_passed']==r['report']['passed']
for g in geometry['groups']:
 subset=[r for r in rows if r['case']['layout_id'] in g['layout_ids']]
 complete={(r['case']['layout_id'],r['case']['task']) for r in subset}=={(lid,t) for lid in g['layout_ids'] for t in tasks}
 failures=[]
 for r in subset:
  if not r['fitness']['search_success']:
   reasons=list(r['report']['reasons'])
   if not r['fitness']['support']:reasons.append('full footprint support failed')
   if not r['fitness']['upright']:reasons.append('tilt limit failed')
   failures.append(dict(layout_id=r['case']['layout_id'],task=r['case']['task'],reasons=reasons))
 input_errors=[]
 for lid in g['layout_ids']:
  case=next(x for x in protocol['cases'] if x['layout_id']==lid)
  try:load_diagnostic_layout(case['layout'],lid)
  except ValueError as exc:input_errors.append(dict(layout_id=lid,error=str(exc)))
 groups.append(dict(**g,layout_input_errors=input_errors,eligible_for_render=complete and not failures and not input_errors,complete=complete,observed=len(subset),passed_episodes=sum(r['fitness']['search_success'] for r in subset),passed=complete and not failures,failures=failures,training_ready=False))
fresh=[r for r in rows if r['case']['role']=='fresh_screen'];controls=[r for r in rows if r['case']['role']=='canonical_control']
if result['complete']:assert len(fresh)==32 and len(controls)==4 and all(g['complete'] for g in groups)
report=dict(complete=result['complete'],controls_passed=sum(r['fitness']['search_success'] for r in controls),fresh_passed=sum(r['fitness']['search_success'] for r in fresh),fresh_observed=len(fresh),complete_groups_passed=sum(g['passed'] for g in groups),groups=groups,scope='Group-aware no-render screen, split frozen before outcomes; only passing entire groups eligible for subsequent rendered review, no training admission.',training_ready=False,goal_complete=False)
a.out.write_text(json.dumps(report,indent=2));print('Fresh',report['fresh_passed'],'/',report['fresh_observed'],'groups',report['complete_groups_passed'],'/8','complete',report['complete'])
