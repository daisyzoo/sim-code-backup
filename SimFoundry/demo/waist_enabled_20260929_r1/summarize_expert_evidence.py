"""Point-in-time expert evidence summary; never a training admission decision."""
from pathlib import Path
import json,datetime
r=Path(__file__).resolve().parent
names=['far_endpoint_pair_r1','depth_b_confirmation_r1','contact_load_pair_r1','frontal_bypass_smoke_r1','frontal_feedback_smoke_r1','frontal_follow_y_smoke_r1','frontal_recontact_smoke_r1','frontal_sweep_x_smoke_r1','frontal_tracked_sweep_smoke_r1','frontal_lead1_smoke_r1','frontal_load_recovery_smoke_r1','frontal_wide_load_smoke_r1','frontal_tip_side_smoke_r1','frontal_tip_extended_smoke_r1','frontal_box_quarter_turn_r1','frontal_nearer5cm_r1','frontal_contact_pad_r1','frontal_strict_descent_r1','frontal_offcenter_rear_r1','frontal_object_frame_rear_r1','frontal_press_clearance_r1','frontal_top_contact_r1','frontal_top_guarded_r1','frontal_top_drag_r1','frontal_top_drag_fast_r1','frontal_top_center_r1','frontal_top_load5_r1','frontal_top_load5_long_r1','frontal_visible_corner_r1','frontal_corner_compensated_r1','frontal_core_corner_r1','frontal_support_hysteresis_r1','frontal_forward25_r1','frontal_guarded_recovery_r1','frontal_hold_push_x_r1','frontal_cross_admittance_r1','frontal_forward40_r1','frontal_forward40_long_r1','frontal_hysteresis02_seed0_r1']
lines=['# 专家物理证据汇总','',f'更新时间UTC：{datetime.datetime.now(datetime.timezone.utc).isoformat()}','', '**以下都是开发阶段专家结果，不是模型成功率。全部 training_ready=false。** 单布局一次运行不能证明泛化或唯一因果，需完整类别交换组及独立重复验收。','', '| 实验 | 布局范围 | 帧预算 | 原数值+姿态通过 | 非目标最大XY位移 |', '|---|---|---:|---:|---:|']
for name in names:
 p=r/name/'RESULT.json'
 if not p.exists():continue
 j=json.loads(p.read_text());rows=j['rows'];passed=sum(x['quality']['passed'] and x['pose']['search_success'] for x in rows)
 maxother=max(x['quality']['metrics']['mailer_max_xy_m' if 'push_box' in x['episode'] else 'box_max_xy_m'] for x in rows)
 group='depth_a完整交换组' if name=='far_endpoint_pair_r1' else ('depth_b完整交换组' if name in ['depth_b_confirmation_r1','contact_load_pair_r1'] else '62000阻挡布局的两任务')
 if name=='frontal_box_quarter_turn_r1':group='62020盒旋转90度诊断'
 if name=='frontal_nearer5cm_r1':group='62022双物体移近5cm诊断'
 budget='/'.join(str(v) for v in sorted(set(x['quality'].get('frames',0) for x in rows)))
 lines.append(f'| [{name}]({name}/RESULT.json) | {group} | {budget} | {passed}/{len(rows)} | {maxother*100:.3f} cm |')
lines+=['','好结果：depth_a达到4/4；62000在960帧重复顶面接触诊断中原数值+姿态2/2且非目标0。','差结果：depth_b换位仍有翻倒；62000同策略320帧0/2，960帧虽通过但袋81/960、盒484/960帧目标完全画外，反复恢复冗长，仍不准入训练。长短预算不可混算。','', '没有用后推X位移替代指令方向进度，没有将几何接近替代接触力，也没有用一次通过替代完整训练及h10闭环。', '', '当前进程位置见RUNNING_PROCESS.json，须核实际PID和STATUS，不能仅凭本文认定仍运行。']
(r/'EXPERT_EVIDENCE_SUMMARY.md').write_text('\n'.join(lines)+'\n')
