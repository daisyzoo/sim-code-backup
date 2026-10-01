"""Require two fully reviewed original groups and actual ended processes."""
from pathlib import Path
import sys,json,subprocess,hashlib
w=Path(__file__).resolve().parent;r=Path(sys.argv[1]).resolve();p=json.loads((r/'PROTOCOL.json').read_text());s=json.loads((r/'STATUS.json').read_text());c=json.loads((r/'CONTROL_EVIDENCE_EXECUTION.json').read_text());assert s['stage']=='numeric_complete_actual_visual_review_pending' and c['stage']=='complete'
for d in [s,c,json.loads((r/'REGION_DIAGNOSTIC_EXECUTION.json').read_text())]:assert not (Path('/proc')/str(d['pid'])/'cmdline').exists()
reports=[]
for group in p['groups']:
 subprocess.run([sys.executable,str(w/'close_region_x_follow_group.py'),str(r),group],check=True,stdout=subprocess.DEVNULL);reports.append(json.loads((r/(group.upper()+'_RESULT.json')).read_text()))
assert len(reports)==2 and sum(x['push_total'] for x in reports)==8 and all(x['wait_passed'] for x in reports)
records=json.loads((r/'COLLECTION_EXECUTION.json').read_text());assert len(records)==10
for record in records:
 ep=next(r.glob('case_*/'+record['episode']));assert record['raw_sha256']==hashlib.sha256((ep/'raw.npz').read_bytes()).hexdigest() and record['collector_process_returncode'] in (0,1)
rows=[y for x in reports for y in x['rows']];assert len({x['episode'] for x in rows})==8;assert len(c['rows'])==sum(x['original_control_reports_verified'] for x in reports)
out=dict(push_passed=sum(x['push_passed'] for x in reports),push_total=8,waits_passed=2,actual_review_complete=True,original_control_reports_verified=len(c['rows']),tracking_action_reports_verified=8,continuity_action_reports_verified=8,x_follow_reports_verified=8,rows=rows,groups=reports,protocol_sha256=hashlib.sha256((r/'PROTOCOL.json').read_bytes()).hexdigest(),training_ready=False,scope='Complete original two swap groups8push+2ordinarywait, all archived source/raw/action/actual sampled image checks verified. Development diagnostic, no dataset admission or independent model score.')
(r/'RESULT.json').write_text(json.dumps(out,indent=2));lines=[f'# 区域接触X跟随候选完整结果：{out["push_passed"]}/8 推动，2等待通过','',out['scope'],'','|组|推动通过|等待|','|---|---:|---|']
for group in reports:lines.append(f'|{group["group"]}|{group["push_passed"]}/{group["push_total"]}|通过|')
lines+=['','本报告为完整开发诊断结果，不能直接作为训练数据准入或独立模型成绩。各失败及原因以原始质量与CAUSE_REPORT.md为准；不从成功单条推断整组通过。','详见CAUSE_REPORT.md，原门、零位、无助推和非目标稳定检查保持。']
(r/'RESULT.md').write_text('\n'.join(lines)+'\n');print({k:v for k,v in out.items() if k not in {'rows','groups'}})
