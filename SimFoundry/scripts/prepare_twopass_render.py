#!/usr/bin/env python3
"""Freeze all eligible complete screen groups for diagnostic RGB reproduction."""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--screen',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();screen=a.screen.resolve();out=a.out.resolve()
result=json.loads((screen/'run/RESULT.json').read_text())
assert result['complete'] and not (screen/'run/ERROR.json').exists()
audit_path=screen/'GROUP_AND_INPUT_AUDIT.json'
subprocess.run([sys.executable,str(ROOT/'scripts/audit_twopass_screen_groups.py'),'--root',str(screen),'--out',str(audit_path)],check=True)
audit=json.loads(audit_path.read_text());assert audit['controls_passed']==4
eligible=[g for g in audit['groups'] if g['eligible_for_render']]
if not eligible:raise RuntimeError('No complete valid group available for rendering')
protocol=json.loads((screen/'PROTOCOL.json').read_text());out.mkdir(exist_ok=False);groups=[]
for g in eligible:
 layouts=[]
 for lid in g['layout_ids']:
  case=next(c for c in protocol['cases'] if c['layout_id']==lid);src=Path(case['layout']);payload=src.read_bytes()
  if 'layout_sha256' in case:assert hashlib.sha256(payload).hexdigest()==case['layout_sha256']
  dest=out/f'layout_{lid}.json';dest.write_bytes(payload)
  layouts.append(dict(layout_id=lid,path=str(dest),sha256=hashlib.sha256(payload).hexdigest()))
 groups.append(dict(group=g['group'],split=g['split'],kind=g['kind'],layouts=layouts))
preparation=screen/'RENDERER_PREPARATION.json'
first_far_exit_y=protocol.get('first_far_exit_y',.30)
if preparation.exists():
 prepared=json.loads(preparation.read_text());collector=Path(prepared['collector']).resolve()
 assert collector.parent==ROOT/'scripts' and hashlib.sha256(collector.read_bytes()).hexdigest()==prepared['sha256']
else:
 assert first_far_exit_y==.30, 'Changed first endpoint requires a bound renderer'
 collector=ROOT/'scripts/collect_twopass_sorting_diagnostic.py'
(out/'PROTOCOL.json').write_text(json.dumps(dict(groups=groups,collector=str(collector),collector_sha256=hashlib.sha256(collector.read_bytes()).hexdigest(),screen=str(screen),screen_audit_sha256=hashlib.sha256(audit_path.read_bytes()).hexdigest(),role='diagnostic',first_far_exit_y=first_far_exit_y,crossed_contact_offset=0.,training_ready=False,goal_complete=False,scope='All complete eligible groups from frozen screen. Independent RGB dynamic-expert reproduction; preserve every failure. No training admission, no VLA evaluation.'),indent=2))
(out/'collector_source.py').write_bytes(collector.read_bytes())
print('Prepared',len(groups),'complete groups /',4*len(groups),'episodes')
