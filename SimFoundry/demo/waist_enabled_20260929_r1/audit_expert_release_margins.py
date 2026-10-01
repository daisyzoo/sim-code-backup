"""Data-quality evidence: original gate margins and early release, no new gate."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];r=Path(sys.argv[1]).resolve();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rows=[]
for ep in sorted(r.glob('case_*/layout_*')):
 if ep.name.endswith('wait_no_package') or not (ep/'quality.json').exists():continue
 quality=json.loads((ep/'quality.json').read_text());fr=json.loads((ep/'frontal_bypass.json').read_text());key='box' if 'push_box' in ep.name else 'mailer';direction=-1 if key=='box' else 1
 with np.load(ep/'trace.npz') as z:xyz=z[key].astype(float)
 progress=direction*(xyz[-1,1]-xyz[0,1]);assert abs(progress-quality['metrics']['target_final_progress_m'])<1e-7
 release=next((x for x in fr['rows'] if x['mode']=='top_release'),None);info=None
 if release:
  t=release['step'];p=direction*(xyz[t,1]-fr['plan']['initial_target_xyz'][1]);zone=direction*xyz[t,1];info=dict(step=t,reason=release.get('release_reason'),progress_m=p,signed_y_m=zone,existing_margin_release_would_be_ready=bool(zone>=max(.205,direction*fr['plan']['initial_target_xyz'][1]+.16)))
 rows.append(dict(episode=ep.name,original_task_passed=quality['passed'],original_pose_passed=json.loads((ep/'EARLY_REVIEW.json').read_text())['pose']['search_success'] if (ep/'EARLY_REVIEW.json').exists() else None,progress_margin_m=progress-.15,min_final10_zone_margin_m=float(np.min(direction*xyz[-10:,1]-.20)),release=info,source_sha256={f:sha(ep/f) for f in ['raw.npz','trace.npz','quality.json','frontal_bypass.json']}))
passed=[x for x in rows if x['original_task_passed'] and x['original_pose_passed']];summary=dict(push_episodes_checked=len(rows),passed_episodes=len(passed),passed_confirmed_release_before_existing_buffer=sum(x['release'] is not None and x['release']['reason']=='confirmed_original_target_position' and not x['release']['existing_margin_release_would_be_ready'] for x in passed),passed_progress_margin_mm=[x['progress_margin_m']*1000 for x in passed],passed_final10_zone_margin_mm=[x['min_final10_zone_margin_m']*1000 for x in passed])
report=dict(summary=summary,rows=rows,source_sha256={str(p.relative_to(repo)):sha(p) for p in [repo/'simfoundry/data/paired_sorting.py',repo/'simfoundry/data/reach_sweep.py',repo/'simfoundry/data/confirmed_position_release.py']},auditor_sha256=sha(Path(__file__)),scope='Read-only exact original end-progress150mm and all-last10-frame zone200mm margins; compares actual first release with existing expert margin function205mm/160mm. No new quality threshold, no admission change, no physical/model causal claim. Extra expert target margin remains an untested intervention.',training_ready=False)
(r/'EXPERT_RELEASE_MARGIN_AUDIT.json').write_text(json.dumps(report,indent=2));lines=['# 成功示范的终点裕量审计','',report['scope'],'','|条件|原任务通过|推进裕量mm|末10帧最小目标区裕量mm|释放原因|','|---|---|---:|---:|---|']
for x in rows:lines.append(f'|{x["episode"]}|{x["original_task_passed"]}|{x["progress_margin_m"]*1000:.6f}|{x["min_final10_zone_margin_m"]*1000:.6f}|{x["release"]["reason"] if x["release"] else "未释放"}|')
lines+=['','原质量门未改，失败保留。ConfirmedPositionRelease按原150mm/200mm条件确认后可提前释放，而原ready_to_release本来留10mm推进/5mm区间裕量。成功示范非常贴近原门槛是学习鲁棒性风险，但无新模型因果证据。后续应在完整配对物理检查下比较保留内部裕量，不能只延长轨迹或修改评分。当前运行与候选对照保持冻结。'];(r/'EXPERT_RELEASE_MARGIN_AUDIT.md').write_text('\n'.join(lines)+'\n');print(summary)
