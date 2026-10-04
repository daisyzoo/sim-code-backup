"""Record preserved window R1 failure, local-axis diagnosis and isolated camera probe."""
from pathlib import Path
import json,hashlib,datetime,shutil
W=Path(__file__).resolve().parent; ROOT=W.parents[1]; R=W/'front_contact_window_physical_r1'; D=W/'window_native_camera_probe_r2'; now=datetime.datetime.now(datetime.timezone.utc).isoformat(); read=lambda p:json.loads(Path(p).read_text()); sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def identity(pid):
 p=Path('/proc')/str(pid)
 try:
  st=(p/'stat').read_text().rsplit(')',1)[1].split();argv=[x.decode(errors='replace') for x in (p/'cmdline').read_bytes().split(b'\0') if x];return dict(pid=pid,start_ticks=st[19],state=st[0],argv=argv,live=st[0]!='Z')
 except (FileNotFoundError,ProcessLookupError):return dict(pid=pid,live=False)
crash=read(R/'NATIVE_CRASH_DIAGNOSIS_V2.json');assert read(R/'STATUS.json')['status']=='runtime_or_audit_failed';assert not identity(605996)['live'] and not identity(613652)['live']
for p,h in crash['source_sha256'].items():assert sha(p)==h,p
probe=read(D/'STATUS.json'); pp=read(D/'PROTOCOL.json'); proc=[identity(pp['producer_pid'])]
if probe.get('collector_pid'):proc.append(identity(probe['collector_pid']))
progress=read(D/'case_840023/progress.json') if (D/'case_840023/progress.json').exists() else None
branch=W/'front_box_trailing_physical_r2/case_840020/layout_840020_push_box_to_bin/LOADED_PARENT_NEAR_AXIS_BRANCH_DIAGNOSIS_V1.json'; bound=branch.with_name('LOADED_PARENT_LOCAL_AXIS_BOUND_CHECK_V1.json');b=read(branch);l=read(bound);assert b['original_certificate']['passed'] is False and l['passed'] is True and l['original_audits_still_failed'] is True
proofs=[R/'NATIVE_CRASH_DIAGNOSIS_V2.json',R/'FIRST_TWO_ACTUAL_REVIEWS_V1.json',branch,bound,D/'PROTOCOL.json',D/'EARLY_RUNTIME_OBSERVATIONS_V1.json',Path(__file__)]
readiness=dict(created_at_utc=now,status='physical_r1_aborted_native_camera_crash_no_candidate_benefit_proven',stage=str(W/'staged_front_contact_window_v2'),candidate='front_window_native_v4.py',completed_conditions=2,planned_conditions=10,incomplete_condition='layout_840023_push_box_to_bin',unexecuted_conditions=7,actual_reviews=2,first_two_window_branch_selected=False,qualified_groups=0,training_ready=False,model_goal_achieved=False,physical_retry_launched=False,isolated_camera_probe_status=probe,isolated_camera_probe_progress=progress,isolated_camera_probe_processes=proc,source_sha256={str(p):sha(p) for p in proofs},limitations=['Partial two-pass trial cannot establish improvement; both completed tasks did not select new front window.','Native crash at camera graph evaluation is observed; root cause and corrective fix are not proven.','320-frame probe is diagnostic only, changes horizon/environment timeout, and cannot replace complete1200/70frame matched10conditions.','Original failed stationarity audits unchanged; local-axis evidence is diagnostic and not an acceptance certificate.'])
with (W/'front_contact_window_candidate_v1/READINESS_REVIEW_V8.json').open('x') as f:json.dump(readiness,f,indent=2)
latest=read(W/'LATEST_ACTIVE_RUNS.json'); runs=['front_corridor_lateral_physical_r1','front_box_trailing_physical_r2','front_loaded_z_quarter_physical_r2','rear_early_edge_physical_r1','front_contact_window_physical_r1'];frozen={};processes=[]
for name in runs:
 run=W/name;protocol=read(run/'PROTOCOL.json');frozen.update(protocol['frozen_files_sha256']);st=read(run/'STATUS.json');a=read(run/('AUDIT_STATUS_V2.json' if name=='rear_early_edge_physical_r1' else 'AUDIT_STATUS.json'));rows=a['rows']
 entry=dict(collection_status=st['status'],completed_conditions=st['completed_conditions'],actual_reviews=len(list(run.glob('case_*/layout_*/ACTUAL_REVIEW_BINDING.json'))),audit_status=a['status'],audit_rows=len(rows),failed_audit_rows=sum(x.get('returncode',0)!=0 for x in rows),audit_expected=234 if name==runs[-1] else 224,closed=(run/'RESULT.json').exists(),training_ready=False)
 latest['runs'][name]=entry
 for pid in [protocol['producer_pid'],st.get('collector_pid'),a.get('pid')]:
  if pid:processes.append(identity(pid))
frozen.update(pp['frozen_files_sha256']);mismatch=[p for p,h in frozen.items() if not Path(p).is_file() or sha(p)!=h];assert not mismatch,mismatch[:5]
latest['window_camera_probe_runtime_observations']=read(D/'EARLY_RUNTIME_OBSERVATIONS_V1.json')
latest['latest_storage_planning_only']=dict(plan=str(W/'finished_collection_archive_dedup_r3/PLAN.json'),estimated_free_gib=read(W/'finished_collection_archive_dedup_r3/PLAN.json')['estimated_free_gib'],applied=False,reason='Only3.4MiB recoverable; no relinking or deletion. EarlierV2 planning failed on missing legacy summary before any mutation.')
latest.update(updated_at_utc=now,previous_goal_turn_classification='progress',current_goal_turn_classification='progress',scope='Preserved terminal native RTX failure; first2 actual reviews; local-axis diagnostic bounds; isolated camera repro, not model success.',training_admissions_added=0,new_training_or_conversion=False,training_ready=False,goal_complete=False,free_gib=shutil.disk_usage(W).free/2**30,frozen_source_count=len(frozen),frozen_mismatches=mismatch,last_frozen_source_revalidation=now,latest_goal_live_process_observation=processes+proc,front_contact_window_candidate=readiness,front_contact_window_native_crash=crash,front_contact_window_camera_probe=dict(status=probe,progress=progress,processes=proc),trailing_r2_near_axis_diagnosis=dict(branch_report=str(branch),local_bound_report=str(bound),only_one_near_branch_primal_feasible=True,original_audits_still_failed=True,local_dominance_margin_m=l['local_dominance']['guaranteed_axis_separation_m']),next_steps=['Finish isolated320-frame native-camera reproduction and bind results/images; no inference of a fix from a single non-crash.','Complete audits of retained R1 episodes; preserve full-trial incompleteness. Diagnose renderer before a new complete matched10condition1200/70frame run; retain original>30GiB full launch gate.','Near-axis local proof may inform a prospective independent certificate, but do not retroactively clear old failures or change physics guards.','Only complete qualified paired train/validation groups can convert/train; original diversified shared RGB+instruction goal with non-target15mm,zero-first11D,noassist,h10,untouched192push+3wait/multiple seeds and actual model visuals remains unachieved.'])
(W/'LATEST_ACTIVE_RUNS.json').write_text(json.dumps(latest,indent=2,ensure_ascii=False))
section=f'''## {now} 窗口物理R1相机原生崩溃退出；两条通过不证明新策略有效；近轴独立局部分析与短程复现

上一目标轮progress，本轮progress。front_contact_window_physical_r1 producer605996及collector613652已自然退出，原生日志exit139，STATUS runtime_or_audit_failed。10条件只有2完整、1中断、7未执行；2实际图审已绑定，但都未选中新窗口，0完整合格组。第3条840023后盒在相机SyntheticData graph.evaluate调用中崩溃，无raw/quality；progress最后90而外视pre_0110已保存，不能把90当准确崩溃步。实际看110外视，两物体在桌面、右手接近，图像不证明故障根因。终态日志、Python栈、最后图像及来源哈希存NATIVE_CRASH_EVIDENCE_V2/NATIVE_CRASH_DIAGNOSIS_V2；V1因终态已无collector_pid而KeyError、空目录保留，没有发kill或重跑原目录。inotify警告也在旧完成轨迹出现，无证据认定显存/磁盘耗尽或根因；未改环境、相机、原stage。

独立相机复现首版150帧被原>=320参数门拒绝(code2)，0物理，全部保留。新window_native_camera_probe_r2用原冻结collector、同case/seed/相机/物理和控制flags，只改新输出路径与320帧，真实parser预检；诊断状态{probe['status']}，见LATEST实查PID。后盒320帧已保存且没有复现原生崩溃；袋仍慢速运行，原quarter父185→190也耗129秒、当前154秒，不能凭慢认定死锁或新窗口独有。只读gdb采样被系统ptrace限制拒绝，没有取得调用栈、未改内存。原全10条件1200/70帧、>30GiB启动门保持；本独立单case保留25GiB+原单case1GiB预算。短程episode timeout随长度缩短，不是位级相同复现，也不是正式成功；即使不崩溃也不能称修好，不能训练或取代失败R1。

TRAILING_R2第667步独立两近轴分支：只有轴38满足原primal，轴138不满足；轴38三FD步长残差约1.242e-8低于原1e-6。保守几何局部界对2e-7rad关节盒和全部165竞争轴核得严格主导余量1.248e-6m，80角点/随机实现检查通过，宽半径证书拒绝；有限浮点界不是全局最优/连续整段碰撞证明。原2µm唯一性门与原失败审计未改，局部诊断不能自动清除失败。READINESS_REVIEW_V8为最新，原CPU审核继续，冻结{len(frozen)}来源实核不变。另筛五个已关闭实验的只读源码归档只可释放3.4MiB，未执行去重；旧失败raw只读盘点亦未删除。0新增准入、转换或训练；共享多样摆放分拣完整目标保持未完成。

'''
h=ROOT/'handoff.md';text=h.read_text();assert '---\n\n' in text;h.write_text(text.replace('---\n\n','---\n\n'+section,1))
print(json.dumps(dict(recorded_at_utc=now,probe_status=probe['status'],probe_progress=progress,frozen_files_verified=len(frozen),free_gib=latest['free_gib'],goal_complete=False)))
