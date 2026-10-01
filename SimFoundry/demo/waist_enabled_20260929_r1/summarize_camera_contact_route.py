"""Combine visibility, static pose tradeoffs and actual rear-route depth costs; no controller approval."""
from pathlib import Path
import json,hashlib
w=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();d=json.loads((w/'CAMERA_CONTACT_POSTURE_SCREEN.json').read_text());assert d['checker_sha256']==sha(w/'screen_camera_contact_postures.py');rows=[]
for ep in d['episodes']:
 path=next((w/'joint_edge_retry_groups_r1').glob('case_*/'+ep['episode']));assert ep['camera_diagnostic_sha256']==sha(path/'CAMERA_FRUSTUM_DIAGNOSIS.json') and ep['provenance_sha256']==sha(path.parent/'provenance.json')
 for visibility in ['unconstrained','target_only','both']:
  chosen=[]
  for r in ep['rows']:
   sols=[s for s in r['solutions'] if s['visibility']==visibility and s['solver_success'] and (visibility=='unconstrained' or s['view_constraint_min']>=-1e-6)]
   if sols:
    best=min(sols,key=lambda s:s['active_reference_error_mm']+s['inactive_reference_error_mm']);chosen.append(dict(step=r['step'],**best))
  rows.append(dict(episode=ep['episode'],visibility=visibility,normal_converged_states=len(chosen),best=chosen))
route=json.loads((w/'REAR_ROUTE_DEPTH_COST.json').read_text());assert route['checker_sha256']==sha(w/'diagnose_rear_route_depth_cost.py')
for r in route['rows']:
 ep=next((w/r['run']).glob('case_*/'+r['episode']))
 for n,h in r['source_sha256'].items():assert sha(ep/n)==h
out=dict(scope=__doc__,rows=rows,source_sha256={n:sha(w/n) for n in ['CAMERA_CONTACT_POSTURE_SCREEN.json','CAMERA_FRUSTUM_SUMMARY.json','REAR_ROUTE_DEPTH_COST.json']},checker_sha256=sha(Path(__file__)),training_ready=False,control_wired=False)
(w/'CAMERA_CONTACT_ROUTE_FINDING.json').write_text(json.dumps(out,indent=2))
lines=['# 后绕路线：接触与视野需要联合规划','','后绕数值修复没有带来困难任务成功；新的诊断把问题定位到路线深度、接触姿态与相机视野之间的冲突，而非只看末端求解器。下面是有限证据，不是不可行性证明。','','## 实测深度代价','','新后盒在首top_push之前已向桌深处移动100.426mm，后袋68.862mm；父版分别99.977/68.698mm。首2mm深度变化在rear_push阶段（盒61步、袋60步），属于显式避障路线，不是最终joint重试意外推走。原plan采用物体包围盒绕行，明确不保证全臂、IK、动力学或视野；不能把包围盒不碰撞当整条动作可执行。','','## 静态姿态筛查','','12个真实后绕推动状态，各用实测姿态和腰置零两种初值，分别无视野约束/仅目标中心/双物体中心入画8px内边界。原URDF关节界、腰±.98保持，拟合当前虚拟接触参考位置、非工作掌和当前手局部up。筛查故意不施加单步slew，不是可直接执行动作；无全臂/路径/表面接触或遮挡保证。','', '|条件|约束|正常收敛状态|活动参考位置误差mm（逐状态最优正常收敛结果）|','|---|---|---:|---|']
for r in rows:lines.append('|'+r['episode']+'|'+r['visibility']+'|'+str(r['normal_converged_states'])+'|'+'/'.join(f"{x['active_reference_error_mm']:.3f}" for x in r['best'])+'|')
lines += ['', '木盒仅目标可见时残差约27.7–31.1mm；双物体约58.0–63.1mm，不能直接缩腰保持同一接触姿态。后袋初两状态目标可见残差0/1.708mm，后四状态21.6–31.2mm，说明不能把一条早期可行静态姿态当完整路线可行。部分候选关节变化超过1甚至3rad，不可跳到该姿态；求解成功不等于接触有效。非凸局部两初值未证明全局最优，更未证明原任务无解。', '', '首版只看双物体约束，已保留BOTH_ONLY_V1并扩展目标单独条件。无新增每帧必须两物体可见质量门，不把额外条件缩小/改写原目标。', '', '## 下一步', '', '先关闭正在运行的完整原8推2wait。后续停止把数值状态8当主要瓶颈，检查接触点/接触朝向与物体绕行路线的联合可达性；维持相机相对躯干原标定、首零位、指定手、非目标15mm、无助推及原h10要求。目标是多样摆放的共享RGB策略，不是可看见但无法触碰的姿态，也不是只有特权物体位置才能纠偏的专家。任何替代接触/路径须先看实际碰撞与连续性，再独立物理验证，不直接采用本筛查输出。', '', '原数据内参默认值与真实相机K有小差异，已用每条240实测camera pose/K核齐；paired转换及policy输入不使用K，不能归因为成绩下降。后续新采集应写真实K，历史冻结数据不改。所有失败整组仍禁止转换或训练。']
(w/'CAMERA_CONTACT_ROUTE_FINDING.md').write_text('\n'.join(lines)+'\n');print('written CAMERA_CONTACT_ROUTE_FINDING')
