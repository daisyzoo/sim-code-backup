"""Checkpoint parent control integration and verified duplicate-cache cleanup."""
from pathlib import Path
import datetime,hashlib,json,shutil,subprocess
W=Path(__file__).resolve().parent;ROOT=W.parents[1];D=W/'front_normal_parent_pipeline_progress_r1';D.mkdir(exist_ok=False)
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();now=datetime.datetime.now(datetime.timezone.utc).isoformat()
reports={name:W/name/'RESULT.json' for name in ['front_normal_command_stream_r1','front_normal_parent_coordinate_r1','front_normal_parent_math_files_r1','front_normal_geometry_files_r1','front_normal_parent_math_preservation_r1']}
for p in reports.values():assert read(p)['passed'] is True
stream=read(reports['front_normal_command_stream_r1']);assert len(stream['results'])==20 and len(stream['negative'])==5
cleanup=W/'storage_duplicate_staging_20261005_r1/CLEANUP.json';c=read(cleanup);assert len(c['deleted_paths'])==7 and not c['model_or_training_data_deleted']
for p in c['deleted_paths']:assert not Path(p).exists()
for p in c['retained_models']:assert Path(p).is_file()
processes=[]
def proc(pid,role):
 p=Path(f'/proc/{pid}');live=p.exists() and p.joinpath('stat').read_text().split(') ')[1].split()[0]!='Z';r=dict(pid=pid,role=role,live=live,observed_at_utc=now)
 if live:r['command']=p.joinpath('cmdline').read_bytes().replace(b'\0',b' ').decode()
 processes.append(r);return live
for pid,role in [(834290,'completed_final_command_stream'),(844188,'completed_parent_math_files'),(851179,'completed_staging_byte_verification')]:assert not proc(pid,role)
geofile=W/'front_normal_geometry_files_r2/RESULT.json'
if geofile.exists():g=read(geofile);assert g['passed'];geom=dict(status='complete',passed=True,report=str(geofile));reports['front_normal_geometry_files_r2']=geofile
else:
 assert proc(852086,'front_normal_push_geometry_files_v1');geom=dict(status='running',pid=852086,tool_session_id=47225,log='/tmp/front_normal_geometry_files_r2.log',expected_report=str(geofile))
a=read(W/'front_effective_height_physical_r1/AUDIT_STATUS.json');alive=proc(a['pid'],'front_effective_height_original_auditor')
if alive:
 for pid in subprocess.run(['pgrep','-P',str(a['pid'])],text=True,capture_output=True).stdout.split():proc(int(pid),'front_effective_height_current_auditor_child')
effective=dict(status=a['status'],watcher_live=alive,watcher_pid=a['pid'],audits_completed=len(a['rows']),audits_total=224,audit_failures=sum(bool(r['returncode']) for r in a['rows']),current_auditor=a.get('current_auditor'))
free=shutil.disk_usage(W).free/1024**3
out=dict(created_at_utc=now,previous_goal_turn_classification='progress',current_goal_turn_classification='progress',combined_command_stream=dict(passed=True,defaultoff_frames=9740,enabled_checked_frames=9069,complete_unchanged_enabled_conditions=9,changed_front_box_prefix_frames=529,stale_history_rejected_at=529,negative_rejections=5,new_physical_rollout_verified=False),parent_coordinate=dict(frames=9740,coordinate_frames=9592,normal_changes=34,transport_changes=1015,negative_rejections=8,actual_history_untouched=True),parent_math_files=dict(passed=True,front_box_defaultoff_frames=1200,loaded_z_applied=265,wait_enabled_frames=70),body_geometry=dict(enabled_wait_frames=70,actual_gap_tamper_rejected=True,difficult_front_box=geom),unchanged_parent_mathematical_bodies=11,storage=dict(cleanup_report=str(cleanup),temporary_duplicates_removed=7,verified_byte_equal_and_sha256=True,observed_reclaimed_gib=c['observed_reclaimed_bytes']/1024**3,free_gib=free,retained_checkpoints_models_data=True,original_min_free_gib=30,space_gate_satisfied=free>30),effective_original_audit=effective,processes=processes,physical_launch_ready=False,training_admissions_added=0,new_training_or_conversion=False,training_ready=False,goal_complete=False,remaining=['Wait for same running full front-box pose/self-clearance fixture; do not restart on output silence.','Finish native pressure-file wrapper and remaining original phase/control audit dispatch for S3; preserve all original conditions and independent gate math.','Freeze/prove the full new producer/auditor command inventory, then launch fresh original eight-push/two-wait physical comparison with actual images; disk now passes original >30GiB threshold.','Front-bag sustained contact still unsolved: current actual seven bouts include six lost-contact exits and large relative sliding to core edge; do not attribute solely to box blockage or claim pressure increase proven.','Admit only complete paired groups, then data conversion/shared training/untouched-layout multi-seed h10 actual model validation.'])
out['source_sha256']={str(p):sha(p) for p in [*reports.values(),cleanup,W/'storage_duplicate_staging_20261005_r1/VERIFIED.json',Path(__file__)]}
(D/'READINESS_PROGRESS_V1.json').write_text(json.dumps(out,indent=2))
p=W/'LATEST_ACTIVE_RUNS.json';d=read(p);d.update(updated_at_utc=now,previous_goal_turn_classification='progress',current_goal_turn_classification='progress',scope='Normal candidate continuous-history audit completed; parent coordinate+hard front-box loaded math pass. New full push body fixture still requires its actual result. Verified upload-cache duplicates reclaimed48.72GiB; no new physics/training.',free_gib=free,training_admissions_added=0,new_training_or_conversion=False,training_ready=False,goal_complete=False)
d['latest_front_normal_parent_pipeline']=out;d['latest_front_normal_integration']['continuous_command_audit']=dict(status='complete',passed=True,report=str(reports['front_normal_command_stream_r1']))
d.setdefault('runs',{}).setdefault('front_effective_height_physical_r1',{}).update(effective)
observed={x['pid'] for x in processes};d['processes']=[r for r in d.get('processes',[]) if r.get('pid') not in observed]+processes
p.write_text(json.dumps(d,indent=2))
entry=f'''## {now} 连续历史审核完成、前盒完整父数学过；七份已核验上传副本回收48.72GiB，空间门已恢复

上一目标轮progress，本轮progress。front_normal_command_stream_r1完成20开关分支：默认关9740全帧；开启其余9条件完整，840020前盒在首次修正528通过后，529使用旧previous被准确拒绝，共9069已审核帧及5类历史/顺序反例拒绝。**这是固定原观测的9完整不变条件+1改变前缀，不能称新策略全轨迹过。** 原进程834290已终态退出。

新增front_normal_parent_coordinate_v1按normal→transport逆覆盖顺序只恢复明确记录的中间腰角，不改q/previous实际动作/其他任务字段。全9740上下文、9592coord、34normal/1015transport覆盖与8篡改拒绝；只读视图未改输入。front_normal_loaded_episode_inputs_v1、audit_front_normal_z_execution_v1、audit_front_normal_execution_v1及recovery wrapper使用新source/ledger/父坐标；front_normal_parent_math_files_r1困难前盒默认关完整1200帧/265下压及开启wait70实际文件入口通过，source fixtures明确False质量/非物理。新增initial/pose/stage_context/self_clearance消费者保留原数学和实际raw，只显式接运输中间输出到最终normal输出；front_normal_parent_math_preservation_r1核11核心函数AST保留。开启wait70全身真实runtime几何过，篡改post身体间距被原重算拒绝，物理入口拒绝fixture。**困难前盒完整pose+body新文件检查状态：{json.dumps(geom,ensure_ascii=False)}；尚未有该结果不能称完整几何接线已验证。** 当前固定记录中intersection与transport/normal覆盖无重叠；不把该范围检查外推所有未来状态。

**空间实清理：**11保留model未发现互相重复；W&B staging七份临时文件分别与保留模型各7473096344B全文件逐字节和SHA256完全一致，无打开句柄，删除前复核inode/mtime/size/nlink，保留文件stats逐项未变，只移除tmp63zmgmg5/tmpcpggrm0g/tmpx6b_8z6t/tmp7a_v18a8/tmpirh68m01/tmpssg4x3_j/tmpsglsu4fc。证据storage_duplicate_staging_20261005_r1/VERIFIED、CLEANUP、DELETE_JOURNAL；回收{c['observed_reclaimed_bytes']/1024**3:.4f}GiB，当前{free:.2f}GiB，原>30GiB门已满足。模型/checkpoint/训练和物理数据均未删，没有处理其余未知cache。

**坏结果保持：**旧early224项/4失败已关闭、5/8push/2wait/0组；effective仍5/8push/0组，原审核真实进程和{len(a['rows'])}/224、{sum(bool(r['returncode']) for r in a['rows'])}失败见LATEST。前袋本版7接触段有6次lost_contact、相对袋滑到core边缘，现有牵引报告显示另一物体接触力为0，不能仅归因盒遮挡，也不能凭低载荷就宣称加压有效。未新采集/准入/转换/训练。

下一步完成同一push geometry句柄、压力原生文件wrapper及剩余原phase/control调度→冻结完整新producer/auditor/原8推2wait物理计划→真正新闭环和实际画面。空间已恢复，不再沿用磁盘阻塞说法。前袋须单独持续接触对照，完整类别交换组/共享RGB+指令、首零后双臂腰、非目标全过程15mm、等待稳、无助推/h10与未调参布局多seed实际模型目标不变。详细证据front_normal_parent_pipeline_progress_r1/READINESS_PROGRESS_V1。

'''
h=ROOT/'handoff.md';s=h.read_text();at=s.index('\n---\n\n')+len('\n---\n\n');h.write_text(s[:at]+entry+s[at:]);print(json.dumps(dict(report=str(D/'READINESS_PROGRESS_V1.json'),free_gib=free,geometry=geom,effective=effective),indent=2))
