"""Record bounded real progress without promoting diagnostics to model success."""
from pathlib import Path
import json,hashlib,datetime,shutil
W=Path(__file__).resolve().parent;ROOT=W.parents[1];Q=W/'front_loaded_z_quarter_physical_r2';R=W/'front_contact_window_physical_r1';now=datetime.datetime.now(datetime.timezone.utc).isoformat();read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def identity(pid):
 p=Path('/proc')/str(pid)
 try:
  st=(p/'stat').read_text().rsplit(')',1)[1].split();argv=[x.decode(errors='replace') for x in (p/'cmdline').read_bytes().split(b'\0') if x];return dict(pid=pid,start_ticks=st[19],state=st[0],argv=argv,live=st[0]!='Z')
 except (FileNotFoundError,ProcessLookupError):return dict(pid=pid,live=False)
proof_paths=[Q/n for n in ['QUARTER_TRANSPORT_HEIGHT_CONTRACT_DIAGNOSIS_V1.json','EFFECTIVE_LOADED_CONTACT_TASK_CHECK_V2.json','EFFECTIVE_HEIGHT_SAVED_PROPOSALS_V1.json','EFFECTIVE_HEIGHT_SOLVER_REPLAY_V1.json','EFFECTIVE_HEIGHT_RUNTIME_CHECK_V1.json']]+[W/'current_front_transport_profile_r1/RESULT.json',W/'window_native_camera_probe_r2/RESULT.json',W/'front_corridor_lateral_physical_r1/RESULT.json']
for p in proof_paths:
 d=read(p)
 for source,h in d.get('source_sha256',{}).items():assert sha(source)==h,source
assert read(proof_paths[0])['totals']['contradictory_height_requirements']==628
assert read(proof_paths[1])['passed'] and read(proof_paths[2])['certificates_passed']==14 and read(proof_paths[3])['passed'] and read(proof_paths[4])['enabled_applied_count']==2
# Bind terminal partial original window audit; incomplete full trial remains rejected.
a=read(R/'AUDIT_STATUS.json');assert a['status']=='incomplete' and len(a['rows'])==54 and len(a['completed_episodes'])==2 and not identity(a['pid'])['live'];cache={}
def cached_hash(p):
 p=Path(p)
 if str(p) not in cache:cache[str(p)]=sha(p)
 return cache[str(p)]
for row in a['rows']:
 assert row['returncode']==0 and row['report_passed']
 ep=next(R.glob('case_*/'+row['episode']))
 assert cached_hash(ep/'raw.npz')==row['raw_sha256'];assert cached_hash(ep/row['report'])==row['report_sha256'];assert cached_hash(ep/(row['script']+'.log'))==row['log_sha256'];assert cached_hash(W/row['script'])==row['auditor_sha256']
partial=dict(created_at_utc=now,status='terminal_incomplete_trial',completed_conditions=2,planned_conditions=10,completed_episode_audits=54,failed_completed_episode_audits=0,full_required_audits=234,unexecuted_or_incomplete_conditions=8,qualified_complete_groups=0,training_ready=False,original_native_crash_preserved=True,source_sha256={**cache,str(R/'AUDIT_STATUS.json'):sha(R/'AUDIT_STATUS.json'),str(R/'STATUS.json'):sha(R/'STATUS.json')})
with (R/'PARTIAL_CLOSURE_V1.json').open('x') as f:json.dump(partial,f,indent=2)
D=W/'effective_height_candidate_v1';D.mkdir(exist_ok=False)
readiness=dict(created_at_utc=now,status='uninstalled_runtime_checked_collector_and_full_stream_binding_pending',direct_parent=str(Q),diagnosed_conflicting_contexts=628,attempted_proposals_rejected_by_height_conflict=297,iteration_limit_proposals_also_rejected=13,independent_effective_target_bindings=628,negative_cases_rejected=15,legacy_full_target_sides_checked=2,fixed_candidate_certificates_passed=14,fixed_candidate_certificates_total=14,original_solver_success_gate_preserved=True,actual_solver_replays=2,full_runtime_and_continuous_paths_passed=2,default_off_records_bit_identical=True,original_objective_unchanged=True,original_height_tolerance_m=2e-7,collector_integrated=False,new_physics=False,training_ready=False,source_sha256={str(p):sha(p) for p in proof_paths+[Path(__file__)]},limitations=['628contexts and14certificates use saved physical observations; these are not14successful trajectories.','Two certificate-passing iteration-limit proposals are still rejected by the original solver-success gate.','New target binds only the already verified quarter-loaded contact height; original full9 objective, motion/normal/table/clearance/quality gates remain unchanged.','Current source already has bounded support-path acceleration; old uninstalled status was stale.','Profiled85.7s at savedstep190 is dominated by5111constraint evaluations; correcting the height contract does not prove those solver iterations disappear.','Camera probe640RGBframes completed without crash but both320frame tasks failed; original full1200frame-profile audit rejected short settings, as preserved.','Original full windowR1 aborted2/10;54partial audits cannot replace234full audits.'])
with (D/'READINESS_REVIEW_V1.json').open('x') as f:json.dump(readiness,f,indent=2)
latest=read(W/'LATEST_ACTIVE_RUNS.json');frozen={};processes=[]
for name in ['front_corridor_lateral_physical_r1','front_box_trailing_physical_r2','front_loaded_z_quarter_physical_r2','rear_early_edge_physical_r1','front_contact_window_physical_r1']:
 run=W/name;p=read(run/'PROTOCOL.json');frozen.update(p['frozen_files_sha256']);st=read(run/'STATUS.json');aud=read(run/('AUDIT_STATUS_V2.json' if name=='rear_early_edge_physical_r1' else 'AUDIT_STATUS.json'));rows=aud['rows'];latest['runs'][name]=dict(collection_status=st['status'],completed_conditions=st['completed_conditions'],actual_reviews=len(list(run.glob('case_*/layout_*/ACTUAL_REVIEW_BINDING.json'))),audit_status=aud['status'],audit_rows=len(rows),failed_audit_rows=sum(x.get('returncode',0)!=0 for x in rows),audit_expected=234 if name=='front_contact_window_physical_r1' else 224,closed=(run/'RESULT.json').exists(),training_ready=False)
 for pid in [p['producer_pid'],st.get('collector_pid'),aud.get('pid')]:
  if pid:processes.append(identity(pid))
frozen.update(read(W/'window_native_camera_probe_r2/PROTOCOL.json')['frozen_files_sha256']);mismatches=[p for p,h in frozen.items() if not Path(p).is_file() or sha(p)!=h];assert not mismatches,mismatches[:5]
latest.update(updated_at_utc=now,previous_goal_turn_classification='progress',current_goal_turn_classification='progress',scope='Camera probe closed0/2task passes; full lateral224audits closed6/8push; diagnosed628contradictory quarter/full height contracts; isolated effective-target runtime checked, no new physical success.',training_admissions_added=0,new_training_or_conversion=False,training_ready=False,goal_complete=False,free_gib=shutil.disk_usage(W).free/2**30,frozen_source_count=len(frozen),frozen_mismatches=mismatches,last_frozen_source_revalidation=now,latest_goal_live_process_observation=processes,effective_height_candidate=readiness,front_contact_window_camera_probe=read(W/'window_native_camera_probe_r2/RESULT.json'),front_contact_window_partial_closure=partial,lateral_complete_closure=read(W/'front_corridor_lateral_physical_r1/RESULT.json'),next_steps=['Prospectively integrate effective quarter contact target into a new isolated collector and source-bound independent audit family; defaultoff and original full-target cases must remain exact.','Validate full recorded streams and hostile metadata; only then repeat all original8push2wait at1200/70frames in a new complete physical run with original>30GiB launch reserve.','Prioritize confirmed target-contract wiring defect before claiming benefit from contact-window policy. Preserve windowR1nativecrash and incomplete234audit inventory.','Finish original trailing/quarter/early audit closures; trailing third failure is missing output from the known self-clearance audit, not an independently proven new physical collision.','Only fully qualified diverse paired train/validation groups may be admitted; conversion, shared RGB+instruction training, h10 untouched192push+3wait multiple seeds and actual model views remain required.'])
latest['joint_transport_performance_profile'].update(status='integrated_in_current_stage_verified_by_source',production_integrated=True,production_ready=False,integration_observed_source=str(W/'staged_front_contact_window_v2/joint_transport_paths.py'),integration_observed_source_sha256=sha(W/'staged_front_contact_window_v2/joint_transport_paths.py'),scope_note='Physical diagnostic stage integration only; not model deployment or training admission.')
(W/'LATEST_ACTIVE_RUNS.json').write_text(json.dumps(latest,indent=2,ensure_ascii=False))
section=f'''## {now} 找到quarter下压与后续双臂协调的高度合同冲突；628步受影响，隔离修复初验通过，尚无新物理成功

上一目标轮progress，本轮progress。完整扫描quarter父8推：前盒299、前袋329，共628个已应用quarter下压步骤，后续却要求同时保留parent高度并达到原full下压目标。按两个原2e-7m高度门的三角不等式，parent相对full误差>4e-7m，628步条件均相互矛盾。实际尝试297提案全部被loaded contact检查拒绝、0应用；其中13还达到240次solver迭代上限，不把这些失败自动清除。QUARTER_TRANSPORT_HEIGHT_CONTRACT_DIAGNOSIS_V1逐步保存证据。独立重跑前袋190步完整record与原完全一致；cProfile85.722秒，5111次constraints累计85.072秒，主要在几何和数值梯度。原9倍support-cache已经在当前stage集成，旧LATEST未接入状态过期，已纠正；本次高度修复不承诺消除solver迭代耗时。

新增未安装effective_loaded_contact_task_v1仅绑定已验证quarter effective height；保留原完整9维目标函数、2e-7高度门和全部质量门。628上下文通过、297历史提案按正确高度均过该单项；左右两原full任务默认行为核对通过、15篡改拒绝。检查V1错将已right的测试side设right，实际没改而失败；V2明确left后改right，helper未变，旧测试保留。新独立certificate固定14历史未执行提案全部通过（两条solver status9仍不准应用）；真实solver重跑左右各1条候选关节命令与原未执行提案完全一致。完整隔离runtime两条默认关闭record完全相同，开启后经原连续nominal/predicted路径均可应用；只是CPU重建，未发物理动作。effective_height_candidate_v1/READINESS_REVIEW_V1记录还需新隔离collector/全source+stream审核接线和原完整8推2wait物理，不能直接用旧失败数据训练。

相机probe_r2已自然退出，两条各320帧、640RGB完整，首11D state/action均0、非目标XY均0，实际各12帧sheet已看。盒推进71.734mm、袋15.277mm，均原目标区失败；进程code0但case STATUS是Quality gate failed，不能把code0当任务通过。没有复现原生崩溃，但根因/修复未证明。尝试原window全审计在320 vs1200源配置门拒绝，日志保留、未放宽；短程只作相机诊断。原windowR1 watcher已终止为incomplete，两已完成episode共54审核全过且报告/raw/source/log哈希实核，仍2/10且非234完整审核；PARTIAL_CLOSURE_V1明确0合格组。

lateral完整RESULT已关闭：8推6过、2wait过、224全审计过，两个交换组均3/4，仍拒绝训练，无分数改善。TRAILING_R2新增第3失败是下游读取此前失败self-clearance未生成报告，保留原失败链；不是已证明新增碰撞。旧trailing/quarter/early CPU审核继续，以LATEST实查身份为准。冻结{len(frozen)}来源不变；本轮无删除/新物理/准入/转换/训练。现有磁盘{latest['free_gib']:.3f}GiB，原完整实验>30GiB门保持。优先修明确高度接线问题，再判断窗口收益；完整共享多样摆放、物体+指令、非目标15mm、首零后双臂腰、无助推、h10独立布局多seed模型实图目标不变且未完成。

'''
h=ROOT/'handoff.md';text=h.read_text();h.write_text(text.replace('---\n\n','---\n\n'+section,1));print(json.dumps(dict(recorded_at_utc=now,frozen_files_verified=len(frozen),free_gib=latest['free_gib'],height_conflicts=628,physical_success_proven=False,training_ready=False)))
