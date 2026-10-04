"""Record actual reviewed first swap and current contact diagnosis, never admission."""
from pathlib import Path
import datetime,hashlib,json,shutil
W=Path(__file__).resolve().parent;ROOT=W.parents[1];R=W/'front_effective_height_physical_r1'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();now=datetime.datetime.now(datetime.timezone.utc).isoformat()
reviews=[(840023,'push_box_to_bin',[
 '实际查看8RGB4外视：0两物体可辨，171与342右手在木盒处，513目标右缘裁切，685仅边缘、856以后采样目标画外；非目标袋在初帧后多数采样不在视野内。外视可见持续作业，但抽帧不能证明连续无碰撞或完整动作质量。',
 '完整1200帧原任务/姿态独立复算失败，258.593895mm未达稳定目标区；非目标全程XY0、首11D零位、assist0。新transport0应用，不能直接归因高度修复；queryphase缺稳定终止段。']),
 (840023,'nudge_mailer_to_bin',[
 '实际查看8RGB4外视：袋与手在下方工作区域，袋多帧贴近或被下边缘裁切；木盒多帧可见，171与342局部裁切/遮挡。外视显示双臂与腰姿态变化。无法用抽帧证明持续接触，完整数值仍失败。',
 '完整1200帧原任务/姿态独立复算失败，袋推进72.427806mm、非目标木盒全程XY0、首11D零位、assist0；末态top_press，queryphase无稳定终止段。接触失载6次及1次路线换向，独立24子步/COP诊断另存。']),
 (841011,'wait_no_package',[
 '实际查看8RGB：空桌无包裹，双手保持画面两侧，采样未见明显主动摆动；本条无外视，不声称查看外视。',
 '完整70帧原等待独立数值门通过，上半身11动作全0，腰最大状态3.08739611654e-9rad，双掌spread均2.098291mm。首11D零位及无助推保持；原控制审计未完。'])]
for cid,task,obs in reviews:
 ep=R/f'case_{cid}/layout_{cid}_{task}';p=ep/'FRONT_EFFECTIVE_HEIGHT_R1_V1_STAGE_NUMERIC_REVIEW.json';n=read(p)
 assert sha(ep/'raw.npz')==n['raw_sha256'] and sha(ep/'FRONT_EFFECTIVE_HEIGHT_R1_REVIEW.jpg')==n['review_sheet_sha256']
 for name,h in n['external_source_sha256'].items():assert sha(ep.parent/('viewer_'+ep.name)/name)==h
 a={k:n[k] for k in ['raw_sha256','review_sheet_sha256','sampled_rgb_frames','sampled_viewer_frames','external_source_sha256']}
 a.update(episode=ep.name,numeric_review_sha256=sha(p),actual_visual_review='completed_actual_view_8RGB4external' if task!='wait_no_package' else 'completed_actual_view_8RGB_no_external',reviewed_at_utc=now,observations=obs,training_ready=False)
 with (ep/'ACTUAL_REVIEW_BINDING.json').open('x') as f:json.dump(a,f,indent=2)
reports=[R/n for n in ['RESPONSE_COMPARISON_FIRST_SWAP_V1.json','REAR_BOX_CONTACT_EFFICIENCY_AND_WRENCH_V1.json','REAR_BOX_MATERIAL_PROGRESS_V1.json','REAR_BOX_MATERIAL_PROGRESS_V2.json','FRONT_BAG_CONTACT_LOSS_DIAGNOSIS_V3.json','FRONT_BAG_TRACTION_COMPARISON_V1.json']]
for p in reports:
 for source,h in read(p)['source_sha256'].items():assert sha(source)==h,source
protocol=read(R/'PROTOCOL.json')
for source,h in protocol['frozen_files_sha256'].items():assert sha(source)==h,source
status=read(R/'STATUS.json');processes={}
for pid in [status['pid'],status.get('collector_pid'),664590,664591,464857,533900]:
 if not pid:continue
 p=Path('/proc')/str(pid)
 try:
  raw=(p/'stat').read_text().rsplit(')',1)[1].split();processes[str(pid)]=dict(state=raw[0],start=raw[19],cmdline=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode())
 except FileNotFoundError:processes[str(pid)]=dict(present=False)
progress_path=R/f"case_{status.get('layout_id')}/progress.json"
findings=dict(created_at_utc=now,scope=__doc__,goal_turn_classification='progress',first_swap_push_passed=2,first_swap_push_total=4,parent_first_swap_push_passed=3,wait_reviewed_passed=True,actual_reviews_completed=5,training_ready=False,new_admissions=0,new_conversions=0,new_training=0,
 good=['Front-bag original transport applies83->467 frames, progress38.500499->72.427806mm but remains original failure.','Front-bag push24tick loaded fraction.843269->.872135, non-target XY0.','Current bag advances to lateral_y with one actual route-direction recontact.'],
 bad=['First swap2/4 vs parent3/4; both hard swapped tasks fail; no whole group admission.','Front-bag6 actual loss exits,5 last valid COP at or beyond physical core edge; positive minimum drive1mm persists.','Front-bag hand L1 translational ratio>.98 at230/317 loaded lasttick samples, median normal1.847659N; old full-height also failed44.179078mm despite higher2.063999N median normal. More pressure alone is not established solution.','Rear-box contact occupancy and mean24 normal almost unchanged, progress per pushframe falls~20%; both transport0, causal attribution to new branch rejected.','Actual target cropping/off-camera risk remains; no model visual/generalization success demonstrated.'],
 diagnostic_repairs=['V1 front COP diagnostic incorrectly equated lateral feedback direction with governor route axis at1084; no original source fault established. V2 reconstructs real branch with unchanged2um assertion, but NumPy int64 JSON serialization failed. V3 casts boolean count and serializes fully before exclusive write; V1/V2 failures preserved.','Rear materialV2 includes object rotation; forward relative material mean.648260 vs.652812mm nearly equal, so larger slip alone not supported as repeat regression cause. Absolute servo command gaps are not promised one-frame movement.'],
 decision=['Keep current original10conditions/224audits and all failures; do not restart or mix new controller changes.','Complete remaining hard front-box group and actual views; compare mechanism use, force occupancy and original quality by category.','Prioritize sustained traction and interior contact with observed material motion; no repeat of failed fixed lead-cap or blind full-pressure restoration.','Any next candidate must retain specified-hand target manipulation, original physical materials, full body/obstacle constraints and zero initial11/h10/no-assist gates.'],
 source_sha256={str(p):sha(p) for p in [Path(__file__),*reports]},verified_frozen_source_count=len(protocol['frozen_files_sha256']),processes=processes,status=status,current_progress=read(progress_path) if progress_path.exists() else None,free_gib=shutil.disk_usage(W).free/1024**3,goal_complete=False)
with (R/'FIRST_SWAP_CONTACT_FINDINGS_V1.json').open('x') as f:json.dump(findings,f,indent=2)
latest=W/'LATEST_ACTIVE_RUNS.json';d=read(latest);d['effective_height_first_swap_findings']={k:v for k,v in findings.items() if k not in ['source_sha256','scope']};d['effective_height_first_swap_findings']['report_sha256']=sha(R/'FIRST_SWAP_CONTACT_FINDINGS_V1.json');d['latest_effective_height_progress']=dict(created_at_utc=now,status=status,processes=processes,progress=findings['current_progress']);d['last_goal_turn_classification']='progress';latest.write_text(json.dumps(d,indent=2))
p=ROOT/'handoff.md';s=p.read_text();marker='---\n';at=s.index(marker)+len(marker)
entry=f'''\n## {now} effective高度首交换组完整2/4退化；前袋推进改善仍失载，5条实际图审完成\n\n本目标轮progress。原collector671066自然完成1200前袋，producer继续原wait与840020；具体当前PID/启动身份/进度见LATEST和front_effective_height_physical_r1/FIRST_SWAP_CONTACT_FINDINGS_V1。没有重启覆盖失败，没有更改运行stage，全部{{findings['verified_frozen_source_count']}}冻结来源逐hash核验。\n\n**好结果有限：**前袋840023新transport实际83→467应用、155→3接触primal拒绝，推进38.500499→72.427806mm；24子步有载占比84.3269%→87.2135%，非目标木盒XY0；实际进入lateral_y。**差结果必须突出：**仍原门失败，6失载+1路线换向；6次失载的最后有效COP中5次位于/超出物理core边缘，原最小1mm正向drive仍在。首交换组原3/4→新2/4，后盒258.593895mm失败且新分支0应用，不直接归因修复。8推2wait全run尚未齐，不能扩采或准入。\n\n真实看完新后盒/前袋各8RGB4外视与70wait的8RGB，已存ACTUAL_REVIEW_BINDING；累计5条实际图审。后盒513/685边缘裁切、856以后目标画外，前袋多帧下缘裁切，视野风险保留。等待独立原门通过、11动作全0；前两条困难推独立复算均失败，不能用图像抽帧否定原门。\n\n新增接触证据：后盒24tick有载99.776%→98.820%、均载约5N，单位pushframe推进.554→.444mm；修正历史沿用退出reason，父6倾斜+1正常释放，新1失载+7倾斜+1未完成。材料V2同时推进手/物体同一材料点并含物体旋转，相对沿路线位移均值.648260/.652812mm接近，不能归为更大滑移；绝对servo目标差不是下一帧应完成位移。\n\nFRONT_BAG_TRACTION_COMPARISON_V1基于冻结实际friction/frame：手mu1、桌mu.55，新317有载lasttick中230个手切向L1利用率>.98，中位normal1.847659N；老full-height中位2.063999N也仅44.179078mm失败。末tick不是持续摩擦/净冲量证明，不修改物理材质、不盲目恢复full压力、不恢复已否定固定lead-cap。后续重点持续内部接触与实际牵引，等当前困难前盒完成后选单项候选。\n\n前袋COP诊断V1在1084误把feedback近Y方向当governor严格Y轴而失败；V2重算原分支通过全部2um断言，但numpy整数写JSON失败；V3修计数类型/写前完整序列化通过，两失败保留、原控制/门没改。仍0新增准入/转换/训练；完整多样布局共享策略、非目标15mm、首零后双臂腰、无助推/h10、独立布局多seed模型实图目标未完成。\n'''.replace("{findings['verified_frozen_source_count']}",str(findings['verified_frozen_source_count']))
p.write_text(s[:at]+entry+s[at:]);print(json.dumps({k:findings[k] for k in ['created_at_utc','verified_frozen_source_count','actual_reviews_completed','status','free_gib']}))
