"""Summarize fixed-parameter prediction evidence, including large-command tails."""
from pathlib import Path
import json,hashlib,sys
import numpy as np
w=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rows=[]
for arg in sys.argv[1:]:
 ep=Path(arg).resolve();p=ep/'LOADED_CAUSAL_PREDICTION_DIAGNOSIS.json';d=json.loads(p.read_text());assert d['checker_sha256']==sha(w/'diagnose_loaded_causal_prediction.py')
 for n,h in d['source_sha256'].items():assert sha(ep/n)==h
 with np.load(ep/'raw.npz') as z:u=z['action'][:,12:23].astype(float)
 groups={'delta_le_0.005rad':[],'delta_gt_0.005rad':[]}
 for r in d['rows']:groups['delta_gt_0.005rad' if np.max(abs(u[r['step']]-u[r['step']-1]))>.005 else 'delta_le_0.005rad'].append(r)
 binned={}
 for name,values in groups.items():
  if not values:continue
  binned[name]=dict(frames=len(values),metrics={method:dict(p50_mm=float(np.median([next(v for v in r['variants'] if v['name']==method)['position_error_mm'] for r in values])),p90_mm=float(np.percentile([next(v for v in r['variants'] if v['name']==method)['position_error_mm'] for r in values],90))) for method in ['constant_velocity','frozen_unloaded_causal']})
 worst=sorted([dict(step=r['step'],error_mm=next(v for v in r['variants'] if v['name']=='frozen_unloaded_causal')['position_error_mm']) for r in d['rows']],key=lambda v:-v['error_mm'])[:5]
 rows.append(dict(episode=str(ep),report_sha256=sha(p),summary=d['summary'],command_change_bins=binned,worst_causal_frames=worst))
assert rows
out=dict(rows=rows,checker_sha256=sha(Path(__file__)),training_ready=False,scope='Descriptive prediction errors on executed commands, no command interventions. Existing historical unloaded fit verified byte-for-byte; no current trajectory fitting. Velocity baseline can outperform causal on tail errors; neither certifies new-command response or physical contact.')
(w/'LOADED_CAUSAL_PREDICTION_SUMMARY.json').write_text(json.dumps(out,indent=2))
lines=['# 带载响应：仅预测诊断，无控制变更','','|实录|帧数|名义位置误差中位mm|速度外推mm|冻结因果响应mm|因果P90 mm|因果最大mm|','|---|---:|---:|---:|---:|---:|---:|']
for r in rows:
 s={v['name']:v for v in r['summary']['all_loaded_with_past']};e=Path(r['episode']);lines.append(f"|{e.parent.parent.name}/{e.name}|{s['nominal_command']['frames']}|{s['nominal_command']['median_position_error_mm']:.3f}|{s['constant_velocity']['median_position_error_mm']:.3f}|{s['frozen_unloaded_causal']['median_position_error_mm']:.3f}|{s['frozen_unloaded_causal']['p90_position_error_mm']:.3f}|{r['worst_causal_frames'][0]['error_mm']:.3f}|")
lines+=['','所有预测仅使用当前/过去q与动作及当前虚拟参考偏移；下一q仅评分。首加载/上一帧不带载的帧排除，不能外推至这些阶段。参数来自已核哈希的更早无载记录，没有拟合当前实录。','好：观测历史能显著降低“直接达到命令角”的预测误差，并发现名义未外移但实际外移。差：部分大动作/误差尾部上，简单速度外推更好，因果模型仍有毫米级最坏误差。不能直接按中位数设置安全余量，也不能把事实预测当修改命令后的因果保证。','下一仍需完成原物理整组审核；任何使用带载响应的新控制，须另做同原界的可行性、保护和完整物理验证。当前生产、冻结collector与质量门未改。']
(w/'LOADED_CAUSAL_PREDICTION_SUMMARY.md').write_text('\n'.join(lines)+'\n');print('prediction reports',len(rows))
