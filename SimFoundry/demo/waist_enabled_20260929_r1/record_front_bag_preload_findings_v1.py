"""Record all-condition press evidence and a narrowly specified next experiment.
No candidate installed; no new rollout, data admission or training claimed.
"""
from pathlib import Path
import datetime,hashlib,json,shutil,subprocess
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];R=W/'front_effective_height_physical_r1';D=W/'front_bag_preload_findings_r1';D.mkdir(exist_ok=False)
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();now=datetime.datetime.now(datetime.timezone.utc).isoformat()
census_path=W/'front_press_entry_census_r1/RESULT.json';zero_path=W/'front_edge_zero_increment_probe_r1/RESULT.json';c=read(census_path);z=read(zero_path);assert c['passed'] and z['passed'] and c['conditions']==8
for r in [c,z]:
 for name,h in r['source_sha256'].items():assert sha(name)==h,name
all_entries=sum(r['push_bouts'] for r in c['summary']);below=sum(r['entries_below3N'] for r in c['summary']);assert all_entries==below==63
successful_entries=sum(r['push_bouts'] for r in c['summary'] if r['quality_passed']);assert successful_entries==36
comparisons=[];sources={str(p):sha(p) for p in [Path(__file__),census_path,zero_path]}
for e in c['episodes']:
 if 'nudge_mailer' not in e['episode']:continue
 ep=R/('case_'+e['episode'].split('_')[1])/e['episode'];fr=read(ep/'frontal_bypass.json')
 with np.load(ep/'trace.npz',allow_pickle=False) as f:y=f['mailer'][:,1].copy()
 increments=[float((y[b['end']]-y[b['start']])*1000) for b in e['bouts']];loads=[r['lasttick_vertical_n'] for r in e['observations'] if r['mode']=='top_push']
 comparisons.append(dict(episode=e['episode'],quality_passed=e['quality_passed'],progress_mm=e['progress_mm'],push_frames=e['top_push_frames'],push_lasttick_vertical_load_median_n=float(np.median(loads)),bout_y_progress_mm=increments,bout_y_progress_median_mm=float(np.median(increments)),top_cross_frames=sum(row['mode']=='top_cross' for row in fr['rows']),lost_contact_bouts=sum(b['exit_reason']=='lost_contact' for b in e['bouts'])))
 sources[str(ep/'trace.npz')]=sha(ep/'trace.npz');sources[str(ep/'frontal_bypass.json')]=sha(ep/'frontal_bypass.json')
view=R/'case_840023/layout_840023_nudge_mailer_to_bin/FRONT_EFFECTIVE_HEIGHT_R1_REVIEW.jpg';sources[str(view)]=sha(view)
visual=dict(actual_visual_review='completed_actual_view_existing_sheet_this_turn',sheet=str(view),sheet_sha256=sha(view),method='Existing JPEG bytes read through escalated exec because view_image sandbox failed; image displayed and directly inspected.',observations=['Frame0 shows wood box on image left and black bag on image right.','Waist/viewpoint moves substantially; bag is cropped at the lower image boundary in multiple later samples.','Eight RGB samples and four distant external views do not prove continuous physical force or all-frame object visibility.'],existing_review_binding_unchanged=True)
next_candidate=dict(status='specified_not_implemented',name='bounded_front_bag_load_acquisition_with_explicit_xy_anchor',selection='Front-route left-hand bag contact; retain original right-hand and non-front branches and test all eight matched pushes plus two waits.',mechanism='On fresh valid interior contact, bounded preload uses an explicit measured XY anchor rather than accumulating the prior drive waypoint; continue original pressure loop and geometric/tilt/lost-contact/terminal guards. Restore original COP/waypoint history coherently when leaving hold.',original_pressure_domain_preserved=dict(desired_n=5,min_bias_m=-.006,peak_guard='prior24tick >2*desired holds downward increment'),must_resolve_before_install=['Specify finite dwell and load-ready hysteresis without treating old observations as new rollout.','Verify actual emitted joint command and XY travel, not only Cartesian waypoint; preserve original9D objective/constraints or explicitly independently audit any changed target.','Keep actual history/pressure finalization/source and whole-body checks aligned; guard failure stops before emission.','Evaluate whether unchanged6mm bias domain can build traction while holding; timeout/failure is evidence, never force threshold relaxation.','Run full original8push2wait including currently successful controls; inspect actual ten episode images and all224 audits.'],unproven=True)
# Capture actual currently live work, not a lock/status file alone.
def proc(pid):
 p=Path('/proc')/str(pid)
 try:
  s=(p/'stat').read_text().rsplit(')',1)[1].split();return dict(pid=pid,live=s[0]!='Z',state=s[0],start=s[19],command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(),observed_at_utc=now)
 except FileNotFoundError:return dict(pid=pid,live=False,observed_at_utc=now)
P=W/'front_normal_physical_preparation_r3';queue=read(P/'PHYSICAL_QUEUE_STATUS.json');processes=[proc(queue['pid']),proc(queue['dependency_pid'])];a=read(R/'AUDIT_STATUS.json');processes.append(proc(a['pid']))
for pid in subprocess.run(['pgrep','-P',str(a['pid'])],capture_output=True,text=True).stdout.split():processes.append(proc(int(pid)))
physical_started=(W/'front_normal_physical_r1/PROTOCOL.json').exists()
out=dict(created_at_utc=now,previous_goal_turn_classification='progress',current_goal_turn_classification='progress',scope=__doc__,entry_census=dict(conditions=8,entries=63,entries_below3N=63,successful_task_entries_below3N=36,global3N_entry_rule_not_supported=True),bag_comparison=comparisons,zero_increment_probe=[{k:v for k,v in e.items() if k!='rows'} for e in z['episodes']],actual_visual=visual,next_candidate=next_candidate,current_queue_status=queue['status'],processes=processes,parent_audits=dict(status=a['status'],completed=len(a['rows']),failures=sum(bool(r['returncode']) for r in a['rows']),total=224),new_physics_started=physical_started,new_admissions=0,new_conversions=0,new_training=0,free_gib=shutil.disk_usage(W).free/1024**3,training_ready=False,goal_complete=False,source_sha256=sources)
(D/'FINDINGS_AND_NEXT_EXPERIMENT_V1.json').write_text(json.dumps(out,indent=2));p=W/'LATEST_ACTIVE_RUNS.json';latest=read(p);latest.update(updated_at_utc=now,previous_goal_turn_classification='progress',current_goal_turn_classification='progress',scope='All8 press-entry census and zero-increment edge probe narrow the next front-bag experiment; exact geometry/physical queue continues.',goal_complete=False,training_ready=False,new_training_or_conversion=False,training_admissions_added=0);latest['latest_front_bag_preload_findings']=out;observed={v['pid'] for v in processes};latest['processes']=[v for v in latest.get('processes',[]) if v.get('pid') not in observed]+processes;p.write_text(json.dumps(latest,indent=2))
entry=f'''## {now} 八推负载进入普查与边缘零增量反事实完成：不能全局提高进入阈值，也不能把零推进增量叫手停住

本轮progress，原几何PID852086及排队PID869664实际状态见front_bag_preload_findings_r1/FINDINGS_AND_NEXT_EXPERIMENT_V1；queue={queue['status']}，新物理PROTOCOL存在={physical_started}。原effective审计{len(a['rows'])}/224、{out['parent_audits']['failures']}失败，未重启。没有新入库/转换/训练。

**新增证据改变下一步选择：**front_press_entry_census_r1逐实际force packet独立复算全部8推top_press/top_push负载；63次进入push的filtered load均<3N，其中36次属于5条任务门通过的轨迹。因此不支持把3N简单作为全局进入阈值；原history也不能证明提高阈值后一定卡死或一定改善。失败前袋349pushframes/median末tick1.77393N/总72.4278mm，成功后袋340pushframes/median4.67868N/总337.2985mm，两者均6次lost_contact；另两袋成功median3.51429/4.36798N。失载次数和初次负载低都不能独立解释成败，持续实际牵引与每段推进效率更关键。前袋top_cross711帧，恢复成本保留。

front_edge_zero_increment_probe_r1逐值复现原318袋+321盒COP反馈命令；对原边缘<10mm上下文，仅去掉新增drive、保留真实历史/前馈/横向修正。前袋44/44仍有沿推进方向的waypoint前导1.98033–7.83828mm（中位5.91084）；前盒136帧中102仍正前导。**这是原状态下代数反事实，不是新物理；当前helper不允许零drive，本轮没有改bounds。** 因此下一项候选明确为有限时长的前袋加载保持，使用实测XY锚处理累计前导，同时保持原5N/−6mm压力域、峰值/倾斜/避障/失载/terminal保护；不能仅取消增量。该候选目前只有明确规格，尚未实现/安装或证明可达，必须核真实最终关节命令与history，再完整8推2wait验证；不夹入已排队front-normal版本。

本轮实际重新查看旧前袋8RGB+4外视复核图（默认view_image沙箱故障，读取原JPEG并真实显示）：起始黑袋在图像右、木盒在左；腰运动改变视角，后段多帧袋子下缘裁切，外视太远不能替代接触力核验。原ACTUAL_REVIEW_BINDING未改，视野风险保持，不宣称完整可见。

完整目标仍为多样类别位置解耦共享RGB+指令策略、首零11之后双臂腰、非目标全过程15mm、无助推/h10；合格整组→共享训练→独立布局多seed真实模型画面均未完成。当前父5/8、0合格组的坏结果保留，后台检查/队列继续。

'''
h=ROOT/'handoff.md';text=h.read_text();at=text.index('\n---\n\n')+len('\n---\n\n');h.write_text(text[:at]+entry+text[at:]);print(json.dumps(dict(report=str(D/'FINDINGS_AND_NEXT_EXPERIMENT_V1.json'),queue=queue['status'],physics_started=physical_started,parent_audits=out['parent_audits']),indent=2))
