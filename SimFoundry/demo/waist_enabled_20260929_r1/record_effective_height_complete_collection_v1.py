"""Close collection evidence only; leave original control audits and full goal open."""
from pathlib import Path
import collections,datetime,hashlib,json
W=Path(__file__).resolve().parent;R=W/'front_effective_height_physical_r1'
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
c=read(R/'RESPONSE_COMPARISON_10_V1.json');v=read(R/'NUMERIC_VISUAL_SUMMARY.json');diag=read(R/'FRONT_BOX_ROUTE_REGRESSION_V1.json');protocol=read(R/'PROTOCOL.json')
assert c['completed_conditions_compared']==v['actual_reviews']==10
assert v['push_passed']==5 and v['wait_passed']==2
for report in [c,v,diag]:
 for p,h in report['source_sha256'].items():assert sha(p)==h,p
for p,h in protocol['frozen_files_sha256'].items():assert sha(p)==h,p
groups={}
for group in sorted({x['group'] for x in c['rows']}):
 rows=[x for x in c['rows'] if x['group']==group];push=[x for x in rows if not x['wait']];wait=[x for x in rows if x['wait']]
 assert len(push)==4 and len(wait)==1
 groups[group]=dict(parent_push_passed=sum(x['parent']['saved_quality_passed'] for x in push),candidate_push_passed=sum(x['candidate']['saved_quality_passed'] for x in push),push_total=4,wait_passed=wait[0]['candidate']['saved_quality_passed'],failed_episodes=[x['candidate']['episode'] for x in push if not x['candidate']['saved_quality_passed']],admission='rejected_incomplete_task_group',training_ready=False)
rows=read(R/'AUDIT_STATUS.json')['rows'];fail=[{k:x.get(k) for k in ['episode','script','returncode','report_passed']} for x in rows if x['returncode']!=0 or x['report_passed'] is not True]
result=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,groups=groups,collection_complete=True,actual_visual_reviews=10,parent_push_passed=6,current_push_passed=5,push_total=8,wait_passed=2,wait_total=2,qualified_groups=0,new_admissions=0,new_conversions=0,new_training=0,control_audits_complete=len(rows)==224,audit_rows_at_record=len(rows),expected_audit_rows=224,audit_failures_at_record=fail,verified_frozen_sources=len(protocol['frozen_files_sha256']),decision='Do not expand or train this candidate. Keep full audits running; isolate numerical solver fix and sustained-contact/cross-track repair before any new full-condition physics.',front_box_findings={'parent_push_frames':diag['parent']['push_frames'],'current_push_frames':diag['current']['push_frames'],'parent_route_restart_count':sum(x['restarted'] for x in diag['parent']['events']),'current_route_restart_count':sum(x['restarted'] for x in diag['current']['events']),'late_recontact_nonpush_frames':sum(x['nonpush_frames_to_next_push'] for x in diag['current']['events'] if x['step']>=1000),'step1010':next(x for x in diag['current']['events'] if x['step']==1010)},limitations=['Matched unchanged-branch rear-box regression does not establish that effective-height branch caused it.','Observed front-box route switches obey original clearance thresholds. Do not suppress protective recontact or relax margins.','Independent whole-group shared-policy training, untouched layouts/multiple seeds and actual model videos remain unfinished.','No diagnostic failed samples admitted; first zero11, later both arms/waist yaw, no assist, non-target15mm, waits and h10 remain unchanged.'],source_sha256={str(p):sha(p) for p in [Path(__file__),R/'RESPONSE_COMPARISON_10_V1.json',R/'NUMERIC_VISUAL_SUMMARY.json',R/'FRONT_BOX_ROUTE_REGRESSION_V1.json',R/'PROTOCOL.json']},training_ready=False,goal_complete=False)
with (R/'COMPLETE_COLLECTION_FINDINGS_V1.json').open('x') as f:json.dump(result,f,indent=2)
text='''# 本轮完整采集结果：不扩采，不训练\n\n8 条推动和 2 条等待全部采集、10 条实际画面复核完成。**推动从父版本 6/8 降为 5/8；两组都未完整通过，合格组 0。** 原控制审核继续，不能将本文件作为全部审核关闭或训练准入证明。\n\n| 配对组 | 父版本推动 | 本轮推动 | 等待 | 准入 |\n|---|---:|---:|---:|---|\n'''
for group,g in groups.items():text+=f"| {group} | {g['parent_push_passed']}/4 | {g['candidate_push_passed']}/4 | 通过 | 拒绝 |\n"
text+='''\n**好结果有限：**交换前袋推进38.50→72.43mm，实际运输修正83→467次，但仍失败。全部本轮非目标物体最大XY位移为0，首11维状态/动作零、无助推，两个等待通过。\n\n**坏结果：**前盒103.95→88.88mm，持续失败；交换后盒316.77→258.59mm，从通过退化为失败。后盒新高度分支未应用，不能直接把退化归因该分支。后盒原225步最优性审核仍失败，原1e−6门不变。\n\n前盒独立重算两版共2398帧间距和路线状态，均与原记录一致。第1010步目标X位移+1.344mm造成间距损失，旋转仅补回0.078mm；真实间距10.332mm低于11.5mm恢复门。后期三次重接触共占147帧非推动时间。需改善横向跟踪/安全余量保持，不能删保护性换向或放宽间距门。\n\n下一步：完成原224项控制审核；修正并完成隔离解析求解器原生链验证；持续接触和横向跟踪另立候选，原同条件完整验证后才讨论扩采。只有完整类别交换训练/验证组通过全部质量门，才转换和训练共享模型；最终仍须未参与调参布局、多种子h10闭环及实际模型画面验证。\n'''
with (R/'COMPLETE_COLLECTION_FINDINGS_V1.md').open('x') as f:f.write(text)
print(json.dumps(dict(recorded=True,groups=groups,audit_rows=len(rows),audit_failures=len(fail),verified_frozen_sources=result['verified_frozen_sources'])))
