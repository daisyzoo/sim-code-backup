"""Bind three final review sheets actually viewed by the assistant this turn."""
from pathlib import Path
import json,datetime,hashlib
W=Path(__file__).resolve().parent;R=W/'rear_early_edge_physical_r1';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rows=[]
notes=[(840021,'push_box_to_bin','实际查看8RGB4外视：171盒在右边缘被裁切，342之后盒画外，非目标袋仍在画面；后段腰转动使视角变化。稀疏外视可见右臂伸出，但画外不能替代目标区数值判定。'),(840021,'nudge_mailer_to_bin','实际查看8RGB4外视：171左手在袋上方，342袋在左侧裁切，513仅左边缘残片，685后袋画外；非目标盒持续可见。保留模型目标视野风险，稀疏画面不能证明全程无碰撞。'),(841010,'wait_no_package','实际查看8RGB：0、9、19、29、39、49、59、69帧空桌和双掌姿态稳定，未见无指令漂移。等待没有外部视图样本。')]
for i,task,note in notes:
 ep=R/f'case_{i}'/f'layout_{i}_{task}';p=ep/'REAR_EARLY_EDGE_R1_V1_STAGE_NUMERIC_REVIEW.json';n=json.loads(p.read_text());ready=json.loads((ep/'READY_FOR_AUDIT.json').read_text());assert n['frames']==ready['executed_frames']==(70 if task=='wait_no_package' else 1200)
 assert sha(ep/'raw.npz')==n['raw_sha256'] and sha(ep/'REAR_EARLY_EDGE_R1_REVIEW.jpg')==n['review_sheet_sha256']
 for f,h in ready['source_sha256'].items():assert sha(Path(f))==h
 for f,h in n['external_source_sha256'].items():assert sha(ep.parent/('viewer_'+ep.name)/f)==h
 a={k:n[k] for k in ['raw_sha256','review_sheet_sha256','sampled_rgb_frames','sampled_viewer_frames','external_source_sha256']};a.update(episode=ep.name,numeric_review_sha256=sha(p),actual_visual_review='completed_actual_view_8RGB'+('4external' if task!='wait_no_package' else '_stable_wait'),reviewed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),observations=[note,'原任务姿态数值通过；仍待全控制审核，诊断数据不准入训练。'],training_ready=False)
 with (ep/'ACTUAL_REVIEW_BINDING.json').open('x') as f:json.dump(a,f,indent=2,ensure_ascii=False)
 row={k:n.get(k) for k in ['episode','frames','progress_mm','non_target_max_xy_mm','original_task_and_pose_passed']};row['binding_sha256']=sha(ep/'ACTUAL_REVIEW_BINDING.json');rows.append(row)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),rows=rows,actual_reviews_total=len(list(R.glob('case_*/layout_*/ACTUAL_REVIEW_BINDING.json'))),training_ready=False)
assert out['actual_reviews_total']==10
with (R/'FINAL_THREE_ACTUAL_REVIEWS_V1.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(out,indent=2))
