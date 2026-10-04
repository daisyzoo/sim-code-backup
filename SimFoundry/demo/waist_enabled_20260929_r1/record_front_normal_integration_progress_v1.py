"""Authoritative checkpoint of completed evidence and actually live remaining jobs."""
from pathlib import Path
import datetime,hashlib,json,shutil,subprocess
W=Path(__file__).resolve().parent;ROOT=W.parents[1];D=W/'front_normal_integration_progress_r1';D.mkdir(exist_ok=False)
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();now=datetime.datetime.now(datetime.timezone.utc).isoformat()
report_paths=[W/n/'RESULT.json' for n in ['front_normal_observation_binding_checks_r2','front_normal_observation_wrappers_r1','front_normal_command_records_r1','front_normal_native_files_r1','front_normal_native_stream_r4']]
for p in report_paths:assert read(p)['passed'] is True
stale=W/'front_normal_native_files_r1/STALE_HISTORY_REJECTION_PROOF_V1.json';assert read(stale)['passed']
early=W/'rear_early_edge_physical_r1/CLOSED_ORIGINAL_AUDITS_AND_TASK_DECISION_V1.json';closed=read(early);assert closed['qualified_groups']==0
sources={str(p):sha(p) for p in [*report_paths,stale,early,Path(__file__),W/'front_normal_native_stream_r3/RESULT.json',W/'front_normal_observation_binding_checks_r1/RESULT.json']}
processes=[]
def proc(pid,role):
 p=Path(f'/proc/{pid}');live=p.exists() and p.joinpath('stat').read_text().split(') ')[1].split()[0]!='Z';r=dict(pid=pid,role=role,live=live,observed_at_utc=now)
 if live:r['command']=p.joinpath('cmdline').read_bytes().replace(b'\0',b' ').decode()
 processes.append(r);return live
live_runs={}
for run,file in [('rear_early_edge_physical_r1','AUDIT_STATUS_V2.json'),('front_effective_height_physical_r1','AUDIT_STATUS.json')]:
 a=read(W/run/file);alive=proc(a['pid'],run+'_original_auditor');live_runs[run]=dict(status=a['status'],audits_completed=len(a['rows']),audits_total=224,audit_failures=sum(bool(r['returncode']) for r in a['rows']),watcher_pid=a['pid'],watcher_live=alive,current_auditor=a.get('current_auditor'),training_ready=False)
 if alive:
  children=subprocess.run(['pgrep','-P',str(a['pid'])],text=True,capture_output=True).stdout.split()
  for pid in children:proc(int(pid),run+'_current_audit_child')
stream_dir=W/'front_normal_command_stream_r1';stream_done=(stream_dir/'RESULT.json').exists()
if stream_done:
 stream=read(stream_dir/'RESULT.json');assert stream['passed'];sources[str(stream_dir/'RESULT.json')]=sha(stream_dir/'RESULT.json');stream_state=dict(status='complete',passed=True,report=str(stream_dir/'RESULT.json'))
else:
 assert proc(834290,'front_normal_command_stream_v1');status=read(stream_dir/'STATUS.json');stream_state=dict(status='running',pid=834290,tool_session_id=3566,completed_branches=len(status['episodes']),log='/tmp/front_normal_command_stream_r1.log',result=str(stream_dir/'RESULT.json'))
free=shutil.disk_usage(W).free/1024**3
out=dict(created_at_utc=now,previous_goal_turn_classification='progress',current_goal_turn_classification='progress',source_observation=dict(positive_checks=20,tamper_rejections=9,prior_missing_duplicate_coord_hole_fixed=True,source_contact_file_branches=4),independent_command_record=dict(original_contexts=9740,corrections=32,holds_then_recovery=2,tamper_rejections=12,recursive_new_physics=False),native_v3=dict(original_frames=9740,off_on_calls=19480,applied=34,recovery_commits=2,failure_stops_before_history=2,pressure_finalization_verified=True,test_harness_r3_failure_preserved=True,test_harness_r4_uses_real_TracedPeakLoadControl=True),file_entry=dict(defaultoff_rear_frames=1200,enabled_wait_frames=70,ledger_checked=True,physical_entry_rejects_fixtures=True,stale_candidate_history_rejected_at_step=529,rejection_source_proven=True),continuous_command_audit=stream_state,live_runs=live_runs,processes=processes,free_gib=free,physical_launch_original_min_free_gib=30,physical_launch_ready=False,source_sha256=sources,training_admissions_added=0,new_training_or_conversion=False,training_ready=False,goal_complete=False,remaining=['Complete combined command-stream audit; preserve default-off results and reject fixed-original history after the first changed command.','Wire original control/self-clearance/phase consumers to final-normal ledger without replacing actual raw history or skipping parent certificates; pressure stream consumer already has dedicated recovery transition checks.','Prepare sufficient disk headroom without deleting running inputs or failure evidence; retain original >30GiB physical launch gate.','Fresh full eight-push/two-wait physics with actual visuals; front-box normal correction does not solve front-bag sustained contact.','Only admit complete category-swap groups, then convert/train shared RGB+instruction policy and validate untouched layouts, multiple seeds and actual h10 visuals.'])
(D/'READINESS_PROGRESS_V1.json').write_text(json.dumps(out,indent=2))
p=W/'LATEST_ACTIVE_RUNS.json';d=read(p);d.update(updated_at_utc=now,previous_goal_turn_classification='progress',current_goal_turn_classification='progress',scope='Normal v3 source/observation and final-command integration; native19480 calls passed, combined recursive history audit pending unless explicit report complete. Old early trial closed224 audits with4 failures,5/8push,0groups. No new physics/training.',free_gib=free,training_admissions_added=0,new_training_or_conversion=False,training_ready=False,goal_complete=False)
d['latest_front_normal_integration']=out;d['latest_rear_early_closed_audits']=dict(report=str(early),audit_invocations=224,audit_failures=4,root_failure_families=2,qualified_groups=0,watcher_live=False)
for key,value in live_runs.items():d.setdefault('runs',{}).setdefault(key,{}).update(value)
old=d.get('processes',[]);observed={r['pid'] for r in processes};d['processes']=[r for r in old if r.get('pid') not in observed]+processes
p.write_text(json.dumps(d,indent=2))
entry=f'''## {now} 新最终动作历史审核接线与v3原生19480次验证；旧early正式关闭224项仍4失败/0合格组

本轮progress。front_normal_stage_source_binding_v3补上coordination缺失/重复漏洞（旧r1两漏检失败保留）；observation r2共10条件×开关20正例与9篡改拒绝，四个真实文件source/contact wrapper分支通过，均诊断quality=False。front_normal_command_records_r1独立核全部9740固定原上下文：32纠偏+2保持后原恢复，12篡改拒绝；不能把固定原历史逐帧通过当成新闭环轨迹。

新增audit_front_normal_command_stream_v1把已验证的运输中间命令与最终normal命令分开：父证书消费明确记录的未执行腰角，所有证书/路径/最终门都基于同一个实际前动作；只有全部通过才更新history。audit_front_normal_native_stream_v1及front_normal_command_ledger_v1保留raw最终动作，只向父数学审核提供已验证中间命令。front_normal_native_files_r1默认关后盒1200帧/开启wait70帧文件入口和只读ledger过；诊断标记不能走物理入口。候选新命令拼接旧轨迹，在529帧被源绑定previous_command拒绝；STALE_HISTORY_REJECTION_PROOF_V1独立核实确实是该断言，不是无关失败。完整stream当前状态：{json.dumps(stream_state,ensure_ascii=False)}。若仍运行，继续同一session/PID，不因长计算无新输出重启。

v3采集器真实AST纠偏→finalguard→pressure recovery commit→history，全10条件9740×开关19480次通过，34应用/2恢复，两个异常分支在历史更新前停。native_r3测试夹具误用无updates的旧ContactLoadControl而失败，原失败保留；native_r4采用生产TracedPeakLoadControl通过。这是固定原观测/预备状态的原生接线检查；真实状态重建仍以prefix_r3/r4为证，不称新物理成功。

**坏结果正式关闭：**rear_early原224/224审计完成、4失败，watcher533900自然退出并核/proc；新增第4失败是840020黑袋self-clearance未生成报告造成pose审核FileNotFoundError。两根因仍为840023盒step902早期分支reason不符和840020袋step655原stationarity超1e−6。原实际5/8push、2/2wait、10实图，配对组2/4与3/4，0合格组；CLOSED_ORIGINAL_AUDITS_AND_TASK_DECISION_V1保留日志/raw哈希，不绕过失败。

当前free={free:.2f}GiB，原>30GiB物理门不降；effective旧审核真实watcher/子进程仍核活，详见front_normal_integration_progress_r1/READINESS_PROGRESS_V1与LATEST。本轮新物理/准入/转换/训练均0。下一步完成联合stream、原self-clearance/phase消费者接线及空间准备，再同条件物理+实际画面；前袋持续接触尚未解决。共享RGB+指令、多样类别位置解耦/完整交换组，首零后双臂腰、非目标全过程15mm、空桌稳、无助推/h10及独立布局多seed目标保持，未完成。

'''
h=ROOT/'handoff.md';s=h.read_text();assert '\n---\n\n' in s;at=s.index('\n---\n\n')+len('\n---\n\n');h.write_text(s[:at]+entry+s[at:])
print(json.dumps(dict(report=str(D/'READINESS_PROGRESS_V1.json'),stream=stream_state,free_gib=free,live_runs=live_runs),indent=2))
