"""Record exact pending dependency and authorized full trial queue; no false physics claims."""
from pathlib import Path
import datetime,hashlib,json,shutil,subprocess
W=Path(__file__).resolve().parent;ROOT=W.parents[1];P=W/'front_normal_physical_preparation_r3';D=W/'front_normal_launch_queue_progress_r1';D.mkdir(exist_ok=False)
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();now=datetime.datetime.now(datetime.timezone.utc).isoformat()
def identity(pid):
 p=Path('/proc')/str(pid)
 try:
  stat=(p/'stat').read_text().rsplit(')',1)[1].split();return dict(pid=pid,start=stat[19],state=stat[0],live=stat[0]!='Z',command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(),observed_at_utc=now)
 except FileNotFoundError:return dict(pid=pid,live=False,observed_at_utc=now)
pressure=read(W/'front_normal_pressure_files_r1/RESULT.json');assert pressure['passed'] and pressure['frames']==1200 and pressure['pressure_updates']==1199
imports=read(W/'front_normal_dispatch_imports_r1/RESULT.json');assert imports['passed']
plan=read(P/'PLAN_CHECK.json');assert plan['passed'] and plan['conditions']==10 and plan['push_conditions']==8 and plan['wait_conditions']==2
queue=read(P/'PHYSICAL_QUEUE_STATUS.json');qp=identity(queue['pid']);assert qp['live'] and 'queue_front_normal_physical_v1.py' in qp['command'];gp=identity(queue['dependency_pid'])
a=read(W/'front_effective_height_physical_r1/AUDIT_STATUS.json');ap=identity(a['pid']);children=[identity(int(pid)) for pid in subprocess.run(['pgrep','-P',str(a['pid'])],capture_output=True,text=True).stdout.split()]
geop=W/'front_normal_geometry_files_r2/RESULT.json';g=read(geop) if geop.exists() else None
if g is None:assert gp['live'] and 'check_front_normal_push_geometry_files_v1.py' in gp['command']
newrun=W/'front_normal_physical_r1';physical_started=(newrun/'PROTOCOL.json').exists()
paths=[W/'front_normal_pressure_files_r1/RESULT.json',W/'front_normal_dispatch_imports_r1/RESULT.json',W/'front_normal_audit_dispatch_r1/RESULT.json',P/'PLAN.json',P/'PLAN_CHECK.json',P/'RUNNER_PREPARATION.json',P/'CLOSURE_PREPARATION.json',P/'PHYSICAL_QUEUE_PROVENANCE.json',W/'check_front_normal_dispatch_imports_v1.py',Path(__file__)]
for report in paths[:2]:
 for name,h in read(report)['source_sha256'].items():assert sha(name)==h,name
out=dict(created_at_utc=now,previous_goal_turn_classification='progress',current_goal_turn_classification='progress',pressure_files=dict(passed=True,frames=1200,updates=1199,negative_rejected=pressure['negative_rejected'],new_recovery_physics_verified=False),dispatch=dict(conditions=10,total_checks=224,compiled_modules=len(imports['rows']),imported_modules=sum('import_returncode' in r for r in imports['rows']),cli_modules_require_real_episode=sum('import_skipped' in r for r in imports['rows']),actual_full_dispatch_executed=False),matched_plan=dict(parent='front_effective_height_physical_r1',push=8,wait=2,only_new_flag='--front-normal-nondegradation',original_gates_unchanged=True),geometry=dict(process=gp,result=str(geop),complete=g is not None),queue=dict(status=queue['status'],process=qp,status_file=str(P/'PHYSICAL_QUEUE_STATUS.json'),original_preflight_required=True,no_retry=True),parent_audit=dict(status=a['status'],count=len(a['rows']),failures=sum(bool(r['returncode']) for r in a['rows']),watcher=ap,children=children),processes=[qp,gp,ap,*children],free_gib=shutil.disk_usage(W).free/1024**3,physics_started=physical_started,training_admissions_added=0,new_conversion_or_training=False,training_ready=False,goal_complete=False,good='Pressure native consumer and complete224 dispatch/preparation retained; exact dependency process followed by original preflight and full8+2 run is genuinely queued.',bad='Direct parent still5/8 pushes and zero qualified groups. Front bag sustained contact unsolved. Static/source/fixture success does not establish candidate physical benefit.',remaining=['Follow queue and exact geometry PID; if failure, preserve and diagnose, never restart merely for silence.','Original full physics,224audits,actual ten episode images; parent audit closure and matched comparison.','Fix front-bag sustained contact separately; do not silently bundle rear numerical solver changes.','Complete admitted category-swapped groups before conversion/shared-policy training; original h10/multiseed/untouched layouts and actual model visuals.'],source_sha256={str(p):sha(p) for p in paths})
(D/'READINESS_PROGRESS_V1.json').write_text(json.dumps(out,indent=2))
p=W/'LATEST_ACTIVE_RUNS.json';latest=read(p);latest.update(updated_at_utc=now,previous_goal_turn_classification='progress',current_goal_turn_classification='progress',scope='Native pressure files passed; full normal8push2wait224audit run queued behind exact live full-body geometry check and original preflight.',free_gib=out['free_gib'],training_ready=False,goal_complete=False,new_training_or_conversion=False,training_admissions_added=0);latest['latest_front_normal_launch_queue']=out
observed={x['pid'] for x in out['processes']};latest['processes']=[r for r in latest.get('processes',[]) if r.get('pid') not in observed]+out['processes'];latest.setdefault('runs',{}).setdefault('front_effective_height_physical_r1',{}).update(status=a['status'],audits_completed=len(a['rows']),audit_failures=out['parent_audit']['failures']);p.write_text(json.dumps(latest,indent=2))
entry=f'''## {now} 新压力文件审核通过、完整224审计调度与8推2等待计划已准备；真实后台排队等待困难前盒全身检查

本目标轮progress：front_normal_pressure_files_r1原1200帧/1199压力更新通过，三类错误（fixture冒充物理、filtered压力篡改、陈旧phase raw哈希）被拒绝；这是默认关闭前盒原轨迹夹具，**不是新恢复的物理证明**。原front_normal_pressure_stream的独立数学、原24子步提取和阶段依赖保留。完整front_normal_audit_dispatch_r1保持原10条件224项及顺序；新dispatch imports核25模块语法、20个可安全导入模块实际加载成功，5个顶层CLI保留待真实episode调用，不能称224已实际运行。

front_normal_physical_preparation_r3严格匹配直接父effective的全部6命令/8推2等待，仅输出路径和--front-normal-nondegradation改变，101采集source、1200/70、全部原门。计划v1/v2因错误假设push_assist参数/赋值失败的原文件保留；v3依据原metadata assist_frames=0/push_assist=False与defaultoff AST来源核验。新producer、两watcher、完整/短episode reviewer和close_front_normal_trial1_physical_v1均已准备，收尾仍要求原224项、完整类别交换组、10实际看图和父审核关闭。

**真实后台**：queue PID{qp['pid']}存活，状态{queue['status']}；它只等待原geometry PID{gp['pid']}同一启动身份结束且RESULT通过，之后执行原producer完整preflight。当前geometry result存在={g is not None}，新物理PROTOCOL存在={physical_started}；不得把排队叫采集成功。首次真实configuration-only正确在缺geometry RESULT处拒绝，未生成CONFIGURATION_CHECK，也未降门。队列无重试；失败写PHYSICAL_QUEUE_STATUS与log，后续据证定位。几何原进程仍在完整body数学，不因输出安静重启。

原effective审核{len(a['rows'])}/224、{out['parent_audit']['failures']}失败，实际watcher及子进程见front_normal_launch_queue_progress_r1/READINESS_PROGRESS_V1。**坏结果不变：**父5/8推、2/2wait、0合格组；前袋持续内部接触未解决。新准入/转换/训练0，未把rear数值重试夹入本front-normal对照。当前空间{out['free_gib']:.2f}GiB，原>30GiB门保持。后续实际对照/全审核/实际画面→单独前袋持续接触→完整组准入/共享训练/独立未调参布局多seed h10真实模型验证；首零11、双臂腰、非目标全过程15mm、无助推均不变。

'''
h=ROOT/'handoff.md';text=h.read_text();at=text.index('\n---\n\n')+len('\n---\n\n');h.write_text(text[:at]+entry+text[at:]);print(json.dumps({k:out[k] for k in ['created_at_utc','queue','geometry','physics_started','free_gib']},indent=2))
