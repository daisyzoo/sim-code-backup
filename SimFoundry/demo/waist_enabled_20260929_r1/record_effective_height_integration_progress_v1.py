"""Record actual integration evidence and exact live handles, not task success."""
from pathlib import Path
import datetime,hashlib,json,shutil
W=Path(__file__).resolve().parent;ROOT=W.parents[1];D=W/'front_effective_height_preparation_r1';P=W/'front_effective_height_physical_preparation_r2';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text());now=datetime.datetime.now(datetime.timezone.utc).isoformat()
def identity(pid):
 try:
  p=Path('/proc')/str(pid);s=(p/'stat').read_text().rsplit(')',1)[1].split();return dict(pid=pid,start=s[19],state=s[0],cmd=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode())
 except FileNotFoundError:return None
checks=['COLLECTOR_WIRING_CHECK.json','NATIVE_COMMAND_CHAIN_CHECK.json','INDEPENDENT_RECORD_CHECK_V1.json','AUDIT_FAMILY_IMPORT_CHECK.json','NATIVE_WAIT_ENABLED_CHECK_V2.json','NATIVE_WAIT_DISABLED_CHECK_V2.json'];sources={};summaries={}
for n in checks:
 p=D/n;r=read(p);assert r['passed'];summaries[n]=dict(passed=True,path=str(p),sha256=sha(p));sources[str(p)]=sha(p)
 for f,h in r['source_sha256'].items():assert sha(f)==h,f
front=D/'NATIVE_FRONT_DEFAULTOFF_CHECK.json';front_status=dict(report_present=front.exists(),process=identity(657442),source_and_observation_passed=True,transport_stream_passed=True,parent_execution_pending=not front.exists())
if front.exists():assert read(front)['passed'];sources[str(front)]=sha(front)
queue=read(P/'CONTINUATION_QUEUE_STATUS.json');qid=identity(queue['pid']);assert qid and qid['state']!='Z';sources[str(P/'CONTINUATION_QUEUE_STATUS.json')]=sha(P/'CONTINUATION_QUEUE_STATUS.json')
runs={}
for n,s in [('front_loaded_z_quarter_physical_r2','AUDIT_STATUS.json'),('front_box_trailing_physical_r2','AUDIT_STATUS.json'),('rear_early_edge_physical_r1','AUDIT_STATUS_V2.json')]:
 r=read(W/n/s);i=identity(r['pid']);assert i and i['state']!='Z';runs[n]=dict(audit_rows=len(r['rows']),failed_audit_rows=sum(x['returncode']!=0 for x in r['rows']),audit_status=r['status'],identity=i)
cleanup=read(W/'excluded_0902_image_cleanup_r1/RESULT.json');free=shutil.disk_usage(ROOT).free/2**30
review=dict(created_at_utc=now,previous_goal_turn_classification='progress',current_goal_turn_classification='progress',passed_checks=summaries,active_sources_enabled=97,active_sources_disabled=93,defaultoff_full1200=front_status,physical_plan=str(P/'PLAN.json'),expected_conditions=10,expected_audits=224,queue=queue,queue_identity=qid,original_quality_gates_unchanged=True,new_physics_started=(W/'front_effective_height_physical_r1/PROTOCOL.json').exists(),new_training_admissions=0,new_conversion=False,new_training=False,goal_complete=False,free_gib=free,storage_cleanup=cleanup,source_sha256=sources,remaining=['Finish native1200 parent execution; queue checks complete configuration and original preflight before any newphysics.','Complete matched8push2wait actual physics,224 audits and actual image review; compare only after parent full closure.','Only qualified complete paired train/val groups may be converted; sharedpolicy,h10,untouched layouts/multiple seeds and actualmodel images remain unproved.'],failures_preserved=['native wait V1 imported root helper due adapter sys.path changes; V2 restoresstage precedence and asserts actualmodule path','plan V1 inverse renaming collided; partial artifacts retained, planV2/R2 exact remap passed','launcher V1 generic remap touched semantic flag; V2 limits moduleprefix and inverse checks exact parent'])
with (W/'effective_height_candidate_v1/READINESS_REVIEW_V2.json').open('x') as f:json.dump(review,f,indent=2)
latest=read(W/'LATEST_ACTIVE_RUNS.json');latest.update(updated_at_utc=now,previous_goal_turn_classification='progress',current_goal_turn_classification='progress',scope='Effective-height isolated collector/audit integration passed nativewait enabled/disabled; full1200 parent execution live; matched10condition continuationqueue waiting; excluded0902imagesremoved; no newphysicalsuccess or training.',free_gib=free,free_storage_gib=free,training_admissions_added=0,new_training_or_conversion=False,training_ready=False,goal_complete=False,effective_height_candidate=review,next_steps=review['remaining'])
for n,row in runs.items():latest['runs'].setdefault(n,{}).update(row)
latest['latest_storage_cleanup']=dict(path=str(W/'excluded_0902_image_cleanup_r1/RESULT.json'),**cleanup)
p=W/'LATEST_ACTIVE_RUNS.json';tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(latest,indent=2,ensure_ascii=False));tmp.replace(p)
section=f'''## {now} 高度修复已接入隔离collector与完整审核家族；开关两种70帧等待通过，1200帧父执行复核实活

上一目标轮progress，本轮progress。新staged_front_effective_height_v1以quarter父为直接对照，仅新增明确默认关闭effective-quarter-height开关和4helper，原完整目标函数、2e-7高度容差、原240迭代与solver成功门不变。实际collector六CLI及7拒绝配置、左右真实priority→transport→finalguard→history共6检查、独立记录39篡改拒绝均通过；42审核适配保留原224库存，39实际import+3CLI AST通过。70帧原生等待开/关完整source→stream→ledger→parentexecution均通过，97/93活跃source、25/21负例拒绝；均为独立copy2临时副本，不是新物理，physical入口拒绝fixture。完整1200前盒默认关副本source/observation与transport stream已过，父执行仍在PID657442/start99328681实际计算；不能提前记全过。原始raw/动作/source未改。

准备front_effective_height_physical_preparation_r2完整8推1200+2wait70，原6命令的任务/组/seed/质量门保持，仅新输出目录及高度开关。5数值/图审/审核队列入口逆向逐字核原，数值路由10完整、1短程及5拒绝通过。持续队列PID{queue['pid']}已实查，等待同一1200测试自然结束，成功后自动完整configuration/preflight；GPU空闲、原>30GiB启动与25GiB剩余预算必须过，任何失败停止不重试。当前尚无新物理成功，不以队列启动作为完成。READINESS_REVIEW_V2为新准备状态。V1等待测试导入路径失败、V1计划逆向映射失败和V1launcher语义flag替换失败均保留；修的是测试/生成器新版本，未改冻结stage/旧审计。

按既有清理授权删除handoff明确禁止训练的0902旧JPG38678张，约0.971GiB分配空间；200JSON元数据保留，逐文件SHA与protocol/currentprocess依赖检查、结果存excluded_0902_image_cleanup_r1。目录明确标为不完整不得训练。当前free约{free:.3f}GiB仍含约750MiB正在使用的临时完整副本，退出后再由启动器实查，未放宽存储门。三旧审计仍实际运行，quarter {runs['front_loaded_z_quarter_physical_r2']['audit_rows']}/224零失败、trailing {runs['front_box_trailing_physical_r2']['audit_rows']}/224四失败、early {runs['rear_early_edge_physical_r1']['audit_rows']}/224两失败，原失败保留；6147三run冻结来源已核不变。本轮0新增训练准入/转换/训练；共享多样布局、类别位置解耦、非目标15mm、首11D零位后双臂腰、无助推/h10与独立多seed模型实图目标保持未完成。

'''
p=ROOT/'handoff.md';s=p.read_text();pos=s.index('## 2026-');p.write_text(s[:pos]+section+s[pos:]);print(json.dumps(dict(recorded=True,free_gib=free,front_test=front_status,queue=queue['status'])))
