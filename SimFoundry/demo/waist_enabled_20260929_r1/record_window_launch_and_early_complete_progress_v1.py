"""Record current, process-verified continuation with unchanged full goal."""
from pathlib import Path
import json,hashlib,datetime,shutil
W=Path(__file__).resolve().parent;ROOT=W.parents[1];D=W/'front_contact_window_preparation_r2';C=W/'front_contact_window_candidate_v1';P=W/'front_contact_window_physical_preparation_r1';R=W/'front_contact_window_physical_r1';E=W/'rear_early_edge_physical_r1';now=datetime.datetime.now(datetime.timezone.utc).isoformat();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text())
def identity(pid):
 p=Path('/proc')/str(pid)
 try:
  s=(p/'stat').read_text().rsplit(')',1)[1].split();args=(p/'cmdline').read_bytes().split(b'\0');return dict(pid=pid,start_ticks=s[19],state=s[0],argv=[x.decode(errors='replace') for x in args if x],live=s[0]!='Z')
 except (FileNotFoundError,ProcessLookupError):return dict(pid=pid,live=False)
proof_names=['OBSERVATION_STREAM_CHECK_V1.json','AUDIT_FAMILY_IMPORT_INVENTORY_CHECK_V2.json','NATIVE_WAIT_ENABLED_CHECK_V2.json','NATIVE_WAIT_DISABLED_CHECK_V2.json','NATIVE_FRONT_DEFAULTOFF_CHECK_V1.json','NATIVE_FRONT_ENABLED_CHECK_V1.json'];proofs={}
for name in proof_names:
 p=D/name;d=read(p);assert d['passed'];proofs[str(p)]=sha(p)
for p in [P/'PLAN.json',P/'CONFIGURATION_CHECK.json',P/'LAUNCH_PREFLIGHT.json',P/'LAUNCH.json',E/'NUMERIC_VISUAL_SUMMARY.json',E/'COMPLETE_NUMERIC_VISUAL_COMPARISON_PENDING_AUDITS.json',E/'case_840023/layout_840023_push_box_to_bin/EARLY_EDGE_902_INFEASIBILITY_V2.json',W/'finished_collection_archive_dedup_r1/RESULT.json',W/'retired_pool_failed_raw_cleanup_r1/RESULT.json']:proofs[str(p)]=sha(p)
launch=read(P/'LAUNCH.json');process=identity(launch['pid']);assert process['live'] and process['start_ticks']==launch['start_ticks'];state=read(R/'STATUS.json') if (R/'STATUS.json').exists() else dict(status='launcher_revalidating_configuration_before_collection',completed_conditions=0)
assert state['status']!='runtime_or_audit_failed',state
physical=bool(state.get('collector_pid') and identity(state['collector_pid'])['live'])
readiness=dict(created_at_utc=now,status='complete_integration_verified_matched_physical_started' if physical else 'complete_integration_verified_launcher_live_revalidating_preflight',candidate='front_window_native_v4.py',stage=str(W/'staged_front_contact_window_v2'),parent='staged_front_loaded_z_quarter_v1',independent_observation_native_updates=817,additional_observations=35,full_parent_fixtures_observations=2398,fake_old_bag_rejected_at_step=790,native_wait_enabled_and_disabled_frames=70,full_front_window_off_frames=1200,full_front_window_enabled_frames=1200,fixture_physical_arrays_unchanged=True,fixture_is_new_physics=False,original_audit_invocations=224,additional_window_audit_invocations=10,total_required_audit_invocations=234,configuration_passed=True,preflight_passed=True,launcher=launch,launcher_identity=process,physical_collection_started=physical,current_state=state,training_ready=False,model_goal_achieved=False,limitations=['817 native loaded updates use fixed historical future observations.','Enabled1200-frame box fixture has no added loss evidence; verifies complete interfaces and independent stream checks, not new controller physical success.','Original parent224 audits remain pending for final comparison.','Front-box completion may require a separate contact/transport correction; no relaxed task gates or selective condition removal.'],source_sha256=proofs)
with (C/'READINESS_REVIEW_V7.json').open('x') as f:json.dump(readiness,f,indent=2)
latest=read(W/'LATEST_ACTIVE_RUNS.json');latest.update(updated_at_utc=now,previous_goal_turn_classification='progress',current_goal_turn_classification='progress',scope='Completed early-edge10actual reviews:5/8push+2wait, no matched pass/fail change, bothgroups rejected. Window full integration passed; matched8push2wait launcher actually live.',training_admissions_added=0,new_training_or_conversion=False,training_ready=False,goal_complete=False,free_gib=shutil.disk_usage(W).free/2**30)
runs=['front_corridor_lateral_physical_r1','front_box_trailing_physical_r2','front_loaded_z_quarter_physical_r2','rear_early_edge_physical_r1','front_contact_window_physical_r1'];processes=[];frozen={}
for name in runs:
 run=W/name
 if not (run/'PROTOCOL.json').exists():continue
 proto=read(run/'PROTOCOL.json');frozen.update(proto['frozen_files_sha256']);st=read(run/'STATUS.json');a=run/('AUDIT_STATUS_V2.json' if name=='rear_early_edge_physical_r1' else 'AUDIT_STATUS.json');audit=read(a) if a.exists() else {};rows=audit.get('rows',[]);rv=run/'NUMERIC_VISUAL_SUMMARY.json';nv=read(rv) if rv.exists() else {};entry=dict(completed_conditions=st.get('completed_conditions'),collection_status=st['status'],actual_reviews=len(list(run.glob('case_*/layout_*/ACTUAL_REVIEW_BINDING.json'))),audit_rows=len(rows),audit_expected=234 if name=='front_contact_window_physical_r1' else 224,failed_audit_rows=sum(x.get('returncode',0)!=0 for x in rows),audit_status=audit.get('status','not_started'),closed=(run/'RESULT.json').exists(),training_ready=False)
 if nv:entry.update(push_passed=nv['push_passed'],wait_passed=nv['wait_passed'],qualified_groups=0)
 latest['runs'][name]=entry
 for pid in [proto['producer_pid'],st.get('collector_pid'),audit.get('pid')]:
  if pid:processes.append(identity(pid))
 for n in ['NUMERIC_LAUNCH.json','CLOSURE_QUEUE_STATUS.json']:
  if (run/n).exists():
   p=read(run/n).get('pid')
   if p:processes.append(identity(p))
mismatches=[p for p,h in frozen.items() if not Path(p).is_file() or sha(p)!=h];assert not mismatches,mismatches[:5]
latest.update(frozen_source_count=len(frozen),frozen_mismatches=mismatches,last_frozen_source_revalidation=now,latest_goal_live_process_observation=processes,front_contact_window_candidate=readiness,rear_early_edge_current_run=latest['runs']['rear_early_edge_physical_r1'],rear_early_edge_complete_comparison=read(E/'COMPLETE_NUMERIC_VISUAL_COMPARISON_PENDING_AUDITS.json'),latest_storage_cleanup=dict(source_archive_dedup=read(W/'finished_collection_archive_dedup_r1/RESULT.json'),retired_failed_raw=read(W/'retired_pool_failed_raw_cleanup_r1/RESULT.json')),next_steps=['Observe exact new window producer/collector/audit/numeric handles; fix only new-version defects, never repeat failed physics selectively.','Complete all8push2wait and234audits with actual image review; compare every condition against quarter parent after original224closure.','Retain early2failed audits and trailing_r2step667ambiguous-axis failure; independent902certificate is not an official audit pass.','Only complete qualified multi-layout train+validation paired groups may convert/train; untouched192push+3wait,multiple seeds,h10 and actual model visual proof still required.'])
(W/'LATEST_ACTIVE_RUNS.json').write_text(json.dumps(latest,indent=2,ensure_ascii=False))
text=f'''## {now} 提前避边完整5/8推+2等待、无逐条成败改善；窗口完整开启/关闭验证通过，新10条件启动器实活

上一目标轮progress，本轮progress。early全部10采集与10实际画面复核完成：首交换组2/4、另一组3/4、两等待通过，均拒绝训练；与直接TRAILING_R2父5/8及逐条成败完全一致。840020前盒120.959233mm失败、2倾斜3失载，后袋337.412640mm通过、6失载；840021盒155.400410mm/袋159.995213mm通过，非目标全程XY均0。困难后盒原12.763mm非目标移动仍在原15mm以内，但任务失败。目标后段画外/裁切风险已实看并保留。完整数值图审对比COMPLETE_NUMERIC_VISUAL_COMPARISON_PENDING_AUDITS明确不是完整审核关闭。early收尾queue599186已启动，精确等533900原224及TRAILING_R2父完整RESULT。

提前避边审核两失败同源902：625eligible选择中仅1个candidate reason不一致，其余重建无error。运行时numerical_infeasible、独立LP no_joint_XY_direction，均不override且实际完整回退parent。EARLY_EDGE_902_INFEASIBILITY_V2用Fraction正权消元证两份严格约束矛盾；不能证明加入原1e−8容差后的系统仍不可行，未放宽阈值、未替换原失败audit。前盒未选中新分支，重复初态相同但微小动作/接触差异后放大，不能归因新策略；FRONT_BOX_REPEAT_DIVERGENCE_V1。TRAILING_R2第667步ambiguous_active_axis仍未解决。

窗口补齐完整24tick/实际支持点/失载生命周期独立审核；OBSERVATION_STREAM_CHECK_V1核817原生候选更新、35追加证据、7观测篡改拒绝；完整父前盒1199测试记录通过，伪装旧前袋在790必拒绝。42家族适配保留原224+每条件window1=234，39import+3CLI AST和完整调度库存通过。70wait窗口开/关、1200前袋默认关以及1200前盒窗口开启完整source→transport→ledger→execution→window均通过；这些是独立copy2副本及重建window记录，不是新物理。原始数组/动作和源文件hash不变，所有临时副本已退出清除；此前可写hardlink副本被自动审批拒绝，改用独立copy2后通过，未重试该危险方式。

新front_contact_window_physical_preparation_r1已完整6命令/10条件配置和预检通过，只有out目录和--front-contact-window改变。原8push1200、2wait70、原质量/首零11D/无助推/h10不变；234审核和原图审路由齐备。启动器初版静态复核修正source_binding字段为路径而非dict，修正前文件与派生报告保留；首次配置缺EULA环境在bootstrap失败，正确环境配置v2通过，未启动错误物理。producer{launch['pid']}/start{launch['start_ticks']}实活，当前{state['status']}，已完成{state.get('completed_conditions',0)}/10；以LATEST的实查进程为准，不能把启动称任务成功。READINESS_REVIEW_V7最新。

存储：旧/tmp多为已有硬链接，查明删除不会释放空间，因此保留。5个已完成采集run的只读源码归档2814项无损去重，原所有路径/hash保留，工作stage/数据/model未动，实际释放1.286GiB；CPU审核可继续读取，归档今后禁止原地写。按此前清理授权删除20260928旧池6条明确失败且无当前依赖raw，释放0.165GiB，失败质量报告、图片、哈希清单保留（原raw不再可重放）。启动前原>30GiB/后续25GiB门通过，没有改门。0新增正式训练准入、转换或训练；完整多样布局共享图像+指令、非目标15mm、首零后双臂腰、无助推及独立多seed/h10模型实图目标未完成。

'''
handoff=ROOT/'handoff.md';s=handoff.read_text();anchor='---\n\n';assert anchor in s;s=s.replace(anchor,anchor+text,1);handoff.write_text(s)
print(json.dumps(dict(recorded_at=now,window_state=state,physical_collector_live=physical,frozen_files_verified=len(frozen),early_actual_reviews=10,free_gib=latest['free_gib'],goal_complete=False)))
