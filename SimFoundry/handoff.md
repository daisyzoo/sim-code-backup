# 分拣采集 / PI0.5 交接（更新于 2026-09-30）

给下一个 agent / 人用。一律用中文回复用户。工作区：`/home/user/Documents/zoo/sim`。

**硬约束（新工作必守）**：[`PROJECT_CONSTRAINTS.md`](PROJECT_CONSTRAINTS.md)。其中 §1 要求上半身 11 关节首帧为 **0 位**；本文档下文及历史数据里使用的 `U1_REAL_REST_*` 休息角仅作对照，**不得**用于新采集（采集前核验实际初始状态）。

---

## 2026-10-02T21:32:15.286564+00:00 两个首次居中物理均有推进改善但仍失败；持续滑移已实测定位，补齐遗漏审核依赖

前一goal轮及本轮均 **progress**，整体goal active未完成。共享RGB+指令、类别位置解耦前后/斜向/左右交换、首11维q/action零后双臂/腰yaw可动、非目标全过程15mm、无助推、原h10/其余门、完整组整体划分与独立未调参192推3wait多seed实际模型图审均不变。**0新增训练准入/转换/新模型**。

**父对照正式关闭：**`front_initial_margin_baseline_r1/RESULT.json`和`RESULT_WITH_SUPPLEMENT.json`齐备。194原审核+8独立稳定性补充+10人工实际图审；原两旧confirmation公式失败保留，补充后无未解决控制项。仍 **6/8推+2wait**，reverse11/diagonal10各3/4、两组拒绝训练。原runner3299110、auditor3299158、supplement3299919及closure3327141状态见LATEST实测。

**新物理重要好/差结果：**`FRONT_INITIAL_TWO_FAILURE_FINDINGS.json`及各episode两个`FRONT_INITIAL_CONTACT_MOMENT_DIAGNOSTIC.json`/`FRONT_INITIAL_LOST_LOAD_DIAGNOSTIC.json`来源绑定。
- 840023交换袋：真实首交接step156、150command、3连续ready，首次实际COP距中心 **4.626mm**；推进从父 **1.301→29.730mm**，0通道保护帧，非目标0。**仍任务失败、10次lost_contact**。首次推166–219手参考点XY移动108.409mm、物体20.162mm，相对滑移88.312mm；最低支撑点从碰撞核内61.933mm到核外2.582mm并载荷归零。54帧中52帧按压bias已达原−6mm，中位实际载荷1.874N、目标Z仍比实际低2.493mm。不能把更居中当持续摩擦成立。
- 840020前盒：首次实际COP距中心 **2.917mm**；推进从父 **53.473→109.261mm**，非目标0、0通道保护帧。**仍失败，1次倾斜+9次lost_contact**。首次推181–205手移动48.747mm、物体10.471mm，相对滑移38.385mm后倾斜重接触。两困难组仍失败，不扩训练。
- COP/瞬时力矩从真实previous-action最后物理tick力包与XYZW姿态独立重算，parent7/74和candidate326/363个加载COP与原日志一致。离散末tick不是24子步积分，也不能单凭它确证力矩因果。当前实际推断：初次落点有效，持续推进使手滑过物体；下一步检查相对推进上限与实际载荷，而非继续只调整初始姿态。

**发现并处理审核准备遗漏（不是静默修绿）：**原16适配生成器漏生成被continuity调用的`audit_front_initial_stage_region_causal.py`。前两条continuity/bounds/rear_xy共6项因该文件不存在而失败。先前inventory只覆盖顶层，未发现此传递依赖。原冻结文件及缺失名称继续保持原样，原失败日志不改。另建`audit_front_initial_region_{action,causal,continuity,bounds,rear_xy}_supplement.py`五级链，仅变模块/报告名称、原全部公式/阈值可逆重建，显式子进程依赖存在；首两非region实际完整文件通过，但不能代替后绕/首次新事件分支实测审核。`FRONT_INITIAL_REGION_SUPPLEMENT_PREPARATION.json`记录原因与源码对应。独立watcher **3335859**按原整条审核完成后补充8推，原audit仍运行不改。新增`close_front_initial_with_region_supplement.py`仅在全部齐备后校验原日志确为exact缺文件错误、五报告与来源全过才另外生成RESULT_WITH_REGION_SUPPLEMENT，其他错误与任务失败一律保留；目前只验证pending路径，尚未关闭候选。

**当前真实进程与任务：**candidate runner **3324325**、collector **3342871**（case840021）、original auditor **3324396**、supplement **3335859**重新核实/proc。已登记 **7/10** 条，实际图审6条，原审核66项；补充2/8。3307冻结文件重验一致；后续不得编辑已冻结旧源码。空闲约30.58GiB，原空间门不改。

**继续执行顺序：**完成当前全10条件、全部原控制/native审核、独立补充及实际图审，再原closer+补充closer关闭同设置比较。下一候选应先离线检验“相对已验证物体接触参考的有限推进”，避免累计drive只相对手本身导致滑出；保留原法向压力/峰值/关节/几何门，明确验证会不会只是从滑脱变成停滞。若压力仍饱和，再依据实测关节目标残差评估受控补偿，不能直接放宽力或质量门。**此相对推进方案尚未实现/物理启动**。保留8完整诊断组32推8wait、12train/validation组及其余后绕困难项，准入后才转换共享训练与独立模型验收。

以下历史以本段最新证据为准。


## 2026-10-02T21:05:25.306587+00:00 同设置父对照10/10与实际图审完成；首次居中落手物理已启动

前一分拣goal轮与本轮均 **progress**，整体goal active未完成。共享RGB+指令、完整多样类别交换布局、初始11维零后双臂/腰yaw允许、非目标全过程15mm、无助推、原h10/质量门、整体组划分及未调参192推3wait多seed实际模型图审要求全部保留。**0新增训练准入/转换/新共享模型**。

**父对照完整数值与实际画面：**`front_initial_margin_baseline_r1/NUMERIC_VISUAL_SUMMARY.json`已绑定全部10条独立数值与实际8RGB抽帧（推另4外视）；**6/8推+2/2wait**，reverse11与diagonal10各3/4推、整组均拒绝。840023袋1.301087mm和840020盒53.472832mm通道保护失败保留，详见前述独立复算。成功的840022袋、840021盒/袋末态仍top_push、缺少既定可选query-phase导出的稳定释放后缀；不把它改成新的原质量门，也不通过强行改标签解决。目标画外风险保留。此刻原审核 **139/194**、6/10条完整；旧两confirmation公式失败有独立补充通过，原报告保留。采集runner3299110已消失。auditor3299158与supplement3299919仍核实活跃。

**新候选真实启动：**队列正常等待父10条件退出，完整preflight通过后单次启动`front_initial_physical_r1`。runner **3324325**、collector **3330029**、auditor **3324396**均/proc核实；**3307冻结来源全部一致，不修改已冻结W.py/控制器**。同原8推2wait，仅新增首次居中落手flag；当前case840023，已登记2/10条件。首盒已1200帧、独立数值+pose过、实际图审绑定；推进159.980930mm、非目标0、terminal后缀213帧。但首次落手selected=false/0events，是回归对照，不能当新策略收益。

**实际重复性证据：**首盒`MATCHED_PARENT_ARRAY_COMPARISON.json`和`MATCHED_PARENT_DIVERGENCE.json`表明同seed非逐帧相同：q第1步差2.95e-14rad，action首次差第10步7.45e-9rad，到119步出现mode差、共41帧模式不同；最终推进只比父少0.001729mm、两者均过。数值敏感是合理推断，不证明已排除所有实现原因；完整组与多seed仍必须。首候选图中后期盒画外，与父一样保留风险。

**不中断的收尾安排：**新增`queue_front_initial_baseline_closure.py` PID **3327141**已核实活跃，绑定人工图审及numeric原始哈希、exact原auditor身份。仅当194项原审核、8补充均终态并退出后，顺序执行原baseline closer与独立supplement closer生成RESULT/RESULT_WITH_SUPPLEMENT；任何异常停止、不重试采集、不自动标记图审或豁免任务失败。当前状态`waiting_for_original_auditors`，最终父RESULT尚待齐备。

接续当前候选原进程，重点看840023袋和840020盒实际selected落手及后续旋转/通道失效；完成完整组所有控制/native审核和实际图审再比较。保持原8诊断完整组32推8wait与12训练/验证组及其余后绕困难项；不能用首条通过代替完成。当前空闲约31.95GiB，原30GiB启动/25GiB储备门不改。

以下历史以本段最新证据为准。


## 2026-10-02T20:50:26.679053+00:00 同设置父对照采集中；首次居中落手已排队，两个通道失败已独立重算

本轮与前一分拣goal轮均 **progress**，整体goal active未完成。完整共享RGB+指令、类别位置解耦前后/斜向/左右交换、首11维q/action零后双臂/腰yaw可动、非目标全过程最大XY15mm、无助推、原h10/其余质量门、完整组整体划分及独立未调参192推3wait多seed实际模型图审均保留。**0新增训练准入/转换/新模型**。

**实际父对照：**`front_initial_margin_baseline_r1`是不变MS控制器在reverse11与diagonal10的同设置基线，完整8推2wait；不能用旧BASE的不同profile当单变量对照。此刻采集 **7/10**，runner3299110、collector3317443、auditor3299158、supplement3299919均重新核实/proc；121项审核、6条完整、2项记录失败。前840022盒/袋旧稳定性公式失败均有独立supplement通过，原报告不改，其余审核仍须完成。已实际查看并哈希绑定6条图审，非全帧视觉安全认证；目标裁切/画外仍需模型验证。

**差结果与可复核原因：**`FRONT_INITIAL_PARENT_CORRIDOR_FAILURE.json`对实际XYZ、XYZW姿态逐帧独立重算，344个已发出route_goal_x与日志相符，两首次保护步精确重现。交换840023袋推进 **1.301087mm**，初始规划桌边余量5.138958mm（仅比原5mm多0.138958mm），第112步偏转约0.0735度及轻微姿态变化后降到4.901835mm，后1088帧保护抬手。840020盒推进 **53.472832mm**，初始余量21.014376mm，第234步偏转约16.7616度后降到4.970834mm，后966帧保护抬手。两非目标全过程XY=0。是未来规划通道失效，并非当前物体落桌；原保护不放宽。两组失败不得入训练。

**补齐的前物理验证：**完整native观测来源3正例+10负例、真实状态类8场景压力/COP/高度/参考历史（每例17帧含11载荷帧）+5篡改拒绝、自碰撞新dispatch22检查完成；这些为明确标记的夹具，不是新物理。旧history/V2失败保留。发现旧离线planner夹具用了外观尺寸，实际控制器本来已读取collision core；不是控制器误用尺寸的证据。用实测core完整重算8例仍7selected/1预算fallback，随后actualAST接线8场景/8parser/10非法命令均过。66控制文件未改。见`FRONT_INITIAL_ACTUAL_CORE_CHECK.json`、`FRONT_INITIAL_ACTUAL_STAGE_CHECK.json`及LATEST绑定其余报告。

**持续运行安排：**`front_initial_physical_preparation_r1/PLAN.json`、`run_front_initial_physical.py`、watcher、closer已准备。原6命令/10条件仅增加`--front-initial-center-landing`，全部6实际parser与前置来源检查已通过，完整预检正确因父采集未结束而阻止启动。队列`queue_front_initial_physical.py` PID3315572已核实运行，绑定父进程starttime和命令；父10条件正常退出后才完整预检并单次启动新`front_initial_physical_r1`，异常/超时不重启或跳门。**本记录时新候选尚未物理启动**。CPU原审核可重叠，新旧双方完整审核及实际画面齐备才允许关闭matched比较。

**空间口径更正：**原代码预算是每个两推case 1GiB、每wait case 0.25GiB，非此前文字所写每单推1GiB；启动30GiB/储备25GiB门不改，当前约32.83GiB。原8前侧所属8完整诊断组32推8wait、后绕困难项与原12训练/验证组均不缩减。接下来先完成本批原对照与候选，再据两类结果决定接触与路线余量改进，完整组准入之后才转换共享训练及独立验收。

以下历史以本段最新证据为准。


## 2026-10-02T19:59:54.861813+00:00 原末段版已正式关闭；新前侧完整文件审核与参考生命周期已验证，物理尚未启动

本轮与上一goal轮均 **progress**，整体goal active未完成。完整共享RGB+指令、类别位置解耦前后/斜向/左右交换、首11维q/action零后双臂/腰yaw可动、非目标全过程15mm、无助推、原h10/其余质量门、完整组整体划分及未调参192推3wait多seed实际模型图审要求不变。**0新增训练准入/转换/新模型**。

**已关闭的差结果：**`terminal_lead_physical_r1/RESULT.json`正式生成；两原进程3223400/3223459均已/proc消失，204/204审核、10实际图审、3202冻结来源全齐。仍 **6/8推+2/2wait**，无困难交换收益。reverse07为2/4拒绝；diagonal02为4/4仅诊断。840015袋step210原KKT残差 **4.9762298865651566e-6 > 1e-6** 失败保留，无豁免、无准入。

**本轮实现与好证据（不是物理）：**见`FRONT_INITIAL_CENTER_NATIVE_ADAPTER_FINDINGS.json`。
- 保留旧审核，新增`audit_front_initial_center_live_v2.py`/`planning_v2.py`：检查所有静态/因果回退、首次应规划却漏记、路径中漏事件、终点未交接、重复规划、力包覆盖和交接后anchor/reference。`FRONT_INITIAL_CENTER_NATIVE_V2_CHECK.json` **5类完整文件正例+16反例**；另`UNFINISHED_HORIZON_CHECK`单独证明满1200帧但末步路径未完成也拒绝。
- `SOURCE_POSITIVE_CHECK`真实新源码快照正例+6篡改拒绝；**只证明provenance/args，完整native观测与runtime/substep来源正例仍需补**。
- 新normal/task-row适配只接受独立验证front事件，不冒充rear；原普通/加载法向/KKT算式可逆还原。`TASK_ROWS_CHECK`对旧实际整条1199控制记录逐字段重算相同，真实step210失败仍在；7路由夹具过。
- `prepare_front_initial_stage_audits.py`生成6个隔离原pose/contract/context/normal/task/self-clearance适配；`POSE_FILES_CHECK`完整1200帧困难840023袋和840016预算fallback组合文件通过。原rear记录仍单独保留，front独立记录，hold/final-command与实测capture接线已加。
- **关键时序确认：**`front_initial_center_reference_ledger.py`将持久手部center与重接触会清除的surface分开。真实状态类8场景均验证：lost-contact内部重置在当帧surface算完后，方向切换外部重置在算surface前；不能一律在计数增加当帧删旧surface。`REFERENCE_LIFETIME_CHECK`保留8全部案例与原off56边界对照。
- `prepare_front_initial_stage_remaining_audits.py`生成16个参考/末段输入/near-half/高度/原压力/加载/恢复及修正稳定性适配。`front_initial_stage_run_contract.py`清单与原60条件逐个核对，**原审核类别无遗漏，22源码差异全部绑定**。这仅是清单/来源证据，不能代替剩余实际文件检查。

**下一步连续操作：**
1. 新stage66文件与原PREPARATION/CHECK哈希仍一致；不改控制源。完成完整native观测来源正例和自碰撞新分支/最终action检查；原pre/post FK、关节/slew/肘门数学不改。
2. 验证ledger消费者near-half/terminal-input与新front-height；检查pressure/COP历史在捕获清理后的原逻辑，不允许以未验证skip代替。新stability复用已验证margin修正式，原历史失败仍保留。
3. 只有全部适配准备齐才冻结物理协议。保持原8前侧所属8完整组 **32推8wait**、4原失败/4原成功都在；其余未有同设置父对照者补matching margin baseline。原完整12训练/验证组不缩减。空闲约35.44GiB；按原30GiB启动/25GiB储备、推1GiB和wait.25GiB保守门规划完整批次，不悄悄降低门。
4. 当前没有活跃采集/训练；本轮CPU检查均已完成。首次居中落手 **仍未物理启动**，不能把上述夹具/清单当任务改善。后续继续完整组物理、质量与实际画面，整体准入后共享训练及独立h10多seed模型验证。

以下历史以本段最新证据为准。


## 2026-10-02T19:22:12.212705+00:00 首次居中落手已隔离接线；独立1103事件审核通过；原物理新增驻点审核失败

本轮 **progress**、前一goal轮progress；整体goal active未完成。共享RGB+指令、类别位置解耦的前后/斜向/左右交换、完整配对整体划分、首11维q/action零后双臂/腰yaw可动、非目标全过程15mm、无助推、原h10及其余质量门、未调参独立192推3wait多seed和实际模型画面全部保留。**0新增训练准入/转换/新共享模型**。

**当前原run：**`terminal_lead_physical_r1`10/10采集与10实际图审已全齐，数值仍6/8推+2wait。runner3223400已/proc消失；同一auditor3223459仍活，现 **146/204审核、6/10条完整、1失败**；空闲约35.45GiB。不重启、不修改3202冻结源码，全部审核齐后才`close_terminal_lead_physical.py RUN --apply`。

**新增差结果已定位并原样保留：**840015袋本已任务失败，第210步`audit_terminal_lead_stage_task_optimality.py`也失败。真实求解status0/37迭代、名义肘gap5.00000087mm，但独立全支撑顶点stationarity残差**4.9762298866e-6 > 原1e-6**。`TERMINAL_LEAD_CONTROL_FAILURE_FINDINGS.json`用实际q、前action、J/error/边界/原独立几何逐项重算，certificate与原失败逐字段相同。不是日志误报，不放宽阈值、不豁免、不把数值6/8当准入；该任务新末段floor触发0，不能归因于未触发特性。

**新的实质实现：**`staged_front_initial_center` **66文件**，从已完整审核margin父版本复制、默认off `--front-initial-center-landing`。实际collision core、双手pose和原q/前q/前action进入V3；原front guards先执行；command/handover/stop独立日志；原最终动作slew/关节/几何门保留。真实3帧交接后持久更新physical center/surface、法向及inactive anchor，清理压力/COP/XY历史。独立`verified_unloaded_front_initial_joint_path`不冒充rear重接触，真实计数0。复制top helper资源根已按新stage层级修正，不盲用parents[2]。

**检查完成（仍不是物理）：**
- `staged_front_initial_center/CHECK.json`：实际parser8组合、8场景collector块/协调器/最终action链、10类非法命令拒绝；原代码可逆diff、资源根匹配。7首次命令、1无可行预算路径保持原行为；7人工端点三帧交接及stop传播均过。
- 缺失载荷反例发现新runtime停止日志重复step导致TypeError，已在物理前修复并记录`PREPARATION_STOP_LOG_FIX.json`，没有放过异常。
- `FRONT_INITIAL_CENTER_EVENT_AUDIT_CHECK.json`：不导入候选的独立URDF几何/命令/真实参考审核，**1103显式仿射夹具事件、7交接、1原控制fallback**，10类错计数/载荷/当前q/动作/ready/vertex/surface/anchor/normal/缺连续帧全拒绝。全部8场景在报告中。
- `FRONT_INITIAL_CENTER_PREFLIGHT_AUDIT_CHECK.json`：独立复算8场景因果预检及替代选择，840023先拒111节点路径，再选择133步替代；预测capture永不当实际交接。原840016246节点预算失败保留fallback，不扩240预算。
- 新`front_initial_center_stage_source_binding.py`和`audit_front_initial_center_live.py`已经编写，保留原完整时长/24子步/无助推/压力来源要求；4旧margin/lead来源拒绝与语法检查通过。**尚未完成正向native文件夹具、原normal/reference/anchor/pressure/KKT/terminal审核适配，不能启动新物理。**详见`FRONT_INITIAL_CENTER_INTEGRATION_FINDINGS.json`。

**接下来的连续操作：**
1. 接续旧204审核并正式关闭，保留新增KKT失败，10图审无需重做。
2. 完成新live/source正向native夹具和原审核适配。原`verify_normal_rows`、pose_live、task_optimality等仍仅识别rear joint-path；须加入**独立已验证**的新front类型和capture，保留所有原普通/后绕/加载数学，不可一遇新模式就跳过。
3. `FRONT_INITIAL_CENTER_COMPLETE_GROUP_COVERAGE_PLAN.json`列原8前侧所属完整8组，**32推8wait**；四原失败及四原成功都保留。尚无matching margin baseline的组须按同设置补父对照，不能用不同BASE profile分数冒充单变量收益。先优先reverse11/diagonal10/reverse07/reverse03困难组，再保留lateral08预算fallback与其它原成功完整回归。冻结原输入/来源/GPU/空间门后再运行；原30GiB启动、25GiB储备及保守每剩余推1GiB/wait.25GiB不改。
4. 最终仍需原12完整train/validation组准入、转换共享训练和独立h10多seed实际模型验收；8组诊断覆盖不替代完整目标，也不意味着已经训练或物理成功。

以下历史以本段最新证据为准。


## 2026-10-02T18:48:59.527975+00:00 完整物理数值仍6/8；首次真实居中落手受控交接/可跟踪性预检已完成离线实现

本轮 **progress**，上一分拣goal轮progress；中间Git代码备份已核验完成。整体goal active未完成。共享RGB+指令、类别位置解耦前后/斜向/左右交换、完整配对整体划分、首11维q/action零后双臂/腰yaw可动、非目标全过程最大XY15mm、无助推、原h10/其余质量门、独立未调参192推3wait多seed与实际模型画面要求不变。**0新增训练准入、0转换、0新共享模型**。

**物理新结果：**同一个`terminal_lead_physical_r1`已完整10/10，原数值+pose **6/8推、2/2wait**，仍与margin父版本一致，**困难交换两推仍失败，没有任务成功率收益**。10条均实际查看8RGB（推另4外视）并绑定哈希；`NUMERIC_VISUAL_SUMMARY.json`只是数值/图审中间汇总，不代替最终RESULT。runner3223400已/proc消失；auditor3223459仍/proc活，当前 **65/204审核、2/10条审核完整、0已记录失败**，冻结3202文件不改。空闲约35.47GiB。全部原审核完成后再`close_terminal_lead_physical.py RUN --apply`，不要重启原run或提前宣称控制通过。

- **好结果有限：**840014盒160.040796mm/袋160.001412mm，669/823步释放，原成功任务末段更快；840004盒284.388646mm/袋300.021663mm，559/884释放；840005袋159.997359mm，728释放。以上非目标0。原成功/等待保持，不是新模型收益。
- **差结果明确：**840015盒296.623453mm、非目标7.634317mm，仍未稳定越过右区；袋145.854943mm、非目标0，末态front_guard_lift；840005盒158.443913mm数值过但仍top_push、无稳定terminal suffix。实际RGB后段目标/双物体裁切或画外风险保留，不修改门。
- **因果归因纠正：**`TERMINAL_LEAD_DIFFICULT_BRANCH_ATTRIBUTION.json`两条困难任务initial_top都false、新floor触发均0；盒命令第5步、袋106步已出现>1e-7差异。因此这些困难任务数值变化不能归因于未触发的新末段反馈；执行/仿真差异归因未解决。

**困难主线的新实现：**见`FRONT_INITIAL_CENTER_IMPLEMENTATION_FINDINGS.json`。新增文件均在RUN冻结后创建，没有改live代码。`front_initial_center_plan.py`约束实际最低手hull点中心XY±2mm、离面6–7mm、thin-axis≥.8，四个当下/固定中性seed、原关节/手-另一物/肘5mm及采样路径；`front_initial_center_tracking.py`使用真实recontacts==0（不伪造恢复计数），只当前/前一状态/前动作因果响应，原command/预测geometry/slew保留。lifecycle只3帧**实测**ready才能捕获真实reference/surface/normal/inactive anchor；240步不变，接管后失败显式stop。

**离线好/差证据与修正：**
1. V1全部8仿射路径失败，原源码和`FRONT_INITIAL_CENTER_LIFECYCLE_CHECK.json`保留。静态solver .7999999999999996与.8严格比较导致错误拒绝；V2仅在新增center/alignment ready比较采用原solver同量级2e-7数值容差，原任务门/3帧/240步不变。V2完整8真实初始观测，8首命令独立几何/公式验证，**6/8仿射路径交接，8/8人工端点三帧交接夹具通过**；不是真实物理。
2. `FRONT_INITIAL_CENTER_TRANSPORT_DIAGNOSIS.json`：困难840023最小运动111节点路径在106命令时名义肘间距**4.655975mm**低于5mm，虽然预测状态6.642351mm和静态路径过，仍正确拒绝。同场景actual-state seed130节点/133仿射步可过。840016原成功盒246节点在240命令仍离终点22.469mrad、alignment.792359，不能放宽预算或删此原成功例。
3. `front_initial_center_selection.py`+`front_initial_center_lifecycle_v3.py`落实**先当前/过去观测的有限仿射预检，再按运动代价选择可跟踪替代路径**；预检捕获全部丢弃，真实控制仍ready0开始。`FRONT_INITIAL_CENTER_SELECTION_CHECK.json`完整8场景：**7选择、1接管前明确保持原控制**（840016），不排除任何任务。840023自动选133步替代，非布局ID特判。仍须真实采集验证模型响应假设，不能把7当任务成功。
4. `front_initial_center_top_contact.py`/`route.py`/`cop_route.py`隔离复制原类，仅显式捕获surface hook+恢复清理；`front_initial_center_adapter.py`清理压力、COP/XY历史并交接。`FRONT_INITIAL_CENTER_STATE_CHECK.json`核原源码反向diff，**56个off真实类边界输出逐字段一致、8个capture连续/原front guard优先/恢复清理**。首次测试把微倾斜表面当水平面，断言失败另存`FRONT_INITIAL_CENTER_STATE_ASSERTION_DIAGNOSTIC.json`；已按真实normal投影验证，未改控制。

**连续下一步（不是停止点）：**
1. 原terminal_lead 204审核接续，10实际图审已全齐；审核完成后正式关闭，保留所有失败。当前只审核在后台，不能说采集/训练仍在跑。
2. 以已完整审核的margin父版本隔离接collector默认off开关，使用V3+selection+上述真实点surface适配，不混合尚未完整控制审核的lead。读取真实collision core及双手pose；先原front guards再lifecycle，独立记录command/handover/stop；最终原command admission保留；实测交接同时更新持久physical center、normal、inactive anchor，再进入原loading。不要仅复制rear_region限制或虚构recontacts。
3. 原复制top_contact helper当前位置在W，若移入stage须核资源根路径：`support_mesh`的parents[2]不能盲搬。新增source/测量/命令独立审核及parser off/on/不兼容拒绝，真实默认off一致后，才启动完整原组物理回归；840016父控制fallback保留分母、全部4原前侧失败必须覆盖，不能只测一个新成功。
4. 原3 rear_push前置问题、完整12train/validation组严格准入/整体划分、转换共享训练、独立多seed h10实际模型验收继续保留。几何/仿射夹具不是准入或目标完成。

以下历史以本段最新证据为准。


## 2026-10-02T18:14:26.555979+00:00 前侧初次真实落点成为主线；末段完整对照已启动并首两条审核/实际图审通过

本轮 **progress**，上一分拣goal轮也是progress；目标active未完成。共享RGB+指令、类别位置解耦的前后/斜向/左右交换、多样完整组整体划分、首11维q/action零位后双臂/腰yaw可动、非目标全过程15mm、无助推、原h10/其余质量门、未调参独立192推3wait多seed和实际模型图审不变。**0新增合格训练数据、0转换、0新共享模型**。前一margin完整结果仍6/8+2wait，没有困难任务收益。

**当前真实运行：** `terminal_lead_physical_r1`，与已关闭margin父版本相同8推2wait、原1200/70/5N/seed，仅`--terminal-directional-lead`。完整十条件启动前审核通过，source冻结 **3202**。当前pipeline **2/10**，正在layout840015；runner3223400、collector3228925、auditor3223459均/proc live。原适用审核194项全部保留，旧确认公式用已独立验证的margin版本，另加10次独立反馈审核，共预期204；当前执行 **48** 项、完整审核 **2** 条，失败 **0**。已完成2条真实图审，空闲约36.92GiB。当前冻结W已有.py及stage不可改，新诊断文件须另建。

**首两条有限好结果：**840014盒完整1200，原任务+pose过，推进160.040796mm、非目标0、首q/action零、assist0，669步释放（父1059）；独立实际反馈285行、44行floor。840014袋完整1200，同门过、160.001412mm、非目标0，823步释放（父全程未释放停在158.367470mm）；实际反馈556行、133floor。两条`EARLY_TERMINAL_LEAD_MEASUREMENT_CHECK.json`及actual review绑定已写，原native审核现均完成且通过。这是原成功任务的效率/释放改善，**不是新增困难任务或整组/模型收益**。

**实际画面差结果保留：**两条8RGB+4外视均已实际查看。盒0/171/342可辨，171/342手部遮挡，513严重右裁切，685起大部分画外仅某些抽样小角残留；袋全8可辨。袋任务目标袋171起所有抽样画外，非目标盒171/342可辨、513起左下/下边缘部分裁切。外视有机器人/桌面，但抽帧不替代逐帧/子步质量门；后续RGB模型验证仍必需。

**新反馈审核防遗漏完成：** `TERMINAL_LEAD_STAGE_AUDIT_ADAPTER_CHECK.json` 实际10父条件/194原审核清单一致、8条旧稳定性补充逐字段一致；独立新checker不导入候选，重建实际trace/姿态、Y路径、X目标、clearance/lateral状态、前命令、期望Y前导/限幅及expert映射。明确标注的历史未来观测夹具1808改变行，**不是候选rollout**；错X/目标/缺标注/超步长/错phase/错direction/陈旧前命令标注7类拒绝，旧source拒绝。原适配、运行、图审与closer均新文件，原报告未覆盖。完成所有条件后用`close_terminal_lead_physical.py RUN --apply`，失败/短例用对应incomplete review并保留原分母。

**困难干扰主线的新证据，而非仅做末段：**
- `FRONT_CAUSAL_WRENCH_RELANDING_SCREEN.json`覆盖原8前侧（4成功4失败）加当前840015袋。每个候选只用已完成前10动作的最后物理tick力包、当下姿态；明确**不是24子步积分冲量**。代数保持原力分布，沿任务横向移动力作用线可使yaw矩抵消，仅是假设。6个因果窗有内部候选，**3个原成功也会触发**；当前困难袋447步候选世界X约−21.88mm，未执行。
- `FRONT_WRENCH_RELANDING_ENDPOINT_PROBE.json`：6场景修正点均有原界内静态落点；`FRONT_WRENCH_RELANDING_PATH_PROBE.json`：其中5场景有独立检查过的名义卸载+再落路径。840012原成功盒直线卸载检查拒绝，不能因为末端可达就走该路径。当前困难袋一条合格名义路径81节点；这些不是实测卸载、COP落位、接触黏着/摩擦、完整身体扫掠或物理成功。见`FRONT_WRENCH_RELANDING_FINDINGS.json`。
- **原840020盒与840023袋从未到lateral_y**，先前此规则不覆盖。实际首次保护分别237/112；840023袋仅 **7步top_push**，十观测反馈先天来不及。不能缩短窗口硬凑覆盖，也不能只汇报6个有候选的样本。
- 因此优先首次真实接触点：当前front控制目标是虚拟支撑参考，实际手最低点可在物体上偏移数厘米；rear-region专有捕获机制没有用于front。`FRONT_INITIAL_CENTER_LANDING_PROBE.json`以每条**第一真实无载top_cross**状态和当下场景，将实际手hull最低顶点约束在物体顶面中心XY±2mm、离面6–7mm；真实URDF限位、独立手/另一物及肘/原采样无载路径检查。**全部8条均有静态居中落点及直线路径**，原成功和失败都保留；这是新的初接触可行线索，不是物理COP居中证明。
- 最小关节运动方案的路径点数依次230/149/156/121/141/246/155/111；840016原成功盒246存在原240步预算风险，230也要验证实测跟踪。路径点数不是严格运行时间下界，不重复旧后绕解释错误。见`FRONT_INITIAL_CENTER_LANDING_FINDINGS.json`。此候选**尚未接collector/无物理**。

**连续下一步：**
1. 接续当前同一terminal_lead run，先关注840015困难盒/袋；落盘即原门复算+实际8RGB4外视绑定。全10及204适用审核齐后收尾，不重复旧run、不因当前单项成功扩采。
2. 主实现方向是默认off的**前侧初次真实最低点居中落手**：仅当前实测无载且父guard先通过时规划；严格原关节/预测/手和肘间距/动作slew；测量连续ready后才能捕获物理参考、surface点、法向及非工作手锚点，清理压力/XY历史再进入原加载。原front守护、载荷、目标、时限和全任务门保持；无路径/预算风险必须显式保持原行为或安全失败，不能伪造交接。先真实生命周期/反例/独立source审核，再完整配对物理回归。不要只改surface fraction或再次锁手yaw。
3. 过去力矩的卸载再落手可作后续恢复，但它会扰动原成功且有未覆盖早期失败，不先全局部署；两条初前推失败优先步骤2。
4. 原3条rear_push前置失败、12完整train/validation组、合格准入/整体划分、转换共享训练和独立h10多seed实际模型验收仍全部保留；不能以以上几何探针或首两条改进标记完成。

以下历史以本段最新实际证据为准。


## 2026-10-02T17:36:31.579245+00:00 余量对照完整关闭6/8；后绕可达界新证据；末段候选仅隔离接线

本轮 **progress**，上一分拣goal轮也是progress；中间Git备份已完成。整体goal active未完成。共享RGB+指令、类别位置解耦的前后/斜向/左右交换完整配对与整体划分、首11维q/action零位后双臂/腰yaw可动、非目标全过程最大XY15mm、无助推、原h10及全部原质量门、独立192推3wait多seed和实际模型图审要求保持。**0新增合格训练数据、0新增转换、0新共享模型。**

**本轮物理结果正式关闭：** `terminal_margin_physical_r1/RESULT.json` 与 `RESULT_WITH_SUPPLEMENT.json` 均已实际生成并复核；10/10条件、194原审核、8独立确认补充审核、3149冻结来源和10条实际图审绑定全部核验。原4项`audit_contact_stability_control.py`失败保留，只对确属旧确认公式的错误独立修正，修正后无未解释控制失败。任务仍 **6/8推+2/2wait**，父版本也是6/8，**没有任务成功率收益**。reverse_diagonal07 **2/4**仍拒绝；diagonal02 **4/4**且控制通过，但这是诊断run，不自动授予训练准入。

**好结果：**840014盒159.993470mm/袋158.367470mm、840004盒284.026042mm/袋300.078541mm、840005盒157.452658mm/袋159.992859mm及两wait原任务+pose过。840014盒1059才达160mm释放，保留约9.99mm任务质量余量。840004袋恢复父版本已有约300mm成功，不是新解决困难任务。**差结果：**840015盒282.815486mm仍未入右区，非目标袋14.275864mm近15mm门；840015袋140.097152mm、front_guard_lift仍失败。840014袋和840005盒末态仍top_push，不应把任务数值通过当释放已解决。部分目标/双物体后段头部RGB画外或裁切风险仍保留；没有据此改变任务门。

**后台真实状态：**已逐/proc核实runner3168349、原auditor3168395、补充auditor3178307均消失；当前该项目Python后台列表为空，GPU计算任务列表为空。不是后台还在图审；10条真实画面已完成并绑定。空闲约37.84GiB。正在做离线改进准备，尚未启动后继物理或训练。

**新的困难后绕证据：**`FRONT_ALTERNATIVE_REAR_LANDING_PROBE_V2.json` 六个假设后绕落点，仅840023角点/终点静态规划及抽样路径过，其余四个局部求解失败，不能当全局不可行。新`REAR_LANDING_OUTER_REACH_CERTIFICATE.json`用真实URDF肩到手顶点链长三角上界、4097个腰yaw点及连续Lipschitz误差界；在固定物体姿态和当前±.98命令范围内，原10mm inset/4–10mm实测交接区的必要可达距离超过链长上界：840007后角约**13.112mm**，840015后角约**6.020mm**、后终点约**19.753mm**。其余三点此界不确定。只否定这些特定固定姿态落点，**不证明整个布局或所有可控旋转/曲线路径不可行，不删除布局、不扩大关节范围**。这改变下一步：不要继续对同一不可达后角反复增加IK次数；须改物体路径/接触姿态。

**明确更正后绕时限解释：**旧`FRONT_ALTERNATIVE_REAR_LANDING_FINDINGS.json`把248/241路径点数直接当超过240运行步的证明，解释过强，原报告保留。`FRONT_ALTERNATIVE_REAR_LANDING_BUDGET_V2.json`替代其解释：真实交接看实测endpoint容差+几何连续3帧，不要求最后index；沿保存名义路径按每步一节点理想跟踪，最早交接251/244，说明预算风险，**不是实际动力学不可能证明**。两点仍无物理运送/交接认证。

**反证无效简化：**`INACTIVE_ANCHOR_TASK_COMPETITION_PROBE.json`/FINDINGS覆盖8个实际记录状态，原求解命令逐项精确复现；对侧掌任务权重1/.25/0且原法向、限位、双肘与最终guard不改，初始rear六样本主动残差零改善、terminal两样本仅.001782/.000870mm。没有部署去掉对侧掌锚点；只是局部目标竞争反证，不能否定整体姿态/路径重规划。

**末段辅助候选已推进但未物理验证：**`staged_terminal_directional_lead`58文件，继承本轮margin父版本，只新增默认off `--terminal-directional-lead`，限diagnostic margin协议及initial-top lateral_y、正剩余小于原3mm步。`terminal_directional_lead_state.py`让真实父状态机仍管守护/压力/Z/释放；只改变末段Y参考，不提高力、不改目标或质量门。CHECK实际3个parser条件（含缺依赖拒绝）、左右14个真实状态机边界覆盖press→push、持续push、到目标释放、失载重接触、手间距和非目标移动保护；原压力及所有非声明字段一致，默认off一致，拒绝中途换反馈历史。仍不是物理收益。`TERMINAL_DIRECTIONAL_LEAD_AUDIT_PLAN.json`列出原26类/194次审核与新语义、来源绑定待办；**未完成新source/独立反馈审核适配，不可启动物理**。

**连续下一步：**
1. 完整收尾已经完成，不重启旧run或重复图审；以两个RESULT为终态，保留全部失败与可见性风险。
2. 困难任务主线转为联合物体姿态/路线与机器人接触可达性：前侧必须处理旋转吃掉通道，不再无条件改同一后绕；原三个rear_push前置失败也不能被当作top恢复成功。已有Y预移/接触/旋转历史先复用，避免重做已失败的掌朝向硬锁或盲目COP补偿。
3. 完成小范围末段辅助候选独立Y/历史/来源与原审核适配后，才做同原完整10条件物理对照；辅助末段修复不能取代困难干扰问题。
4. 回原12完整train/validation配对组、严格准入/整体划分，再转换共享训练及未调参独立192推3wait、多seed h10和实际模型图审。诊断组件或容易布局成功不算完成。

以下历史以本段最新实际证据为准。


## 2026-10-02T16:51:37.607486+00:00 同一余量对照继续；困难组仍失败；补充旧确认审核与末段/旋转通道诊断

本轮 **progress**，上轮也是progress；goal active未完成。共享图像/指令、类别位置解耦、多样完整配对与整体划分、首11维q/action零位后双臂/腰yaw可动、非目标全过程最大XY15mm、无助推、原h10及其余质量门、独立192推3wait多seed和实际模型画面全部保留。0新增合格训练数据、转换、共享模型。

**当前真实后台：**仍是`terminal_margin_physical_r1`，原run未重启，pipeline **7/10**，当前layout840005；已有7条完整quality落盘、7条实际图审绑定。runner3168349、collector3186793、原auditor3168395、新独立补充auditor3178307均/proc live。原审核执行60项、完整关闭2条；补充已处理2/8推。当前空闲约38.40GiB。PROTOCOL冻结的旧源码和stage不可改。

**好结果，但不是整体收益证明：**840014盒159.993470mm、袋158.367470mm，840004盒284.026042mm、袋300.078541mm，均1200完整并原任务+pose数值通过、非目标0、首q/action零、assist0；841007等待通过。840004袋恢复原约300mm成功动作，相比退化强制恢复约76mm有改善，但它在6/8父版本原本成功，不能称新增解决困难任务。首840014盒1059步达到160mm才释放。840014袋结束仍top_push，距释放余量1.632530mm，最后300步只推进.123411mm，不能把数值通过当作释放稳定。

**差结果：**840015盒完整1200推进282.815486mm，末端仍未过右侧目标区；非目标袋**14.275864mm**，已接近原15mm门，不能说另一物体不动。840015袋完整1200推进140.097152mm，front_guard_lift保护，非目标0。困难交换两推仍失败；本两组尚无准入结果。真实图审已覆盖以上全部：840014两推与840004袋后段目标/双物体画外；840004盒8抽样都可辨；困难盒后段双物体严重右缘裁切；困难袋两物体可辨但袋手遮挡/底缘裁切，末段手抬起；等待8RGB稳定。图审不代替原全过程门。

**审核接线遗漏已显式处理：**`audit_contact_stability_control.py`仍用旧.15/.20确认公式，首盒608条position_confirmation_mismatch，原报告/失败日志保留，绝不修改已冻结源码。新增`audit_terminal_margin_contact_stability_supplement.py`只把确认与已有.16/.205余量相交，所有原倾斜/撤离/释放位姿/卸载载荷检查保留且新来源+完整实测独立release审核必过。`TERMINAL_MARGIN_STABILITY_SUPPLEMENT_CHECK.json`：65完整旧公式报告逐字段一致，错误确认、释放XY、卸载bias、倾斜原因4类反例拒绝。首两实际补充都通过（袋release仍None）。`watch_terminal_margin_stability_supplement.py`单独处理全部8推，失败仍保留；完整收尾先`close_terminal_margin_physical.py --apply`保留原失败，再`close_terminal_margin_with_supplement.py --apply`单独核实修正，只能解释确属旧公式的不一致，不能抹掉其他审核或任务失败。关闭前必须全部10条件与实际图审齐。

**末段停滞新证据/有限候选：**`TERMINAL_SETTLING_FINDINGS.json`证实原直接路线反馈目标正好等于释放边界，目标误差<12mm时手部前导随误差缩小，袋有约4.4N载荷仍近停。仅支持测试驱动力/跟踪问题，未证明唯一摩擦或不可达原因。默认off的`terminal_directional_lead_candidate.py`仅在原lateral_y、未达目标且余量<原step时保留原3mm有向前导，原X/目标/12mm范围/3mm相邻slew不改，**未接collector或新物理**。V1历史输入检查未验证切换处previous，不能作原生命周期证明；V2明确排除215切换行，独立先复现原命令，11291连续历史行/918改变/20双方向边界通过。不能用旧未来轨迹替代候选rollout。

**前侧任务干扰新方向：**`FRONT_YAW_CORRIDOR_RESERVE_SCREEN.json`在原48推里8个front选择，3个初始全yaw通道宽度为负，恰是840007/840015/840023袋失败；各约−23.296/−5.790/−52.121mm。另一个失败840020盒宽度仅+.0855mm。仅固定当前倾斜、障碍姿态下的目标自由yaw包络筛查，**不证明所有姿态控制路径不可行，也不删除布局**。3例原后绕object-envelope备选均可行、路径约.677/.602/.558m，但全机器人可达性/手臂碰撞/接触推进未验证。见`FRONT_YAW_CORRIDOR_ALTERNATIVES.json`。下一应检查旋转余量与完整可达路线，不能继续只放大/缩小front间距。

**连续下一步：**接续本run其余3条件和原/补充审核；每条用现有review脚本实际看图再独占绑定。完整10收尾后对照原6/8，不以累计原容易成功遮盖两困难失败。再验证余量末段候选的真实接线/全原门，并把前侧备用路线送全机器人/接触可达性审查；还须解决3原初始rear接近、完整12train/validation组、转换共享训练和独立h10多seed实际模型验证。所有旧progress gate等探针仍未部署。

以下历史以本段最新实际证据为准。


## 2026-10-02T16:21:28.223302+00:00 重求解对照关闭4/8；终止余量修复完整10条件已启动

本轮 **progress**，前一分拣goal轮有真实诊断/实现进展；中间Git备份已完成。goal active未完成。共享RGB+指令、类别位置解耦且含前后/斜向/左右交换、完整配对组划分、首11维q/action零位后双臂/腰yaw可动、非目标全过程最大XY15mm、无助推、原h10及其余质量门、独立192推3wait多seed与实际模型图审全部保留。0新增合格训练数据/转换/共享模型。

**坏结果正式关闭：** `rear_transport_retry_physical_r1/RESULT.json` 为10/10条件、**4/8推、2/2wait**，低于原6/8；reverse07为1/4、diagonal02为3/4，均拒绝入库。194原审核中14失败全部保留（盒末端pending_recontact），3113冻结来源与10实际图审绑定核验。原runner3125394/watcher3125542/collector3125569均/proc missing。840004袋76.731663mm、840015盒96.456376mm、840015前袋139.079269mm、840014盒149.994195mm失败。840015新物理规划476/实测582的方向见证原本status0，**没有实际触发retry**；旧529回放通过不能算真实重试收益。原/新轨迹在规划重试之前已分叉，不能据此唯一归因。840004袋等后期抽样RGB目标/双物体画外风险保留。

**确认的数据质量问题：** 原`confirmed_position_release.py`稳定10帧+.15m/.20m确认会提前触发`top_release`，绕过`reach_sweep.ready_to_release`已有的.16m推进/.205m目标区余量。56历史推、59,244原确认行复现，33次实际确认释放未满足原余量。840014盒刚过150mm再回落到149.994195mm仍按原门失败，绝不改阈值抹平。新`margin_confirmed_position_release.py`将原确认与原余量取交集，不改质量门；这仅解决释放边界，不代表遮挡/持续牵引/接近问题已解决。

**有限好结果与隔离接线：** `staged_terminal_release_margin`56文件，以完整审核6/8的`staged_joint_edge_clearance_intersection`为父；不结合退化的强制rear恢复或progress gate。真实parser/左右monitor初始化CHECK通过；独立审核不导入候选，56历史复算/旧提前释放拒绝通过。新22份来源/原审核适配保留已完成的edge V2修正和全部原数学门；`TERMINAL_MARGIN_STAGE_AUDIT_ADAPTER_CHECK.json`核10原条件、184项原审核清单与实测目标绑定，拒绝旧来源冒充新版本。另加`audit_terminal_margin_stage_release.py`，按完整原1200/70、实际trace与严格逐步时序检查新确认和release原因。历史检查没有新物理成功含义。

**当前真实后台：** `terminal_margin_physical_r1`，写入时状态collecting、0/10，当前layout840014；runner3168349、collector3168419、auditor3168395均已/proc核实。`terminal_margin_physical_preparation_r1/PLAN.json`与原edge计划逐项相同，仅新增`--terminal-release-margin`，仍同8推2wait、1200/70、5N、原seed，原控制检查全部保留且新增独立release检查。启动preflight通过。不得修改本次PROTOCOL冻结的源码；首条新结果见下段。

**首条新物理有限好结果（2026-10-02T16:27:01.279559+00:00）：**840014盒1200完整，原任务+pose复算通过，最终推进159.9934697mm、非目标0mm、首q/action11零、assist0。独立实际trace/1199控制观测核验在1059步推进160.000026mm时按确认分支释放，末端回落仍留约9.99mm质量余量。`EARLY_RELEASE_MEASUREMENT_CHECK.json`已保存；实际8RGB4外视已看且独占绑定：盒513右缘裁切，685起抽样头部RGB画外，黑袋可见，末段抬手。原控制审核尚待整个case落盘后后台执行；第二条840014袋正在采集。不能据单例当整组/训练/模型收益。

**存储：** `TERMINAL_MARGIN_CACHE_DEDUPLICATION.json`确认两缓存四个Hunyuan推理权重SHA256与HF内容地址逐项相同，用硬链接共享，所有路径/权重内容保留，释放约12.96GiB；当前约40.09GiB。没有删唯一权重、训练数据、实验原始记录或审核依据；原30GiB启动/25GiB运行储备未降低。缓存权重必须保持不可变，后续改写需新inode。

**下一步连续执行：**
1. 接续此同一run；每条落盘后用`review_terminal_margin_stage_episode.py`或incomplete版生成真实8RGB4外视并实际查看、独占写ACTUAL_REVIEW_BINDING；全10完成后`close_terminal_margin_physical.py`关闭，不遗漏短例/失败。
2. 观察修复是否保留原成功动作、阻止提前释放、有没有新增后退/丢载/非目标干扰。完整两组不通过就不入库；通过也只诊断，须原12完整train/validation配对、多样样本、转换共享训练和独立h10多seed模型实际画面。
3. 延后progress_gate V2：6固定原输入1新有载/5原受控卸载、首次bag258/box225独立FK/KKT过，仅无物理探针。加强X推进与原Z抬升上限联合求解5/6局部求解失败，非全局不可行证明；未接collector。原有载入口还会打断原成功推进，不能贸然组合。
4. 原几何投影通道筛查仅历史诊断，不证明真实未来碰撞；.10rad端点腰余量探针两原端点已满足，未改变姿态，无收益。3初始rear接近和front旋转/桌面通道问题仍待解决，不增腰极限或缩小布局目标。

以下历史以本段最新实际证据为准。


## 2026-10-02T15:12:35.479987+00:00 原跟踪完整收尾5/8；一次交接重求解同组物理运行；发现恢复入口命中原成功轨迹

本轮 **progress**，前一分拣goal轮也是progress；中间Git备份已完成，与分拣质量无关。goal active，全部共享图像/指令、类别位置解耦、多样完整配对、首11维零位后双臂/腰yaw可动、非目标全过程15mm、无助推、原h10/其他质量门、独立192推3wait多seed及实际模型画面要求保留。0新增合格训练数据、转换、共享模型。

**坏结果已正式关闭：** `rear_tracking_physical_r1/RESULT.json`：完整10条件，**5/8推、2/2wait**，原对照6/8。194原审核，**16失败全部保留**，来自840015盒529短例；3060冻结来源和10实际图审绑定全核。两个组分别2/4与3/4，均不入库。840004袋77.273272mm/1200仍失败，840015盒69.517288mm/529短例，前侧袋140.258390mm/1200仍失败。停止原进程均/proc missing；不要再把旧run写为6/10后台。

**有限好结果：** 一次有界重求解的132个真实无载上下文回放（398..529）完成，112独立事件审核通过；旧/off命令逐步一致，529原status9失败保留，新候选status0且原完整路径/实测3帧ready等门通过。记录的原规划是明确回放fixture，**不是新物理交接或成功**。见原短例`REAR_TRANSPORT_RETRY_LIFECYCLE_FAILURE_V2_CHECK.json`。12个双手规划/实测原成功上下文无额外重试、原结果不变。

新隔离`staged_rear_transport_retry`72文件，默认关闭`--rear-transport-feasible-retry`，规划与实测两个入口接线，原问题/220迭代/1e-12/单次额外初始化和原全部几何门保留。CHECK实际左右collector选择与10反例过；新独立retry metadata审核已接pose，26份原导入/来源/报告适配可逆，完整10条件审核清单一致、8未选分支native与2完整front pose原输出一致。源码绑定拒绝旧run冒充新run。

**当前真实后台：** `rear_transport_retry_physical_r1`，runner **3125394**、collector **3125569**、watcher **3125542**，本文写入时均/proc活。pipeline 0/10、当前layout 840004；3113冻结来源不得原位改。首840004盒完整1200，任务+pose通过、推进285.026625mm、非目标0mm、首q/action零/assist0，实际8RGB4外视已看并绑定；剩余完整控制审核待完成。未选新retry分支，是原成功对照而非收益。124实际采集来源与新flag/force0已核。固定同8推2wait、seed/参数/1200或70/5N不变，只增一次retry。preflight通过；保留逐组空间门和所有原审核。

**新证据要求重新评估恢复触发时机：** `REAR_RECOVERY_TRIGGER_SPECIFICITY.json`扫原48推，原数值quality35过；10rear选中里，20mm入口会命中7例，**其中4例原本数值任务成功**。840004袋首次258，过去30步已真实推进32.0197mm，原后30步还推进10.5459mm，末300.7269mm/非目标0。因此强制恢复可能打断正在有效的侧推；不能把所有问题归为恢复阶段接触摩擦，更不能不断提高X补偿或余量。这里仅数值quality标签，840007盒等仍受原完整控制/组审核约束，不能将此筛查当训练准入。
另一个明确只用过去30步、同bout连续top_push+实测载荷、目标进度<.1mm的入口筛查`REAR_ENTRY_MEASURED_STALL_SCREEN.json`在这10原rear上**0触发**：避免了原成功干预，但同样没覆盖失败，**不是可直接采用的新策略**。三个初始接近失败仍不在该有载入口范围。屏幕后30步只作历史描述，绝不能变控制输入。

存储：只对不可变源码归档逐hash去重并保留所有路径释放.7803GiB；可重建pip包缓存和Warp编译缓存清理1.3566GiB，全部原始数据、checkpoint、模型、审核/fixture保留。两份操作清单分别`REAR_TRANSPORT_RETRY_SNAPSHOT_DEDUPLICATION.json`与`REAR_TRANSPORT_RETRY_REBUILDABLE_CACHE_CLEANUP.json`，启动前约30.07GiB，未降低原空间门。

**继续执行：**
1. 接续同一新物理run、不重启；落盘后用`review_rear_transport_retry_stage_episode.py`/incomplete版做真实8RGB4外视审核并独占写绑定，全10完成后`close_rear_transport_retry_physical.py`收尾。重点看529是否真实越过、之后能否持续推进，及恢复是否继续损害袋子。短例/新增失败全部保留。
2. 暂不直接把近停滞卸载候选并入物理；它不能消除过早介入问题。继续从全原rear数据区分有效推进、真实阻挡、达到极限与末段可达性，设计保留有效原动作的受约束恢复入口，不能用类别/布局ID特判或凭空松保护。
3. 840015原失败1053是最终肘名义间距4.7444mm低于原5mm；已有joint-edge版完整1200推进277.7493mm仍未达目标，单纯恢复X不是已证明的原因修复。前侧旋转与3初始接近、完整12train/validation组、共享训练、独立h10多seed/实际模型图审仍未完成。

以下历史以本段最新实际证据为准。

## 2026-10-02T14:34:17.411833+00:00 跟踪补偿袋仍失败；盒529短例定位为方向见证迭代耗尽，独立一次重求解可过但未接物理

本轮 **progress**（上轮也是progress），goal active未完成；整个原目标和训练/验证完整组、无助推、首零后双臂/腰yaw、非目标全过程15mm、原h10/质量门及独立模型验证全部保留。0新增合格训练数据/转换/模型。

**当前后台继续同一run：** `rear_tracking_physical_r1`，pipeline **6/10**，runner **3088459**、collector **3104994**（layout 840014）、watcher **3088618**，本段写入时/proc活。审核已执行101次，其中16失败，当前失败全部来自529短盒，不予豁免。3060冻结源码不可修改，不要重启live run。当前6条落盘均实际图审绑定：840004两推、840015两推、840005两推；其余继续。

**坏结果：**
- 840004袋完整1200仍失败，推进 **77.273272mm**（latched74.816491，原成功300.726861），非目标0，首q/u0，assist0。**926/1200加载恢复**、782补偿、141超域回原loaded求解、3无前次；0卸载。前两个phase分别257→356和364→491退出较快，500后一直保持到末尾。实际图像目标左缘裁切，685起抽样RGB两物体均画外，不能推断其几何。
- 独立同帧材料点：补偿步名义X中位 **1.052148mm**，实际 **.0109997mm**，物体 **.0010729mm**。583/782步预测X贴近.1mm下限，而新实际X预测误差均值 **.0958009mm**（旧固定轨迹约.0023mm不再适用）；56次X超1.5mm、85次Y超.5mm。载荷中位4.309N。数据证明补偿使实际点更常正向，但仍极低效，不能称解决任务。见`REAR_TRACKING_PHYSICAL_EFFECT.json`和`REAR_TRACKING_FLOOR_AND_DOMAIN_FINDINGS.json`。
- 840015盒 **529帧短例**失败，推进 **69.517288mm**。125加载恢复/100补偿/21超域/4无前次；397先触发真实卸载，529在已实际无载、接近末端时因 `measured_rear_transport_unverified` 停止。不是没有抬手或没有到达。原1200条件分母保留，短例原审核失败全部保留，不可补成成功。
- 840015前侧袋完整1200仍失败，推进 **140.258390mm**；原front旋转/桌面通道问题未解决，非目标0。此分支没有因rear补偿自动变好。

**好结果但不算新增改进：** 840004盒完整过，推进284.018114mm、非目标0；840005袋150.440589mm、盒150.008246mm完整过且非目标0。三条实际8RGB4外视已看；840005成功目标后半大量裁切/画外。完整质量与图审不能代替整体模型结果。

**盒停止原因有具体修复候选，未改live：** `REAR_TRANSPORT_STOP_FINDINGS.json`及`REAR_TRANSPORT_FEASIBLE_RETRY_FAILURE_CHECK.json`从真实529上下文完整复现原SLSQP status9、220迭代耗尽。旧candidate名义+X1mm、几何和final guard已过，但solver未收敛，因此原停止正确。新`rear_transport_feasible_retry_candidate.py`默认off，只在status9且原几何可行时，从这个候选点再求解**同一问题一次**，原220/ftol1e−12、所有边界、scene及插值路径门都保留；新返回status0并通过原独立`verify_witness`，3路径点，手-物间距53.0345mm、肘间距49.0349/138.6898mm。原失败保存在retry元数据里，未把status9伪装成功。
`REAR_TRANSPORT_FEASIBLE_RETRY_REGRESSION.json`固定12个原成功上下文（双手×规划/实测×首中末），off完全一致、启用时未触发retry且原输出完全一致，原独立路径审核过。只解决数值见证边界，**不是新物理交接成功或加载牵引证明**。该候选及新诊断文件都在run冻结之后新建，尚未collector接线。

**袋停滞卸载仍只是候选筛查：** `screen_measured_rear_recovery_stall_v2.py`在同phase/同contact、过去30条已真实提交loaded命令后，按实测旋转投影重建剩余通道距离。先前.5mm/30阈值在436仍慢速前进时就触发，V1报告保留；保守V2仅要求30步至少.1mm（原单步最小名义量），首次 **581**：剩余1.08051→.991646mm，改善.088864mm，目标X仅+.008762mm，大部分来自旋转半径减小。旧latched袋/盒V2均无触发，所以这个规则不是所有低效恢复的通用解决办法，不能夸大。
`rear_corridor_measured_stall_unload_candidate.py`使用明确`measured_recovery_stall`原因，绝不伪造原loaded求解失败；原垂直卸载优化数学保持，新增实际witness字段守卫。`MEASURED_STALL_UNLOAD_PROBE.json`在真实581输入独立FK/所有低点顶点抬升/原关节双肘/KKT通过，5坏witness拒绝。**仅一个无仿真探针、无状态提交、无后续交接**；盒的实际交接数值问题表明不能直接接线部署这一策略。

**下一执行：**
1. 继续当前余下完整条件的实际审核/图审，用`review_rear_tracking_stage_episode.py`/incomplete版与`close_rear_tracking_physical.py`收齐全10。短盒失败/未完成pending不可用原full audit通过替代。
2. 优先把一次有界方向见证重求解接入隔离版本的规划和实测交接两个入口，保留显式flag/来源/独立路径证据；必须复现实际529完整生命周期，不能只通过一行witness。
3. 再把实测近停滞的历史observer、实际commit/reset/卸载/重新接触生命周期和独立native串齐；不把前30步原未来结果当候选将来轨迹。组合策略要通过完整同组新物理，不能放松约束或加大bias上限冒充解决。
4. 仍须解决front旋转/3初始接近、原12完整train/validation配对、转换共享训练、独立h10多seed及实际模型图审。当前诊断完成或单步证明都不是整体目标完成。

以下历史记录以本段最新实际证据为准。

## 2026-10-02T14:04:57.639460+00:00 保持阶段完整仍5/8；新因果跟踪补偿完整10条件物理已启动

本轮 **progress**，goal active 未完成。上一goal轮有实际诊断/实现进展；随后Git备份任务已完成，本轮回到整体分拣目标。全部多样完整类别交换配对、首11维q/action零位后双臂/腰yaw可动、非目标全过程15mm、无助推、原h10/其余质量门、独立192推3wait多seed及实际模型画面要求保留。没有新合格数据入库、转换或共享模型。

**坏结果已经正式关闭：** `rear_latched_physical_r1/RESULT.json` 为完整 **5/8推、2/2wait**，原基线6/8；reverse07是2/4，diagonal02是3/4，两个组全部拒绝。10实际8RGB/4外视（wait无外视）均已看并绑定；部分成功目标后期裁切/画外，不能以数值通过声称全程视觉可见。194原审核、2968冻结来源已核。840004袋推进 **74.816491mm** 失败（原300.726861成功），840015盒 **61.176307mm** 失败，840015袋 **139.700670mm** 失败；三例首零/assist0/非目标0mm。袋915恢复步、5次切换，减切换没有恢复有效推进。

**审核缺陷与物理失败分别保留：** 原194审核中28失败，原因是从四元数重建几何后exact error比较遇到最大约8e−17舍入差；原结果未覆盖。独立V2用经过独立校验的序列化几何核精确元数据，原实际几何/关节/1e−6 KKT门不变；28完整补充审核全部通过，6个错误元数据反例拒绝。`RESULT_WITH_SUPPLEMENT_V2.json`绑定原失败、全部补充与10图审，无未解决审核项；任务5/8不变、两组拒绝不变。不要引用此前文档“原审核0失败”。旧runner3050751/watcher3050877/supplement3065980均已/proc missing。

**新候选原理及有限证据：** `rear_recovery_tracking_observation_v2.py`只用当前实测q和上一实际提交命令，在同一当前材料点计算FK跟踪残差；连续步、同手、同接触bout、真实commit/phase才可用。X偏差绝对值≤1.5mm、Y≤.5mm，超域拒绝而非裁剪；Z不补偿，原压力不变。`rear_recovery_tracking_solver_v2.py`把预测实际Y约束为0、预测X仍.1–2mm，名义X额外限3.5mm，原关节/动作/双肘/核心边缘/表面法向/非目标保护不变，并加名义桌面边界检查。这里确实改变原名义Y=0的控制约束，必须以新物理对照验证，不能冒充原控制数学完全相同。
历史预测误差袋X均值约.0023mm、盒.0036mm，相对原约.64/.62mm跟踪损失很小；这是因果预测诊断，**不是已证明实际补偿有效**。恢复后旋转/后退吞掉通道余量的问题仍保留。

**新接线与独立审核已完成：**
- `staged_rear_recovery_tracking/PREPARATION.json`从latched可逆复制，`--rear-recovery-tracking`默认off，必须依赖原diagnostic recovery+hysteresis。实际collector直接读取上一条已提交record，不改仿真物体或外力。
- `CHECK.json`2400关闭身份保持、14实际adapter/collector选择及phase提交、压力状态不变；全实际加载历史袋912+盒910可用、0超域，其余3+6为无连续前次。5CLI情况和非法commit拒绝。
- `REAR_RECOVERY_TRACKING_RECORDS_CHECK.json`14独立FK/完整记录及原1e−6 KKT过，10反例拒绝。V1历史commit=None接受缺陷及失败报告保留，V2已修且check通过。
- 新native的4个fallback文件夹具（含卸载/实测交接/wait）和2个连续请求夹具通过，分别21与10反例拒绝。这6个明确是 **合成文件、非物理轨迹、不可训练**。
- 来源检查68stage文件、可逆collector/adapter/原helper和所有前置checks；旧run拒绝被标成新run。27份原审核只改导入/来源/报告名，`REAR_TRACKING_ORIGINAL_AUDIT_CHECK.json`10条件清单一致、8未选rear流native原样、2完整front pose原样。新分支自身使用独立tracking auditor而不是伪造parent输出。

**当前真实后台：** 新 `rear_tracking_physical_r1`，runner **3088459**、collector **3088655**（840004）、watcher **3088618**；本文写入时均/proc活。pipeline 0/10，原10条件顺序840004/840015/840005/840014/841002/841007；仅新加tracking，参数/seed/1200或70/5N等不变。启动检查通过，冻结 **3060来源**；此时所有W根.py和新stage不可原位改。当前新增代码不少但均是隔离候选，未改生产源。初始约30.13GiB，通过原30GiB启动门且继续逐组空间检查。

**下一操作：** 接续此live run，不重启；先看840004袋和840015盒实际+X、恢复步数、任务推进与另一物体全过程峰值。完整落盘立即用`review_rear_tracking_stage_episode.py`（短例用incomplete版）做数值/实际画面绑定，原全部审核自动跑。全部10结束用`close_rear_tracking_physical.py`正式收尾；任何新失败完整保留，不能只挑成功条目扩采。若补偿未转成真实牵引或导致退化，拒绝此候选；不能只扩大偏置/门限。还需解决持续侧推旋转、前侧通道和3初始接近，然后回原12完整train/validation组、转换共享训练、独立h10多seed模型验证。整体目标未完成。

以下历史记录以本段最新实际证据为准。

## 2026-10-02T13:12:33.475289+00:00 新保持阶段袋子完整仍失败：326→5次切换，915步恢复吞掉推进时间；当前全组继续

本轮仍 **progress**，goal active未完成。`rear_latched_physical_r1`已完成pipeline **2/10**；runner **3050751**、collector **3057009**（layout 840015）、watcher **3050877**均/proc活。审核已执行24次、失败0次，当前None；整体审核尚未关闭，不得重启现有run或更改2968冻结来源。

**坏结果与明确的干预结论：** 840004袋完整1200原任务失败，推进 **74.8165mm**（旧恢复版76.0459mm，原基线成功300.7269mm），非目标 **0mm**，首11维q/action0、assist0，实际8RGB4外视已看并绑定。黑袋左缘严重裁切、木盒171后画外；原pose与完整审计需分开看，不能用画面推断毫米稳定。
新阶段从257触发，在513/838/1190实测退出，521/848再触发；**总分支切换降为5次（旧326），915步加载恢复、0卸载**。最终phase inactive，但任务失败，证明减少切换本身不足。`REAR_LATCHED_PHASE_OUTCOME.json`按全部真实时间线计算；不要误用只筛active帧得到的0次切换。

独立FK同帧冻结点名义+X中位 **.596465mm**，实际中位 **−.006812mm**，物体中位−.001192mm；载荷中位5.00012N。新恢复初期确有前移，915恢复步物体X合计+2.66725mm，但大部分时间仍用于极低效恢复，未转成成功分拣。见该episode `REAR_RECOVERY_STALL_FINDINGS.json`。

**退出后丢余量已有分解证据。** `REAR_LATCHED_REENTRY_FINDINGS.json`：513→521仅8步，通道缺口增长2.67238mm，其中袋旋转投影X半径增加 **1.59705mm**、袋X后退 **1.07533mm**，只侧向推进3.37416mm；838→848仅10步，缺口增长2.32141mm，其中旋转半径 **1.82162mm**、后退 **.49978mm**，侧推进5.22722mm。另一物体平移0。因此不能把失败仅归为小阈值抖动；还需解决持续侧推时的旋转/后退及真实有载跟踪，不能继续单纯加退出余量。

**好但非新增收益：** 840004盒完整1200通过原task+pose，推进283.6239mm、非目标0mm、首零/assist0，实际8RGB4外视已核且两物体抽帧可辨；rear记录0行，是原成功且新分支未选对照，不是候选改进证明。

下一继续困难840015盒和其余同10条件原审核/真实图审；全组收尾仍用 `close_rear_latched_physical.py`，所有失败保留。本轮新增独立关节跟踪、phase统计与旋转/平移分解已落盘。当前不改正在跑的策略；全组对照结束后，应集中验证有载实际执行效率及持续侧推通道保持/物体旋转，保留原约束，避免再走只改滞回宽度的循环。原前侧旋转、3初始接近、12完整train/validation组、共享训练及独立h10多seed模型验证均未缩小，仍0新增合格数据/模型。

以下为历史记录，以本段最新实际证据为准。

## 2026-10-02T13:03:28.736286+00:00 新保持阶段完整10条件物理已启动；独立审计接线完成，快照去重释放3.89GiB

本轮 **progress**；上轮也是progress。goal active未完成。整体共享RGB+upper11指令、多样类别位置解耦完整配对、首零后双臂/腰yaw可动、非目标全过程15mm、无助推、原h10及其余门、独立192推3wait多seed/实际模型目标全部保留。0新增合格训练数据、转换或共享模型。

**上版差结果仍保留：** `rear_corridor_physical_r1/RESULT.json`完整5/8推+2/2wait，比原基线6/8退化；840004袋300.73→76.05mm且失败、840015盒249.75→54.38mm仍失败，两个组均拒绝。全部194原审核和10实际图审已正式关闭，没有把好条目单独入库。

**新独立审核已完成并通过启动前检查。**
- `audit_rear_corridor_latched_phase.py`不导入候选，逐帧用真实输入重建原20mm触发、实测22mm退出/已沿Y越障、原mode/contact优先、进入步和commit时间线。`audit_rear_corridor_latched_records.py`保留原几何/关节/边缘/状态提交检查，显式新增有效缺口；`audit_rear_corridor_latched_native.py`调用独立phase及原1e−6新目标KKT，原实际previous action/卸载/压力/实测交接全部保留。
- `REAR_CORRIDOR_LATCHED_NATIVE_FIXTURE_CHECK.json`4完整文件格式夹具（3×1200+wait70）、3597阶段行、加载袋/盒与卸载交接通过，21异常拒绝。全部是明确合成、不可训练，不能称物理成功。
- `REAR_LATCHED_HELD_NATIVE_CHECK.json`另一个1200格式夹具，使用实际盒214触发/217原缺口已消失的两个固定输入，新动作/1199阶段/独立KKT过；4假退出/伪进入/关flag/错目标拒绝。这也是合成稀疏夹具，不是新物理反事实。
- `rear_corridor_latched_source_binding.py`完整逆向还原新stage→原GUARD→原祖先，检查65stage来源、61原helper不变及所有前置证据，原参数profile只显式增加新开关；实际运行来源也已核验。
- `REAR_LATCHED_ORIGINAL_AUDIT_PREPARATION.json`27份原审核模块只改可逆入口/来源/报告名，原数学不变。`REAR_LATCHED_ORIGINAL_AUDIT_V2_CHECK.json`全部10条件适用清单原样对应、8真实未选rear流native输出一致、840005盒/袋各1200完整前侧pose原输出一致。初版比较因新增空phase元数据失败已保留；V2明确核空phase与初始state后比较全部原字段，未改审核门。

**真实后台正在运行，接续不要重启：** runner **3050751**（`run_rear_latched_physical.py`）、collector **3050909**（当前840004）、watcher **3050877**（`watch_rear_latched_physical_audits.py`），本段时间均/proc活。新目录 `rear_latched_physical_r1`，原完整8推2wait，顺序840004/840015/840005/840014/841002/841007，其余原布局/seed/1200或70/5N/相机等参数逐项相同，只加 `--rear-corridor-hysteresis`。`rear_latched_physical_preparation_r1/LAUNCH_PREFLIGHT.json`通过，冻结2968来源；此时已有的W根.py与stage源码都不可原位改。
首case `EARLY_SOURCE_CHECK.json`核117实际来源，新开关启用且外加push/wait force0；原raw首零/assist0/控制/任务/实际图审仍在落盘后核验。目前pipeline计数0/10，审核0，不能把进度图或单条件当完整成功。

**原因进一步具体化（原失败实录，并非新分支结果）：** 新 `analyze_rear_recovery_joint_tracking.py`按独立URDF FK分解每帧冻结支撑点跟踪差。旧袋779恢复步，左肩pitch/roll的平均X损失−.8243/−.5218mm，肘补+.6401mm；旧盒694步，右肩−.8302/−.4644mm、肘+.6446mm。FK局部线性残差最大袋.00690/盒.00238mm，说明名义0.63–0.65mm很容易被实际关节跟踪差抵消；这不是认定摩擦/驱动器唯一因果，也不是可直接加补偿的校准。两条episode已保存 `REAR_RECOVERY_JOINT_TRACKING_FINDINGS.json`。若新phase保持但仍不动，下一要看真实牵引/跟踪和指令累积，不再忽略小缺口或放松原门。

**空间已解决且证据保留：** 仅对`source_snapshot`/`runtime_source`/`substep_runtime_sources`不可变历史快照做逐字节SHA256核验后的hardlink去重，保留6723路径，5450路径合并同内容副本，释放3.888GiB。live stage/原始数据/模型/报告均未删；少数mode不同项跳过。见`REAR_LATCHED_SNAPSHOT_DUPLICATE_INVENTORY.json`、`REAR_LATCHED_SNAPSHOT_DEDUPLICATION.json`。这些快照禁止原位编辑；新工作写新目录。当前free=32.19GiB，原30GiB启动门已满足。

下一：继续同一live run，落盘即用 `review_rear_latched_stage_episode.py`（短例用incomplete版）核原门和实际8RGB/4外视，完整审计自动运行。首关注840004袋退化是否恢复与840015盒实际+X能否留足余量；用 `close_rear_latched_physical.py`收齐全10后关闭，所有失败保留。单例成功仍不能训练；其余前侧旋转/3初始接近问题和原12完整train/validation组、转换共享训练、独立模型验收继续。

以下为历史记录，以本段最新证据为准。

## 2026-10-02T12:37:04.674850+00:00 后绕恢复完整对照关闭：5/8低于基线6/8；新保持阶段已接线、尚未新物理

本轮 **progress**，goal active未完成。原共享RGB+upper11按物体/指令、多样完整类别交换组、首零后双臂/腰yaw可动、非目标全过程15mm、无助推、原h10及其余门、独立192推3wait多seed/实际模型验收全部保留。无新增合格训练数据、转换或共享模型，不能将诊断成功条目单独入库。

**坏结果已正式关闭。** `rear_corridor_physical_r1/RESULT.json`全部10条件完成：**5/8推+2/2wait，原同条件基线6/8推**。reverse07仍2/4；原成功diagonal02从4/4退至3/4，两个完整组都拒绝准入。194次适用审核全过、2924冻结来源核验、10条真实图审绑定全部完成。这说明控制/质量审计通过不等于分拣任务成功。runner3008374、watcher3008503、最后collector3032356均已/proc missing；当前没有这个run的后台采集或审核，不要重新启动它。

**关键退化：** 840004后绕袋从原成功推进**300.7269mm**降为失败**76.0459mm**，末10signedY最低−18.8770mm；779恢复步、0抬手、非目标0mm。独立URDF FK同帧冻结支撑点名义+X中位.651858mm，实际中位**−.013620mm**，物体中位−.002205mm；载荷中位4.99918N，不能说无加载。258以后326次分支切换，恢复动作物体X累积−1.72365mm、Y−12.39493mm；原分支X−.83858mm、Y+7.07417mm。因此除了切换，还存在实际跟踪/牵引不足；保持阶段未必单独解决。见该episode `REAR_RECOVERY_STALL_FINDINGS.json`/`REAR_RECOVERY_SWITCHING_FINDINGS.json`。实际8RGB4外视已看，袋左缘、木盒左下裁切如实记录。

840015交换盒从原失败推进249.7452mm降为失败54.3783mm，694恢复、579切换、非目标0mm；840015前侧袋仍失败138.6471mm。其余原成功对照和两等待通过，但不是新增收益。

**新候选已有真实实现与组件证据，尚无物理结论。** `rear_corridor_latched_phase_v2.py`保留原20mm缺口触发，仅在实测达到22mm或已沿Y越过障碍才退出；原mode/contact/first-load保护优先，卸载与实测交接生命周期保留。`rear_corridor_latched_solver.py`显式2mm退出余量，不伪造物体位姿、不放宽间距/关节/压力/原KKT；`rear_corridor_latched_adapter.py`仅在原最终命令保护通过后提交phase，记录before/after/真实几何，禁止旧状态、重复或篡改命令提交。

`REAR_CORRIDOR_LATCHED_CANDIDATE_V3_CHECK.json`已完成两条真实后绕问题流2398帧独立阶段复算、14抽样实际求解动作FK/双肘/关节/原1e−6 KKT，全部通过；旧边界后继续保持的历史输入分别袋163/盒292帧。这只是固定输入检查，不是新物理反事实。V1合成边界浮点字面值问题、V2初始coord无active_side的失败均保留；V3明确传任务side且核存在时一致，未改原20mm门。

`staged_rear_corridor_latched`独立采集器已生成，新增 `--rear-corridor-hysteresis` 默认off、必须依赖原recovery诊断合同；可逆差分核验父源，未改已关闭run。其 `CHECK.json`实际CLI4种设置、2400关闭身份保持、14真实RearCopRouteState提交与提取的collector phase-commit AST全部过；压力bias/filter/recontacts不变，3类非法提交拒绝。检查PID3038862已退出。

**下一执行顺序：**
1. 补独立native全轨迹phase重建与新目标KKT接线（现在旧审计只允许原deficit>0，不能直接给新phase开豁免）；检查phase跨卸载/实测交接、未执行stop不得提交，复用不变原保护和数学。
2. 接新stage来源合同/原审核适配，补必要反例与原成功/前侧/等待的默认off回归；这些是新分支正确记录与审核，不能扩大为无限诊断替代物理实验。
3. 固定同10条件完整物理对照：优先840004退化袋和840015困难盒，保留原组全部任务与相同seed/步长/载荷/相机；只改phase，明确检验实际+X牵引、切换、目标推进、非目标峰值。若保持但依旧实际反向或停滞，应转向实际执行跟踪/有载恢复策略，不能再调成功阈值或只增加示范数量。
4. 仍须解决前侧旋转和3条初始接近，回原12完整train/validation组；合格完整组后转换、共享训练及独立模型验收。当前0新模型，整体目标未完成。

当前没有本轮采集/训练后台任务；所有已列检查已结束。free=28.58GiB；未删证据。后续新物理仍须检查原启动空间预算，不能因上轮已能运行而跳过。

以下为历史记录，以本段最新证据为准。

## 2026-10-02T12:10:40.356417+00:00 关键交换盒完整失败：694次恢复、579次边界切换相互抵消；全10对照继续

本轮 **progress**，goal active未完成。最新真实进程：runner **3008374**、collector **3020822**（layout 840004）、watcher **3008503**，均/proc活。`rear_corridor_physical_r1`已完成pipeline **5/10**，落盘6条；已实际图审5条，审核91次、已记录失败0次，当前`audit_rear_corridor_stage_pose_task_optimality.py`。尚未关闭全组，勿重启或改冻结源。

**坏：新恢复没有解决关键盒子，进度明显不足。** 840015盒完整1200，原任务失败：推进 **54.3783mm**、末10signedY最低 **−48.9495mm**，仍远未到右侧区；非目标最大XY **0mm**。首零/assist0与原pose要求保留，实际看8RGB4外视并绑定。新增有载恢复 **694步**，首214、末1198，**0抬手**，pending=false；这不是成功示范，禁止入库。视觉后段手盒基本滞留，袋画外/严重裁切。

**原因已有完整轨迹证据，仍待独立干预验证。** `case_840015/layout_840015_push_box_to_bin/REAR_RECOVERY_STALL_FINDINGS.json`用独立URDF FK复算同一帧冻结支撑点：所有694次缺口仅0.0000156–**0.042485mm**，中位 **0.013859mm**。名义+X位移中位0.630865mm，但真实冻结支撑点中位仅0.020381mm，物体中位0.007451mm；垂直滤波载荷约4.997N，不能归因于完全没加载。每次状态提交消掉原向目标方向的lead，中位1.5722mm（首例9.4444mm），反复阻断侧向累积。名义位移累加不是同一实物点轨迹，最后tick力也不冒充24substep完整审核。

`REAR_RECOVERY_SWITCHING_FINDINGS.json`更直接：214以后 **579次分支切换、290段恢复（每段仅1–3步）**，292次unchanged均为no_rear_corridor_deficit。恢复步物体X累积 **+5.3798mm**、原分支步 **−5.8771mm**，净 **−0.4973mm**；Y分别+10.4639/−9.7096mm，净+0.7543mm，与停滞一致。下一应隔离检验**带状态的恢复阶段：原20mm缺口触发，实测恢复到额外退出余量才结束**，防边界抖动；不把阈值放宽来忽略缺口，不更改当前run，不以旧轨迹重放预测新物理。X约束/压力/原task KKT与全组比较仍必需。

**其余已完成条件：** 正常840014盒/袋各1200原task+pose通过，推进150.2946/150.2198mm、非目标0mm、首零/assist0，都是无新增rear恢复的原成功对照，不能算收益；交换840015袋1200仍失败，推进138.6471mm、末10signedY40.6674mm、非目标0mm，原前侧问题保留；841007wait70通过且8RGB实际空桌/手稳定。上述5条均已有数值及真实图审绑定；黑袋对照后段画外/其它裁切风险如实记录，不新增全帧可见硬门，也不能用数值过来宣称模型视觉过。

继续剩余diagonal02成功组4推+wait和原全审核，完整关闭8推2wait后才决定下一版；这是诊断，不授予任何训练准入。整体原12完整组/类别位置解耦/非目标全过程15mm/首零后双臂腰/无助推/h10/共享训练/untouched192推3wait多seed实际模型目标均未缩小，仍无新增训练数据或模型。free=29.45GiB，V4保留原启动30GiB并用剩余任务预算+25GiB保证持续写入，未删除原始证据。

以下为历史记录，以最新实际证据为准。

## 2026-10-02T11:50:35.776856+00:00 后绕恢复完整物理8推2wait已启动；2388事件审核通过，首原成功对照通过

本轮 **progress**，上一目标轮也是progress；goal active未完成。共享RGB+upper11指令、多样完整类别交换配对、首零后双臂/腰yaw可动、非目标全过程15mm、无助推、原h10及其余门、独立192推3wait、多seed与实际模型验证均不变。无新增合格训练数据、转换或共享模型。

**好：完整事件核验正式结束。** `REAR_CORRIDOR_TRANSPORT_EVENT_CHECK.json`全部11历史流、2388执行事件、45规划方向见证和45实测交接完成passed，PID2982911已missing；原失败/短例未补齐或准入。此前所有native、状态、KKT、方向、原27项/新增native28清单及压力transition检查都已完成。`run_rear_corridor_physical_v4.py --check-only`实际通过，已写`rear_corridor_physical_preparation_r1/LAUNCH_PREFLIGHT.json`。这是启动条件，不是任务完成。

**物理进行中，继续这些进程，不要重启：** runner **3008374**、collector **3008536**（840014）、watcher **3008503**，本段时间均/proc活。新目录`rear_corridor_physical_r1`，固定reverse07失败组与diagonal02成功组，共8推2wait，原5N、1200/70、环境seed/相机/布局不变，不混front interval或edge intersection候选。`PROTOCOL.json`冻结2924源，现有W根.py与stage源禁止原位修改；后续修正用独立版本。首case `EARLY_SOURCE_CHECK.json`实际核114来源。

**首例数值与实际图审已完成，控制全审尚待。** 840014盒1200帧原task+pose过，推进150.2946mm/末10signedY248.2744mm/非目标0mm，首11维q/action全0、assist0。`rear_corridor_recovery.json`0rows，属于原本成功的无恢复对照，**不算候选新增收益**。实际看了8RGB4外视并写`ACTUAL_REVIEW_BINDING.json`：袋全抽样可辨，盒513起右缘裁切，末段仍部分可辨；视野风险留给真实模型闭环，不擅加全帧可见硬门。同case袋正在采集；runner的完成条件计数须等整case退出后推进，目前已落盘1条，pipeline计数0，不能混淆。

**空间检查纠正，仅运维而非质量门。** 现有计划只要求启动至少30GiB；此前脚本每case仍要求30GiB，会在正常写入后误停。新`rear_corridor_storage_budget.py`保留启动>30GiB，给4双任务case各1GiB、2wait各.25GiB（总4.5GiB），每case要求剩余预算+25GiB保留，7阶段与不足空间拒绝已检查。版本V4及watcherV4绑定该变化，未改任何数据/接触/质量门。`REAR_RUN_STORAGE_DUPLICATE_INVENTORY.json`只读检查无可去重的大文件，未删除唯一历史文件。当前free=30.66GiB。

**差结果/原因进一步具体化：** 原三条“初始接近失败”其实并非无接触：840008盒/袋、840016袋始终停在rear_push预定位，目标已有135.9–182.1mm最大XY位移，但rear_clearance_measured=false，0region rows、未进top。末段腰为±.98rad附近；配对交换840009盒/袋、840017袋原全部通过，最大腰分别.389/.381/.781。见`INITIAL_REAR_APPROACH_REFERENCE_FINDINGS.json`与`INITIAL_REAR_APPROACH_SWAP_COMPARISON.json`。控制点与物理最低支撑点Z差约40–67mm只是诊断线索，不是单一因果证明，更不证明全局不可达。实际重看困难840008盒8RGB4外视：初始类别交换可辨，随后袋画外、盒右裁切，见`INITIAL_REAR_APPROACH_BOX_VISUAL_SUPPLEMENT.json`。下一需评估预定位路线/实物接触参考与当前关节范围内可达性，不能只补数据或放大腰范围。

下一继续当前完整10条件，重点840015交换盒是否真正恢复通道并避免物体互撞；原前侧旋转袋和三条预定位失败未解决。完成全部原27+新native适用审核、实际画面、完整组对照后才决定是否扩至原12组；诊断run本身不授予训练准入。足量完整train/validation才转换/共享训练并进行原范围独立模型验收。

以下为历史记录，以最新实际证据为准。

## 2026-10-02T11:25:23.868064+00:00 原27审核适配完成，新增native必查；完整事件复核仍运行，尚无新物理收益

本轮 **progress**，goal active未完成。代码备份已另行确认，主目标继续：共享RGB+upper11按物体/指令、多样完整类别交换组、首零后双臂与腰yaw可动、另一物体全过程15mm、无助推、h10与其余原门、独立192推3wait多seed/实际模型画面全部不变。**仍无新增合格训练数据、转换或共享模型；原仅1完整train组5条与0合格validation。**

**好：审核接线完成并有具体回归证据，不是物理成功。**
- `REAR_CORRIDOR_NATIVE_FIXTURE_CHECK.json`4个完整长度文件fixture（3推1200/等待70）及14异常拒绝；明确合成、无物理、不能准入。
- `REAR_CORRIDOR_STATE_RECONSTRUCTION_V3_CHECK.json`全部11历史流新旧XY/高度结果一致，原短例拒绝保留；3显式commit前缀与4异常检查。初版/V2因历史短例未执行行触发旧IndexError/KeyError的失败文件保留，未删行/补帧。
- `REAR_TRANSPORT_WITNESS_INDEPENDENT_CHECK.json`45规划+45实测方向见证、176路径点独立复算。新版完整pose审核用 `audit_rear_corridor_transport_events_v2.py`，保留原compact scene拒绝。
- `REAR_CORRIDOR_POSE_BOUNDARY_V2_CHECK.json`3合成恢复边界与3原接近失败流；原姿态审核拒绝的三个例仍同样拒绝。初版测试错误期待这些失败流通过，保留失败报告。
- `REAR_CORRIDOR_PARENT_TASK_CHECK.json`袋/盒有载、盒抬手三类原KKT目标投影和真实上一动作约束检查，6反例拒绝。稀疏数学fixture不冒充完整轨迹。
- `REAR_CORRIDOR_FRONT_POSE_CHECK.json`和`REAR_CORRIDOR_FRONT_GEOMETRY_CHECK.json`840005盒/袋各1200帧，原/新完整姿态、真实几何/动作链及原任务KKT一致。只回归历史前侧无新rear请求路径，不是新物理对照。
- `REAR_CORRIDOR_PRESSURE_TRANSITION_CHECK.json`三类commit前缀按原24substep标量力重算，卸载清bias但保留filter及更新计数，9篡改反例拒绝；没有虚构新动作后的力。
- `REAR_CORRIDOR_AUDIT_INVENTORY_CHECK.json`原27 distinct均保留，增加native recovery成为28；压力标量/更新公式AST与原版完全一致。`rear_corridor_audit_inputs.py`先核独立native/KKT再提供本帧父目标，原raw q与上一实际u绝不替换；pending时间线包含交接帧、排除首次抬手帧。已适配XY、height、parent KKT、edge command chain、真实self-clearance、hold/terminal测量、pressure及source/profile绑定。

**仍待：** `check_rear_corridor_transport_events.py` PID **2982911**于本段时间真实/proc为R，已落盘 **1600/2388** 原记录事件；完整45交接和11历史流尚不能宣布结束。session29956仍为原检查，勿因观测超时重启。`rear_corridor_preflight_pending.log`保留启动前检查在该report=running处拒绝的记录。没有新Isaac采集或训练。

下一使用 **`run_rear_corridor_physical_v3.py --check-only`**，watcher **`watch_rear_corridor_physical_audits_v3.py`**、合同 **`rear_corridor_stage_run_contract_v2.py`**。V2修正旧edge最终状态名为带supplement独立纠正的正式状态；V3把压力transition完成设为启动必需。原proposal的launch_allowed=false保持历史，只有完整preflight通过才另写`rear_corridor_physical_preparation_r1/LAUNCH_PREFLIGHT.json`；当前尚无该通过证明，**不要跳过检查直接启动**。通过后新目录原失败reverse07+成功diagonal02完整8推2wait，不混front interval/edge intersection修复，原5N/1200/70、相机与seed不变。watcher、完整/短例reviewer与closure已版本化准备，actual review仍需实际看图。

**差结果仍清楚：** 最近front interval物理对照仍6/8+2/2，与基线持平；前侧旋转通道及840008盒/袋、840016袋三条初始接近未解决。后绕恢复仍未经新物理，不能声称任务效果提高。必须继续原12完整组及训练/独立模型验收，不缩成上述组件检查。free=30.95GiB。

以下为历史记录，以最新实际完成报告为准。

## 2026-10-02T10:32:19.638289+00:00 新恢复目标原1e−6 KKT全1943通过；完整native与27原审核适配继续

本轮progress、goal active未完成。继下段采集接线和组件检查后，继续补独立新目标KKT：`REAR_CORRIDOR_STATIONARITY_CHECK.json`全部1943完成（1693有载后移、250首次抬手），1943过/0失败，最大stationarity residual=2.98999390109e-08，原1e−6门未改。`rear_corridor_stationarity.py`使用独立HandModel FK和原双肘所有活动支持顶点证书；等式用双向法向，抬手最低高度用全手每顶点约束，保留原primal/active容差、当前与前动作bounds、原非活动臂/法向目标。固定历史输入不是物理反事实或数据准入。

`REAR_CORRIDOR_STATIONARITY_NEGATIVE_CHECK.json`两种命令均验证原命令过，篡改任务目标、非法动作和因果输入拒绝；篡改目标残差分别0.140802/0.082841，不是只看solver成功标记。审核PID2970972已/proc missing。新 `audit_rear_corridor_native_commands_v2.py`已将该独立KKT作为每个真实新override的必需条件，精确逆向初版见 `REAR_CORRIDOR_NATIVE_V2_PREPARATION.json`；**完整native文件fixture仍待实现，原27项状态/压力/路径审计适配仍未完成，不能物理launch。** 组件总检查文件只说明其当时完成范围，后补KKT以本段报告为准。

下一直接完成完整新native fixture与原后绕XY/phase/pressure/path审计适配，保留父控制目标重建和最终真实动作两层；再依固定 `rear_corridor_physical_preparation_r1/PLAN.json`运行原完整8推2wait，随后原12组全family。前通道旋转和三条初始接近失败继续保留，整体训练/独立h10多seed模型验收目标不变。目前无新物理采集/训练/新合格训练数据。

以下为历史记录，以最新完成报告为准。

## 2026-10-02T10:25:44.960780+00:00 后绕恢复已接隔离采集器并完成组件检查；补上待交接下压保护，原全轨迹审核仍待接线

本轮 **progress**；前一个目标轮也有实际代码/诊断收尾进展。goal active未完成，不是blocked或暂停。原共享RGB+upper11指令、多样类别交换完整配对、首零后双臂/腰yaw可动、非目标全过程15mm、无助推、h10及其余原门、untouched192推3wait和多seed/实际模型验收全部不变。仍只有旧1完整train组5条准入，0新增转换/共享模型，0合格validation。

**差结果正式收尾：** `front_interval_physical_r2/RESULT.json`在10:03UTC完成，全部10条件仍6/8推+2/2wait，与同条件基线6/8持平；reverse07仅2/4推，diagonal02原4/4推。184原审核、2803冻结源、10实际图审已核；短盒970帧失败及18原审核失败保留，不补齐、不拼接，不授予训练准入。原collect/watcher均已退出，旧pending文件仅为历史。

**好：新控制已接入真实隔离采集器，尚非物理成功。** 首版 `staged_rear_corridor_recovery`由原peak源可逆派生，默认关闭：原joint-edge后选已验证的+X/Y保持命令，最终原guard通过后才同步command/last_waypoint/push_x_anchor；若无验证有载命令则发经验证的首次垂直抬手，再调用原recontact复位、清压力bias并保持filter、计数+1。原父row/coord/action完整保留在新日志，专家模式和压力最终状态同步，禁止None回退成旧侧推。重新落点与实测交接加+X名义方向见证，未制造实际卸载或到达。

`staged_rear_corridor_recovery/CHECK_V2.json`真实解析器和全部11历史流完成：关闭13053action逐值/对象保留，1943请求实际求解得到1693后移与250首次抬手；独立FK/双肘/关节/slew/边缘复算，1693+250真实状态提交与45实测交接记录验证完成。首CHECK因遗漏既有OMNI_KIT_ACCEPT_EULA环境在导入阶段退出，失败原文件保留；V2仅另存输出并恢复环境，未改求解器。独立 `REAR_CORRIDOR_INDEPENDENT_RECORD_CHECK.json`也完成全部1943，动作/参考/压力/模式/物体位姿/因果/重复解等篡改反例拒绝。**这些是固定历史输入检查，不是反事实物理，更不是任务成功率。**

**发现并修复接线缺口：** pending恢复时，原lifecycle可能在未完成交接前返回unchanged，而父状态进入descend/press/push。新增独立 `staged_rear_corridor_recovery_guarded`和`rear_corridor_recontact_gate.py`明确拒绝该回退；原lift/withdraw/release及已验证路径保留。真实collector AST新增块覆盖8803历史事件：关闭17606组合、非pending8803保留身份；强制pending测试4311拒绝、4492保留。这是反例测试条件数量，不是物理中4311次失败。额外非法模式/类型拒绝。`COMPONENT_CHECKS.json`正式绑定全部报告与源码，父源码可逆，所有旧helper与全流已测首版一致；全部检查进程已退出。

新 `rear_corridor_stage_source_binding.py`已实际验证拒绝其它stage；`audit_rear_corridor_command_records.py`独立新增分支审核已全1943检查；`audit_rear_corridor_native_commands.py`已写完整文件绑定，但完整native fixture和原27项审计适配**尚未完成**。不能只更名旧审计：需重建父COP/XY并推进实际输出状态、独立新目标KKT、原压力reset与filter、真实phase/path/scene/待交接控制。

下一具体工作：按 `REAR_CORRIDOR_AUDIT_COVERAGE_PLAN.json`完成上述全轨迹审核和反例；再用 `rear_corridor_physical_preparation_r1/PLAN.json`固定原reverse07失败组+diagonal02成功组8推2wait，仍1200/70、5N、同seed/相机/布局，只新增后绕恢复，不混front interval或joint-edge intersection；当前launch_allowed=false且未启动。之后原12组全family，继续解决前通道旋转与3条从未进top的接近失败，完整train/validation准入后才转换/共享训练与独立模型验收。

实际状态：此前列出的collector/watcher/组件检查PID已逐一/proc missing；无新物理采集/训练，free=30.99GiB。此次Git代码备份已另外完成c90a490；当前工作继续分拣主目标，不应转回备份。

以下为历史记录，以本段和所引最终报告为准。

## 2026-10-02T09:49:55.052982+00:00 前通道全10采集/图审完成仍6/8；后绕恢复关节控制已实现并完成全流离线核验

本轮 **progress**，goal active未完成。原共享策略、多样类别交换配对、RGB+upper11、首零之后双臂与腰yaw允许、非目标全过程15mm、无助推、h10、全部原质量门与untouched192推3wait多seed/实际模型验收不变。仍只有旧1完整train组5条准入，0新增转换/共享模型，0合格validation；不得将下面的名义命令可行率当作任务成功率或数据准入。

**前通道物理坏结果正式明确，控制审核尚未收尾。** r2全10已采、全10数值与实际图审已绑定（交换盒仍单独970帧不完整review），`front_interval_physical_r2/TASK_POSE_VISUAL_COMPARISON.json`原任务6/8推+2/2wait，原同条件基线6/8。失败reverse07原2/4推+wait过，成功diagonal02原4/4推+wait过。只840015袋698–918的221步改变区间，其余7推0change；不能将成功对照算候选收益。袋仍155.555mm/末10Y57.575失败，yaw增大后919区间为空；盒仍970帧自碰拒绝/失败，不补齐230帧。原r1崩溃无择优拼接，r2完整条件不剔除。

新增完成实际图审：840004盒284.767/末10Y206.420mm，双物体8RGB可辨；袋299.938/205.048mm，513以后目标画外、另一物体大幅裁切；840005盒150.328/245.218mm，171起目标画外，袋全8可辨；840005袋150.262/228.610mm，目标后段左裁切仍可辨，盒全8可辨。四推均1200、非目标0、首零/assist0，原任务/pose过。841002wait70、全11action0、腰3.08717e−9、8RGB稳定。所有视野风险仍须真实模型验证，不新增全帧可见硬门。新 `close_front_interval_physical.py`可核全部10清单/原失败审核/短例/actual bindings/冻结源/完整组，只在全部结束后 --apply；已检查pending不写RESULT，不能提前宣布完整控制通过。

**好：后绕持续恢复已有可调用关节控制代码，非仅几何规划。** `rear_corridor_joint_recovery_candidate.py`默认关闭原命令逐值保留；启用时基于当前两物体旋转包络原20mm后通道，当前实测FK参考请求+X、名义Y保持，保留原任务Z/非活动臂/法向误差、11维限位/步长/slew、接触核心边缘约束（右手原0.5mm向内）、双肘5mm。模式/guard/terminal/首加载优先；当前与上一实测动作必须一致。失败返回None且要求单独经过验证的重接触，不发无验证旧侧推。仍**未接采集器**，无物理运动预测/通过声明。

首固定47请求38有验证命令/9无验证解。发现恢复量上限只设为缺口会在小缺口时与原右手0.5mm inward约束冲突，保留父结果；独立 `rear_corridor_joint_recovery_reserve_candidate.py`只将请求设为min(2mm,max(1mm,缺口))、额外检查请求后的5mm桌边，最多增加1mm恢复余量，不放宽原门。同47为39/8，8非法输入或保护反例均正确处理。

**全流差/好并列：** `REAR_CORRIDOR_JOINT_RECOVERY_FULL_CHECK.json`实际代码覆盖全部1943历史有载请求，1693输出float32命令经独立HandModel FK、IndependentElbows、关节/slew/方向/核心边缘检查，250未得验证解。无一个被solver拒绝的尝试满足全部几何残差，所以不能靠忽略solver状态接受它们；局部求解失败仍不证明全局数学无解。全部输入/源码哈希已重核，runner2944131已退出。`FULL_FINDINGS.json`（完整文件名 `REAR_CORRIDOR_JOINT_RECOVERY_FULL_FINDINGS.json`）逐轨迹保留；按类别 `REAR_CORRIDOR_JOINT_RECOVERY_CATEGORY_FINDINGS.json`：盒1454/1704名义命令可行，250全是盒；袋239/239，但这些有载袋轨迹本来任务成功，不能称修复了失败袋。原840008盒/袋、840016袋3条接近失败没有进入top，0请求明确保留、完全未解决。困难原/新盒224首恢复均可验证，原840023盒413首恢复仍无验证解，不能只挑困难新盒成功点。

下一优先实现**无验证解的重接触路径与成功后的状态同步**：现有状态机若内部Y目标在恢复时继续累计，会抵消恢复，必须将command/last_waypoint与实际输出参考协调；新pose选择还须确认能执行+X方向，不能仅因落点在几何内部就恢复侧推。完成源绑定/完整独立控制审核后再接隔离采集器，原失败完整组+成功完整组对照，然后原12组全family。前通道旋转控制/路线重规划和3原始接近失败仍需继续，不能借当前核心函数缩小目标。详见 `REAR_CORRIDOR_RECOVERY_IMPLEMENTATION_PLAN.md`。

实时/proc：[{'pid': 2923677, 'state': 'missing', 'cmdline': None}, {'pid': 2947893, 'state': 'missing', 'cmdline': None}, {'pid': 2923724, 'state': 'S', 'cmdline': '/home/user/miniconda3/envs/env_isaaclab/bin/python /home/user/Documents/zoo/sim/SimFoundry/demo/waist_enabled_20260929_r1/watch_front_interval_physical_audits.py /home/user/Documents/zoo/sim/SimFoundry/demo/waist_enabled_20260929_r1/front_interval_physical_r2 '}, {'pid': 2944131, 'state': 'missing', 'cmdline': None}]。前通道STATUS已10/10 collection_complete_audits_visual_pending，watcher已审核6/10，current=layout_840004_nudge_mailer_to_bin/audit_front_interval_stage_region_bounds.py，原失败调用数18（短盒18项，最终仍逐条核对）。free=31.02GiB。不要重启已完成采集；继续当前watcher，完成后运行close --apply。现有冻结源不可改，新增独立版本允许；未启动新训练。

以下为历史记录，以本段为准。

## 2026-10-02T09:31:16.745123+00:00 联合修复对照正式收尾；前通道实际触发仍失败，旋转使区间为空

本轮 progress，goal active 未完成。**好：诊断收尾与原因更具体；差：尚无任务成功率收益、无新增合格训练数据/模型。** 目标与所有原门不变，不以专家离线方向可行代替物理或共享模型成功。

`joint_edge_intersection_physical_r1/RESULT_WITH_SUPPLEMENT.json`已正式核验10条件：6/8推+2/2wait，基线也是6/8。184原审核调用逐条绑定，困难盒12原失败保留，11依赖V2+1压力V2另存并全部过；2746冻结源无变化，全10数值与实际图审完整。原collector/watcher/V2进程已退出，无需重跑。只关闭诊断证据，不准入训练；`TASK_POSE_VISUAL_COMPARISON.json`的pending为历史状态，以新RESULT为准。

**后绕早干预有方向依据，但不是物理成功。** `REAR_CORRIDOR_RECOVERY_DIRECTION_SCREEN.json`覆盖原10rear+新困难盒，1943个合格有载请求解析区间与独立LP一致，非push/guard/首加载保留。困难新盒224首次失去20mm余量时可请求+X0.524mm；699接触时只容许0.000437mm，1052方向无解。现有接触点晚期不能直接后移，需早恢复通道并处理重接触/全关节覆盖；三条原始接近失败从未进入top，不被此方案覆盖。具体实现顺序见 `REAR_CORRIDOR_RECOVERY_IMPLEMENTATION_PLAN.md`，尚未新物理接线。报告初次序列化numpy bool失败已修正并保留partial失败文件，不是物理采集失败。

**front r2首完整原定组已采5条件，原任务2/4推+wait过，交换两任务都失败。** 正常840014盒1200推进150.294mm/末10Y248.273mm、袋150.100/253.421mm，非目标0，原任务与pose通过且实际8RGB4外视已绑定；正常袋171仅左裁片，342起目标画外，盒末段严重右裁切，模型视野风险保留。841007空桌70全11action0/腰3.08746e−9、8RGB稳定已绑定。原首组边界崩溃未重现，当前继续第二完整组，不因两失败停止或剔除条件。

交换840015盒970提前终止，原最终自碰验证在step970拒绝4.794877mm（原5mm）；推进238.681mm/末10Y130.293mm，非目标6.819mm，失败缺230帧。新增 `review_front_interval_incomplete_episode.py`只做明确不完整证据/实际图审，不降低原完整1200审核；`FRONT_INTERVAL_INCOMPLETE_REVIEW.json`与ACTUAL已绑定。其原适用控制审核失败保留，不能补齐/缩分母。盒后段/袋均严重裁切，不据图推断毫米间距。

**交换袋实际区间修复698–918共221步触发，但919通道变空后保护停。** 完整1200推进155.555mm、末10Y57.575mm、非目标0，未到目标区，仍失败。`FRONT_INTERVAL_PHYSICAL_FIRST_FAILURE_FINDINGS.json`绑定原记录；独立SciPy完整旋转包络 `FRONT_INTERVAL_PHYSICAL_ORIENTATION_GEOMETRY.json`确认袋yaw8.733°→30.517°，X半宽85.138→101.448mm，盒近侧X几乎不变；原5mm桌边/12mm包裹规划约束可行区宽32.561mm→−0.059348mm（919）。因此中点选择只解决额外预留冲突，不能解决旋转导致本体宽度过大。后续需接触/旋转控制或路线重规划，不放宽门；还未证明哪种新控制物理可行。8RGB4外视均实际查看：袋全8仍部分可辨，后期手遮挡/底裁切并举手停止，不能将失败归为目标全程画外。

后台实际/proc核验：[{'pid': 2923677, 'state': 'S', 'cmdline': '/home/user/miniconda3/envs/env_isaaclab/bin/python /home/user/Documents/zoo/sim/SimFoundry/demo/waist_enabled_20260929_r1/run_front_interval_physical.py --out /home/user/Documents/zoo/sim/SimFoundry/demo/waist_enabled_20260929_r1/front_interval_physical_r2 '}, {'pid': 2936282, 'state': 'R', 'cmdline': '/home/user/miniconda3/envs/env_isaaclab/bin/python /home/user/Documents/zoo/sim/SimFoundry/demo/waist_enabled_20260929_r1/staged_front_corridor_interval/collect_paired_sorting.py --device cuda --viz none --newton-contacts --role diagnostic --layouts 1 --steps 1200 --motion-protocol waist_yaw_enabled_v1 --waist-limit-rad 1.0 --waist-coordinated-expert --bounded-coupled-ik --inactive-retract-m .10 --expert-staging-z .92 --expert-contact-offset -.13 --expert-crossed-contact-offset -.04 --expert-far-contact-offset -.11 --expert-max-contact-x 0 --trace-episode-contacts --trace-solved-contact-forces --expert-far-sweep-retreat-m .08 --trace-viewer-every 5 --expert-goal-release --expert-far-exit-y .34 --expert-frontal-bypass --expert-frontal-feedback --expert-frontal-follow-y --expert-frontal-top-recontact --expert-frontal-top-guarded-descent --expert-frontal-top-continuous-drag --expert-frontal-top-drag-step-m .003 --expert-frontal-top-load-n 5. --extended-waist-diagnostic --trace-control-jacobian-every 20 --trace-hand-contact-forces --expert-frontal-press-z .822 --environment-seed 0 --trace-arm-contact-forces --expert-front-top-route --expert-top-projected-support --expert-frontal-top-inset-fraction 1. --expert-front-clearance-m .012 --expert-top-alignment-tolerance-m .010 --expert-front-recover-clearance --expert-top-hold-established-x --expert-top-nearer-far-contact --expert-front-confirm-nominal-clearance --expert-front-recontact-z .86 --expert-front-recovery-hysteresis-m .0005 --expert-top-confirmed-release --expert-initial-top-route --expert-front-contact-inset-fraction .9 --expert-top-tilt-recontact-rad .03 --expert-terminal-joint-hold --expert-top-contact-normal-hold --expert-initial-top-near-inset-fraction .5 --region-top-approach --diagnostic-layout-json /home/user/Documents/zoo/sim/SimFoundry/demo/waist_enabled_20260929_r1/front_interval_physical_preparation_r1/layouts/840004.json --layout-start 840004 --region-tracking-residual --front-cop-slip-following --front-cop-phase-anchor --front-cop-route-axis --region-causal-response --region-causal-xy-response --region-separate-measured-bounds --rear-cop-centering --rear-core-slice-feedback --front-cop-drive-step-m .002 --front-cop-edge-speed --rear-coupled-progress --rear-joint-xy-progress --rear-joint-edge-command --rear-joint-edge-analytic-retry --self-clearance-task-ik --front-direction-recontact --front-diagonal-entry --front-micro-repair-retention --rear-short-recovery --unloaded-recontact-pose --recontact-interior-preference --precise-clearance-task-ik --rear-joint-edge-parent-seed-retry --minimum-motion-recontact --rear-slow-drag --rear-box-center-preference --rear-box-entry-lift --rear-box-inward-correction --trace-substep-contacts --peak-load-bias-guard --front-corridor-interval --out-dir /home/user/Documents/zoo/sim/SimFoundry/demo/waist_enabled_20260929_r1/front_interval_physical_r2/case_840004 '}, {'pid': 2923724, 'state': 'S', 'cmdline': '/home/user/miniconda3/envs/env_isaaclab/bin/python /home/user/Documents/zoo/sim/SimFoundry/demo/waist_enabled_20260929_r1/watch_front_interval_physical_audits.py /home/user/Documents/zoo/sim/SimFoundry/demo/waist_enabled_20260929_r1/front_interval_physical_r2 '}]。r2完成5/10、当前layout840004；审核已完成5条，有18个原失败审核调用（目前是短盒相关，须继续核对全部最终结果）。free=32.08GiB。所有5条已采数值/实际图审完成（短盒单独不完整报告）。现有冻结.py勿改，只新增版本；物理采集期间不训练。

下一先完成r2剩余原组与全部审核/图审，不重启活进程；再按独立后绕恢复计划实现真实控制器与全层约束，同时解决前通道旋转与仍未建立后绕的3原失败。完整多family train/validation合格后转换/共享训练，保留untouched192推3wait、多seed、h10与实际模型验收。失败数据未入库，无新共享模型，整体目标尚未达到。

以下为历史记录，以本段为准。

## 2026-10-02T09:16:56.171534+00:00 后绕间距丢失定位；前通道物理重跑已越过崩溃点

本轮 progress，goal active未完成；共享RGB+upper11指令策略、完整类别交换/前后/斜向/左右、首零之后双臂与腰yaw可动、非目标全过程15mm、无助推、原h10不变。原基线正式60条件35/48推+12/12wait，仅1/12完整组准入；仍无新增转换/共享模型，无合格validation，未完成untouched192推+3wait、多训练/推理seed和实际模型画面验收。

**差：joint_edge完整8推2wait已采完，6/8推+2/2wait，与同条件基线持平。** 全10数值和实际图审完成，见 `TASK_POSE_VISUAL_COMPARISON.json`。只困难840015盒11步实际修复；其1200步仍未进入原目标区，非目标最大13.040mm，原1053截断对照8.725mm。action699已有真实盒袋接触，早于1052首次修复，不能把所有差异归因于修复。其余成功例没有触发修复，不能归为修复收益。原审核watcher2889025仍活，不能把任务比较报告称为全部审核关闭。

**好：确认后绕问题发生在建立通道之后。** `REAR_CORRIDOR_LOSS_FINDINGS.json`独立旋转包络核验原10条rear轨迹，7条在障碍仍前方/重叠时失去原20mm规划余量，其中4任务过、3失败；不是7条都失败。困难新盒76步已达余量、224步失去，随后408个top_push控制帧继续侧推，699真实物体接触。包络重叠本身不作为接触证明。top/COP控制器只记录间距，未恢复物体绕行路径；下一重点是推进中恢复X通道并协调原COP/关节约束，不靠延时或放宽门。

**审核覆盖修正单独保存。** 原紧凑拒绝记录两处948/1117没有step，旧12项审核失败保留。新增独立compact拒绝树验证2正例+7篡改/安全状态反例，严格重算原关节边界；完整原1200步pose V2通过322events/3handovers，不改质量失败。其依赖V2补审runner2913416仍活；另发现pressure只以文件名依赖pose而未包含于模块映射，新增 `audit_joint_edge_stage_pressure_v2.py` 仅替换前置pose与输出报告名，精确逆向父源码，原全substep标量压力数学不变。独立supplement PID2928867已启动；见 `JOINT_EDGE_PRESSURE_V2_PREPARATION.json` 和 `PRESSURE_V2_LAUNCH.json`。这些修复不授予训练准入。

**前通道全部27项审核已接线，真实物理对照进行中。** `FRONT_INTERVAL_AUDIT_INVENTORY_CHECK.json`确认全部适用清单/报告/逆向源码。首r1第一盒完整1200且原数值门过，但第二袋第0步发生采集主进程Isaac/OmniGraph原生崩溃，保留 `CRASH_LOG_AT_INTERVENTION.txt` 与 `CRASH_INTERVENTION.json`。SIGTERM已发；后来SIGKILL脚本因进程已消失在发信号前断言退出，未发送SIGKILL。r1主/collector/watcher均terminal/missing；原因尚未唯一确定。首完整盒未与其它run拼接，不入库。

`FRONT_INTERVAL_INFRASTRUCTURE_RESTART_REVISION.json`预先限制仅一次基础设施重跑，原10条件/2完整组/同seed/1200或70/5N/原相机不变，无择优拼接。r2 runner2923677、watcher2923724、collector2923751实际活，840014袋已到480（已越过旧崩溃点，不证明故障消失）；实际105来源核验过，见r2/case_840014/EARLY_SOURCE_CHECK.json。若同任务边界再次崩溃，先诊断生命周期，不循环重跑。原候选只front区间，不混入joint_edge修复。r2冻结当前W根.py，勿改现有冻结文件；新增独立版本/文档允许。

下一：持续追踪r2完整两组及原EDGE/V2全审核、实际图审；独立开发后绕持续路线恢复，先验证可达性与接触约束，再完整困难/成功组物理对照。失败不能入库，完整多family train/validation合格后才转换/训练和原范围模型验收。

以下为历史记录，以本段为准。

## 2026-10-02T08:38:12.231059+00:00 基线正式关闭；交换盒仍失败且确认物体间干扰；前通道审核推进

本轮 **progress**，goal active未完成。目标仍是共享RGB+upper11指令策略在完整类别交换/前后/斜向/左右多样布局下完成分拣；首11维零位，之后双臂与腰yaw可动，非目标全过程15mm、无助推、原h10与其它门保留。足量完整train/validation、多seed模型闭环、untouched192推3wait及真实模型画面都尚未完成，不能以当前专家诊断替代。

**原基线已正式收尾。** `fresh_closed_peak_trials_r1/RESULT.json` 为 complete_trial_audited，60条件、35/48推、12/12wait、仅1/12完整组通过。全部12 formal reviews及60实际画面已绑定，审核执行计数primary216/observer60/pressure60/control478/additional336。第12reverse validation 2/4推+wait过，整组拒绝。仍只有此前1完整train组5条准入，无新转换/模型、无合格validation组。`FAILURE_MODE_SUMMARY.json` 全部13推失败按观察表现为5完整时长未完成、4前侧通道保护、3后绕未进入top_push、1提前guard停；这是分类不是单一因果证明。

**采集接续透明记录。** 原新runner2877675在首840014双任务采完后因审核清单里front_diagonal重复列出而断言退出，非物理异常。原冻结源未修改。新增 `resume_joint_edge_physical_collection.py` 复用已完整保存首pair，不覆盖、不重采；`watch_joint_edge_physical_audits.py` 只去除完全同名的重复调用，每项不同审核保留。`RESUME_PROTOCOL.json` 扩展原2743文件冻结；现在复核2746源0变化。当前采集完成7/10，layout840005，producer2888850/collector2902061，watcher2889025；实测/proc=[{'pid': 2888850, 'state': 'S', 'children': ['2889025', '2902061']}, {'pid': 2902061, 'state': 'R', 'children': ['2902371']}, {'pid': 2889025, 'state': 'S', 'children': ['2906186']}]，free=33.79GiB。状态文件只是记录，下一轮仍核验/proc，勿重启活进程。

**好与差并列：联合edge修复实际触发，但未解决任务。** 原840015盒1053帧提前拒绝，新盒完整1200，11次changed在1052–1064之间；原推进249.745→277.749mm，末10signedY最低169.286mm仍不足200mm，任务失败。非目标最大8.725→13.040mm，虽低于原15mm但余量不足。完整raw+24物理substep（同时保留记录中的observer重复）确认新旧都从action699出现盒袋真实接触，frame700非目标开始移动，新轨迹在首次修复1052前已移动8.759mm；没有非零robot→mailer接触力。明确是物体间路径干扰，不可把它全归因于新增联合修复。原记录与新轨迹均无助推/首零，失败不入库，见`SWAP_BOX_INTERFERENCE_FINDINGS.json`。实际8RGB4外视：盒后段严重裁切，1027后不可辨；抽样图无法判定毫米干扰，结论来自真实接触记录。

**交换袋仍失败。** 新840015袋1200推进141.626mm，末10signedY43.646mm，非目标0；696步首次front_corridor_no_table_margin，504guard帧。实际8RGB4外视目标可辨但手遮挡/下裁切，末段举手停滞，失败不能简单归因画外。原同例765才保护；新首pair与原轨迹也存在微小早期数值差异被模式切换放大，不能承诺相同seed逐帧相同或把所有变化都归给候选。首840014双任务均过、0repair触发且全部适用审核过，不能作为修复收益。

**审核缺口不是任务通过。** 新盒pose/self-clearance/normal/terminal_inputs等审核因两处紧凑拒绝规划记录 `{accepted:false,reason:current_scene_rejected}` 没有step而KeyError；pressure因前置pose报告缺失未验证，不能称为压力超标，也不能记通过。独立几何确认948/1117右腕测量角1.97222209超过原1.9722界约2.209e−5rad，而当帧命令在界内，规划器正确拒绝，随后原控制继续。`SWAP_BOX_REJECTED_SCENE_FINDINGS.json`绑定证据。下一新增独立审核版本应严格核对该拒绝分支/父fallback/未执行，不补造step，不宽限原门，不覆写原失败。

**成功对照与视野风险。** 新840004盒推进283.978mm、末10Y205.631；袋299.835/204.945；均1200、原任务/pose过、非目标0、首零/assist0，但其全部control尚待watcher。盒2tilt0lost、phase3/563/634；袋0tilt6lost、phase3/905/292。实际盒8RGB双物体可辨；袋171裁切/342可辨，513后两物体画外，保留对共享视觉模型的风险。841007wait70、全11action0、腰3.08734e−9、8RGB稳定；这些actual bindings已保存，当前共7条实际图审。

**前通道候选向完整审核推进，尚未物理启用。** 新 `check_front_interval_independent_enabled.py` 在原8+新失败袋9实际状态流10791行执行真实候选guard/goal前缀，对照独立Scipy旋转几何；default-off实际原记录全过，enabled为明确标识的固定状态流合成前缀，非反事实动力学。四成功例无变化，五失败输入流可提出替代目标；6篡改（目标/区间/标志/缺记录/旧不安全目标/绕过保护）均拒绝，额外注入4mm手距真实候选仍保护。`FRONT_INTERVAL_INDEPENDENT_ENABLED_CHECK.json`。

新增独立 `front_interval_stage_source_binding.py` 精确逆向collector+front组件、核原profile/实际来源/observer；旧edge来源在缺front开关处被拒绝（stage自身核验已过）。`audit_front_interval_diagonal_live.py` 只将独立核验的区间goal接入原完整diagonal/COP/力包/waypoint复算；原9轨迹10791控制行、2146 loaded行与父审核逐值一致、0 errors，见`FRONT_INTERVAL_COP_REGRESSION_CHECK.json`（仍是default-off回归，未证明enabled完整接触/动力学）。全部改动能逆向还原父文件；其余source-bound pose/clearance/pressure/task等适配和整套清单尚未完成，前通道物理不得提前启动。

接下来：完成当前原定8推2wait和全部实际审核/两组对照；处理紧凑规划拒绝的独立审核覆盖；补齐前通道全部审核后在原失败完整组+成功完整组单独物理比较，不与edge候选混入。后绕仍须解决真实物体间路径干扰、接触效率与腕边界，不能只延长时长；视野须在共享模型阶段实际验证。只有足量完整多family组通过才转换/训练，再做原独立全范围多seed h10验收。原门、全部失败与原实验清单均保留。

以下为历史记录，以本段为准。

## 2026-10-02T07:54:30.825948+00:00 全60条件采集与实际图审完成；联合edge修复已开始真实物理对照

本轮 **progress**，goal active未完成。原任务质量为 **35/48推、12/12wait**；四families按盒/袋各6次：lateral4/6+4/6、depth6/6+3/6、diagonal5/6+6/6、reverse_diagonal4/6+3/6。全60实际图审绑定已齐，5N设置也已全60绑定（配置一致不等于动态压力/任务过）。原runner2696467正常结束，STATUS collection_complete_audits_visual_pending。原watcher2696468仍实际运行：最后case840023的两个任务控制审核尚未收齐；GROUP_REVIEWS已11组，第12不提前判。仍1组5条准入、0新转换/模型，独立全范围多seed h10目标不变。

**已调整启动先后，未减少检查。** 此前计划等全12组最终close再启动新物理。现原采集全部结束、GPU空闲、全60图审/配置核对完成，且本次要比较的失败reverse07和成功diagonal02早已逐条完整审核，因此允许新物理与其他组的只读CPU审核并行。`JOINT_EDGE_PHYSICAL_CONCURRENCY_REVISION.json`明确替换PLAN中这一等待要求，保留完整原trial最终close、所有新旧审核和准入标准；预检核验60条件清单、全部raw/pressure哈希、两个对照组全部证据、原runner已退、GPU无compute及>30GiB，实测通过。旧 `JOINT_EDGE_PHYSICAL_LAUNCH_GATE_CHECK.json`只属于前一顺序版本，不作为新preflight报告。

**真实新采集已启动，不是仅提交计划。** `joint_edge_intersection_physical_r1`，runner **2877675**、当前collector **2877864**，layout840014首盒日志已到实际step150（以最新日志为准），role diagnostic，edge_clearance_intersection=True。完整reverse07失败组+diagonal02成功组 **8push2wait** 继续全部跑；仅joint-edge/肘交集修复，前通道候选未混入。真实provenance107项已被 `verify_trial_provenance` 核验通过，记录 `case_840014/EARLY_SOURCE_CHECK.json`；不代表任务或动态安全成功。原5N、1200/70、首零、无助推要求及所有适用原审核保留。没有任何新修复物理结果已被宣称成功。

新run PROTOCOL冻结 **2743** 文件：包含原1520、**当前W根全部.py**、edge stage、计划及已闭合对照/配置证据。**不要修改这些现有文件**；后续只能新增独立版本/文档，或等此run结束。旧审核还要完成最后pair→第12组→`close_closed_peak_trials.py --apply`，之后运行新增 `summarize_closed_trial_failure_modes.py`；不要因新物理已运行就省略旧baseline收尾。原closing函数不会把新独立collector误判为原collector，核验原LAUNCH和原STATUS即可。

下一先查/proc与两个run状态，别重启。继续原最后controls/第12formal/close，再跟踪新8推2wait的完整数值/来源/控制/actual visuals，重点查看原840015盒1053是否不再被最终guard拦停及非目标稳定，不以能执行更多步当成功；前通道独立stage后续还需整轨迹来源与审核接线，后绕效率/可达性与相机视野仍未解决。要形成足量完整多family train/validation才能共享训练、untouched192推3wait多seed h10实际模型验收。

实时2026-10-02T07:54:30.825948+00:00 /proc=[{'pid': 2696468, 'state': 'S', 'children': ['2881054']}, {'pid': 2877675, 'state': 'S', 'children': ['2877864']}, {'pid': 2877864, 'state': 'R', 'children': ['2878171']}]，free=35.71GiB。机器状态绑定见W/`LATEST_ACTIVE_RUNS.json`与`JOINT_EDGE_PHYSICAL_LAUNCH.json`。

以下为历史记录，以本段为准。

## 2026-10-02T07:45:48.715776+00:00 前通道修复形成默认关闭的独立stage；原48推已生成，第11组正式失败保留

本轮 **progress**，goal active未完成。原全范围共享策略、双臂/腰yaw、首零、非目标全过程15mm、无助推、h10及原质量门不变；足量完整train/validation、untouched192推+3wait、多seed模型闭环和实际画面验收继续。当前已生成48推、任务质量35/48过；等待12/12，actual bindings=59，formal groups=11；仍1组5条准入、0转换/新模型。生成数不等于runner审完数或整体关闭。绑定见 `FRONT_INTERVAL_CANDIDATE_AND_LAST_PUSH_FINDINGS.json`。

**好：前通道候选已从公式变成真实状态机代码，仍未物理运行。** `front_top_route_interval_candidate.py`从冻结front_top_route_micro逆向可还原，只在原extra3mm预留目标不可行而原5mm桌边/12mm物体间距区间仍非空、其它保护和锁停均未触发时，取区间中点。默认False不加新日志字段。真实guard/goal函数前缀在固定7轨迹8393个实测状态上执行：默认关闭8393行与父逻辑一致；启用仅840007袋754、840015袋765、840020盒237三行改变，四个成功例不改。5反例（旧锁停、手距、非目标移动、桌边、物体间距）均仍保护。只复核原观测和原prior latch，不是反事实整段新轨迹，也未执行后半接触SM/IK/动力学。

`staged_front_corridor_interval`由冻结staged_peak_load_guard新建，collector4处显式可逆接线、组件hash绑定。真实COP类继承修改后的FrontTopRoute，跟随层读取修正的row.route_goal_x，不另造旧目标；12实际CLI预检（2接受10拒绝）通过。与joint-edge修复分离，不偷偷混入正在采集的源。下一front物理验证仍需完整episode来源/原审核适配和完整配对组；不要把prefix或CLI通过当成功。相关manifest/CHECK均在独立stage及W根。

**差：第11斜向validation正式3/4+wait过，96/96控制过，整组因840020盒任务失败隔离。** GROUP_REVIEW hash 2fcb51d87bc6037d2726717f58050a2b453dc7b659676780700c4d7e3f09edaa。第12原摆放840022双任务均过：盒150.086mm/末10Y241.907mm，袋150.336mm/261.788mm，非目标0、首零/assist0；phase盒3/503/694、袋3/594/603。实际8RGB4外视：袋342左严重裁切、513后图外，盒513后只右边局部但可辨；非目标均可辨。

**差：第12交换两任务均失败。** 840023盒完整1200推进237.788mm，但末10signedY最低125.881mm未进区；rear route，无front stop，9倾斜、0失载、509top_push、369top_cross。原袋完整1200仅推进1.301mm、末10signedY−90.521mm；112步front_corridor_no_table_margin后1088guard帧，无倾斜/失载。两条非目标0、首零/assist0，实际8RGB4外视已绑定。盒171/342右侧可辨、513窄片、685后不可辨；袋全8目标可辨（手遮挡），木盒后段左裁切可辨，所以袋失败不能归因画外。

未改候选再次覆盖最后袋：`FRONT_CORRIDOR_REPLANNING_SCREEN_R4.json`现在8完整front例9592行、6660原goal重放；四成功不改，四失败各首次停前1提议。新增840023袋112原桌边4.901914mm，原约束仍有X=[.361801530,.364703444]，中点.363252487；之后1087锁停保留。该R4是既有几何公式+独立LP补充，不能冒称真实组件prefix checker也已经扩到8例（其固定7例结果仍原样）。

新增 `summarize_closed_trial_failure_modes.py` 已语法检查，要求60条件正式RESULT才输出按family/task任务与控制分别计分及全部失败表现，目前未运行。下一按完整run关闭→联合edge物理对照执行器的顺序不变，前通道后续独立验证；还需后绕接触效率/可达性及视野问题，不因一个候选缩目标。

实时2026-10-02T07:45:48.715776+00:00：STATUS completed=59 layout=841011，/proc=[{'pid': 2696467, 'state': 'S', 'children': ['2874563']}, {'pid': 2696468, 'state': 'S', 'children': ['2874249']}, {'pid': 2874563, 'state': 'Z', 'children': []}]，free=35.79GiB，1520冻结源全重验0变化。旧collector消失表示该case采集结束；runner仍等实际子审核，不重启。最后等待和第12controls/actual绑定若未齐继续做；只在全部60审完、全12group/pressure绑定/close完成后启动 `run_joint_edge_intersection_physical.py`（无需用户再批准）。

以下为历史记录，以本段为准。

## 2026-10-02T07:26:29.123069+00:00 联合约束整轨迹审核补齐并回归通过；前通道第三个失败复现，第11组实际图审完成

本轮为 **progress**，goal active未完成。仍坚持原共享视觉指令策略、双臂/腰yaw、首11维零位、全过程非目标15mm、无助推、真h10及其余原质量门；全范围train/validation、untouched192推+3wait与多个种子模型闭环和实际画面验收均未缩小。当前formal groups=10、actual visual bindings=55；前11组任务 **33/44推、11/11wait** 过，但第11组控制审核待齐，不能预准入。仍仅1完整train组5条准入，0新转换/模型。证据绑定 `fresh_closed_peak_trials_r1/JOINT_STAGE_FULL_AUDIT_AND_ELEVENTH_GROUP_FINDINGS.json`。

**好：新联合edge/肘间距修复的原审核清单全部适配到独立版本。** 本轮新增17文件，包括正常力、压力、24substep接触、region/无载/带载执行链及run_contract；新旧清单均27项，16审核/上下文文件逐修改逆向恢复原父文件，原数学/质量门未改。最终执行命令改为分别检验“原edge解的原约束”和“新的交集证书”，不能拿旧edge输出冒充真实最终action。新 loaded parent调用逐支撑顶点KKT版本；当前1520冻结源、55stage文件哈希重验不变。`JOINT_EDGE_STAGE_REMAINING_AUDITS_PREPARATION.json`与`JOINT_EDGE_STAGE_AUDIT_INVENTORY_CHECK.json`绑定。

**整轨迹回归是明确标注的合成序列化fixture，不是物理成功。** 上轮已完成完整1200帧self-clearance回归、1199控制行、71原edge逐值保留，缺一新记录拒绝；本轮 `JOINT_EDGE_STAGE_LOADED_FIXTURE_CHECK.json` 再完整检查1199任务行、292 loaded parent帧、71原edge及71新最终交集，篡改输出拒绝。实际stage来源绑定必须拒绝fixture；record回归才局部mock来源，不用于正式审核/准入。回归先发现独立尺寸重建的float表示与记录严格比较不一致、以及hand变量被旧循环覆盖，两者已修正并最终回归通过；独立几何尺寸原1e−7对照保留，新证书严格绑定日志实际core。

**数学审核统一复核已终态，不要重启PID2841473。** 固定38push清单：34满足原完整轨迹/pose前置并复核，33通过；4前置不足明确未验证。原有3个false：840007袋step194仍残差2.45980264e−6失败；840012盒现在通过max4.44380655e−7；840015袋数学通过max1.40663005e−7但任务仍失败。其它31原true仍true。原报告/组准入未重写，斜向06不能仅凭这个补充报告自动入库。

**第10前后validation组正式失败：3/4推+wait过，96/96控制过。** 840018袋推进130.481mm不足150mm保持失败。交换840019盒285.149mm/末10Y200.528mm、袋150.031mm/212.900mm通过，非目标0、首零/assist0；盒7倾斜4失载、袋0倾斜7失载。该盒只有26release帧且最后关节未满足phase helper的settled十帧后缀，`EARLY_QUERY_PHASES.json`记录“No distinct active phase and settled ten-frame terminal suffix”；这不是篡改任务质量理由，也不能裁帧或伪造terminal。袋phase3/742/455。两条8RGB4外视与841009空桌8RGB实际绑定已齐。盒513之后目标边缘裁切、685以后不可辨；袋双物体8帧可辨但黑袋左/底裁切。GROUP_REVIEW hash c4a305ec5901c538985ad0fe7076ee80e623fdbcbb0fbe90285535fa39d6e471。

**第11斜向validation组新差结果：原摆放盒完整1200只推进55.471mm，末10signedY−102.578mm失败。** 第237首次 `front_corridor_no_table_margin`，随后963帧front_guard_lift；全8RGB仍能辨盒/袋，故不是仅由画外解释。原袋336.855mm/末10Y205.232mm通过，0倾斜7失载、phase3/952/245；袋0/171/342可辨、513左裁切、685后双物体不可辨。交换840021盒150.238mm/281.860mm、袋150.626mm/308.675mm过，非目标0、首零/无助推；盒8倾斜5失载、phase3/982/215；袋0倾斜5失载、phase3/541/656。盒目标171只余右边裁片、342后不可辨；袋513只黑色边片、685后左侧部分严重裁切，木盒全部可辨。四条各8RGB4外视实际看过绑定；841010wait70全11action0、腰3.087381e−9、实际8RGB稳定。整组控制尚待840021两任务完成，`audit_closed_peak_trial_group.py ... fresh_diagonal_10`目前返回pending，不提前判控制或准入。

**前通道R3扩展七个完整例，原门不改。** `FRONT_CORRIDOR_REPLANNING_SCREEN_R3.json`共8393行、6549原goal重放；四成功例仍不改，原两失败袋与新840020盒各仅首次保护前提议安全区间中点。新盒237原计划桌边4.893769mm、原5mm桌边+12mm物体间距仍允许X=[0.366812464,0.369706233]，中点0.368259349，其后962已锁停行不改。独立LP核对，但不是完整机器人路径/接触物理验证；不将此候选混进联合edge单改动对照。

**下一物理对照执行器已完成但未启动。** `run_joint_edge_intersection_physical.py`读取既有8push2wait计划：完整反斜向07失败组+斜向02准入对照组。启动前要求原60条件完整RESULT且重新close核证、GPU无compute进程、可用>30GiB、来源/审核回归哈希一致；新独立目录，失败不抹掉，27清单中适用原审核逐条执行并保存，仍需实际图审，不自动训练。已实测baseline尚未关闭时拒绝启动（`JOINT_EDGE_PHYSICAL_LAUNCH_GATE_CHECK.json`）；无需用户再次批准。空桌仍明确diagnostic factory envseed0/70，不冒称fresh合同同seed。

实时核验：2026-10-02T07:26:29.123069+00:00，STATUS completed=55 layout=840022，进程[(2696467, 'S'), (2696468, 'R'), (2859421, 'S')]，free=36.63GiB。先完成原第11/12组controls与实际图审、全60pressure setting绑定和close；然后运行该执行器真实对照，继续分别解决前通道、后绕接触及相机可观测性，足量完整合格组后转换/真实loader/shared训练/独立多seed h10，不把离线改进当终点。

以下为历史记录，以本段为准。

## 2026-10-02T06:53:29.516369+00:00 联合约束修复独立stage接线通过；角点数学审核V2已完成真实整轨迹复核，统一批量复核继续

本轮/上一分拣轮均 **progress**，goal active未完成。原12组60条件持续；当前正式9组审核，前9组任务27/36推+9wait通过，**1完整train组5条准入、0新转换/模型**。第10组首对也完成实际图审（一过一失败），因此已图审47条＝28/38推+9wait。详细绑定见 `fresh_closed_peak_trials_r1/STAGED_JOINT_CONSTRAINT_AND_VERTEX_AUDIT_FINDINGS.json`。原首零/后续双臂腰yaw/非目标15mm全过程/无助推/真h10/全范围train-validation/untouched192推3wait多seed目标均不变。

**好：联合防滑与肘间距修复已实际接入独立stage，默认关闭。** `staged_joint_edge_clearance_intersection`从已冻结`staged_peak_load_guard`复制，5处显式改动可以逆向恢复父collector字节；旧fresh运行源无修改。仅原joint_edge override后、原final_guard前接入新adapter，保留原任务、0.5mm木盒内移、关节界/步幅、5mm肘间距。求解失败无可执行输出，原final_guard继续记录拒绝并停止，不能偷偷回退未经验证命令。新flag限制diagnostic、需原edge/inward/self_clearance/substep，禁止policy/pilot/idle/waistprobe。

9个真实完整prelaunch CLI检查（2正7拒绝）通过；初次缺EULA环境变量的checker已明确退出，设置本项目已有OMNI_KIT_ACCEPT_EULA后重跑通过，不是模拟启动。原8组32推共352次edge override经过 **stage真实record adapter**，351逐值保留，仅未执行的1053命令变化；另4条错配输入拒绝。独立审核器 `audit_joint_edge_clearance_record.py` 不导入候选solver/helper，重新计算原任务、原edge解、独立URDF手/肘、最终交集和逐顶点KKT；候选残差9.692e−9，5种篡改输入均拒绝。**这仍是离线证据，尚未启动修复后的物理采集。**

**好/差同时保留：角点审核数学修正已从探针形成独立版本。** `support_vertex_stationarity.py` 仅在唯一最大分离轴时使用全部active支撑顶点法向；原5mm可行性、1e−6驻点与active容差保持，轴有歧义明确拒绝。1319真实override（175+336+808）与既有独立诊断逐项一致；840007袋194仍2.4598e−6失败，不能为提高通过率消掉。6个失败反例与精确二维角点验证、另将轴重复但不改变几何间距的歧义反例均通过；零目标梯度也不能让歧义轴自动过。

新 `audit_pose_task_optimality_vertices_v2.py` 由原fresh task auditor只替换stationarity计算/版本报告生成，替换清单可逆还原原文件，全部来源、q/action、任务目标、原界/可行性、solver元数据及无载路径检查不变；保存**单独**`POSE_TASK_OPTIMALITY_VERTEX_V2_AUDIT.json`。已实际重跑原pose全检查+1199行task：840007袋仍失败194；840012盒336override通过（max4.4438e−7）；840015袋808override通过（max1.4066e−7）但其任务失败仍在。原审核/原GROUP_REVIEWS没有回写；第7组仍不因这个补充报告自动入库。

为避免只挑原失败例修改审核，已启动统一补充复核 `run_pose_task_vertex_v2_review.py`，**session46599，PID2841473**；固定启动时已完成episode清单共38推，逐条原pose/source全部复核；缺少原前置证据或horizon不完整明确列未验证，不能算通过。当前6行已完成、current=layout_840003_nudge_mailer_to_bin，下一先查/proc和该session，不重复启动。JSON状态文件会继续变化，本段为快照。

**第9左右validation组失败保留**：840016袋后绕失败；840017交换盒/袋均完整1200过，推进150.028/150.097mm、末10Y308.059/306.982mm、非目标0、首零/assist0。盒5倾斜9失载、phase3/1160/37；袋0倾斜5失载、phase3/644/553。8RGB4外视实际看过：交换盒171目标仅右边窄条、342后不可辨；交换袋171后目标不可辨，另一物体均仍可辨。841008wait70全11action0、腰3.08738e−9rad，实际8图稳定。GROUP_REVIEW SHA69429134653c55fed0496dd675055e9535261e14f063483e92d8ccf77802c9b3：3/4推+wait过、84/96审核过，840016袋12项原依赖失败，完整隔离。

**第10前后首对：盒过、袋失败。** 840018盒264.273mm/末10Y201.405mm、4倾斜3失载、phase3/749/448；8RGB均能辨双物体（手遮挡）。袋完整1200推进130.481mm虽末10Y215.102mm仍不足150mm进度门，top_push968帧、0倾斜2失载，不能仅按进区判成功。袋RGB仅0双物体可辨，171只余木盒左下裁片、342后双方不可辨。两任务非目标0、首零/无助推，8RGB4外视已绑定，交换对与等待仍按原计划继续。

准备了 `joint_edge_intersection_physical_preparation_r1/PLAN.json`：原失败fresh_reverse_diagonal_07完整四推+wait，原已准入fresh_diagonal_02完整四推+wait，6真实CLI均预检通过；这是 **8推2等待的因果对照**，不替代全12组/最终模型验收，不是新可训练数据。wait使用已有diagnostic空桌factory元数据、envseed0/70帧，不能冒称fresh-v2同seed合同。还未启动：必须先完成当前采集/审核，并补齐新stage整个episode来源/最终命令联合约束审核及原审计适配，单record检查不能冒充整轨迹通过。

最新进程实核 2026-10-02T06:53:29.516369+00:00：STATUS completed49、layout841009，/proc [(2696467, 'S'), (2696468, 'R'), (2842743, 'R'), (2841473, 'S')]；free38.11GiB，1520冻结文件复核0变化。下一继续原全批实际图审/组审核与最终pressure绑定/关闭；并完成联合约束新stage整轨迹审计→完整物理对照。前通道安全区间候选和后绕顶部路线仍需完整机器人/物理证明，不与该单改动混淆。只有全范围合格组与图像质量/真实loader验证到位才共享训练；独立多seed真h10闭环与实际模型画面验收继续保留。

以下为历史记录，以本段为准。

## 2026-10-02T06:32:11.346777+00:00 新定位：防滑修正破坏先前避碰约束；联合求解已离线重放，前8组正式审核完成

本轮为 **progress**，goal active未完成；Git备份是独立任务，不计共享策略完成。当前原12组60条件继续，已正式审核8组；前8组 **24/32推、8/8wait** 通过原任务指标，42条实际图审包含第9组首对（该对1/2），因此已图审推为25/34。**仍仅1个完整train组5条准入，0新转换、0新模型**，全范围与独立192推3wait/多个seed/真h10验收保持。详见 `fresh_closed_peak_trials_r1/JOINT_CONSTRAINT_AND_EIGHT_GROUP_FINDINGS.json`。

**差：第7斜向不是第二个可入库组。** 四推+wait任务过，但正式95/96控制审核过，840012盒335步原KKT残差8.9665e−6失败；GROUP_REVIEW SHA77252fe84c8a1844d4cbe36a009155585ed5ab8a83c30fe64fd636ffb49ad02e，完整隔离。独立全部336override逐顶点角点诊断0失败、无轴歧义；335原残差降至4.4438e−7，原5mm/1e−6阈值不改。这是原min函数单梯度漏掉角点法向的证据，**未修改冻结原审核或以诊断代替准入**。下一版正确数学审核需版本化、独立负例验证与重新审核，不能回写旧false为true。

**差：第8反斜向组2/4推+wait，完整隔离。** 840014原盒/袋各1200通过且实际8RGB4外视已绑定。840015交换袋完整1200只推进144.4967mm、末10Y46.517mm，第765步`front_corridor_no_table_margin`后435帧front_guard_lift；原任务失败、非目标0、首零/无助推。交换盒于1053步最终命令检查拦停，仅录1053/1200，quality推进249.745mm但未到目标区；原完整horizon inspector正确拒绝，另存明确不完整诊断，绝不补帧/裁剪或训练。非目标记录最大8.7254mm，首11q/action0、assist0。两任务8RGB4外视与841007wait8RGB实际已看并绑定。正式审核96项中18项失败，盒17项多为截断依赖级联、袋1项KKT；不是18个独立物理根因。GROUP_REVIEW SHA9eb07a9d2ebc0235d6cb9d066f63f3c2b54142dbc5a5d35cc80b86f244416b8a。

**好：盒拦停原因已精确复现，并形成可调用修复候选。** 1053步原self_clearance_task命令左肘间距4.999997mm通过；后续joint_edge_inward修正只保边缘内移/前进，没有将肘约束带入自身求解，把间距降到4.744426mm，最终guard正确拒绝，**该拒绝命令未执行**。以1052动作最后substep实际物体姿态重建原adapter，float32输出逐值一致（最大误差0）。新 `joint_edge_clearance_intersection_candidate.py` 在同原任务目标、界/速度/防滑0.5mm/前进要求与肘5mm同时求解；两个起点均20迭代得同一解，最大改动.00157785rad、肘5.00000056mm、向前.450299mm，独立URDF/FK和原门通过、KKT9.692e−9。不是物理成功或全身避碰证明。

新checker覆盖前8组全部32推中的352次真实edge override：**351原本安全命令逐值保留，仅修复1053一条未执行失败命令**；3负例验证非法输入/其他门失败/缺上下文不会输出未经验证命令。可调用候选与独立双起点probe逐值相同，CROSSCHECK绑定。当前完全隔离，**未装入运行采集器**，不改变冻结源；下一步在独立stage接线与新版本联合KKT审核之后，做原配对组物理对照，不能将历史输入离线回放当修复后轨迹。

**前通道同根因再现**：通用原候选R2覆盖6front例7194行、6313原目标重现≤2.79e−12m，四个成功例不改；两失败袋仅首次停前提议原5mm桌边/12mm包裹间距可行区间中点。840015第765步原规划桌边4.7965mm，实际剩余区间[.385020201,.387816725]，候选.386418463；其后434已锁停行仍保护。不是放宽门，也未验证完整手臂扫掠/真实跟踪。该袋原KKT137/317/535失败全部逐顶点诊断通过（≤4.55e−8，无轴歧义），任务失败仍保留。

**顶部运送离线路线既有好也有差**：20mm偏好替代起姿4/4完整路径失败；原12mm已存在规划fallback的6起姿全路线也0/6，均保留，不能因单段过门称路线成功。新支撑顶点分支约束（选点必须为最低凸包顶点、原门+独立细采样不变）在6条完整路线中仅 **840001盒neutral_waist−.5的Y→X22段过**，其余5条仍失败，包括840008盒所有3起姿。此为实际case分母的离线规划进展，手仍悬于core6–7mm，物体是几何假设平移；没有物理压力/推动、零位接近与全身连续路径证明，禁止直接执行全部q。原6布局其它成功/失败保留，不能只选过的路线缩目标。

第9组840016首对实际已看：盒推进362.202mm、末10Y205.317mm通过，phase3/758/439、1倾斜1失载；袋后绕1165帧停滞，推进71.403mm/末Y−86.628mm失败。两例非目标0、首零/无助推。袋RGB171之后两物体均不可辨，明显相机视野风险；盒171黑袋不可辨，其余多数双物体可辨但手遮挡/底边裁切。不能以图外单独解释专家几何失败，也不能靠重采样恢复画外观测。

实时核验 2026-10-02T06:32:11.346777+00:00：STATUS completed44、layout841008；/proc [(2696467, 'S'), (2696468, 'S'), (2829317, 'R')]，可用39.21GiB，1520冻结文件全重验0变化。当前原runner/watcher继续，不重启终态旧collector；本轮所有离线/图审sessions已结束，无新训练。下一顺序：收完原12组并原审核/实际图审/pressure全run关闭；分离处理最终修正约束冲突、前通道规划和后绕接触路径，优先可复现实测冲突，正确KKT角点审核版本化；隔离接线/原配对布局物理验证后形成足够全范围train+validation合格组，才转换/phase/h10真实loader/共享训练；未调参独立192推3wait及多个seed模型闭环验收与实际图审不省略。

以下为历史记录，以本段为准。

## 2026-10-02T05:58:43.791956+00:00 真实接触力方向已交叉核验；顶部后绕候选完成端点/路径筛查，第7斜向四推与等待过、待整组控制审核

本轮progress，上一分拣轮亦progress；goal active未完成。**原12组60条件继续：前7组28推22过、7wait全过，35条实际图审已齐；正式GROUP_REVIEWS仍6组，仅1组斜向train5条真正准入，0新转换/模型。**第7组fresh_diagonal_06审核返回pending：840012袋、840013盒/袋controls未齐，不能提前准入。独立192推3wait多seed/h10、全范围train/validation要求保持。证据：SIGNED_CONTACT_AND_TOP_TRANSPORT_FINDINGS.json。

**好：第7斜向完整四推全部原source/任务/pose过、非目标0、首11q/action0、assist0。**840012盒推进311.8079mm、末10最小205.1051mm，2倾斜1失载，phase3/864/333；8RGB双方均可辨（有手遮挡/边缘裁切），4外视已绑。840012袋349.6929/201.1314mm，0倾斜9失载，rear_push56、phase3/1186/11；差：RGB非目标171后不可辨，袋171/342左裁切、513仅小片、685后不可辨，外视已看。840013交换盒150.0090/298.5705mm，6倾斜7失载，phase3/1047/150；差：171木目标只窄边条、342后不可辨。840013交换袋150.4677/257.1705mm，0倾斜6失载，phase3/638/559；袋后段左边严重裁切但留黑色部分，木盒全8可辨。841006 wait70全11action0、腰最大3.0874847e−9rad、8RGB稳定。均保留完整帧，专家数值成功不是模型可学证明。

**接触力正负号有实证**：check_recorded_contact_force_sign覆盖6条已完成rear-selected轨迹（包括新840012袋），共345600个物体-子步。归档support.py与当前安装解码器一致；当前constraint.py稀疏/稠密均Jbody2−Jbody1，shape映射保序。Newton body_qd前3为世界COM线速度。以24个最早已完成solve力、真实质量、重力，与逐子步mΔv/dt交叉比较，shape_ids第1索引侧取正、第0侧取负时RMS力平衡误差0.000886–0.002571N；反号2.167–2.203N；原符号峰值仍有0.0698–0.1161N残差，不称精确动态复现。解码器归档已绑；constraint/solver/state源是本次安装版本检查，并非全部有历史归档。原observer元数据不回写。该证据支持这些轨迹的平动力符号/时间配对，不证明力作用点与结束姿态同步或反事实因果。

依此6条rear手/目标有符号力时间和，沿正确任务Y分别+0.79382、+0.48538、+0.12190、**−0.84229袋/−0.29362盒**、+0.26535Ns；是手力贡献，不是包含桌面/重力的物体总冲量。REAR_NORMAL_TANGENT_DIAGNOSIS独立用每动作最后solve的frame/Fn分解，decoder误差≤2.14e−7N；两卡住任务法向的任务Y向量和分别−12.662/−6.250N，摩擦切向分别+7.091/+3.915N，部分抵消。这里是末子步抽样向量和，不能冒充24子步法向冲量。说明优先接触法向/姿态，而不应单纯增压或只锁住Y跟随。

**新增候选方向：顶部先建立接触，按安全Y预移→X后绕路径运送。仅离线，未安装/未采物理。**screen_initial_rear_top_contact对6原rear例各初始/后绕原Y/后绕预移Y共18scene、4起点共72优化，全部失败保留；14/18scene至少1独立URDF/手/肘几何通过的端点。原.98命令腰界、双臂可动；真实core内20mm、手最低点高于core6–7mm、薄轴对齐≥.8、另一手最低.84m、手/物体10mm与肘/躯干5mm，只是已有离线接触姿态规划偏好，不新增数据门。840008袋与盒初始都找到；盒后绕原Y未找到、预移Y4/4起点找到；840001盒两个后绕endpoint未找到，840007盒initial未找到，有限优化非全局不可达。

**端点不等于路径**：原直接连接和固定四分点约束版各仅1/10已尝试路径通过独立细采样，另1布局因无初始endpoint未试2路线。多数失败来自最低支撑点XY在两个约束位置之间跨出原20mm内区2–64微米；候选/独立几何点逐值一致，不是降低门或重标签能解决。screen_rear_top_transport_refined将真实失败的插值位置纳入下一次SLSQP，最多8次/段，保留所有拒绝；原采样门不变，10um/标量残差规划预留不改变质量门。最后完整6布局结果：840004袋X先、Y先均过；**840008困难袋Y先26步/94独立采样过、X先第7步求解未收敛**；840012袋两路线过；840001盒两路线仍未过；840008盒X先12/23、Y先24/35时仍拒绝；840007盒无初始endpoint。总5/10尝试路径过，不能掩盖两盒与初始规划失败。

全部路线是把物体的假设平移作为离线几何参数，手仍悬于core6–7mm；未移动仿真物体，没有真实压力、跟踪、摩擦推动，也不含完整机器人连续扫掠。**不能称已修复后绕或直接执行解出来的q。**当前继续仅对两失败Y先盒尝试其余已知合格初始姿态分支（4路径），script screen_rear_top_transport_alternative_starts.py、session37477；未检查最终完成，下一先poll，不重复启动。原全部6布局其他失败仍保留，不能把该有界重试当缩小目标。

2026-10-02T05:58:43.791956+00:00 /proc实核[{'pid': 2696467, 'exists': True, 'state': 'S'}, {'pid': 2696468, 'exists': True, 'state': 'S'}, {'pid': 2802947, 'exists': True, 'state': 'R'}]；STATUS completed35、layout840014，free约40.97GiB，1520冻结源重验零变化。watcher正在840012袋pose_loaded_execution，确认为实际运行，不因等待文件滞后重启。接下来收完原批与全部controls、整组审核/合格准入；并查替代起姿结果与未找到初始姿态，形成完整机器人路径+保持原压力/接触门的物理候选，不能只对容易布局采集。之后合格全范围train/validation转换、真实phase/h10loader与共享训练、untouched独立多seed模型闭环/实际图审继续。

以下为历史记录，以本段为准。

## 2026-10-02T05:31:39.208699+00:00 六完整组已正式审核与实际图审；后绕Y漂移与肘约束角点数值问题有新证据

本轮progress，整体goal active、未完成；上一次Git备份核验属于独立备份任务，不计模型进展。**原12组60条件继续，前6组24推18过、6wait全过，30条实际图审完整；仍仅1合格已准入斜向train组5条，0新转换/模型。** 第7组正在采，不能用前6组或已有容易布局代替全范围。最新具体证据见 KKT_REAR_Y_AND_SIX_GROUP_FINDINGS.json。

**好：840010前后原摆放盒/袋完整1200原source/任务/pose通过**，推进150.1194/253.5644mm、末10最小268.1629/200.7201mm；非目标0、首11q/action0、assist0，盒1倾斜3失载、袋0倾斜7失载。8RGB+4external实际已绑：盒全8能辨双方但木目标后段右下裁切；袋685后目标不可辨。840011交换盒亦通过151.4845mm/末10最小204.3287mm、非目标0、7倾斜0失载；图审0/171双方可辨，342后木目标不可辨。**差：840011交换袋完整1200推进270.8330mm，但末10Y仅152.7895mm，0倾斜11失载，仍top_push、无terminal；不能截断入库。**袋8RGB双方均可辨但手遮挡/底裁切，失败不由抽样目标缺失解释。841005 wait70全11action0、腰3.0873690e−9rad、8RGB稳定已绑。

第五fresh_lateral_04已正式审核：2/4推+wait过、94审核中70过24失败，SHA a12be65a43a0d7100a499660659d7b0fd27c052fe386362d4364b3f8a5e922c6；24项是840008盒/袋各12项，多项因从未进入region阶段（pose_live `assert not selected or bool(regions)`）及其依赖级联失败，不是24个独立物理原因。第六fresh_depth_05已正式审核：3/4推+wait过、全部原控制审核过，SHA846906b05df7c58e4079252f40ec46bcb739baa5290a9254e730794cfef29f11，仍因交换袋原任务失败完整隔离；两组均无准入。原冻结源/判据未改。

**肘部约束诊断**：840007袋175个override逐记录独立重建固定分离轴/支撑顶点。在原5mm间距、1e−6驻点阈值和原active容差下，原11失败中的10个（340–349）在同时计入所有active顶点后通过，残差≤1.741e−7；194仍2.4598e−6不通过。所有active轴唯一，无轴歧义。这说明单个min函数梯度漏掉角点法向组合，但不是给原失败翻案。原审核11失败/完整任务失败保持。55个离线重求解候选（11输入×5）中，固定轴逐顶点约束+ftol1e−14、previous或candidate起点各11/11满足原可行性和驻点门；previous最大1.1734e−8，194为4.8845e−9、命令最大变化.0004079rad。**限定：原形式重求解11/11未精确重现原命令（5.923e−7..3.782e−4rad），不能称精确运行时重放或已定位全部实现原因。**候选保留完整旧目标/界/5mm，未安装runtime、未改冻结审核、未做物理验收。

**后绕新筛查覆盖全部5条已完成rear-selected成功/失败**：原初始X→Y与可用Y预移0/半/全后X→Y，合计15路线、45位置IK起点，保留所有结果。初始safe Y推进约22.26–118.79mm；初版沿旧计划rearX使840008两例20mm门差约2.291微米（初始姿态settle差异），保留false结果。另独立current_geometry版本按实际首帧旋转包围盒重新计算rearX（不降20mm），15路线固定初始包围盒/X桌边通过；只几何筛查，不是手臂/动态/完整桌边或接触证明。IK只改变最后rear掌心请求Y、保持原X/Z、原工作界：840008两例恢复初始Y即可找到位置解，而之前真实漂移Y请求最好仍17.54/24.55mm残差。这支持优先防止侧推错误Y漂移/研究接触方向，不支持盲目增加后绕X/腰范围。840001仅改变到充分Y预移后有精确位置解，但它原rear本就完成、失败在后段，不能把该改动当整体修复。

**真实24子步接触证据**：5例独立observer均过，rear手/目标unsigned Y/X分量时间和比分别.287/.203/.198/.244/.177；不是signed净力或冲量、force/body符号未验证。前三例rear沿正确任务Y分别+64.25/+40.62/+11.21mm；840008袋/盒分别−80.22/−63.19mm，最后有效接触592/162。横向分量大小本身不区分成功，需定位接触方向/姿态和跟随错误Y的反馈链路，不凭比例宣称因果或加压力。

2026-10-02T05:31:39.208699+00:00实际进程核验[{'pid': 2696467, 'exists': True, 'state': 'S'}, {'pid': 2696468, 'exists': True, 'state': 'R'}, {'pid': 2785922, 'exists': True, 'state': 'R'}]，STATUS completed30、layout840012；余量约43.52GiB。当前第7组新增原quality尚未图审，不计入上述24推分母。后续继续原全批逐条实际图审/完整组审核；下一控制候选优先后绕Y偏移和接触姿态、完整机器人扫掠/物理对照，前通道/肘角点候选单独归因。全范围合格train+validation→转换/新腰绝对统计/phase实际loader→共享训练→untouched192推3wait、多seed、真h10和模型图审，目标不变。

以下为历史记录，以本段为准。

## 2026-10-02T05:02:45.370313+00:00 新左右原摆放两推均后绕失败、交换两推过；2311步IK与14端点探针、前通道候选已离线核

**第四组正式审核补充 2026-10-02T05:06:13.541694+00:00：**fresh_reverse_diagonal_0396项原独立审核中95项通过、1项失败（840007袋pose_task_optimality的11帧KKT/stationarity未过，见REVERSE_DIAGONAL_POSE_OPTIMALITY_FAILURE；原判据不改），原任务仍推3/4、wait1/1，GROUP_REVIEWS SHA 5d84196c9bce2d9c50f6158d5bbe80497f9db3d7068bd4c1769153161a3555ec已完成、full_group_checks_passedFalse。固定版approver --apply实际拒绝，三case均无review.json/无GROUP_ADMISSIONS，完整失败组隔离，详见REVERSE_DIAGONAL_ADMISSION_REJECTION。此前pending控制状态是早前快照，现已收齐；当前仍1合格已准入组、0转换/模型。

**最新补充 2026-10-02T05:04:43.580653+00:00：**840009袋完整原source/任务/pose过，推进150.2000mm/末10最小306.2188mm、非目标0、0倾斜5失载；phase3/572/625。8RGB+4external实际已绑，0/171双方可辨，342/513仅左缘暗片难辨目标，685后不可辨。841004等待70帧全11action0、腰最大3.0873812e-9rad、8RGB稳定已绑。第五lateral最终推2/4+wait1/1、整组隔离，当前25条实际图审齐、累计20推15过/5wait过；正式控制审核仍继续。LATERAL04_VISUAL_COMPLETION留证。当前STATUS completed25、layout840010，实际进程状态[{'pid': 2696467, 'exists': True, 'state': 'S'}, {'pid': 2696468, 'exists': True, 'state': 'S'}, {'pid': 2772329, 'exists': True, 'state': 'S'}]；原runner/watcher未停，旧2765067/2771404已终态。

本轮progress，上一轮亦progress；整体goal active。原12组60条件不缩减，**1已准入斜向完整train组5条，0新转换/模型**。当前quality 15/20推、5wait通过，实际图审23条；未图审的新交换袋/等待继续处理，不能先称全部图审齐。

**差：第五lateral原840008盒/袋完整1200均失败**，推进−63.1923/−80.2205mm，rear_push1149/1162帧，非目标0、首零/assist0。各8RGB+4external实际已绑；盒后7RGB木目标右缘严重裁切/手遮挡、袋不可辨；袋后7帧目标左缘/手遮挡可辨、盒不可辨。无rear→top交接、无terminal suffix，不能裁剪入库。**好：交换840009盒原source/任务/pose过**，推进150.1256mm、末10最小265.8653mm、非目标0、3倾斜/0失载；实际8RGB+4external绑，0/171双方可辨、342后木目标不可辨；phase3/344/853原帧全保留。交换袋quality亦已通过，完整inspector/图审进行中。即使余条件通过，第五整组仍因原两失败隔离。

**新后绕诊断** diagnose_rear_approach_stall：两例独立24子步审过，2311原bounded IK重解命令≤5.954e−8rad；盒最后有效手接触162/tick22，袋592/tick12，末100帧物体XY均不动。盒末rear X尚差59.4126mm、掌心误差[20,17.427,−4.151]mm；袋差8.3638mm、误差[16.364,−12.714,−.632]mm。盒123起1077帧waist+.98、袋111起1089帧−.98；双向统计在LATERAL04_REAR_APPROACH_COMPARISON，单episode只统计upper不能把袋upper0误读成未饱和。末工作臂最小奇异值.000381/.000587、条件数1497/973，不能认定全球不可达，工作界不变。

screen_rear_palm_endpoints按绑定URDF/原关节界、active6DOF+固定非工作臂关节，针对两实际末掌心请求各7起点；14结果全部保留，最好残差盒24.5517mm/袋17.5378mm，预算内未找到精确解。仅位置优化，碰撞/路径/物理未验证，不能批准endpoint；有限多起点不是不可达证明。下一优先路径顺序与接触姿态，按REAR_APPROACH_REPLANNING_NEXT.md比较Y预移再X绕行及完整几何/机器人可达性。

**前通道候选离线进展** screen_front_corridor_replanning：3条front-selected共3597行，3151原route_goal重现≤2.23e−12m；成功840001袋/840004盒不变，仅失败840007袋首次754帧提出区间[.3764473,.3788830]中点.3776652m，独立最大双侧余量LP一致。原5mm桌边/12mm通道、其他当前保护与445已锁存停止保持；未验跟踪/全手臂扫掠/接触、不安装runtime。不能把它或Z权重探针说成后绕失败的通用解。

2026-10-02T05:02:45.370313+00:00实际runner2696467/watcher2696468活；STATUS completed25、current_layout840010、collector记录2772329（当时/proc状态R；旧2765067已终态，不重启）。control160/extra106、completed control episodes15、已执行0失败，840007完整审核仍未齐，第四组仍待正式GROUP_REVIEWS。LATERAL_REAR_FAILURE_AND_CORRIDOR_SCREEN_FINDINGS绑定新证据和进程，剩余约44.88GiB。全范围采集/审核继续；之后合格全范围train/validation、转换/新腰统计/实际phase loader/共享训练/untouched192推3wait多seed真h10与模型图审目标完整保留。

以下为历史记录，以本段为准。

## 2026-10-02T04:42:24.323780+00:00 合格数据的模型画面盲区已实际核；反斜向袋通道保护失败、盒的非目标干扰已子步定位

本轮progress，上一goal轮亦progress（首个正式完整组准入）；整体goal active。**当前1合格完整train组5条（fresh_diagonal_02），0新转换集/模型。原12组60条件继续**，不以斜向成功替代完整范围。当前数值13/16推、4wait过、20实际图审齐；首lateral/depth仍各3/4隔离。

**数据问题新证据：已准入斜向组也存在执行中的目标画外。** 四条真实CAMERA_FRUSTUM_DIAGNOSIS独立URDF重构核960个实际相机pose/K样本；840004袋top_push190/292(65.07%)目标OBB完全画外，active468/928；840005盒top_push231/249(92.77%)画外、active399/550；另两条top_push几何无完全画外，但不代表无手遮挡或充分可辨。四条每条0/首推/中推/末推共16真实RGB经过生产224函数，并实际查看。840004袋中/末推、840005盒中/末推目标不可辨，确认不是只在terminal静止阶段丢失。ADMITTED_DIAGONAL_POLICY_PREPROCESS为精确完整production _preprocess_images结果，ACTUAL_REVIEW_BINDING实际16图已绑定；参数占位CPU module无模型权重/无推理。早前ADMITTED_DIAGONAL_MODEL_INPUT只用了resize函数、先归一化，不能冒充完整预处理一致；新版本按真实RGB/255→resize→*2-1执行。原float padding−1会变成−3（显示裁为黑色），仅如实记录，不改训练源或宣称它造成历史分数差。可见性风险不新设逐帧硬门，不删除难帧；原相机/当前冻结源均未改，阶段采样不能补回画外目标。

**好：840007交换盒完整1200原source/任务/pose通过，推进283.8877mm、末10最小205.0319mm；5倾斜、0失载；首零/assist0。差：非目标袋trace最大12.7294mm，接近15mm门。** diagnose_fresh_non_target_contacts独立fresh子步审过，只用每动作24个最早完成solve边界：非目标子步最大12.734142mm(action748/tick11)仍在门内；木盒/袋接触74动作808子步，从447/tick22到748/tick3，最大contact magnitude sum3.9836N；右手/袋候选实际求解力全部0。绝对力幅时间和2.07344Ns不是signed净冲量，不据此作反事实因果结论。episode_contacts.post_action_pose[t]与trace[t+1]精确相同，时间对齐已核。说明真实物体间干扰存在；8RGB+4external实际图审已绑，盒685后不可辨、黑非目标多段裁切/画外，不能从图片称稳定。

**差：840007交换袋失败，反斜向最终四推仅3/4。** 完整1200推进213.6582mm、末10目标Y仅62.3288mm；非目标0，0倾斜/4失载。第754帧进入front_guard_lift，后446帧保持停止，没有settled terminal suffix，不能裁成成功。实际8RGB双方全部可辨（袋手遮挡/下裁切），末段抬手停住；质量失败不来自可见性。独立SciPy原旋转包围盒公式与归档front_top_route_micro复核：袋yaw由−.1551到+.2656rad，X半宽85.3018→91.4473mm；规划桌边余量753时5.1405mm、754降到4.4357mm，恰与原5mm保护触发一致，而当前物体桌边仍7.7922mm。FRONT_CORRIDOR_FAILURE_DIAGNOSIS绑定原源/姿态/trace。

**下一控制方向的限定**：FRONT_CORRIDOR_RESERVE_SCREEN仅离线显示，若保留原12mm通道距离但去掉额外3mm规划预留，754及后446实录姿态的最小桌边余量7.4357mm仍高于5mm。这不是允许删保护/缩安全门，也不证明新轨迹可行；必须检查跟踪偏差、全手臂与连续扫掠/物体姿态演化，再决定重规划或抑制接触旋转的完整物理对照。当前Z优先级离线候选不能被视为解决这个通道失败；不能只加压力或延长1200。

第四wait841003通过，70帧全11action0、腰最大3.0873517e-9rad，8RGB稳定且绑定。audit_closed_peak_trial_group fresh_reverse_diagonal_03返回pending_control_audits（840007两推），正式GROUP_REVIEWS尚未生成，全组已因已知原任务失败保持隔离，无review.json/准入。后台现已进入下一lateral840008，不重启旧collector2748289（已终态）。2026-10-02T04:42:24.323780+00:00实际/proc runner2696467/watcher2696468/collector2758651活，STATUS completed20；control142/extra98、完成control episodes14、已执行0失败，未完成不算通过。MODEL_VISIBILITY_AND_REVERSE_DIAGONAL_FINDINGS绑定证据与进程，剩余约46.01GiB。

继续原完整采集/逐条图审/完整组审核，等840007控制齐后正式隔离第四组；其余不同family原划分/原质量门保留。收齐后才全60pressure绑定/closer，合格全范围train+validation→转换/新腰绝对统计/phase采样实际loader→共享训练→未调参192推3wait多seed真h10与模型画面。当前仍未得到共享策略成功证据。

以下为历史记录，以本段为准。

## 2026-10-02T04:26:12.320158+00:00 首个完整斜向正式组4推+等待全部通过并真实准入；合格数据阶段比例已核

本轮为progress；上一次分拣轮有几何筛查/写入修复证据，中间Git备份核验不计模型进展。**整体goal active、未完成。原12组60条件持续，首个合格完整训练来源组fresh_diagonal_02已真实准入5条；尚无新转换集/模型。** 原四family×3、8train4validation、48推12wait及untouched192推3wait多seed/h10/图审完整目标保留。

**好：fresh_diagonal_02四推4/4、wait1/1，原96独立审核调用全部通过，实际每推8RGB+4external/等待8RGB齐；GROUP_REVIEWS SHA 0288ab1e80a73e57542136102c1e6f284d9a32ae8082296ed14726b3cecfec17，GROUP_ADMISSIONS SHA f721acd1e927b80dd34ef50425b3dc4e4d6687352f7b6189153a019c3ec018bf。** approve_closed_peak_trial_group --apply已实际经过完整checked_sources五条配对合同校验并写三case/review.json，首个真实正向准入路径通过。GROUP_REVIEWS里的admittedFalse是准入前快照，不回写；以独立GROUP_ADMISSIONS为准。首lateral/depth各推3/4仍全组隔离，失败不混入。

新交换斜向袋840005推进150.0156mm/末10最小228.3627mm、非目标0、0倾斜/6失载，实际图审0/171/342双方可辨，后段袋在左缘裁切；wait841002全70帧11action0、腰最大3.08654e-9rad，8RGB稳定。新反斜向首对840006盒150.4417/末10最小301.7712mm、袋150.2575/229.1132mm，两条原source/任务/pose过、非目标0/首零/assist0；盒2倾斜2失载、袋0倾斜5失载。两条8RGB+4external实际已绑定；**差：盒342后目标不可辨（仅边缘片段），袋513后不可辨，图像可学仍未证明。** 840006全正式控制审核尚未收齐，840007交换正在采集，不能算反斜向整组通过。

**真实合格数据曝光诊断**：inspect_admitted_trial_exposure.py只读核准入/整组证据哈希后调用实际production phase exporter，全4870帧保留；ADMITTED_DIAGONAL_EXPOSURE记录start12(0.2464%)、active2800(57.4949%)、terminal1988(40.8214%)、wait70(1.4374%)，四推terminal比例22.42%~53.92%。不是裁数据或选定采样配额；后续按真实全部合格train冻结task/phase配额。真实train-only组调用make_split拒绝无validation，未建转换目录，不伪造全局划分。

**补记前轮几何筛查和准入写入修复**：BAG_VERTICAL_PRIORITY_GEOMETRY_SCREEN对942实际loaded输入的Z任务行/error×2离线候选，独立URDF FK用真实left/right_wrist_roll_rubber_hand；原肘gap重现误差≤1.67e-16m、手参考≤2.76e-7m。失败袋候选最小肘距7.1318mm仍过5mm，原掌桌门无越界、工作手与非目标盒静态无相交；手部朝向误差略增（不是物体倾斜），未验连续扫掠/累计接触，未安装runtime候选。selection用当前动作mean load仅描述性，不能直接当因果运行开关。sorting_quality常量使用当前确切hash并断言原值，不伪称归档源。approve写入修复了checked_sources记录含Path导致summary JSON序列化失败，以及部分写入回滚；旧版保留before_serialization_fix。五个合成writer测试通过（stub源检查），本轮真实正向准入另有证据。

本次2026-10-02T04:26:12.320158+00:00实际/proc：runner2696467/watcher2696468/collector2748289活，current_layout 840007、STATUS completed17；旧2741849已终态，不重复启动。已完成quality 12/14推+3wait，实际图审17条；control140/extra98已执行0失败、complete episodes14，不是整批完成。FIRST_ADMITTED_GROUP_FINDINGS绑定证据和进程，剩余空间约47.87GiB。继续原采集/全组审计；全60结束才pressure绑定/closer；合格全范围train+validation齐后完整转换/新腰绝对统计/实际loader/共享训练。不能只用当前斜向成功组替代多样化目标，相机保持冻结原版。

以下为历史记录，以本段为准。

## 2026-10-02T04:03:16.796255+00:00 首两完整正式组各96原审计通过但均推3/4隔离；袋子失载已子步定位，斜向首对通过

本轮progress，goal active，上一轮有统计入口修复和新失败证据。**后台原12组60条件继续**，04:02UTC实际/proc核runner2696467/watcher2696468/collector2734658（case840005类别交换斜向）活；旧2726629已终态。STATUS completed12；实际当前10推8过（袋4/5盒4/5）、2wait通过、12条实际图审齐。当前源/1200/70/5N/.03/原门/相机未改，0合格完整训练组/转换/模型。

**首次完整fresh组审核真实路径已完成**：GROUP_REVIEWS/fresh_lateral_00.json SHA ee9c70f7bf45ff16e91adf8aa92074348534dd02be06bfc71af72b4cbb2ac7e4、fresh_depth_01.json SHA149fc47f55d0a5d54feff80fdcad395f6f6ecbbf12e77ed5782103f3f7fd2c3e；每组原96审核调用全部通过，但分别后盒/交换袋原任务失败，均推3/4+wait1/1，full_group_checks_passedFalse、全组quarantine。FAILED_GROUP_ADMISSION_REJECTION真实两组拒绝，六个case无review.json，未准入；这是完成负向路径，合格整组正向准入仍未出现。

**好：新斜向840004盒284.1076mm/末10最小205.7605mm、袋300.7269/205.8369mm，原source/任务/pose过，非目标0；首零/assist0。**盒2倾斜/袋6失载；各8RGB+4external实际看并绑定。盒8样本双方可辨（中段手遮挡）；**差：袋0/342双方，171左缘黑片，513起目标不可辨，1027/1199仅左缘木片。**正式其余审核和交换840005/等待仍继续，不能称斜向整组通过。第二wait841001实际8RGB稳定，70全11action0、腰3.0874026e-9rad，原门过。FIRST_TWO_GROUPS_AND_BAG_CONTACT_FINDINGS绑定两完组/新图审/进程。

**袋失载新证据**：diagnose_closed_peak_trial_load_history.py仅把原instant只读诊断的来源validator改成显式fresh、输出改CLOSED_PEAK_TRIAL_LOAD_HISTORY，数学不改；对840002成功袋和840003失败袋均独立子步审核通过。失败15动作peak>.3而末load≤.3，成功5；10次失载退出前通常已有2–3个完全无载动作，不能把全部15事件直接等同10退出。diagnose_closed_peak_trial_contact_migration.py从实际body/COM算两条，每段接触localY由−30到−50mm滑向+60mm附近，两图实际已看；证明失败袋也有滑移，但成功袋同样存在。BAG_LOSS_EVENT_COMPARISON：loaded动作失败454、成功488；竖直绝对载荷均值2.6095/4.9554N、中位2.5856/5.0781N；失败bias中位−6mm已到原下限，成功−5.040mm；虚拟控制点高于目标高度中位3.4049/1.9709mm。它们不是实际穿透深度或有符号净力，不能由此直接增加目标压力。原任务/时长失败保持。

**仅离线的控制分配候选**：screen_bag_vertical_task_priority.py对942个实际loaded输入先重解原bounded IK，全部与保存final命令≤2.98e-8rad；再只把active Z任务行/error乘2（最小二乘Z权重乘4），原关节/测量步长界保持，最大previous slew .0272rad内。BAG_VERTICAL_PRIORITY_OFFLINE_SCREEN：失败袋绝对线性Z残差均值.9131→.2638mm，成功.6096→.1783mm；**代价** BAG_VERTICAL_PRIORITY_NORMAL_TRADEOFF：原加权normal任务残差均值成功1.145→1.316mm，失败2.158→2.431mm。不是实测姿态角，未作非线性几何/累计接触验证，未选定/安装runtime候选、未动冻结源。下一需真实几何/姿态约束复核及其余完整布局结果后判断是否值得物理对照，不能只看Z改善就推广或取消当前完整采集。

后续继续原36commands/60conditions，每条新图审/完整组全审；只有真合格完整组才进入转换及[CLOSED_PEAK_TRAINING_PREPARATION](demo/waist_enabled_20260929_r1/CLOSED_PEAK_TRAINING_PREPARATION.md)的新腰绝对统计、phase sampler/真实loader/共享训练。全60结束才新pressure绑定/closer；原untouched192推3wait多seed实际h10与模型图审目标完整保留。相机实机兼容问题仍未答复，风险保留、不增逐帧全可见硬门。

以下为历史记录，以本段为准。

## 2026-10-02T03:45:56.505828+00:00 前后组已三推通过；修复新训练统计中的旧锁腰假设，真实2470query验证过

**最新补充 2026-10-02T03:48:51.845913+00:00：**前后交换袋840003已完整1200失败，推进257.2121mm但finalY181.6294/末10最小173.7911mm，未达原200mm目标区；非目标0、首零/assist0、0倾斜/10失载。8RGB+4external实际已看并绑定，8样本双方可辨，袋部分下裁切/手遮挡。前后4推最终3/4、wait待采；首8推共6通过（袋3/4盒3/4），两组均不能入库，正式控制审核未齐，0新数据/模型。FIRST_EIGHT_PUSH_FINDINGS为最新。原collector2719034本轮/proc确认已终态（不要沿用下文早前live状态）；runner2696467/watcher2696468仍活，继续原审核及下一wait/布局。DEPTH_BAG_PHASE_COMPARISON实际对照：失败袋top_push477有效相邻间隔推进257.406mm=.5396mm/步，比成功袋499间隔227.395=.4557mm/步更快；但下降443+按压101=544帧，成功216+29=245帧；失败初始到目标距离更长、恢复接触消耗预算，不能照搬后盒滑移低效结论或延长原1200后改判成功。

本轮progress，goal active，上一轮亦有实际图审/接触对照与工具进展。**原12组60条件后台继续**；03:45UTC实际/proc核runner2696467/watcher2696468/collector2719034仍活，当前case840003袋子。旧2712480已终态。STATUS completed7是正式primary等审核计数；实际当前7推+1wait质量/8条真实图审齐。控制watcher尚在840001后盒的audit_closed_peak_trial_pose_loaded_execution（子2721923本轮ps为R），不是卡住即重启；CONTROL29/EXTRA19行当时0失败，完成episode2。首lateral仍推3/4+wait1/1不能入库，完整控制审核未齐。

**好：前后组新增后袋227.1533mm/末10最小200.8383mm、交换木盒174.5114/200.8264mm均原source/任务/pose通过，非目标0；首零11q/action0、assist0。**后袋0倾斜/6失载，交换盒8倾斜/2失载，正式native按driver继续。加上上一前盒152.018mm，前后组目前3条通过，第四条未完成，不能说整组4/4。DEPTH_THREE_AND_TRAINING_PREPARATION_FINDINGS保存实际进程/8质量及8真实图审hash。

**差：新后袋685/856/1027/1199四个抽样目标不可辨，0/171/342/513双方可辨但裁切/手遮挡。交换盒0/171双方、342右缘木片，513起木目标不可辨，黑袋后段部分右下裁切。**两条各8RGB+4external已实际看并绑定，数值成功不证明图像可学。首lateral后盒失败未解，仍0合格完整训练组/0转换/0模型。

**发现并实际修复新训练入口问题**：scripts/prepare_relative_action_stats.py旧末尾assert全部waist0会拒绝真实新腰臂示范。保留旧脚本，新增prepare_closed_peak_trial_relative_stats.py，要求已通过导出审核、全记录显式新waist合同、train/validation与统计episode一致；保留真实LeRobot h10 query/arm10相对、padding排除和原状态统计，只将腰零断言改为原始绝对腰角完整往返验证；统计文件改为校验后才写。新增waist_relative_label_roundtrip.py实际生产处理器验证两真推+一wait共2470query/24565有效未来步，非零腰最大.5382/.7984rad、最大还原误差2.98e-8rad；8个腰清零/手臂篡改/NaN负控拒绝、零等待仍通过。WAIST_RELATIVE_LABEL_ROUNDTRIP_CHECK为小修后最新source，INITIAL仅历史。临时每episode诊断范围未写训练统计，不是批准当前不完整/失败组。

实际新CLI导入/help过，旧锁腰转换集在输出目录创建前拒绝（WAIST_RELATIVE_STATS_CLI_CHECK）；**真实新转换集完整统计路径仍未运行**。可用训练Python是/home/user/Desktop/project/vla/env/.venv/bin/python；torch/transformers/accelerate/datasets/av/pyarrow与本地模型/tokenizer已核。unitree_lerobot conda路径不存在，不再误用；本轮仅CPU检查，无GPU训练。

**新数据曝光审查实际完成**：audit_fresh_trial_training_exposure.py从原raw state/action与全expert_control重新计算8完整episode阶段，失败后盒phase不成立明确保留、不裁失败。TRAINING_EXPOSURE_SNAPSHOT_R1：如全原60均匀帧采样，wait仅1.4374%，推起步3/1200=.25%；沿旧weight16起步仅3.8554%。这是全批假设算式，当前不是训练集；合格train后仍须明确task/phase配额，不把旧合成sampler配额套用。生产phasehook已存在，实际新配额/真实loader审核未完成。

下一按[CLOSED_PEAK_TRAINING_PREPARATION](demo/waist_enabled_20260929_r1/CLOSED_PEAK_TRAINING_PREPARATION.md)：继续原采集→完整组审计/合格准入→转换/逐行视频文本核验→新腰绝对统计/实际phase sampler与h10 loader→共享训练→原untouched192推3wait多seed真实h10/图审。当前源冻结不改；相机实机兼容问题仍未答复，不默认改相机、不将可见风险静默消掉。整体目标不缩减。

以下为历史记录，以本段为准。

## 2026-10-02T03:33:47.551722+00:00 首正式完整组采齐3/4推+1/1等待、拒绝训练；下一前后盒通过；接触迁移与推动效率新对照

本轮分拣为progress，goal active、完整目标未完成。前一次分拣有实际试采/诊断progress；中间Git备份核验不计模型进展，不再重复授权/推送。**后台原12组60条件继续**，runner2696467/watcher2696468/collector2712480本轮03:32UTC实际/proc核活；当前case840002（前后摆放），旧2702647已终态。STATUS completed5是正式执行审核计数；实际已有5推+1wait质量文件，6条实际图审绑定。1520冻结源与原门未修改。

**好：新增前袋357.6522mm/末10最小204.2674mm，非目标0，原source/任务/pose通过；首wait70全11D action0、腰最大3.0874108e-9rad，原门通过，8RGB实际空桌双手稳定。**下一前后首盒152.0180mm/末10最小227.6007mm、非目标0，原source/任务/pose过，6倾斜退出，正式native仍待driver；8RGB+4external已实际看，全部RGB能辨认双方，木目标部分手遮挡/底部和右侧裁切。首零q/action、assist0各核。

**差：本批后盒233.6243mm仍失败，非目标8.3693mm在15mm门内，仍未稳定入目标区。**实际新8RGB+4external已看：0双方可辨，171至1199七个RGB抽样均不可辨目标/非目标。前袋8样本双方可辨但部分遮挡/裁切。首lateral完整推3/4、wait1/1，整组不能入库；原control/extra仍在执行，不能声称完整审计已关闭。audit_closed_peak_trial_group返回pending_control_audits（840001两推），approve helper返回readyFalse，未写review.json。FIRST_GROUP_AND_DEPTH_BOX_FINDINGS保存实际六条/来源/图审hash及活进程；0合格完整训练组、0转换、0新模型。

**新增定位证据**：diagnose_contact_migration.py已对已关闭instant后盒840001和成功前侧盒840004执行，两CONTACT_MIGRATION图均实际查看；后盒7退出位置与独立CONTACT_MOMENT_COMPONENTS_MM逐值1e-10交叉核。后盒重接触由偏边逐渐变为中心附近，但每推动段接触localY向负边迁移约15–39mm，多次倾斜退出；成功前盒也会迁移，故迁移不是充分失败判据。diagnose_contact_drive_efficiency.py与CONTACT_DRIVE_REAR_FRONT_COMPARISON实际对照：后盒同top_push相邻时刻物体约.351–.415mm/action，虚拟手支撑参考约1.008–1.181、目标命令约1.349–1.470，领先手约9.832–13.961mm；前盒末两段物体1.908/1.542、参考2.772/2.623。支持后盒持续相对滑移/低效率，但布局、手姿、参考点/控制分支不同，**不作因果或已修好结论**。recontact selected_surface_local_xy不能直接当物体坐标，新报告坐标从实际COM/姿态重算；虚拟参考不等于真实接触COP。CONTACT_MIGRATION_COMPARISON_FINDINGS留证，不追加压力阈值盲试。

**新准入/总关闭工具**：approve_closed_peak_trial_group.py已实现仅合格整组生成review.json、调用原严格checked_sources完整5条件；失败回滚仅自己新写文件。close_closed_peak_trials.py已实现60条件/12组/四family各3/8train4validation、原报告hash、源冻结、实际图审、执行分母/进程终态、逐family任务失败汇总，默认只核验，--apply只在全齐时写RESULT，不自动训练。实际当前live拒绝提前关闭/整组未齐拒绝准入通过（CLOSED_PEAK_TRIAL_CLOSER_READINESS_CHECK）；**完整正向路径尚未测试**，待真实全批/合格组出现，不冒称已通过。

下一：继续原36commands/60conditions，逐条实际新图审、逐完整组原审核；首lateral待controls齐正式quarantine。相机实机兼容性问题此前已异步询问，尚无答复，当前相机冻结保持。全60齐/进程终态后先verify_closed_peak_trial_pressure_setting.py RUN 5一次，再新closer --apply；不能用旧10条件关闭器。合格组审批→原分组train/validation转换与共享训练→untouched192推3wait、多seed实际模型h10/画面。原质量门/全范围不缩减。

以下为历史记录，以本段为准。

## 2026-10-02T03:09:17.757230+00:00 正式12组60条件试采已启动；首对真实新盒/袋均通过，旧RGB归档释放19.92GiB；instant完整关闭7/8+2/2

**最新补充 2026-10-02T03:12:02.653716+00:00：**首普通盒/袋各1200均通过真实source+原任务/pose，推进150.2261/150.0130mm，非目标均0，首11q/action0/assist0；两条实际8RGB+4external均已看并绑定，盒342起、袋171起目标不可辨风险保留。首case正式8primary+2observer+2pressure已实际全过；FIRST_TWO_FRESH_FINDINGS绑定。STATUS completed2、当前类别交换840001，collector2702647，旧2696537终态。仍0合格完整组/转换/模型，后续控制审计继续。

本轮progress，goal active。**已从单布局诊断推进到真实新鲜试采**：fresh_closed_peak_trials_r1原12组按序、8train4validation、四family各3、48推12wait；1520冻结文件，protocol SHA `8e747a8d12a0eaab4eb4e2ec741e4b51fe14cc848e9b16c991c0629f5db785f0`。02:59:02UTC启动runner2696467/watcher2696468，首collector2696537；最新/proc核runner/watcher仍活，首collector2696537已终态，driver进入该case审核（见PROGRESS_FIRST_FRESH_REVIEW）。真实role=pilot、v2合同SHA b591bd03fa8efd2cb571c972a4aba87a1b430d418bd244bbf1df329573cd04a4、106实际归档来源、解析后设置、原graph/observer核过，ACTUAL_STARTUP_BINDING不是诊断改标签。

**好：首正式普通盒1200原质量/source/pose通过**，推进150.2261mm、末10最小303.611mm、非目标0、首11q/action0、assist0。FRESH_SOURCE_AUDIT验证了新data审核的真实正向路径。已实际看8RGB+4external并绑定；**差：342起木盒目标不可辨**，原camera风险未解决，不以专家数值成功证明模型学会。FIRST_FRESH_EPISODE_FINDINGS完整绑定。当前仍0完整合格组/转换/新模型；首袋及后续完整原组继续，首组包含此前困难后盒，失败不能跳过。

**上一instant已全10关闭**：8推7过、2wait全过，后盒仍234.9598/115.4354mm失败，左右3/4拒绝，斜向4/4仅诊断；36primary80control56extra10observer10pressure、10实际图审全部齐且通过，进程2655738/2655739/2681132全终态。RESULT SHA `6b4ab9e0008ac1c1e36d7c6d22689b2320532c57451f218d98ebbedf8199f573`，FULL10_CLOSED_FINDINGS已写，PRESSURE_SETTING_BINDING已生成，勿重跑close/5N绑定。末斜向盒150.2348/245.1248mm与袋通过，第二wait70全action0/腰3.087382e-9；末盒171起目标不可辨，袋513/685左缘裁切后段只黑片，实际均看。新试采选已完整关闭peak父（两版同7/8+2/2，新final保护无总体收益），不再追加同布局阈值候选。

**新pipeline实现和验证：**23版本native/context模块控制数学保持，加独立fresh micro角色/source版本（旧micro诊断断言已显式适配）；CLOSED_PEAK_TRIAL_SOURCE_BINDING_CHECK_R218合成来源正/拒绝过（临时夹具自动删除，无物理成功冒充），36CLI/15拒绝/6旧参数回归；原完整审核清单变为60条件216primary336extra60observer60pressure、controls按原plan分支，无减门。run_closed_peak_trials.py/watch_closed_peak_trial_audits.py真实后台运行，正式源均冻结不改。source_binding ROOT导入修复后R2重新核，旧R1仅历史。inspect_closed_peak_trial_episode.py与review_closed_peak_trial_episode.py为新逐条工具，前者pressure旧diagnostic角色限制已修为显式verify_closed_peak_trial_pressure_setting.py（全run60/12wait），后者失败也保留独立原pose。audit_closed_peak_trial_group.py已实现4推+wait/全原报告执行与hash/实际图审/真实data门，缺证据pending、失败整组quarantine，不自动写review.json；当前仅完整未齐拒绝路径已实测，完整fresh正向待首组。不能用旧single-group closer/schema代替新全批审核。

**空间问题已处理：**依用户历史清理授权，retired_rgb_archive_20261002_r1严格保护当前冻结文件全文引用的23组和converted provenance原raw；只对23个无活动依赖的已终态早期诊断，115份raw先保存全部非RGB并逐数组dtype/shape/bytes核一致，保留原实际图审、外视、报告和89份各任务成功/失败代表完整raw后删除历史RGB。回收文件分配19.9178GiB，free31.729→51.633GiB；当前冻结1519全部哈希重验通过，模型/训练数据/last均未删。RAW_RGB_PRUNED和RAW_ARCHIVED逐处注明不可恢复完整RGB、不可当完整训练数据；不要再试图对归档raw重验旧hash。新正式60预留17.5534GiB，扣后34.0778GiB，原30GiB门未降。训练checkpoint另预算，旧不足估计保留历史。

下一按[CLOSED_PEAK_TRIAL_NEXT](demo/waist_enabled_20260929_r1/CLOSED_PEAK_TRIAL_NEXT.md)继续真实逐条/完整组审核→转换→共享训练→未调参独立192推3wait、多seed真h10与实际模型画面。仍未完成整体目标，不能以启动任务、首条成功或旧斜向组成功结束。

以下为历史记录，以本段为准。

## 2026-10-02T02:38:45.695033+00:00 首六推5/6+首wait实际复核完成；正式12组试采入口与隔离转换已接入、尚未采集

本轮progress，goal active。instant_guard原任务继续；新增普通盒150.1089/末10最小303.4937mm、普通袋150.0450/268.1078mm原门+pose通过，非目标均0；六推仅后盒234.9598/115.4354mm失败，左右完整3/4仍拒绝。后袋新增压力1115更新逐条复算过，50新增finalhold全部改变局部高度，0倾斜/7失载；普通盒0新增、普通袋24新增，保护并未解决后盒失败。FIRST_FOUR_FINDINGS/FIRST_SIX_FINDINGS保存完整绑定。首70wait全11D action0、腰3.087356e-9rad，原门通过并实际8RGB空桌双手稳定；七条实际图审已齐。0新合格训练组/转换/模型。

实际新画面：后袋0/342双方可辨、171左缘黑片不宜认定目标、513起目标不可辨；856起仅木色细片。普通盒342起目标不可辨、普通袋171起目标不可辨，外视各4帧已看。相机风险仍未解决，不新增逐帧可见门。原CONTACT_MOMENT_COMPONENTS.json把米标为mm，**使用CONTACT_MOMENT_COMPONENTS_MM.json**；力矩值未变。后盒7退出桌面加权localY约−43mm，手−32至−38mm，正负力矩强抵消，非单一手载荷因果证明。PROGRESS_BUDGET后盒有效loaded435帧推进172.782mm约.397mm/帧（父.402），无载恢复349帧；前盒215帧282.887mm约1.316；后盒晚期51帧有包裹间接触>0.05N、首次1051。原非目标门过不代表无阻挡。已有COP/X/联合XY/0.5mm向内约束，不要重复当新方案。

**从反复同布局调参转向完整新鲜试采的具体进展：**prepare_closed_peak_trial.py已生成staged_closed_peak_trial，基于已完整关闭peak_guard父7/8+2/2（不冒充全可行）；仅改启动准入，逆向恢复父collector字节一致，AppLauncher后运行主体完全相同，50辅助Python+2JSON保持字节。fresh_closed_peak_trial_contracts_r1原12组、8train4validation、四family各3、48推12wait不变。check_closed_peak_trial_cli.py真实36命令通过、15错误拒绝、6原diagnostic参数一致；没有启动模拟器。准备过程EULA环境/报告group键错误均已修复；prepare_closed_peak_trial_initial.py保留第一份已写合同所绑定旧builder，已发合同不改。

隔离数据入口closed_peak_trial_data_audit.py/prepare_closed_peak_trial_lerobot.py已建立：显式staged collector/Profile路径绑定，不伪造scripts别名；原质量、pose、完整交换组+wait检查保持。7条真实诊断meta拒绝证据CLOSED_PEAK_TRIAL_DIAGNOSTIC_REJECTION，正向fresh数据尚未验证。**仍不能直接启动旧runner或宣称训练就绪**：约22个native审计需显式pilot/source版本化并验证，原run_fresh_waist_pilot内置审核不够；还需全60条件runner/完整组review准入。

**存储预算不满足下批全量试采：**CLOSED_PEAK_TRIAL_STORAGE_ESTIMATE按实录case全部文件外推60条+25%预留17.553GiB，当前free32.249GiB，原保底30GiB须另释放15.304GiB；训练checkpoint另预算。只读检查datasets36G、dist3.4G、/tmp575M；本轮未删任何数据/checkpoint，不降低原门，继续找非依赖中间产物。下一具体清单[CLOSED_PEAK_TRIAL_NEXT](demo/waist_enabled_20260929_r1/CLOSED_PEAK_TRIAL_NEXT.md)。不改当前instant冻结1519源。

本轮实际/proc核runner2655738、watcher2655739、末斜向collector2681132均活；旧2673547已终态。STATUS完成7，余2斜向推和第2wait仍继续；formal当前进度以PROGRESS_AFTER_TRIAL_PREPARATION及执行文件为准。全部10/36primary80control56extra10observer10pressure和10实际图审齐、进程终态后，verify_top_pressure_setting.py新run5一次（尚未生成）再close_instant_guard_groups.py；不要重启collector。整个目标仍是新鲜完整组→共享RGB11D→未调参独立192推3wait、多seed真实h10及实际模型画面，不能用本诊断分数作完成。

以下为历史记录，以本段为准。

## 2026-10-02T02:05:07.137546+00:00 末载荷首两条1/2完整图审：后盒仍失败、前袋通过；原采集器终态，后台正式审核继续

本轮progress，goal active。instant_guard_groups_r1首后盒234.9598/末10最小115.4354mm仍失败、7倾斜/非目标8.8931mm；首前袋358.0831/204.6982mm通过、非目标0、0倾斜/3失载。两条完整1200、首11D q/action0、assist0/原5N/pose/source均核，实际各8RGB+4外视已看并绑定；0新合格训练组/转换/模型。

前袋1199真实压力更新/1199最终控制状态独立过，17新增finalhold（peak0），16实际高度命令改变、1阶段转换未做局部推导，不能声称17都改变高度；后盒1101更新/1199最终状态、102新增hold中99改高度+3原guard清零结论保留。两条共2300更新已独立过，正式native审核未齐。前袋8RGB双方可辨，171木盒左缘裁切，中段袋被手遮挡/底部裁切；480实际camera pose/K已核，两条top_push OBB排除后盒438/438、前袋0/429。原视觉风险不改。

FIRST_TWO_FINDINGS绑定两条完整证据及实际进程。runner2655738/watcher2655739本轮核活；首collector2655794已确认终态，不再描述为活。首后盒pose_live子进程2662059已结束；FIRST_TWO最新实际子进程2663328正在audit_instant_guard_pose_self_clearance，STATUS completed0是primary收尾计数，非0条采完。余6推2wait、余8图审与全部36/80/56/10observer/10pressure继续，不提前close/训练，不重启原collector或改1519冻结源。全齐终态后原5N全run绑定一次（尚未生成）再close_instant_guard_groups.py。全部既定fresh12组→共享RGB11D训练→untouched192推3wait、多seed真h10+实际模型图审目标保持。

以下为历史记录，以本段为准。

## 2026-10-02T02:01:21.508773+00:00 末载荷完整对照已真实启动；首后盒仍失败，新增保护99次改变高度但倾斜仍7次

本轮progress，goal active。instant_guard_groups_r1冻结1519文件，protocol SHA `03aa4e7ded983dd3eaf67f18ef6fa9be66106ef22645bf79af4f25294a2679ec`，原完整8推2wait/布局/seed/order/1200/70/5N/.03/腰1rad/相机/graph/原门全部保留。只新增instant_load_bias_guard。22显式版本原审核+16来源损坏拒绝+完整driver覆盖36/80/56/10observer/10pressure准备过；不改原数学。实际108归档来源、与父参数仅新flag/两路径差、observer/runtime metadata同父及graph已核，INITIAL_SOURCE_BINDING齐。

**坏：首后盒1200仍失败**，推进234.9598mm/末10最小115.4354mm、非目标8.8931mm；父226.2423/103.1660/6.1776mm。同为7次倾斜退出，峰18.6644N，不能称有效改进。首11D q/action0、assist0/5N/source原pose核；1101压力更新+1199控制最终状态独立逐条复算过，115总hold（peak13、final106、交集4），其中新增102finalhold，99真实高度命令变化、3原撤手guard清零。七倾斜中五次上一末载荷>=5N；首297时peak6.1047/final5.5679、bias−1.9529mm仍倾斜.040094，证明该规则不足以防止倾斜，并非未生效。q18/action7/box63在1e-7已分歧，早于首finalhold269，+8.718mm不可因果归因。FIRST_REAR_BOX_FINDINGS绑定完整证据；正式primary/observer/pressure仍由driver稍后执行，不抢写。

实际8RGB+4外视已看并绑定：0双方；171都不可辨；342右缘木片；513/685/856/1027/1199都不可辨。240实际camera pose/K与FK核齐，438/438 top_push目标OBB几何画外；原相机风险未修复，不增可见门，不重做旧广角静态渲染。

runner2655738/watcher2655739/collector2655794本轮真实核活，当前同case前袋继续；首盒失败不删、不提前close、不改1519冻结源、不并发新物理。0新合格训练组/转换/模型。余7推2wait与9实际图审、全部原审核需完整跑完后，verify_top_pressure_setting.py新run 5一次（尚未生成），再close_instant_guard_groups.py且须进程终态。

空间：原预算预留后不足30GiB时，删除已结束三个/tmp来源夹具（有硬链接，真实回收约78MiB，不能把逻辑260MiB冒充释放），另清理三个无活动编译的Warp .pch临时目录真实回收277.30MiB；原数据/模型/来源/报告不动，清理两JSON有记录。新STORAGE_BUDGET预留3.767GiB后30.219GiB通过，原每case30GiB不降；FIRST_REAR_BOX_FINDINGS最新free约33.70GiB。源夹具仅可复现临时副本删，check报告原hash保留。

后续工具：inspect_instant_guard_episode.py（可wait）；review_completed_diagnostic_episode.py+实际图绑定（wait用render_episode_frames.py原8帧）；diagnose_instant_guard_load_history.py后再diagnose_instant_guard_candidate_episode.py独立压力+父分歧，再diagnose_instant_guard_waypoint_effect.py（只新增finalhold局部高度，不作物理反事实，未推导phase会显式列出）；diagnose_recorded_camera_frustum.py不变。formal报告新INSTANT_GUARD前缀，但raw观察SUBSTEP_*和peak_load_updates.json保持原名。候选无正式训练准入；原fresh12完整配对组→共享RGB11D→untouched192推3wait、多seed真h10及实际模型画面整体目标不变。

以下为历史记录，以本段为准。

## 2026-10-02T01:44:29.831042+00:00 峰值保护完整7/8+2/2正式关闭；末载荷候选隔离接线16CLI过、未启物理

本轮progress，goal active。peak_guard_groups_r1全部10完整、36primary/80control/56extra/10observer/10pressure/10实际图审齐且过，RESULT SHA `5f1ee4d4d1efa03db9493ae561e93b851335d65547fa0a8fa1a9c616c70d67b4`。最后斜向盒150.007/末10最小244.897mm、斜向袋150.191/228.539mm通过且非目标0；第二wait70全11action0、腰3.087381e-9rad和8实际RGB稳定。后盒仍226.242/103.166失败，总7/8与参考无改善；左右3/4拒绝，斜向4/4仅诊断。0新合格训练组/转换/模型。PRESSURE_SETTING_BINDING已生成，close已完成，勿重跑。

末两推各8RGB+4外视实际绑定齐：斜向盒171起木目标不可辨；袋513起左缘黑片仍可辨，勿误说全画外。480实际camera pose/K核齐，top_push目标OBB排除盒228/247袋0/267；原相机/视觉风险不变，无新可见门。末两实际pressure各1199逐条复算过且0hold；下一候选真实前态一跳输入累计8推9390、新增165hold，两wait0，不是累积物理模拟。

新trace+独立math21项/6992合成事件已核；新pressure stream16项（原接触输入加3明确合成边界）过。staged_instant_load_guard已在父正式close后隔离创建，6块剥除parent字节一致、原helpers不改；16真实CLI（含defaultoff/九拒绝）过且未建模拟器。原stage/frozen1402未改。新audit_instant_guard_pressure.py正式audit入口仍依赖未写的新source/contacts/native合同，不能直接运行或套旧audit。下一详见[PEAK_CLOSED_INSTANT_NEXT](demo/waist_enabled_20260929_r1/PEAK_CLOSED_INSTANT_NEXT.md)：显式源合同/原全审核版本化+新pressure文件绑定、完整原8+2driver与预算/冻结，才启动单物理。

runner2612587/watcher2612588/collector2637715本轮ps均终态，无新采集后台。FULL10_CLOSED_FINDINGS绑定完整结论；当前空闲33.68GiB，下一预算须重核，原30GiB每case门不降。完整fresh12组→共享RGB11D→独立untouched192推3wait多seed真h10+实际图审目标保持。

以下为历史记录，以本段为准。

## 2026-10-02T01:25:10.269785+00:00 峰值版六推5/6及首wait通过；末载荷候选未接线检查通过

本轮progress，goal active。peak_guard_groups_r1新增普通盒150.0175/末10最小303.402mm、普通袋150.0646/268.127mm原门+pose过且非目标0；首70wait全11D action0、首q0、腰最大3.0874e-9rad、八RGB实际空桌/双手稳定。前六推仅后盒226.242/103.166mm失败，左右完整3/4仍拒绝。六推+首wait首零/assist0/5N/source与实际图审7条齐；SIX_PUSH_AND_WAIT_FINDINGS绑定，旧阶段报告不改。0新合格训练组/转换/模型。

普通盒峰7.488N、0hold，普通袋11.963N、1hold（461）；六条压力共6992事件逐步复算过。普通盒342起目标不可辨、普通袋171起不可辨；新增各240真实camera pose/K核同，top_push目标OBB画外157/245与229/292。原图像数据风险未解决，保持原相机及硬件兼容问题未答复；不增可见硬门。

**下一候选仅离线准备：**instant_load_bias_guard.py在上一完整24子步末载荷>=原5N且原将下压时保持bias，原peak>10N保护/滤波/上抬/偏置范围/阶段/guards不变；instant_load_control_adapter.py继承观察一次性消费。19边界+11原冻结TopContact转换（含倾斜/失载/错位清零、press→push/descent→press/release）通过；四实录4594独立前置状态逐条复算，新增hold后盒/前袋/前盒/后袋83/18/14/22，都会影响成功轨迹。screen_instant_load_episode.py扩展普通盒/袋2398实录，新增0/18；wait实际pressure空，0update核过。共六实录6992，但不累积反事实状态、不预测任务收益。

INSTANT_LOAD_*CHECK和CANDIDATE_PREPARATION/BINDING记录证据/风险；当前collector完全未import instant_load，未创建新stage/CLI/trace/audit版本/物理。保留已有peak_guard frozen1402。不许直接套旧压力audit给改变后的bias或把离线通过当物理准入。须先当前全8+2完整关闭、余两推输入及wait检查齐、再评估下一单因素物理候选；若采用须显式新flag/meta/源合同/独立数学审计、全部原审核、预算/预检/冻结。原pilot v2与转换盘点本轮只读确认：诊断collector拒pilot，不能改标签入库，未来仍需显式新trial适配与完整组审核。

当前runner2612587/watcher2612588真实核活，STATUS completed7、layout840005；collector2637715本次ps确认活。旧2630422/2636783本次均终态。审核计数见SIX_PUSH_AND_WAIT_FINDINGS：primary26/36、observer7/10、pressure7/10、control40/80、extra21/56，已执行失败总0；不代表未执行通过。下一余两斜向推+第二wait与3实际图审、原全部审核；全齐终态后5N全run绑定一次（尚未生成）、close_peak_guard_groups.py。完整fresh12组8train4val/48推12wait→共享RGB11D→untouched192推3wait多seed真h10目标保持。

以下为历史记录，以本段为准。

## 2026-10-02T01:08:55.376878+00:00 峰值候选首四推3/4；新力矩诊断与角速度预警误报筛查

本轮progress，goal active。peak_guard_groups_r1首四条1200帧完整：后盒失败226.242/末10最小103.166mm；前袋357.894/204.509、前盒285.261/206.913、后袋300.379/205.489mm通过。非目标后盒6.178mm、其余0；四条首11D零/assist0/5N/source与实际各8RGB+4外视齐。独立压力更新后盒1081、前袋1199、前盒1199、后袋1115全复算过；holds11/0/0/15。后袋峰26.067N仍过、0倾斜/6失载退出，不能声称保护限制峰值；后盒仍7倾斜。FIRST_FOUR_FINDINGS绑定四条完整证据，旧FIRST_TWO/首后盒不改。0新合格训练组/转换/模型。

**新增诊断，不是新控制：**diagnose_pressure_filter_lag.py完成原八推连续同阶段2576与当前首两推完整2280压力更新复现无不匹配；末载荷>=5N仍下压原后盒85/候选83，多个成功任务也存在，不可当失败充分条件。diagnose_substep_angular_balance.py已六条真实记录（原后盒/前盒/后袋+当前后盒/前袋/后袋），以world Δ(RIRᵀω)对比signed contact couple+(p−COM)×F，步初/末COM参考都报告；活动目标残差RMS6.83e-7~1.19e-6 Nms，非完全守恒或唯一因果。候选后盒309峰tick手x+.6951/桌面−.6747Nm→净.0204；原成功后袋25N时两者更接近抵消。不能把绝对手峰当净倾覆矩。state.py定义当前prospective核，不回填历史；decoder与runtime归档同hash。

screen_recorded_angular_forecast.py原八+首两3256次一步恒ω姿态预测，next0.03 TP5/FP68/FN20/TN3163，原后盒仅1/7、候选3/7、成功前盒误报18；**不接线此预警控制**。这两FIRST_TWO诊断已封存，不要对新增history重跑（明确len10）。diagnose_peak_guard_waypoint_effect.py局部同状态Z公式核：后盒11holds中7当前高度改变、1被1mm slew截住、3原倾斜guard清零换撤手；后袋15/15高度改变。只是局部命令差，不是关节运动/反事实物体成功。PRESSURE_DYNAMICS_FINDINGS/BINDING详细记录首三阶段诊断，第四条扩展见FIRST_FOUR。

四条960实测camera pose/K核齐；top_push目标OBB几何画外后盒421/421、前袋0/433、前盒0/227、后袋181/282。前盒全8可辨，后袋513起目标不可辨，末两RGB仅左下木片。保持原相机；旧minimum_motion_camera_comparison实际渲染和224审核已完成且硬件兼容询问未答复，勿重复投影当进展/勿擅改相机。

本轮最终ps确认runner2612587/watcher2612588活，collector2621788已经终态；driver实际子进程2629293正审后袋pose_self_clearance，watcher子进程2628812正审首后盒rear_xy。原首collector2612640同为终态。前三条原12primary+3observer+3pressure正式全过；control9/80、extra2/56已执行0失败但未全齐。原剩余四推两wait未完成，不能关闭/训练。FIRST_FOUR_FINDINGS保留真实ps与计数；STATUS的completed是driver收尾计数，不是raw完成数。后续继续原完整协议、余四推两wait和全部图审/审核；所有1402冻结来源不改、不起第二物理、不抢写正式audit。全齐且进程终态后5N全run绑定一次（目前未做）、close_peak_guard_groups.py。完整fresh12配对组→共享RGB11D→untouched192推3wait、多seed真h10和实际模型画面目标保持。

以下为历史记录，以本段为准。

## 2026-10-02T00:53:13.000970+00:00 峰值候选真实首两推1/2：后盒仍失败，11次保护有效但倾斜未减少

本轮progress，goal active。peak_guard_groups_r1原8推2wait完整对照已运行，1402冻结文件全核，protocol SHA `ea5f461be6e1e1bd325cd1f0a682bbcb34bb8604a991a7fe929c3ddc3c4d6db8`。实际105来源/归档逐一核，参数与substep_reference03仅新增peak_load_bias_guard与两路径；观测器安装/graph原样，INITIAL_SOURCE_BINDING为真实启动证据。新增22显式版本审核、15来源fixture/15独立压力流检查、原36primary/80control/56extra/10observer+10pressure完整driver已准备验证后冻结；旧合同/控制数学不改。

**坏：后盒1200帧仍失败**，推进226.242mm/末10最小103.166mm，参考219.434/96.303mm；非目标6.178mm。1081真实压力更新/1199最终状态逐步独立复算通过，11hold、最大峰16.753N，但原倾斜撤手7→7、最大倾斜.04323→.04744。304/307/310/313各hold，间隔仍下压，314 bias−4.232mm、315倾斜.03867撤手。action40/q44/box63在1e-7已分歧，早于首hold304，不能将+6.809mm归因保护；只时序证据，未证明唯一原因或新候选有效。

**好：前袋1200帧原门+pose通过**，推进357.894mm/末10最小204.509mm、非目标0；1199更新/1199最终状态独立过、0hold、峰7.894N。两条首11D q/action精确0、assist0、5N/source核过，实际各8RGB+4外视已看/绑定；不是全native审核关闭。后盒0双方、171均不可辨、342右缘木片、513起均不可辨；前袋八帧双方可辨但有遮挡/裁切。480个真实camera pose/K核齐：后盒421/421 top_push目标几何画外，前袋0/433；不是像素判定或新硬门。旧minimum_motion_camera_comparison_r1实际8套/224尺度已审核，保持原相机不重做未答复兼容决定。

原runner2612587、watcher2612588本轮真实核活；首collector2612640已终态，runner正在执行首后盒audit_peak_guard_pose_live（实际子进程见FIRST_TWO_FINDINGS）。STATUS completed0是primary收尾计数，不能说0条采完，也不能把已退出collector描述为活。当前两条raw已齐；仍需余六推二wait、全部native/observer/pressure和余八实际图审，不提前close。0新合格训练组/转换/模型。

新只读工具 inspect_peak_guard_episode.py、diagnose_peak_guard_load_history.py 保持父数值源码可逆替换；输出PEAK_GUARD_NUMERIC_REVIEW/LOAD_HISTORY。diagnose_peak_guard_candidate_episode.py EP在history后复算压力并比较参考分歧，输出PRESSURE_STREAM_DIAGNOSIS；非正式压力audit，不能代替driver的PEAK_GUARD_PRESSURE_AUDIT。review_completed_diagnostic_episode.py+实际查看后才绑定ACTUAL_REVIEW_BINDING；wait用原8帧。FIRST_REAR_BOX_FINDINGS/BINDING及FIRST_TWO_FINDINGS记录现有证据。勿改1402冻结源/勿并发新物理/勿抢写driver正式audit。全10/36/80/56/10observer/10pressure+10图审及进程终态后5N全run绑定一次（目前尚未生成）、close_peak_guard_groups.py。完整fresh12组→共享RGB11D→独立untouched192推3wait、多seed真h10目标不变。

以下为历史记录，以本段为准。

## 2026-10-02T00:26:14.020163+00:00 子步参考7/8+2/2正式关闭；峰值候选新隔离stage和15真实CLI通过

本轮progress，goal active。substep_reference03_groups_r1 RESULT SHA `e5ca2132d20d372a4a9ec8a346904dbb94c3bf2b9649ce1b6f1cd240a30adc25`，全部10/36primary/80control/56extra/10observer/10实际图审齐并全过。后盒原任务仍失败，左右组3/4拒绝，斜向4/4仅诊断；0新合格训练组/转换/模型。PRESSURE_SETTING_BINDING已在勿重跑。原runner2566837/watcher2566838/collector2591590/2597757逐一确认终态，当前没有原采集/审核后台任务。

更正上一handoff快照：00:22:14报告已80/56 complete且实际ps仅表头，但“watcher本轮核活”复用了更早状态；不能理解为那一刻仍活。当前已真实终态验证并正常close，无原任务重启。旧FULL10绑定不改，纠正记在CLOSED_AND_CANDIDATE_NEXT/BINDING。

staged_peak_load_guard已隔离准备：9默认关闭块剥除后parent字节一致、所有原helpers未改；TracedPeakLoadControl仅previous24tick peak>10N时保持负bias增量，原filter/upward/guards原样。新增真实压力边界trace与每控制帧最终state，raw/meta/plan标记。6真实CLI+defaultoff+8非法拒绝=15通过，未构建模拟器。旧21/15/4800真实interval+8拒绝/2323离线event+14审计证据hash均核；候选未启动物理，不能宣称效果。

**下一具体步骤见CLOSED_AND_CANDIDATE_NEXT.md：**先peak_guard_source_binding（9块、observer不变、实际args/meta/归档）与原审核明确版本化；再独立压力文件audit逐步从真实npz复算峰值/因果时序/滤波/bias/上抬及finalstates与原phase/reset/action交叉核，wait updates必须空，并做损坏拒绝。原36/80/56+10observer不省略，新增10pressure。全部后新完整driver/closer/空间预算/冻结，再启动一个物理原8+2单因素候选。当前只stage/CLI，不要直接拿旧来源审核或直接开跑。

1920真实camera pose/K核齐、后盒407/407 top_push几何目标画外等风险不变；候选不修复视觉可观测性，不新增可见硬门、不改相机。完整fresh12组→共享RGB11D→独立布局多seed真h10目标继续。

以下为历史记录，以本段为准。

## 2026-10-02T00:22:14.390569+00:00 原.03全8推2wait完成7/8+2/2；全部实际图审齐，候选未接线

本轮progress，goal active。substep_reference03_groups_r1全部10采完：仅后盒219.434/末10最小96.303mm失败；最后斜向盒150.284/245.174、斜向袋150.222/228.569mm通过，非目标0。八1200推及两70wait首11D零/assist0/5N/source全部核，10实际图审绑定齐；第二wait全11action0/腰3.087e-9rad、画面稳定。斜向袋513起仍有左缘黑片可辨，不误称全画外。PRESSURE_SETTING_BINDING已生成，勿重跑。FULL10_PRE_CLOSURE_FINDINGS(JSON/MD/BINDING)为新完整证据。0新合格组/转换/模型。

八条CAMERA_FRUSTUM_DIAGNOSIS复用原工具，1920个真实camera pose/K核过、全帧按实测q重建。top_push目标OBB几何画外：后盒407/407、普通盒161/249、普通袋232/295、后袋173/275、斜向盒229/248；前盒/前袋/斜向袋0。不做像素/遮挡保证、不新增门、不改相机；这不是特权状态专家失败的因果解释，但共享RGB学习风险仍重。原raw K偏差按实测K处理，历史未改。

八实录active pressure一步筛查2627条父更新复现、16hold（后盒7/后袋7/普通袋2），只是旧状态一步，非闭环。新增peak_load_update_trace.py与独立audit_peak_load_update_math.py，七条旧状态离线2323事件/16hold及14错误/边界检查过。prepare_peak_load_guard_stage.py --check-only验证9默认关闭接线块、剥除字节还原父，不创建stage；正式prepare要求reference正式RESULT全审核过/原进程终态。尚未接线/新物理，后续需新来源合同和独立真实执行审核。

采集runner2566837/collector2591590/2597757均终态，watcher2566838本轮真实核活；primary36/36、observer10/10全过，control80/80、extra56/56已执行失败0/0，尚未关闭。全齐终态后close_substep_groups.py（5N绑定已在），之后再运行prepare_peak_load_guard_stage.py。完整fresh12组→共享RGB11D→独立布局多seed真h10目标不变。

以下为历史记录，以本段为准。

## 2026-10-02T00:06:31.396435+00:00 六推5/6与首wait通过；候选接触阶段筛查与适配器已验证但未安装

本轮progress，goal active。substep_reference03_groups_r1新增普通盒150.241/末10最小303.625mm、普通袋150.051/268.113mm均过原门且非目标0；后盒仍失败，六推5/6。第一70wait全11action0/首q0，腰3.087e-9rad、八实际画面空桌/手稳定。六推各8RGB+4外视及首wait绑定齐。普通盒342起/普通袋171起目标画外，原视觉风险保留。SIX_PUSH_ADAPTER_FINDINGS/BINDING保留新证据；原四推绑定未改。0合格新训练组/转换/模型。

未安装peak_load_control_adapter.py保留原压力滤波与上抬，仅上一24tick峰值>10N阻止负bias增量；15项包含真实冻结region_top_contact的press→push、倾斜撤手、失载、偏置清零与inactive测试通过。peak_load_observation.py纯读取器对四真实4800interval与独立history逐值一致，8损坏/只读检查通过。原pureguard21项不变，新旧报告源hash核过。六实录扩展top_press/top_push/press→push一步筛查2055条父控制均复现，后盒/前袋/前盒/后袋/普通盒/普通袋各改7/0/0/7/0/2步（共16）。成功普通袋也受影响，不能声称候选无退化；不累积旧状态预测轨迹，未接线/未新物理。

当前runner2566837/watcher2566838/collector2591590真实核活，旧2584367/2590630终态，completed7、layout840005继续；原36primary/80control/56extra/10observer仍未齐，尚不关闭。下一先完整8+2及全部图审/审计终态，5N绑定一次+close；之后才新stage默认关候选、原完整协议/独立压力审计。保持完整fresh12组→共享RGB11D→独立布局多seed真h10目标。

以下为历史记录，以本段为准。

## 2026-10-01T23:53:47.427553+00:00 子步首四推3/4；后袋25N仍成功，峰值候选存在跨任务影响

本轮progress，goal active。substep_reference03_groups_r1当前四推完整：后盒失败219.434/末10最小96.303mm；前袋357.803/204.418、前盒285.236/206.889、后袋300.956/206.066mm通过，后三非目标0，后盒5.249mm。四1200帧/首11D零/assist0/5N/source与实际各8RGB+4外视齐。前盒均可辨，后袋513起目标大多画外；原相机风险保留。FOUR_PUSH_FINDINGS/BINDING为新证据，旧绑定未改。0新合格组/转换/模型。

**反例：**后袋峰值24.955N高于失败后盒17.778N且成功、无.03倾斜，不能峰值大小当失败充分条件。未安装peak_load_bias_guard纯函数与check21项通过；四真实top_push连续旧状态一步筛查399/426/216/269条，后盒/前袋/前盒/后袋各改7/0/0/7步（最大0.5mm）。非闭环反事实，未筛top_press和转换；不能宣称无跨任务影响、不能仅凭后盒候选就安装。

新diagnose_substep_linear_balance.py四实录独立线动量检查：真实mass/dt/shape_body、body_qd前三world COM线速度；初始支撑mg吻合，主动物体子步冲量残差RMS1.07e-5至1.50e-5Ns。后盒308/312/315峰值对应实际动量与接触+重力预测残差1e-9至1e-8Ns，非简单记录噪声；手绝对载荷≠物体净力，未验证角动量/唯一因果。state.py定义是当前新增来源说明，不回填历史。

runner2566837/watcher2566838/newcollector2584367本轮真实核活，旧2575776终态；completed4，layout840000继续。原1288冻结hash全核通过；36primary/80control/56extra/10observer尚未齐，勿提前关闭或重启。全齐终态后5N绑定一次+close_substep_groups.py。继续完整组/其余任务候选影响与阶段评估；不并发第二物理、不改冻结源，完整fresh12组→共享RGB11D→独立布局多seed真h10目标不变。

以下为历史记录，以本段为准。

## 2026-10-01T23:32:51.700279+00:00 原.03子步完整组已运行；首后盒失败但发现17.8N瞬态被末tick漏采

本轮progress，goal active。先21版本化审核仅来源重命名+observerbinding、原数学不变；独立文件18项/来源11项检查通过，原36/80/56+新增10子步审核完整driver已验证。归档SHA去重53组2278副本，无删路径/内容、无工作源链接，释放7.624GiB，两个封存结果证据与原frozen复核无变；IMMUTABLE_ARCHIVE_DEDUP_RESULT/OPERATIONS保留，归档今后必须只读，编辑先复制到新inode。余38.2GiB支持新run预算3.695GiB且保留原30GiB每case保护。

新substep_reference03_groups_r1冻结1288，protocol SHA `f6ad28c8a3e0ecf1a0bba64627f3aa16e923acfdae563c4d5b93217109004bc2`；保持原.03/5N/graph/相机/layout/seed/order/1200/70/8push2wait，只加observer，未改生产源。runner2566837/watcher2566838/collector2566889真实核活。首实际101归档源与参数差只有observerflag/两路径核绑定INITIAL_SOURCE_BINDING；实际安装/RTX图捕获成功，24子步、8manager、32记录；body IDs30/34、质量0.18/0.20kg、局部COM0已真实绑定，不回填历史。

首后盒1200完整 **219.433717/末10最小96.302807mm仍失败**，非目标5.248689mm；首11D零/assist0/5N/原pose/source核过。实际8RGB+4外视绑定：0双方可辨、171双方不可辨、342木片右缘、513起双方不可辨。真实子步38400记录/350488接触通过独立audit并存于SUBSTEP_LOAD_HISTORY.independent_audit，勿抢写正式SUBSTEP_CONTACT_AUDIT（runner后续会生成）。REAR_BOX_RESULT/FIRST_REAR_BOX_FINDINGS与绑定齐。0新合格组/转换/模型。

**新证据：**28action期间peak>0.3末tick<=0.3，maxpeak17.778N vs末tickmax6.762N；5action瞬间倾斜>0.03末tick未超。308/312/315 top_push peak17.767/17.134/17.778N却末0，下一步实录下压bias各-0.5mm，到317累计约-4.814mm，318倾斜退出。均值也仅1.731/1.372/1.662N，不能直接声称均值能治；重复边界竖直载荷差0。SUBSTEP_PRESSURE_FEEDBACK_FINDING只记录时序关联，非因果/新控制成功。绝对载荷时间和不是净冲量，state/force评估时刻不混同。

当前前袋采集继续（最新进度以真实文件为准）。下一继续全部8+2/原审核+子步审核/实际图审，全齐终态后5N绑定+close_substep_groups.py。数值复核用inspect_substep_episode.py（新binding原数学一致）；图审原工具；diagnose_substep_load_history/pressure_feedback只读。严禁修改冻结源或并发第二物理。完成当前组后再评估考虑峰值/失载、防止继续下压的受限反馈候选，原fresh12完整组→共享RGB11D→独立布局多seed真h10目标保持。

以下为历史记录，以本段为准。

## 2026-10-01T23:10:44.107564+00:00 撤手.05正式7/8+2/2关闭但有1主审核失败；GPU观察器验证通过，下一回到.03

本轮progress，goal active。tilt05 RESULT SHA `1c44d1a83bb4f3f474476203e27c89df543c3afd162dad7907c5250a345b58ca`；完整10/36primary/80control/56extra/10实际图审齐，80/56全过，但前盒audit_tilt05_micro_clearance_live主审核失败；后盒原任务仍失败221.308/末10最小100.560mm。左右3/4拒绝，斜向4/4也因该审计拒绝。0新合格训练组/转换/模型。runner2519113/watcher2519114/collector2544260/2550363均已真实终态，当前无物理或审计后台任务。

**重要纠正：**此前阶段“已执行0失败”漏了前盒主审核；MICRO_GUARD_SCOPE_CORRECTION独立复算535/536 tilt .0319858/.0401751，实际.05 guardFalse但原audit硬编码.03True。front_top_route_micro将同一个tilt_guard传给MicroClearanceReturn，并非微小返回仍独立.03。之前合同/描述这一点错误，保留冻结历史和失败，不改原审计补绿。两帧stage_changed/restarted/retained都False，不能夸大动作影响；原正式姿态.20不变。该候选同7/8未改善，下一明确用已完整审计过的box_inward_groups_r1原.03作observer baseline。

SUBSTEP_RUNTIME_BRIDGE_GPU_CHECK20项真实CUDA捕获/重复replay通过（两路径完整24子步25/32样本、输入变化实时采到、停用/溢出、输入byte不变），但只是合成数组、未初始化Newton物理。SUBSTEP_RECORDING_CHECK13项用真实旧接触包合成子步，末样本6Dforce/pose/ID比对、压缩往返与损坏拒绝通过。staged_substep_observer已隔离准备，新增9段默认关闭观测剥除后与parent逐字一致，原helpers同；有0.05CLI13历史报告及**REFERENCE03_PRELAUNCH_CHECK13项**，后者才用于下一原.03。尚未冻结/启动场景，未有真实子步采样。检查全部source哈希已再核。

下一详见SUBSTEP_REFERENCE03_NEXT.md：先显式更新stage来源合同及引用的原审核（控制数学不改）、独立packed子步文件审核/真实源绑定、完整原8+2/36/80/56+新增子步审核协议；空间预算再冻结启动。不能旧合同source失败后跳过；不能默认相机/反馈/graph变更。当前余约31GiB，下一8+2会逼近30GiB原每case保护，不可静默降门。源/原数据未删。完整四族12fresh组→共享RGB11D→untouched独立布局多seed真h10目标保持。

以下为历史记录，以本段为准。

## 2026-10-01T22:56:13.669720+00:00 撤手.05全8推2wait采完且实际图审齐：7/8+2/2，正式审核继续

本轮progress，goal active。8推1200帧原任务/pose7过，仅后盒221.308/末10最小100.560mm失败且非目标8.280mm，父同7/8，左右完整3/4仍拒绝。最后斜向袋150.219/228.567mm通过且非目标0；513起目标仍有左边缘黑片可辨，不能称完全画外。两70wait全11action0/首q0、腰约3.087e-9及八RGB实际稳定。全10图审绑定齐、首零/assist0/5N PRESSURE_SETTING_BINDING已生成勿重跑。FULL10_PRE_CLOSURE_FINDINGS绑定本轮完整终采证据，旧SEVEN_PUSH/FIRST_THREE不改。0新合格训练组/转换/模型。

runner2519113、collector2544260/2550363已终态；watcher2519114真实核活，primary36/36、control40/80、extra26/56，已执行0失败但尚未完整；RESULT不存在。待80/56齐且watcher终态后close_tilt05_groups.py，禁止提前关闭/重启。原1206冻结源全核未变。

独立子步缓冲18项、installed decoder9项、新substep_contact_runtime_bridge.py假manager19项隔离CPU全过并再核报告源哈希。尚无真实安装/真实子步记录/GPU graph验证，未改当前physics或反馈。旧CPU cuda_disabled误标由单独隔离重跑报告明确纠正，不改旧报告。下一详见SUBSTEP_INTEGRATION_NEXT.md：正式关闭后GPU重复replay→隔离接线→完整同源物理与原末tick一致性→因果诊断再改专家。完整fresh12组→共享RGB11D→untouched独立布局多seed真h10目标保持。空间约31GiB，无删除。

以下为历史记录，以本段为准。

## 2026-10-01T22:52:41.332107+00:00 撤手.05七推6/7与首wait通过；子步回调桥CPU验证完成但未安装

本轮progress，goal active。七推均完整1200帧/首11D零/assist0/5N/.05/source与各8RGB+4外视实际绑定；后盒221.308/末10最小100.560mm仍失败，非目标8.280mm；后袋299.925/205.035、普通盒150.221/303.606、普通袋150.025/268.088、斜向盒150.207/245.097mm通过且非目标0，前袋/前盒亦通过。第一70wait全11action0/首q0、腰3.087e-9及八RGB实际稳定。0新合格训练组/转换/模型。SEVEN_PUSH_OBSERVER_FINDINGS及绑定为完整证据，旧FIRST_THREE不改。原视野风险保留：普通盒342起、普通袋171起、斜向盒171起目标画外；后袋大量帧目标不可辨。

子步观察器独立缓冲已实现，隔离CPU18项、installed decoder解析9项、新substep_contact_runtime_bridge.py假manager19项通过。旧CPU报告cuda_disabled误标已单独隔离重跑报告纠正：全部原运算CPU但当时CUDA仍枚举；新进程CUDA_VISIBLE_DEVICES空且0设备。未改旧绑定文件；未接真实collector/未测GPU图/无真实子步数据。桥只独立数组写、支持24子步25或32样本，安装前拒绝已捕图，记录actual mass/COM/inertia/mapping，原反馈不替换。下一见SUBSTEP_INTEGRATION_NEXT.md；先当前全组关闭，再GPU replay验证/隔离接线/完整同源物理与末样本一致性比较。不凭单次2mm改善下因果结论。

runner2519113/watcher2519114/collector2544260本轮真实核活，layout840005后袋继续；已primary26/36、control40/80、extra22/56且已执行0失败，但尚未全齐。1206冻结源本轮全核无变，余约31GiB，未删数据。余全8+2/36/80/56/10图审与进程终态后5N绑定+close_tilt05_groups.py；不提前启动下一物理。原四族12完整fresh组→共享RGB11D转换训练→独立untouched192推3wait、多seed真实h10及实际画面完整目标保留。

以下为历史记录，以本段为准。

## 2026-10-01T22:26:57.861895+00:00 撤手.05前三推2/3：后盒仍失败；确认24子步仅末帧受力的观测缺口

本轮progress，goal active。tilt05_groups_r1首三条1200完整数值/首11D零/assist0/5N/.05/source及实际各8RGB+4外視已绑定：后盒221.308/末10最小100.560mm失败（非目标8.280mm）；前袋357.767/204.383、前盒283.863/205.516mm通过且非目标0。0新合格组/转换/模型。FIRST_THREE_FINDINGS及绑定为本轮完整证据，不重写。

后盒较父只+2.146mm，倾斜退出8→7、最大倾斜.047119→.063527；加载417→431帧/净160.334→164.124mm，无载恢复351→342，有载回退8.880→12.017mm。盒袋非零受力32→38帧，首1073→1060，仍晚段干扰。新只读diagnose_tilt05_episode_comparison.py同时独立复现父完整bucket精确相等；action7/q20/box64已>1e-7分歧，阈值暴露304，不能归因2mm。新旧末tick力矩对比与旧准静态分析均已完成；nearflat越界父1/新0，不支持简单静态倾覆解释，旧about_com字段实际关于poseorigin且忽略惯性/非目标力，不能当动态证明。

SUBSTEP_OBSERVATION_GAP由inspect_substep_observation_gap.py实际绑定：control1/15s、physics1/120s×3，即24子步/control，当前只记录最后一子步。NewtonManager实际归档与当前SHA一致；CUDA图内pre-substep/post-final回调已查，需固定独立GPU观测缓冲区并保留原graph/物理/反馈，补真实mass/COM、序列与forcebuffer不变检查。尚无子步观察器实现/安装，未改IsaacLab。mjwarp_manager/support.py仅新检查绑定，不回填历史来源。deterministic_mode=not_guaranteed只是配置，非已证明根因。

RECENT_VARIANTS_REVIEW完整保留：旧全后1.5mm后盒277.684但后袋失败；旧box-only是1mm，当前box1.5/bag3同时加center/lift/inward；干净box1.5/bag3无额外改动未做。无新候选stage/合同/下一物理，不盲目再提阈值。先完成当前全8+2并补观测/重复辨别再决定控制策略。

runner2519113/watcher2519114/collector2528937本轮核活，layout840004后袋采集中；control9/80、extra0/56当前未齐；旧collector2519166终态。1206冻结文件全核无变。后续继续tilt05_inspect_episode.py/原图审/实际绑定；全齐终态后原5N绑定+close_tilt05_groups.py。空间约32.00GiB，未删除。所有原质量/完整新鲜12组→共享训练→独立布局多seed真h10目标保持。

以下为历史记录，以本段为准。

## 2026-10-01T22:04:50.100246+00:00 内移完整7/8+2/2正式封存；同源内部撤手.05完整对照已运行

本轮progress，goal active。box_inward_groups_r1正式RESULT SHA `1940997787d160a15e7fe48ea7ddf33518561ac8bd7332112eab9d34231c8f44`，全部10/36primary/80control/56extra及10实际图审齐，所有control/extra/primary审核过，但后盒原任务门失败；推7/8、wait2/2，左右组3/4拒绝、斜向4/4仅诊断。旧runner2482917/watcher2482918/末collector2513189已终态。PRESSURE_SETTING_BINDING已生成，勿重跑。新完整数字/图审事实见FULL10_PRE_CLOSURE_FINDINGS，旧记录不改。

下一tilt05_groups_r1已冻结1206文件，协议SHA `de381a8ff1903408cc192a76efe373898724e1b7be6c8fd640d0b33a20112204`；仅同一collector内部撤手.03→.05，正式.20、micro-return.03及原5N/相机/所有门/原8+2/预算/layout/seed不变。runner2519113、watcher2519114、首collector2519166本轮真实核活，首840001正在采集，97真实归档与父全部同源，实际args仅路径/阈值差已绑定INITIAL_SOURCE_BINDING。尚无完整新raw，不宣称首零或成功。

新tilt05_inspect_episode.py/TILT05_INSPECTOR_PREPARATION已加入冻结：原数值AST一致，新显式核实际.05/source/protocol，以当前inward为父，输出TILT05_NUMERIC_REVIEW。后续push完整用此脚本+原review_completed_diagnostic_episode.py，再实际查看/绑定；wait原八帧。全10/36/80/56+10图审及进程终态后5N绑定+close_tilt05_groups.py。禁止编辑冻结源，不能把诊断转训。

详见[TILT05_PROGRESS](demo/waist_enabled_20260929_r1/TILT05_PROGRESS.md)。空间约32.76GiB，父2.156GiB；此次仅只读盘点未删数据，fresh60与训练前再预算。仍0新合格组/转换/模型，四族12完整新鲜组→共享RGB11D→独立untouched192推3wait、多seed真h10+实际画面目标完整保留。

以下为历史记录，以本段为准。

## 2026-10-01T21:56:20.082560+00:00 内移完整8推2等待及实际图审齐：7/8+2/2；正式审核继续

本轮progress，goal active，0新合格训练组/转换/模型。box_inward_groups_r1全部10 raw已完成；八推原数值/pose7过，后盒219.162/末10最小99.763mm失败且非目标7.694mm，父版同为7/8，未解决完整左右组。新增普通盒150.230/303.615、普通袋150.081/268.144、斜向盒150.092/244.982、斜向袋150.273/228.620mm皆过且非目标0。两70wait全11action0、腰约3.087e-9；10条首11D零/assist0/5N已核，全部8RGB推另4外视实际复核绑定，PRESSURE_SETTING_BINDING已生成勿重跑。FULL10_PRE_CLOSURE_FINDINGS为带哈希的阶段证据，不替代RESULT。普通盒342后、普通袋171后、斜向盒171后目标不可辨；斜向袋513后仍有左侧袋边缘可见，勿写完全画外。

采集runner2482917/collector2506663与2513189均终态，36primary齐。watcher2482918与其实际audit子进程本轮核活：control57/80、extra35/56当前0失败但未全齐，不能关或重启。1179冻结源本轮全核无变，余约33GiB；只读空间盘点未删文件。待80/56全齐+watcher终态后直接close_box_inward_groups.py，然后prepare_tilt05_groups.py/核冻/单物理启动。tilt05_groups_r1尚不存在。新tilt05_inspect_episode.py及TILT05_INSPECTOR_PREPARATION数值AST保持，新增显式.05/raw-plan-source核验、父对照改当前inward，prepare已要求冻结前核此报告。其余既有检查未重写。

暂停旧pilot适配研究于只读，没有新增pilot合同/适配器或试采；既有staged collector只允许diagnostic，不能把数据改标签。下一仍完成内部撤手.05全8+2对照，原质量门保持；四族12fresh完整交换组→共享RGB11D→独立untouched192推3wait、多seed真实h10和实际图审仍未完成。

以下为历史记录，以本段为准。

## 2026-10-01T21:38:07.334122+00:00 内移前四推3/4；后盒仍失败、发现生效前轨迹分歧；内部撤手候选预检完成

本轮progress，goal active，0新合格组/转换/模型。当前box_inward_groups_r1四条1200帧完整数值/源/5N/首11D零位/assist0/实际8RGB+4外视复核：后盒219.162/末10最小99.763mm失败（非目标7.694mm）；前袋357.949/204.564、前盒284.715/206.368、后袋296.201/201.311mm通过，非目标均0。图像目标画外风险保持明确。FIRST_FOUR_FINDINGS与绑定记录详细证据，不重写已绑定报告。

后盒倾斜退出6→8、无载重接触349→351、加载408→417，15/53向内命令实际材料相对物体仍向外；未解决持续接触。盒袋实力32帧、首1073、峰1.154N，晚段干扰存在但非全部根因。新修正296才首次作用，但upper action17/q18/box66已经差>1e-7；布局/随机化/配置/碰撞数组同，不能把13.7mm涨分全归因新控制。

下一候选准备同一已冻collector只改内部撤手.03→.05；正式upright.20、micro-return自身.03、其他门/预算/全部8+2保持。TILT05_DIAGNOSTIC_CONTRACT_CHECK（2核心AST、8坏metadata/旧实录拒绝）与TILT05_RUN_PROTOCOL_CHECK（6真CLI/非法.20拒绝/完整36/80/56）已通过并核当前哈希。prepare_tilt05_groups.py已写未执行，尚无tilt05_groups_r1目录或下一物理。父清单未含search_reward.py，TILT05_SOURCE_EXPECTATIONS显式新绑定，不回填历史。

当前runner2482917/watcher2482918/collector2499728本轮核活，layout840000，旧2482971/2491995已退出。control9/80、extra5/56已执行0失败，仍未完整。1179源全核无变。清理已逐文件匹配保留tar.gz的旧dist重复53wheel副本，释放2.9118GiB，余约33.9GiB，归档/代码/模型/实验数据保留；恢复说明与DUPLICATE_WHEELHOUSE清单齐。

详见[BOX_INWARD_PROGRESS](demo/waist_enabled_20260929_r1/BOX_INWARD_PROGRESS.md)。继续剩余4推2wait与全部正式/实际图审；全齐进程终态后5N绑定和close_box_inward_groups.py，再评估冻结下一对照。四族12fresh完整交换组→共享RGB11D训练→独立untouched192推3wait、多seed真实h10+实际画面目标不变。

以下为历史记录，以本段为准。

## 2026-10-01T21:06:32.406793+00:00 抬手完整7/8+2/2封存；0.5mm内移完整物理对照已启动

本轮progress，goal active，0新合格训练组/转换/模型。抬手版10条件+36primary/80control/56extra+10实际图审齐，RESULT SHA `b2e32c7006fbeb63bd453cafb4a5150a5a45a97bbb4d50301d35e0dde36c74e2`，左右3/4拒绝、斜向4/4仅诊断。后盒205.457mm/末10最小83.106mm失败；control3/extra6正式失败保留，独立实测pose补充通过不覆写。末两推150.102/150.258mm且非目标0、两等待全11action0已实际复核；相机目标画外问题保持可见。旧进程已终态。

接触材料点独立分解显示近倾斜实际向内运动仍可被物体平移/旋转抵消；常速度外推p95反而较差，未采用。63输入0.5mm独立全过；1mm step317 KKT超原门拒绝，189总体passedFalse保留。0.5mm平均名义前进0.860→0.460mm是实质风险，需完整物理。

新staged_box_inward_correction默认关仅右后盒原edge资格加0.5mm；7类启动检查通过（含25版本AST、63独立、4原生169events/21拒绝、6CLI+7非法），旧源/质量门不动，入口审核采用已验证实测pose修正。冻结1179，协议SHA `32d25be44da3fe760cf8c471577dfbf9ba2315a3ac82b4c30de85bb8f85861d8`，runner2482917/watcher2482918/collector2482971本轮已核活，首840001进行中，97真实归档源匹配；实际live画面两物体不可辨。未宣称新轨迹成功。

详见[BOX_INWARD_PROGRESS](demo/waist_enabled_20260929_r1/BOX_INWARD_PROGRESS.md)。下一步新完整raw用inspect_box_inward_episode.py→原图审工具→实际查看/绑定；10条件+36/80/56齐且进程终态后5N绑定/close_box_inward_groups.py。禁止修改冻结源。原四族12新鲜完整交换组→共享RGB11D训练→untouched192推3wait、多seed真实h10及画面目标保持。

以下为历史记录，以本段为准。

## 2026-10-01T20:27:54.577906+00:00 抬手前三推2/3；真实高度审核补充通过，后袋继续

本轮progress，goal active，0新合格组/转换/模型。box_entry_lift_groups_r1已数值/原pose/源/5N/首11D零位/assist0/实际8RGB+4外视复核前三条：后盒205.457/末10最小83.106mm失败（非目标2.170mm）；前袋358.237/204.852mm通过；前盒284.544/206.197mm通过，后两者非目标0。前盒八RGB两物体可辨、171/342手局部遮挡。后袋当前840004仍采集，driver2448024/watcher2448025/collector2455538刚核活；首collector2448086已终态。STATUS completed_conditions2是driver primary收尾计数，不能据此忽略已完成第三条raw。

**正式审核失败原因新增：**后盒多个依赖原audit_box_entry_lift_events在实测最低高度与URDF FK高度1e-8比对失败。40真实抬手事件按记录observed_hand_pose重算误差精确0，FK最大差2.500794e-7m、姿态差2.655587e-7，原0.84m高度判断全部一致。不得修改冻结审核或回填旧失败。

**独立补充已完成：**新增audit_box_entry_lift_events_measured.py只将ready所用高度改为独立顶点×实测手位姿复算，保持原1e-8记录一致性、FK/实测pose1e-4、0.84m入口/三帧ready/全部其余数学不变。新audit_box_entry_pose_measured_supplement.py只新import/来源/输出，native完整流程AST一致。check_box_entry_measured_height.py复现原失败、40真实lift事件全过、height/pose/ready三类篡改拒绝。session79414/PID2458674已exit0：完整后盒1200frames、349commands、7handovers补充通过，文件BOX_ENTRY_POSE_MEASURED_SUPPLEMENT.json SHA `8aefeec73e6c0d01c56a06c472790819e564de064468415dc308961189b891c1`。原正式失败和任务失败仍保留，补充不授予训练资格；后续新审计版本需纳入此纠正并做回归。

实体控制发现见下一段：抬手确实消除高度阻塞但无载恢复349vs180帧、净有载推进146vs194mm；木盒后段与黑袋12帧非零接触峰1.051N，但发生晚、不是整个失败唯一原因；六次倾斜前已有5–6/8帧边缘纠偏，不能只归因为触发过晚。不得盲目加中心权重/减步长/放宽预算。下一改进应基于已执行纠偏的实测材料点相对运动、力方向及目标绕障通道；未接线下一候选。

下一步继续本轮全8推2wait、36primary/80+56/10实际图审，保留全部失败；后袋等完整后inspect_box_entry_episode.py、实际图审；全齐后原5N绑定+close_box_entry_groups.py。1079冻结源上次全核无变，首case95归档已绑定，禁止改冻结代码。整体仍四族12fresh完整交换组48推12wait/整体split→共享RGB11D→独立未调参192推3wait多seed真h10和实际画面；尚未达到。

以下为历史记录，以本段为准。

## 2026-10-01T20:20:49.918251+00:00 抬手后盒仍失败205.457mm；前袋通过；已确认后段盒袋受力与纠偏仍失效

本轮progress，goal active；0新合格训练组/转换/模型。当前唯一box_entry_lift_groups_r1首840001两条完整1200已实际8RGB+4外视复核绑定：**后盒失败205.456875mm/末10最小83.106123mm，非目标2.170051mm；前袋通过358.236834/204.852000mm，非目标0。** 首11D q/action零、assist0、5N/source核过。首pair1/2非完整组成功。后盒差于父255.201/137.138mm；新后盒RGB171起七样本双方不可辨，前袋八样本双方可辨但中段遮挡/裁切，不能证明RGB模型可学。

**有效改善及边界：**六次补抬手共40frames全部完成，height-blocked记录0，七次中心规划/交接齐、最后1168交接，不再unfinished路径；不是分拣成功。全部无载验证路径349frames（父180），有载推408frames净146.059mm（父448净194.259），倾斜退出仍6次。中心落点逐次改善：实际首次COP半径50.89→13.18mm，但每次推后COP仍滑向局部Y约−33mm；重复恢复与有载效率是主要待解方向。FIVE_VARIANT预算/力矩、LANDING_TRANSFER、ENTRY_RECOVERY记录齐。

**任务干扰真实证据：**不能把几百帧零力接触manifold当碰撞受力。排除零力后，新轨迹盒袋力>0.05N共12frames，首1112，峰1.051N；父中心版15frames、峰1.080N；旧3mm/1.5mm/1mm记录均0非零帧。新接触对盒有正Y反向力，但发生晚，不能解释整个前期失败；bag位移<15mm不等于无阻挡。PARCEL_INTERFERENCE_DIAGNOSTIC含明确shape/来源/阈值/前后统计；末substep非积分力。

**已排除简单解释：**现有10mm边缘反馈在六次倾斜退出前最后8采样内已override5–6帧，不能声称完全没触发或只需提高阈值。EDGE_FEEDBACK_TIMING_DIAGNOSTIC记录了这一点。下一控制定位应看已执行纠偏的真实材料点/手-盒相对运动和力方向，以及盒子绕非目标物体的通道；不得盲目继续增中心权重、减步长、提早阈值或延长1200预算。尚未选择/接线下一物理候选。

**因果限制：**新旧action第7帧、q第18帧已出现>1e−7差异，实际entry首次532；PRE_ENTRY_COMPARISON已绑定，所以总分差不能严格全归因单参数。当前新源1079冻结刚全核无变，首case95实际归档绑定。禁止修改冻结stage/审核/drivers。

runner2448024/watcher2448025实时核活；STATUS在首case primary期间可仍显示collector2448086，不据此重启，须查/proc children。首case采集已完成，正式36primary/80+56审核由原进程继续，不抢写。完成余6推2wait/10实际图审与全审核后5N绑定、close_box_entry_groups.py，失败保留分母。新只读inspect_box_entry_episode.py/diagnose_box_entry_recoveries.py可用于完整后续push；wait按原8帧图审流程。

旧box_center_groups_r1本轮已正式关闭7/8+2/2，RESULT SHA8f3f625cf2a6ccddeb990b68c1bb1e07484e476b8acc1c4e19d9ef71e08f4211；左右3/4拒绝，斜向4/4仅诊断。原control3失败/extra6失败均保留。完整目标仍四族12fresh交换组48推12wait分组split→共享RGB11D训练→untouched192推3wait、多seed真实h10+实际画面，未缩小。

以下为历史记录，以本段为准。

## 2026-10-01T20:07:32.735882+00:00 中心落点完整7/8+2/2封存；抬手修正完整物理已启动

本轮progress，goal active；0新合格训练组/转换/模型。旧box_center_groups_r1已完成全部10条件、36primary/80control/56extra执行及10实际抽样图审，原5N/首11D零位/assist0核过。RESULT SHA `8f3f625cf2a6ccddeb990b68c1bb1e07484e476b8acc1c4e19d9ef71e08f4211`。推7/8、等待2/2；左右交换组3/4拒绝，斜向4/4但属于诊断不入库。80control中3失败、56extra中6失败及后盒primary失败均保留，未回填绿色。

**差结果：**后盒255.201mm/末10最小有符号Y137.138mm未达原200mm，1159起恢复至1200未完成，正式审核拒绝unfinished recovery path。画面问题仍在：斜向盒171起全部7RGB样本目标画外；斜向袋513/685局部遮挡裁切，856起目标不可辨。不能把专家数值过门等同RGB可学或模型h10通过。

**好结果：**最后斜向盒150.027/244.917mm、斜向袋150.160/228.507mm，非目标XY均0；第二等待70帧全11action0、腰最大3.08738e-9rad；两推8RGB+4外视、等待8RGB已实际查看并绑定。旧driver2410426/watcher2410427/collector2434465确认终态。

新staged_box_entry_lift完成独立审核版本与原数学/driver一致性、2398帧重建+36边界+21元数据拒绝、4原生合成夹具169events+6旧inactive+21损坏拒绝、完整6CLI+5错误CLI检查。13起点真实SLSQP仅测试进程maxiter1的故障注入，实际wrapper全部保持unchanged、无命令、同恢复不反复重试，独立拒绝几何和伪造成功拒绝全过；REJECTED_PLAN_CHECK显式非物理。所有检查源哈希核齐后冻结1079文件。新只读inspect_box_entry_episode保持旧数值/pose数学，另有绑定。

**当前唯一物理box_entry_lift_groups_r1已启动**：runner2448024/watcher2448025/首collector2448086实际核活，首840001。协议SHA `1aca780b45569ddbdad40f5e4a9c4a56de072cbe070af91ba455233033f126dd`。新参数仅--rear-box-entry-lift：右后盒实测无载且低于原0.84m入口时先抬至名义0.845m，连续3帧实测达门后从新实测姿态规划原1.5mm/400中心重接触；两阶段共240ticks、整段1200帧不变。双臂腰允许运动、原5N/相机/全部8推2等待和原门保持。禁止修改冻结stage/审核/drivers；启动不证明新首零位或任务成功，raw完整后逐项复核。

下一步：核首case真实归档来源并绑定；随完整episode运行inspect_box_entry_episode.py，实际图审且保留失败。新全10/80+56/36及10图审完成后5N绑定、close_box_entry_groups.py。若后盒仍失败，按真实抬手/交接/载荷与预算证据定位，不能延时、弃难或将诊断转训。完整目标四族12新鲜交换组48推12wait整体split→共享RGB11D训练→未调参独立192推3wait/多seed真实h10与实际画面保持，未缩小。当前34.3GiB、无并行训练。

以下为历史记录，以本段为准。

## 2026-10-01T19:45:54.909858+00:00 中心对照六推5/6+首等待过；新抬手组合13/13完成并隔离接线，未启动下一物理

本轮progress，goal active，0新合格训练组/转换/模型。当前唯一物理对照box_center_groups_r1：已实际复核六条1200推+首70wait，六推5/6。后盒255.201/末10最小137.138mm仍失败（非目标3.300mm）；其余前袋357.992/204.607、前盒283.671/205.324、后袋300.327/205.437、正常盒150.243/303.628、正常袋150.048/268.111mm通过（非目标均0）。首wait全11action0、waist3.08724e-9rad，通过且实际8RGB绑定；六推各8RGB+4外视绑定。原相机目标画外依旧：普通盒342后、普通袋171后无目标，不能宣称RGB模型效果已改善。

**差结果保留：**后盒原pose/self_clearance primary及多个依赖审核拒绝`unfinished recovery path`，原因是1159重接触在1200尚未结束；未更改审核或抹去失败。当前原control 40/80、extra 23/56，失败分别3/6，尚非完整结论。runner2410426/watcher2410427/当前collector2434465本轮核活，layout840005继续；970冻结源全核无变。其余斜向两推和第二wait继续，全部齐后原压力绑定/close_box_center_groups.py，保留完整分母。

**新抬手候选验证：**13个实录高度被拒起点×4合成响应52/52抬手跟踪4–10tick过；完整抬手+原中心重接触13/13合成交接39–50tick，最后1151起点1193才完成，剩7帧不足以证明完成分拣。第一次标签比较错误的原log与修正说明保留，最终session54695/PID2424863已正常终态。不是物理成功，不扩大原1200预算。

独立新`box_entry_lift_recontact_guarded.py`补齐抬手完成→原规划的pending状态：保持原接触/物体/历史/父guard连续性，后续规划失败必须stop，拒绝的抬手尝试也保留，原240tick两阶段共享。旧prototype不改，其13结果保留。`check_box_entry_lift_guarded.py`全13命令精确复现、独立两阶段事件核验与每起点9种交界故障拒绝全过；`audit_box_entry_lift_events.py`不导入候选控制器，独立URDF/命令/三帧实测/共享预算；52抬手trace+10数据篡改拒绝全过。session18456/16281已exit0，源哈希全当前。

新隔离目录`staged_box_entry_lift`已准备，**未冻结、未启动物理**。只collector新增默认关`--rear-box-entry-lift`及显式right生命周期/plan/raw/source归档，其他原运行源与参数逐字保持，复制2新helper。`INTEGRATION_CHECK`整个关闭AST精确同父、6实际左右/开关类选择通过；`PRELAUNCH_CHECK`6完整真实CLI+5错误配置拒绝通过（session26383exit0），未创建sim。CLI保留诊断role，绝不把现有失败诊断转训。

下一步必须补齐：新阶段独立source合同和完整native-file审核（含entry_lift planning/拒绝尝试/无锚点捕获/两阶段预算）；新增16审计版本保持原数学；合成原生文件和损坏拒绝；完整8+2 drivers/protocol/version checks。只在当前完整run关闭、这些检查全通过并核源后，才能冻结下一物理候选。`prepare_box_entry_stage.py`已执行，勿重跑；尚无box_entry_groups物理run。当前所有CPU预检均已终态成功，只有当前物理及其正式审计仍运行。

整体目标四族12新鲜完整类别交换组/整体split→共享RGB11D转换训练→未调参独立布局多seed真实h10与实际图审保持，未缩小。

以下为历史记录，以本段为准。

## 2026-10-01T19:32:13.068179+00:00 前四推3/4；无载抬手52组合成跟踪过，完整衔接仍在计算

本轮progress，goal active；0新合格训练组/转换/模型。当前box_center_groups_r1前四推完整：后盒255.201/末10最小137.138mm失败；前袋357.992/204.607mm、前盒283.671/205.324mm、后袋300.327/205.437mm通过。四条均已实际8RGB+4外视绑定、首11D q/action零/assist0/5N/源核。后盒非目标最大XY3.300mm，其余0。完整交换组尚未齐，不准入训练。

**差结果：正式审核也拒绝后盒。** 第1159起最后重接触在1200结束时仍active，pose/self_clearance primary和多项依赖报`unfinished recovery path`；级联错误底层也已检查同因。保留所有失败日志/原报告，不放宽审核，不伪造绿色补充；UNFINISHED_RECOVERY_AUDIT_FINDING.json记录当前观察。剩余所有条件继续。原相机后袋目标513后画外，后盒也画外，模型泛化问题仍待。

**新控制准备（未接线、未物理）：**`box_recovery_entry_lift.py`默认关，只右侧实测无载且原高度不足时，原lift优化和原几何/命令约束抬至名义0.845m，必须连续3帧实测>=0.84m并接近终点；40tick准备超时、载荷/物体移动/父guard/历史不连续立即中止。`check_box_entry_lift_tracking.py`三个版本13真实首次被拒起点×4合成响应=52全过，4–10tick，独立URDF命令/预测/实测检查与每条8保护停止齐。不是实际物理，也不是后续推成功。

`box_entry_lift_recontact.py`未接线组合器把抬手命令交给原adapter保持top_cross，不重捕获锚点，下一实测帧才调用原中心规划；两阶段共用原240tick（含阶段边界耗尽保护），不增加原1200预算。`check_box_entry_lift_combined.py`对全部13起点跑完整合成衔接，**session54695/PID2424863已核活**，目前已写7/13行，仍未全完成；截至本次前四个均45/47/46/48tick交接。最晚真实起点1151可能受原1200预算限制，失败必须保留。首次session51910因比较脚本只parent_mode标签top_descend/top_cross不同exit1；逐字段复现仅该差别，按原adapter声明修正比较，所有其他数值精确比较，控制器没改，原失败log及BOX_ENTRY_LIFT_COMPARISON_FIX.json保留。第二次日志box_entry_lift_combined_r2.log。

当前物理driver2410426/watcher2410427核活，已完成case840004采集，STATUS可在primary审核时滞后，不据此重启。下一步继续原全8推2等待、36primary/80+56正式审核和10实际图审；压力绑定后关闭完整结果。新组合13检查全结束后评估所有成功/失败/预算，再做独立阶段审核与显式source/CLI隔离接线；只有完整验证后才能启动下一物理，当前970冻结源不得编辑。

整体目标四族12新鲜完整交换组/整体split→共享RGB11D→独立未调参布局多seed真实h10与实际画面保持，未缩小。

以下为历史记录，以本段为准。

## 2026-10-01T19:18:14.093265+00:00 中心落点后盒仍失败255.201mm；已定位落点后滑移和五次高度窗口错过

本轮progress，goal active，0新合格训练组/转换/模型。当前唯一物理box_center_groups_r1首case840001两条已完整1200帧、各8RGB+4外视实际复核绑定：**后盒失败255.200736mm/末10最小137.137935mm，非目标最大XY3.300199mm；前袋通过357.991815/204.606980mm，非目标0。** 首11D q/action零、assist0、5N与新来源均核过。当前仅1/2，不是完整交换组通过。后盒低于同1.5mm旧版277.684/154.352，禁止把相对1mm145.149的恢复冒充成功。

真实接触/时间诊断：后盒448有载帧净进194.259mm（旧1.5mm451帧215.472mm），倾斜退出6次（旧3），失载2次。八次恢复仅三次有中心规划，其中两次完成交接。第351规划半径52.59→45.11mm，451真实交接；首次COP48.88mm，到第505滑至65.09mm并倾斜。第985规划49.04→16.06mm，1022交接；COP首次18.95mm，末75.41mm并失载。第1159规划13.66mm但预算结束前未交接。**五次恢复（2–6）没有执行中心规划**：实际最低手点最高只有0.8315–0.8331m，低于原0.84m入口，112帧被拒；不能仅增加中心权重解决。原压力/姿态/预算门未改。COP是末substep记录，不是积分力或严格因果证明。

原相机问题仍明显：后盒RGB首0两物体可辨，342只有木盒小片，171及513后均无可辨物体；前袋8RGB均可辨两物体但局部遮挡/裁切。没有改相机，也不将专家数值过门当作共享RGB模型验证。

新只读工具inspect_box_center_episode.py、diagnose_box_center_push_budget.py、diagnose_box_center_contact_wrenches.py与旧版逆变换AST一致，只新source合同/4版输出；源在BOX_CENTER_REVIEW_TOOL_BINDING.json。LANDING_TRANSFER_DIAGNOSTIC.json绑定上述实际恢复/落点证据。**下一步准备方向是保留原0.84m高度保护，先安全抬手再重新落点**：screen_box_recovery_lift.py从三版13个首次被拒的因果起点，复用原lift优化和原路径约束，13/13几何可达0.845m、1–7路点；check_box_recovery_lift_screen.py独立URDF/路径/限位破坏拒绝13/13通过。只是离线几何，不是跟踪/新物理，不改当前冻结stage，尚未接线新候选。需下一步检验命令/预测/实测启动与生命周期、保护/超时，再完整物理验证，不能延长1200预算。

runner2410426/watcher2410427本轮实际核活；首collector2410481与该case primary已结束，新collector2418549实际核活，当前layout 840004，已完成条件2。状态与实际进程均已复核，不得重复启动。970冻结源本轮全部核验未变。原全8推2等待及80+56/36和10实际图审继续，后续逐条检查；全部齐后5N绑定+close_box_center_groups.py。旧1mm完整7/8+2已封存，RESULT SHA09e06d9f81c98ea4547c36f41f32f9da972f0878cad03785b01e31467b46a978。

完整目标仍四族12新鲜完整交换组、整体split→共享RGB11D转换训练→未调参独立布局多个seed真实h10及实际画面，未缩小。

以下为历史记录，以本段为准。

## 2026-10-01T19:05:20.092170+00:00 1mm完整对照已关闭7/8+2/2；中心落点完整物理已启动

本轮progress，goal active，整体目标不变；0新合格训练组/转换/模型。rear_box_rate_groups_r1已正式关闭，RESULT SHA `09e06d9f81c98ea4547c36f41f32f9da972f0878cad03785b01e31467b46a978`。8推7过、2等待全过；左右交换组3/4拒绝、斜向组4/4但诊断不准入训练。36primary、80control、56extra全通过，10真实采样图审/5N/首零位/assist0完成，旧runner2377097/watcher2377098已结束。好结果后袋301.114/206.224mm；差结果后盒145.149/24.926mm，1mm方案退化且拒绝。详见旧run/COMPLETE_PHYSICS_FINDINGS.md。

**当前唯一物理：box_center_groups_r1**，runner2410426/watcher2410427/collector2410481实际核活，首840001后盒正在执行；9项预检全过且源哈希一致后冻结**970文件**。协议SHA `a0b2b4900d46bbc90e029cb2634147b5be55db9e36ca952e9c6cb5d3d9811750`。不得修改stage、审核、检查、drivers及任何冻结依赖；未完成raw不能提前声称新首零位或任务成功。新方案后盒1.5mm+400/m²无载中心软偏好，后袋恢复3mm，前侧/初始3mm。保留原完整8推2等待、1200/70帧、5N、相机、质量门、全部审核与实际图审。CPU预检链已成功终态，16合成生命周期/4native夹具364events不是真实物理证据。

下一步：随完整episode落盘做新source/数值/姿态检查与8RGB+4外视实际复核；保留全部失败。完成10条件、80+56和36审核后5N绑定并close_box_center_groups.py。若后盒仍失败须按真实接触证据定位，不能延长预算或丢掉困难布局。相机中目标画外/遮挡仍是模型泛化风险，尚无模型h10验证；不得用专家通过冒充共享策略成功。完成合格完整新鲜pilot→转换训练→独立布局多种子h10仍待。

以下为历史记录，以本段为准。

## 2026-10-01T18:59:58.781472+00:00 后盒1mm完整8推已完成：7/8；中心落点候选9项预检完成，尚未启动物理

本轮progress，goal active。0新合格训练组、0新转换、0新模型。完整目标仍是四族12组新鲜类别交换数据与整体划分、共享RGB+11D策略、未调参独立布局/多个种子真实h10和实际图审；首零位、双臂/腰yaw允许、无助推、非目标全过程15mm和原质量门不变。

**好结果：**后袋恢复3mm后301.114mm/末10最小206.224mm通过，斜向盒150.260/245.149mm、斜向袋150.092/228.439mm均通过；8推数值共7/8，非目标最大XY均0。首等待70帧全11动作零，腰漂移3.09e-9rad，八帧已实际查看并绑定。

**差结果：**后盒1mm仅145.149mm/末10最小24.926mm，明确拒绝为改善或扩采方案。此前1.5mm后盒277.684/154.352mm仍失败；单纯降速不能解决持续接触。有载437帧阶段净进85.112mm，远低于1.5mm的215.472mm。目标画外问题依旧：斜向盒首帧两物体可见，171之后七个RGB样本盒均不可见，不能将专家数值通过等同模型可学。

当前rear_box_rate_groups_r1完整诊断剩第二等待与正式收尾；driver2377097/watcher2377098仍须现场核活，8推/2wait分母不变。861冻结源本轮全核无变化；正式审核由原进程写入，不抢写。七推+首等待已实际图审绑定，最后斜向袋采样图正在生成，之后第二等待同样复核。

新staged_box_center_preference已完成并核源全部9项预检（含16合成生命周期、4读档夹具共364events、6旧inactive、16损坏拒绝）。CPU连续链2401723及native2403397已终态成功；合成数据明确不是真实物理/训练数据。新方案后盒1.5mm加400/m²无载重接触中心软偏好，后袋3mm，其余原门/5N/相机/预算不改。实际触点并不等于最低顶点，且恢复路点增多可能抵消收益。**尚未冻结/启动box_center_groups_r1**，须先完成当前10条件、80+56/36审计、10真实图审、5N核验和closer，再准备唯一下一物理全8+2。

以下为历史记录，以本段为准。

## 2026-10-01T18:22:21.217354+00:00 后盒1mm完整145.15mm退化，前袋通过；余条件与正式审核继续

当前唯一物理对照rear_box_rate_groups_r1，首case两条完整1200帧已落盘并实际8RGB+4外视复核：后盒失败145.148864mm/末10最小24.925828mm；前袋通过357.894301/204.509467mm。2条首11D q/action零、assist0、非目标全过程XY0、5N/来源齐。首pair1/2，不是完整交换组成功。正式primary/80+56审核正在进程内完成，不提前抢写报告。runner2377097/watcher2377098实时核活；首collector2377147已正常结束，STATUS可能暂留旧collector字段，应看/proc子进程，不重启。

**差结果明确：后盒1mm显著退化，拒绝作为扩采或改善方案。** 与1.5mm的277.68相比仅145.15，连150mm推进门未达；有载推437vs451帧但阶段净进85.112vs215.472mm，倾斜退出6vs3，失载2vs4。减少重规划事件175vs224没有补偿推进效率损失，其他下降153vs26帧增加。接触COP仍约[-53.74,-40.74]mm、偏心力矩没有消除。首100帧比较第73帧即存在新旧数值差异，不能把总差全归因单参数。完整证据FIRST_REAR_BOX_FINDINGS及绑定，三步长budget/wrench、PRE_TOP_PUSH_COMPARISON均为只读实际日志诊断；力矩关于位姿原点，非质心/冲量/因果证明。

**好结果边界：前袋仍通过且8RGB均可辨两物体，但这不证明后绕袋恢复。** 新后袋尚待。第一后盒RGB中后段目标画外仍未解决；原相机保持。首后盒失败不终止余6推2wait，继续完整分母与审核。861冻结源刚核全，协议76dabcd1bda3a128d0e1a3c749c5745b9f5a9c9de95e785a80ad7b5a7ebeb4f3不改。

下一步：余任务完整数值/源/5N/实际图审，所有审核与10条齐后pressure binding+close_box_rate_groups。停止继续盲目降低固定步长，下一控制定位优先真实接触落点/姿态与执行响应/偏心受力；未选择或接线下一物理候选。先前rear_slow_drag完整6/8+2已封存，RESULT SHA0047777ffd1ca040b42b97495218d9afc7aef4efb96ca18a52f9ae17f8dc3491，80+56全过但两组各3/4拒绝。

完整目标未变：四族12fresh完整交换组（48推12wait，8组train4组val）→共享RGB11D转换训练→untouched192推3wait、多seed实际h10。PILOT_INTEGRATION_READINESS已核12计划hash和转换入口：候选有14处涉及diagnostic角色的guard、无条件拒绝pilot，后续需独立试采接线/来源绑定；不能改诊断元数据转训。无合格新训练组/转换/模型。当前39GiB，无并行训练。本轮progress包括完整旧实验封存、新物理首pair与真实诊断/图审，goal active。

以下为历史记录，以本段为准。

## 2026-10-01T18:11:21.469615+00:00 统一减速6/8已封存；后绕木盒单独减速完整对照已启动

后绕统一1.5mm完整诊断已正式封存：6/8推、2/2等待，左右/斜向完整组各3/4拒绝训练。80原控制+56附加全部通过，36primary完成，10条真实图审/5N/首11D零位/assist0齐。结果SHA 0047777ffd1ca040b42b97495218d9afc7aef4efb96ca18a52f9ae17f8dc3491。后盒277.683519mm/末10最小154.351577仍失败；后袋292.294189/197.194934退化，非目标2.544306mm<15mm。目标画外风险仍在；无合格新组/转换/模型。

新rear_box_rate_groups_r1已实际启动：runner2377097/watcher2377098/首collector2377147，首840001。协议SHA 76dabcd1bda3a128d0e1a3c749c5745b9f5a9c9de95e785a80ad7b5a7ebeb4f3，861冻结源；首case真实来源92文件核过。仅实际后绕木盒路线每步1mm，后绕袋/前侧/初始保持原3mm；基于minimum_motion而非把退化的袋保留。原完整8推2wait、1200/70帧、5N、相机、腰1rad、质量/非目标15mm门、80+56/36审核均保持。当前启动证据不证明首零位/任务成功，完成raw后逐项核。严禁修改冻结stage/驱动/审核/合同，勿重复启动。

只读跟踪诊断不支持“名义手点上行就是实际失载原因”，名义Z与真实下一步明显不同；两后绕近失载状态没有虚拟点过而当前材料点名义向外的主要证据。不接入离线名义不抬手约束。详见上一run COMPLETE_PHYSICS_FINDINGS与TRACKING_MATERIAL_FINDINGS_BINDING。

下一步每条完成后用inspect_box_rate_episode.py核数值/源/5N、实际8RGB+4外视，等待8RGB；原全审核结束与压力绑定后close_box_rate_groups.py。后续四族12fresh完整组/分组划分→共享RGB11D转换训练→untouched192推3wait多seed真实h10目标保持。上轮备份已完成，本轮是实际物理及审核progress，goal active。

以下为历史记录，以本段为准。

## 2026-10-01T18:06:53.598761+00:00 后绕统一减速完整物理6/8、两等待通过；两组拒绝，正式审核收尾

后绕统一减速完整8推实际结果为6/8、2/2等待；原minimum_motion为7/8+2。两完整交换组各3/4，均拒绝训练，0新合格组。后盒277.683519mm/末10最小154.351577mm仍失败；后袋292.294189/197.194934失败，相对父205.041111末值退化。六其余推通过原任务/姿态门，非目标最大XY除后袋2.544306mm外均0，原15mm门保持。10条首11D q/action全0、assist0、实际图审完成。原相机目标画外问题仍明显；抽样图不代替h10闭环证明。正式控制审核尚在完成，不能先宣称全部审核通过。

新的只读诊断修正了名义运动解释：后盒近失载33状态，名义FK全部预测向上，实际下一步只有11向上；后袋61状态名义全部向上，实际16。历史仿射预测改善点位误差，但仍错误预测这些Z方向，不能据此给控制器加名义不抬手硬约束。两类近失载状态中，虚拟点满足边缘约束而当前材料点名义向外的计数均0；“换个接触参考点就解决失载”没有证据。材料点不是未来COP，下一物体位姿仅用于观测评分。报告覆盖首4推/两后绕，不冒充全8或反事实物理。

下一候选仅后绕木盒每步1mm、后绕黑袋恢复3mm，前侧/初始路线保持3mm；由原minimum_motion基线派生。8选择组合、2398真实历史控制帧重建、36独立数值边界、21元数据拒绝、6实际CLI+4非法拒绝已通过且来源hash当前。必须先封存本轮10条及80+56+36审核，再冻结新实验并启动完整8推2等待；没有延长1200帧预算、降低200mm目标区门或改相机。速度进一步下降也可能耗尽预算，此试验未保证成功。

以下为历史记录，以本段为准。

## 2026-10-01T17:41:31.060124+00:00 后绕减速前四2/4，后袋退化；完整余项继续，失载方向冲突已诊断

当前rear_slow_drag_groups_r1前四困难推完整2/4；原对应3/4，已明确不采用后绕统一减速为整体改进。后盒277.683519mm/末10最小154.351577仍失败（倾斜13→3）；前袋357.707337/204.322502与前盒284.574419/206.227317通过；后袋292.294189/197.194934失败且相对父退化，非目标盒2.544306mm<15mm但非零。4套真实图审/零位/assist0/5N/source齐，0合格新训练组。详见FIRST_FOUR_FINDINGS。

下压失载只读证据：四次末12帧均−6mm偏置饱和，腰0.98rad频繁饱和，目标负Z而部分关节命令名义参考点正Z3–7mm；不等于真实运动或因果证明。新50状态非上抬筛查49/50、0.25mm下压47/50，其中近失载样本推进小且有局部失败，不接线。LOSS_TRACKING_FINDINGS/DIAGNOSTIC和两DOWNWARD_*SCREEN保留好/差；当前版本不改。

runner2343346/watcher2343347仍在跑；840004物理已结束、primary阶段可能显示旧collector字段，以/proc实际为准。首pair8primary均过，后盒新版原控制9/9已过，附加正在执行；全80+56/36及余4推2等待未完。780冻结与1ce97b9…协议不变；不得抢写自动审核路径。下一步核后袋新审核、正常/斜向/两wait实际图像→完整封存，再选控制改进/完整fresh组训练路径，未完成目标。

以下为历史记录，以本段为准。

## 2026-10-01T17:24:40.757291+00:00 后绕减速首后盒277.68mm仍失败，倾斜退出13→3；完整对照继续

首后盒完整1200帧已完成：277.683519mm，末10最小有符号Y154.351577mm，仍未达200mm而失败；父214.598842/96.505165。好：倾斜退出13→3，有载推246→451帧，虚拟Y误差中位20.383→13.601mm；差：失载2→4，6条恢复/224events消耗预算，0合格新组。首11D零/assist0/非目标XY0/5N/source核齐，8RGB+4外视已实际绑定；342仅右缘盒片段，其余后期多数双方不可辨。FIRST_REAR_BOX_FINDINGS及REAR_BOX_RESULT有完整证据。

物理runner2343346/watcher2343347/collector2343395仍核活，当前840001配对前袋；整case完成后自动primary/controls/additional，禁止抢写其正式报告。完整余7推2等待继续，780冻结源与新协议1ce97b9…不改；正式审核尚未完成，不宣称候选通过。下一步配对前袋完成后实际raw/图审，检查新审核运行，并继续后袋/正常/斜向/两等待；相机硬件问题仍未答复，保持原配置。上轮及本轮均progress，目标active，0新训练/转换/模型。

以下为历史记录，以本段为准。

## 2026-10-01T17:15:58.506668+00:00 后绕减速完整8推2等待已启动；原相机/质量门保持

2026-10-02 当前完整8推2等待已启动。runner2343346 / watcher2343347 / 首collector2343395，首布局840001。协议SHA 1ce97b9b92dae216fccbc1728ec91e81914b6b6eaf2df81e95b5d646e386a614，780冻结来源；首case真实归档来源已核，5N、原全局3mm、显式rear_slow_drag开关正确。真实首11D零位需待raw落盘核验。

代码检查发现CLI和运行时COP都要求原全局3mm，直接改原计划全局参数会触及前侧行为。因此修正为默认关的--rear-slow-drag：只在实际选择rear_cop_centering路线时将有效drag_step设1.5mm，前侧和初始顶部路线仍3mm。stage仅collector接线/元数据与rear_cop_route参数守卫改动，其余运行时源码逐字相同，关闭后的AST逻辑同原。默认生产与冻结父版本不改。

预检：6真实CLI及4非法组合拒绝；两原后绕完整2398控制帧重建与原3mm逐项相同，36独立边界数值与15元数据错配拒绝；多次规划审核采用已验证reentrant方法名修复；其余独立数学AST逆变换保持，loaded只换声明步长参考。完整36primary/80原/56附加/10实际图审保留。新物理尚未完成，不能以预检作为成功。

上一轮7/8+2已关闭但后盒仍失败，0合格新训练组。此次保持同布局/次序/种子/1200推帧70等待帧/5N/腰1rad/原相机/全部原任务与非目标15mm门。关注后盒倾斜退出频率、实际推进与末10稳定到区；不会因速度变慢延长预算或剔除条件。

完成每条后核原质量与11D首零位、assist0、非目标全过程位移、实际图像并绑定；完整结束后压力绑定及close_slow_drag_groups.py封存正式结果。四族12fresh完整交换组/分组划分→转换共享RGB11D训练→untouched192推3wait、多seed实际h10仍未完成。

以下为历史记录，以本段为准。

## 2026-10-01T17:06:36.611223+00:00 完整最小姿态7/8封存；实际相机对照完成；推进速率对照准备中

完整最小姿态对照已关闭：7/8推、2/2等待；后盒214.598842mm但末10最小有符号Y96.505165mm，未到原200mm目标区，仍失败。0合格新训练组/转换/模型。全部10实际图审、5N核验和689冻结源验证齐；原审核74/80、附加44/56，正式失败保留。方法/数组endpoint重名错误已用独立reentrant补充修复，两困难任务native/全task/clearance/loaded执行链完整通过，不能回填旧正式准入。

后盒13次倾斜退出，通常持续12–19推帧后退出，虚拟目标Y领先实际约20mm；力矩无明显改善。下一项只把推送每步增量3mm改1.5mm，原相机/5N/腰1rad/1200帧/全部8推2等待/质量门不变。尚未准备或启动新物理实验，需独立新审核版本消除硬编码3mm并回归。

实际相机对照已完成，全部8套图审，64次姿态/内参误差0；32样本原目标投影画外14、0.4焦距0，实际可见性改善但遮挡/裁切/缩小至约18px风险仍在。两困难任务224图已看，未推理。用户相机兼容问题未答复，保持原配置。离线居中硬门3/8、软惩罚8/8但路径变长，去薄轴约束两个局部求解0/2，腰1.2假设未推广；均非物理/训练准入。

原runner2300534/watcher2300535/collector2328214及render队列2312941/child2329078均已核实不存在。RESULT SHA118b8229ba1ccef820832c482ee5d77f6ef65550638dc24d2e9d12622a2b35af，协议78f4f41b…保持。目标四族12fresh完整交换组/split→共享RGB11D→untouched192推3wait、多seed真实h10不变。

以下为历史记录，以本段为准。

## 2026-10-01T16:29:46.839643+00:00 最小姿态前四条3/4；后盒214.60仍失败；多次恢复审核命名冲突定位；真实相机对照已排队

- 本轮progress，goal active；**0合格新组/转换/模型**。仍唯一物理`minimum_motion_groups_r1`，runner2300534/watcher2300535实时核活，最新collector2314987，layout840000；689冻结源刚全核，协议78f4f41b…保持，禁止改冻结源。已完成四困难条件与4套实际8RGB+4外视绑定，首11D q/action零、assist0、非目标XY0、真实源/5N核过。
- **好/差**：后盒214.598842mm/末10最小Y96.505165mm失败（父192.157924）；前袋357.753977/末204.369143过，前盒284.558803/末206.211701过，后袋299.931034/末205.041111过。后盒171起7样本双方不可辨，后袋513起5样本目标不可辨。全8+2与剩余6图审继续；不以3/4准入。
- 新contact/budget/wrench/activation只读报告在新run。后盒倾斜退出7→13，有载净进118.041→158.508但抬手回退增；252帧/12恢复因原最低高度门未进入新规划。仅294/1122两新计划，102/22名义路点、105/25真实ticks，不能宣称总恢复少。倾斜前力矩中位基本相同；新旧干预前已分歧，不作总收益因果宣称。
- **审核代码bug**：`audit_minimum_motion_plan.PlanAudit.endpoint`方法被原EventAudit同名数组覆盖，第二计划TypeError，多项正式审核依赖同错，原失败保留。新增`audit_minimum_motion_plan_reentrant.py`、`audit_minimum_motion_events_reentrant.py`、`audit_minimum_motion_pose_reentrant_supplement.py`只方法/导入/输出重命名，逆变换AST过。后盒1200完整130events/2handover补充过，1199task KKT4.106572e-8；`check_minimum_motion_reentrant_supplement.py`原错误复现、首计划证明精确相同、次计划6损坏拒绝。session31627/22864已exit0，**后袋补充session39889已exit0：1200全帧236events/6handover通过**。没有改原正式报告/门。后续loaded等需要独立补充，不能复制绿色到原路径。
- **相机真实渲染队列PID2312941**核活，等driver2300534全10结束后运行`render_recorded_camera_comparison.py`到`minimum_motion_camera_comparison_r1`，日志minimum_motion_camera_comparison.log；当前仅编译，尚未实际渲染。相同记录关节/物体+原K与0.4focal静态RTX，8条×4样本，逐项位姿和内参核；不是动力学/训练数据。缺完整8条/源变/其他collector时停止。检查MINIMUM_MOTION_CAMERA_QUEUE与真实pid，不因等候重启。
- 当前剩43GiB，无并行训练。继续原8+2/80+56/36与10实际图审、完整5N后原closer，封存正式失败；相机实际比较与接触改进并行推进。目标四族12fresh完整交换组/split→共享RGB11D→untouched192推3wait、多seed真实h10未缩小。详见新run/FIRST_FOUR_FINDINGS.md及MINIMUM_MOTION_PROGRESS。

以下为历史记录，以本段为准。

## 2026-10-01T16:07:54.068193+00:00 新最小姿态完整8+2已启动；689冻结/首case92实际源核过；启动画面物体不可辨

- 本轮progress，goal active；0新合格组/转换/模型。**当前唯一物理 `minimum_motion_groups_r1`**：runner2300534/watcher2300535/collector2300592实时核活，首840001后盒进行中。协议SHA **`78f4f41b4e1fbedae167419988052a8a826a8691d8d813872dfc42dd3bb053ad`**，**689冻结源**，首case92真实归档与协议及CLI minimum_motion/parent_seed/precision/interior/unloaded true、5N已核。**禁止修改当前stage、检查、审核、驱动与任何冻结依赖。** 状态collector字段可能随primary阶段变旧，要核真实children，不重启。
- 自动链session1979/PID2298446已exit0完成。native PID2298901已正常结束：四明确SYNTHETIC_NOT_PHYSICS夹具101/84/114/94共393events、六旧inactive、16损坏拒绝及非零前一步力过滤/wait来源过。全部8预检源一致后prepare/launch；物理保持原8推2wait、1200/70、5N、相机、任务/布局/次序和80+56/36、10真实图审。
- 前一段所说“读档正在进行”已被本段更新覆盖。`MINIMUM_MOTION_PROGRESS`和run PROGRESS为当前，所有预检齐；新candidate真实数据尚未完成，首11D零位/assist0需完成raw后直接核，不能拿启动声明代替数值。现场step270 top_lift固定图已实际看：桌面与一手、两物体不可辨，`LIVE_START_REVIEW`哈希绑定；无相机改善或新任务成功声明。
- 新stage/独立审核/六CLI/全16因果规划与合成首命令/12篡改/16合成生命周期细节见下一段。实际因果路线69–133路点；后盒late1168合成恢复需84tick，到1251超原1200，四变体均明确失败，绝不延长正式预算。须在真实接触中减少恢复才有收益。
- 当前新版drivers为 `run_minimum_motion_groups.py`/`watch_minimum_motion_audits.py`/`close_minimum_motion_groups.py`。完成全10/80+56/36/10实际图审后 `verify_top_pressure_setting.py NEW 5` 再用新版closer。原关闭parent_seed RESULT SHA7bd046c8…与补充loaded执行证据保留；新loaded版本预先声明独立task→slew→edge链，不改旧正式失败。
- 所有本轮旧CPU已终态：11651因果、69105runtime（41681初次AST计数错误exit1后修）、29146独立计划/首命令、81184CLI、44936协议、89066生命周期、1979连续链、92063冻结源核验；Native/prepare子进程亦正常结束。新物理不并行训练。下一步随实际完成逐条看raw/图/质量，不以开始一轮或离线可行结束目标；四族12fresh完整类别交换组/split→共享RGB11D→未调参192推3wait多seed真实h10仍待。

以下为历史记录，以本段为准。

## 2026-10-01T16:04:21.027365+00:00 最小姿态恢复已隔离接线；16因果起点与完整合成生命周期过；读档→物理自动链运行

- 上轮/本轮均progress，goal active；**0新合格训练组/转换/模型**。已关闭父初值7/8+2的RESULT SHA `7bd046c86fc5edd4c40c2699f03c1447699ded8413021a4023af80a4cdeff8f7`及593源不改。当前新stage `staged_minimum_motion_recontact`，尚未以启动/离线验证冒充实际接触成功；是否已随后启动请看下述自动链最新状态。
- **因果实现完成**：session11651原筛查最终16完成，13直线可行。新`minimum_motion_recontact.py`只当前q和重新计算的原规划终点，原20mm内缩/6–7mm高度/10mm包裹/5mm肘/限位保持；先最小关节运动abs(PCA薄轴对齐)≥0.8，必要时15/30/60mm三分段抬高手路。PCA仍仅几何启发，非真实掌面识别。`check_minimum_motion_runtime_planner.py`全部16动态候选过、父规划精确复现实录，默认关闭AST精确、求解失败显式原回退、2坏flag拒绝。**实际候选69–133路点**，不是上一轮依赖强对齐seed的69–125。初次check分支语句计数5写成4的验证脚本错误已修正后完整过（41681首次exit1；69105最终exit0）。
- 隔离collector新增默认关`--minimum-motion-recontact`，需parent_seed+analytic+precision+interior+unloaded/diagnostic原条件。原lifecycle文件不改，新`minimum_motion_lifecycle.py`只在调用plan加True，剩余完整更新/保护/交接AST同原；collector仅开启时选新class，plan/raw/source归档两新文件齐。INTEGRATION_CHECK默认关闭整个collector AST同父、9非法模式拒绝；PRELAUNCH_CHECK全6真实CLI过；无新相机/压力/loaded控制修改。
- 新`audit_minimum_motion_plan.py`独立URDF/PCA/端点/每次失败尝试/三段路径/选择/父回退；`audit_minimum_motion_events.py`只替换原直线路点构造为独立验证的分段路点，原所有measured/nominal/predicted/command/240tick/三帧ready/捕获数学保留。INDEPENDENT_AUDIT_CHECK **16全路径+16明确合成首命令过，12篡改拒绝**，session29146已exit0。没有把合成事件冒充新物理。
- 显式16新审核模块/`MINIMUM_MOTION_AUDIT_VERSION_MAP.json`已生成；新source合同额外强制CLI/raw新flag及精确方案参数/新源，10旧真实父实录拒绝。AUDIT_VERSION_CHECK 15原数学版本（13全体同、native只新metadata要求、loaded显式扩展）、16元数据篡改拒绝。新`audit_minimum_motion_loaded_parent.py`分支AST与上一轮完整后袋393push+6拒绝已验supp精确同，用独立全task KKT+原限幅连接edge；旧拒绝结果保持，非放宽原数学门。
- **完整合成生命周期好/差**：`check_minimum_motion_lifecycle.py` session89066已exit0，4真实first/last起点×4响应（标定/快慢decay/变bias）全部完成，7保护中止每条齐。后盒首恢复101ticks，末84；后袋首114、末94。**后盒1168起点四变体均到1251才交接，超原1200**，原记录保留，不延长正式预算；须真实接触减少恢复次数才有意义。LIFECYCLE_CHECK只是合成模型，不是真实跟踪或接触验证。
- 新prepare/run/watch/close/contract均保持原6命令8push2wait、1200/70、5N、相机、任务/次序/80+56/36和10实际图审，额外新flag和来源断言。RUN_PROTOCOL_CHECK全6CLI/driver结构过，session44936exit0；第一组CLI81184已exit0。7项已完成预检源hash当前全核。
- **当前真实连续链**：`advance_minimum_motion_groups.py` **session1979 / PID2298446**，等待原生命周期PID2293701结束后已启动 `check_minimum_motion_native_files.py` **PID2298901**，日志`minimum_motion_native_files.log`。最近已过前3个SYNTHETIC_NOT_PHYSICS完整读档夹具（101/84/114events）；后盒late仅为读档映射到800，明确不是物理成功。还需第4+原6inactive+原16损坏/非零力过滤/wait源 checks。链仅在8预检全部pass+来源一致、旧采集不存在后prepare/freeze并自动启动唯一新物理`minimum_motion_groups_r1`+watcher；任一失败写stopped并停止，勿直接重启掩盖错误。
- **不要修改当前stage/预检/审核/驱动文件**：自动链可能随时冻结。先poll1979和MINIMUM_MOTION_ADVANCE_STATUS并核/proc。若已launch，核实际归档源和CLI新flag/5N/原零位、查看startup画面并绑定，然后全10真实图审。新run全结束后verify_top_pressure_setting.py NEW 5及新版closer；补齐生成数据组/训练/未调参h10多seed前目标都未完成。MINIMUM_MOTION_PROGRESS和PLAN已更新，原PARENT_SEED_PROGRESS仅历史关闭。

以下为历史记录，以本段为准。

## 2026-10-01T15:33:12.130023+00:00 父初值完整7/8+2封存；后袋执行链补充过；最小姿态路径16起点首命令过

- 本轮progress，goal active；**0新合格训练组/转换/模型**。`parent_seed_groups_r1`正式closed，RESULT SHA `7bd046c86fc5edd4c40c2699f03c1447699ded8413021a4023af80a4cdeff8f7`；593冻结源重核，完整36primary/80原全部过/56附加55过/10实际图审与全10真实5N绑定齐。runner2246876/watcher2246877/末推collector2270871实时核终态，无新物理或训练。剩余约44GiB。
- **好/差：完整7/8推、2/2等待，与精度父同分；困难后盒仍192.157924mm/末74.095123mm失败**，虽23新增重试22成功、完整task/loaded原数学门过（后盒9taskoverride max3.7683e-8；106refinement/1fallback/23retry max9.4322e-8）。后袋300.141901/末205.251977过、前盒284.091696、前袋357.885629。正常盒/袋150.086343/150.081597；斜盒/袋150.037795/150.277376；全部首11D零、assist0、非目标XY0；双wait70全动作0。详见PARENT_SEED_CONCLUSION。
- **正式唯一附加拒绝：后袋loaded task在833/834改变**，原冻结loaded审核按合同拒绝且无report；正式两组task3/4和4/4均all_audits false，不回改。新独立`diagnose_loaded_task_override.py`定位原baseline越命令边界约2.18/2.22mrad而非肘贴近（约31.75mm最小间距）。新`audit_parent_seed_loaded_task_supplement.py`仅在明确拒绝点接入独立全task KKT证明+原float32限幅再边缘执行链，原其它AST数学保持：393push/120refinement、0fallback、max5.1403e-8；两帧task到父命令误差0。1199 task重核max1.789e-8，6种篡改均拒绝；后盒无覆盖分支完整14字段含records与旧报告精确一致。PARENT_SEED_LOADED_TASK_SUPPLEMENT/CONTROL绑定齐，仍不是旧正式准入。
- **图像差**：正常盒342起、正常袋171起、斜盒171起目标不可辨。后盒多数样本/后袋后半段仍不辨；斜袋513后有左黑裁切片，不误报全画外。最后6套已实际查看绑定，所有10齐。相机0.4焦距仍只有投影/模型尺度证据，尚未真实新渲染。
- CONTACT_WRENCH_DIAGNOSTIC/FINDINGS完成18旧/新实录：末子步力包逐条姿态/世界力转化核验；倾斜前载荷高和边角COP力矩、丢载前载荷低为观察关联，不因果/冲量/翻倒证明。PUSH_BUDGET_DIAGNOSTIC/FINDINGS完成12实录：后盒有载push219→258但净进116.749→118.041mm，回退3.994→14.897；恢复419帧、其它抬手208。新旧干预前已分歧，勿归因父初值重试。
- **离线新候选**：`screen_flat_face_recontact.py`16起点全部终点可行，11直线路径可行；5失败由途中高度低于4mm（两例穿顶），`analyze_flat_face_paths.py`完整证明，`screen_flat_face_lift_paths.py`5/5分段修复但路径长。PCA薄轴只是几何启发，非已识别真实掌面。`screen_minimum_motion_face.py`把目标换最小关节运动+薄轴对齐abs≥0.8（仅候选参数、非新硬门）：16终点、13直线过；三后盒518/622/750在15/30/15mm抬高分段81/88/69路点过。完整selected16路线69–125路点（按最小目标函数，不能沿用先前最少路点111上界），仍比旧28–89多。
- `check_minimum_motion_first_command.py`全部16旧proposal精确复现、16新首命令原measured/nominal/predicted/action门过；整条实际240tick跟踪、接触收益未验证。MINIMUM_MOTION_*来源绑定，生产/冻结源未改、未接新控制。最小运动筛查的第二seed来自同当前观测的先前强对齐解；**运行时不能硬编码历史终点**，需要实时计算或替换为因果初值复核。
- 当前唯一新CPU **session11651** `screen_causal_minimum_motion_face.py`真实运行（PID 2283942）：同16起点仅原规划终点+当前q初值，输出CAUSAL_MINIMUM_MOTION_FACE_SCREEN.json，勿因未完成重启。下一轮先poll，再全部路径/首步复核、隔离默认关闭在线helper/独立审核、完整8+2物理；当前新方案尚无stage/runtime。已结束的sessions31349/87577/31533/69459/81458/22854/39925/60608/56757/29102/96818/66816/21647/80462/90096/35479/55192/18798均exit0。
- `PARENT_SEED_PROGRESS`及run PROGRESS已关闭并指向新CPU；`MINIMUM_MOTION_RECONTACT_PLAN.md`列明接续。完整四族12fresh类别交换组及组级split→严格RGB11D共享训练→未调参192推3wait/多seed真实h10与实际图审目标不变。不是单次7/8、几何或补充审计通过即完成。

以下为历史记录，以本段为准。

## 2026-10-01T14:44:04.245111+00:00 父初值完整8+2已启动：首对1/2，后盒192.158仍败；模型视野尺寸诊断

- 本轮progress，goal active；0新合格组/转换/模型。当前唯一物理试验 **parent_seed_groups_r1**，协议SHA `ad55d90745a78e8bd86decd5a3bb313963a44fea343debee4aee72c8c947278e`，**593冻结文件全核**。runner2246876/watcher2246877实时存活；首collector2246927已采完两条退出，目前runner子进程2253851为首后盒audit_parent_seed_pose_live.py（实时核活），不要把STATUS旧collector当运行证据或因此重启。首case90实际归档源与CLI parent_seed/analytic/precision true、5N核过。旧精度版7/8+2已关闭，RESULT与全部冻结源不变。
- **差：首后盒1200推进192.157924mm、末10signedY74.095123mm仍败**（父192.896031/74.833）。实际新增重试23次、22覆盖成功；1081仍status8显式保留父命令。新旧q/action在71/69帧即差>1e-6，首重试378；此前最大差0.202/0.222rad，初交接266→256也早于重试，不能把轨迹指标变化直接归因候选。失载4→3但倾斜恢复5→7、恢复命令441→410、push240→272，推进未改善。FIRST_REAR_BOX_RESULT/FINDINGS与新CONTACT_EXIT_COMPARISON完整。
- **好：首前袋1200推进357.885629mm、末204.500794mm原task/pose过。** 两条首11D state/action0、assist0、非目标全过程XY0、raw flag/ftol1e-13/5N实际核过。两套8RGB+4外视实际已绑定：后盒除首帧/513极右窄棕片外多不可辨，前袋双方8样本可辨但手遮挡/底左裁切。正式完整执行/KKT报告仍待后台，source/metadata通过不冒充数值通过。
- 新16显式审核模块/PARENT_SEED_AUDIT_VERSION_MAP与新drivers：run_parent_seed_groups.py/watch_parent_seed_audits.py/close_parent_seed_groups.py/parent_seed_run_contract。保持15审核数学AST同原，loaded只换真实新helper身份和独立第三次metadata验证/额外计数，原loaded task改变拒绝不放宽。6预检齐：integration、6actualCLI、15数学版本+18来源配置破坏拒绝+10旧实录拒绝、4明确synthetic native fixtures258events、全8+2/80+56/36driver协议、**新精度基线9592帧默认关精确/开启仅22原失败改善，其余9570不变，原独立数学门过**。旧5N26/26探针报告另存未改。
- CPU66342/38709两CLI、47418native、96013新精度历史、99329prepare均exit0；593已冻结，禁止再改prepare/check/stage/审计依赖。实际startupstep360 top_press画面桌面一手、两物体不辨，LIVE_START_REVIEW已绑定。后续全10实际图审与verify_top_pressure_setting.py NEW 5后，用新版closer封存，不是旧precision closer。
- 新PRECISE_FULL8_CAMERA_MODEL_SCALE_SCREEN：精度8×240实际相机位姿针孔投影、未新渲染。局部base config224×224与真实resize_with_pad函数CPU核验640×480→224×168；0.3焦距前盒p10仅13.6×13.5模型像素。0.4全部无目标全画外，但后袋/斜盒各1样本、正常袋12样本未达双方半框（诊断不是门）；下一独立观察先比较原/0.4真实渲染再决定，不修改当前相机，不能缩放旧RGB生成画外。PRECISE_CAMERA_MODEL_SCALE_FINDINGS记录。
- 新INACTIVE_OBJECTIVE_COMPETITION：只读全8，后盒240/240后袋375/375 Jac全，其余13–23采样帧，显式缺帧列表。初次缺Jac停止后按实际覆盖修正。后盒inactive锚误差中位1.787mm/线性残差0.043mm，active20.462/0.981mm；梯度182/240相反但成功任务亦有，不能定为任务干扰根因或据此降权；腰62/240命令近0.98界，需继续接触/跟踪分析。无控制变化。
- 当前PARENT_SEED_PROGRESS/REAR_EDGE_PARENT_SEED_PROGRESS最新；余6推2wait与80+56继续。完整四族12fresh类别交换组及组级split→共享RGB11D→未调参192push3wait多seed实际h10与真实图审目标不变，新增重复基线需求用于判断先于干预分歧，不能把首对失败当终点或避开后盒。

以下为历史记录，以本段为准。

## 2026-10-01T14:22:50.474760+00:00 精度全8+2封存7/8+2；完整一组4/4审核过；重试候选完成隔离接线

- 本轮progress，goal active；0新合格训练组/转换/模型。precise_interior_groups_r1正式closed，RESULT SHA `9a7bc17f0cc7b9581c2ab748292d8d0755c340e9528a61236fb29c06e92b72dc`；完整7/8推+2/2wait，协议lateral3/4拒绝、diagonal4/4且全部审核过但仅诊断，非训练准入。当前物理与watcher均已退出（2210665/2210666/last2239184实时核终态），不得用旧STATUS字段重启。419冻结源全核，10真实图审/实际5N绑定、36primary/80原77过/56附加50过齐。
- **好**：困难后袋300.706/末205.816mm正式KKT过（10overrides max3.04186e-8）；原其余成功7条全部KKT过，最大6.61068e-8。正常盒150.191724/袋150.036596、斜盒150.157407/袋150.223926mm原task/pose过。双wait70稳定，全部首11D零/assist0，8推非目标XY0。完整结果较父5N6/8改善但单seed，不作泛化成功结论。
- **差**：后盒仍失败、1200末恢复未完导致原依赖审核拒绝；不能称全部数学通过。新正常袋RGB171起目标不辨，正常盒342起不辨，斜盒171起不辨；斜袋513及后仍有左边黑色裁切片，已实际看并正确记录。新全部10review绑定齐；视觉风险不因数值过而忽略。见PRECISE_INTERIOR_CONCLUSION。
- 父初值候选helper/adapter旧5N全8共9592输入回放：默认关精确复现，开启仅26失败改变，其余9566动作/trace不变；26独立原数学门通过。新增audit_parent_seed_retry_metadata，保留前两次status8记录；全9592旧/新元数据核过，26正例及15篡改拒绝/3明确不override失败分支通过。HISTORY_CHECK/METADATA_HISTORY_CHECK/METADATA_REJECTION_CHECK绑定核过。
- 新 `staged_precise_parent_seed` 从完整精度版复制，只改collector/helper/adapter。默认关新CLI --rear-joint-edge-parent-seed-retry，需原analytic+precise+interior+unloaded/diagnostic，plan/raw metadata和调用已接，默认关闭AST精确、实际参数/记录及8非法组合拒绝、全部源编译INTEGRATION_CHECK过。候选helper/adapter仍与probe完全相同。尚缺完整显式新版物理source/执行/元数据审计、native/prelaunch/full协议；**未prepare/冻结/启动新物理**，不可拿旧审计身份冒充兼容。REAR_EDGE_PARENT_SEED_PLAN/PROGRESS最新；probe旧报告不改。
- CPU94754/6887旧pending已poll exit0；19175/97495/51233/37678全部图审/历史核验exit0；94175全5N绑定exit0；76848正式closer exit0。剩余约46GiB。下一步完成新候选全部版本审计/预检/原8+2协议再单物理对照，保持四族12fresh完整组/split→共享RGB11D→未调参192push3wait多seed实际h10与图审目标。

以下为历史记录，以本段为准。

## 2026-10-01T14:00:47.605379+00:00 精度困难后袋300.706通过，前后3/4；后盒恢复未完审核拒绝；父初值离线26/26

- 上轮/本轮progress，goal active，0新合格组/转换/模型。当前同一precise_interior_groups_r1全8+2，419冻结源全核不变；runner2210665/watcher2210666/collector2226607真实核活，layout840000；当前新case90实际归档与CLI精度true/5N核过。勿修改冻结源或重启。
- **好：后袋840004完整1200，原task/pose通过，推进300.706148mm，末10signedY205.816224mm**（父5N282.558失败）。失载仍8次；恢复commands345→313、交接8→7、push389→375；单seed不证明稳定/随机因果。前盒284.400374/末206.053272同过，四前后task **3/4 vs父2/4**。
- **差：首后盒仍败且1200末恢复路径未完成**。原audit_precise_interior_pose_live拒绝unfinished recovery path，normal/terminal/initial-near/region/height等依赖审核按原规则失败、缺报告，不是工具授权问题，不豁免。当前数学KKT是否改善尚未有完整报告可证明。后台继续全部条件并保留所有失败。
- 四条rawftol1e-13/四源身份/真实5N/首11D state/action0、assist0、非目标全过程XY0已核，四套8RGB+4外视已绑定。新前盒双方8样本可辨；后袋171仅左边碎片、342/513可辨但遮挡/裁切，685/856/1027/1199目标不可辨，部分帧仅盒边片。FRONT_BOX_RESULT/REAR_BAG_RESULT/FOUR_TASKS_RESULT最新。
- 新 **staged_rear_edge_parent_seed_probe** 只helper、默认关闭parent_seed_retry，原主+解析重试仍有限status8失败时，从原边界内父命令增量额外试一次。原成功/目标/边界/.055/float32/方向门保持，旧analytic_retry失败元数据保留，新增parent_seed_retry记录第三次。**未接采集器/版本审核/全协议/物理，不能归因当前后袋通过于它**。
- screen_rear_edge_alternative_initializers：原5N两rear全部26失败精确重现，三个离线初值中bounded_parent本身26/26通过。初次用SciPy旋转与采集器原rotation_xyzw不同导致基线不重现，已停止并修正重建后才出有效报告，不能把浮点重建差当效果。实际check_rear_edge_parent_seed_probe：default-off AST精确、26原失败default-off一致/开启26过独立URDF有限差分Jacobian与原1e-6KKT/边界/方向/5mm自间距，maxKKT1.57737206e-8；4保护分支/5失败链/2非法flag通过。PROBE_CHECK源hash全核，REAR_EDGE_PARENT_SEED_PLAN/PROGRESS列明尚缺完整历史接线、真实CLI/source归档和显式新metadata审核；不要假称旧审计兼容。
- CPU72675首次筛查因基线不重现exit1；修正后76820完整筛查、62954实际helper、63821前盒/18806后袋图审、3313接触更新均exit0。当前余4推2wait/6图审/原80+56继续，完成后全5N绑定与新版closer。完整四族12fresh组/split→共享RGB11D→未调参192push3wait多seed真实h10与图审不变。

- 2026-10-01T14:01:49.315923+00:00 同轮新正式审核：前袋PRECISE_INTERIOR_POSE_TASK_OPTIMALITY通过，5次ordinary override、0失败、max1.60618293e-8；前盒通过，168次ordinary override、0失败、max3.65983402e-8。父5N对应1/24失败；新实录与旧轨迹不同，不作逐帧同输入因果，但这两条实际原数学门已过。后盒仍被unfinished recovery依赖阻断，不能称全数值通过。

以下为历史记录，以本段为准。

## 2026-10-01T13:44:21.594088+00:00 精度首对1/2：后盒192.896仍败、前袋358.100过；实际raw精度身份已核

- 上轮/本轮progress，goal active，0新合格组/转换/模型。当前同一precise_interior_groups_r1全8+2，419冻结源全核未变。runner2210665/watcher2210666真实存活，当前children/collector见PRECISE_INTERIOR_PROGRESS；首case完成后可能处于primary审核阶段，不能用旧collector2210686缺失判断总作业停止，勿重启或改源。
- **好/差：首后盒1200推进192.896031mm（父5N160.782），末10signedY74.833229mm<200仍败；首前袋358.099505mm，末10signedY204.714671，原task/pose过。** 首对1/2与父5N相同。两套8RGB+4外视实际已绑定，后盒非首帧大多无可辨目标/棕色边片，前袋双方8样本可辨但手遮挡/底部裁切。
- 两条原始首11D state/action0、assist0、非目标全程XY0；实际5N CLI/两份plan核过，audit_precision_source_contract核4归档源、精度flag及**rawftol1e-13**通过。仅身份核验，当前最优性报告仍待后台完成，不冒称数值通过。FIRST_REAR_BOX_RESULT/FIRST_FRONT_BAG_RESULT/FIRST_PAIR_RESULT.md最新。
- 新diagnose_precise_contact_exit及新run CONTACT_EXIT_COMPARISON：后盒初始交接280→266、倾斜6→5、失载2→4（3/4最后COPX距边≤3mm）、恢复commands452→441、push221→240；单seed/不同轨迹，不作随机因果。父两rear+当前1rear报告，不假称后袋已完成。
- 新REAR_EDGE_EXECUTION_OUTCOMES / FINDINGS：旧5N/3N四rear，逐命令验证final_upper_command==raw.action，回退==父命令，前一末子步力包postpose==当前观测。5N后袋23失败回退都名义向外>0.1mm，3下一观测低载；20双方有载中14边距缩小>0.1mm。但115名义非向外修正仍12下一观测低载、103双方有载中14边距缩小，**只修失败回退不够，名义FK约束不保证实际接触**。全部为关联/末子步，非因果/连续物理；当前精度不改该非线性边缘solver。
- REAR_FRONT_REROUTE_RECHECK复核旧实际候选：简单“前移再侧推”固定朝向AABB路线后盒/后袋桌边margin−16.284/−48.540mm，原门拒绝；不能直接改走前侧，也不声称所有旋转/曲线路径都不可能。无新控制接线/相机改变，完整任务保留。
- CPU64609边缘实录、94663/3888图页均exit0；只读新诊断终止。余6推2wait/8实际图审及80+56继续，完成后全10压力5N绑定与新版closer。四族12fresh完整类别交换组/splits→合格RGB11D共享训练→未调参192push3wait多seed真实h10/图审目标不变。

以下为历史记录，以本段为准。

## 2026-10-01T13:32:47.687244+00:00 3N完整关闭5/8+2，独立5N精度版全8+2已启动并核90来源

- 上轮/本轮progress，goal active；0新合格组/转换/模型。当前唯一物理 **precise_interior_groups_r1**：runner2210665/watcher2210666/collector2210686实时核活，首840001后盒step300 top_lift。实际progress画面已固定并观看绑定LIVE_START_REVIEW：桌面/一手，极右窄棕色片，两完整包裹不可辨。勿把当前单帧或启动当任务/数值/视觉成功。
- **419冻结文件**，新协议SHA **bdf6ab73abc8ec8d7d240d83abb990bb313a1fb78059b246984ccee7133e4aa5**；首case **90实际归档源** 与冻结协议逐一一致，真实CLI precise_clearance_task_ik=true、top_load=5N。只相对关闭5N父增加普通task solver ftol1e-11→1e-13；原目标/限位/步长/float32/150iter、KKT1e-6、相机、接触/布局/顺序/预算不变。勿改冻结stage、auditors、drivers、预检/prepare、旧replay，勿重prepare或开第二物理。
- 当前用**新版** run_precise_interior_groups.py / watch_precise_interior_audits.py / close_precise_interior_groups.py，precise_interior_run_contract及audit_precise_interior_*。5预检均已核，全部6命令8推2wait/80原+56附加/36primary与10实际图审要求保留；source合同额外绑定四源/精度flag/raw1e-13。若将来出现非线性loaded task变化，原loaded执行拒绝保持，不可豁免。
- 父压力对照 **recontact_interior_load3_groups_r1** 已原冻结closer成功关闭，RESULT SHA **737adddf28707a91085905db8b20b0da7f858a0ef2dc64588771515174726441**，完整 **5/8推+2/2wait**（5N父6/8+2），两组2/4和3/4，0准入。全部10实际图审、80原全过/56附加52过、36primary及全10实际3N绑定齐。旧runner2178434/watcher2178435/lastcollector2207109已退出。4前后task最优性失败共7帧，max1.30247348e-6；正常/斜向4条数值过，不能豁免前4。
- **好/差：斜向袋150.012270mm原task/pose过，末10signedY228.359mm，最后等待稳定；统一3N总体退化，已拒绝采用。** 最后两条原始首11D state/action0、assist0、非目标XY0/等待全动作0，实际图审齐；3N斜向袋末段部分裁切，有左边碎片，不误记全画外。详见RECONTACT_INTERIOR_LOAD3_CONCLUSION及旧run RESULT。旧PROGRESS已关闭，新PRECISE_INTERIOR_PROGRESS是当前。
- 新只读REAR_COP_REFERENCE_DECOMPOSITION及脚本：两压力各后盒/后袋，逐段受力点相对选定点分解为COP−虚拟观测参考、观测参考−当前待执行命令、命令−选定表面点，代数恒等核过。后袋失载段COP局部X变化中位5N−16.58/3N−15.56mm，名义内部落点并未保证持续内侧接触。**当前命令未执行，差值不是跟踪误差；分量中位不可直接相加、虚拟参考不是物理接触面、未建立因果或新控制。** 没有混入新精度运行。
- CPU53370斜袋review与68872全参数绑定/关闭均exit0；prepare419及新后台已实际启动。剩余约48GiB，当前8+2完整跑完后verify_top_pressure_setting.py NEW5N 5与新版closer关闭。接续首例完成实际图审、rawmeta1e-13与audit_precision_source_contract，再全10/80+56，不以精度改进替代持续接触/相机方案。四族12fresh完整类别交换组/splits→共享RGB11D→未调参192push3wait多seed真实h10/图审总目标不变。

以下为历史记录，以本段为准。

## 2026-10-01T13:22:53.814534+00:00 3N七推4过+首等待过；八套图审齐；全8基准相机筛查与斜向袋图审纠错

- 上轮/本轮progress，goal active；0新合格组/转换/模型。当前原recontact_interior_load3_groups_r1全8推2wait继续，runner2178434/watcher2178435/collector2201188实时核活，layout840005；304冻结文件全核未变，当前斜向case840005共89实际来源与CLI3N核过。勿重启/修改冻结源。
- **好：斜向盒840005完整1200推进150.063828mm，原task/pose过**；末10min signedY244.954mm；首11D state/action0、assist0、非目标XY0。实际8RGB+4外视已绑定：0双方，171盒只余右边窄片，342后目标不辨。当前七推4过（困难前后仍1/4），并非完整run结果。
- 首等待841000完整70原质量过；双掌spread各2.098291mm、腰maxabs3.08738e-9rad，全11D动作0，首零/assist0实际原始核过。8真实RGB稳定空桌，已绑定，FIRST_WAIT_RESULT。当前7推+1wait共8图审齐，余斜向袋与最后等待随作业继续。
- **差：四前后原task最优性报告均失败，共7帧**（后盒1/前袋1/前盒4/后袋1），max1.30247348e-6>1e-6；正常左右两条KKT过。原80+56审核仍继续，计数见PROGRESS。统一3N退化结论保留，失败不入库。
- 新screen_full_interior_camera_fov.py / INTERIOR_FULL8_CAMERA_FOV_SCREEN.json：关闭5N基准全8×240真实相机位姿纯针孔筛查，旧4条全部指标一致，未改相机/未渲染新RGB。原焦距目标全画外按后盒/前袋/前盒/后袋/正常盒/正常袋/斜盒/斜袋为191/0/0/116/185/200/208/0。0.4焦距约105.76°，八条无全画外，但正常袋双方半框仅226/240；0.3约120.84°才全部240，物体宽高缩为30%，前盒p10约39×39px。半框为诊断指标不是新硬门；遮挡/畸变/硬件/模型效果均未验证。详情INTERIOR_FULL8_CAMERA_FOV_FINDINGS.md。
- **图审纠错**：复看父5N斜向袋同哈希REVIEW_EVEN，856/1027/1199实际仍有袋子左边裁切片，旧“完全画外”描述过强。新增INTERIOR_DIAGONAL_BAG_VISUAL_REVIEW_ADDENDUM.json纠正为部分裁切，原冻结图/绑定/RESULT未修改，不把投影单独当图审。原准入与失败不变。
- CPU12766全8筛查与50788斜盒review均exit0。独立5N精度完整5预检/协议已就绪但仍未prepare/冻结/物理；必须当前全10+80/56+10图审及压力绑定齐、进程终态后原closer关闭，再prepare_precise_interior_groups.py并单一物理新版driver启动。完整四族12fresh组/splits→共享RGB11D→未调参192push3wait多seed真实h10与实际图审目标不变。

以下为历史记录，以本段为准。

## 2026-10-01T13:14:04.653404+00:00 3N前后四推1/4，正常盒新增通过；五套实际图审、四任务力包核验完成

- 本轮progress，goal active；0新合格组/转换/模型。原recontact_interior_load3_groups_r1完整8推2wait仍在运行，runner2178434/watcher2178435与当前collector2200368实时/proc核活，layout841000。304冻结源不变；本case89实际归档与CLI3N核过。勿重启、勿改冻结源或协议。
- **差：前后四推由父5N2/4退化为3N1/4**。前盒283.511mm原task/pose仍过；后袋197.696mm（父282.558）仍败，末10min signedY102.439mm<200，失载8→9；前袋357.962→256.675由过变败。后盒推进160.782→197.826改善仍失败。不能推广统一3N，也不能以更多push帧代替成功。
- **好：正常左右盒840000完整1200推进150.227726mm，原task/pose过**；末10min signedY303.613mm。前5条原始首11D state/action0、assist0、非目标全程XY0，5套8RGB+4外视实际已绑定。后袋末4RGB无物体；正常盒342及之后目标不辨，仍不能声称视觉可学。
- FOUR_TASKS_RAW_CHECK / FOUR_TASKS_MEASURED_LOADS / FOUR_TASKS_DIAGNOSIS.md新增：四条件真实末子步力包逐条独立复算。后袋有载中位4.876→2.643N，低于0.2N push样本27→35；前盒5.181→3.264N。3N确实降载，但时长不同/单seed，不作随机因果断言。新可见性报告含5条：后袋240真实pose投影90目标全画外/85双画外；正常盒177目标画外，前袋/前盒0。投影不是遮挡证据；专家使用特权状态，不把图像问题当专家物理失败原因。
- 当前3份原task最优性报告失败共6帧（后盒1/前袋1/前盒4），max1.30247348e-6>原1e-6；后续仍在审核，不豁免。当前原/附加计数见PROGRESS实时快照。
- 独立精度阶段完整协议现已补齐：prepare_precise_interior_groups.py、precise_interior_run_contract.py及独立run/watch/close，RUN_PROTOCOL_CHECK新增通过，**全部5预检及来源hash再次核实**。保持父5N全6命令/8推2wait、80原+56额外审核及36primary，只有精度flag与显式新版源绑定；无相机/压力/任务门改变。PRECISE_INTERIOR_PLAN/PROGRESS为准。仍未prepare/冻结/物理，必须先当前3N完整关闭再启动。
- 当前余正常袋/2斜向推/2wait随作业继续；余5真实图审、全10压力绑定和全审核齐后用原closer关闭。CPU77508/86332/12816/57990均exit0。完整四族12fresh配对组/splits→共享RGB11D训练→未调参192push3wait多seed真实h10/画面目标不变。

- 2026-10-01T13:15:42.280301+00:00 同轮续作：第六条正常袋完整1200推进150.278531mm原task/pose过，末10min signedY268.341mm，首11D state/action0、assist0、非目标XY0，实际8RGB+4外视已绑定；171起7样本目标袋画外。当前六推3/6（父5N同六条4/6），六图审齐。原collector2194315正常退出后当前collector2201188布局840005真实核活；首等待case841000的89归档/CLI3N已核。仍余2斜向推2wait与4实际图审，全审核继续；NORMAL_BAG_RESULT/PROGRESS为最新。

以下为历史记录，以本段为准。

## 2026-10-01T12:53:29.423440+00:00 3N首对0/2：后盒197.826改善仍失败，前袋256.675由过变败；精度审核版本/文件读取已核

- 上轮/本轮progress，goal active，0新合格组/转换/模型。当前同一recontact_interior_load3_groups_r1完整8+2继续，304冻结源重核不变、协议SHA2da8e65585cebbead4ecbb1ecbaf887a396c753bddbf2f2e22854780bac73a37。runner2178434/watcher2178435活；实际子进程见PROGRESS，不以旧collectorPID独断停止。勿修改冻结源、PREFLIGHT、压力绑定helper/prepare或重启。
- **好/差新实测**：首后盒1200推进197.825715（5N160.782）、末10signedY76.993<200仍失败；倾斜6→4、失载2→4（4次最后COP都X边≤3mm）、恢复command452→415、push221→272。**前袋1200推进256.675422（5N357.962通过）、末10signedY100.780862，新失败**；失载2→8/路线切换7→1/push432→523。首对0/2 vs父1/2，不能推广统一降压。保持全条件继续。
- FIRST_PAIR_MEASURED_LOADS独立求解力包核实际垂直力：有载中位后盒4.982→3.010N、前袋4.786→3.065N；低于0.2N push样本后盒15→30、前袋5→19。末子步观测/不同轨迹时长，非随机因果；两条原始首11D state/action0、assist0、非目标XY0，实际3N参数已绑定。
- 首2套8RGB+4外视实际已绑定：后盒仅首帧两物体，其余7目标画外；前袋8样本双方可辨，袋底裁切/手遮挡。新OBSERVABILITY_AND_BOUTS_PARTIAL：后盒240投影200完全画外，前袋0且240半框；不把视觉问题当专家力学退化原因。FIRST_PAIR_RESULT.md/PROGRESS最新。
- 精度stage **staged_interior_task_precision** 新独立audit_precise_interior_* /precise_interior_audit_context/audit_precision_source_contract：显式PRECISE_INTERIOR_AUDIT_VERSION_MAP，15模块仅命名及增加源绑定断言、数学AST精确，原KKT1e-6/loaded拒绝变更规则等保留。source helper核真实精度flag/4归档源/solver仅ftol变化/raw1e-13，11合成metadata错误拒绝、10真实旧5N数据全部拒绝新精度身份。
- NATIVE_READER_CHECK：原4明确合成/padded文件258命令事件用新reader/新stage几何过；不是新物理或完整精度动作校验。INTEGRATION/PRELAUNCH/AUDIT_VERSION/NATIVE_READER四报告源hash全核，默认关闭、未冻结/物理，**仍缺完整新版run协议/driver清单，勿启动**；未混入3N。旧full8/212普通求解30失败→0独立复算保留。
- CPU29594native、47298/5023图页、20946可见性均已核exit0；新接触/压力只读脚本结束。下一继续3N余6推2wait、原80+56和余8图审，全参数绑定后终态close；再按完整结果选方案，独立精度物理和实际观测保持分开。四族12fresh整组/splits→共享RGB11D→未调参192push3wait多seed实际h10/图审目标不变。

以下为历史记录，以本段为准。

## 2026-10-01T12:40:32.125096+00:00 深入落点5N完整关闭6/8+2；3N同源码完整对照已启动；独立精度212次30失败→0

- 上轮/本轮progress，goal active，0新合格组/转换/模型。当前唯一物理 **recontact_interior_load3_groups_r1**，runner2178434/watcher2178435/collector2178454实时核活；首840001后盒step300 top_push，实际RGB仅桌面/一手，两物体不可辨，LIVE_START_REVIEW已绑定。**304冻结文件**，协议SHA **2da8e65585cebbead4ecbb1ecbaf887a396c753bddbf2f2e22854780bac73a37**，89实际归档来源与CLI3N已核。勿改冻结controller/auditors/drivers/plan_recontact_interior_load3.py/verify_top_pressure_setting.py/PREFLIGHT/协议，勿重prepare或第二物理。
- 父 **recontact_interior_groups_r1** 已原冻结closer成功关闭，RESULT SHA **b15f2ecbd327ebac8c536ba14af2d4280f3b41ccbf877c657ca3272e6d047d7b**。完整8推6过、2wait过，两组各3/4，0合格组；所有10实际图审及原80/额外56+primary已齐，旧runner2146722/watcher2146723/collector2175874均核退出。80原全过、56额外51过；5条原task最优性失败共30次（后盒1/前袋1/前盒24/后袋1/斜向袋3），max1.32711325e-6，不豁免。所有原始首11D state/action0、assist0；无训练。PRESSURE_SETTING_BINDING10条5N已绑定。
- 好/差：父后盒160.782末10signedY41.236、后袋282.558末180.696且终点运动，仍全失败；推进较父改善但成功率仍6/8，不能称成功率提升。最后斜向盒150.339186/袋150.141358mm原任务过，最终等待稳定。图审反复目标画外，尤其两个后排；四任务FOV诊断只覆盖原4条，不外推全8。RECONTACT_INTERIOR_CONCLUSION.md为完整结论。
- 新3N仅同一staged_recontact_interior的CLI顶部期望压力5→3，原6命令、8推2等待、顺序/布局/种子/预算/相机/所有质量审核不变，无控制源码分叉；压力减少可能改善盒倾斜也可能恶化滑脱，未有完整结果。不混入数值修复。父已关闭后才prepare304源并setsid实际启动；LAUNCH记录完整。
- 新独立 **staged_interior_task_precision** 默认关闭 --precise-clearance-task-ik 已从当前interior移植原精度修复，只有普通task_ik ftol1e-11→1e-13；父其他Python逐字相同，collector/coord关闭开关AST相同，9参数分支/实际solver和归档选择、6实际pre-AppLauncher CLI过。INTEGRATION_CHECK/PRELAUNCH_CHECK源码hash全核；**未适配新source-contract审核版本、未冻结/物理，不能启动或当旧审核已适用**。当前3Nrun完全不包含它。
- **INTERIOR_TASK_PRECISION_FULL_REPLAY.json** 对父全8报告212次普通修正实录独立复算，旧30失败→0，max1.24231944e-7，原目标/边界/float32/150iter/KKT1e-6不变。旧三条195/26报告保留且是新stage集成check依赖，勿覆盖。full新报告不等于物理或训练通过。
- CPU68993/17988/93446预检图页、93490绑定关闭、40522完整精度均exit0已核。当前仅3N物理/配套审核；剩余50GiB左右。RECONTACT_INTERIOR_LOAD3_PROGRESS.json及新run/PROGRESS为当前；旧RECONTACT_INTERIOR_PROGRESS已改关闭状态。
- 下一接续同3Nrun全8+2、原80+额外56、10实际图审、实际3N参数绑定（verify_top_pressure_setting.py NEW_RUN 3），进程终止后同冻结close_recontact_interior_groups.py关闭。随后独立解决精度审核版本与物理、实际观测方案；完整四族12fresh配对组/splits→合格RGB11D共享训练→未调参192push3wait多seed实际h10/图审目标不变，失败数据不入库。

以下为历史记录，以本段为准。

## 2026-10-01T12:25:53.278896+00:00 六推已完成4过2败；原KKT26失败，3N单因素完整对照预检就绪未启动

- 上轮/本轮progress，goal active，0新合格组/转换/模型。同一recontact_interior_groups_r1仍运行，295冻结源重核无变，勿改stage/auditor/driver/protocol/reprepare。
- 新正常左右840000盒推进150.237769mm、袋150.059216mm，原task/pose均过，6推已完成4过2败（两后失败保留）。六条首11D state/action0、assist0、非目标实际XY0复核。6套推8RGB+4外视及1套等待8RGB已实际绑定：新盒342后画外、新袋171后不可辨，不冒称视觉可学。首等待841000完整70帧质量过，双掌spread各2.0983mm/腰漂3.08735e-9rad；原始5N/零位/无助推绑定已核。余2推1wait/3图审和全审核继续。
- 原独立数值报告目前三条KKT失败26（后盒1/前袋1/前盒24，max1.327113e-6>原1e-6），不是全审核过。INTERIOR_TASK_PRECISION_REPLAY在三份完整报告195普通修正上旧26失败→0，max1.242319e-7；仅ftol1e-11→1e-13，目标/限位/原1e-6门不变，未接线/物理/混入压力候选。未来新报告不自动包含在该3条复验。
- 新plan_recontact_interior_load3.py及recontact_interior_load3_plan/PLAN.md/PREFLIGHT.json：保持同一冻结collector/auditors/相机、全部8推2wait/顺序/种子/1200/70，只CLI顶部压力5N→3N；六条实际pre-AppLauncher通过，无源码分叉。verify_top_pressure_setting.py绑定实际CLI与frontal/raw两份计划，5条5N真记录接受5N、拒绝错误3N标签；未证明3N物理收益，摩擦减少可能恶化袋滑脱。新run目录尚未创建，不启动第二采集。
- 必须先父完整审核/10图审和已冻结close后，执行plan_recontact_interior_load3.py --prepare（核父RESULT完整/进程退出/源hash），再用相同run_recontact_interior_groups.py和watch_recontact_interior_audits.py启动新recontact_interior_load3_groups_r1；新run结束还要verify_top_pressure_setting.py NEW_RUN 3后原closer。不能预先冻结未完成父结果或豁免原失败。
- runner2146722/watcher2146723实查存活，当前STATUS completed7，layout840005，当前真实children见PROGRESS；采集是否活跃以/proc核验，不以旧collectorPID或STATUS推断。CPU30913/23043预检、88543精度、77248/96306图页均已核exit0。
- 后续完整目标不变：四族12fresh类别交换整组/splits→合格RGB11D共享训练→未调参192push3wait、多seed实际h10及真实图审；不以本参数对照或局部精度成功代替目标。

以下为历史记录，以本段为准。

## 2026-10-01T12:15:53.439384+00:00 深入落点四前后任务2过2败；后袋282.558mm仍失败，真实相机画外风险量化

- 本轮progress，goal active；0新合格组/转换/模型。当前同一recontact_interior_groups_r1原8+2，295冻结源和当前89归档重核不变，协议SHA378828c91164c2599aeaae4bc04ccf49ae258c8719f278bc4f2a9610414341a5，勿改stage/audit/driver/protocol或reprepare。
- 好：前袋357.962、前盒284.453原task/pose过；后盒160.782、后袋282.558较父改善。差：后盒末10signedY41.236、后袋180.696<200，后袋末态运动，均失败。四条实际原始首11D state/action0、assist0、非目标XY0，4套8RGB+4外视已实际绑定。
- 新接触诊断INTERIOR_CONTACT_MOMENTS/INTERIOR_BOUT_PRESSURE：后盒有载push121→206、载荷中位6.044→4.979N，点力矩中位降低但仍6倾斜2失载；后袋8优先落点仍8失载（父9），恢复command335→345、push376→389。非随机单次，不作因果/成功宣称。
- OBSERVABILITY_AND_BOUTS_PARTIAL：各240真实相机位姿，后盒目标画外191、后袋116（双物体同时191/71）；两前任务0。actual4图审完成，后袋末4RGB仅桌面。CAMERA_FOV_SCREEN仅静态投影，0.5焦距HFOV93.177两后目标画外0但半框/双目标不足；0.4 HFOV105.762四条双半框全覆盖、物体缩小至40percent。无新渲染/真实相机兼容或模型验证，不改当前相机/准入门。
- runner2146722/watcher2146723实时核活，旧2155111正常退出，当前collector2163275、layout840000实时核活；STATUS completed4。四条primary各4调用完成且过，原80/额外56仍执行，勿称全部通过。CPU60410/96063/20350/88649/98917均exit0；新诊断终止。
- 下一继续同run余4推2等待和6图审、80+56全审核后冻结close。FOUR_TASKS_DIAGNOSIS.md、RECONTACT_INTERIOR_PROGRESS为最新。完整四族12fresh配对组/splits→共享RGB11D→未调参192push3wait多seed实际h10不变。

以下为历史记录，以本段为准。

## 2026-10-01T12:00:55.380251+00:00 深入落点首后盒160.782mm改善仍失败；前袋通过，完整批继续

- 上轮/本轮progress，goal active，0新合格组/转换/模型。同一 **recontact_interior_groups_r1** 全8+2继续，295冻结源重核不变，协议SHA378828c91164c2599aeaae4bc04ccf49ae258c8719f278bc4f2a9610414341a5。勿修改冻结stage/audits/drivers/protocol或reprepare。
- **好/差** 首后盒1200推进160.782（父113.536）但末10signedY41.236<200，原任务/姿态仍失败；非目标XY0，首11D state/action0，assist0。6优先/2fallback，8交接，恢复command532→452、push124→221；倾斜退出8→6、失载1→2。初始region交接280vs289，改法前已不同，勿把单次全部收益当因果/多seed已证。FIRST_REAR_BOX_RESULT及CONTACT_EXIT_COMPARISON已存。
- 后盒8RGB+4外视实际绑定，除首帧两物体外其余7RGB都不辨目标，末4仅桌面。**实际独立pose审核passed，460事件/8交接**，只读预核FIRST_REAR_BOX_POSE_PRECHECK与后台正式INTERIOR_POSE_LIVE_AUDIT逐字段相同；不等同全部质量/audits过。
- 前袋1200推进357.961506mm，原task/pose过、非目标盒XY0，首state/action0、assist0；实际8+4已绑定，双方8样本可辨，中段袋遮挡/裁切，1027/1199手抬离。整组尚不合格。
- runner2146722/watcher2146723实时存活；旧collector2146736已正常退出，当前已进入840004物理collector2155111（实际/proc核活），STATUS completed_conditions=2；89新case来源也再次核齐。原审计调用数以PROGRESS/EXECUTION为准，未全过。CPU46259/32065/23928已核exit0。
- 下一接续同run，完成840004等剩余6推2等待、原80+额外56和余8实际图审；按原步骤冻结close。完整目标四族12fresh完整配对组/splits→共享RGB11D→未调参192push3wait多seed实际h10保持。RECONTACT_INTERIOR_PROGRESS/PLAN及run/FIRST_LAYOUT_RESULT.md为当前。

以下为历史记录，以本段为准。

## 2026-10-01T11:48:38.332305+00:00 深入落点优先完整8推2等待已实际启动；原生/独立生命周期审核已完成

- 上轮/本轮progress，goal active，0新合格组/转换/模型。当前唯一物理 **recontact_interior_groups_r1**，runner2146722/watcher2146723/collector2146736均实时实查存活，840001后盒进行。协议SHA **378828c91164c2599aeaae4bc04ccf49ae258c8719f278bc4f2a9610414341a5**，295文件冻结；89实际归档核齐。**勿修改冻结stage/审计/driver/protocol，勿重prepare或误重启。**
- 好（实现证据）：20合成响应rollout/1251独立命令及实测捕获，4真实first/last起点，7类active停止均拒绝；原生4合成258事件+6原未启用轨迹、16篡改拒绝；14依赖审核只名称替换AST精确，16落点优先记录13篡改拒绝，6实际pre-AppLauncher CLI/80原+56额外控制流一致。stage五个CHECK当前hash全核。
- 差/风险：末袋原1200预算5例失败保留，原25ticks交接1214/新32ticks1221；首袋原72→新89ticks，深入落点必须用真实更少滑脱抵消额外时间。原task精度候选仍隔离未混入，新phys仍可能原1e-6失败。frame180实际RGB已看，仅桌/手，两物体画外，不能称可学或完成完整图审。
- 文件夹具首次继承实际残余filtered load但空force包为0被原审计拒绝；修为明确合成空历史，所有载荷仍在原卸载区间，未改审核门/真实轨迹。第二次转换漏episode字段已补；before_interior_native_contact_history保存两次失败。late-remap/padding仅IO测试，绝不能入库。
- CPU65582生命周期、53239协议、35557版本、71491/10334前两次fixture失败、32730最终fixture均已核终止；准备/启动命令exit0。当前Newton MJWarp采集，无训练；~53GiB启动前空闲。
- 直接下一：接续同run完整8+2，原80+额外56审核及10实际RGB/外视，重点两后排真实COP/恢复时间/成功。完成且pids退出后仅用已冻结close_recontact_interior_groups.py关闭；失败/短轨迹/unfinished均留分母不入训练。RECONTACT_INTERIOR_PROGRESS/PLAN为当前。四族12fresh完整配对组/splits→共享RGB11D→未调参192push3wait多seed真实h10目标不变。

以下为历史记录，以本段为准。

## 2026-10-01T11:31:05.679464+00:00 更深入接触落点15/18可行；新默认关闭优先/回退候选已接线，未物理

- 本轮progress、goal active；0新合格整组/转换/模型，无物理/训练/CPU作业。CPU66260（18端点）、23391（精度复验）、40749（接口）均实际exit0；10455交接核验exit0。上一段的66260仍运行状态已过期。
- 完整loaded_edge_coverage已关闭6/8+2、0组；RESULT SHA 0bfd4b9580b3e5ec8aa5cd8110c27eccb2147f235baca5c6b391e687886358dc，964冻结源不改。差：后盒862帧98.720mm/后袋268帧86.349mm提前停止；前盒另有原KKT24失败。全部10图审与80+56审核完成，详见LOADED_EDGE_COVERAGE_CONCLUSION。
- **新好/差** staged_recontact_deeper_probe全部18真实恢复起点独立绑定与几何完成：20mm端点15/18（盒6/9、袋9/9），选中插值路径几何全过；盒早期330/449/559无解。可行盒路径点316→441，袋331→407，恢复时间可能更长，尚无物理收益。
- 新stage **staged_recontact_interior** 从原recontact_pose复制，未继承失败新edge适配器。仅默认关闭CLI --recontact-interior-preference：优先20mm端点及插值几何，失败明确日志并用原12mm规划器；原12mm失败仍失败。原卸载/跟踪/实测交接/loaded控制/5N/预算/质量门不变。CONTRACT_CHECK当前通过：关闭collector/lifecycle AST一致、原规划器逐字一致、18缓存路由、2实际无缓存求解（盒330回退/袋301优先）、4CLI与实际来源归档，其余父Python逐字不变。未冻结、未物理、非数据准入。
- 数值独立复验 **LOADED_EDGE_TASK_PRECISION_REPLAY**：6完整报告178原task修正，收紧ftol1e-11→1e-13后24失败→0，max8.065455e-8<原1e-6；短后排无完整报告不在此复验中。未合并新候选/不冒称物理已过。
- **直接下一** RECONTACT_INTERIOR_PLAN/PROGRESS：完成优先/回退生命周期逐步跟踪、实测捕获、停止分支及独立原生/source合同版本；原全8+2冻结单物理/全部审计实际图审，再判断减少滑脱是否抵消更长路径。禁止只拿15静态落点或24数值修复当任务完成。四族12fresh完整组/splits→共享RGB11D训练→未调参192push3wait多seed真实h10目标不变。

以下为历史记录，以本段为准。

## 2026-10-01T11:23:07.500576+00:00 有载边缘完整关闭6/8+2；方向冲突与有载预测误差已定位

- 上一分拣轮/本轮progress，goal active；0新合格整组/转换/模型。loaded_edge_coverage_groups_r1 runner/watch/collector已退出；冻结closer实际exit0，10图审和全部80+56审核齐，964源重核不变。RESULT SHA 0bfd4b9580b3e5ec8aa5cd8110c27eccb2147f235baca5c6b391e687886358dc。勿重启/修改冻结源/重prepare。
- **差** 两后排提前停止：盒862/1200推进98.720mm、袋268/1200推进86.349mm，均no_verified_nominal_edge_command。原前盒任务过但KKT24帧失败max1.38225883948e-06；门未改。左右/斜向各3/4，均拒绝训练。
- **好** 前袋357.863、前盒283.840、4容易150.018–150.230mm原任务过，2等待过；最终3条8RGB/4外视或8wait实际已看并绑定，现10条齐。最终盒171后目标画外，袋513靠左/685后裁切，RGB风险保持。原80调用68过，额外56调用43过，短失败依赖失败保留。
- **机制** 两停止点数值比例重试可局部恢复；独立probe188旧成功不变+2停止点通过，未接线/物理。后袋角点两个向内基向量对推进均负，固定物体平面内正推进不可行；265–267实际袋推进0.9447→0.0492mm/步，retry-only不足。
- **新证据** LOADED_ONE_STEP_RESPONSE_DIAGNOSIS六实录有载状态评估完成，空载因果预测接触下最大误差7.791mm；不能充当有载保障。LOADED_EDGE_RESPONSE_BUDGET_SCREEN8状态24比较：名义5mm7/8、因果5mm6/8、额外完整8mm误差余量0/8，均未物理。首版误差余量被半步缩小已保留并修正，以当前v2为准。
- 当前CPU新screen_recontact_deeper.py/句柄66260正在筛查全部18恢复起点，仅新隔离staged_recontact_deeper_probe改规划内缩12→20mm；与旧冻结stage无交叉写。不预测通过/不训练。先实查该句柄/进程和/tmp/recontact_deeper_endpoint_screen.log，再读DEEPER_ENDPOINT_SCREEN.json；当前尚未获得结果，勿称已完成。
- 已终止核验CPU16284(close)、83644(初筛)、7586(修正筛查)，先前20089已输出完整结果；无物理/训练进程。完整结论LOADED_EDGE_COVERAGE_CONCLUSION.md；四族12fresh配对组/splits→RGB11D共享训练→未调参192push3wait多seed真实h10目标不变。

以下为历史记录，以本段为准。

## 2026-10-01T10:45:47.556541+00:00 有载边缘实际首后盒862帧停止失败；前袋通过，完整批续跑840004

- 上轮/本轮progress，goal active；0新合格整组/转换/模型。loaded_edge_coverage_groups_r1继续原8+2。runner2104470/watcher2104471/当前840004 collector2110564实查存活，旧collector2104509已退出；STATUS已完成2条件。勿重启/改冻结stage/审计/协议/重prepare；964源刚重核不变，89实际采集源启动已核。
- **坏结果** 首后盒862/1200提前停，推进98.719647mm，原目标失败；停止理由no_verified_nominal_edge_command，非目标XY0、首11D state/action0、assist0。127实际edge修正；只读861已执行决策独立前缀复算全过max3.25815e-7，不代替全长/质量审计。8RGB+4外视已看绑定：首帧双方可见、738小盒角，多数其余画面仅桌/手。
- **原因新证据** stop862三候选均status8，两个端点独立局部几何+KKT过；3候选×比例1/100/5000重试9次，1/100的6次status0且同原1e-6过，5000仍8。未执行、不修改冻结源；仅表明该记录上下文下不是已证的几何不可行。当前q绑定pre862/上一action绑定raw861、xyz绑定packet861；停止时R仅记录上下文存在，不能假称另有orientation862。详情LOADED_EDGE_FIRST_STOP_DIAGNOSIS及FIRST_EXECUTED_PREFIX_DIAGNOSIS。
- **好结果** 前袋完整1200推进357.863188mm、原任务/姿态通过、非目标XY0；新native/pose/geometry等primary过，8RGB+4外视已看并绑定，双方8样本可辨，袋中后期遮挡/裁切；不称完整组/模型成功。
- 原20/80审核调用14过，额外14/56调用8过，短轨迹/依赖失败保留；更多审计和条件仍执行，以EXECUTION更新为准。新review_completed_diagnostic_episode仅允许生成短失败轨迹同样8+4图页，不改任何数据门或quality。新增CPU96571/11384/78503/26455均exit0已核；一次只读系统python缺numpy未读出，换环境解释器重跑。
- 下一：保持原全批，继续实际图审、实际edge/持续COP与两后排终点，完整close后再决定是否用明确版本的数值重试候选，不在当前中途修。四族12fresh整组/splits→合格RGB11D共享训练→未调参192push3wait多seed实际h10/图审目标保持。

以下为历史记录，以本段为准。

## 2026-10-01T10:35:23.064202+00:00 新有载边缘覆盖完整物理已启动；原审核数学保持且新增全记录绑定

- 上轮progress，本轮progress，goal active。0新合格整组/转换/模型。当前唯一物理loaded_edge_coverage_groups_r1，runner2104470/watcher2104471/collector2104509均实时核活，原840001后盒进行；不再称仅离线。CPU检查68421/40914/61569/58282/23889/33636/79529均exit0已核。
- 冻结964文件，协议SHA 60aa3d168a25e7fc9b9775462c7640b2fc9b51dcf904b09aab63e379389c8669；启动后89实际来源对协议核齐。**勿修改staged_loaded_edge_coverage、审核/runner/watch/closer/协议或重跑prepare**，stage内BASELINE保留冻结前描述，以外部progress/本段为准。剩余55GiB起跑；单采集无训练。
- **好（实现证据）** 原生读写10条9740帧/2398边缘决策/58修正、12篡改拒绝；4来源夹具/8拒绝、实际计划字段精确；原全程geometry9740帧和task9592数学AST/实录一致；原loaded8轨迹一致；实际新审核动作链2398/58及8负例通过；11region/reference/normal/height依赖仅命名替换AST精确；完整原80+56和新增10coverage注册、实际CLI/defaultoff/stop来源当前，运行控制流保持原全条件。合成文件q/对象来自旧录制，不是新物理/训练数据。
- **差/新增诊断** 原KKT直接复算共29帧失败，含此前后袋unfinished pose阻断依赖报告而未计的1帧；已关闭RESULT仍是3条28已报告失败，不追改或宣称父全审核通过。新数值筛选只作用新edge候选，原全局task求解器仍旧且门不变。当前实际step150政策相机图已看：桌面/手，袋盒不可辨，画外风险保持；完整新物理任务收益未定。
- 新audit_loaded_edge_coverage_live逐帧绑定raw/action、coord两份记录、真实packet(t-1)、前级legacy动作和finalclearance，完整1200/70+零位无助推，短/停/漏记拒绝。新pose/sourcecontext保持无载数学；新版geometry/loaded先核父提议再核独立edge最终动作；新task原数学照核，失败不豁免。
- 下一接续同句柄全8推2等待，原80/额外56/新增10审核与10实际图审，突出两后排任务/持续COP/原KKT，再冻结closer关闭。全四族12fresh整组/splits→合格RGB11D共享训练→未调参192push3wait多seed实际h10/图审目标不变。详见LOADED_EDGE_COVERAGE_PROGRESS与PLAN。

以下为历史记录，以本段为准。

## 2026-10-01T10:18:00.780025+00:00 重接触完整关闭6/8+2；当前有载边缘候选修复1次数值选优缺口

- 上一目标轮progress（中间Git侧任务完成），本轮progress；goal active。0新合格整组/转换/模型。当前无采集/训练作业；CPU检查句柄17900/9445/12695/46496/27022/92133/87417/82415/37193/8919/5318均终止已核；失败检查日志保留。55GiB空闲。
- **父批已完整关闭** recontact_pose_groups_r1 RESULT SHA f198ec18aca1808eb8c0ecf94ac4f4d69ca393ea1ec79143ba594529692a9f97；原8推6过、2等待过，左右/斜向各3/4拒绝。80原+56额外全部调用、10实际图审绑定齐，210冻结源重核不变；STATUS旧名称仍pending时以RESULT为准，勿重启/重prepare/改冻结源。
- **好/差** 前侧两条及4容易原任务过、8推非目标XY0；后盒113.536mm退化，后袋269.076mm虽改善但末Y174.186mm<200仍败。末1199恢复未交接，pose及依赖审计失败；KKT原1e-6有3条28帧失败、max1.36982e-6，未豁免。
- 新LOADED_RELATIVE_CONTACT_MOTION诊断：后袋317连续有载对中169近X边，38名义外移、58实际外移，21名义不外移仍实际外移。38漏修分别17重复firstloaded、5无X内切片、3Cartesian已feasible、13solver失败；均真同bout推动。原Cartesian.override依赖造成覆盖缺口。负物体平移/接触迁移可占优，名义纠偏不证明真实COP稳定；后盒压力/偏心倾斜与袋滑移分开。
- **新staged_loaded_edge_coverage默认关闭已接线，未冻结/未物理**。当前packet(t-1)有载+同推动阶段决定资格，不要求上一载荷/Cartesian.override；保留真press→push与原guard/terminal/region/无载路径。原全局task_ik与5N压力未改。初完整58独立审计抓到后袋1165帧1.60342e-6（旧39状态未覆盖），before_loaded_edge_coverage_stationarity保存失败；现对最终float32三初值候选先原1e-6驻点筛除再按代价选优，无合格就显式停止。
- **当前预检** 实际8历史流9592帧/58修正/0拒绝；58独立COP/原界/肘/方向/KKT全过max5.15064e-7、12篡改拒绝；9592独立分支覆盖8种原因/8错标签拒绝（含19真transition保持）；实际collector58开/58关+2停止过；12正8负CLI/关闭AST精确过。5当前报告哈希均核齐。root同名prototype和39报告是历史，实际选择stage版；ADAPTER_CHECK是旧夹具，以ADAPTER_ACTUAL_CHECK等当前5报告为准。
- **直接下一任务** 原生raw/coord/contact/final/source绑定和原pose/sourcecontext/全程self-clearance/loaded/KKT/region依赖明确版本化（旧冻结审计不能直接冒称适用新动作），完整原8+2协议watch/close接线后冻结并物理。不得把反事实通过当收益，也不混入全局precision或压力改法。四族12fresh整组及划分→合格RGB11D共享训练→未调参192push3wait多seed实际h10/图审全部保持。详见LOADED_EDGE_COVERAGE_PROGRESS.json与PLAN.md。

以下为历史记录，以本段为准。

## 2026-10-01T09:26:42.306912+00:00 重接触姿态困难4已完成2/4；后盒退化、后袋改善仍未入区

- 上轮分拣progress，本轮progress；goal active，0新合格整组/转换/模型。继续同recontact_pose_groups_r1，runner2052462/watcher2052463，840004物理collector2060509已正常退出，当前runner在该case原主审核；以STATUS与实时proc为准，不因旧collector消失重启。当前原控制9/80、额外3/56已完成，其余继续，未全部通过。冻结210源本轮重核不变、阶段/协议勿修改。
- **好**：前袋358.188/前盒284.584mm原任务姿态过；四困难非目标最大XY0；后袋推进269.076mm好于腕prior232.855，但末Y174.186mm未达原200mm，仍失败。4条实际8RGB+4外视全已绑定，0合格新组。
- **差**：后盒113.536mm退化；541新独立已验证事件(532command+9handover)，仅124推动帧，9结束bout=8倾斜/1失载。后袋335command+8handover、376推帧，9失载、6次末COP贴X边，8次Zbias-6mm；末1199仍command、路径未交接，独立pose审计已以unfinished recovery path退出1，无通过报告；不放宽预算或审计。两个类别失败机制不同。
- 新只读接触分析显示后盒初COP仅1/9贴任一3mm边，但载荷中位6.044N(旧3.34–3.36)，偏心按压力矩XY中位.1648/.3571Nm增大；这不是全净力矩/因果证明。真实camera240样本后盒172两物体全出画、后袋113目标出画(76两物体)，前袋/前盒图审可辨；新诊断用记录相机姿态，后盒投影图已实际看，非遮挡/全程像素可见证明，不新增可视硬门或改标定。
- 离线端点：三真实起点仅居中3/3可行但腰达.98、视野更差；居中+视野0/3。去腕回零偏好、两种视野目标×3起点×4初值共24求解，6组合0合格；局部失败不证明全局不可达，未接线/未物理。相机FK对240实测最大位置2.06e-8m/矩阵2.05e-7。初脚本误以每command都有planning已修为只读新path记录，失败日志保留；CPU39309/61477和诊断25091终止已核。
- 详情CONTACT_FINDING_PARTIAL.md及RECONTACT_POSE_PROGRESS。下一完成当前余4推2等待/80+56/10图审后冻结closer；再按两后排机制设计受控压力/接触路径优化，不采用已失败视野目标。四族12fresh整组/splits→合格RGB11D训练→未调参192push3wait多seed实际h10全目标保持。

以下为历史记录，以本段为准。

## 2026-10-01T09:12:14.379353+00:00 重接触姿态完整物理已启动；首后盒113.536mm失败且RGB视野丢失

- 分拣上轮progress（新增region/reference/control接线并真实启动）；Git备份侧任务已完成，本轮恢复同一物理句柄，goal active。0新合格整组/转换/模型。
- recontact_pose_groups_r1已冻结210文件，协议SHA aee0fc43ee9e3f02e1a7ccdc4423272535f6274cd2ece6ba1216c774a726a648；87实际归档来源启动已核，当前210冻结源全重核一致。runner2052462/watcher2052463/collector2052472本轮ps核活，840001前袋继续。勿修改stage/审计/协议或重跑prepare；原8推2等待1200/70预算不变。
- 上轮region链8完整回放/16capture/81拒绝、reference等8回放、实际六CLI/80controls预检完成；原80审核中的normal/terminal/nearhalf显式版本化，额外56，原数学门不放宽。
- **差**首后盒完整1200推进113.536mm、未到目标区，比腕prior124.420mm和父rear-short121.454mm退化。记录532新路径command、9次handover；不是恢复不执行，持续接触收益须用真实COP核。原始质量及姿态门失败，不能训练。
- **好**首后盒非目标XY0、support/upright过。实际8RGB+4外视已看且绑定：首帧两物体可见，后续大多只见桌面，513仅盒角，685后四样本两物体不可辨；不是全程可视证明，RGB可学性风险突出。独立全审计仍待case结束，不报全部通过。
- 下一：接续同批8+2，逐条实际图审和80/56审核，完整关闭后才决策；同时定位恢复后的接触与视野。原四族12fresh整组/splits→合格RGB11D共享训练→未调参192push3wait、多seed实际h10/画面全目标保留。

以下为历史记录，以本段为准。

## 2026-10-01T08:44:26.902792+00:00 原生文件及loaded/KKT/几何/height版本已预检；发现晚期恢复超预算

- 上轮/本轮progress，goal active。0新合格整组/转换/模型。候选staged_recontact_pose运行源本轮未改、未冻结、未物理。上一批仍腕prior6/8+2wait、0整组。当前无采集/训练；本轮所有CPU句柄60409(初夹具失败)、4594/25025/5507/54493/25213/6381/10253/22431/58865均已核终止，最终v5原生文件exit0。磁盘57GiB。
- **好：新独立原生文件绑定已过** audit_recontact_pose_live读取实际格式raw/trace/orientation/frontal/coord/expert/region/recontact/contact/selfclearance/terminal和冻结来源；实际q/action、前包packet(t-1)载荷/滤波、decay/core存档来源、无载gate/动作链/捕获及持续normal/inactive/局部点一致性。4合成文件轨迹442事件+6原始前侧/容易完整轨迹、16篡改拒绝；空桌无frontal合法、push缺frontal拒绝。完整442是I/O夹具，不是新物理，静态补齐不能训练。
- **旧门未放宽**：新task版本与原KKT数学AST精确，8父轨迹9592帧一致，父rear-short原22失败保留；1768新路径分支/4负例；loaded数学AST精确、8父轨迹454真实加载帧一致；全程self-clearance原几何/普通链AST精确、10父轨迹9740帧一致；height原8一致、新16路径/16负例过。新loaded入口仍要求全程geometry报告通过/来源一致；这些新版本源码在根W，旧冻结审计未改。报告LIVE_FILES_CHECK/TASK_OPTIMALITY_CHECK/LOADED_EXECUTION_CHECK/SELF_CLEARANCE_CHECK/HEIGHT_CHECK均当前源码重核绑定。
- **差：局部成功存在预算假象**。首次原生夹具晚起点写入1200帧越界，进一步RECONTACT_ORIGINAL_BUDGET_SCREEN绑定冻结协议发现16合成路径8预算内、8超；晚盒1136起172事件到1307(超108)，晚袋1130起135到1264(超65)。真实1200/70预算不变；I/O夹具明确把晚起点平移到800仅为读写测试，不可作任务证据。真实策略早段改变后未必到这些晚状态，此发现是风险而非新物理结论。
- 原生夹具还修了front/easy没有region文件这一实际schema；新增source decay/core核验和wait缺plan规则。v4运行期间补wait分支后不采用旧绑定为最终证据，完整新v5已重跑过；失败/旧日志保留。Source/runtime stage未改。
- **直接下一任务**：版本化region action/causal/continuity/measured-bounds及rearXY审核链，允许且只允许独立验证的新handover更新selected point；不要改冻结旧脚本。然后完整watch/close/protocol接线核实际源/CLI/空桌/停止与审核依赖，才冻结同8推2等待1200/70物理。未运行新物理不是后台在采集。precision仍隔离，整任务优先看接触持续性/两后排终点与预算，不报局部到位当完成。
- 原四族12fresh整组/splits→合格RGB11D共享训练→未调参192push3wait、多seed实际h10/画面全目标保留。详见RECONTACT_POSE_PROGRESS.json与PLAN。

以下为历史记录，以本段为准。

## 2026-10-01T08:21:56.363452+00:00 新重接触独立事件/动作链/normal审核通过；仍未物理

- 上一分拣goal turn progress（中间Git侧任务已完成），本轮progress，goal active。0新合格整组/转换/模型。当前无物理/训练进程；本轮CPU检查句柄19082/25365/30191均已核实exit0。已冻结父版/腕prior实验不改、不重跑prepare。
- 补记上一轮实际接线：staged_recontact_pose基于已关闭rear-short，默认关闭。scene/plan/lifecycle/adapter已接线；16合成plant1768事件/16交接、15CLI/default-off AST精确、实际collector/coordination及停止传播检查通过。新stage未冻结、未物理。完整来源见RECONTACT_POSE_PROGRESS.json。
- **好：本轮独立审核过** audit_recontact_pose_events不调用候选几何/控制，独立URDF手/肘、face-axis双手对物体间距、因果命令、原界/步长/.055slew、实际到位3帧/控制点/normal/非工作掌捕获。全部1768事件16交接，21篡改拒绝；实际collector最终动作链同1768保持命令、3536terminal拒绝；normal原数学/阈值重放8历史物理记录过，16合成交接/64篡改拒绝。INDEPENDENT_EVENTS_CHECK/FINAL_ACTION_CHECK/NORMAL_CHECK三个报告及runtime源哈希已重核。
- **差/限制：仍无新物理成功证据**。最后完整腕prior仍6/8+2wait，后盒124.420/后袋232.855mm未到原目标区；原KKT4条24帧败，整组拒绝。新增通过只说明实现与记录一致，未解决物理接触/任务终点，也不证明新模型可学。
- 新路径逻辑mode是top_cross，但执行关节路径可降到precontact；原target_xyz .86是未执行Cartesian参考，不得用旧cross审计冒称执行通过。真实handover重设normal/局部点/非工作掌，需明确版本；无载path之外原loaded数学及KKT1e-6保持，不得跳过。对象变化>2mm/.02rad或原guard/load变化显式停止，当前没有自动重规划。
- **下一直接任务**：将独立event/normal审核绑定实际episode raw q/action、对象pose、packet(t-1)载荷/滤波、coord/expert/region及冻结来源，做实际文件夹具负例；版本化loaded/KKT与region/height审计（旧冻结文件不改），齐后冻结原完整8推2等待1200/70预算。precision不混入。完整原四族12fresh配对组/splits→合格RGB11D共享训练→未调参192push3wait多seed实际h10/画面目标保持。

以下为历史记录，以本段为准。

## 2026-10-01T07:44:02.893392+00:00 无载腕偏好完整6/8+2等待关闭；新无载姿态追踪原型已实现但未接线

- 上轮、本轮均progress，goal active；0新合格整组/转换/模型。unloaded_wrist_prior_groups_r1已由冻结closer完整关闭，RESULT.json SHA40b8c8ab6ee4cb06d84b9f2301907ecfc3131e69a94d02844b75be5ee577be6e，RESULT.md齐，PARTIAL指向终稿。runner1983639/controls1983643/extra1983644/collector2002883已ps确认退出；本轮无新物理作业，不要称后台仍在采集。原stage/协议/报告不改、不重跑prepare。
- **好**8推6过、2等待过；两前侧与4容易保留成功、八推非目标XY0。**差**两后排124.420/232.855mm仍失败，左右/斜向整组各3/4拒绝，与父rear-short同6/8无任务收益。原80、额外56、prior8/height8/micro8/diagonal8、全部10实际图审绑定与9740命令/19480双肘控制tick齐；min实际gap3.588mm。原KKT1e-6共4条24帧败（后盒1、前盒21、后袋1、容易840005袋1），max1.38897125e-6，未豁免。
- UNLOADED_WRIST_RECURSIVE_DWELL_SCREEN：4实录状态×prior开关×3响应=24条60步递推；首J/error与实际约2.1e-7/1.25e-7一致。延长原腕prior晚袋仍偏离.25–.26rad，有bias末端残差9–15mm，不作统一改法。
- RECONTACT_POSE_REGION_SCREEN：真实最低顶点在core内缩10mm/高6–7mm；释放旧normal只作为无载重选pose假设，保持原界/肘/hand-other；4状态×有无腕目标8静态端点/理想插值过，带固定局部bias直接追踪失败。RECONTACT_POSE_TRACKING_SCREEN在同一双手对双物体10mm直接几何检查下比较：8无补偿未完成、8补偿完成，仅模型内验证；腕目标4条59/178/77/141ticks，晚期成本高，不能当物理证明。
- 已实现staged_recontact_pose_probe/recontact_tracking.py：默认禁用、选中后排/重接触/top_cross/实测load0滤波<=.05才提议；仅current/previousq/previouscommand估计bias，原界/实测步长/.055slew与命令+预测几何复核，失败不返回新命令，无normal重置或loaded改动。check_recontact_tracking_probe真实4起点×2端点8递推共643命令、每条8拒绝门case，直接公式比对<2e-6。此计数按报告汇总；首次文档手填641的断言被643实数拦截，未改报告。尚未整理端点planner模块、接线collector/lifecycle或独立normal-reset审核，**未冻结、未物理**。
- RECONTACT_POSE_PLAN.md已写接线合同：卸载后才释放旧normal，实际到达真实点后重捕获measured参考/normal回原按压；原guard优先、对象动则重规划、loaded不可无载下发；实际调用/动作链/guard/normal捕获独立检查过后才冻结同8+2，不能直接下发静态端点。precision另候选不混入。接续此原型向真实闭环推进，不再重复只腕微调。原四族12fresh/splits→合格RGB11D共享训练→未调参192push3wait多seed实际h10全目标保持。

以下为历史记录，以本段为准。

## 2026-10-01T07:27:06.289813+00:00 无载腕偏好困难4完成2/4；真实COP贴边与可达性筛查已补齐，完整批继续

- 上一分拣goal turn progress，本轮progress；中间Git备份侧任务已完成。goal active，0新合格组/转换/模型。原全8推2等待继续：runner1983639、collector1995542(case840000)、原controls1983643/额外1983644本轮ps核活。STATUS整case已4条件，另容易盒已完成；不是重启或新物理。142冻结文件hash重核一致（84实际归档启动核验保留）。约58GiB空闲。
- **好**前袋357.957/前盒284.614mm原任务姿态过，已实际8RGB4外视绑定；容易840000盒150.208mm过并图审。**差**后盒124.420mm/末signedY6.357，后袋232.855mm/137.965仍失败，失载11/12不减；四困难非目标XY0。后盒1、前盒21、后袋1帧原KKT1e-6失败保留。当前原50调用全过、extra28有25过3数值失败；不能说全审计通过。
- 新UNLOADED_WRIST_EXECUTION_EFFECT/OUTCOME/POSTURE诊断更新四困难；后盒26/后袋25实际应用，下一q回中17/8次，不能把同状态反事实命令回调当整轨迹收益。首次应用前已出现跨run差异，不作3mm因果结论。
- 新diagnose_unloaded_wrist_contact_exit及UNLOADED_WRIST_CONTACT_EXIT_DIAGNOSIS：后盒15bout有12初始COP贴3mm边、11失载全部末COP贴X边（中位.023mm）；后袋12初始均不贴边，但9/12末贴X边，需区分机制。handover后物体局部选点保持不变。载荷对齐packet(t-1)到t，真实core，不是虚拟点/周期冲量。
- 三新只读screen：REAR_CENTERED_PHYSICAL_CONTACT_SCREEN(真实最低顶点、4状态×2normal，中心0/8达到2mm)；REAR_INWARD_PHYSICAL_CONTACT_SCREEN(原normal，5/10/15mm，6/12落点+抽样线性关节路径过，晚盒5mm仍差4.56mm)；REAR_FREE_INACTIVE_CONTACT_SCREEN取消非工作掌位置锚，保持其整手>.84/两包裹顶<.82及原界/肘，四中心残差未改善。局部优化失败不证明全局不可达；所有静态/抽样path不算全身/动力学/训练准入。脚本运行均已退出，无第二物理/训练。
- 详见unloaded_wrist_prior_groups_r1/CONTACT_FINDING_PARTIAL.md、更新UNLOADED_WRIST_PRIOR_PROGRESS/PARTIAL_PROGRESS；五条实际图审已完成并绑定。下一接续全批80/56/10图审和原closer；不扩采腕微调失败版，需真实落点+无载姿态重规划递推验证，独立precision候选未混入。原四族12fresh/splits→合格RGB11D共享训练→未调参192push3wait、多seed实际h10全目标保持。

以下为历史记录，以本段为准。

## 2026-10-01T07:01:29.690475+00:00 无载腕偏好独立审核/真实context完成，原全8推2等待已冻结并实际启动

- 上轮/本轮均progress，goal active，0新合格整组/转换/模型。唯一物理unloaded_wrist_prior_groups_r1，runner1983639/collector1983642/原controls1983643/新extra1983644本轮proc核活；首840001后盒已有真实RESET和PROGRESS。协议SHAadd25186439f12a5082591a1eac16b707d481c013e5c2ea50ed76d1ca01aae17，实际84来源逐个对协议核齐。staged_unloaded_wrist_prior、协议/runner/审计全部冻结，勿改、勿重跑prepare或并行第二物理。
- 新真实context记录手xyz/rotation与minZ；audit_unloaded_wrist_prior_live不导入候选helper/solver/geometry，独立URDF FK、掌参考/法向一致性、全手最低点、启用条件/float32 prior/候选高度和回退复核。实际collector context与coordination AST共9592输入，8真实CLI正例/10字段篡改拒绝、54候选通过；均/tmp反事实夹具，候选不传递到下一状态，不当物理数据。
- 新audit_unloaded_wrist_task_optimality保持原非线性KKT数学AST/阈值1e-6，仅先独立验证新prior；8夹具完整审核仍原3条22帧败，未豁免。audit_unloaded_wrist_loaded_execution保持原数学AST，仅collector版本绑定更新；后盒140/后袋314原加载推动完整复算过。新watch56调用含prior+原区域/XY/斜向+loaded+KKT；原80controls保持。close_unloaded_wrist_prior_full已预备，10全图审后才关闭。
- **上线前拦截**新增attempted_solver_trace初共享meta导致循环JSON引用，独立检查抓到，已改deepcopy并全回放/CLI重过；首次task_error篡改测试保留Python共享list而非落盘JSON，改JSON往返后10拒绝齐。旧失败日志保留。启动源码检查曾误查不存在args.push_assist，未把缺字段当通过；84源已独立核验，无助推以完成时raw collect_meta和原审核核。
- 父rear-short已完整关闭6/8+2wait，左右/斜向各3/4，差后盒121.454/后袋234.174未入区，好前袋357.853/前盒284.475；原源码版本拒绝8日志+独立补审8完整保留，0整组。当前新动作只无载后侧恢复偏好，原normal/loaded/界不改，精度修正未混入。
- 下一接续同句柄完整8+2，核原80/新56/height8/micro8/diagonal8和10实际图审；比较两后侧持续接触与任务终点，不能以启动/单步成功替代。原四族12fresh配对组/splits→仅合格RGB11D共享训练→未调参192push3wait、多seed实际h10/画面全目标保持。

以下为历史记录，以本段为准。

## 2026-10-01T06:45:39.055881+00:00 后排短恢复完整6/8+2等待已关闭；无载腕偏好新候选接线与9592帧回放通过，未物理

- 上轮/本轮均progress，goal active；0新合格整组/转换/模型。rear_short_recovery_groups_r1完整关闭，左右3/4、斜向3/4、困难2/4，两组拒绝；RESULT.json/RESULT.md/CAUSE_REPORT完整，PARTIAL已指向终稿。旧runner1944896/原controls1944899/extras1944900/末collector1969112/补审1964785本轮核实退出，**当前没有物理/训练进程**，不是后台仍在图审。
- **好**前袋357.853mm/末Y204.468、前盒284.475、四容易与2wait原门过；八推非目标XY0。**差**后盒121.454/后袋234.174mm未到区，失载增加，短恢复不能单独解决。原80/额外48+8height/8micro/8diagonal+8独立补审/全10实际抽帧绑定完成；9740命令/19480双肘tick采样/min3.452mm，非全身substep证。额外KKT3条22帧失败(盒1/前盒20/袋1，max1.3474386e-6)，不豁免；原8源码版本拒绝日志保留并绑定独立补审，v2closer关闭。
- **无载姿态对照**新UNLOADED_WRIST_POSTURE_SCREEN和ORIGINAL_NORMAL_SCREEN，4实录8状态每种16静态解；原锚点保留时6/8有正向回调且插值过、释放仅4/8（短恢复低高度路径下探），不是取消normal的充分理由。原袋末保持normal可能腕反而更偏，不能宣称普遍可回中；未全身/接触/递推验证。
- **新staged_unloaded_wrist_prior** 父rear-short，默认关--unloaded-wrist-prior，只后侧已重接触top_lift/cross、实测load0/滤波0..05N、全手minZ≥.84时把原腕prior0改clip(-.15*q,±.04)。原位置/normal/阻尼/界、loaded保持；候选nominal手高不足或求解失败回退原完整命令及原task_inputs。8实录9592帧仅54候选（后盒28/后袋26）全部原命令/几何/高度过、腕较父减小，原活动手残差增幅最多.150mm。不是递推物理，不能直接入库/下发。首次筛查遇pre-top无contact_load中止，明确此类mode不适用后v2完整通过，旧日志保留。
- **已验接线** collector/coordination默认关AST精确等价、12实际CLI、21helper门、实际归档开关；接线版coordinator实际AST分支全9592默认关/54候选+2fallback测试过。UNLOADED_WRIST_PRIOR_PROGRESS来源已绑定，stage未冻结、未启动。**剩余**实际collector context提取与真实全手高度来源、独立eligibility/prior/KKT与版本绑定loaded审核及负例完成后才冻结原全8+2；原KKT审计只认waist prior，需要新增明确审核而非放宽门。precision候选独立、不混此变更。
- 原四族12fresh完整配对组/splits→仅合格组RGB11D共享训练→未调参192push3wait、多seed实际h10与画面目标保持，不以诊断闭环或单步探针替代终点。

以下为历史记录，以本段为准。

## 2026-10-01T06:25:58.615845+00:00 后袋短恢复234.174mm仍失败；纠正额外审核源码版本不匹配，新增独立补审

- 上个分拣goal turn progress，本轮progress；0新合格完整组/转换/模型，goal active。当前原全8+2已完成7条件、case840005采集中；runner1944896/collector1963395与原controls1944899/extras1944900、新补审1964785本轮proc核活。无重启/无第二物理。
- **差**后袋234.174mm（父217.975），末Y139.284mm未到原200mm；恢复742→671帧、加载215→272，但失载7→12。后盒121.454mm仍失败；前袋/前盒原任务过，四困难2/4。后袋8RGB4外视实际看并绑定：513后目标/工作左手画外；各非目标XY0，支撑直立过，不等于可学性证明。新增两容易840000已原任务/姿态与实际图审绑定。
- **重要更正**前交接将已执行额外审核近似描述为已通过不准确：audit_micro_unchanged_loaded_execution.py硬校验collector==micro，rear-short版已变文件，因此现有全部6条在源码断言处退出1。不改冻结旧审计/原日志；新增audit_rear_short_unchanged_loaded_execution.py只更正collector绑定并新增原协议/冻结源/height/默认关AST证据链，原数学AST完全一致，1正7负检查过；现6条补审均通过。原数值KKT失败仍保留。新watch_rear_short_supplemental_audits.py继续余2；最终须close_rear_short_recovery_full_v2.py，旧v1不支持此次补充证据，勿偷偷修改。
- **新单步姿态证据**REAR_WRIST_NULLSPACE_SCREEN四实录41bout，原任务预测值/实测及previous动作界/双肘5mm保持时有小幅腕回调余量，早期约.037–.038rad；后盒末bout几乎0。非线性材料点变化最大.436mm，未证明稳定接触/递推路径，秩对浮点敏感，不当物理候选或入库数据。后袋新末腕−1.252rad，手朝向+32.535°/袋yaw−73.388°，姿态与旋转/失载相关但非单因果。
- 下一完成全批10/80原48额外+8补审/10实际图审并保留所有失败；据此选择后排接触/无载姿态改进，精度候选已单独接线但尚无物理验证。原四族12fresh/splits→仅合格完整组RGB11D共享训练→未调参192push3wait、多seed实际h10/画面目标保持。

以下为历史记录，以本段为准。

## 2026-10-01T06:09:45.883026+00:00 后排短恢复首盒121.454mm仍失败；前袋/前盒保持过；独立精度候选已接线

- 上轮/本轮progress，goal active，0新合格整组/转换/模型。rear_short_recovery_groups_r1首840001完整1/2（盒败、前袋过），两条独立height/geometry和实际8RGB4外视绑定；原控制/额外审核首对完成，KKT后盒1帧败/前袋过。840004前盒原任务/姿态284.475mm过并实际图审绑定，同case后袋采集中，不能称整批过。
- **差后盒**121.454mm vs父117.495，仍未到区，非目标XY0。恢复817→775帧，重接触8→14（失载4→11），有效加载94→118，晚期每次推进仅约.2mm。SHORT_RECOVERY_OUTCOME_DIAGNOSIS整段统计，不用单次恢复更短替代接触成功。**好前袋**357.853mm/末Y204.468原门过，视觉末段手抬离、袋盒稳定，未明显退化。两后绕可观察性风险继续。
- **新姿态证据** REAR_POSTURE_DRIFT_DIAGNOSIS：后盒首→末push腕.172→1.941rad、腰约.98，手朝向−17.453°/盒yaw+37.865°、X参考误差3.46→10.37mm；旧micro袋手+27.247°/物体−64.896°但无同类绝对限位。仅观察相关，不宣称单因果；已回看旧REAR_CONTACT_AUTHORITY_FINDING和WAIST_BOUND_TRADEOFF，扩腰袋无单步收益、盒收益有限，不重复盲扩。
- **staged_task_ik_precision新隔离接线**以已关闭micro为基线，默认关--precise-clearance-task-ik，仅新task_ik_precision.py ftol1e-11→1e-13，原目标/normal/150步/float32/界/KKT1e-6保持。collector与coordination关闭AST逐值等价、9参数、实际solver/归档分支过；16完整实录434几何覆盖54失败→0，来源绑定于RECORDED_TASK_REPLAY；未冻结/未物理、不混入当前height。初AST抓到归档新if误包原USD层行，已上线前修正并重新精确通过；不是放宽检查。TASK_IK_PRECISION_PROGRESS已记录。
- **唯一物理句柄** runner1944896/controls1944899/extras1944900/collector1950690本轮/proc核活，current840004、已完成2条件，同原全8+2继续。冻结rear stage/protocol/runner/审计不改；旧首collector1944901已退出，属正常进入下一case，未重启任务。
- 下一先看新后袋接触/进展与全批审核，齐10/80原48额外/8height+8micro+8diagonal/10图审后close_rear_short_recovery_full.py；再确定接触基线并独立物理验证精度修正。仍保留原四族12fresh整组与split→合格整组共享RGB11D训练→未调参192push3wait、多seed实际h10/画面；禁止失败入库或用容易任务/启动成功缩小终点。

以下为历史记录，以本段为准。

## 2026-10-01T05:55:24.582801+00:00 micro全8推2等待6/8关闭；后排短恢复已全批实际启动；IK精度离线54失败→0

- 上轮/本轮均progress；目标active，0新合格组/转换/模型。本轮补完余6实际图审，micro_clearance_groups_r1完整关闭：6/8+2wait，左右3/4/斜向3/4、困难2/4，两组拒绝。RESULT.md/json与CAUSE/进度已同步，原四族12fresh/splits→合格整组RGB11D训练→未调参192push3wait多seed实际h10/画面，范围不缩小。
- **好**前袋357.974mm/末Y204.589、恢复669→450、5次小修正保接触，前盒283.971mm过；四容易和两wait过，八推非目标XY0。**差**后盒117.495/后袋217.975仍失败；后排工作手/目标大部分RGB画外。原80控制/额外48/8micro+8diagonal、9740命令/19480双肘采样、全10抽帧绑定齐，minactualgap3.512335mm。额外KKT完整4轨迹16帧失败（难后盒1/前盒13/后袋1/容易840005袋1），max1.2749143e-6；门未放宽。不是模型h10或全身/substep证明。
- **rear短恢复独立审核已补齐** audit_rear_short_recovery_live.py不导入controller，首.91/再次.86/撤手≥.91与source/实际expert映射；4原版+候选完整流、真实CLI4正10负、2前排不适用通过。初版把跨越进入高度错当全跨越每帧高度，原版485被拒；修进入时序不改阈值，失败日志保留，v2过。check_rear_short_recovery_live_entry.py用/tmp反事实夹具，不当物理数据。
- **唯一新物理** rear_short_recovery_groups_r1，runner1944896/controls1944899/extras1944900/collector1944901本轮/proc实核活；当前840001后盒，真实RESET/PROGRESS到rear_push已出。原布局/seed/1200push70wait/顺序完整8+2，只加--rear-short-recovery，协议SHA8c132299bdc150a90015f2333daa07c72a57406ebdad256c67f33786d286ea45；实际82源逐个对冻结协议核齐。staged_rear_short_recovery/协议/runner/审计已冻结，勿改/勿重跑prepare/勿并行第二物理。旧runner1918462/controls1918467/extras1918468/末collector1942805已核退出。先前close仍计算时prepare被缺RESULT门拒绝、未建目录，等同句柄成功后才冻结/启动，无抢跑。
- **后排边缘诊断** CURRENT_REAR_BOUT_CONTACT_GEOMETRY记录每bout首末COP：后盒后期X边距约2mm→0；后袋后期X约10–14mm→0–2mm。真实恢复817/742帧，但推进收益衰减，不假设短恢复独自解决滑移。REAR_TASK_COMPETITION放松非工作手的单步残差收益小，不支持直接改此任务；盒边界与袋不相同。
- **隔离精度探针** staged_task_ik_precision_probe只有task_ik.py ftol1e-11→1e-13，其余原目标/导数/150步/float32/界/KKT1e-6保持。两个已关闭版全16推434几何覆盖，原54失败→0；max新KKT1.2486183e-7、max指令差.000472449rad、max47迭代。screen_task_ik_precision.py与RESULT来源绑定，未collector接线/物理，**不混入当前单变量高度对照**。
- 下一追同新句柄完成全部条件、原80/额外48与新增8height+8micro+8diagonal/10图审，然后close_rear_short_recovery_full.py；保留所有失败。之后依据后排真实收益/接触与精度单独验证决定下一实现，不用容易样本或启动成功替代全目标。存储当前约63GiB可用。

以下为历史记录，以本段为准。

## 2026-10-01T05:36:28.230108+00:00 保接触版四困难2/4：前袋首次过原终点；后排恢复与任务竞争诊断，短恢复已隔离接线

- 上一分拣goal turn progress，本轮progress；完整目标active，0新合格整组/转换/模型。本轮4实际图审均绑定，FIRST_FOUR_RESULT.md/json进度已更新，当前全批仍未关闭。
- **好**前袋357.974mm、末Y204.589mm，原质量+支撑直立过；实际5次返回保接触，恢复669→450帧、top_push406→437，1012开始release。前盒283.971mm过，四非目标XY均0。困难由1/4→2/4，不冒充全8。
- **差**后盒117.495mm/后袋217.975mm仍未到区，后排RGB目标/工作手多数画外；当前原40控制/24额外调用已完成，额外KKT3轨迹15帧失败（盒1、前盒13、后袋1），前袋该项过；不放宽原门、不入库。四条原几何和独立micro/diagonal已过、8RGB4外视实际看并绑定。
- **新原因证据** CURRENT_RECOVERY_BUDGET全6实录无恢复重叠；本版后盒817恢复帧（4tilt397+4lost420），后袋742（7lost）；后排真实恢复.91m、实际支持点约.89，前排.86。各次推进后期衰减，短恢复不保证解决滑移。REAR_TASK_COMPETITION_DIAGNOSIS4实录：仅离线删另一手3位置任务行、保留bounds/normal/双肘，工作手残差改善很小；盒腰/右腕边界活跃，袋无绝对界，不据此改另一臂或宣称全局不可达。
- **staged_rear_short_recovery** 新隔离采集器默认关--rear-short-recovery，仅rear region设置recontact_travel_z=.86，其余helpers逐字父micro一致。默认关AST等价/12参数分支/后排限定过；4完整实录4796帧原版匹配、20保护刺激、1285改变参考一步IK/独立双肘与非目标手间距过；水平跨越全手高度余量至少44mm。接线版RECORDED_INPUT_REPLAY/TASK_IK_SCREEN有来源绑定；**未冻结/未启动物理，未完成新live高度审核/负例**。不改当前冻结stage或协议。
- **唯一物理** micro_clearance_groups_r1 runner1918462/controls1918467/extras1918468/collector1930280本轮/proc实核活，当前840000，已完成条件4。源82/原协议不变，不重启不并行第二采集。余正常/交换和2wait照原全8+2继续；齐10图审/80原/48额外后用close_micro_clearance_full.py关闭。
- 下一完成当前全批、独立rear恢复高度/source审核与拒绝样本后，才冻结新完整对照。原四族12fresh整组+split→合格整组RGB11D共享训练→未调参192push3wait多seed实际h10/画面，范围不缩小。

以下为历史记录，以本段为准。

## 2026-10-01T05:15:01.532422+00:00 斜向入口完整5/8关闭；小修正返回保接触同原全批已实际启动

- 上轮/本轮均progress。本轮余8实际图审完成并关闭front_diagonal_entry_groups_r1完整8push2wait：5/8+2wait，左右2/4、斜向3/4、困难1/4，两组拒绝；0新合格组/转换/模型，goal active。
- **好/差**：前袋38.879→340.651mm，初段yaw−2.048°、无桌沿guard，但末Y187.266mm还差12.734mm；13次重接触恢复669帧，其中11次方向切换552。前盒284.163mm过；后盒114.623/后袋215.443mm仍未入区。四容易与两等待过，不以总分掩盖困难失败。RESULT.md/json、CAUSE、FIRST_PAIR_CAUSE及进度/coverage已同步。
- **完整质量**：80原控制、48额外调用、8方向+8斜向独立复算、9740命令/19480双肘tick采样通过，最小实际gap3.446mm；非全身/substep证明。额外IK最优性4困难轨迹38帧失败，max1.304900e-6，原1e-6不放宽。全10抽帧实际看并绑定；后绕画外、前侧遮挡/裁切仍保留。旧runner1892113/controls1892118/extras1892119/末collector1910588已实查退出。
- **新micro候选**只曾lateral→front小修正后的front→lateral返回，整个修正最大偏移≤5mm、当前实测COP距core边≥10mm、normal≥.3N且原restart条件成立时保留接触；首大转向、失载、tilt/终止/桌沿/其他物体/手间距保持。观察筛查袋5次/盒2次，229/82恢复帧仅观察开销不是可实现省帧。全有载点袋最小26.275mm、盒10.220mm，无将来patch保证。
- staged_micro_clearance_probe未物理；**staged_micro_clearance_return已独立接线**。实际collector默认关AST等价/9参数分支/2类选择通过；接线版2完整流2398帧关等价+真实输入复算/9原保护/6篡改拒绝，13历史接触拒绝检查；真实CLI1正8负通过；全部54改变参考一步IK/独立几何过，原9行位置+法向任务保持。这些不是物理成功。初回放失败：原接触摘要有>.05N采样即valid，不能误当总力≥.3；另实时.tolist用Python标量而离线npfloat32运算差4.4e-7N，修离线float64匹配实路径，容差未放宽。失败日志micro_clearance_replay[_v2/_v3]保留，v4和接线版通过。
- **当前唯一物理micro_clearance_groups_r1** runner1918462/controls1918467/extras1918468/collector1918466实际/proc核活，首840001后盒；原8push2wait/layout/seed/1200+70/顺序保持，仅加--front-micro-repair-retention。协议SHAf9758e6e9db6cf2dc77e1631e3120981d46fababf107db2c19e175caf277f4e0；实际启动后82源逐个对协议核齐，真实RESET/PROGRESS已出。禁止改stage/protocol/审计或重跑prepare。新MICRO_CLEARANCE_RETURN_LIVE_AUDIT替代旧无例外方向重启审计，原斜向/COP等复算保持；原80/额外48仍跑，KKT失败未豁免。
- 下一接续同句柄全批，重点前袋保接触是否真正节省恢复且达到原终点、前盒无退化；补全原控制/几何/最优性与图审。后绕两困难/可观察性仍需独立解决，可先核实其真实恢复高度/耗时与接触滑动，不盲调PD或重复虚拟点替换。完整四族12fresh整组+split→合格组共享RGB11D训练→未调参192push3wait多seed实际h10/实际画面，全范围不缩小。

以下为历史记录，以本段为准。

## 2026-10-01T04:44:39.729970+00:00 斜向首前袋340.651mm明显改善但末端差12.734mm；首对原任务0/2，完整批次继续

- 本轮progress。front_diagonal_entry_groups_r1首840001两条完整审核和实际图审；后盒114.623mm失败，前袋38.879→340.651mm仍因末Y187.266mm未过原200mm失败。两条非目标XY0、支撑upright过；2400命令/4800双肘采样过，最小gap盒4.336/袋11.295mm。20原控制/12额外调用、2斜向/2换向复算过；额外IK最优性两条3帧失败，max1.207603e-6，未放宽。0合格组/转换/新模型，goal active。
- **好**前袋125→203斜向入口X−93.473/Y+118.110mm、yaw−2.048°，无桌边guard（父533停止）。**差**后段yaw至31.323°包络增宽，11次方向切换占552恢复帧，加2失载117，共669；top_push406，最后1195重新press已无足够步数。DIAGONAL_RECONTACT_BUDGET绑定实际事件，不将事后删帧当可实现新轨迹，不放宽步数/终点。
- 首对8RGB4外视已实际看绑定；后盒/工作手多数画外，前袋后半遮挡/裁切；不是完整连续画面/模型成功。当前CAUSE/PARTIAL/FRONT_DIAGONAL_ENTRY_PROGRESS已更新。
- **唯一物理同原完整8+2** runner1892113、controls1892118、extras1892119、collector1897961实际/proc核活，当前840004前盒。首真实79来源已逐个对冻结协议核验。勿改stage/protocol/审计或重跑prepare，不并行第二物理/训练。
- 新CURRENT_REAR_TRACTION_DIAGNOSIS/FINDING：父+新四完整后绕材料点和力包复算。新后盒/袋名义虚拟材料差中位.122/.105mm，命令到下一实测材料点距离9.182/9.541mm，实际前向相对滑动.974/1.151mm；未证明单一摩擦/PD/数值原因，不盲目换参考点或调增益。带载0几何IK覆盖。该诊断与前袋恢复耗时分开，后绕仍待解决。
- 下一完成本批前盒/后袋及四容易/两等待全组证据，再评估在原物距/桌沿下减少切换与恢复开销；任何新候选尚未接线。原四族12fresh/split→合格完整组RGB11D共享训练→未调参192push3wait多seed实际h10/实际图审目标不缩小。

以下为历史记录，以本段为准。

## 2026-10-01T04:30:51.508936+00:00 换向重接触完整5/8关闭；斜向入口完整同条件物理已启动

- 上轮Git备份支线progress；本轮主线progress：补齐余6实际图审、完整8推2wait关闭、斜向候选接线/独立LP复算/动作筛查/冻结后真实启动。goal active，0新合格组/转换/模型，全范围不缩小。
- **好/差**：front_direction_recontact_groups_r1原任务5/8+2wait、左右2/4/斜向3/4/困难1/4，两组拒绝；前袋22.718→38.879mm仍失败，前盒283.561过，后盒119.134/后袋218.054未入区。原80控制、48额外、8换向审核和9740命令/19480双肘采样核齐；额外IK最优性5条25帧失败(max1.593356e-6)，门未改。全10实际抽帧绑定，视野风险保持。RESULT.md/json和CAUSE_REPORT.md已关闭。
- 新前袋426卸载重接触/479恢复/533桌边保护；侧向力臂35.467→6.526mm，但先期frontX已转−27.64°/X−113.35mm。实际物理力与材料点诊断已绑定；非全步冲量/因果证明。未走新分支后盒同配置仍不逐位复现，已留UNCHANGED_REAR_REPEATABILITY，不把小差归因于前侧flag。
- **新staged_front_diagonal_entry** 默认关仅front带载入口近角点+耦合COP XY；原guard/方向重接触/关节/首零无助推不改。120几何LP、120实际方向edgeLP先筛；实际采集器AST关等价/8参数分支/两类选择/前侧嵌套通过，接线版4流4796帧默认关重建+独立LP路径/真实力包COP/actualray/XY命令复算+9保护+6篡改拒绝，493录制状态单步IK均可行。这些不是物理成功。最初纯轴edge假设已于接线前修正，旧报告明确保留PRE_DIAGONAL_EDGE。不得改冻结目录/重跑prepare。
- **唯一当前物理 front_diagonal_entry_groups_r1** runner1892113/controls1892118/extras1892119/collector1892117实际/proc核活，case840001后盒；原8push2wait/layout/seed/1200+70/顺序未改，只加--front-diagonal-entry。协议SHA88bc7aca59278c11412f5dff05bb9bd308d8e20159ca80d079e01753adbb6bd5。已有真实RESET与Newton捕图日志，非只锁文件。原controls等STATUS出现后才启动避免上轮启动竞争。新独立斜向audit替代只适用原轴的edge复算；其余原审计保持，KKT失败不豁免。
- 下一接续真实句柄完成全批，关注前袋初期旋转/实际力线/保护、前盒有无退化；后绕接触持续/视野仍需解决。原四族12fresh整组+split→合格组共享RGB11D训练→未调参192push3wait多seed实际h10/实际图审不缩小。最新FRONT_DIRECTION_RECONTACT_PROGRESS/FRONT_DIAGONAL_ENTRY_PROGRESS与coverage同步。

以下为历史记录，以本段为准。

## 2026-10-01T03:43:56.706172+00:00 双肘完整5/8关闭；换方向重接触原全8+2新物理正在运行

- 本轮progress：原self_clearance_groups_r1完整8推2wait结束，runner1827091/collector1855220/controls1842457已退出；RESULT.md/json及CAUSE_REPORT.md关闭。左右2/4、斜向3/4、困难1/4；5/8与父同分，两组拒收，0新合格组/转换/模型，goal active。
- **好**：前盒283.350mm原门过且2400实测双肘几何采样过/min4.870mm；原同例旧q+当前USD1047相交。新全批9740命令/19480prepost几何过、min3.588mm，仅肘躯干/控制tick，不是全身或substep证。80原控制+40额外区域/连续性/参考/适用最终执行通过；8推动各8RGB4外视+2wait各8RGB已实际查看绑定。冻结源未改，初零/无助推保持。
- **差**：前袋175.843→22.718mm，后盒130.261→124.247mm，后袋217.629→218.116mm仍未到区。新袋旋转压缩质心通道55.249→11.065→5.742mm；429–457共29帧侧向有载、实际材料点与物体X全前移，26名义X已后退且该段0避碰IK覆盖；COP换到局部负X侧、29τz全负，458桌边5mm保护后742guardlift。FRONT_BAG_MOTION_CAUSE/FRONT_BAG_CORRIDOR_RESULT绑定，末tick力非积分因果证明。后绕目标/工作手大量画外，RGB可学性仍待解决。
- **额外审核未过**：4困难IK最优性215帧超过原新增1e-6，max1.473276e-6；每条最差帧5差分尺度仍失败。可行性另过；未放宽/未解决/非前袋因果证明。TASK_OPTIMALITY_BATCH及GRADIENT_SENSITIVITY。首次敏感性报告sha(str)异常修Path后完整重跑，旧日志保留。
- 新staged_front_direction_recontact只front带载top_push路线切换时调用原recontact、重置接触/COP；原桌沿/其他物体/手间距优先、终止/tilt优先、默认关。实际collector AST默认关逐值等、7参数分支/2类选择/前侧嵌套过；四全历史4796帧默认关重建、启用分支+9保护过；独立触发/力复算与6篡改拒绝过。不代表实际改善。
- 已冻结并实际运行 **front_direction_recontact_groups_r1** 原8推2wait同布局/seed/顺序/horizon，仅加flag；原几何/IK/质量门不改。当前runner1862361、collector1862370（840001后盒）及controls1863783均实查存活。最初controls1862362因STATUS尚未写入退出，0rows保留CONTROL_EVIDENCE_STARTUP_RACE；仅重启同审核器，物理未重启。协议与stage勿改/勿重复prepare。新runner还逐条独立DIRECTION_RECONTACT_LIVE_AUDIT，原控制watcher同步。额外IK失败未解决，明确诊断而非训练准入。
- 下一：接续真实句柄全批，尤其前袋与前盒换向接触/旋转是否改善且无退化；补齐本批原全部控制、source/final-action/独立最优性和实际图审。后绕接触持续/视野及IK精度独立保留。原四族12fresh整组+split→合格组RGB11D共享策略→未调参192push3wait多seed真实h10/实际图审目标不缩小。详情FRONT_DIRECTION_RECONTACT_PROGRESS.json。

以下为历史记录，以本段为准。

## 2026-10-01T02:54:08.357415+00:00 双肘约束已接隔离专家；真实等待通过，原全8推2wait运行中

- 本轮progress，Git授权核验仅支线。goal active；0新合格组/转换/模型。新staged_self_clearance_task_ik已接直接任务IK，最终region/hold/rear覆盖后门及pre/post实际body几何。默认关64逐值同、启用64、80坐标/故障检查；独立真实wait正例+8篡改拒绝。初零/原限位/步长/无助推/原门不变。
- 真实self_clearance_runtime_preflight_r1原70wait：原门过、手漂移2.098mm、动作0、140实测检查过、最小83轴gap31.973mm，12格policy及外视0/65实际看。runner退出hash str类型异常曾遗留running，已核/proc退出+66源不变并明确关闭异常，collector正常；不是task/model改善。
- 当前实际mask完整归档：准确几何碰撞体left92/right95/torso97两对明确filtered且不在precomputedcontactpairs；不是历史mask证明。USD9层/上游/相机/embodiment/model来源及真实K已补档。仅双肘躯干，不宣称全臂安全。
- **首交换840001两条已完整0/2**：盒124.247225mm、袋22.717610mm（父130.261106/175.842965），另一物体XY0；两条全1200命令/2400实测几何过。盒9修正/min实际gap4.335562mm；袋365修正363贴工作左肘5mm、右0，min实际3.793834mm。袋X−119.894mm，458桌边5mm保护后742guardlift；原历史相交均工作臂，非工作锚假设未获支持。盒107loaded原执行/26refinement/0fallback/KKT2.68e−8新增受限审核过（只支持loaded未改IK）；两条12格policy+各2外视实际看，原完整控制/额外图审pending。当前840004继续，runner1827091、collector1832917实际存活，PARTIAL_PROGRESS更新。
- 唯一完整物理self_clearance_groups_r1，原8推2wait顺序/seed/布局/1200+70保持。冻结协议/source，禁止改stage/重跑prepare。当前首840001后盒进行中，接触重试/目标画外风险仍在。真实句柄及进度见SELF_CLEARANCE_INTEGRATION_PROGRESS，需重新核/proc后继续。
- 新runner仅接独立几何/最终动作链审计及原wait；原contact/refinement eligibility/stationarity等完整控制及实际图审尚须适配原全项后补，不得冒充全部原审计通过。无解停止该条明确失败，短帧/空帧不捏造，保留同组另一任务及其他原条件。若auditor失败终止runner，先定位，禁止凭状态另启覆盖。
- 详细SELF_CLEARANCE_INTEGRATION_RESULT.md/json，coverage已绑定。原完整基线仍5/8+2wait两组拒绝；原四族12fresh/split→合格整组RGB11D共享策略→独立192push3wait多seed真实h10/实际图审目标不缩小。下一先完整本批证据关闭，再依实际接近/接触/几何/视野修专家。

以下为历史记录，以本段为准。

## 2026-10-01T02:29:21.880241+00:00 双臂避碰全8全帧审核、四运动学对照关闭；直接任务IK809输入检查完成，未接线

- 上轮/本轮均progress。goal active，0新合格组/转换/模型；当前无物理/训练。原joint_edge_retry 5/8+2wait、两组拒绝，RESULT690bbc38...不变。
- **完整数据审核** RECORDED_FULL8_ELBOW_TORSO_CHECK原8×1200=9600实测帧，前袋825/前盒1047仍相交，其余6条该项全帧无发现。SELF_COLLISION_PHASE_AUDIT首次袋308/盒146均top_push，后续接近/释放也出现。仍历史q+当前实际USD的来源限制，非全机器人无碰撞认证。
- **模型** staged_self_clearance_probe三轴保守，零位仅7.8mm，因此初10mm测试失败后共享候选预设5mm（旋转旧10不改/初零不改）；staged_self_clearance_faces_probe改确定性83分离轴，362导数误差<8.33e-11、原LP见证不误放、默认关闭50/零位等待过。正间距可证分离、负值不等于碰撞。
- **4完整重放均非物理** 各8×1200：三轴软前袋中位23.96/max61.83mm、前盒15.51/32.05mm漂移；83轴软前袋26.04/60.18、前盒15.84/29.67；四容易完全不改，后绕仅15/16修正。硬XYZ staged_self_clearance_exact_probe袋首305后890保持、盒1051后149保持，不能用停滞当成功。anticipatory_probe软30mm提前姿态(硬5mm/XYZ不改)袋首477后723保持仍败，盒1089修正0保持；四容易不改、后绕36/38修正0保持。各RESULT已完整关闭，不重跑覆盖目录。
- 静态6姿态×2初值硬位置可行，非连续路径证；FIRST_HOLD_DIAGNOSIS305/306线性可行但原/LP初值非线性端点均真违约，307线性不可行，未接纳失败。REFERENCE_CHANGE_DIAGNOSIS首次参考切换袋约.003mm/盒.024mm，不是主要解释。旧硬投影10故障分支拒绝危险输出。
- **当前准备主线** staged_self_clearance_task_ik_probe/task_ik.py直接原Cartesian J/error+阻尼+先验加双肘几何，不强追旧关节FK；原测量臂.04/腰.015、previous.055、关节/腰界保留。默认关闭809输入逐值等原bounded_damped_step；809实际记录输入723输出(11修正)，所有713当前≥5mm输入通过；96历史不足间距仅10下一指令可行、86None拒绝，无实物/闭环宣称。8故障输入检查通过。尚未collector接线/冻结/新物理。
- 汇总BILATERAL_CLEARANCE_RESULT.md/BILATERAL_CLEARANCE_PROGRESS.json及coverage已更新，绑定全部报告。下一直接任务IK接入隔离专家、默认关，处理region/terminal/rear最终覆盖后实执行动作、实测几何及完整USD/相机/runtime过滤归档；首零/等待/界/异常/独立最终审核后原全8推2wait实物理/图审。不得把专家修正偷偷加到policy评测。后袋接触与视野仍未解决；原四族12fresh/split→合格整组RGB11D训练→独立192push3wait多seed实际h10/图审目标不缩小。

以下为历史记录，以本段为准。

## 2026-10-01T01:56:43.252733+00:00 新数据质量风险：原前侧示范肘—躯干几何相交；旋转路径加整臂约束后运动学过

- 上轮/本轮均progress。本轮真实8流力矩/接触力臂、两版材料点筛查、2旋转衔接、真实USD整臂/LP相交、8流抽查+两流全帧、自碰撞配置/来源/实际画面核查、guarded路径1049复核已做。goal active，0新合格组/转换/模型，无物理/训练。原5/8+2wait两组拒绝，RESULT690bbc38...不改。
- **关键差结果（数据）** 原8流61帧/流抽查后，前袋840001全1200帧825相交(首308)、前盒840004全1200帧1047相交(首146)，最大共同内切球约32.94mm；前盒此前原门成功。LP确证当前实际USD凸体与历史实测q相交，非只AABB疑似；其余六流仅抽查无发现，不作全帧保证。当前g1 cfg enabled_self_collisions=False，本地源与历史归档一致、spawnUSD与检查一致，两历史arm_contacts含字段但无肘躯干力记录。**历史根USD/上游默认/runtime mask未全归档**，不能宣称独立重建历史mask。当前完整资产层SHA现已绑定。
- 前盒REVIEW_EVEN及pre_0180原外视实际看；第一视角躯干画外、外视后侧遮挡，画面不足以确认/否定相交，不称视觉证明。SELF_COLLISION_SOURCE_AUDIT明确来源/图审限制；未启用新物理自碰撞、未改冻结源/门。
- **好/差旋转** 近边57.2mm材料点固定手+盒263站过；近角66.14mm140/263败。近边全臂1049样本592肘躯干疑似，LP115.25站.061mm内球、160站32.945mm确证，拒绝原路径。新rotation_elbow_clearance真实USD躯干坐标AABB分离轴10mm约束→263站全过；独立1049样本所检环境/跨臂/远端躯干对全分离，插值材料误差.039164mm。未检查零位到接触/完整扫掠体/相邻机械结构/动力学，不能直接下发。
- **力学限制** 8实录mu手1桌.55；均压简化预算3N旧10.28mm力臂比.275、近边1.528只是敏感性。新的单点粘着准静态toy模型(24/48积分)预设手80度圆弧→盒近边约45.896度且质心[29.876,-15.257]mm；旧中心仅4.798度、近角50.890度。不等于真实仿真，但不能把预设物体原地转作为已执行控制。
- 汇总SELF_COLLISION_AND_ROTATION_RESULT.md/json及coverage已绑定14报告；全部隔离诊断无collector接线。原全轴几何慢扫中断保留日志，V2合法正分离早返后完整完成，不能误认原扫描完成。当前无后台物理/训练。
- 下一优先共同专家/数据审核的整臂几何与资产/runtime来源；旋转要实际姿态力反馈并处理平移/分段重接触、零位接近退出，再真实物理原全配对组。后袋持续接触仍未解决；原四族12fresh/split→合格整组共享RGB11D训练→独立192push3wait多seed实际h10/画面目标完整保持。

以下为历史记录，以本段为准。

## 2026-10-01T01:33:03.850205+00:00 真实材料接触与旋转前绕联合筛查：几何正向，连续控制未通过

- 上个分拣目标轮progress；Git授权核验支线不计分拣进展。本轮progress：原后绕4状态真实手网格自由朝向筛查两版、原完整8任务12/20mm旋转路线、独立8003角点检查、木盒5站机器人接触视野及两种衔接已执行。goal active，0新合格组/转换/模型，无物理/训练。
- **好** 20mm间距/5mm桌沿保留，困难木盒转65度可前绕但桌沿仅6.73mm；选80度桌沿38.924mm、前侧X0.364195、maxX初始0.585791，避免原深推100.426mm。五站均有真实手材料点/目标中心入画/手部避障静态解。14候选8003角点独立过，旋转还加Lipschitz样本间余量。不是力学/全臂/可执行保证。
- **差/重要拦截** 自由接触点263站衔接在0–80度旋转时q完全不动，因此静态可达不等于推动控制；该自由滑动版92站后失败，不可采用。固定手+盒材料点版本仅31/263接受(0–30度)，31度status8、材料点误差7.294微米、部分dq触.055/视野贴边；未接受失败/放宽门，非全局不可达证据。当前接触力臂10.28mm，力矩未知，不能直接物理下发预设路径。
- **旧位置/袋** 原后绕4状态×3初值×有/无视野两版未找到视野接触可行解，有限支持顶点/局部求解/保守全局桌面平面限制，非不可能证明。袋20mm旋转路径仍无前绕，最优仅转2度rearX.646702，比原.649179少2.48mm；盒方案不代表整组改善。
- 文件 MATERIAL_CONTACT_ROUTE_RESULT.md/json 汇总绑定8报告；脚本screen_material_contact_view[_v2]、screen_rotated_object_routes[_20mm]、check_rotated_route_geometry、screen_rotated_route_contact、check_rotated_route_contact_continuation、check_rotated_route_sticking_continuation。均隔离诊断，无候选接线。原joint_edge_retry RESULT SHA690bbc38...仍5/8+2wait、两组拒绝；冻结源/协议/门未改。
- 下一有力臂接触点/粘滑力学/分段旋转重接触、零位到接触与全臂路径；后袋持续接触仍独立解决。原四族12fresh/split→合格整组共享RGB11D训练→未调参192push3wait多seed实际h10/画面保持。相机相对躯干不改，中心入画只是本筛查条件不是新增硬门。不要将静态对象预设轨迹当真实旋转或新训练数据。

以下为历史记录，以本段为准。

## 2026-10-01T01:13:53.790041+00:00 有限重试完整5/8关闭；数值改善无任务提升；视野/深度路线数据问题已量化

- 上轮/本轮均progress：本轮余6推动/两等待真实图审、全8+2关闭、相机实测位姿/内参诊断、静态接触视野筛查、原rear_push深度代价实测已执行。goal active，0新合格组/转换/模型，不缩小原四族12fresh/split→合格整组共享RGB11D训练→独立192push3wait多seed实际h10/画面目标。
- **完整好/差** joint_edge_retry_groups_r1 5/8+2wait，左右2/4、斜向3/4，困难1/4，两组拒绝。后盒130.261106/前袋175.842965/后袋217.628896mm失败，前盒284.193903过；全部非目标XY0/支撑upright过。后袋父219.069548→217.628896，末10Y124.179624→122.676007，有载215→212/lost7→7；数值回退11→2，11重试/79最终修正，没转化为任务改善。不能再以求解器优化当主要扩采方向。
- **关闭证据** 80原控制、8各reference/execution/front/domain/continuity、355原pushIK、114最终修正/2回退、6case×60归档/10过程、全8推动8RGB4外视+两rear事件/两wait8RGB实际看并绑定。RESULT SHA690bbc38bf3805b3cc2a5440f30d2d636afccc3198a71af860009062089cca9f。runner1750282/末collector1774955/controls1750844/events1750845均退出；目前无物理/训练，goal未暂停。PROTOCOL/stage/旧auditors未改，禁止重跑prepare/freeze。CAUSE已完整重写，中间存WORKING_HISTORY；CLOSED/PARTIAL/coverage同步。
- **质量余量** EXPERT_RELEASE_MARGIN_AUDIT原门复核：四容易推进margin .007665–.345609mm；5成功中4早于已有160mm/205mm内部buffer释放。无新门，也无稳健成功宣称。
- **新视野诊断** diagnose_recorded_camera_frustum.py+summarize_camera_frustum.py实跑父全8+新困难4，14400重建帧/2880实测camera pose/K逐一核验（viewer_observer每5帧）。camera位姿重建误差<2e-6，手FK也核；当前后盒115/115推动目标OBB画外、后袋156/240，容易成功也有大量画外。包围盒入画≠无遮挡；相机相对躯干原标定未改。实际图审一致。报告CAMERA_FRUSTUM_SUMMARY.md/json。
- **更正/内参发现** 首版只查raw误称无相机位姿，后找到viewer_observer已全部重跑；原报告保留*_PRE_RUNTIME_POSE.json。raw默认K[605.500610,605.413574,326.147003,249.571503]，真实K[605.457092,605.457092,320,240]，中心差6.147/9.572px；新诊断用实测K，未放宽相等断言隐藏问题。paired转换和policy输入AST核RGB/state/action/task，不含K；不能归因为模型成绩下降。未来新采集应显式实际K并补相机配置来源，历史npz不改。**oracle专家有worldpose，画外不是其本次物理失败直接原因，而是学生数据可学性风险。**
- **静态接触/视野** screen_camera_contact_postures.py：12后绕状态×两初值×无视野/仅目标/双目标；原URDF界/腰±.98，拟合当前虚拟参考/非工作掌/局部up，非控制器。仅目标盒误差27.7–31.1mm；双目标58.0–63.1mm；袋仅目标早两0/1.708mm、后四21.6–31.2mm。部分q变化1–3rad，不能执行；无全局最优/全臂/连续接触证明。首双物体版存BOTH_ONLY_V1，不能用额外双物体入画要求否定原目标。新报告CAMERA_CONTACT_ROUTE_FINDING.md/json绑定输入来源。
- **原路线深度代价** diagnose_rear_route_depth_cost.py：首top_push前盒+X100.426mm/袋68.862mm（父99.977/68.698），最早2mm移动均显式rear_push（盒61/袋60）；不是末端重试偶发推偏。后绕规划只保物体包围盒间距，不保后续手接触/可达性/视野。前绕候选因原桌沿及包围盒间距被拒；不能静默删困难几何。
- 下一：联合检查接触点/朝向与原绕行路线的可达性、真实碰撞及可观察性，先隔离几何/连续路径，再完整原组物理与实际图审；不再只有solver形式修补，不把静态解直接下发，不直接改相机标定。原首零位、之后双臂腰可动、指定手、非目标15mm、无助推、h10及所有质量门保持。只有合格完整配对组才转换训练，目标仍全范围。

以下为历史记录，以本段为准。

## 2026-10-01T00:41:48.567913+00:00 有限重试首两条均失败，20原控制及实际画面已核；完整原批次继续

- 本轮progress：完整审计入口32项/冻结/启动外，已完成首后盒与前袋真实质量、动作与8RGB4外视审核，后盒事件图及父比较。goal active，0新合格组/转换/模型。
- **坏结果** 后盒130.261106mm（父131.609464），末10最小有向Y12.198305mm；前袋175.842965mm（父179.288432），均未进原目标区。两条非目标最大XY0、支撑/upright过、首11D state/action零、无助推已核。后盒115原pushIK/35最终修正/0回退/0重试过，loaded106→104/lost5→5/tilt4→4。前侧不走新重试，两例均不构成重试改善或退化的因果证据。
- 首两条20原控制、reference/execution/front报告过；ACTUAL_REVIEW_BINDINGS2条。后盒多数RGB目标/工作右手画外，事件0/229/231/232/233/237/292/1199亦实际看；前袋目标可见但掌遮挡/下边缘裁切。保留RGB闭环风险，不能仅凭专家动作合规训练。
- **当前唯一物理** joint_edge_retry_groups_r1，实际/proc核活[1750282, 1756530, 1750844, 1750845]，已进入case840004前盒，随后后袋及全部容易/交换/等待仍保留。新case60真实归档核齐；PROTOCOL add9e9c3.../stage53dce124...冻结不变。当前PARTIAL/CAUSE/coverage已同步，不能重跑prepare/freeze或并行物理。
- 下一完成前盒与尤其后袋的原任务/载荷/重试/最终动作和实际图审，全8+2关闭后再评估同设置重复；盒跟踪、前袋推进和视觉覆盖仍须解决。原四族12fresh/split→合格整组转换共享RGB11D训练→独立192push3wait多seed实际h10/画面全目标不缩小。

以下为历史记录，以本段为准。

## 2026-10-01T00:33:07.250372+00:00 有限重试完整入口审核通过并冻结；原8推2wait物理已启动

- 上轮/本轮均progress。本轮完整auditor CLI3正29负通过、候选冻结、原完整对照实际启动且post-AppLauncher60源码核验。goal active，0新合格组/转换/模型；不是启动即完成。
- **当前唯一物理 joint_edge_retry_groups_r1** runner1750282、首collector1750286、controls1750844、events1750845已实际/proc核活。首840001后盒运行；顺序840001/840004/840000/841000/840005/841002，原8push2wait、原seed/1200+70/布局保持，只新增--rear-joint-edge-analytic-retry。PROTOCOL add9e9c3bf4480af1f8e964368220d522f953d3b9f44eb43a6815c1864826e25，staged_joint_edge_retry MANIFEST53dce124fd4c7eb63194afe15cf5746ea7fbe6b506e6c4e481f805ec4bdc8673。禁止重跑freeze/prepare、改冻结源/审计或并行第二物理。
- 新make_joint_edge_retry_entry_fixtures用当前父joint_edge8实录，两rear+前侧。连续历史新袋23动作变化/84修正/2回退；盒0变化/35修正；只更新代数残差，改变previous的非push入口必须原history相等，物理观测固定/RGB省略。首次生成因前侧没有可选region_approach日志清单错误失败，原失败目录entry_fixtures_incomplete_v1保留；修正清单后完整重跑。
- check_joint_edge_retry_auditor_entry实际32CLI：3正例、29来源/config/原力/父动作/previous/首零/最终KKT/残差/重试状态及跨模式篡改均按预期接受/拒绝。没有放宽原审计。freeze另实际执行collector plan新增AST与fixture配置核齐，绑定全部已有9592默认/连续历史/15失败/59CLI/60归档证据。numeric失败原因未独立复现限制保留。
- 新run_joint_edge_retry_groups、prepare_joint_edge_retry_run、close_joint_edge_retry_group/full、compare_joint_edge_retry_actual已建。prepare已核与父commands除新flag和新目录完全相同；新runner+closure要求retryflag、独立JOINT_EDGE_RETRY_EXECUTION_LIVE_AUDIT，所有原控制/等待/实际图审门保持。compare只准备尚未有新完整真实结果。
- ACTUAL_STARTUP_CHECK已核60真实归档、实际flags/所有冻结依赖/四进程。首次启动核验误把push_assist当CLI字段导致KeyError；该采集器无此CLI，无助推记录在raw.collect_meta，后续原runner/close仍强验assist_frames0/push_assistFalse及q/action首零，未跳过门。
- **首条已完整（2026-10-01T00:38:32.593742+00:00）** 后盒130.261106mm失败（父131.609464），末10最小有向Y12.198305mm；非目标0/支撑upright过、首零/无助推已核。独立115原pushIK/35最终修正/0回退/0重试过；载荷106→104/lost5→5/tilt4→4，handover250→232，未触发重试不可作收益归因。8RGB4外视+事件0/229/231/232/233/237/292/1199已实际查看并绑定，目标/右手多数画外，强化RGB纠偏风险。compare_joint_edge_retry_actual已实跑，首条CAUSE/PARTIAL已写。误调fresh-pilot图审因缺合同退出无产物，改正确review_completed_episode完成，未改门/伪合同。其余7push2wait继续；实际case840001前袋运行。不得把动作通过作为任务成功。父仍5/8+2wait、两组拒绝；盒带载跟踪/前袋推进/视觉遮挡/容易裕量过小仍待解决。下一首后盒真实质量/最终动作审计/8RGB4external和事件图，再后袋数值改善是否带来持续接触和原目标区通过；原全部条件及重复对照保留。四族12fresh/split→合格整组转换共享RGB11D训练→未调参192push3wait、多seed、实际h10/画面全目标不缩小。

以下为历史记录，以本段为准。

## 2026-10-01T00:23:31.953627+00:00 有限失败重试完整离线验证与collector接线；尚未新物理

- Git备份核验不算分拣进展；本轮progress：恢复95753会话确认exit0，补故障注入、真实collector接线、完整挂接/CLI/归档和新审计元数据检查。goal active，0新合格整组/转换/模型。当前无新物理/训练，不是goal暂停。
- **好** 固定历史8条9592默认逐值一致、9452保护不变；只在原有限SLSQP8失败从原LP初值解析导数重试一次，原成功不变，袋11回退→1。连续历史重算359父IK后袋84修正/2回退、12重试，23帧动作变化，剩余438/583显式保父。全物理观测固定，不是物理成功。
- **差/纠正** 全面解析Jacobian在8条中新增7失败(714/835/839/847/968/1093/1097)，不是旧11坏帧筛查所暗示的无回归；约束缩放、等价残差目标、失败点重启未采用。盒带载跟踪偏差/前袋推进/遮挡/容易裕量仍未解决。真实仍joint_edge_groups_r1 5/8+2wait、两组拒绝，RESULT3facc6b7...未改。
- **staged_joint_edge_retry** 从冻结父复制16源码，仅collector/helper/adapter改，其他13不变；新--rear-joint-edge-analytic-retry默认关，依赖原edge开关。原目标/LP初值/限位/.055slew/ftol1e-11/maxiter300/最终float32门保持，最多重试一次。未MANIFEST/未冻结/未物理；probe仍独立保留。
- **实做验证** check_joint_edge_retry_failures15分支；check_joint_edge_retry_hook实际9592帧默认一致、启用逐值对探针、7194前侧排除/16首帧保护、AST去显式新增与父相同。check_joint_edge_retry_prelaunch59非法CLI、默认/启用/原开关兼容、实际60源码归档过。首次CLI缺原runner已有OMNI_KIT_ACCEPT_EULA环境，恢复后过。所有检查/hash见staged_joint_edge_retry/PROGRESS.json及RESULT_SCOPE.md。
- 新audit_joint_edge_retry_execution_live.py保留原独立raw力/parentIK/finalFK/KKT、不导入候选helper，仅新stage绑定和重试配置/trace审核；check_joint_edge_retry_metadata23真实/影子retry记录+11损坏拒绝过。**完整新auditor CLI/来源/记录损坏fixtures尚未做，不能冻结或启动。** 数值失败原因未独立复现限制保留。旧stage/auditor/协议未动。
- 下一先补完整auditor入口正负fixtures，再新freeze/prepare/runner/close和原8推2wait实际对照，关注原成功保持、袋持续载荷/目标区而非只solver次数；盒子跟踪与前袋问题仍须解决。原四族12fresh/split→仅合格完整组转换训练共享RGB11D→未调参192push3wait、多seed、实际h10/画面全目标不缩小。原首零位、之后双臂腰允许、指定手、非目标15mm/无助推/所有原门保持。空间约74GiB。

以下为历史记录，以本段为准。

## 2026-10-01T00:01:45.245404+00:00 关节方向完整5/8关闭；后袋局部改善仍失败；11回退及解析导数筛查完成

- 上轮与本轮均progress。本轮完成剩余6推动/2等待真实图审、全8+2关闭、四实录预测及11数值回退复现/导数筛查。goal active，0新合格完整组/转换/模型。原4族12fresh/split→合格整组转换共享RGB11D训练→独立192push3wait多seed实际h10/画面目标不缩小。
- **完整好/差** joint_edge_groups_r1 5/8+2wait，左右2/4、斜向3/4，两组拒绝；困难仍1/4。前盒283.347353过；后盒131.609464、前袋179.288432、后袋219.069548败。后袋父179.842092→219.069548、末10Y84.952168→124.179624，有载178→215、lost8→7，但未进原200mm区。盒lost4→5/tilt4→4。全部非目标0/支撑姿态过。4容易推进margin仅.023483–.069147mm，5成功全部早于已有内部buffer释放（原门未改），非稳健。
- **关闭证据** 80原控制、8各reference/execution/domain/continuity、359原推动IK完整重放、110最终修正/11回退、6case×60归档、10过程记录、全8推动8RGB4外视+两rear事件/两wait8RGB实际图审已核。RESULT SHA3facc6b7a07557647627ecb3d8ae4755c03456f3813b3c9886a794a163887a97。CAUSE_REPORT/PARTIAL/CLOSED与coverage已更新。runner1706882、末collector1731486、controls1707392、events1707393均退出；目前无物理后台任务，不是goal暂停。冻结PROTOCOL/stage未改。
- **两类机制不同** 后盒35最终修正中32下一实际相对外移>.05mm；关节执行比例不同破坏名义抵消。后袋75修正中固定物体轴外移6、相对物体9，相对向内中位+.909745mm；243原IK完整独立过、11数值回退。不可直接套用盒子补偿。所有点均当前冻结虚拟参考，不是未来COP。模型目标/工作手画外与掌遮挡风险保留。
- **四实录固定预测检查** diagnose_loaded_causal_prediction.py + summarize_loaded_causal_prediction.py 已跑父jointXY盒/袋和新jointedge盒/袋，参数与更早unloaded_tracking_dynamics_bias_audit_r1/RESULT.json的ae9d82b...哈希及数值核齐，不拟合当前轨迹，不生成新命令。当前过去q/u预测，下一q只评分；首加载排除。父盒/袋/新盒误差中位.284/.191/.311mm，新盒35修正.231mm；**新袋194帧中位.657/P90 4.917/最大6.254mm，75修正中位2.015/P90 5.068mm**，速度外推有时更好。报告LOADED_CAUSAL_PREDICTION_SUMMARY.md/json，禁止直接移植旧无载模型或把事实预测当命令干预因果保证。
- **数值回退** diagnose_joint_edge_fallbacks.py 已原float32逐一复现11袋回退，均SLSQP8 line-search；11被拒endpoint均过原方向/界容差+独立解析Jacobian KKT，最大残差约1.62e-8。实际命令未改、未接受失败状态、未改门。JOINT_EDGE_FALLBACK_DIAGNOSIS.json在新后袋目录。
- **仅隔离筛查** screen_joint_edge_analytic_solver.py（SHA9d76885a3097f034bc8471589d95213b67da8aa08db0f43d613cb2244badd6a2）同11实测输入只改约束Jacobian为解析值，原目标/界/容差/LP初值保持。导数与中心差分核对过；10正常成功并过独立检查，438步仍状态8。JOINT_EDGE_ANALYTIC_SOLVER_SCREEN.json在新后袋目录。未接线/未冻结候选/无新物理，不能只以11坏样本成功就采集。
- 下一：先诊断剩余438步数值终止，检查解析导数在全部有效实录和保护/默认路径的影响，保留盒跟踪问题与袋预测反例；选定单一可解释改变后另建隔离候选、原/最终独立审核、同原8+2和重复对照。原首零位、双臂/腰允许、指定手、15mm非目标、无助推、h10与其余原质量不变。空间约74GiB。

以下为历史记录，以本段为准。

## 2026-09-30T23:29:07.953164+00:00 关节方向首两条均失败；实际跟踪不均衡定位，完整原条件继续

- 本轮progress：真实最终动作独立审核、两条8RGB4外视/后盒事件实际看、父比较、同seed分叉、名义与真实逐关节响应分解已执行。goal active，0合格新组/转换/模型；不以启动或局部审计通过作完成。
- **坏结果** 后盒131.609464mm（父134.620070）、末10Y13.546662，仍失败；有载106→106，lost4→5/tilt4→4。前袋179.288432mm，仍失败。两条非目标0/姿态支撑过。后盒画外风险、袋掌遮挡保留，ACTUAL_REVIEW_BINDINGS已2条。20原控制/两条reference/execution/front/domain与两case60归档来源核齐。
- **局部好证据不是成功** 后盒116全推动原IK独立重放，35最终修正、0数值回退；原界/slew/FK方向与独立KKT通过。首次最终修正617步，但原/新模式101步已分叉，前袋排除新flag也185步分叉；来源/物理/布局同字节核齐，单seed总分差不作因果收益。
- **真实原因线索** diagnose_loaded_waypoint_tracking + diagnose_joint_xy_actual_response + 新diagnose_joint_edge_tracking.py已执行：35修正帧中32下一实测固定参考在固定物体轴与实际相对物体均外移>.05mm；名义向内中位约0，实际固定轴−.612663mm、相对−.421236mm。右肩pitch名义/实际一阶局部贡献中位−2.395/−1.745mm，而roll+2.210/+.533mm，不同关节响应不均，名义相互抵消不能保实际方向；各中位数不能相加，逐帧分解余项最大.01011mm。物体平移中位贡献+.2577mm、旋转−.0836mm，本例不是单纯物体跑得快。所有点为本步固定虚拟参考，不是预测未来COP。新诊断首跑模块路径错误已修复重跑，不改数据/生产/冻结源。
- **当前唯一物理** joint_edge_groups_r1，实际核活[1706882, 1712872, 1707392, 1707393]，case840004前盒运行，后袋和余下容易/等待均保留。PROTOCOL c42a7e2c18b81133cfd7c6228884439656540485f691bf14733268105ca62aeb / stage c69482a3469a8e531af245cbee58ba0cf9b84d15ec442fb267120d46d9ae2e3f未改。不能并行第二物理或重跑prepare/freeze。CAUSE_REPORT/PARTIAL/coverage已更新。
- 下一继续前盒/后袋全原门与实际图审，后袋完成运行compare_joint_edge_actual.py、loadedtracking→jointXYresponse→jointedgetracking确认是否同机制。整批8推2wait全部审核关闭后，才决定过去观测带载响应和向内余量的离线筛查/下一隔离候选；不能把只名义FK不向外继续当接触保证，不改原门、不扩腰界。仍完整4族12fresh/split→合格整组转换训练共享RGB11D→独立192push3wait多seed实际h10/画面目标。

以下为历史记录，以本段为准。

## 2026-09-30T23:19:59.135968+00:00 关节方向候选接线/独立动作审计完成；同原8推2等待已实际启动

- 上一分拣目标轮progress（实际collector接线/递归影子动作/独立审计）；Git备份核验不算分拣进展。本轮progress：22实际CLI检查确认通过，修正静态几何结论，冻结并启动唯一物理对照。goal active，0新合格完整训练组/转换/模型。
- **当前 joint_edge_groups_r1** runner1706882、首collector1706890、controls1707392、events1707393实际核活；首840001后绕盒运行。原case顺序840001/840004/840000/841000/840005/841002、8push2wait、seed0、1200/70、布局原字节保持；只增加--rear-joint-edge-command。PROTOCOL c42a7e2c18b81133cfd7c6228884439656540485f691bf14733268105ca62aeb；stage MANIFEST c69482a3469a8e531af245cbee58ba0cf9b84d15ec442fb267120d46d9ae2e3f。post-AppLauncher60归档/新flag及全部冻结依赖已核；ACTUAL_STARTUP_CHECK记录。禁止重跑prepare/freeze、并行第二物理或改冻结源/审计。
- **staged_joint_edge_command**16源码，父14中13helpers字节未变，只collector改变并新增helper/adapter。新flag默认关闭，原限幅float32之后、previous更新之前改最终upperaction；原top_push/validrearXY条件及全部保护先行、首次加载/前侧/初始排除。原父命令/实际previous/最终命令分别记trace；原边界、原位置法向非工作手目标、原Z及动作slew保持。数值失败明确保留父动作。collector ea39bc43cce4cc2014ae5bbaa8bfdffeffdd6f82bd4d297474338a1d1a209b81；helper47af9ad37986d7cca2e81886c8eb2ce872481cd61e3e9ebfbbc9a0af044a11ca；adapter9d83a403f66421db6815d77fa3125be3a2b72d3bc557a43e4f024d968c42afb0。
- **已执行检查**58非法CLI/60源码实际归档；14选择34原包力；真实collector AST去除显式新增后与父相同，实际finalhook四完整实录4796默认一致、2398前侧排除、4首零排除、2259启用保留、139动作改变。顺序影子传播实际修改动作并重算下一步原父IK/残差，但固定所有物理观测且不含RGB，不是物理成功。真实独立auditor入口3正例19损坏拒绝（源/config/rawforce/parent/previous/finalstationarity/zero/staleresidual等），原数据未变。
- **独立执行审计 audit_joint_edge_execution_live.py**084ad7cc977a2783ff20270b8726282a0dc1858e74506adc4a537b06bf64cca7，先跑未改rearXY/region/causal/continuity/domain审计，从原包力与归档core重算；所有top_push重放原boundedparentIK，最终动作另核FK方向/原界/原slew/解析Jacobian KKT，未导入新helper或adapter。输出JOINT_EDGE_EXECUTION_LIVE_AUDIT；新runner/close使用本输出，不把原父动作与已修改实际动作强行相等。仍保留原参考/front和全部控制审计。数值回退原因本身未独立再现，只有非零状态与原动作保持核验，明确计数。
- **更正好/差结论**旧未接线probe将normalerror保持JSONfloat64，与实际原控制器float32不同，已修正probe并全跑；旧报告JOINT_EDGE_COMMAND_PROBE_CHECK_PRE_FLOAT32保留。现在盒38修改、袋101修改+1 nonlinear_solver_failed回退，不能再说袋102/无回退。重跑静态接触几何：盒50状态向外>.05mm为0；袋107状态为1（回退帧向外5.124mm）；非目标手/物体名义间距最小33.45/21.90mm，非工作锚最坏增.07668mm。只是当前接触中心锚到手后的一步静态FK，不是未来COP/全臂/沿途/真实碰撞证明。coverage新hash同步。
- 新run/prepare/close已创建并pycompile；compare_joint_edge_actual.py已准备、未有新完整结果。父rear_joint_xy仍完整5/8+2wait/困难1/4、两个整组拒绝，RESULT de248d42a89a68b1fe02e377aa1a7ab538fd44bce5fe783c885bb268c22846e9未变。
- 下一核首后盒最终质量、独立原/最终动作、8RGB4外视及接触事件；再后袋检验是否真实减少丢载同时满足推进。其余全部原条件不省略，需同设置重复辨别单seed分叉；原4族12fresh配对/split→仅合格整组转换共享RGB11D训练→独立192push3wait多seed实际h10/画面目标不缩小。首零位/之后双臂腰允许/指定手/15mm非目标/无助推/原质量不变。

以下为历史记录，以本段为准。

## 2026-09-30T22:49:12.328310+00:00 二维参考完整5/8关闭；默认关闭关节方向helper实录检查完成，尚未collector接线

- 上轮/本轮均progress。本轮最后4推动+2等待实际图审与整批关闭、参考点说明更正重跑、接触中心/双手间距独立检查、默认关闭helper与四实录保护/错误回退验证已实做。goal active，0新合格组/转换/模型。
- **完整好/差** rear_joint_xy_groups_r1 5/8+2wait，左右2/4、斜向3/4，两组拒绝；困难1/4。前盒283.479810过，后盒134.620070/前袋169.248464/后袋179.842092败。后袋末10Y84.952168、lost2→8/有载759→178，盒lost4/tilt4未改善。全8非目标0/姿态支撑过；4容易推进margin .061212–.254577mm，5成功中4早于原buffer释放，不稳健。80原控制/8各审计/313实际推动动作精确重放/6×58源码/10过程+所有实际8RGB4外视和等待/事件审核完成。RESULT SHA de248d42a89a68b1fe02e377aa1a7ab538fd44bce5fe783c885bb268c22846e9。CAUSE_REPORT完整，旧四困难报告归档WORKING_HISTORY，PARTIAL/CLOSED已闭合。
- runner1664428、末collector1688878、controls1664436、events1664437均实际确认退出。目前没有新物理任务；不是后台仍采集，也不是goal暂停。PROTOCOL/stage冻结保持。
- **说明更正并重跑** 本步冻结偏移虚拟支持参考可能不在手网格，不能叫手材料点。diagnose_joint_xy_actual_response、screen_joint_edge_ik/nonlinear均改说明并重跑，coverage哈希更新。原数值不变。
- **新独立几何** check_joint_edge_contact_geometry.py检查早先数学解，check_joint_edge_helper_contact_geometry.py检查当前helper输出，均绑定源码/实录/候选结果；将当前力加权COP锚到当前手局部后观察名义位移，不是未来COP预测。helper157状态外移>.05mm均0，最坏盒−.03095/袋−.01059mm；名义双手与不应接触物体间距最小33.45/21.90mm，袋非工作手掌锚点误差增最多.07668mm，法向角恶化>.001rad均0。只静态一步手几何，非全臂/沿途/实际碰撞证明。
- **staged_joint_edge_probe/joint_edge_command.py** 仅新helper+README，默认False，未collector/waistcoordination/生产接线。原top_push与rearXY有效覆盖后有资格；已有效方向原动作保留，原界与原目标不变，数值/不可行明确父动作回退。helper SHA 47af9ad37986d7cca2e81886c8eb2ce872481cd61e3e9ebfbbc9a0af044a11ca。check_joint_edge_command_probe：4完整实录4796默认、4645保护/排除、8非法拒绝、2注入失败路径过，盒38/50+袋102/107动作修改，其余保留，无真实样本数值回退；全输出独立FK/界/slew、输入不变，原313动作完整还原。检查SHA 0f10ecb31fb835ceeb4ca0ef07486272d678ca10fc38d0f92f84dddc0d504e5a。单步36.6/44.2ms中位只离线性能，不是实际运行证明。
- 下一可做：以已闭合本版为父，先真实collector默认关闭接线、原父与最终命令分开独立审核、原包力/核心/姿态/参考来源核对、保护生命周期/前侧首次加载排除、参数/归档/损坏拒绝，再冻结同原8+2单变量物理。不得把新override导致旧执行审计失败直接放宽通过。需同设置重复区分单seed分叉。原4族12fresh/split→仅合格整组转换训练共享RGB11D→独立192push3wait多seed实际h10/画面全目标不缩小。

以下为历史记录，以本段为准。

## 2026-09-30T22:31:45.551326+00:00 二维参考方向四困难1/4；实际方向分配定位与非线性关节离线筛查

- 上一分拣目标轮progress（首后盒实际审核/准备腰界探针）；Git支线不是分拣进展。本轮progress：四困难实际图审绑定、完整原动作审计、分叉及腰界/实际响应/线性和非线性关节筛查已执行。goal active，0新合格组/转换/模型。
- **好/差** rear_joint_xy_groups_r1已审困难4条1过：前盒283.479810mm过/末10Y205.132708；后盒134.620070mm败，前袋169.248464mm败，后袋179.842092mm败/末10Y84.952168。四条非目标XY0、支撑姿态过。后袋比父145.603701推进多但lost2→8、有载759→178；盒lost4/tilt4未改善。实际8RGB4外视及两后绕事件帧已看，遮挡/画外风险保留。40原控制通过，后盒114/后袋199全推动原动作误差0，四参考/执行哈希核齐；两case58源码核齐。
- **分叉** 新盒模式100帧已分叉，XY500才首次生效，前袋未启用新rear也波动；不把整段分差当新控制因果收益。RUN_DIVERGENCE_DIAGNOSIS已实际运行，与正确直接父、原布局/物理绑定。
- **腰界不直接扩大** probe_loaded_waist_bound.py已执行新/父盒+父袋，原全帧精确基线，假设.98→1.08仅单步；盒残差改善中位.202/.256mm、非工作手恶化>.1mm为51/90帧，父袋改善0，所有单步命令仍<1.0。未改实际范围，未证明扩大范围有效。
- **新原因证据** diagnose_loaded_waypoint_tracking.py实际新盒/袋名义参考前进11.291/11.598mm，下一实测仅2.561/2.780mm；diagnose_joint_xy_actual_response.py固定本步冻结偏移虚拟参考点、分离物体运动/旋转，50盒/107袋修改中36/32指令向内但实际相对外移>.05mm，名义关节解局部向内量中位−1.102/−3.898mm。不是COP预测，不能只在Cartesian目标层保证方向。
- **未接线离线候选** screen_joint_edge_ik.py保留原腰/步长/slew和位置/法向/非工作手目标，加近核心边关节方向约束；50+107均可行但非线性FK仍30/85外移>.05mm。screen_joint_edge_nonlinear_ik.py同状态加入非线性FK方向约束后157均可行、>.05mm外移0，名义推进盒9.284/袋9.484mm；袋主动残差增、另一手误差恶化>.1mm有46帧，法向恶化>1e-4为0。只单步原状态，未验证递归/碰撞/真实接触/保护或性能，不得直接物理启动。
- 当前唯一物理runner1664428、collector1676269、controls1664436、events1664437实核活，case840000正常布局进行；剩余正常/交换斜向/两wait全部保留。PROTOCOL a327be982fe332a35d4afd3663f65e4282951a5276331f36805efbf6ed8035e4、stage MANIFEST c8053f9cef56fe137c13ce8e482616b21b8169d0639e03657eed0fb7b7b25b32未改。ACTUAL_REVIEW_BINDINGS四条、CAUSE_REPORT/PARTIAL/coverage已更新。
- 下一先余下4推2wait原审核+实际图审/整组/全批关闭，再决定关节方向候选的独立接线保护/原力到动作审核与同设置重复对照。原4族12fresh/split→仅合格整组转换训练→独立192push3wait多seed实际h10/画面全目标不变。禁止失败数据入库或拿离线方向当任务成功。

以下为历史记录，以本段为准。

## 2026-09-30T22:10:16.688417+00:00 后绕Y减速完整5/8关闭；二维参考方向同原8+2实际启动并核58来源

- 上轮与本轮均progress：末两推动/末等待实际图审、全批关闭，二维wrapper/独立审计/实际collector接线检查、冻结与唯一物理启动均实做。goal active，0新合格完整组/转换/模型。
- **父完整好/差** rear_coupled_progress_groups_r1全5/8+2wait，左右2/4、斜向3/4，两组拒绝，困难1/4。前盒283.275962mm过/末10Y204.928860；后盒134.131903、前袋168.125164、后袋145.603701失败。后袋lost8→2、有载196→759，但末10Y49.926523、682减Y步中位scale.050937，不能用接触代替分拣。全部非目标0/姿态支撑等待过；容易4推进margin.017075–.274187mm，5成功全部早于已有buffer释放，非稳健。实际画外/遮挡风险保留。80原控制、8独立参考/动作/域、后绕928实际推动动作误差0、6×57来源、所有实际抽帧及旧进程退出核齐。RESULT SHA 422a606301a2d1a793fa710942261309405f749b3786c8ed5ac84b6c9bedea4a。CAUSE_REPORT改完整，旧六条中间稿保留WORKING_HISTORY，CLOSED/PARTIAL均闭合。
- **新唯一物理 rear_joint_xy_groups_r1** PID [1664428, 1664430, 1664436, 1664437]实核活，首840001后盒进行。仍原case顺序840001/840004/840000/841000/840005/841002、8push2wait、seed0、1200/70与几何，仅新增--rear-joint-xy-progress，原Y-governor开关和fullreartrace保留；PROTOCOL a327be982fe332a35d4afd3663f65e4282951a5276331f36805efbf6ed8035e4，stage MANIFEST c8053f9cef56fe137c13ce8e482616b21b8169d0639e03657eed0fb7b7b25b32。post-AppLauncher58归档、实际flags/依赖及活PID已核。禁止重跑prepare/freeze、并行第二物理、改冻结源。
- **staged_rear_joint_xy** 14来源，父13仅collector+rearwrapper改变，新增rear_joint_xy_progress.py，11helpers字节不变。先跑全部原rear/firstload/模式保护，再算父X和原Y减速；新几何在原X±2mm/实测lead±30mm内选择近局部边不向外且保留最多Y的X/Y参考方向，Z不动，不可行保留父Y-governor。当前helper/wrapper已接线，不再只是未接线探针。禁止将参考方向几何当物理COP预测。
- **离线已运行检查** helper1153实录几何/960改、1153disabled、10非法/4保护；wrapper6实录输入7194默认逐值相同、1133启用单步，真实倾斜/失载/释放保护保持。audit_rear_joint_xy_live.py从原包力重算COP与实际碰撞core、内部父XYZ/Xslice/原Y、外层新XY（独立LP，与helper顶点枚举不同），传播发出命令历史7194默认/1129合成修改，111损坏和非法类型拒绝。17真实CLI包括两类默认/合成、声明不符、源码/新helper损坏、所有新配置负例及前侧排除。合成固定物理观测，仅命令历史传播；CLI原基础动作审计不是有载新动作证明，正式新轨迹仍需未改audit_rear_coupled_execution_live.py逐帧全推动重放。
- **实际collector校验** 新CLI50非法拒绝/58实际来源归档、14选择（含新flagoff/on及前侧/初始排除）/34独立原包COP、192完整trace调用、240前侧排除、28域16负例、3边界18负例均过。新collector SHA5b84f44ee38aa834d1e10939d310321346e0bd6da7cff4af8671967ec15dd5ac；wrapper2926cc4373069c871dfd1140ae9ea6c3bf4a7bf184d43d5e2d706d7bb838c80e；helperea02b1ed1a004f019646e896c397da105c23d89ab5eca9eafe36f94613ac4fef。探针与stage关键来源相同，所有checker/source hashes冻结。未改生产源和任何原门。
- run_rear_joint_xy_groups.py、close_rear_joint_xy_group/full.py、prepare_rear_joint_xy_run.py已准备并执行prepare/launch。新参考输出REAR_JOINT_XY_LIVE_AUDIT，执行仍REAR_COUPLED_EXECUTION_LIVE_AUDIT，前侧仍FRONT_EDGE_SPEED_LIVE_AUDIT。compare_rear_joint_xy_actual.py已准备pycompile未对新结果运行，正确父rear_coupled_progress_groups_r1；区分上游Y提议和最后XY实际命令，避免把被替换的减Ytrace算作实际减速。无新完整结果。
- 下一首后盒/前袋完成后原质量/实际8RGB4外视+事件/独立原力XY与全推动执行复核；再后袋重点失载收益与推进速度是否兼得，原所有条件继续。前述单seed生效前分叉证据仍有效，不以毫米级单次差异决定稳健改善。原4族12fresh配对/split→合格整组转换→共享RGB11D训练→未调参192push3wait、多seed、实际h10/画面全目标与首零位/双臂腰允许/无助推/非目标15mm原质量保持。

以下为历史记录，以本段为准。

## 2026-09-30T21:52:04.488643+00:00 后绕袋失载8→2但推进退化；完整左右组2/4拒绝；新二维方向仅隔离探针

- 上一目标轮progress（首三条图审/分叉/固定锚筛查）；本轮progress：后绕袋全1200帧原质量/姿态/实际8RGB4外视+事件图完成，763全推动实际动作精确重放；两正常图审、首等待8RGB和完整左右组关闭。当前6已审推动3过+1wait；四困难1/4，完整全批尚未结束。goal active，0合格新完整训练组/转换/模型。
- **好/差一起看：后袋** lost8→2、有载推动196→759；736真实COP覆盖/763推动动作审计通过且动作误差0，非目标XY0，支撑/姿态过，最大倾斜.004515rad。但推进190.072522→145.603701mm、末10Y95.182598→49.926523mm，仍失败；682缩Y步中位scale.050937、7无Y-only解回退，最后仍top_push。不是解决了分拣。后盒134.131903mm仍败、lost4/tilt4不变；前袋168.125164mm败；前盒283.275962mm过、末10Y204.928860，均非目标0。
- **完整左右组 fresh_lateral_00 2/4+wait通过，整组拒绝**：40原控制、4参考/动作/域/连续性、每case57来源及4条8RGB4external/等待8RGB核齐；结果SHA 20ecc2c62f7c7a6a19fd3abf51a5ec4e8fd9b830a005cc909b761a35af126474。正常盒150.274187mm、正常袋150.017075mm均过，但推进margin仅.274187/.017075mm，不能称稳健。后绕和正常活动手/目标画外、前侧接触遮挡的实际视觉风险保留。已审6条和首等待绑定完成。
- **两方向参考筛查已实际执行** REAR_JOINT_XY_DIRECTION_SCREEN：闭合父+当前两类共1153真实已审计X覆盖，保留原X±2mm单步/参考±30mm界和Z，近局部XY边不向外约束下同时求X与最大Y。独立LP与顶点枚举一致。新盒139/袋736几何均能保留完整Y；袋比父X额外修正中位.970884mm。旧edge袋180中56需缩Y，整体保留93.34%。只能证明这些冻结状态的一步参考方向几何，不预测COP或物体推进。
- **关节/非线性检查** REAR_JOINT_XY_IK_SCREEN 对当前139+736有载覆盖，原实际动作先精确还原，再用原J/法向/非工作手/阻尼/界和slew解候选。预测手参考前进增量中位盒1.206817mm、袋2.037788mm；X目标残差盒4.942→5.363mm、袋.572→1.136mm，袋96帧法向残差比原增>1e-4。REAR_JOINT_XY_NONLINEAR_SCREEN用归档FK/支撑面重算，前进点增量中位1.202296/2.033824mm，线性误差最大.253/.279mm，名义法向角恶化>.001rad均0；当前FK与实测参考最大差.000291/.000356mm。全部是手的静态一步，不是物体推进或碰撞安全/接触稳定预测。
- **隔离实现 staged_rear_joint_xy_probe/rear_joint_xy_progress.py** 默认off，未wrapper/collector接线、未冻结、未物理。1153真实几何与独立LP对齐、960修改、1153默认不覆盖且输入未变、10非法输入拒绝、4原非push/低载保护。helper SHA ea02b1ed1a004f019646e896c397da105c23d89ab5eca9eafe36f94613ac4fef。仅已有效父rearX覆盖后有资格调用，首次有载/未交接应由父保护；未来wrapper必须保留现有Y-governor作为不可行回退，不可静默退回无保护推进。尚无传播历史/原力重算审计/真实参数接线检查，不得直接启动。
- **非工作手固定锚筛查补齐袋**：763原推动逐帧还原，在759有载状态完全放松inactiveXYZ后主动线性残差改善中位.027492mm、最大.241383mm，仅29帧>.1mm，腰界0；此局部收益不足以当主要瓶颈。未证明全程双臂重规划无效。
- 当前唯一物理rear_coupled_progress_groups_r1 PID [1634415, 1652446, 1634422, 1634423]核活，840005交换斜向进行，后续841002等待仍保留；当前57来源及冻结审计依赖核齐，PROTOCOL仍3f724...、stage af536...，约78GiB空闲。未改冻结/生产或原门。CAUSE_REPORT保留旧首三条到WORKING_HISTORY。
- 下一：收尾最后2push+wait，实际图审、完整8+2关闭及释放裕量审查；同时仅隔离推进二维wrapper默认身份/原保护/独立原包COP和真实命令历史重算审计。全批关闭后才决定并冻结物理对照，并安排同设置重复运行区分单seed分叉。原4族12fresh配对/split→仅合格整组转换训练共享RGB11D→未调参192push3wait/多seed/实际h10/画面全目标不缩小。

以下为历史记录，以本段为准。

## 2026-09-30T21:38:05.063895+00:00 后绕耦合前三条1/3；单seed分叉先于改动，固定非工作手不是已证主要瓶颈

- 本轮progress：首后盒/前袋/前盒3条1200帧原姿态、8RGB4外视及后盒事件实际已看并绑定；参考/完整执行审核与正确父对照已运行，新分叉诊断和非工作手约束离线筛查已实跑。Git备份支线不计分拣进展。goal active，0新合格完整组/转换/模型。
- **好** 前盒283.275962mm原任务过，末10Y204.928860mm、maxtilt.055327、支撑过；全部3条非目标XY0。后盒165/165全推动真实动作重放误差0，139COP独立通过。**差** 后盒134.131903mm、末10Y16.069101仍失败，父136.297144/18.234342；有载108→157但lost4→4/tilt4→4，89缩Y中位.3483、无Y-only无解回退0。前袋168.125164、末10Y9.725768失败，父207.918867/51.074088，lost7/tilt1不变。实际后绕目标/活动手画外、前侧接触遮挡与前盒末段局部出画风险保留。3条已审1通过不是全8+2。
- **RUN_DIVERGENCE_DIAGNOSIS** 全部父/新归档核齐，规范模块名后仅collector/rearwrapper/helper变化，布局字节和物理配置一致；后盒第1帧q差1.46e-11rad、第73帧位置差>1mm、第100帧模式分叉，新Y控制598才生效；前袋未启用rear，124帧约60nm位置差、171>1mm、331失载恢复分叉。不能把整段成绩变化因果归给新控制；完整后需重复物理对照区分稳健收益，具体非确定性来源未证明。
- **INACTIVE_ANCHOR_TRADEOFF** 首后盒完整165帧baseline精确重放，在157有载状态离线减/删非工作手位置行；完全删后主动线性残差改善中位约1e-6mm、最大.209mm、仅24帧>.1mm；基线腰界115/157，删后120。该状态附近放开固定锚单步收益小，不据此接线新物理。没有证明全程重规划无效或新动作碰撞安全；没有向物理发送新动作。
- 当前rear_coupled_progress_groups_r1唯一物理PID [1634415, 1640112, 1634422, 1634423]核活，840004后袋进行；当前case57归档核齐，前盒等case结束后自动参考/动作/front审核。PROTOCOL仍3f724...，stage仍af536...；冻结源码/审计/生产未改。不重启、不并行第二物理。CAUSE_REPORT、PARTIAL_PROGRESS、coverage同步。
- 下一审核后袋完整效果和全动作；原正常/交换/两wait完整关闭后再选改动。不按单次小分差选版；安排同设置重复物理对照，关注接近/恢复敏感性与持续接触损失。禁止延长本对照帧数或失败组入库。原4族12fresh配对/split→共享RGB11D训练→未调参192push3wait/多seed/实际h10/画面全目标及首零位/双臂腰允许/无助推/非目标15mm原门保持。

以下为历史记录，以本段为准。




## 2026-09-30T21:23:46.777018+00:00 边缘减速完整5/8关闭；后绕推进耦合完整单变量对照实际启动并核57源码

- 上轮/本轮均progress。本轮父末组实际图审/完整关闭、新独立原力与执行审计、实际collector接线/参数/边界检查、冻结和唯一物理启动已执行。goal active，0新合格组/转换/模型。
- **父完整好/差结果** front_edge_speed_groups_r1：5/8+2wait，左右2/4、斜向3/4，两组拒绝；困难1/4。前盒282.156631mm过、末10Y203.809530；前袋207.918867仍失败（末10Y51.074087），后盒136.297144、后袋190.072522失败。前袋lost7/tilt1、前盒lost2/tilt9均未减少；后盒/袋不走前侧flag不错误归因。容易4成功推进margin0.022–0.353mm，前盒进区margin3.810mm，5成功全部早于已有buffer释放，非稳健。全部非目标0、姿态/支撑/等待过；实际画外/遮挡风险保留。80原控制、8独立审计、6×56源码、8×8RGB4external+2×8等待、旧PID退出核齐。RESULT SHA d5c5c5d7f368c4cc82d260695eed67f3761d850111d6675fe65985d77cbf6d19。CAUSE_REPORT已改完整，旧中间保留WORKING_HISTORY。
- **新唯一物理 rear_coupled_progress_groups_r1**：[1634415, 1634420, 1634422, 1634423]实际核活，首840001后盒进行；保持原6case/8推2wait、1200/70、seed0、顺序/几何，父完整edge版，仅加--rear-coupled-progress（同时新增只读全后绕top_push雅可比记录）。PROTOCOL 3f72432558693ab86d1efa72c7df53231ba0e5e515d98561eb63f28692dc5615；MANIFEST af536c0c67b1dee97fd1c58d4bbdd4b73dc9f87a98cf521efe85cc639a52efa3。post-AppLauncher57归档、实际flags/前侧2mm+edge保持、冻结依赖已核。STATUS后才启动观察器，禁止重启/并行第二物理/改冻结源码和审计。
- **staged_rear_coupled_progress**：父12来源仅collector+rearwrapper变，新增rear_coupled_progress.py，10父helpers字节不变（13stage来源/57实际归档）。原rearCOP有效纠偏后，根据当前COP/旋转/core，近局部边10mm时仅缩原前进Y0..1，使参考方向不再向边缘；无Y-only解回退父并记reason。原X/Z、首次有载、模式/倾斜/失载/释放/质量/界不变。新前侧逻辑不动。候选不能保证COP跟随或任务更快，原帧数不延长。
- **独立审计** audit_rear_coupled_progress_live.py SHA df16c4d2d34c05317506c719e816ff46fcf365777abcefcdc2a43bcd1ca2dea6，从原raw前包力重算COP，重建内部父XYZ/Xslice及外层新Y，独立LP验证且使用实际发出历史。6流7194默认、526合成修改步、105损坏/非法enable拒绝；12真实CLI包含两类默认/合成、来源/配置负例及前侧排除。合成流没有进物理，CLI旧基础动作审计主要覆盖无载override/首次接触，不冒充新有载执行。
- **补齐执行链** audit_rear_coupled_execution_live.py SHA 5f3de52db92e6448503b5b6b74b9d90bb062e2138d1baf7cd1138eac30be7c51：由记录的goal、雅可比/法向行、归档boundedIK、原float32权重/边界/最终slew重建实际raw11D动作。六真实历史48采样推动帧误差全0，36错误输入拒绝。历史明确非全覆盖；新collector强制每个被选后绕top_push记录Jacobian/q/side（192实际调用AST组合验证），新标准audit缺任一推动帧则失败，不能用--historical-sampled过门。新整组关闭必须参考审计和完整执行重放同时过。原雅可比本身不由此证明测量准确；实际contact/任务另审核。
- **实际接线检查已执行**：49非法CLI与57真实归档；12选择/34独立原包COP、192全推动trace调用；前侧新flag排除240选择/加载/排除检查；28域16负例、3边界18负例。两旧测试夹具初缺rear_coupled_progress属性，补True后通过，未改collector或原断言。probe7194默认/490单步、826实录几何LP对照/441变化、15fixture11负例及3保护继续有效。所有prepare/freeze已执行，勿重复覆盖。
- 新run/关闭脚本 run_rear_coupled_progress_groups.py、close_rear_coupled_progress_group/full.py、prepare_rear_coupled_progress_run.py 已准备并执行prepare。首次prepare后在启动前修正完整报告标题并重绑protocol依赖；现在以上3f724...为实际协议。新rear审计输出REAR_COUPLED_PROGRESS_LIVE_AUDIT、执行输出REAR_COUPLED_EXECUTION_LIVE_AUDIT；front仍原FRONT_EDGE_SPEED_LIVE_AUDIT。compare_rear_coupled_progress_actual.py已准备，正确父front_edge_speed_groups_r1，实际参考审计+执行审核通过后再比较，新增缩Y/无解回退/全推执行帧指标，终端释放与旧reason分开。尚无新完整结果。
- 下一实际审核首后盒/前袋，重点后绕失载/加载持续/目标区是否改善、是否仅减速或增加回退；所有前侧/正常/交换/等待条件继续。原4族12fresh配对组/split→合格整组转换→共享RGB11D训练→未调参192push3wait、多seed、实际h10/画面全目标不变。首零位/双臂腰允许/指定手/非目标15mm/无助推和原质量全保持。存储约79GiB。

以下为历史记录，以本段为准。

## 2026-09-30T20:57:59.549074+00:00 边缘减速四困难1/4；后绕推进耦合隔离探针已完成几何与完整默认回放

- 上轮与本轮均progress：前盒/后袋完整质量与实际图审、正确父前盒比较、后绕新二维方向screen和helper/wrapper实现实跑。goal active；0新合格组/转换/模型。
- **好结果** 前盒282.156631mm、末10最小Y203.809530mm仍过，418实际覆盖独立过、101带载步减速；非目标0、支撑/姿态过。此前前袋207.918867mm比父175.593562改善但失败。四困难只有盒过，ACTUAL_REVIEW_BINDINGS现4条，全8RGB4外视及两后绕事件已实际看。
- **差结果** 新前盒lost2→2、tilt9→9，最大倾斜.048158→.067463rad，进区裕量4.510→3.810mm。前袋lost7→7/tilt1→1、末10Y51.074仍远未到原200mm；后袋190.072522mm失败，180实际COP审计过、maxtilt.004186、非目标0。后盒136.297144失败。后绕不走前侧flag，不错误归因。实际图保留画外与遮挡风险。
- 当前唯一物理front_edge_speed_groups_r1，[1606600, 1618183, 1606609, 1606610]实际核活，840000正常布局进行；正常/交换斜向/两等待完整保留。此case56归档及所有冻结审计依赖已核齐。CAUSE_REPORT改为四困难完整中间结果，前版存WORKING_HISTORY。全run尚未关闭，不重启/并行物理、不改冻结源。
- **REAR_COUPLED_PROGRESS_SCREEN**：3关闭版本6后绕，826真实已审计X覆盖；保留已录X/Z，仅缩放原前进Y，当前COP距局部XY边<10mm时求参考方向不继续向外的最大系数0..1。解析区间独立LP核对。2mm父盒52/99减Y、袋116/180减Y/5无Y-only解；可解命令保留72.7%/53.1%（袋5回退后整体约54.4%），不代表真实物体推进或接触。旧moving前馈几何保留更多Y仍实测失败，明确不以几何比例评定成功。
- 新 **staged_rear_coupled_progress_probe** 只有rear_coupled_progress.py+rear_cop_route.py，未collector接线/未冻结/未物理。默认关闭，在原rearCOP有效覆盖后按当前测量和原3mm推进缩Y，保留X/Z、无反向；无解保留父命令并记reason。helper SHA5bcf6dbe7375a5acfb4fc73b1d4b98d579ca8be96d80f3077a51fa05f81779d4；wrapper SHA97be2061d0d112f9ff494441f01bc5402cd284de16996d5136c4d525d8046ea4。probe父为完整2mm，但rear wrapper/centering/region_top_contact与当前edge版字节相同；下一真实父须当前完整关闭后明确，不能混front配置。
- 实跑check_rear_coupled_progress_probe：7188默认helper调用、826实际输入独立LP对照/441变化、15镜像/保护fixture、11非法输入。helper检查5N仅用于门控已审计有载样本，不冒充raw力重算。check_rear_coupled_progress_lifecycle：6完整7194帧默认父逐值相同、490启用单步比较；仅Y变化、模式/XZ/其他字段及真实tilt/lost/release保护保持。合成一步与真实X输入分开，不混为物理效果。
- 下一必要：先独立raw力COP/原父XYZ/新Y重算审计及损坏拒绝，再collector默认flag/实际core/hook/归档、原域和前侧排除、CLI/边界检查。旧audit_rear_cop_core_slice_live中unchanged_parent_yz与emitted_waypoint只适用父，需要在独立新审计重建内部原X纠偏和外层新Y，不能删断言冒充过。原连续性只审首次press→push，候选保留首次加载。新审计尚未写；不能直接启动新run。当前批次全闭合后才冻结单变量对照。
- 原完整4族12fresh配对组/split→仅合格组转换→共享RGB11D训练→未调参192push3wait、多seed、实际h10/画面全目标不变。首零位/双臂腰允许/指定手/非目标15mm/无助推及原质量全部保持。

以下为历史记录，以本段为准。

## 2026-09-30T20:46:44.946728+00:00 边缘减速前袋207.919mm仍失败，466真实覆盖独立通过；完整原批次继续

- 本轮progress延续：新前袋1200帧原质量/姿态/8RGB4外视已实际审核，前侧新审计466实际覆盖独立过，正确2mm父比较已实跑。首后盒同已实际审核，当前ACTUAL_REVIEW_BINDINGS2条、0通过；不是全8+2。
- **有限好结果** 前袋175.593562→207.918867mm，末10最小有向Y19.434741→51.074088mm，非目标0、姿态/支撑过，maxtilt.042246rad；62/466带载步减速。frontX532→540帧，侧向667→659，有载239→262、中位单步.859212→.882448mm。首次覆盖均125、初Y仅约30nm差，仍只单seed。
- **差结果** 原200mm区仍未达，lost7→7、tilt1→1未减少；桌面最小margin5.712mm，失败不入库。首后盒136.297144mm失败，98实际COP过，后绕不受新开关，不做错误归因。实际图审保留后盒目标/活动手画外、前袋掌遮挡风险。
- 当前front_edge_speed_groups_r1唯一物理，[1606600, 1612456, 1606609, 1606610]实际核活，已进入840004前盒；新case56归档及全部冻结审计依赖核齐。其余后袋、正常、交换斜向和两等待仍完整保留。当前PARTIAL_PROGRESS、CAUSE_REPORT及coverage已同步。compare_front_edge_speed_actual SHA 4dcd22b187a48c64da4abad026ed9491dbbd9df245c3cc34e7e2f63f130dcc5e，前袋比较SHA 9d9b142b223d7932cea4c582250075d7976b905a844883498c5af968a1e86edc。
- 下一继续前盒原通过是否保留、tilt是否改善，再完整组审核关闭；后绕新分解见下段与REAR_CONTACT_AUTHORITY_FINDING，尚无后绕新控制器。goal active、0新合格组/转换/模型，原4族12配对组/split、共享RGB11D、独立192push3wait多seed实际h10/画面全目标不变。

以下为历史记录，以本段为准。

## 2026-09-30T20:43:01.669256+00:00 前侧2mm完整5/8关闭；边缘减速同原8+2真实运行；后绕失载二维分解完成

- 上一目标相关工作完成冻结候选验证，本轮为progress：末袋/等待实际图审、父完整关闭、真实启动新对照、首后盒实际图审与98原COP复算、新6历史后绕几何分解。Git支线仅完成备份核验，不算分拣进展。goal active；0新合格组、0转换、0新模型。
- **好/差结果** front_drive_increment_groups_r1完整5/8+2wait，左右组2/4、斜向组3/4，均拒绝。困难1/4：前盒282.856971mm过，末10Y204.509869；后盒135.181572、前袋175.593562、后袋189.372770均失败。非目标XY0、支撑/姿态/等待过；容易4条进度裕量0.029–0.250mm，前盒区裕量4.510mm，5成功全部早于既有buffer释放，不能称稳健。80控制、8独立动作/COP/域、6×55源码、所有真实采样图与进程退出核齐。RESULT SHA 7672819813262448922f808f0994ecb46c6cc2cf5852cde1c072c2336a895392。CAUSE_REPORT已写完整；旧中间文件保留WORKING_HISTORY。
- **新唯一物理 front_edge_speed_groups_r1**：[1606600, 1606602, 1606609, 1606610]实际核活，首840001后盒已完整，前袋运行；完整原8推2等待、布局/seed0/1200+70/顺序保持，仅多--front-cop-edge-speed。PROTOCOL 951855d69cf80471f138b5c226589c4dad9cf8f12ea85af5bd254054fd28923c；MANIFEST 900fbcc993635e337e98b17c643c64feee16243c41fb77f854886456de18d8f9。post-AppLauncher56归档、实际2mm/edgeflag与全部冻结依赖核齐。STATUS出现后再启观察器。禁止重跑prepare/freeze、并行第二物理或改冻结源码/审计。
- **首后盒坏结果** 136.297144mm，原任务失败，姿态/支撑过，非目标0；98真实COP覆盖独立过。实际8RGB4外视及事件0/250/252/253/254/258/313/1199已查看绑定，目标/活动手多数画外。此条件不走前侧新开关，不将变化归因减速；新前侧效果尚无完整证据。ACTUAL_REVIEW_BINDINGS现1条。
- 新候选之前未记入handoff的验证现已完成：19真实auditor CLI、42负collector CLI+56真实源码归档、18选择+218加载更新+4排除、后绕10选择34前包、28域16负例、3边界18负例；4796默认逐值/1971合成覆盖/68篡改继续有效。只collector+frontwrapper+新edgehelper变，9helpers不变；当前有效COP距世界推进核心边10mm内2→1mm，原力/Z/保护/3mm步/30mm领先不变。新auditor audit_front_edge_speed_live SHA51ae66a85b07f1ec0c24c42a25fe9372dead4e06cdf12f235baa9122aa49c10e，rear仍旧core_slice，输出FRONT_EDGE_SPEED_LIVE_AUDIT。比较脚本compare_front_edge_speed_actual已准备，待两前侧全帧真实审计后运行。
- **后绕新增实证** REAR_CONTACT_AUTHORITY_DECOMPOSITION：3关闭版本6条，独立前包raw法向力COP与旧审计逐值核验；局部X变化精确拆为初始姿态世界XYZ相对位移投影+局部轴旋转（全加载段/末10步），恒等式验证。当前后袋8失载都无腰界/X步界/领先界，实际支撑worldX相对物体都向内；后6段世界Y投影损失11.6–15.4mm超过X贡献3.1–6.6mm，前两段旋转项突出。后盒5失载全触腰界，4段Y投影超过X，末支撑跟踪差约12.15mm。局部X边脱落并不排除世界Y推进作用，不能统一只增X反馈/扩腰界。下一后绕方向是检查二维推进与纠偏耦合；旧移动前馈实测失败，不直接复用。COP及最低顶点非固定材料点，分解不是独立因果项；无新后绕控制器/物理。初版诊断及完全匹配hash源码保留_v1。
- 下一继续新前袋/前盒真实效果比较及完整原组审核，不用首条/总分掩盖失败。原4族12fresh配对组/split→仅合格整组转换→共享RGB11D训练→未调参192push3wait、多seed、实际h10/画面全目标不变。首零位/双臂腰允许/指定手/15mm非目标/无助推/原门全保持。存储约81GiB。

以下为历史记录，以本段为准。

## 2026-09-30T20:19:15.641022+00:00 前侧盒2mm通过；四困难1/4，边缘减速未接线探针完成完整离线回放

- 本轮progress：前盒及后袋完整原质量/实际图审，前盒421实际COP独立复算和父比较、前侧失载边缘/提前量原力诊断、新隔离减速探针4796帧/1971合成覆盖及独立68篡改检查。goal active；0新合格组/转换/模型。
- **好结果** 前侧盒282.856971mm、末10最小有向Y204.509869mm，原任务+姿态/支撑通过；非目标XY0。父273.183838/末10Y194.836736失败。两首次覆盖均107且首状态仅数十nm不同，仍仅单seed，不能泛化。前X242→266帧、侧向957→933且112帧释放；侧向带载中位.5865→.8141mm。421实际覆盖独立audit过，8RGB4外视已实际看（右下/掌遮挡风险保留）。
- **差结果** 新盒仍9tilt，lost3→2；前袋175.593562mm仍失败且lost5→7+1tilt；后盒135.181572、后袋189.372770mm均失败，后者180实际后绕COP审计过，maxtilt.004538且非目标0。后绕不受前侧开关作用，单次变化不归因。四困难完整1/4，不能用盒单条通过当组准入。后袋8RGB4外视及事件0/207/209/210/211/215/270/1199实际查看绑定。
- 当前唯一物理front_drive_increment_groups_r1，[1579912, 1591392, 1580416, 1580417]实际核活，在840000正常袋；正常盒原质量/姿态与实际8RGB4外视已复核通过，ACTUAL_REVIEW_BINDINGS现5条（2过）。当前case55源码核齐，后续等待/交换斜向/等待全保留。不改当前冻结源码/审计、不启动第二物理。
- 新FRONT_CONTACT_EXIT_2MM_DIAGNOSIS和FRONT_CONTACT_EDGE_WARNING_SCREEN（原raw力、归档collision scale、实测旋转core）：父袋5/5、父盒3/3、新袋7/7、新盒2/2失载前COP距当前世界推进方向核心边≤3mm；新袋10mm预警提前7–10帧。与后绕局部X边机制分开。新诊断第一次NumPy整数JSON序列化失败，转bool计数后完整成功，未改原始记录。
- compare_front_drive_increment_actual.py修正terminal_release沿用旧last_recontact_reason的潜在误计，单列release，原前袋和新盒报告均重跑；source/审计不变。新盒实际为2lost+9tilt+1release。coverage两比较hash已同步。不是物理或质量改动。
- **staged_front_edge_speed_probe仅未接线候选**：front_edge_speed.py在当前有效带载COP距当前推进方向核心边≥10mm保留名义2mm，0..10mm线性降至既有1mm下限。默认关闭，无停住/反向/未来COP预测，原力/Z/模式/保护/3mm步/30mm领先不变。实测输入仅影响新袋48/440、新盒89/421带载步；不承诺减少lost或加快任务，可能更慢。
- check_front_edge_speed_probe.py：4796输入独立几何/默认关闭、15镜像边界、9负例过。复制front_cop_route/contact_slip_following到probe，仅wrapper加edge配置；check_front_edge_speed_replay.py四完整父/新历史4796逐值默认2mm相同、1971合成覆盖、28guard、48无载步、7非法增量过。没有collector接线或stageMANIFEST。勿把合成命令当真实轨迹。
- 新audit_front_edge_speed_live.py独立原力COP/rotation/core边距离和drive重算，非推动/无载禁用也核；check_front_edge_speed_auditor.py四流1971覆盖、68篡改拒绝，auditor SHA 51ae66a85b07f1ec0c24c42a25fe9372dead4e06cdf12f235baa9122aa49c10e。**主入口CLI尚未实跑**（新增归档core/provenance匹配分支），下一必须补主入口+非法enable/配置、实际collector/55归档/前侧hook及rear域排除等，才可冻结；物理必须等待当前全8+2完成审核关闭。新审计输出FRONT_EDGE_SPEED_LIVE_AUDIT.json，当前run仍用FRONT_DRIVE_INCREMENT_LIVE_AUDIT.json，不改旧协议。
- 下一先继续全批质量和实际图审，再决定基于完整front_drive_increment_groups_r1试单一edge-speed候选；无新run/runner/协议，当前父尚运行。原4族12fresh组/split→合格转换共享RGB11D训练→未调参192push3wait多seed实际h10/画面不变。零位/双臂腰允许/指定手/非目标15mm/无助推/原门全部保持。

以下为历史记录，以本段为准。

## 2026-09-30T20:05:38.953386+00:00 前侧2mm袋推进81.6→175.6mm但仍失败；实际失载证据修正后绕假设

- 本轮progress：核活当前唯一物理、首后盒与前袋完整原质量/姿态/实际8RGB4外视，后盒事件已实际查看，首后盒99实际纠偏独立过，前袋440实际覆盖独立过，父/新比较实际执行。新source case840004的55归档和全部冻结依赖已核。goal active，0新合格组/转换/模型。
- 当前front_drive_increment_groups_r1实际存活[1579912, 1585733, 1580416, 1580417]，已进入840004前盒，后续后袋/正常/交换斜向/waits完整保留。ACTUAL_REVIEW_BINDINGS现2条。尚非全8+2；不能重启或并行第二物理，也不能改冻结stage/审计。
- **有限好结果**：前袋推进81.607506→175.593562mm、末10最小有向Y−71.777→19.435mm；非目标XY0、姿态/支撑过。frontX768→532帧，带载417→201；lateral431→667帧，带载185→239；带载单步轴向物体位移中位.2676→.6339mm(frontX)、.4882→.8592mm(Y)。两版首次覆盖均125，首对象状态微小差异，单seed不证明泛化。compare_front_drive_increment_actual.py已实跑，原/新独立审计全部hash绑定。
- **差结果**：前袋仍距原200mm区约181mm，失败不入库；lost5→7，新增1倾斜恢复，maxtilt.057884rad（原pose.20内）。更快推进增加接触恢复成本，不当可用专家。后盒135.181572mm失败、pose/support过、非目标0；不受前侧参数影响，不将随机变化归因新开关。首盒实际8RGB4外视和0/226/228/229/230/234/289/1199事件显示目标和活动手大多画外；袋末段多数可见但掌遮挡，风险保留。
- 新diagnose_rear_contact_exit.py→REAR_CONTACT_EXIT_DIAGNOSIS.json：三代六条完整历史失载前raw力COP/实际旋转核心边距。独立check_rear_contact_exit_sources.py核档碰撞scale/尺寸和所有输入hash通过。core_slice父盒4/4、袋7/8失载前COP距局部X边≤3mm；Y边分别0/4、1/8。**虚拟参考Y超前不等于真实接触从Y边脱落**，不据此更改后绕Y速度。初脚本遇rear阶段无contact_load，明确assert非top且无活动bout后跳过；来源检查系统python缺numpy，改纯Python后成功，未修改数据或门限。
- 盒各接触段Y推进后期10.527→8.057→4.867→2.911mm下降；袋后期约8.8–10.5mm/接触段。仅延长时间不能直接当通用解。失载末有效COP局部X负前缘、部分Z已达−6mm且尚有数N载荷，单纯增压未获充分支持。REAR_CONTACT_EXIT_FINDING.md明确支持与限制，无新后绕候选/物理。重读原几何：后盒front路径桌面margin−16.284mm，rear需x≈.675–.683；不能强制前绕穿桌边。旧目标旋转几何screen仅可能开通道，未证明实际控制旋转，不改初始姿态。
- 下一继续实际前盒结果/独立比较与后袋，其后全8+2审核关闭，再基于两类别决定2mm是否保留。未准备下一物理参数扫描。完整目标保持原4族12fresh配对组/split、合格转换共享RGB11D模型、未调参192push3wait多seed实际h10/画面。原零位/双臂腰允许/指定手/非目标15mm/无助推/质量门不变。

以下为历史记录，以本段为准。

## 2026-09-30T19:54:49.215866+00:00 移动前馈完整4/8关闭并拒绝；前侧2mm推进完整单变量已实际启动

- 本轮为progress：完成旧8+2全部实际画面绑定/80原控制/6×55归档/完整关闭，新增前侧实际CLI/collector接线及独立审计入口检查、冻结和唯一物理启动。Git备份支线已完成，不当作分拣进展。goal active；0新合格组、0转换、0新模型。
- **差结果** rear_core_slice_motion_groups_r1完整4/8+2wait，两组各2/4拒绝；困难0/4。RESULT SHA 56e67aebd4fb2c9fb3aa45b1a41f07ed0fe3935a68db5628d635ae1767dee986。后盒136.301758、前袋81.483819、前盒271.872327、后袋187.613502mm均失败。后袋额外X漂移11.517→28.527mm，触腰界0→13，仍未到末10区；后绕移动前馈不继续携带。正常/交换斜向4条过但推进裕量仅0.044–0.290mm，全部既有buffer前释放；不能视稳健成功。非目标全程XY0、姿态/支撑/等待过。CAUSE_REPORT已改完整，旧中间报告存WORKING_HISTORY。旧runner1545361、collector1577764及观察器1545436/1545437实际已退出。
- **新候选** staged_front_drive_increment基线为完整关闭的staged_rear_cop_core_slice，只有collector+front_cop_route改，9helpers字节不变；默认1mm/候选2mm，原.05反馈、3mm逐轴步/30mm领先、力/Z/所有质量保护保持。不含moving-slice FF。MANIFEST cdb3be715869d270a3c389d848355f21932e406ac0e6fec6b357d1d10a51ca60。
- 实际检查已完成：37负CLI、55归档；前侧14选择+6加载接线+4排除=24；后侧10选择34前包；28测量域16负例、3边界18负例。前轮11990默认逐值/5533合成覆盖及120篡改继续有效。新增check_front_drive_auditor_entry.py实跑11主入口case：两类默认实际/2mm合成过，声明不匹配/越界/禁用仍留trace共6拒绝，rear禁用通过。新测试只离线、不能预测物理成功。stage/probe均不重跑prepare或改写冻结文件。
- **当前唯一物理** front_drive_increment_groups_r1，实际核活[1579912, 1579914, 1580416, 1580417]；首840001后盒已step60+，其后前袋/840004/正常/等待/交换斜向/等待完整顺序保持。PROTOCOL f392668e5718677790d405b32533d39efb4d7b4069d4e2c01089e1dfec3bcb4d；parent_result绑定rear_core_slice_groups_r1（不是刚失败moving版）。仅新增--front-cop-drive-step-m .002，两token差异已核。post-AppLauncher55源码及冻结依赖/实际参数已核，LIVE_STARTUP_SOURCE_CHECK通过。观察器在STATUS出现后启动，不重启/不并行第二物理。
- 新脚本run_front_drive_increment_groups.py、close_front_drive_increment_group/full.py、prepare_front_drive_increment_run.py已准备且prepare已执行。新front审计audit_front_drive_increment_live.py写FRONT_DRIVE_INCREMENT_LIVE_AUDIT.json；rear仍audit_rear_cop_core_slice_live.py。compare_front_drive_increment_actual.py已准备未实跑，待两前侧完整独立audit后比较：原进区门、带载阶段/失载/首干预前状态，不能只看推进量或把单seed前期随机差异归因新参数。完成每条真实8RGB4外视、等待8RGB与完整配对审核再关闭。
- 全目标仍原4族12新鲜配对组/split→仅合格完整组转换→共享RGB11D训练→未调参192push3wait、多seed、实际h10闭环和画面验证。零位/双臂腰允许/指定手/非目标15mm/无助推与原质量不变。存储约83GiB，失败不训练，不缩小目标。

以下为历史记录，以本段为准。

## 2026-09-30T19:36:38.525451+00:00 移动前馈四困难0/4：盒退化、袋仍失败；前侧2mm推进探针完成独立离线验证

- 上轮/本轮均progress。本轮四困难完整数值与实际8RGB4external/两后绕事件、独立命令比较、实际材料运动/路径效率新证据、新前侧隔离探针及独立审计已执行。goal active，0新合格组/转换/模型。后台唯一物理仍rear_core_slice_motion_groups_r1，当前840000：runner1545361/collector1561061、control1545436/event1545437本时刻实际核活。当前8+2未完整，勿重启。第二case55源码+全部冻结依赖已核齐；normal/waits/swapped后续全保留。
- **差结果**：后盒136.301758mm（父141.684）、前袋81.483819、前盒271.872327、后袋187.613502（父184.225）mm均失败；姿态/支撑过、非目标全程XY0。后盒97实际覆盖独立过，带载117→109、lost4→6/tilt4→3，末10Y17.330mm；handover233→244，前期差异在干预前存在。后袋163实际覆盖过，带载196→179、lost8→7但末bout未结束，末10Y91.998mm远未到200；命令反向5→0不等于成功。
- **新增坏机制证据** REAR_MOTION_DRIFT_DIAGNOSIS：后袋首次干预后X额外漂移11.517→28.527mm，实际覆盖步腰规划界命令0→13、2mmX步界0→12；loaded腰最大实测.894→.983。盒57/97覆盖步腰触.98。新前馈几何方向正确但推进/可达性未解决，不应继续携带到前侧下一实验。
- **有限好证据**：新后盒step235腰实测.980053246（物理1rad内）超过规划.98后命令.979913890向内，原域独立审计通过；首次真实域恢复1，不是质量通过。首后盒及后袋比较工具都已实跑；ACTUAL_REVIEW_BINDINGS现4条，事件都已实际查看。各画外风险保留，不增可见性硬门。
- **前侧诊断** FRONT_LOADED_EFFICIENCY_DIAGNOSIS六历史：袋frontX约768帧、有载417，105.6mm退让只有1.54mmY；lateral431帧仅185有载约80mmY，五次失载/恢复占近半时间。FRONT_MATERIAL_REFERENCE_DIAGNOSIS与FRONT_REFERENCE_ROTATION_COMPONENT新实跑：袋真实材料相对滑移frontX .770/lateral1.195mm每步；实际材料-虚拟旋转差-.0026/.2587mm，名义差.641/.809不能当真实偏置逆补偿。不要因静态FK名义差就更换参考点。原python汇总缺numpy，切项目环境后实际成功；不是仿真失败。
- FRONT_DIAGONAL_CORNER_GEOMETRY_SCREEN精确四仿射段最小AABB间距、端点桌面：保持原12mm/5mm的15mm角点，袋路径450.601→388.959mm只省61.643mm（14%），盒省20.857mm。422袋/74盒历史当前姿态截图几何通过，但无手/臂/接触/原顺序状态机证明，未接线/未物理，不能把假设路径当任务成功。
- **新候选仅前侧drive1→2mm**：历史native前袋160.939仍失败/前盒280.925过，对比当前约82只支持受控测试，不证明步长单因果。staged_front_drive_increment_probe默认1mm保持；.05反馈、3mm逐轴最大步/30mm参考领先、parent力/Z/模式/原保护不变。10完整历史11990默认逐值、5533合成覆盖，70保护+120无载步骤+7非法增量过；audit_front_drive_increment_live独立原力COP/几何/路径/命令复算，120篡改拒绝。全部离线，不预测更快不会加剧滑移。
- **staged_front_drive_increment已新隔离接线，未冻结/未物理**。prepare_front_drive_increment_stage.py本轮已执行，不重跑覆盖。基线选择完整关闭的staged_rear_cop_core_slice；probe引用motion版前侧文件但已证明与该父字节相同，只改front_cop_route和collector，**不携带rear-core-slice-motion-feedforward**。新增--front-cop-drive-step-m默认.001、候选.002，非默认要求front_cop_route_axis；余9helpers字节不变。下一完成真实CLI/55归档/collector前侧选择与contacthook/后侧域排除检查及auditor主入口，再冻结。下一协议应比较core_slice父而非当前motion父；等当前完整8+2闭合后才唯一启动。尚无新run目录/runner/关闭脚本。
- 新文件FRONT_NEXT_EXPERIMENT_DECISION.md归纳下一实验依据/限制。当前所有离线session已结束，只有原物理/两个观察器继续。原4族12组/split→合格转换训练共享RGB11D→未调参192push3wait多seed实际h10/画面全目标不变，失败不训练、零位/双臂腰允许/指定手/15mm非目标/无助推及原质量均保持。

以下为历史记录，以本段为准。

## 2026-09-30T19:14:23.835989+00:00 原旋转核心反馈完整4/8关闭；移动区间前馈完整对照已真实启动

- 本轮为progress：12完整历史独立验证、新默认关闭前馈接线/审计/冻结、父8推2等待全图审关闭与新唯一物理启动。前一Git支线仅备份状态核验，不算分拣进展。goal active，0新合格组/转换/模型。
- **父rear_core_slice_groups_r1完整4/8+2wait**，两组各2/4拒绝；RESULT SHA ea0f7becabad361fc23808276e427f0cc98e12f43901b23a7b6d586436167ba3。全部80原控制、8新COP/域/因果连续性、6×55源码归档、10实际退出与8×(8RGB4外视)+2×8等待实图核齐。旧runner1519129/末collector1543276/control1519138/event1519139实际已不存在。CAUSE_REPORT改为完整；历史保留WORKING_HISTORY。
- **好/差明确**：后袋反馈反向102→0、命令反向81→5，180实际覆盖过；仍184.224650mm失败，末10有向Y89.335mm，有载209→196、lost9→8，不是持续接触改善。后盒141.684057、前袋81.607506、前盒273.183838mm皆失败（前侧不受后绕开关，不能归因单次波动）。正常盒150.007546/袋150.005661、交换斜向盒150.035471/袋150.210902mm通过，裕量极小且全在既有专家buffer前释放。非目标全程XY均0，姿态/支撑过。仍困难0/4，不能用总分掩盖。
- **新线索已实算** diagnose_core_slice_motion→CORE_SLICE_MOTION_DIAGNOSIS：当前后袋172连续有效点，安全X区间目标步移中位.90134mm，旧锚前馈.11246、命令增量.35317、遗漏移动.66528mm。物体旋转/COP沿Y滑动使目标X变，单改反馈方向没改前馈。新helper固定原局部锚X投影并夹在当前COP世界YZ所定10mm内核X区间内，用当前/上个有效目标X差做前馈；首loaded保持原动作，失载/空区间/原模式/步长无交集reset。保留.05gain、2mm步、30mmlead、原Y/Z/所有保护。非未来预测、非动力学逆补偿。
- **新stage staged_rear_core_slice_motion**已冻结MANIFEST 739267acfada9e05cca815fc7c26d4d15768a63c574c92cae5e4c5ad641b60ff。12流14388帧两旧flag默认逐值，1417一步反事实；独立raw力COP+LP+自维护history；20状态fixture11非法输入；12合成全流1417覆盖308篡改拒绝；真实CLI30负例55归档，12选择34前包，完整状态机14388逐值/1417一步/3原保护，28域16负例和3边界18负例均实跑。CLI首次缺既有OMNI_KIT_ACCEPT_EULA环境而EOF，用runner相同环境后通过，无代码/断言放宽。生产及已冻结父源码未改。
- **当前唯一物理rear_core_slice_motion_groups_r1**：runner1545361/collector1545396在840001，control1545436/event1545437实际核活；19:12:25UTC启动，2026-09-30T19:14:23.835989+00:00已post-AppLauncher55源码+全部冻结依赖核齐。PROTOCOL a6bb057bdc8e50ddbd8b9870273346e5550d8b921ba27d8dac0192404561a425；相同6命令/8推2wait/seed0/1200+70/顺序，仅增加--rear-core-slice-motion-feedforward；观察器在STATUS出现后启动。prepare_stage/run均已执行，不得重跑覆盖。无完整新结果。
- 新audit_rear_core_slice_motion_live.py先原域→因果连续性，再独立移动slice历史+LP+原YZ，写REAR_CORE_SLICE_MOTION_LIVE_AUDIT.json；关闭close_rear_core_slice_motion_group/full，比较compare_rear_core_slice_motion_actual读正确父core_slice。新run不得并行第二物理，不改冻结/原门。先实际后盒、后袋是否减少失载/到区，再保留全部前侧/正常/交换斜向/等待；失败不训练。
- 额外已完成诊断：BYPASS_MOTION_BUDGET_DIAGNOSIS揭示后盒顶接触前约100.5mmX为计划绕行，rear_push占95.5mm；非无载意外碰撞。TARGET_YAW_ROUTE_GEOMETRY_SCREEN仅静态目标转90度可能开前通道，未证明真实手/臂/力控可转，绝不能改初始摆位替代动作。首盒YAW_CONTACT_MOMENT_DIAGNOSIS瞬态力矩/偏航仅观察，不是可控转向。旧有载模型/统一减阻尼/停Y均无稳定改善证据，不接线。
- 完整目标仍原4族12配对组/split→合格后转换共享RGB11D策略→未调参192push3wait多seed实际h10闭环及实际RGB；首11D零位/双臂腰可动/指定手/非目标全程15mm/无助推/原质量不变。释放裕量候选单列未物理，不混本轮。剩余约85GiB，无新训练。

以下为历史记录，以本段为准。

## 2026-09-30T18:38:24.926641+00:00 新旋转核心候选首盒真实完成：141.684mm仍失败，107实际覆盖审计通过

- 当前rear_core_slice_groups_r1唯一物理runner1519129/collector1519131、control1519138/event1519139实际核活；首后盒完整，前袋/后续全部原条件继续。未启动其他物理/训练，0合格新组/转换/模型。新单条不是完整8+2结果。
- **差结果**：后绕盒141.684057mm失败，父rearCOP138.099724mm；末10有向Y21.769661mm仍远未到原200mm区。非目标XY0、支撑/姿态过，maxtilt.055284rad。独立新CORE_SLICE审计107真实覆盖通过，原测量域/因果/连续性过，域外/恢复0。
- compare_rear_core_slice_actual已实际执行并绑定正确父rear_cop_measured_bounds_groups_r1：有载110→117，仍4tilt+4lost，末多一个未结束bout；新反馈反向0/命令反向0、空slice回退1。父handover228、新233，干预前已有轨迹差异，不用3.58mm增量证明因果改善。新8RGB4external与事件0/230/232/233/234/238/293/1199实际view并绑定；活动手/目标在交接多数画外，未新增可见性硬门。
- 下一重点收袋实际结果，验证102旧反向反馈是否在新真实历史消除、是否延长接触并满足末10区；同时完整收前侧/正常/交换斜向/wait，原质量和完整组准入不变。无需重跑prepare/freeze；新比较脚本已准备并实跑首例，旧源码/审计继续冻结。goal保持active，本轮为明确几何原因/完整验证/真实启动/首条实际审核progress。

以下为历史记录，以本段为准。


## 2026-09-30T18:33:54.679784+00:00 旋转核心方向问题已独立定位；新完整8+2单变量对照实际启动

- 上轮完整关闭/真实图审/诊断为progress；本轮父拟合留出预测、明确几何方向错误、隔离候选/接线/独立审计与真实启动同为progress。goal active，0新合格组/转换/模型。
- **当前唯一物理** rear_core_slice_groups_r1：runner1519129/collector1519131在840001，control1519138/event1519139本时刻实际os.kill核活。18:31:44UTC启动，18:32:37实际post-AppLauncher55来源+全部冻结依赖核齐；先等待runner STATUS创建才启动观察器，未复发旧race。尚无完整结果。PROTOCOL SHA d41ec5a5df1b667fe5494106d3ad7cbf5633ecd0718bc11e36405c0fa3c642e2；MANIFEST 80460d0471c081f3ab03992887d620f468df129721a890315d6b19f6f9683863。prepare_rear_core_slice_stage/run均已执行，不能重跑覆盖。
- **新具体坏机制**：父rearCOP使用固定物体局部锚投影的worldX−当前COPworldX误差，物体旋转后可与当前COP保持worldY/Z的核心内侧X方向相反。独立raw前包接触力加权COP/实际姿态/归档碰撞scale+单变量LP核验：新父后袋200实际覆盖中140次距10mm内核外且存在X解，102反馈方向反、81最终X命令反；后盒97有解外部中0反馈反、1命令反。非简单关节饱和/统一跟踪误差；不能把所有袋失败都归该项。
- **候选** staged_rear_cop_core_slice（父staged_rear_cop_measured_bounds11来源，只3文件变化）：默认关闭--rear-core-slice-feedback requires rearCOP。只把反馈error换为当前旋转碰撞体10mm内核与worldX直线交集的最近位移；原对象锚前馈、Y/Z、首loaded保持、.05gain、2mm步/30mmlead、倾斜失载释放保护不变。无X交集则回退原parent/reset，并非放宽几何或改Y。生产及父冻结代码未改；释放裕量/阻尼/有载响应模型均未接入。
- **实跑检查**：10完整历史11990帧默认逐值（helper及rearCOP启用/core-slice关闭的完整状态机），1130一步反事实；独立LP18几何fixture/4非bool负例，10合成完整命令流1130覆盖/162损坏拒绝；真实CLI29负例55归档、collector10选择34前包、原域动作28fixture16负例、真实边界3fixture18负例、原tilt/lost/release3保护。边界/域检查初次fixture缺新flag，补齐True/False后全部实跑过，未改控制器或放宽断言。新audit_rear_cop_core_slice_live先调用原域→因果/连续性，再独立LP/COP/原Y/Z复算，写REAR_COP_CORE_SLICE_LIVE_AUDIT。旧审计保留。
- **不能提前报好**：同原输入候选后袋反向反馈102→0，最终反向命令81→9，原前馈/限幅仍可能不利；后盒最终1→0。COUNTERFACTUAL_DIRECTION_LIMITS明确一步假设，不是实际新闭环效果。新run与已关闭父5/8+2wait相同6命令/8推2等待/几何/seed0/1200+70/顺序，仅多一个flag，完整两组都保留。
- **有载模型诊断已否定直接逆补偿**：diagnose_loaded_causal_response父盒134/袋183样本分别拟合，冻结系数评估新盒110/袋209整段；constant_velocity XYZ MAE盒[.090,.339,.109]mm、袋[.168,.371,.204]，gain+momentum盒[.091,.316,.137]、袋[.154,.394,.236]，并非稳定优于惯性外推。按整段betterXYZ为盒4/6/0（8段）、袋8/3/2（9段）。留一父接触段系数敏感，error/velocity相关常>.95，袋肩pitch gain可近0，不应取倒数放大。loaded_causal_response_diagnosis_r1/RESULT和IDENTIFIABILITY均完成；命令FK与下一实测差不能直接认作可逆静态偏差。所有离线检查已退出。
- 下一先首后盒实际完整审计/图审、后袋实际是否消除旋转下错误方向，并比较持续接触/倾斜/失载/末10区；保持余前侧/正常/交换斜向/wait全原条件，若runtime或审计失败保留上下文、不能盲重启。新比较工具应读取CORE_SLICE新报告和当前父rearCOP报告，不复用旧父regionmeasured做错误对照。关闭脚本close_rear_core_slice_group/full已写；运行run_rear_core_slice_groups，sources与dependencies冻结。
- 全目标仍原四族12完整类别交换组/split、共享RGB11D、首零位/之后双臂腰允许/指定手/非目标全程15mm/无助推/原h10，合格后转换训练并未调参192push3wait多seed实际模型验证；前袋效率和成功释放裕量问题仍待解决，不以启动或单条替代完成。

以下为历史记录，以本段为准。


## 2026-09-30T18:15:02.767667+00:00 完整后绕COP对照已关闭：5/8+2wait，未获完整组；暂无后台任务

- **本轮progress**：完整8推动2等待实际图审/80原控制/8因果连续性前后COP测量域/6×55源码归档/10实际退出全部核验。RESULT SHA 80cfa14048c33bf20ea8a761cc637ce1570537532042b89e12dd815b9aba6507；左右2/4、斜向3/4均拒绝。runner1475035/末collector1507255/control1476005/event1476006现实际不存在；本轮所有离线session也已退出。当前无后台物理/训练任务，不要把历史STATUS运行记录当现状。goal active、0新合格训练组/转换/模型。
- 好：正常盒150.031120/袋150.015853、交换斜向盒150.224462/袋150.045380、前盒280.842409mm过，非目标全过程XY均0；前盒为非干预路线，不能把父4/8→5/8解释为后绕纠偏有效。差：后盒138.099724、后袋183.038332、前袋82.133301mm失败；两个后绕仍没有稳定接触/到区成功。所有失败保留，不能入库。五通过均在既有专家裕量前释放，四易例推进裕量仅.016/.031/.045/.224mm，前盒末10区裕量也仅.276mm，不能宣称鲁棒。
- 新loaded_damping_allocation_probe_r1：四实际流35采样推帧原command重放完全一致，32有载点正确投影几何校验过；阻尼缩至.5/.25后X改善与退化混合，新盒多数变化很小。只是离线静态分配，不支持统一下调阻尼作为下一物理候选；旧非线性多数不收敛/3点float32拒绝也不部署。
- 新diagnose_loaded_material_reference实际执行，LOADED_MATERIAL_REFERENCE_DIAGNOSIS：前包t-1实际COP定义当前t固定手/物体材料点，currentpose严格对齐；110盒/209袋样本。材料点与虚拟参考名义X增量差中位-.01686/.09820mm、p95abs .02138/.12220mm，远小于名义到下一真实材料点X差中位1.98196/1.43774mm，Y约-9.20314/+10.12964mm。实际手对物体材料X漂移中位+.12712/+.15873mm。此证据不支持把参考点定义错误当主要原因，不能直接换参考系。该分析是观测与静态FK，不是有载动力学预测/证明摩擦饱和。
- **下一具体工作**：先基于完整两类真实有载历史（含父版）建立严格因果的关节命令→下一实测响应诊断，区分稳态跟踪滞后、限位和接触载荷变化；检查X恢复请求为何有持续实测偏差、箱接触后期腰饱和而袋多无关节位置/步长饱和。只在 held-out 接触段/两类中验证后才设计补偿，不能复用无载gain冒充有载模型、用未来帧指导当前动作、或盲加gain/停Y/统一减阻尼。另前袋通道效率与释放裕量仍未解决，不能被后绕诊断遮盖。尚无新控制候选，下一采集必须新目录/单一物理/完整原任务/原门及独立审计。
- 目标仍原四族12完整类别交换组和划分、首11D零位/之后双臂腰yaw允许/指定手/非目标全程15mm/无助推/原h10；合格后转换共享RGB11D策略，再未调参192push3wait多seed模型闭环和实际画面。当前完整开发诊断5/8不是模型成绩或训练许可。

以下为历史记录，以本段为准。


## 2026-09-30T18:08:47.378295+00:00 有载分配与几何校验：首完整左右组2/4拒绝；两后绕机制需分开

- 本轮progress：新增逐值动作重放、正确校准虚拟参考点的独立有限差分、实际6推+首wait图审与完整左右组关闭；goal active，0新合格组/转换/模型。上一Git备份支线已核实完成，不计分拣进展。
- 当前唯一物理runner1475035/collector1499527在840005，control1476005/event1476006本时刻实际核活{'1475035': True, '1499527': True, '1476005': True, '1476006': True}。末交换斜向两推和末wait未全图审/关闭，不能给完整8+2成绩。当前6已审核中3过，左右组2/4+wait拒绝（40原控制/4因果域COP/3×55归档/首零位无助推/实际8RGB4external核齐）。生产和冻结控制/审计未改。
- **好结果有限**：新前盒280.842409mm原质量+姿态过，非目标0；不属于新增后绕干预，不能归因新纠偏。正常盒150.031120、正常袋150.015853mm过但推进裕量仅.031/.016mm，释放问题仍单独保留。
- **差结果**：后盒138.099724mm、前袋82.133301mm、后袋183.038332mm均失败。新后袋较父167.657092增加，但末10有向Y仅83.552413mm；实际COP200覆盖过，loaded183→209而lost8→9，不是持续接触成功；两后绕域外/实际恢复仍0。两前后图审已绑定：前盒手遮挡/末帧右下裁切，后袋活动左手/目标在交接多次画外；没有新增可见性硬门。后袋REAR_COP_ACTUAL_COMPARISON完成。
- **精确求解重放**：replay_loaded_coupled_allocation父盒/袋+新盒24采样推帧实际command误差0，另replay_rear_bag_coupled_allocation新袋11帧误差0。结果loaded_coupled_allocation_probe_r1及loaded_rear_bag_allocation_probe_r1。Y请求减半/暂停对新盒5有载点均加大X误差、腰饱和不减；新袋各点效果混合，不支持统一暂停Y方案。
- **几何疑点已排除**：check_loaded_projected_geometry和check_rear_bag_projected_geometry实际21+11有载点，使用记录center_local/world_normal重算orientation-dependent reference；全部当前参考点对齐与有限差分过，最大J误差2.71e-7m/rad。先前单点未带center_local的大误差属离线检查错误，不是控制器bug。旧LOADED_WAYPOINT_TRACKING固定当前offset语义保留，它是不同材料参考点，不应误当未来虚拟参考点。新PROJECTED_GEOMETRY_CHECK明确区分。
- **分配探针未获运行许可**：X_FEASIBILITY在21点原关节/step/slew、其余线性误差不变差下均有局部解，但非线性inactive可变差；新NONLINEAR_ALLOCATION直接重算真实几何并约束activeYZ/inactiveXYZ/normal分量，18/21候选float32满足所声明数值容差，3拒绝，且多数优化器未报告收敛。新盒改善小且并不全可接受，不能接线/宣称物理有效；无全局不可达结论。
- **实际接触新证据**：两后绕CONTACT_SURFACE_MOTION_AUDIT已实跑，106盒/200袋有载末子步样本。物体沿路线每步中位.758/.817mm，手相对材料1.067/1.500mm，载荷4.930/5.275N；这是有限间隔材料滑移描述，非COP速度/冲量/摩擦饱和证明。LOADED_BOUT_EDGE_DIAGNOSIS显示盒后四段X余量耗尽且腰接近.98，单段有载推进7.55→6.23→3.81→1.30mm；袋首段靠Y边缘，此后多X边缘且腰约-.56至-.63，11有载采样均未触物理/规划关节位置界。不可用盒的腰饱和解释袋全部失败。
- 下一先收完当前8+2/全审计图审及关闭，再分开定位盒的接触姿态/关节分配与袋无饱和仍X失载的材料运动/载荷跟踪。不盲增gain、不暂停Y、不改摩擦/门槛/时长/原任务；新非线性仅离线探针，未创建新物理控制候选。释放裕量另候选不合并。原四族12配对split、首11D零位/之后双臂腰允许/指定手/非目标全程15mm/无助推/h10与未调参192push3wait多seed共享RGB11D目标保持。

以下为历史记录，以本段为准。


## 2026-09-30T17:45:26.424573+00:00首条真实后绕COP退化：102实际纠偏过审，X跟踪余差与腰饱和增加

- 本轮继续为progress，不blocked/不完成。当前唯一物理rear_cop_measured_bounds_groups_r1：runner1475035/collector1482692在840004，control1476005/event1476006本时刻os.kill核活。首后绕盒及同组前袋2完整，其他原条件继续；0新合格组/转换/模型。
- **差结果首盒**：138.099724mm vs完整父156.851478mm，两者失败；新末10有向Y20.037mm，非目标XY0，支撑/姿态过（最大tilt.055877）。新audit_rear_cop_measured_bounds_live真实102覆盖独立过（auditorSHA11cad396f75bef762f48ce82e1fea23b75c4bb37d3935b05d76d3f78e57027b9），原域/因果/连续性过，域外/向内恢复0。实际8RGB4external+8事件已view绑定；交接活动手和目标画外风险保持。新frontbag82.133301mm失败，原姿态过且实际8RGB4external已查看绑定，不属于后绕干预不能归因其变化。
- compare_rear_cop_actual.py实际执行，新首盒REAR_COP_ACTUAL_COMPARISON：有载134→110，9→8段、4tilt保持、lost5→4；少失载不是改善，新后4失载前实际coreX余量-.017/.042/.014/.019mm仍贴边。top_descend595→629、top_push144→118。报告不由单次same-seed差异证明唯一因果，首handover227→228本身也有先期差异。
- **更具体跟踪限制**：新diagnose_loaded_waypoint_tracking.py对父/新真实q[t]、command[t]、q[t+1]用同一当前offset独立FK，参考点对齐<0.00031mm。X目标-当前中位2.698→6.902mm，X目标-名义关节命令FK1.233→4.023mm，名义-下一真实X1.488→1.998mm；有载腰命令触.98从3/134→74/110，Y名义与下一实测仍约9.2mm差。发出纠偏不等于实际接触点跟上，既有名义余差也有执行误差；尚未证明所有动作分配都不可达。结果LOADED_WAYPOINT_TRACKING_DIAGNOSIS和LOADED_TRACKING_COMPARISON均已绑定。脚本首次缺repo搜索路径、后遇numpy整数JSON，两者修复后两报告成功实跑，没有放宽断言/改变仿真。
- 下一在当前全8+2保持冻结运行时，先收新后绕袋及前盒；然后重建有载coordinated_step/ bounded_damped_step，评估横向drive与X接触维护如何分配，在原normal/inactive/joint约束下是否有可行名义解，不能盲增横向gain或用无载响应拟合冒充有载动力学。入口simfoundry/data/waist_coordination.py coordinated_step、bounded_ik.py；coordination.json有contact_normal_tracking和每20帧trace_jacobian，真实raw用于逐值复现。尚未创建该新控制候选。
- compare_rear_cop_actual.py/diagnose_loaded_waypoint_tracking.py为只读新分析工具，生产和冻结源未改；CAUSE_REPORT追加首盒退化，coverage更新2实际审核推动，所有离线工作已结束。后续完整父关闭/新run协议/观察器启动时序记录见下段。原四族12配对split、首11D零位/双臂腰允许/指定手/非目标15mm/无助推/原h10/未调参192push3wait多seed共享RGB模型目标不变。

以下为历史记录，以本段为准。

## 2026-09-30T17:37:01.763441+00:00接续：范围父版完整4/8关闭；后绕COP组合对照实际启动

- 前轮为progress；本轮余2push+末wait实际图审、完整父关闭及新唯一物理启动/55核源为progress。goal active，0新合格组/转换/模型，原目标不缩小。
- **父region_measured_bounds_groups_r1完整关闭4/8+2wait**，两组各2/4拒绝。80原控制、8因果/连续性/前COP/域、6×53归档、10实际退出与全部8×(8RGB4external)+2×8wait核齐；旧runner1441368/collector1472835/control1442356/event1442357均实际不存在。RESULT SHA 18107f87172d37a208e1315545b89f23bb2f1578c4bcaaeec436321ff80afef3。正常盒150.079459/袋150.037132、交换斜向盒150.280803/袋150.366411mm过；四困难仍0/4，非目标XY全0。四过均在既有专家裕量前释放，推进裕量仅.037..366mm，不能宣称鲁棒性改善。全部域内求解未实际触发恢复，真实崩溃恢复仍未证实；旧失败保留。CAUSE_REPORT改为完整，历史保留PRE_CLOSE及WORKING_HISTORY。
- **当前唯一物理rear_cop_measured_bounds_groups_r1**：17:32:12UTC runner1475035/collector1475077在840001，当前os.kill仍活；control1476005/event1476006。实际post-AppLauncher55源码+全部依赖17:33:37核齐EARLY_STARTUP_SOURCE_CHECK；首盒已进入top_push/recovery，尚无完整raw/效果结论。PROTOCOL SHA 1c41b86054fcf6c006000fde352e350cd9006e58322e76dbe2c72fe443aa8304；相对父6命令仅多rear-cop-centering，原8推2wait/seed0/1200+70/布局顺序保持。
- **观察器启动时序问题已处理**：初始1475036/1475037抢在runner STATUS建立前FileNotFound退出，原control_watcher.log/event_watcher.log保留。确认物理runner/collector仍活、初始两观察器确已退出后，只重新附加只读观察器为1476005/1476006，日志*_after_status.log；物理没有重启。RUNNING_PROCESSES与ACTIVATION记录原因和新PID，55核源时两新观察器真实核活。
- staged_rear_cop_measured_bounds仍冻结MANIFEST87a32f456517aaec9aa7550ccba254f52126ac870293490ef0d2fe3e1ed6b55c，prepare_rear_cop_measured_bounds_run本轮**已执行**，不能重跑覆盖。新audit先独立域再后绕COP；关闭close_rear_cop_measured_bounds_group/full保留所有原门。compare_rear_cop_actual.py已准备但未运行，需新完整REAR_COP_LIVE_AUDIT和MEASURED_BOUNDS_LIVE_AUDIT后才比较同条件真实载荷段/边缘/质量，不能把反事实当执行。
- 下一先首盒完整实际审核/图审与接触比较，同时保留全8+2；若运行/审计异常保留原上下文，不盲重启。前侧bag让通道效率/edge和box倾斜恢复仍单独未解决，释放裕量候选不混入。只有完整原四族12配对合格新组才转换/训练，再未调参192push3wait多seed实际h10共享RGB11D验证；零位/双臂腰允许/指定手/非目标全程15mm/无助推/原质量保持。

以下为历史记录，以本段为准。

## 2026-09-30T17:25:13.892251+00:00接续：完整左右组2/4拒绝；前侧两类失败机制进一步分开

- 上轮progress；本轮正常袋/首wait实际图审与完整左右组关闭、新两版前侧时序/COP/材料位移和命令速度分析为progress。goal active；0新合格整组/转换/模型。
- **唯一物理仍region_measured_bounds_groups_r1**，runner1441368/collector1465359(840005)/control1442356/event1442357本时刻实际os.kill核活，约89GiB空间。已完成实际6push评审：正常盒150.079459、正常袋150.037132mm通过，四困难0/4；首wait稳定通过并实际8RGB绑定。close_region_measured_bounds_group已经关闭fresh_lateral_00，2/4+wait、40原控制/4因果/连续性/域/3×53归档；整组拒绝。余交换斜向2push和末wait继续，不启动第二物理。
- 新diagnose_measured_front_routes.py已执行，FRONT_ROUTE_CAUSE_COMPARISON绑定每case归档碰撞config/实际raw/前包force：前袋两版768帧才lateral，余432帧尚距原目标区351.8mm，5失载（前X边缘，后Y边缘）；前盒179帧lateral，本版4lost+9tilt，后9次COP并非X贴边（Y余量7.2..16.1mm）。不是延长时长就成功的证据。
- 两条前侧CONTACT_SURFACE_MOTION_AUDIT实际执行：袋frontX/lateralY样本413/183，物体沿路线中位.271/.496mm，手相对材料.764/1.190mm；盒90/399、物体.682/.534mm、相对.771/.644mm。末子步力非积分。FRONT_COMMAND_RATE_DIAGNOSIS四阶段均零反向active命令/零30mm领先裁剪；步长中位袋1.203/1.575、盒1.819/1.590mm，不再支持旧反向抵消解释。报告和CAUSE_REPORT更新；FRONT_DIAGNOSIS_PROGRESS绑定完整左右结果SHA/核活/新报告。
- 下一已冻结staged_rear_cop_measured_bounds保持未运行，MANIFEST87a32f456517aaec9aa7550ccba254f52126ac870293490ef0d2fe3e1ed6b55c、源码/原审计未改。prepare_rear_cop_measured_bounds_run尚未执行，只有父余项全图审/全关闭后才能创建/唯一启动新完整8+2。前侧候选、释放裕量未混入；早释放接线需单独新确认谓词审计，不能连带修改terminal_goal。所有离线检查结束，无其他长任务。
- 后续仍原四族12配对/划分与共享RGB11D模型、指定手/另一物全程15mm、首零位/允许双臂腰/无助推/原h10及独立192push3wait多seed，不以专家诊断进度冒充整体完成。

以下为历史记录，以本段为准。

## 2026-09-30T17:16:41.180217+00:00接续：四困难0/4，后绕持续失载证据复现；范围父版上的COP新候选冻结

- Git备份支线已完成，不计分拣goal进展；本轮新三条困难+正常盒实际图审、两版真实接触比较及组合候选接线/独立审计为progress，goal active。0合格新组/转换/模型，整体目标不缩小。
- 当前唯一物理region_measured_bounds_groups_r1：runner1441368/collector1456767(840000)/control1442356/event1442357在17:14:58UTC实际os.kill核活，3case×53来源和所有冻结依赖核验写FOUR_DIFFICULT_SOURCE_CHECK。当前已完成5推：正常盒150.079459过；后绕盒156.851478、前袋82.406133、前盒258.918792、后绕袋167.657092mm均失败。4困难非目标XY0、姿态/支撑过。正常袋、交换斜向两推和2wait尚未完成，不能关闭/给完整总分。
- 两后绕111/110独立域记录全过，域外实测0/向内恢复0，未物理触发新修复。后绕盒126→134有载步，仍4tilt+5lost；袋182→183、仍8lost。盒失载前COP实际coreX余量0.064/.120/-.027/.036/.041mm，袋后七失载X-.148..1.242mm；首次袋Y.995mm，非X问题不能藏掉。REAR_CONTACT_COMPARISON绑定原始数据，区分vertical>=.2计数与normal>=.3末COP。无因果提升结论。
- 实际5条各8RGB4external与两后绕8event已view/绑定；后绕目标/活动手画外风险保持，前侧遮挡，正常盒342后采样目标画外。不是新增硬门。正常盒推进裕量仅.079459mm，释放候选不合并。CAUSE_REPORT已更新，旧过程保留WORKING_HISTORY。
- **新隔离staged_rear_cop_measured_bounds已冻结，未启动**：基于当前范围父版，仅新增rear-cop-centering，要求measuredflag；8父helper逐字不变，2旧COPhelper逐字相同，collector选择/载荷接线加入。MANIFEST SHA 87a32f456517aaec9aa7550ccba254f52126ac870293490ef0d2fe3e1ed6b55c。新prepare_rear_cop_measured_bounds_stage/freeze_rear_cop_measured_bounds已执行不可重跑覆盖。CLI28负例55archive，8selection34packet，28action16negative，3boundary18negative；加入本次两后绕后共8stream9592default逐值、896一步反事实/3保护；独立8stream896合成覆盖238损坏拒绝。非新物理。冻结检查曾将BOUNDARY报告raw误作源码路径，已用报告episode解析并真实核验；没有跳过检查。
- 新audit_rear_cop_measured_bounds_live先调audit_region_measured_bounds_live，reconstruct AST与旧rear审计完全相同且绑定域报告；新run_rear_cop_measured_bounds_groups/close_rear_cop_measured_bounds_group/full/prepare_rear_cop_measured_bounds_run已写，新关闭同时要求域+COP+所有原门。准备run脚本**未执行**，必须先当前完整8+2关闭后才能创建rear_cop_measured_bounds_groups_r1并唯一启动。无第二物理/训练，所有离线检查结束。
- 下一先收当前余3推2wait，实际图审/全部原审计/关闭原两组；再以上述新脚本做仅新增COP的完整8+2对照并核55归档。后续仍原四族12配对新合格组/转换/共享RGB11D训练/未调参192push3wait多seed实际h10，不能以专家单条/诊断启动结题。

以下为历史记录，以本段为准。

## 2026-09-30T16:55:06.597488+00:00接续：实测/命令范围修复完成真实几何与接线检查，原完整8+2实际启动

- 前一goal轮为完整父关闭/捕获新失败的progress；本轮1430实际求解逐值复现、真实FK边界反事实、独立新域审计及单变量全组实际启动为progress。goal active，0合格新整组/转换/模型；无新物理成功结论。
- **新stage staged_region_measured_bounds**（9来源），基于完整XY_R2对应staged_region_causal_xy_diagnostics，只新增默认关闭--region-separate-measured-bounds（requires causalXY且waist-limit1.0）。collector从原URDF给出实测域，仅腰±1.0；lifecycle把它传入helper并记录measured_state_bounds。命令/因果预测仍腰±.98、所有原几何/步长/载荷、以及测量保持交接必须原规划域保持；其他关节原URDF不变。六辅助源字节未变，三个变化为collector/lifecycle/helper。后绕COP与释放裕量候选未合并。
- **实际检查**：check_measured_bounds_real_geometry四完整后绕1430已执行override（含handover）全部精确，显式域内启用完全一致；真实nearbound8状态×3腰扰动共24命令/预测独立FK检查均过，无域外交接，明确是反事实非失败现场/物理。合成原失败q常量geometry6负例仍单独保留。check_measured_bounds_prelaunch真实CLI24负例/53归档；check_measured_bounds_wiring真实collector AST28fixtures16负例，physical1.0/command.98传参与记录已核；check_measured_bounds_boundary_wiring另3真实几何扰动经torch/USD感知fixture→hook→实际动作覆盖，18独立域/命令/handover损坏拒绝。新增audit_region_measured_bounds_live先跑原所有因果/连续性再核声明/实测物理/命令域外禁handover；没有放宽评分。
- MANIFEST SHA 06c35e7e5455f300ddc66ae5bec83693f4d1510cf5ba7931a11ee8caa02cbed3，PROTOCOL SHA 1f26c686ca1f3668284f637e13d5a1f218b60b312aafde2e42033a376409a8ad。prepare_measured_bounds_stage和prepare_region_measured_bounds_run均已执行，不可重跑覆盖；新run名region_measured_bounds_groups_r1，父仍XY_R2（4/8）而非失败COP，六命令输入比较仅新flag。新runner run_region_measured_bounds_groups.py，关闭close_region_measured_bounds_group/full包含独立域审计；旧源码/审计都冻结不改。
- **唯一物理实际运行**：runner1441368、collector1441407在840001，control1442356/event1442357；16:53:18UTC post-AppLauncher53档案及所有审计依赖真实逐项过，此刻os.kill核活。最新日志step960、modetop_lift，已越过旧210/215附近。仅说明仍运行，未证明同一次越界重现或向内修正成功；需完整raw独立审计。不启动第二物理或训练，原8push2wait/1200+70/seed0/顺序/所有任务保持。
- 下一先拿首盒完整数据，核域外实际q出现次数、向内实际command及预测几何/交接、持续接触与原门；全部8+2/实际图审后闭合。若运行错误则保留精确上下文，不盲重启。范围修复确认后再决定单独加载COP实验，前侧两困难仍未解决。原四族12配对/split、首零位11D/允许双臂腰/指定手/非目标15mm/无助推/h10与未调参192push3wait多seed共享RGB模型目标不变，不能以修复运行崩溃替代达成分拣目标。



## 首条完整实际结果（2026-09-30T16:58:47.019679+00:00）

后绕盒156.851478mm，原任务失败；非目标XY0，支撑/倾斜原门过，最大tilt0.067038rad。独立域审计111solver记录通过，域外实测次数0、向内恢复0，所以并未在物理中触发新修复，不能将149.009→156.851归因本项。交接227帧，原9按压→推切换、因果/几何审计通过；8RGB4外视和事件8帧已实际查看并追加绑定。多数后绕RGB目标画外，未新增硬门。原完整其余任务继续，当前runner1441368/collector1441407实际核活；不能把该单条或诊断通过当训练许可。

以下为历史记录，以本段为准。

## 2026-09-30T16:39:59.770797+00:00重要终态更正：后绕X新run因实测腰轻微越规划界中止；已捕获完整上下文

- **现在没有后台物理/训练/离线长任务**。rear_cop_centering_groups_r1在16:34:02UTC runtime_or_control_audit_failed，0完整条件；runner1431358/collector1431392/control1432136/event1432137均实际不存在。上一节“正在运行”是启动历史，不是当前状态。最后PROGRESS210、viewer215。collector退出0但runner正确拒绝case错误。未盲重试/未删除失败/没有训练准入。
- **新明确原因**：原无载solver把实测q也与规划命令界±.98比较；本次唯一越界upper11索引0=waist_yaw_joint，实测.9800471067428589，超规划4.7106743e-5rad，距原物理1.0尚.0199528933rad。完整q/上下界/残差/gain/offset记录在RUNTIME_FAILURE.json（SHA 76b2dbf829fd4a4110b108ff4671c6b999e4f440df01000cd0b674bd2cd946a0）。原名义+因果预测+step+slew的腰命令代数区间[.965047106743,.979906837695]非空，说明早期状态拒绝发生在尝试受约束向内命令之前；不保证真实几何可行，也不能声称旧XY_R1具体关节相同。
- 新X纠偏尚未进入首次交接后的有载阶段，**没有该候选效果结论**。当前父完整XY_R2仍4/8+2wait，两组拒绝；当前0新合格组/转换/模型。本轮仍progress：完整父关闭、实际新失败可观测、界限诊断和隔离修复检查；不是三轮无进展阻塞。
- **新底层隔离候选staged_measured_bounds_probe**：prepare_measured_bounds_probe.py已执行不可覆盖；contact_patch_step新增可选measured_lower/upper。默认仍原范围；显式实测域需包含命令域且有限，真实配置拟只给腰±1.0、其余原URDF。名义/affine命令±.98、所有几何/核心/步长/质量保持；几何交接measured-q hold额外必须原规划域内。尚无collector接线或完整真实几何验证，不能启动。
- **已实际检查的有限证据**：check_measured_bounds_probe.py用捕获失败q+响应参数，但geometry为明确常量理想fixture，默认仍提前抛出；启用后命令.979906837695、预测.98，不能域外交接；原物理越界/缺界/形状/NaN/域不包含共6负例过。CHECK SHA 3d00cef7768dc2a24c42372ca10d70f7f470ad7e8ce0720bbc06e65bb6085850。只证明分支/代数，不证明真实机器人恢复、可达性或任务成功。
- **下一**：先在真实历史FK/输入上验证默认逐值一致和真实几何安全，测试实测域越物理必拒绝、预测/命令仍严守规划界、域外无交接；再做collector全接线与独立审计。优先把范围处理单独施加在已闭合XY父基线上做完整8+2对照，后绕COP保持隔离，避免一口气混合两个因子。所有原四族12配对/划分、首11D零位/双臂腰允许/指定手/非目标15mm/无助推/原h10/独立192push3wait多seed共享模型目标保持。新失败详细CAUSE_REPORT已写，coverage状态已更正。

以下为历史记录，以本段为准。

## 2026-09-30T16:35:18.341153+00:00接续：XY完整4/8关闭；后绕有载X纠偏全检查完成并实际启动

- 上轮为progress；本轮完整父对照关闭、两组拒绝、真实图审、后绕新候选和独立审计/真实启动为progress。goal active，未完成、无blocked；0新合格整组/转换/模型，整体原共享策略目标不缩小。
- **父region_causal_xy_groups_r2已完整关闭4/8push+2wait**：两组均2/4拒绝；80原控制、8因果/连续性/COP、6×53来源、10退出码、全部实际8RGB4external+wait8RGB核齐；父4PIDs均实际不存在。RESULT SHA 4e98c761514c747603a770b5da41401886e1a10f5813137aab2fec1bed7f3429。R1首轮异常保留，精确关节未知，R2不崩不证明解决。CAUSE_REPORT已重写完整、旧过程另存WORKING_HISTORY。
- **完整结果**：正常盒150.251806/袋150.018863过；交换左右后绕盒149.009157、前袋80.893479失败；正常斜向前盒265.120164、后绕袋165.481582失败；交换斜向盒150.231898/袋150.130376过。非目标XY均0。3→4提升来自原未覆盖正常盒贴门波动，不能宣称新算法导致总分提升。接触与RGB具体证据仍见父完整报告。
- **新隔离staged_rear_cop_centering（11来源）**：rear_cop_centering.py+rear_cop_route.py；默认关闭--rear-cop-centering，只后绕且原region交接后有载top_push。实际core10mm内缩锚，当前/前态物体锚X平移+.05真实COP误差；X每步≤2mm且当前参考领先≤30mm交集，无可行交集返回父。首次有载推动不覆盖，原父update先行且Y/Z不改；失载/倾斜/释放/前侧/initial/等待均保持。释放裕量副本未合入。MANIFEST SHA dcecc14994b6ecf640d92ed55edd36ddfe1cc2a92a5882f0421f3e6551c8024c。
- **检查实际完成**：六完整后绕历史7194帧，596反事实X覆盖独立代数/载荷时序；默认7194帧完全一致，原3类恢复保护通过。测试曾误写target_load_n（实际仍3N），已保留旧报告并修成desired_n=5重跑通过，当前绑定5N结果。新真实CLI27负例+55归档，collector真实AST8类选择+34真实前包独立COP重建，独立audit_rear_cop_centering_live的六真实测量/明确合成命令596步与168损坏拒绝过。都是代码/反事实检查，不是物理成功；当前真实新审计待完整写盘。
- **新唯一物理rear_cop_centering_groups_r1**：16:32:51UTC runner1431358、collector1431392；watcher1432136/1432137，16:33:46真实核活并post-AppLauncher55档案及所有冻结依赖核齐。PROTOCOL SHA ff3b84d5a776ce2dec83c6c6409fe512f4b9f1d6554960466772b40e765f4590，INPUT_COMPARISON核6命令相对父仅新增rear-cop-centering，布局/顺序/seed0/1200+70/原8推2wait保持。完整父结束后才启动，无第二仿真/训练。新run尚无完整轨迹与效果结论。
- 新runner run_rear_cop_centering_groups.py调用audit_rear_cop_centering_live（先执行原因果/连续性审计再核独立X及父Y/Z），旧front审计不变；close_rear_cop_centering_group/full已准备严格加入新审计及原全部门。prepare_rear_cop_centering_stage/run均已执行，不可重跑覆盖。生产源和运行冻结源均不可改。
- **下一**：收实际后绕盒/袋新持续接触、所有前侧/正常/交换/等待退化及所有独立审计/实际图审；若越界异常则保留完整上下文停止该run，不盲重试；全条件后闭合。成功后仍需原四族12配对split的合格新组、转换/共享RGB11D训练、未调参192push3wait多seed实际h10，不能以诊断启动或局部改善结题。首零位、双臂腰允许、指定手、非目标全程15mm、无助推和所有原门保持。

以下为历史记录，以本段为准。

## 2026-09-30T16:12:20.721307+00:00接续：四困难全部失败；后绕真实接触改善但仍失联，释放裕量隔离检查完成

- 上一轮Git备份支线完成，不计分拣进展；前一次goal有真实诊断progress。本轮四困难独立审计/实际图审、接触失效分解与离线释放候选验证构成progress。goal active，未完成，0新合格整组/转换/模型。
- 唯一物理region_causal_xy_groups_r2：runner1405142、collector1416605在840000，watcher1405946/1405947实际os.kill核活。PROGRESS_SOURCE_CHECK_4_DIFFICULT核全部53冻结来源及审计依赖一致。首4推动已经完成，剩余正常/交换斜向及2wait继续；原8+2不缩小，无第二物理/训练。磁盘约92GiB。
- **四困难原门全失败**：后绕盒149.009157、前袋80.893479、前盒265.120164、后绕袋165.481582mm；非目标最大XY均0，支撑/姿态过。前侧未覆盖新XY，不能归因数值变化。R1运行越界精确关节仍未知，失败完整保留；R2未重现不能证明修复。
- **好/差真实分解**：盒246交接、122因果预测步与9切换审计过，有载top_push0→126步；4倾斜保护+5失载，后五失载前COP核心X余量0.680/.112/.844/-.016/-.031mm。袋210交接（父212）、8切换过、有载172→182步，8次失载，174后动作载荷样本材料相对切向位移中位1.506mm。都是末子步载荷，不冒充积分/唯一因果。
- **限位**：盒qwaistmax.983770在top_push；越过.98的96..107/251..258帧都未调用区域求解器，区域实测max.979995。原1.0物理界不变，不据此放宽求解器，也不把R1猜成腰超调。逐帧MEASURED_PLANNING_BOUNDS_DIAGNOSIS、LOADED_BOUT_COMPARISON/CONTACT_LOSS_CAUSE_DIAGNOSIS与袋LOADED_CONTACT_DIAGNOSIS已写。
- 四条8RGB4external和两后绕事件均实际view追加ACTUAL_REVIEW_BINDINGS；后绕盒大量画外，袋左裁/活动手接近时画外，前侧手遮挡。可观测风险待真实共享模型验证，不新增全帧可见硬门。
- **未接线释放候选**：prepare_confirmed_release_margin_probe.py已执行，staged_confirmed_release_margin_probe默认关闭require_expert_margin；只让早释放谓词额外使用已有ready_to_release160mm推进/205mm区间，保留10观测/稳定确认。check_confirmed_release_margin_probe.py实跑父8+本次前3共13189观测默认逐值一致、候选严格子集；20双方向阈值/稳定fixture与4非bool拒绝。CHECK绑定SHA；非新物理/非新评分。旧源码与冻结运行均未改。不要把历史释放后未再达裕量当新控制不可达预测。
- **下一工作**：优先完成本R2完整余项及闭合，再针对真实后绕X接触边缘设计受限横向维护，Y/Z/倾斜/失载原保护保持；释放裕量另单变量验证。若接线释放monitor，注意collector terminal_goal另实例用于终态hold，不能连带改变。原所有布局族/12配对split、首零位11D/双臂腰允许/指定手/非目标15mm/无助推/原h10和未调参192push3wait多seed共享模型目标保持。详见本run CAUSE_REPORT.md。

以下为历史记录，以本段为准。

## 2026-09-30T15:52:29.620253+00:00完整父3/8关闭；XY首轮运行越界中止，仅增强异常信息的复现正在运行

- 父region_causal_response_groups_r1现已完整关闭3/8push+2wait，两组1/4与2/4均拒绝。RESULT SHA92e94f92397ed53fe3201d44106b36c394476c4c9e28d5aa63343c2ee09983fc；80原控制、8因果/连续性/COP、6×53来源、10实际退出码、全部8×8RGB4external+2×8wait已实际审核。所有父PIDs已实际退出。CAUSE_REPORT已按完整结论重写，过程保存在CAUSE_REPORT_WORKING_HISTORY。三成功推进余量0.023393/0.046960/0.393486mm；四困难全失败，正常盒149.999648mm严格失败，不四舍五入。0新合格组/转换/模型。
- **XY首轮region_causal_xy_groups_r1失败，不能继续声称运行**：15:44:50启动runner1401877/collector1401879；53档案实际核源通过后，首盒最后进度210，运行抛出Measured joints outside working bounds。runner15:46:03终态runtime_or_control_audit_failed，0完整episode；两个watcher结束，所有4PID实际不存在。原异常只保存文字，没有q/哪个关节/超限量；不能猜成腰超调。RUNTIME_FAILURE.json保存来源、最后进度和最后viewer帧，原目录/冻结源码保留。原collector进程退出码0不代表成功，caseSTATUS与runner已阻止继续。
- **新唯一观察复现region_causal_xy_groups_r2**：15:50:37UTC runner1405142/collector1405149，control1405946/event1405947；此刻核活，53source/审计依赖已真实核验。PROTOCOL SHAe1ba4d616eef9413f9d6cb47efc9c9c997be3a36b0853d28f5c2d66823109162。相对XY_r1所有命令参数仅目录变化、原8推2wait/所有门保持，原异常仍会停止，不是改参数重试取成功。
- **仅观测改动staged_region_causal_xy_diagnostics**：复制冻结XYstage9文件，8文件逐字相同；contact_patch_approach仅在同一ValueError补充upper11_q/lower/upper/violating_indices/tracking_residual/response_gain/offset。除该异常文字外整模块AST一致；8越界fixture验证ValueError仍抛出、上下文可重建、不调用geometry。新EXCEPTION_CONTEXT_CHECK和MANIFEST已冻结，继承父21CLI/28wiring/3597default/2197独立步280损坏测试证据，不冒充重新跑过。准备脚本prepare_causal_xy_failure_diagnostics.py（已执行不可覆盖）及prepare_region_causal_xy_diagnostic_run.py；实际runner仍run_region_causal_xy_groups.py。没有放宽关节界限/改变正常命令/评分/几何/动作。
- 下一首先收该真实失败上下文（若不重现也保留首轮失败，不能只挑一次通过）；精确确认哪一关节与规划/物理限位的关系，评估更稳健的界限处理后再改控制。若完整运行则仍须原8+2全部审计/实际图审/关闭。当前本轮是新完整结果、运行失败和补齐可观测性的progress，goal active，不blocked。所有原四族/12组划分、首11D零位/允许双臂腰yaw/指定手/非目标15mm/无助推/原h10、独立192push3wait多seed共享模型目标不变。

**复现运行最新核验**：R2 runner1405142/collector1405149仍实际核活，首后绕盒已经出现top_push并继续恢复（最新进度至少510），尚未完整写盘，不能提前认为独立交接/任务已过；R1越界尚未重现，精确关节仍未知。PRE_REGION_REPEAT_DIAGNOSIS记录相同seed/参数在前区域rear模式0/30/60/90的真实box差异，90帧XY差1.595285mm；只证明实际轨迹不是逐值相同，不归因某随机源，也不从R2未崩溃抹掉R1。下一收R2完整原8+2或异常上下文；不要重启当前活跃采集。

以下为历史记录，以本段为准。

## 2026-09-30T15:37:06.052462+00:00接续：左右完整1/4拒绝；发现正常盒贴门释放失败；XY单项候选已全部冻结

- 上轮progress；本轮新独立审计冻结、完整左右组关闭、正常盒真实释放裕量问题和新材料接触比较为progress。goal active，0新合格组/转换/模型。
- **实际唯一物理**：region_causal_response_groups_r1 runner1375993/collector1394066在840005，实际os.kill核活；control1376496/event1376497继续。首6推动完成，840005两推和841002等待继续，不能提前关闭或启动第二物理。当前93GiB可用，生产源与原门不变。

## 最新完整组与数据质量结论

左右完整组fresh_lateral_00已由close_region_causal_response_group.py审核关闭：1/4push+wait过，40原控制/4因果动作和连续性/3case×53来源/全部8RGB4external及wait8RGB绑定核验；拒绝训练。不是全run结果，斜向交换和末wait仍在运行。

正常盒真实释放607帧，理由confirmed_original_target_position，释放时推进150.001913mm、终态149.999648mm（差-0.000352mm），严格原门失败，末10帧区间余量103.384mm。已有ready_to_release内部目标本为160mm/205mm，被该确认释放路径提前绕过；后续应保留专家自身余量，原评分不改。正常袋150.023393mm通过但余量仅0.023393mm；姿态和实际图审已过，目标171后采样画外，不能以数值通过推断模型可学。

新后绕袋真实表面审计：after-action最后子步hand-normal>=0.3N匹配next-state材料点的样本50→163；推进/手对材料相对运动中位分别1.072→0.764mm、0.950→1.458mm。新失载前首段COP核心Y余量0.819mm，后续X余量约-0.108..1.269mm，持续贴边。此口径区别于前一包vertical>=0.2N的60→172控制步，末子步力不是区间冲量，也不证明唯一原因或摩擦饱和。报告REAR_BAG_SURFACE_COMPARISON.json绑定原始材料运动报告。

XY-only候选现已完成独立审计2197近似历史步+280损坏拒绝，staged_region_causal_xy_response/MANIFEST冻结9来源5检查（SHAfc8b9404024b5522030f01125ec9394c8c684609fcd20b8936a4bfe9041c1114）。另在本轮真实袋112全部无载步骤，默认输出精确、新反事实命令112几何/步长过、106预测core余量改善；不是新实际物理。新prepare_region_causal_xy_run.py/run_region_causal_xy_groups.py/close_region_causal_xy_group.py/full.py已写、未运行；新audit_region_causal_xy_live.py与连续性审计冻结时已绑定。下一先完整父8推2wait关闭，再创建region_causal_xy_groups_r1、只新增--region-causal-xy-response，原完整条件/门保持，核源后启动唯一物理。

- 图审绑定状态：已完成840001/840004/840000共6推，每条8RGB4external；两后绕事件已view绑定；841000wait8RGB已view并写ACTUAL_REVIEW_BINDING。余840005两推和841002wait待实际查看。全部当前闭环仍专家开发诊断，不是共享模型评测。原全四族/配对train-val划分、首零位/11D/双臂腰yaw/指定手/非目标全过程15mm/无助推/原h10和未调参192push3wait多seedRGB模型目标均保持。
- 所有本轮检查已结束，无离线长任务。最新释放审计只覆盖当时已完成5推，待全run完成后重算audit_expert_release_margins.py补齐8条。候选PREPARATION是创建时状态，以MANIFEST为冻结依据，尚无ACTIVATION/新run。完整关闭当前父run使用close_region_causal_response_full.py，必须10实际退出/80控制及全图审。准备下一候选时保留父RESULT与protocol SHA。

以下为历史记录，以本段为准。

## 2026-09-30T15:25:38.137780+00:00接续：四困难仍0/4；后绕袋真实持续载荷改善，XY单项候选接线检查完成

- 前轮为progress；本轮五步真实求解精确复现、完整40反事实对照、后绕袋新实录审计/图审与下一隔离接线是progress。goal active，整体目标未完成；0新合格组/转换/模型。
- **当前唯一物理run region_causal_response_groups_r1**：runner1375993、collector1387565在840000，两watcher1376496/1376497实际核活。四困难已经完成；正常840000、wait841000、交换斜向840005、wait841002由同runner继续，原8推2wait不缩小，没有第二物理或训练。

本轮四困难实际已完成且全部失败：后绕盒65.901209、前袋82.058042、前盒275.655091、后绕袋151.748065mm；全部非目标最大XY0。前盒/前袋不在新区域覆盖，不把数值变化归因新后绕控制。四条8RGB4external、两条后绕事件均已实际查看绑定；原动作/连续性/COP审计已由runner完成。

后绕袋好结果有真实接触依据：交接140→212帧更晚，但top_push前一末子步垂直载荷≥0.2N步数60→172；原43/7/4/4…推动段改善为47/32/22/19/17/17/16/16/2，恢复10→8。9次连续性过。独立交接gap4.205mm、另一掌0.787mm、与另一物间距45.126mm；不是接触积分或唯一因果。推进81.965→151.748mm仍未到+.20区。112真实因果预测高度RMSE0.068979/max0.630797mm。

盒停滞复核：117/200/500/900/1198五实际求解逐值复现误差0；物体xyz与另一掌锚点117后全不变，姿态变化约5e-8。新XY-only副本保留Z/另一掌目标，仅XY误差完整补偿affine偏置；完整40条件两近似响应baseline和candidate都10/10。110均匀实际旧状态默认精确，候选110命令几何/步长通过，109预测core余量改善；仍是反事实，未证明新物理。全目标同时修正的旧候选12/20仍拒绝。

已写staged_region_causal_xy_response隔离默认关闭--region-causal-xy-response（requires--region-causal-response），没有启动。真实CLI21负例/53归档、6父命令唯一新flag、collector28fixtures16负例（XY开关/旧previous状态/动作）、默认3597帧+原保护已执行通过。新9来源尚未最终MANIFEST冻结；下一需独立XY启用审计/检查和完整当前父对照闭合，再冻结原8推2wait新协议。运行中的region_causal_response代码不改，不能提前扩采或训练。

- 所有本轮screen/check均已结束，无离线长任务遗留。原四族/配对划分、首11D零位/双臂腰yaw允许/指定手/非目标全过程15mm/无助推/原h10、未调参192push3wait多seed共享RGB模型验证均不变。生产采集器未改。下一先完成父run完整图审和关闭；候选需新独立审计冻结后才上同原完整对照，不能以启动/单条或近似响应成功结题。

以下为历史记录，以本段为准。

## 2026-09-30T15:12:47.929906+00:00实际新证据：后绕盒113.524→65.901mm退化，预测准确但核心交接停滞

- 唯一region_causal_response_groups_r1仍运行，runner1375993/collector1375995在840001前袋，control1376496/event1376497；新后绕盒首条1200帧已完成失败，余下全条件保留。无新合格组/转换/训练。
- 首盒1083区域步无交接；非目标0、姿态通过。独立audit_region_causal_continuity_live实执行通过（0切换），原控制watcher继续。diagnose_causal_actual_response.py实执行1082预测：高度RMSE0.015217mm/p95 0.013241/max0.328373，旧残差RMSE0.228898/max6.658553。末高度4.207375mm、核心X仍差0.284514mm、Y余量0.830214mm，尚未满足真实core10mm交接。不放宽该门。
- 首盒8RGB+4external已实际view并追加ACTUAL_REVIEW_BINDINGS；171..1199RGB采样两物画外，外视手悬停；事件图已由watcher生成但还未实际view。不能把RGB缺失当数值失败唯一原因。
- **另唯一离线screen在运行**：PID1380833/session28594，screen_causal_centered_objective.py，log/tmp/causal_centered_objective_screen.log，out causal_centered_objective_screen_r1。隔离默认关闭probe修正松弛目标（只松弛实测位移，完整补偿affine偏置），原门/几何/界限/阻尼不变。原8历史+新首/末2状态×2近似响应×2版本全40条件，尚未收齐，不采用。早期袋近似600步未到等反例保留。不得改当前冻结run或启动第二物理。
- 下一收全部screen证据、原8推2wait剩余物理/全部独立审计和真实图审，再完整关闭；新真实停滞进一步定位为progress，目标active且全范围不变。详见当前CAUSE_REPORT.md及首盒CAUSAL_ACTUAL_RESPONSE_DIAGNOSIS.json。

**本轮收尾更新**：session28594/PID1380833已正常退出，causal_centered_objective_screen_r1完整40条件：baseline两近似响应均10/10、candidate均6/10，拒绝采用（DECISION.json）。candidate每响应3历史袋/1历史盒600步未到。baseline也把真实失败盒首/末状态预测可达，恒定偏置多步响应模型证据不足，不能把单步预测准等同控制可达。原840001前袋也完整失败82.058042mm（父80.864325），原物理调度/审计继续。无离线长任务遗留；唯一物理run仍以实际STATUS+PID核查。

**实际续跑核验**：runner1375993、collector1381792均os.kill核活，当前布局840004；两个watcher核活。840001盒/袋独立审计已由runner完成，进入840004。两条8RGB4external均实际查看并追加绑定；袋可辨但513右裁/1027底裁，非目标盒171/342左裁。离线40条件已完成无待运行screen。

以下为历史记录，以本段为准。

## 2026-09-30T15:05:26.460173+00:00接续：因果接近候选完成接线验证，原8推2等待物理对照已启动

- 前一goal轮完成接线/独立审计检查为progress；最新Git备份是另项用户任务，不代表分拣进展。本轮补齐真实6命令对照、冻结并实际启动，goal active，未完成。无新合格组/转换/模型。
- **软件检查已实际结束并复核哈希**：staged_region_causal_response的默认3597帧生命周期/3原保护、24真实collector AST fixtures+16拒绝、20CLI负例+53源码实际归档、6父命令唯一新增region-causal-response开关全部过。独立审计复算16近似响应历史共2109步/208损坏拒绝；这不是真实物理成功。前轮USD core高度浮点1+几e-8导致错误拒绝已修正为1e-7读取容差，实际几何和所有原门未改；初次失败日志保留。
- 新MANIFEST冻结9来源5检查；collector SHA5c42313a6080ccbaaa58b2cb1ead94723db906c979736485eb8d9bcfc4e5eedd。PREPARATION记录创建时历史，当前冻结以MANIFEST/ACTIVATION为准。新独立audit_region_causal_live从raw前/当前q、前实际命令及归档父衰减复算因果响应和FK/core交接，不借旧固定残差报告声称通过；连续性审计调用该新审计。
- **唯一新物理run region_causal_response_groups_r1**：15:04:08UTC runner1375993/首collector1375995（840001），control1376496/event1376497；15:04:44UTC实际os.kill核活、post-AppLauncher53归档与所有冻结依赖均过，见EARLY_STARTUP_SOURCE_CHECK。PROTOCOL SHA19570ac4b418b2abbbf876e12dc07a34ad0bab2f0a63d1dd2956728b40acc09b。6case原次序840001/840004/840000/841000/840005/841002、1200推/70wait、seed0、原8推2wait完整保持，数值失败继续、运行/审计异常停止；没有训练或第二物理作业。
- **当前没有新效果结论**：仅后绕采用实际core10mm内缩目标、父拟合衰减+当前因果偏置、前命令变化阻尼；原.98规划/1.0物理腰、前侧/加载/Z保护/图像/质量门不变。父仍完整4/8、两组拒绝，前袋80.864/前盒265.039mm都失败；不得把离线16/16接近当分拣成功。前侧问题仍需独立解决。
- 下一：核新实际接近交接/持续接触与全部8+2退化、原控制/新因果动作审计及真实RGB/外视/事件图审；全部证据后使用close_region_causal_response_group/full关闭，不可提前批准数据。四族完整配对/原train-val划分、首零位/11D/指定手/非目标全过程15mm/无助推/原h10以及未调参192push3wait多seed共享模型验证仍全保留。生产采集器未改，磁盘94GiB。

以下为历史记录，以本段为准。

## 2026-09-30T14:46:55.497694+00:00接续：实际4102帧因果预测明显改善，命令变化阻尼两近似响应均8/8；接线副本已写但未验证/未物理

- 上一goal轮为progress（完整原8推2wait闭合/真实图审）；本轮新实际响应证据、完整128项近似响应对照及隔离接线准备为progress，goal active。没有新合格数据/转换/模型。原完整物理仍front_cop_route_axis_groups_r1的4/8推动+2wait、两组拒绝，不把下面离线8/8写成分拣成功。
- **差结果已收齐**：对称高度全局姿态core_top_global_pose_residual_centered_screen_r1四困难名义14/0/0/1，同时过14/0/0/0；未采用。PID1354434/session96359已正常退出。
- **好：真实记录因果响应**：audit_unloaded_tracking_dynamics.py父phase_anchor4困难拟合a，axis4困难测试显示固定bias改善瞬态但稳态较差；audit_unloaded_tracking_dynamics_bias.py只加b_t=(q_t-u_(t-1))-a*(q_(t-1)-u_(t-1))，在axis完整8push的4102筛选无载/接近帧，8条高度RMSE/p95/最大误差均下降。四困难最大0.551–0.740mm，原固定残差最大6.810–13.540mm；容易袋两条仍有2.178/2.223mm尾部，不是普适保证。父系数逐值未变，无当前条目再拟合；最后求解子步低载不保证区间无接触。两个实际审计已完成（session20380/56362结束）。
- **差：预测好不等于接近成功**：causal_response_approach_screen_r1完整32条件（8旧无载起点×2近似响应×旧核心/新因果）旧3/8→新3/8、旧4/8→新3/8。core与几何门不变。加强XY目标causal_response_centering_screen_r1完整32为3→3、3→4，袋有退化；内部腰预留.98→.998（仍原物理1.0以内）causal_response_waist_reserve_screen_r1完整32为3→4、3→4，未部署。不是全面不可达，也不采用放宽内部角界。
- **好：命令阻尼修正**：causal_command_damping_screen_r1完整32条件，同8起点/两响应，新方案两者均3/8→8/8（16条100–155步）。仅把D*(u_new-q_now)改成D*(u_new-u_prev)，避免把重力补偿当成要压小的动作；原.98rad/XYweight1/核心10mm/所有动作几何门保持。staged_causal_command_damping_probe/CHECK：24历史输入默认精确、4102公式复算4.44e-16rad、8点链式导数1.34e-10m/rad、4负例；独立100例代数检验误差4.34e-19。模型对照对象冻结/近似bias，不能代表新物理或力接触通过。
- **已准备的新采集器副本**：staged_region_causal_response（prepare_region_causal_response_stage.py已执行，禁止重跑覆盖），9文件：collector+7helpers+causal_response_parameters.json。默认关闭--region-causal-response，后绕区域才启用；实际core读取、qs[-1]前态、前命令、衰减/偏置/核心目标/命令阻尼写入日志；新增2归档预计53来源；腰预留仍.02，原前侧/等待/力/Z/加载确认不改。PREPARATION status=written_syntax_checked_not_runtime_validated，collector_wired_in_source=true、physical_started=false。**只有语法和底层探针检查，尚无CLI/生命周期/collector默认一致性或独立新实际命令审计**，不得当成已可启动。
- **下一具体工作**：在新stage完成默认生命周期/collector真实AST参数数据流与CLI负例/53源归档；特别核对qs[-1]为pre_action的q_(t-1)、previous为u_(t-1)，实际core比例与名义state.size不混用；新增独立审计不能复用旧固定残差报告声称通过。然后冻结原8推2wait/1200+70/seed0唯一新增flag，真实启动核源并完成原门/全部图审/整组关闭。该改动只后绕，前侧袋/盒仍需解决，整体目标不缩小。
- **当前没有本轮物理/训练或离线长任务**：上述screen/check和prepare均已结束，没有自动物理后继。生产collector SHAfa8abb62不变。结果集中在CAUSAL_APPROACH_REPORT.md/json；原12组4拒绝8未开始0合格、四族和train/val划分、首零位/11D/指定手/非目标15mm/无助推/h10/独立192push3wait多seed共享模型目标保持。

以下为历史记录，以本段为准。

## 2026-09-30T14:14:04.939352+00:00接续：路线轴完整4/8拒绝，力/表面运动已审，侧推可达与路径筛查进行中

- **唯一物理run已完整结束**：front_cop_route_axis_groups_r1原8推2等待，4/8推动、两wait过、两类别交换组各2/4拒绝。runner1312258/control1312298/event1312299/末collector1344275已实际退出。RESULT SHA5291cc84761ccd46b325e122244206d3a7d63ca6e3a08323d9aa28c00059647a；80原控制、8动作/连续性/COP、6×51来源、10退出码、8×8RGB4external和2×8wait全部核验。无物理/训练或自动后继。
- **突出好/差**：前盒90.712→265.039mm改善但距原区界13.308mm失败；前袋108.450→80.864mm退化；后绕盒113.524/袋81.965mm仍失败。正常和交换斜向4条过，不能掩盖困难失败。末交换斜盒150.060549/袋150.163069mm；末图已实际查看绑定，盒171起目标画外、袋513起左裁，wait稳定。
- **新真实力/表面证据**：audit_contact_surface_motion.py在当前4困难+父前袋共5条实执行，源/力变换/逐帧FK/after-action对象t+1已核。当前袋横向182样本，手相对材料点位移中位1.188mm/步、物体.481mm/步；父袋相对1.168mm/步。盒横向387样本相对.666mm/步。实际手摩擦1.0/桌.55，未改。最后子步力及归一化L1非全区间冲量/摩擦饱和/唯一原因；182/387和审计601/479定义不同。见CONTACT_SURFACE_COMPARISON.json与CONTACT_AND_REACHABILITY_REPORT.md。
- **侧推静态新证据**：固定点4×48均0；侧面区域可变+原.98rad工作界前盒6候选、其他0；假设1.30rad前袋3/前盒11/后绕两例0。1.30仅离线未部署。几何容差达标有部分迭代耗尽，.98前盒6中收敛4，1.30前袋3中1/前盒11中9，不能当物理可达。原慢速R1/R2已因完整等价R3完成而终止，保留SUPERSEDED及部分结果；R3全部20候选直线关节插值0通过。盒17条第1步目标核心重叠约1.148mm；袋3条起点已1.282mm，加载起点不能据此判定侧推不可达。需要先卸载抬手。R3的正面轴提前返回为分离下界、否则全SAT，20随机对照通过；阈值是离线探针，不改原数据质量门。
- **侧推权重探针已完整**：screen_trailing_face_region_balanced.py原.98rad/4状态48尝试，前袋0/前盒11/后绕两例0；改变软优化权重没有解决全任务。静态验收阈值/物理工作界不变。
- **新顶部核心内部全局姿态筛查已完成**：screen_core_top_global_pose.py在同4困难真实状态、16facet×3seeds/full11/.98rad；前袋/前盒/后绕盒/后绕袋名义候选31/22/9/10，当前q[t]-u[t-1]残差预测后同时过8/0/0/0。后三例分别过高、过低/工作界、过低/另一掌锚误差。真实残差不是新姿态实测响应，加载时残差未必适用卸载状态。CONTACT_REACHABILITY_SCREEN_SUMMARY.json/md记录全部失败与边界。
- **两情景共同优化已完整**：screen_core_top_global_pose_residual.py/PID1352683/session27664已正常退出，core_top_global_pose_residual_screen_r1原四状态名义23/16/0/0，同时过11/0/0/0；仍不足以采用。
- **目前唯一实际离线任务**：screen_core_top_global_pose_residual_centered.py真实PID1354434/session96359，输出core_top_global_pose_residual_centered_screen_r1/RESULT.json，log /tmp/core_top_global_pose_residual_centered.log。原单侧最低高度软惩罚改成对称高度误差，以惩罚预测过高；原四状态16facet×3seed、3..5mm检查、.98rad/其余门不变。启动后进程已核活，尚无完整结果，不得重启同目录。没有物理/训练后台或自动物理后继。下一收齐并检查各失败项；静态解之后必须卸载接近路径/全臂碰撞/实际响应验证，不能直接发给物理。

- 原12组4拒绝8未开始0合格、划分/原门不变；0新转换/模型。下一收完路径和权重筛查，静态候选须先可执行路径/全臂与物理接触验证；后绕靠核心内部持续接触仍待解决。完整四族新鲜配对、共享策略训练、未调参192push3wait多seed原h10及实际RGB仍必需。当前有完整闭合/真实图审/新接触和可达性证据，progress，goal active。

以下为历史记录，以本段为准。

## 2026-09-30T13:49UTC接续状态：路线轴四困难推0/4已实核，正常/交换斜向与等待继续

- 实际runner1312258/control1312298/event1312299仍在，collector1327818进入840000；原840000两推、841000wait、840005两推、841002wait待完成。唯一物理run front_cop_route_axis_groups_r1，51冻结源/25审计依赖不动，无训练/第二Isaac/自动后继。
- **前袋退化108.450025→80.864325mm失败，前盒改善90.711806→265.038759mm仍失败**（末Y−.186691657，距原区界13.308343mm）；后绕盒113.524129/袋81.964772mm都失败。前盒0间距guard但3次失载+10次倾斜恢复，不能放宽原门。前袋5次失载、首横向晚107帧，见前条因果边界。
- 新前盒**独立live479加载步骤实际已过**，前袋601已过；首四原动作/连续性/COP及原控制由runner/watcher继续记录。4条8RGB4external+2后绕事件实际查看绑定完成，后绕袋部分左裁/接触手画外。ACTUAL_REVIEW_BINDINGS采用保留旧条目的追加写入。
- 前条新核心内部探针与32项响应结果保持：完美跟踪8/8对8/8、实际无载残差6/8对3/8，未接线/未物理/不扩采。HANDOVER_CORE_RESERVE真实交接记录解释接触余量减少；后续可分析真实力包中的接触切向力/法向/COP迁移，不能把单帧摩擦样本当饱和或唯一原因。
- 下一先完成正在运行的原8推2wait全组/图审/闭合；本候选不能因盒改善掩盖袋退化。全目标、四族/原划分、非目标15mm/首零位/11D/无助推/h10、共享训练及独立192push3wait多seed模型验证不变；0新合格组/转换/模型，goal active。本轮为新接线物理运行和四实际结果/新接触证据，progress。

以下为历史记录，以本段为准。

## 2026-09-30T13:42UTC最新：路线轴完整物理运行，前袋108→81mm退化；无载核心落点筛查保留全部失败

- **唯一实际run front_cop_route_axis_groups_r1**：13:29:23UTC启动runner1312258/首collector1312297、control1312298/event1312299；当前实际collector1320170在840004，均核活。原8推2wait、6case次序840001/840004/840000/841000/840005/841002、1200/70帧、seed0、所有原门与release设置保持。PROTOCOL SHA9b8c006d692c214fa139e26306f1fc08d74458c424eca551625cd66d84b52425。实际post-AppLauncher51源+25依赖核验，仅新route-axis开关和两个目录参数差异。无第二Isaac/训练/自动后继，生产SHAfa8abb62不变。
- **新候选已真实接线/启动**：staged_front_cop_route_axis七源五检查冻结；collector SHA71717dc27d523f8e83890ffc64661c00edebcb18d9d0f302b9f7f929871a72d9、独立audit SHA367f7e06e6407dd7109ea7ea3f666eaa039b8e1dcb52f82b63c87434e43f6c7f。真实AST4flag组合/上一力包、18CLI负例51归档、6原命令唯一flag、8完整9352帧默认精确/原保护，独立15.736nm+各10损坏拒绝已执行。旧probe保留未接线；新stage ACTIVATION为当前启动状态。
- **差结果必须保留**：前袋108.450025→80.864325mm失败，独立实际601加载步骤全过，非目标0、姿态过。路线切换5→1、失载6→5但首横向晚107帧(661→768)，横向top_push254→191帧；实际推进下降。首后绕盒113.524129mm失败，路径不使用front候选。两条8RGB4external及后绕事件实际查看绑定；前袋遮挡/裁切、后绕多数目标画外。原FRONT_ROUTE诊断COP中间X没有实际发出，使用新增adapt_route_axis_feedback/ROUTE_AXIS_FEEDBACK_DIAGNOSIS明确区分，不误读为真实混合命令。
- **新后绕真实交接核验**：audit_rear_handover_core在已闭合phase父两例实际执行。袋名义10mm内缩只剩核心X/Y2.5/1.3mm；实际交接核心X余量4.035→首次加载2.212mm。盒8.982→4.631mm。已绑归档core_scale、真实最低点/solver和上一子步力包，不是唯一原因或新物理可达证明。
- **新未接线核心内部探针（不推广）**：staged_core_interior_probe先保持无载高度、核心内缩10mm达到后才下降，原约束保持。8原起点旧误差基线6/8、候选0/8；发现旧screen混入加载后响应，另staged_core_interior_unloaded_screen保留32项：完美后续跟踪8/8对8/8；仅实际无载残差截断后保持6/8对3/8。当前父盒/袋48/41→151/147步且能入核心，但3历史原过600步未到、原2失败仍失败，不能挑当前两点采用。零新物理/准入；旧0/8不再解释为全局不可达。下一需区分真实响应、无载优化耗时和接触迁移。
- **下一工作**：先收当前front盒/后绕袋及原正常/交换斜向与wait，完成全部审计/实际图审/完整组关闭；不停止困难条件、不启动第二采集。候选部分改善不得覆盖袋退化。前后/反斜向和更靠内持续接触仍需解决，然后四族完整新鲜pilot/转换/共享训练/未调参192push3wait多seed原h10/RGB验证。原12组4拒绝8未开始0合格不变；上一goal轮progress，本轮接线启动、真实退化和新接触/响应证据为progress，goal active。

**2026-09-30T13:47UTC追加**：840004前盒完整265.038759mm（父90.711806）改善但仍失败，末Y−.186691657、距区界13.308343mm。全程0次front_guard_lift，前3次lost_contact、后10次incipient_tilt_independent，多段仅18–25加载采样，非目标0。479mixed输出适配已核验，独立live审计待同case后绕袋完成，不能提前说已过。3条push均匀画面全部实看绑定；新盒两物可辨但手遮挡/底部裁切。后绕袋仍在实际运行。可进一步从真实contact_frame/force_torque_contact/friction核算接触力和漂移，尚无新力控/摩擦改动。

以下为历史记录，以本段为准。

## 2026-09-30T13:26UTC最终更新：阶段锚点完整4/8关闭，两组拒绝；下一路线轴候选仍未接线

- **当前没有物理/训练后台任务**：本轮runner1274366/control1275069/event1275070、末collector1306956已实际退出。完整RESULT SHA `c341b13b4486bea4d87d1e7f45c87ca66db5a8f1e59785cdfb1063d9adce5bfa`；80原控制、8实际动作/连续性/独立COP、6case×51归档、10真实child退出码、8条8RGB4external+2wait8RGB全部核验。原10条首11Dq/action0、assist0；8推非目标最大XY0。没有自动后继。
- **完整好/差结果**：正常盒150.046021/袋150.010400mm、交换斜盒150.181770/袋150.170401过；前袋108.450025、前盒90.711806、后绕盒113.456024、后绕袋81.952121mm失败。两组各2/4、等待均过、0合格训练组。前侧比横向投影明显改善但总分仍4/8，且原连续性成功盒280.925mm仍未恢复。四成功仅.010–.182mm进度裕量，旧释放裕量问题保留。
- **原因/数据**：新后绕10次失载前COP贴核心X边缘；前袋失载后3段贴核心Y边缘。前盒第2段23有效加载、核心余量最小6.079mm，335终止为原10mm间距保护，不是失载。333帧对象X前馈+1.478mm抵消微弱回退；独立诊断与guarded辅助脚本已保存，原控制未改。父8push投影+6RGB全部实看/绑定证明部分推动时目标画外；新8push均匀RGB/外部已实看，交换斜盒171起缺、交换斜袋513起左裁，数值成功不等于视觉学习已解决。
- **下一隔离候选有软件证据但未接线**：staged_front_cop_route_axis_probe仅路线主轴用COP，横向原几何目标、真实上一输出3mm界。8旧完整流9352帧默认精确/模式Z和原保护/零载通过；独立audit_front_cop_route_axis_probe不导入候选控制器，重建父XY+COP+实际混合输出，最大15.736nm、各10损坏拒绝。首3.258mm跳步失败保留并已修正。MANIFEST绑定源码/2检查；**没有collector副本/CLI接线/启动检查/新物理run**。不得复用旧phase审计直接声称新命令已审。
- **下一步**：先为轴候选完善显式默认关闭collector开关/实际AST接线/CLI与归档/独立live审计，然后完整原8推2wait物理比较；不能减少困难条件或混入终点配置改动。后绕更内部可达接触/持续力、视觉输入/终点裕量、四族新鲜完整组/转换/共享训练/独立192推3等待多seed+h10真实闭环仍未完成。原12组4拒绝8未开始0合格保持。此轮有完整闭合、实际接触/视觉证据与隔离候选执行，progress，goal继续active，非完成/阻塞。

以下为历史记录，以本段为准。

## 2026-09-30T13:18UTC最新：完整左右2/4拒绝；四困难失败原因复核，下一路线轴探针未接线

- **实际唯一物理run front_cop_phase_anchor_groups_r1**：runner1274366/control1275069/event1275070核活，collector1299580正跑840005交换斜向，之后原841002wait。PROTOCOL a1182b92不变，正在运行的冻结51源码/25审计依赖及生产采集器未改。无训练或第二Isaac，无自动后继。
- **完整左右4推2过、wait过、拒绝入库**：FRESH_LATERAL_00_RESULT已关闭，40原控制/4实际动作、连续性、独立COP/3case×51源/4×8RGB4external与wait8RGB均核验。六push全部实看绑定；当前全8推2wait尚未关闭。原12组4拒绝8未开始0合格，不改划分、无新模型。
- **突出差/好**：前袋108.450025mm、前盒90.711806mm，比横向父−2.852/4.733改善，阶段切换52→5/86→2，仍不如最早连续性160.9395失败袋/280.925成功盒。后绕盒113.456024/袋81.952121失败；正常两条任务+姿态过。前袋569/前盒150加载帧独立COP已通过，命令正确不等于任务成功。
- **新增原因证据**：盒335帧名义AABB9.069mm触发原10mm保护，333帧对象前馈X+1.478mm淹没驱动−.016/纠偏−.019mm。FIRST_PARCEL_GUARD_DIAGNOSIS可复算；非目标0、手距约39.985mm，不宣称实体碰撞。袋真实core半长67.5/63.8mm：前袋后3次失载末段Y余量约.552/−.004/.004mm；后绕10次末段X余量.253降至.005mm，多数2个加载采样即失载。归档isaac_cfg/core_scale与力包独立绑定，非唯一因果证明。
- **训练输入风险新增全量证据**：父横向8push的6RGB投影图已逐张实际查看并绑定。正常袋/盒/交换斜盒top_push目标完全画外占76.9/66.1/94.0%，后绕盒100%，都未在这些帧达标；成功片段约45–54%终点停留（均匀帧假设）。不是新模型因果或新硬门。当前后绕袋8帧可辨但左裁、主动手常画外；正常盒342起/袋171起缺目标。详见父PUSH_LEARNING_INPUT_REPORT和当前CAUSE_REPORT。
- **下一未接线探针已有执行证据**：staged_front_cop_route_axis_probe沿路线轴保留COP、横向使用原控制并相对实际输出3mm限步。首轮3.258mm跳步失败保留，修正后8完整旧输入9352帧默认精确、模式/Z/六保护/缺COP/12零载核验通过。MANIFEST physical_started=false/collector_wired=false真实有效。未完成collector接线、独立新命令审计或CLI验证，不得当已启动物理。旧观测333帧候选X约−1.020mm，对比实际+1.443mm；旧几何335仍保护，绝不写成成功避障。
- **下一动作与目标**：收840005两推+841002wait、真实图审/全部审计并关闭全run；再完善轴分工接线/独立审计后作完整物理。后绕持续接触/真实落点、四族新鲜完整配对、转换/共享训练、未调参192推3wait多seed与原h10/RGB闭环仍必需。上一目标轮有真实新证据，本轮新增后绕诊断、左右完整组闭合、探针实际执行为progress；goal active，非完成/阻塞。

**本轮追加**：840005交换斜盒已完成原任务+姿态通过并实际8RGB4external绑定，盒171..1199缺目标。路线轴探针独立复算8全流通过、最大15.736nm/各10类损坏拒绝；仍未接collector/CLI/新物理。

以下为历史记录，以本段为准。

## 2026-09-30 12:48UTC最新：横向纠偏完整4/8关闭；阶段锚点完整物理对照已启动并核源

- **唯一真实物理run front_cop_phase_anchor_groups_r1**：12:45:29UTC启动runner1274366/collector1274405（840001后绕盒先，随后前侧袋），control1275069/event1275070在STATUS实际存在、runner/collector核活之后启动。post-AppLauncher51源码快照+25审计依赖与真实参数已核验，LIVE_STARTUP_SOURCE_CHECK保存；实际CLI相较同case父仅front_cop_phase_anchor新True和两个目录路径不同。原8推2wait、6case顺序840001/840004/840000/841000/840005/841002、环境seed0/1200+70帧、release确认开启均保留。PROTOCOL SHAa1182b926836b45730c69e6b2d4b2904238a07680763ee310399bbea4f575596。51源仅隔离collector和front_cop_route相较父不同，生产SHAfa8abb62未改。无第二Isaac/训练/自动后继，磁盘约99GiB。当前新run尚无任务质量结论。
- **父front_cop_transverse_groups_r1完整关闭4/8+2wait**：两组各2/4、均拒绝；80原控制、8实际动作/连续性/独立COP、6case×51归档、10实际child退出码、8×8RGB+4external/两wait8RGB和后绕事件已实际查看绑定。runner1239087/control1239122/event1239123、末collector1271342均实际退出。RESULT SHA30b535bd16f4b6321fc78b741f5f564e59ac024f8e67bfb6c2b6e63c7d202857。8推非目标最大XY实核全0，10条首11Dq/action0、assist0。原12组4拒绝8未开始0合格不变，无新训练组/转换/模型。
- **完整好/差结果**：正常盒150.229365mm/袋150.013469mm、交换斜盒150.145963mm/袋150.395170mm过；后绕盒112.216664mm/袋81.944628mm、前袋−2.851754mm/前盒4.733257mm失败。袋852/盒1024带载步骤独立COP全过、推进抵消消失却转向反复26/43次，旧锚进入横向时X纠偏与目标反向，阶段位移/真实COP诊断详见父CAUSE_REPORT/FRONT_FAILURE_COMPARISON。四默认成功保留并不解决困难任务；父仍比早期连续性5/8少一条原成功盒。
- **终点裕量新全量证据**：audit_expert_release_margins对父8push实际执行，4成功均由confirmed_original_target_position在内部160mm/205mm目标前释放，150mm进度余量仅.013469/.229365/.395170/.145963mm；末10区域余量68.076/103.614/28.742/45.036mm。EXPERT_RELEASE_MARGIN_AUDIT记录无新门/无学习因果声明。新阶段对照暂保留同释放参数，之后单独比较专家裕量，不能混改或改原质量评分。
- **候选已执行而非口头**：staged_front_cop_phase_anchor实际7源/5报告/MANIFEST冻结，collector SHAad6828893ebf46be1364799919e28f23057994098af2088256670ddc1645208e，独立audit SHA64dbccd5051bca81cbab2be05849cc3b5577d86c40ae49fff88ae7b7575b4932。六完整历史输入6954帧、实际AST接线、16CLI负例51快照、独立复算最大7.051nm与每流8损坏拒绝、六实际命令唯一flag差异均已过。prepare已执行、protocol比较断言通过后才launch；MANIFEST.physical_started=false是冻结时字段，当前ACTIVATION.json/README及真实STATUS说明已启动。没有改冻结运行源。原probe未覆写。
- **图审/数据风险仍保留**：本轮补齐末袋8RGB4external（可辨，513起左裁/手遮挡，盒全可见）及末wait8RGB稳定空桌。正常盒342起/正常袋171起/交换斜盒171起目标缺失；不能把数值成功当视觉学习完成。逐帧全可见不是新增门，当前不改相机。
- **下一动作与完整目标**：收新8推2wait真实效果，重点看两front阶段锚点是否减少反向纠偏/间距恢复，同时保留后绕/默认路径全部结果；原审计、完整交换组和实际画面均必需。新首840001盒仍是后绕，不能把它当phase方法直接测试。之后仍要解决后绕645/669帧下降与偏心接触、前后/反斜向、终点裕量和视觉输入，再新鲜pilot四族完整配对/转换/共享训练/独立192push+3wait多seed原h10模型实测。上一goal轮progress，本轮全父闭合/新裕量证据/新完整物理实际启动核源为progress；goal active，非完成/阻塞。

以下为历史记录，以本段为准。

## 2026-09-30 12:38UTC最新：左右完整2/4拒绝；阶段锚点已接线/独立审计冻结，当前最后斜向case仍运行

- **当前唯一真实物理run front_cop_transverse_groups_r1**：runner1239087/control1239122/event1239123实际核活，collector1264126在840005（12:33:11启动）。840000正常盒/袋完成，841000普通wait完成；最后840005两推→841002wait仍需收齐。当前已做6条8RGB+4external、2后绕8事件和第一wait8RGB实际图审绑定；不要把仍未实际查看的末两条/末wait算完成。无第二Isaac/训练/新自动队列，磁盘99GiB。上轮progress，本轮完整左右关闭+接线审计为progress，goal active。
- **完整左右组正式关闭2/4+wait过**：FRESH_LATERAL_00_RESULT实际40控制/4原动作连续性独立COP/3case×51来源哈希及全部raw图审核验。正常盒150.229365mm、袋150.013469mm通过，交换盒112.216664mm/袋−2.851754mm失败，整组拒绝；首11D q/action0与assist0均过。普通wait双掌2.098291mm、腰约3.087e-9rad。正常盒342起/袋171起目标采样缺失，成功贴150mm门，尚无视觉可学或新模型证明。
- **下一候选已从probe推进到隔离接线staged_front_cop_phase_anchor**：7源冻结，collector SHAad6828893ebf46be1364799919e28f23057994098af2088256670ddc1645208e。默认off --front-cop-phase-anchor要求front-cop-slip-following，只原front route stage改变时清COP锚/上一世界锚，再以当前实测带载COP建锚；保留上个已发XY命令/全部原保护/Z/释放/参数。父与probe保留，当前运行源未改，生产SHAfa8abb62不变。MANIFEST.collector_wired=true/physical_started=false，尚未执行prepare，未新建物理run。
- **已执行完整必要检查**：check_front_cop_phase_anchor_wiring实际跑6完整历史输入6954帧（默认同投影父输出精确，固定旧观测原mode/Z与保护/12零载/缺COP界保持），实际collector AST3开关组合和上帧实际包/update调用，独立COP误差1.648nm；prelaunch16负例与实际51源码快照字节验证；audit_front_cop_phase_anchor_live独立重建真实包/姿态/通道阶段/reset/锚/前馈/正交纠偏/限步命令，全部6流最大7.051nm，每流8损坏均拒绝。新增check_front_cop_phase_protocol_inputs对全部6真实父命令（8推2wait）pre-AppLauncher解析，唯一差异front_cop_phase_anchor False→True、无输出目录/AppLauncher。五报告全绑MANIFEST，checker/auditor源冻结；首prelaunch缺已有EULA环境报EOF日志保留，按既有env设置后通过，未启动第二物理。
- **软件边界/失败仍明确**：旧父袋23帧lead暂超30mm/max30.7064，新两历史流反事实509/761clip，COUNTERFACTUAL_LEAD_SUMMARY保留；固定旧观测检查不预测新物理成功。reset会遗忘滑移，旧命令仍有滞后风险，后绕路径也没改变。准备好prepare/run/close_front_cop_phase_anchor_{run/groups/group/full}工具，prepare要求当前完整RESULT+8push2wait图审及结束进程，复制相同6布局/原所有参数只新增flag；当前未排第二物理。
- **后绕新证据未丢**：当前两个后绕REAR_PHASE_MOTION_AUDIT逐1199实际位移转移与原始力包姿态精确对齐；top_descend盒645/袋669帧净运动约0，top_push盒101转移分拣50.616mm、袋82转移42.216mm。最初rear_push盒深度95.761/分拣63.715、袋67.739/40.317mm仍是原避障，不删。LOADED_CONTACT_OFFSETS以前一末子步匹配当前pre-action，盒102/袋62样本，COP相对目标的**世界XY**中位盒−63.975/−32.252mm、袋−56.065/+47.734mm；不是局部XY/力积分或唯一原因证明。REAR_CONTACT_RECHECK和CAUSE_REPORT追加绑定。已读旧soft_center与center_then_descend离线均4/6失败记录，不重复盲目居中；旧未投影后绕COP不接线。
- **下一工作/完整目标**：收完当前末两推与末wait、实际查看、关两完整组及全run，证据允许后再启动阶段锚点同范围新物理。之后仍要解决后绕持续接触、前后/反斜向、终点裕量/相机输入风险，再新鲜pilot完整四族配对准入/转换/共享训练/未调参192push+3wait多seed原h10实际闭环。原12组4拒绝8未开始0合格，划分原样；没有合格新训练组/转换/新模型。

**12:39UTC追加实核**：840005盒已完成150.145963mm原任务/姿态通过，8RGB+4external实际查看并绑定（盒171起缺失；袋可辨513右裁）。现已7条push实际图审，collector1264126继续最后840005袋，之后841002wait；全run仍未完整，case级动作审计在袋写完后由runner执行。

以下为历史记录，以本段为准。

## 2026-09-30 12:26UTC最新：横向反馈两前侧仍失败；定位旧锚跨阶段造成反向纠偏，隔离重建探针通过6全输入

- **唯一真实run仍front_cop_transverse_groups_r1**：runner1239087/control1239122/event1239123实际核活；840001/840004四困难推已完成均失败，12:23:20转840000正常组、collector1254967实际核活。第三case实际51源码快照核验；全部原8推2wait保留，剩正常两推→841000wait→840005交换斜两推→841002wait，无第二物理/训练/自动后继。生产collector SHAfa8abb62不变，磁盘约100GiB。PARTIAL_REVIEW_STATUS保存实核，不能用旧STATUS/PID推断后续仍活。
- **好处有限/差结果突出**：前袋原160.9395失败→未投影−.37156→横向投影−2.851754mm失败；前盒原280.925035通过→未投影−.23654→横向投影4.733257mm失败。新带载袋852/盒1024帧的独立COP、原实际动作/连续性全过，纠偏沿推进分量约0、平行命令增量约1mm、无lead限幅，确实消除旧长期静止，但没完成分拣。两个未修改后绕：交换盒112.216664mm、斜袋81.944628mm均失败，不归因为front改动。四推非目标最大XY均0、首11Dq/action0、assist0。40原控制全通过，四条8RGB+4external与两后绕8事件实际查看绑定；仍0合格新组。
- **新增独立真实阶段证据**：diagnose_front_route_feedback.py由trace/姿态独立复算AABB间距，并把1199个t→t+1位移按命令阶段相加精确回收首末，保存每次阶段变化、旧锚、命令和实际位移。袋26横向段各5–6帧/52切换、首657；盒43横向段6–15帧/86切换、首182。所有26/43次进入横向都保留旧COP锚且X纠偏与X目标相反，袋+3.286..3.926mm、盒+.657..2.596mm。横向段净X/Y袋+35.995/+13.547mm、盒+80.209/−23.077mm，前移推动段袋−144.996/−15.855、盒−136.438/+18.268mm，解释间距恢复反复抵消横向进展；机制有实录支持，不证明重建锚点物理必成功。两EP的FRONT_ROUTE_FEEDBACK_DIAGNOSIS、COP_DRIVE_BALANCE_DIAGNOSIS与run/FRONT_FAILURE_COMPARISON/CAUSE_REPORT已保存。
- **真实画面**：前袋8帧可辨手遮挡、513右裁/后期底边，前盒8帧可辨手盖顶；不能统一归于看不见。后绕盒171/513/685/856/1199缺失，342仅右缘碎片、1027右裁；交接173周边缺失，233盒手可见。后绕袋全部可辨、多数左裁，交接140主动手多画外。视觉审查完成不是可学证明，也没新增逐帧全可见门。
- **隔离未接线staged_front_cop_phase_anchor_probe**：仅复制两源，显式默认reset_cop_on_route_change=False。开启时父路线stage变化才清局部锚/上一世界锚，用当前真实带载COP重建；保持之前已发命令、原3mm界及全部保护/Z/释放。check_front_cop_phase_anchor_probe已执行6完整历史流6954帧：父连续性袋1199/旧12mm盒959/未投影袋盒各1199/当前投影袋盒各1199；默认同投影父输出精确一致，开启同观测模式/Z不变，六例各6保护实际触发+缺COP回退+12零载不推，新两例52/86切换重建。最大步2.082/2.502mm；切换残余纠偏<.15nm。首列表abs类型错和0.095nm容差失败日志保留；只改检查器列表操作与10nm复算容差，未改物理门。MANIFEST/README绑定源、检查与失败反例；无collector接线/物理/后继队列，不能说已解决。旧父袋23帧限步滞后lead暂超30mm/max30.7064；其余历史流也有clip，新两流509/761clip（固定历史振荡观测下），COUNTERFACTUAL_LEAD_SUMMARY完整保留，不当真实新动力学。
- **下一动作**：先完成当前余下4push2wait和实际图审/完整两交换组关闭，保留所有失败；再根据完整结果为阶段重建候选做真实collector接线、独立审计、源码冻结和同范围物理对照。后绕持续接触、前后/反斜向、终点裕量和视觉输入问题仍要解决；不得靠放宽间距/质量或丢掉困难布局过关。原12组4拒绝8未开始0合格、划分不变，独立192push+3wait、多seed/h10模型验证未动；没有合格新数据/转换/新模型。此前goal轮有实际启动/核源进展；本轮完成4真实失败图审、两类新机制证据、6流隔离探针，分类progress，goal active。

以下为历史记录，以本段为准。

## 2026-09-30 12:06UTC最新：未投影COP完整4/8拒绝；横向纠偏完整对照实际启动

- **当前唯一物理run front_cop_transverse_groups_r1**：12:04:56UTC启动runner1239087/collector1239120（840001交换盒先，后交换袋）、control1239122/event1239123，12:06:18实际post-AppLauncher51源码+25冻结审计依赖核验，真实/proc核活。PROTOCOL SHA60fc50199ca900438d2392e3b0735f24a6a4956bd43241c3e907c7be96537903。全部原8推2wait/1200+70/envseed0保持，顺序显式前置问题布局840001/840004，然后840000/841000/840005/841002。每case实际CLI跟未投影父仅目录路径不同；51源中仅隔离collector投影元数据和contact_slip_following数学变化，无额外释放配置改变。生产SHAfa8abb62不变，无训练/第二Isaac，磁盘101GiB。
- **上一front_cop_groups_r1完整关闭4/8+2wait**：左右2/4、斜向2/4，均拒绝；全部原runner1204476/control1204512/event1204513及collector已实际退出。80原控制、8动作/连续性/COP独立审计、6case×51归档、10实际child退出码、8×8RGB+4external与2×8wait实际查看绑定；RESULT/CAUSE_REPORT/两GROUP_RESULT齐全。10条首11D q/action0、assist0；8推非目标最大XY均0，仍不合格。原5/8→4/8退化，不能总分掩盖两front模式失效。
- **完整坏结果与好处界限**：交换前袋160.9395→−.371560mm，原成功斜盒280.9250→−.236541mm，1075/1093真实带载帧独立COP审计全过，约5N载荷下纠偏反向分量/推进中位.999947/1.000147，0个30mm限幅。证明实际命令被抵消，不证明投影后一定成功。四个未启用front的原成功条件均保留；另两后绕盒120.771891、袋81.657177mm仍失败，没有解决后绕。后绕袋与最后两推实际图审本轮补齐；后绕袋可辨但左裁，交换斜盒171后缺失、交换斜袋513起左裁；等待稳定空桌。
- **新候选准备/证据**：staged_front_cop_transverse7源、4检查和独立审计已冻结，四完整失败输入4556帧/原保护/零载/15CLI/51归档/独立复算<5nm+6损坏各拒绝详见前条交接。source MANIFEST.physical_started=false表示创建/冻结时状态，不能据此误报未运行；ACTIVATION.json及实际run STATUS为当前状态。prepare/run/close工具齐备；运行源不能中途改。旧未投影后绕probe保留do_not_wire，未推广。
- **终点裕量有现成可对照配置，未混入当前**：review_release_margin_config.py实际执行pre-AppLauncher参数解析，移除--expert-top-confirmed-release只改变该布尔True→False；原ready_to_release本已有160mm推进/205mm区域内部目标，左右/跨侧四起点函数检查较原门多5–10mm。无需写新控制器、无需改原150mm/200mm/h10评分。关闭确认后不再于恢复模式提前释放，可能影响末端恢复/稳定，必须另行完整物理；现阶段两轮COP参数均保持确认开启。RELEASE_MARGIN_CONFIG_REVIEW.json/md绑定源并明确无新物理/无准入。
- **下一动作/整体目标仍完整**：收当前原两交换组及两wait，验证两front推进是否恢复、默认路径/后绕是否退化、原非目标/姿态/动作和实际图审。随后仍要解决后绕持续接触与前后/反斜向、终点裕量和图像可学性，再生产接线/重新冻结profile及新鲜pilot合同→完整四族配对扩采→转换→共享策略训练→未调参192push+3wait多seed原h10实际闭环图审。原12组仍4拒绝/8未开始/0合格，分组划分不动，无合格新训练组/转换/新模型。前一goal轮progress；本轮完整父关闭、终点配置可行性检查、实际启动并核源为progress，goal active，不是完成/阻塞。

以下为历史记录，以本段为准。

**11:53UTC追加实核**：front run现已进入840005，collector1228945实际存活；840004后绕袋完整推进81.657177mm失败，其均匀/事件实际图审待做。840004前侧盒独立COP1093帧全部通过，前6推60原控制无失败。剩840005两推+841002wait及最后3push图审/全run闭合。

## 2026-09-30 11:51UTC接续：前侧反馈使袋/盒同时停滞；定位纠偏抵消推进，横向投影候选已备但未排物理

- **当前真实run仍front_cop_groups_r1**：runner1204476/control1204512/event1204513实际核活，collector1220993在840004后绕袋step1020（若后续推进以STATUS+真实ps为准），其后原840005交换斜向两推+841002wait仍要完成。完整run尚未关闭，不重启/覆盖当前失败、不提前截掉剩余条件。51源/25审计依赖核冻结，生产collector不变，磁盘约101GiB，无训练/第二Isaac。上一goal轮为progress；本轮完整左右关闭、两个真实反例/代数抵消定位、新候选接线检查为progress，goal active。
- **完整左右组已严格关闭2/4+wait过**：FRESH_LATERAL_00_RESULT，40原控制+4实际动作/连续性/独立COP+3case×51档案，4条8RGB+4external与wait8RGB真实查看绑定；全部5首11D q/action0、assist0，四推非目标最大XY0，0合格组。正常盒150.210977mm/袋150.027357mm过；后绕交换盒120.771891mm失败（该路径不启用front，不能归为新算法改善）；前侧交换袋−.371560mm失败。
- **必须highlight的退化1：交换袋160.939500→−.371560mm**（父也未到区）。当前1075真实带载覆盖由audit_front_cop_live独立复算全部过；中位载荷4.999986N，纠偏沿推进反向分量/推进.999947101，实际平行命令增量中位.0574微米，reference lead中位.550952mm，0帧30mm限幅。927带载帧到下一观测位移<1微米。只是描述性分组，不改门。COP_DRIVE_BALANCE_DIAGNOSIS与diagnose_cop_drive_balance.py绑定全实录。
- **必须highlight的退化2：原成功斜向盒280.925035→−.236541mm**。1093带载覆盖，中位载荷4.999951N，反向纠偏/推进1.000147321，平行命令增量绝对值中位.1498微米、reference lead中位.263872mm，0限幅；871带载帧下一目标移动<1微米。姿态支持/直立、非目标0，但任务失败。已完整quality+pose+代数诊断/实际8RGB4external绑定；该case两任务收齐后runner才执行独立COP/动作审计，不能提前说整case通过。两类别都说明原沿推进方向COP锚点恢复会抵消推进；数学抵消有直接证据，但修正的物理成功仍未证明。
- **当前已做5条push实际图审**：正常盒342起缺失、正常袋171起缺失、交换盒171起两物缺失；交换盒161..169交接164图像无目标，224盒/右手可见。交换袋8帧可辨但171后手覆盖且姿态几乎不变，盒画外；斜向盒8帧可辨、手遮挡、袋右裁，长期停滞。后两失败不能统一归咎于看不见。后绕袋及最后两推图审还待完成。
- **新staged_front_cop_transverse已接线但未物理**：基于上一front隔离7源码，唯一数学变化为纠偏投影到当前目标方向的垂直方向，新增feedback_projection元数据和raw/removed纠偏记录；实测刚体前馈、1mm推进/.05横向增益/3mm限步/30mm期望lead、原保护/Z/目标保持。原两个失败物理记录完整保留。MANIFEST冻结7源+4检查+独立审计SHA，physical_started=false。prepare_front_cop_transverse_run/run_front_cop_transverse_groups/close_front_cop_transverse_group/full已准备，prepare明确要求当前front全RESULT及退出后才可创建新run，没有自动队列。
- **新候选已执行4完整失败输入4556帧**：父袋1199、旧12mm盒959、当前停滞袋1199/盒1199；默认关闭与原当前同profile精确，开启固定旧观测mode/Z一致；431/857/1075/1093实载覆盖，纠偏与推进正交、3mm界。各例原6保护实际触发、缺COP回父、12零载不推，真实collectorAST验证类选择/投影元数据/上一真实包/update，独立COP误差<1e-7m、15CLI拒绝/51快照，独立audit_front_cop_transverse_live全部命令<5nm且6损坏各拒绝。新增盒失败后才有理由由3例扩至4例；原日志保留。COUNTERFACTUAL_LEAD_SUMMARY：旧父袋134clip/23暂超max30.706mm；旧盒822clip；新停滞袋1020clip/盒1040clip，后三max30mm。固定旧静止观测会积累到限幅，不代表实际新动力学或成功。
- **新增后绕逐阶段核算（不要误解为取消绕行）**：audit_rear_phase_motion.py/两run各2例REAR_PHASE_MOTION_AUDIT、Xrun/REAR_PHASE_COMPARISON。1199真实t→t+1位移按实际发出模式分解，总和精确回收首末，post-action包对齐。最初rear_push盒约95.5mm深度/65.0mm分拣、袋67.7mm深度/40.3mm分拣，本来就是原20mm后方避障目标，不可据此删掉/降余量。袋父top_push净X−14.755/Y+44.561mm，X候选+.284/+42.120mm，总深度多主要是后来少往回走；top_descend667/673帧净运动0。盒下降642/647帧净运动近0，top_push分拣56.298→49.669mm；X末1199无下一帧，故该核算100push转移vs日志101push帧，非矛盾。
- **未接线后绕探针不推广**：staged_region_cop_slip_probe基于continuity+未投影COP，2mmXY界、无额外X驱动；20真实推动段188帧父命令<9nm、默认精确/原3保护/12零载/缺COP检查过，盒100/袋62实载覆盖，袋4帧限步后暂超30mm/max33.838。只重建各段真实父起点，不是整条新物理。当前front两个真实反例后已在README/MANIFEST明确do_not_wire_unprojected_feedback_after_real_front_stall，不以软件过推广同一错误。
- **下一步/原目标**：先收当前余下原完整对照及图审，实际关闭全run并拒绝未投影形式；再对横向投影候选做同完整物理比较，任何局部改善仍需原前后/反斜向全组/旧困难盒、全部四族与独立模型验证。后绕可达/持续载荷、过小终点裕量、视觉可学性仍待解决；原12组4拒绝/8未开始/0合格，全划分/独立192push+3wait多seed+h10不动；没有新合格训练组/转换/新模型。

以下为历史记录，以本段为准。

## 2026-09-30 11:27UTC最新：X跟随完整仍5/8拒绝；前侧真实COP反馈完整对照已启动

- **当前唯一物理run front_cop_groups_r1**：11:24:05UTC启动runner1204476/collector1204509（840000正常首盒）、control1204512/event1204513，11:27真实/proc核活。post-AppLauncher实际51份源码归档与新开关已核验。PROTOCOL SHA e73f12aced4f1ae46e1355f6731ba782646df3790942b0e5911a4aa62da7ab62，继承已关闭region_continuity原8推+2普通wait/1200+70帧/envseed0，6实际命令仅路径和--front-cop-slip-following增加。没有第二Isaac/训练；生产collector SHA fa8abb62不变。watcher在STATUS实际存在之后启动，无旧启动竞态。当前启动不是成功证据。
- **上一region_x_follow_groups_r1完整关闭5/8+2wait**：两完整组左右2/4、斜向3/4，均拒绝。原runner1169769/control1170776/event1170777及全部collector已经实际结束；80原控制、8实际动作/连续性/X独立审计、6case×49源码、10子进程退出码、8×8RGB+4external及2×8wait实际查看并绑定，RESULT/CAUSE_REPORT/两group RESULT齐全。全部首11D q/action0、assist0，0新合格组。非目标并非全零：后绕袋使盒最大XY1.191425mm，其余7推为0，仍在原15mm门内。
- **X跟随的负面结果**：交换盒118.356870→113.172334mm，最大tilt .064450→.056490rad但10次恢复全为倾斜；后绕袋84.063763→82.270491mm，top_push82→98，有实测COP末子步样本62→76，仍10失载。袋总深度X62.847→76.562mm，分拣推进反降。compare_rear_x_follow.py/REAR_CONTACT_COMPARISON.json可重建两完整实录；其中pre-action配previous-last-substep与SIGNED_CONTACT_MOMENTS的post-action统计是不同口径，不能混为相同均值或完整积分。X候选不合并入下一对照。
- **新front候选staged_front_cop_slip**：已接线显式默认关闭开关；基础为region_continuity，不含失败X跟随。仅原front路线当前真实有载top_push，以当前/过去COP局部锚+实测刚体运动补偿、1mm驱动/.05纠偏/3mm步长覆盖XY；期望reference lead30mm，限步后可能暂超并显式记录。原控制先执行，Z/倾斜/失载/通道/非目标/释放/关节/质量保持；原目标距离不缩短。缺COP或低载交回原控制，非push清锚。7源码冻结，完整run准备/执行/组关闭工具分别prepare_front_cop_run/run_front_cop_groups/close_front_cop_group/full。
- **front已执行软件检查**：两完整失败实录（交换前袋1199帧、旧12mm停滞盒959帧）共2158帧，默认关闭精确一致；开启固定旧观测时mode/Z一致，431/857实载覆盖、3mm界；两类各6原保护确实触发、12零载不推、缺COP不覆盖。真实collectorAST类选择/前接触包/update调用、独立COP误差1.092nm、15CLI负例/51实际快照、独立audit_front_cop_live全载荷命令<5nm+6篡改各拒绝。原1e-10m浮点比对失败与缺step fixture日志保留，修复仅重建容差/fixture，不改物理门。软件检查不是新物理成功。
- **成功示范贴门的数据风险**：新增audit_expert_release_margins.py对完整父/当前8推原门复算。两轮5成功都由confirmed_original_target_position早于原ready_to_release的160mm/205mm内部目标裕量释放；当前4成功推进余量仅.070153/.185168/.487050/.303170mm，正常斜盒末10区间余量2.807561mm；父4推进余量.0386–.2643mm。属于可学性/容错风险，尚无模型因果证据。之后应单独对照保留专家内部裕量，原150mm/200mm/h10评分不改；没有把该改动混入正在运行的front对照。旧ConfirmedPositionRelease文档称未接线已过时，实际top_contact_bypass明确导入并启用；只以实际代码/记录为准，未编辑冻结源。
- **图像风险继续保留**：当前正常盒342起/正常袋171起/交换盒171起/交换斜盒171起目标采样缺失；前侧交换袋可辨但手遮挡/底裁。后绕袋0..1027可辨且左裁，1199缺失；137..145接近事件袋可辨但主动手多数画外，不能用RGB证明接触力。交换斜袋513起左裁，仍可辨。所有实际view和raw/图片哈希绑定已做，未新增逐帧完整可见硬门。
- **目标与下一动作**：先收当前完整front实际干预及全部原审计、难例、默认路径退化和图审；若有改善仍须原前后/反斜向完整组和旧困难盒验证，不能拿唯一前袋改善代表多样摆放解决。后绕接触/倾斜、终点裕量和视觉可学性仍未解决。原12组4完整拒绝/8未开始/0合格，全四族/split/独立192push+3wait多seed+h10保留。无新合格训练组/转换/模型。前一主goal轮为progress；本轮完整X关闭、新数据裕量审计、front真实启动/核源为progress，goal active，不称整体完成。

以下为历史记录，以本段为准。

## 2026-09-30 10:44UTC最新：XY连续性完整仍5/8；固定X锚点残留，下一完整X跟随对照已实际启动

- **当前唯一物理run region_x_follow_groups_r1**：10:42:40UTC runner1169769/collector1169810（840000首盒）已启动，10:43:59真实ps核活及post-AppLauncher49源码归档/冻结依赖全过，实际CLI跟父仅out_dir/layout文件路径不同。control1170776/event1170777已核活。两个最初watcher1169770/1169771抢在STATUS生成前退出；原错误日志/空执行记录保存为*_STARTUP_RACE_R0，核活真实runner后仅重启watcher，未重启/重采物理。PROTOCOL SHA d64334274bb724c8610397a340571a1976cb6b229d7d43ef2a3da134c3a6828c。完整原左右/斜向8推2普通wait、1200/70帧/envseed0不变；无第二物理/训练，生产源不变，磁盘104GiB。
- **父region_continuity_groups_r1已完整关闭5/8+2wait**：左右2/4、斜向3/4，0合格组，和残差父总成绩相同。原runner1135378/control1136034/event1136035及所有collector已实际结束。close_region_continuity_full.py/两组RESULT/RESULT/CAUSE_REPORT齐全；80原控制、8实际动作+XY切换、6case×49档案、10实际child退出码、8条8RGB+4external和2wait各8RGB实际查看/绑定。全10首11D q/action0/assist0，8推非目标最大XY0。没有成功半组入库。
- **交换盒好/差**：165真实交接，gap3.585mm/另一掌1.844mm，推进65.060→118.357mm但失败。max tilt .064450（原.20姿态过），10恢复中7倾斜/3丢载；原.03专家恢复门不放宽。真实COP局部X中位−66.017mm（半宽70mm）vs几何捕获−58.059mm；97实载末子步手yaw力矩均正，中位+.137058Nm，桌面约−.136015Nm。边缘偏心和旋转一致，但末子步不能当完整冲量/唯一因果。SIGNED_CONTACT_MOMENTS、TOP_CONTACT_BOUT_DIAGNOSIS及实际事件图审保存。
- **后绕袋连续性已生效但任务仍失败**：140交接，10press→push下一帧有载由父1/10→9/10；原6–10mm瞬时X回退消失，实际独立切换审计过。top_push70→82帧，推进75.826→84.064mm；10次lost_contact，push段44/7/4/4/4/4/4/3/4/4。实际max tilt .008725，非目标0，仍未达目标区。LOADED_TRANSITION_COMPARISON以两完整实录绑定，compare_region_loaded_transitions.py可重建。Z切换向下约.5mm，不是猜测的向上数毫米撤载，不据猜测改Z。
- **残留X锚点机制**：后绕袋world-X锚点始终.5909597715m，重新按压surface X逐渐超过.594m，后续push每帧−2mm回旧锚点；实载COP局部X约−67.4mm/距袋X边7.5mm，仅1–5实载样本就丢载。局部位移改善不等于解决；新假设需物理干预验证，不能称唯一原因。前侧交换袋本轮160.939mm同样未到+.20目标，另一路径仍失败。
- **当前隔离候选staged_region_contact_x_follow**：只selected-region+hold-established-x，在每次真实载荷确认进入push时捕获上一发送X和当前物体X，随后补偿观测物体X平移，原2mm X限步/Y/Z/倾斜/失载/释放均保持。_start_recontact清该锚，默认路径不变。不补偿完整物体旋转，也不解决front。collector元数据显式region_push_x_reference，stage所有5源与6检查MANIFEST已冻结；physical_started_at_manifest_creation=false是创建时状态，当前实际run见上。
- **候选已执行软件检查**：盒/袋各10真实press→push fixture重建父命令，候选按压X连续、实测1mm平移跟随、每次重新接触锚重捕获、零载12不推、倾斜/失载/释放三保护输出精确相同；默认3597帧回放精确相同，3实际起点理想FK交接/低载门、真实collectorAST动作及当前previous-command、2FK差异拒绝、8CLI负例、49实际归档字节核验通过。check_region_contact_x_follow、check_region_x_follow_{wiring,lifecycle,prelaunch}。独立audit_region_x_follow_live.py先连续性/残差/动作审计再逐region push复算X锚/目标平移/2mm步；2bout有效+6损坏fixture通过。未用软件成绩当物理成功。
- **两个居中候选均未采用**：staged_region_soft_center权重.35，6历史起点均保留/4到达2失败，当前盒X仅改善.054mm；staged_region_center_then_descend首60步保持无载高度再下降，同4/6，旧袋X−63.2→−43.6mm但当前盒反变−59.2mm/77步（基线−58.1/47步）。全部记录/README/MANIFEST保留，不因旧袋单例上物理。固定物体+旧残差不是真实动力学或不可达证明。
- **前侧COP滑移候选staged_contact_slip_following仍未接线**：本轮补交接其前轮R2工作：实际COP局部锚+物体平移+1mm drive+0.05纠偏、期望30mm lead及3mm slew，限步后可暂超30mm并显式记录。完整前袋429输出/258clip/66超界max30.699mm、旧12mm失败盒857输出/763clip/max30mm；保留R1新增10mmCOP适用条件导致盒全部排除的反例，R2去掉此新增非原门。只反事实旧状态，不能推断新运动/力/成功，未排物理。
- **画面风险保持**：父正常盒513后/正常袋171后/交换盒171后/交换斜盒171后采样目标缺失；失败前袋与后绕袋可辨但裁切/手遮挡，交换斜袋513后左裁；两wait稳定。所有8+2实际图审已完成，数值通过不保证模型可学，不新增逐帧可见硬门。
- **整体目标/下一步**：原12组仍4完整拒绝/8未开始/0合格，独立192push+3wait多seed/h10未触碰。无合格新训练组/转换/新模型。收当前完整X对照，重点真实COP/持续载荷/盒倾斜及默认退化；新close_region_x_follow_group/full已备，不能提前关闭。通过专家与完整配对准入后才全族新鲜扩采→转换→共享RGB+11D训练→独立多seed模型闭环与实际画面。前一主goal轮progress；本轮完整8+2关闭、真实载荷残留定位、候选反例/接线与新实际启动是progress，goal active。

以下为历史记录，以本段为准。

## 2026-09-30 10:04UTC最新：残差完整5/8，持续接触问题明确；命令连续性完整对照已启动

- **当前唯一物理run region_continuity_groups_r1**：10:02:32UTC runner1135378/collector1135415（840000首盒）实际启动，control1136034/event1136035核活。10:03:32 post-AppLauncher49源档案及实际args核验通过，跟父仅output/layout文件位置不同。完整原左右/斜向8推+841000/841002普通wait、1200/70帧/envseed0。当前新候选49源和审计依赖全部冻结，生产collector不变，无训练。
- **父tracking_region_groups_r1完整关闭5/8+2wait**：左右2/4、斜向3/4，0完整合格组，和旧区域版总数一样。原runner1097061/control1098038/event1098039及collector1120969均结束。8×8RGB+4external及2×8wait实际查看/绑定，80控制逻辑检查（含下述R2更正）、8残差动作、6case49归档、10实际child exitcodes闭合；RESULT/CAUSE_REPORT/两GROUP_RESULT完成。全部首11D q/action0、assist0；非目标各推0，无转换/新模型。
- **后绕袋的真实好/差**：840004袋40QP（100..139）后140交接gap4.747mm，142实载1.800N、143为3.417N、144开始top_push3.695N；没有区域abort。原先2QP就越界的接近已局部改善。但终态推进75.826mm失败，10次lost_contact；top_descend678/top_lift273/top_push70帧。首次144..186共43push，其后9次只有3帧。每次后9个press→push X命令回退6.339–9.642mm、下一帧载荷全0，随后原失载门启动。实际8RGB与140事件均查看，目标可辨/左裁，不能解释为单纯画外。
- **原因定位与候选**：TopContact在真实载荷确认后把command重置为实测tip；按压时约9mm跟踪差使切换撤掉此前XY命令。新staged_region_handover_continuity仅对selected-region用上一发送XY初始化push，仍X2mm/Y3mm推进，Z保持原tip初始化/1mm限幅，原真实load确认不变。另继承未安装候选的线性规划高度3.5→4.2mm，原实测3mm保护/3–5mm交接/另一掌<2mm不变，以应对交换盒165..167交接错过。这是两项明确变更，不称单变量。新collector元数据已正确标4.2mm及press_push_xy_initialization，MANIFEST绑定。
- **当前候选实际软件证据**：check_region_continuity_{prelaunch,wiring,lifecycle}默认3597帧精确相同、3理想FK交接、zero-load12不推、3guard优先、真实collector AST/action override、8CLI拒绝和49源码写档；check_region_press_push_continuity对真实袋10切换输入重建父waypoint<1µm，候选XY连续且Z不变、每例zero-load12步不推。新audit_region_continuity_live.py先原残差动作审计再独立按前press命令复算新第一push；runner新run_region_continuity_groups.py冻结审计依赖。close_region_continuity_group.py供后续完整组关闭。启动不是效果证明。
- **审计兼容问题已明示修复**：父840004袋首次handover后，旧audit_terminal_hold_inputs与audit_initial_near_half仍按原mesh中心/固定top落点，分别误差43.6/31.6mm。保留CONTROL_EVIDENCE_EXECUTION_R1和16份原报告/log、before_region_aware_auditors源码。新audit_region_reference_live从实际q/URDF/hull/物体姿态独立核真实最低顶点1268和捕获localXY，原3–5mm/2mm/10mm/卸载/q保持门以及后续全部frame常量保持；不导入控制helper。1实际有效+6篡改fixture全符合；2工具相关16项重跑通过，80逻辑控制检查闭合，未放宽门/改raw。新run使用修正检查器并冻结其SHA及helper。
- **前侧交换袋是另一机制**：840001袋仍159.562mm未达+.20；245front_x push/199lateral_y push，8恢复（7丢载/1tilt）。新FRONT_WORK_EFFICIENCY/LOADED_CONTACT_OFFSETS/FRONT_CONTACT_BOUT_DIAGNOSIS显示前侧法向中位5.010N/X力−2.691N、侧向4.921N/Y力3.088N；每段COP局部边距首5带载样本中位42–52mm→末5约8–14mm。虚拟参考不等于COP；最后子步不是积分/唯一因果。8事件RGB实际查看。新区域候选不覆盖front，不能称已解决；旧12mmobject-relative盒257→13mm退化仍保留，不能重开旧开关或只延时。
- **视觉风险/训练目标不变**：父840004盒各样本目标可见但底/右裁；840005盒171起目标画外，840005袋513起左裁/手遮挡；2wait稳定空桌。上一版完整输入暴露审计与阶段采样建议仍适用但未训练验证。原12组仍4拒绝/8未开始/0合格，独立192push+3wait多seed/h10未动。无合格新训练组、转换、新模型。下一步收新完整对照→查交换盒真实加载/后绕袋持续接触及默认路径退化→再解决front/其余前后反斜向/视觉学习。goal active；本轮progress为完整父关闭、真实载荷后命令跳变原因、审计更正/反证和新完整物理启动。

以下为历史记录，以本段为准。

## 2026-09-30 09:39UTC接续：残差左右仍2/4，接近到3mm但交接错过；斜向继续

- **真实活动run仍tracking_region_groups_r1**：runner1097061、当前collector1113301（840004首盒）、control1098038/event1098039实际ps核活；首左右4推+841000wait已完成，原斜向4推+841002wait继续。当前collector在840004盒step660 top_push，仅进度不称成功。全部49源冻结、生产collector SHA fa8abb62不变；没有启动其他物理/训练。磁盘107GiB。
- **完整左右FRESH_LATERAL_00_RESULT已严格闭合2/4+wait**：close_tracking_diagnostic_group.py核49归档×3case、40实际原控制、4残差动作/原动作重建、4条8RGB+4external与wait8RGB真正查看并哈希绑定；所有5条首11D q/action零、assist0，四推非目标最大XY均0。正常盒/袋过，交换盒65.060mm失败；交换袋159.562mm但finalY约+.006177未到+.20，失败。仍没有完整新合格组、转换或模型。新工具可按原protocol group对下一斜向关闭，不能拿左右部分当整个run完成。
- **后绕盒好/差并存**：旧4QP、距盒顶81.687mm横向越界；当前48QP（119..166）能下降至2.974mm，所有48真实动作、残差、两响应独立FK审计过，非全局slew改坏。但167触发not_unloaded_precontact，无handover/真实载荷。165/166 gap4.266/3.356mm满足高度窗口时另一掌误差2.435/2.129mm未达<2；167另一掌1.845mm已达而gap2.974mm低于原3mm。最后预测gap3.528→真实2.974，向下误差.553mm；TRACKING_HANDOVER_DIAGNOSIS为独立实录FK核验。原保护/交接条件不放宽。
- **新离线单变量staged_tracking_handover_margin未安装/未排物理**：仅线性规划最低高度3.5→4.2mm，原实测3mm保护、3–5mm交接、另一掌<2mm及所有其他门不变。screen_tracking_handover_margin.py对5实录首姿态/相同外加残差序列比较，当前2/5→候选3/5，新增当前盒49步几何到达；父盒600步未达/父袋2步横向越界仍失败。MARGIN_STRESS_COMPARISON保留正反例。反事实历史残差不是新命令真实物理响应，未证明接触/分拣/全碰撞，更不准入；等当前完整物理结果后再决定隔离验证。
- **新数据输入定量审计已完成**：audit_completed_push_learning_inputs.py复用camera/visibility/query_phases，对上一region_patch完整8推诊断，显式跳过2普通wait投影；全部8条各6实际RGB投影叠加已查看/哈希绑定。5成功中正常袋224/291(77.0%)、正常盒164/247(66.4%)、交换斜盒232/247(93.9%) top_push帧bbox全画外，均尚未达位置门。另两成功bbox不全画外但有遮挡/极小裁边，不能等同可辨识。840001失败袋450push无bbox全画外，反证仅修视野不足。
- **采样暴露风险**：同5成功的静止尾段646/568/79/545/650帧，占1200的53.8/47.3/6.6/45.4/54.2%；释放到稳定18–33帧仍计active，原轨迹完整保留。只是均匀query暴露估计，无训练因果结论、没有新可见性硬门/失败数据挑选。详细LEARNING_INPUT_FINDINGS.md、PUSH_LEARNING_INPUT_AUDIT、CAMERA_VISIBILITY_AUDIT、VISIBILITY_DURING_WORK在region_patch_groups_r1。后续合格完整组才冻结任务/布局/阶段抽样，原h10及独立192push+3wait、多seed未动。
- **实际画面**：当前正常盒513后目标缺失、正常袋171后缺失；交换盒大多数后续样本两物缺失（342目标边角），事件164..172无目标，227仅边角，不能靠RGB确认接触因果；交换袋8RGB两物可辨但手遮挡/底裁，仍失败。wait8RGB确为稳定空桌。EARLY_REVIEW/ACTUAL_REVIEW_BINDINGS与交换盒ACTUAL_EVENT_REVIEW_BINDING已写。
- **下一步**：收完正在跑的原斜向后绕袋/其他条件与wait，做原控制+残差动作+实际图审/完整组闭合；结合其真实guard/handover决定4.2mm候选是否进入完整隔离物理对照（不重采覆盖当前失败）。真实加载/接触效率、其他前后/反斜向失败、画外风险仍须解决后才能训练。完整目标active。本goal轮progress：左右完整审核、新真实交接时序原因、单变量离线反证及完整学习输入诊断；不是完成或阻塞。

以下为历史记录，以本段为准。

## 2026-09-30 09:19UTC最新：区域版完整5/8拒绝；残差候选完整物理诊断已启动

- **当前唯一真实物理run tracking_region_groups_r1**：09:17:55UTC runner1097061/collector1097096（840000首盒）实际启动核活；控制1098038/事件1098039。原lateral00/diagonal02全部8推+841000/841002普通wait，1200/70帧/envseed0、原几何/交换/任务保持。09:18:38 post-AppLauncher49档案/实际语义核验通过，较原合同只有region_top_approach=true及region_tracking_residual=true两键。没有完成新quality，不称改善。源码全部冻结；生产collector不变。
- **上一region_patch_groups_r1完整已关闭**：原runner993571/control993572/event1008896/collector1062086均已实际结束。完整分拣5/8（左右2/4、斜向3/4）、2wait过，仍0完整合格组。80实际原控制+8新动作审计、6case各49源码归档、8×8RGB+4external及2×8wait真正查看并哈希绑定，RESULT.json/md和CAUSE_REPORT完成，无批准review/转换训练。新增斜向首盒281.489mm、交换盒约150mm/袋约150mm过；首袋40.632mm失败。
- **两个物理后绕失败**：盒119..122仅4QP→123 current_geometry_guard，localX=-60.594越界.594mm/离顶81.687mm；袋100..101仅2QP→102同guard，localX=-65.391越界.391mm/离顶91.705mm。均load0、无handover；真实FK核验与命令重建过，非全局slew改坏。袋/盒事件8RGB和完整8RGB4external都真正审查。成功斜向交换盒171后目标缺失，交换袋513后左裁，图像可学性仍未证明。
- **新因果残差证据**：audit_causal_region_tracking.py实读4条轨迹；只用当前/过去q和command作一步预测。父盒/袋stable段command-only XY中位误差3.125/4.389mm，上一误差残差预测.037/.032mm；但接管突变最大约15mm。新盒122预测余量−.283mm、实际−.594mm，command-only错判+1.645。数据文件CAUSAL_REGION_TRACKING_PREDICTION完整保留正负，不能据中位变好称动力学模型可靠。
- **隔离probe及反证**：staged_tracking_region_approach中两响应QP仅XY时2/5，加预测最低高度3.5mm后首次3过/延后2失败，补入候选新最低顶点后首次4过/延后2仍失败或600步未达。使用记录瞬态残差作为外加扰动后仅2/4过（父盒600步未达、父袋2步越界；新盒56/袋51过）。冻结物体/人工响应不是物理与示范。未采用延后稳定触发，未删反例，未放宽任何原门。
- **当前新实作 staged_tracking_contact_patch_approach**：collector SHA9bbd47d3a0fee61d4cef9fd5e36d1b59b4801609f8dd39a6fabf376aa280504a；helper6eba707a741ed8ac94de0c46fe69c2da71be9fde36718b4f85a69d58f37a231d。current q−previous actual command（非原coord未执行值）入两响应名义/残差FK；原0.04/0.015步长、0.98腰工作界、10mm接触内缩、物距/桌边保护，额外原0.055全局slew预先入界。显式Z≥3.5mm线性屏障/真实非线性≥3mm检查，最多8次支持点补约束。>0.04rad残差退出到guard。旧无载真实q交接、真实载荷确认和重接触落点保留。
- **已实际软件检查**：check_tracking_region_prelaunch真实parser8拒绝/49快照；check_tracking_region_wiring包含默认3597帧一致、三理想zero-residual接近/交接、zero-load12不推、真实load确认软件fixture、3guard优先；实际collector AST读取上一实际命令残差逐项相符，2FK失配拒绝。MANIFEST绑定，不是物理过。新audit_tracking_region_action_live.py会先原动作重建，再从raw q/u核残差并独立FK检查两预测响应；输出TRACKING_REGION_ACTION_AUDIT.json。run_tracking_region_groups.py用已修正0/1数值失败约定，每case保存进程code，质量失败继续其他条件、runtime/control失败止。
- **完整目标仍active**：原12组4拒绝/8未开始/0合格，新候选完整结果未出，独立192push+3wait未调参。没有合格完整新训练数据/转换/新共享模型；h10独立多seed和实际画面目标仍须完成。当前实际candidate是残差版，不再误报旧region版仍在跑。本轮progress：完整旧诊断关闭、第二真实越界原因、因果预测/反证、新隔离接线与实际新完整诊断启动。

以下为历史记录，以本段为准。

## 2026-09-30 08:56UTC接续：候选左右完整仍2/4，真实跟踪越界已定位；原斜向继续运行

- **当前唯一物理run region_patch_groups_r1**：R3 runner993571、collector1002568（840004首盒）、控制993572、事件观察1008896已实际核活。原左右四推+wait已完成，原斜向840004/840005四推+841002wait继续，1200/70帧/envseed0和原几何不变。以PROTOCOL_R3.json与当前STATUS为准；原863591/863637、922378/923384及续接等待器均结束。生产源和候选49源码继续冻结。无训练。
- **新LATERAL_GROUP_RESULT完整核验2/4+wait过**：正常840000盒150.126mm/袋150.030mm原任务+pose过；交换840001盒62.851mm/袋155.378mm失败，袋finalY+.001993未到+.20。四推非目标0，5条首11D state/action0、assist0；三case各49归档源哈希、40原控制实际报告+4新动作审计、4×8RGB+4external与wait8RGB真正查看绑定。整组仍拒绝，未准入。新候选没有提高左右分数。
- **关键负面：物理跟踪未覆盖**。交换盒区域QP119..122仅4步，123帧current_geometry_guard锁存，尚未handover。实际最低点localX=-60.594mm超原-60mm边界，仍高盒顶81.687mm/load0。122预测localX=-58.355（内余1.645mm），下一实际偏2.239mm，支撑顶点1012→1017；全11D跟踪误差max7.512mrad（另一臂），活动臂max6.123mrad。实际命令重建误差5.72e-8rad且4步无全局slew改写；双手FK实测一致<.1微米。不是载荷已经建立/物体遮挡碰撞证据。下一改进应处理当前真实跟踪误差、接近时剩余运动和近支持顶点切换，先做因果预测/内部余量或稳定接管的离线反证，再隔离完整物理试验，不放宽原10mm区域/物距/桌边/任务门，不重复旧全局servo或yaw-hold退化。
- **数据/画面风险仍明确**：正常盒513后目标画外、正常袋171后画外、交换盒171后两物缺失；交换失败袋全8可辨但手遮挡/底裁。交换盒首次guard事件8图也真正查看。数值成功不证明可学；原前后组3/4拒绝已完整审查、近袋754帧旋转使24mm规划通道桌边4.688mm<5，详细CAUSE_REPORT保持。
- **执行器/审计修正而非控制改变**：R1引用不存在push_assist parser键；R2将已完整数值失败限定exit1（原runner允许0/1）而停止；原child code没有保存，恢复明确不捏造退出码，核raw/状态/manifest/source后保留续接。audit_region_action_live R1误要求rear阶段已有区域日志，R2按实际projected_support_reference覆盖103..1199核验（1097帧），1合法+7损坏fixture全符合预期，原错误报告保留。R3修正退出约定并冻结audit_region_action_live_r2.py，全部已写轨迹不重采/不改；RECOVERY_R2/R3、SUPERVISOR_R1/R2_TERMINAL及protocol三版保留。区域审计文件现为REGION_ACTION_LIVE_AUDIT_R2.json。候选物理失败仍保持失败。
- **当前观察器注意**：watch_region_patch_controls已R3重启为993572；watch_region_failures因切换时看到旧terminal结束，现1008896真正重启，保留既有诊断、不重复覆盖已实际图审。该脚本对完整region轨迹自动生成REGION_PHYSICS_DIAGNOSIS和待审REVIEW_EVENTS，绝不自动批准图像。之后核真实PID/STATUS/报告，不以文件推定在跑。
- **完整目标保持**：原profile4族16推11过、完整组0合格，原12组4已拒绝8未开始；新候选还须收完斜向/等待。没有合格新训练组/转换/新模型；独立未调参192push+3wait、多seed、原h10实际模型图审和数据准入仍未完成。本轮是progress（完整前后与候选左右审核、实际跟踪失败证据、原斜向物理推进），goal active，磁盘约109GiB。

以下为历史记录，以本段为准。

## 2026-09-30 最新：前后完整3/4拒绝；区域接近候选已接线并开始完整诊断

- **前后fresh_depth_01_trial_v2_r1已关闭**：runner824645/control825231实际退出；push3/4+wait通过，整组拒绝。840002盒150.888/袋227.132mm、840003盒174.448mm过；840003近袋149.596mm失败且finalY+.074013，离目标区还126mm。四推非目标0；5条首11D q/action0、assist0；wait双掌2.098mm。40实际控制报告/原质量来源/4×8RGB+4external及wait8RGB全部真正核验绑定；RESULT、PILOT_ADMISSION_RESULT、CAUSE_REPORT已写，无训练准入。
- **失败直接证据**：近袋754帧planned_corridor_no_table_margin_5mm，yaw .117468→.365411，X半包络82.980→95.983mm；24mm规划物距的桌边余量30.694→4.688mm，实际桌边8.429mm/X物距20.259mm，不是已碰盒/掉桌。260真实加载采样手yaw力矩中位+.013993Nm、桌−.014062Nm；接触中心局部XY中位+7.868/+7.830mm，不套用前侧−47mm原因。事件8图实际查看；末子步力矩不是冲量/唯一因果。成功840003盒513起画外，数值过不等于视觉可学。
- **区域候选已在隔离目录接线**：region_top_contact默认None局部落点保持原状态3597帧精确一致；region_approach_lifecycle保持原保护优先、首后绕无载当前几何触发、3–5mm捕获真实手参考/目标局部落点、单步实测q保持、原载荷确认再推、重接触保留。三实际首次姿态理想FK99/92/100步过；零载荷不假推、guard优先、真实采集器AST接线/动作覆盖、2个FK失配拒绝、49源快照/真实parser检查均完成。仅软件证据，生产collector未改。候选collector SHA b24f4f92a2f289a53e4ec4ca840cdcd548928c5dbaed3e16ea0fea266498fc1e。
- **当前真实物理run region_patch_groups_r1**：08:32:41UTC runner863591/collector863637启动，原lateral00与diagonal02全部8推+841000/841002普通wait，1200/70帧/envseed0及原布局保持，仅region_top_approach开。08:36:34真实post-AppLauncher49档案和语义检查通过，唯一语义差别为新开关。当前首840000正常对仍采集，尚无完整组新结论。旧12覆盖4完整拒绝/8未开始/0合格保持，独立测试未使用。
- **执行器修正需跟进**：R1 startup错误读取不存在的push_assist parser键，预期首case完整后执行器会报KeyError；物理采集未改/未重启。新run_region_patch_groups_r2.py按raw assist_frames核验，PROTOCOL_R2.json绑定同49源/全部原commands，新审计audit_region_action_live.py重建QP动作及原slew/限幅。等待续接888783仅等精确863591/863637结束且核对预期错误，再核验已有首case、不重采，启动R2余条件；888782独立原控制审计已启动。AUDITOR_AND_RESUME_PROCESSES、STARTUP_SOURCE_CHECK留证。下轮务必查ps和STATUS/runner_r2.log确认续接，不凭文件假定活跃。R1未保存child exitcode，R2明确记录该限制并实际核所有完整raw/quality/source。
- **08:42后实际更新**：R1按预期在首case写完后KeyError退出，原collector863637结束；等待器888783已正常退出，R2 runner922378/collector923384实际核活并在840001交换盒运行，控制888782活。RECOVERY_R2与SUPERVISOR_R1_TERMINAL完整保留错误/续接，不重采已有2条。首正常840000盒150.126mm/袋150.030mm原任务姿态过，20控制实际pass与2个新动作audit通过（均initial-top无region覆盖）；两条8RGB+4external已实际查看绑定，盒513起/袋171起目标画外。**差信号**：交换盒180帧已region_guard_lift，原因待完整region日志，尚不可据progress猜测。新diagnose_region_physics.py已准备，写盘后核实首次abort前后真实q对候选q/全局slew/原接触日志。新动作审计1合法+6损坏fixture符合预期，WAIT真实parser2条过，来源均不改。
- **整体目标仍未完成**：无合格完整新训练组、转换或共享新模型；候选不声称解决initial-top旋转/相机画外。之后完整候选审查→合格profile新鲜全部族/交换准入→转换训练→独立192push+3wait多seed、原h10真实画面闭环。原零位/无助推/非目标1.5cm及姿态门全保留。本goal轮属progress：完整前后闭环审核/原因证据、候选实际启动和新动作审计；goal active。

以下为历史记录，以本段为准。

## 2026-09-30 最新：左右完整2/4拒绝，原前后组运行；近支持面集合候选已隔离验证

- **当前唯一物理任务 fresh_depth_01_trial_v2_r1**：runner824645/control825231，08:03:21UTC实际启动、ps核活；840002/840003四推+841001普通wait，原计划/布局seed2026093002/train、1200/70帧、环境seed0保持。首840002盒step180已top_push。TRIAL_V2_DEPTH_RUNNING_PROCESS合同SHA `7b45d435b74a2958f537f6003ff1bc6bf072463c689d0870a4d6482e12ea4146`。08:04:24UTC真实STARTUP_SOURCE_CHECK：post-AppLauncher设置+44归档/40合同源码通过，yaw-hold=false。**生产核心继续冻结**，没有其他Isaac/训练或后继自动队列，新组尚无完成quality。
- **fresh_lateral_00_trial_v2_r1已完整关闭2/4+wait过，整组拒绝**：810966/811741实际退出；正常840000盒150.036603mm、袋150.020264mm原质量/pose/来源过；交换840001盒62.661052mm、袋166.954970mm均失败。袋虽超过150mm进度，但finalY+.013570m未到+.20区，不能算成功。四推非目标maxXY0；全部5条首11D q/action0、assist0；wait双掌2.098291mm、腰3.08732e-9rad。40实际控制/raw/report/auditorSHA核验、4×8RGB+4external与wait8RGB真正查看绑定；真实生产来源审计2push+wait过、2失败原门拒绝。未生成approved review/转换/训练。RESULT SHA `694c27d9ee14ed5acedd44a49f94bc7224dd1cac9800b4aaccfa7ba54de21e1d`已绑定下轮，不改RESULT。
- **左右原因/画面**：交换盒1081/1199控制帧top_cross，末虚拟X.623261对固定surfaceX.638293，差15.032mm>原10mm接近门，load0；171起采样RGB两物皆缺失。交换袋8次重接触，lift85/cross275/descend346/press44/push449，末仍top_push/load5.209N、未到目标区；两物8采样可辨，袋685起底裁/手遮挡。正常盒342右裁、513起缺失；正常袋171起缺失。**好：**正常/非目标/wait保持。**差：**交换两条失败，正常进度余量仅.037/.020mm；没有多seed稳健或模型可学证明。CAUSE_REPORT.md保存。
- **反斜向失败的新真实接触证据**：audit_loaded_contact_offsets.py与新增audit_signed_contact_moments.py实读solved_contact_forces，post-action位姿与下一pre-action对齐误差0；840007袋front_x动作110..137共28加载采样，法向力加权真实接触中心局部Y中位−47.105mm（worldY约−46mm），Fx−2.821N。手yaw力矩28/28负，中位−.128522Nm，yaw变化28/28负/累计−6.121°；桌面力矩中位+.128803Nm，净接触yaw力矩中位+.0000677Nm。支持偏心与旋转方向一致，但末子步力矩不是完整冲量/角加速度/唯一因果证明。旧全局center10/12→6/12退化仍保留，不重新开启。详细报告在该失败ep/LOADED_CONTACT_OFFSETS.json、SIGNED_CONTACT_MOMENTS.json与父CAUSE_REPORT追加段；没有修改原RESULT。
- **新隔离近支持面集合QP改进**：screen_causal_contact_patch.py由上轮单argmin改为约束最低高度上0.1mm带内顶点的XY极值，仍原10mm内缩区域/关节步长/另一掌锚点，并0.5mm内部线性化余量/真实候选FK保护。之前首次接近盒/袋失败，这次898001盒frame117→99步、840004袋frame100→92步几何接近3–5mm过，采样手/非目标最小76.807/32.978mm；同参数在本轮新840001盒frame120→100步也过，最小79.649mm（未针对新例调参）。末态两例96/19步过。**只是固定物体/理想跟踪，不是物理加载或分拣成功；相机/全臂碰撞也未证明。**
- **可接续代码已实现但未接线/安装**：staged_contact_patch_approach/contact_patch_approach.py纯单步有界QP与articulated_hand_geometry.py独立URDF FK/Jacobian；check_staged_contact_patch_approach.py实际调用这两个模块，三首次状态+两末态过，与独立探针前两终q误差<1e-8rad。check_contact_patch_geometry_and_guards.py两真实轨迹共88双掌采样误差max.322微米，FD Jacobian max1.34e-10；每例6异常输入（碰另一物体/顶面区域外/NaN/错Jac维度/已近接触/超界q）全部拒绝。这些负例仅软件fixture，非物理数据。MANIFEST明确installed/collector_wired/physics_executed/training_ready全false，绑定全部源/检查。README明确下一接线事项，无审批需求。
- **候选下一必要实作**：先后绕无载接近、原guard优先、只当前状态因果触发；到几何接近后需捕获真实手局部参考和目标局部落点，连续交给原真实载荷确认，不能返回旧fixed surface，也不能仅用会被_start_recontact重置的approach_xy_bias。需隔离默认off局部落点接口/重接触保留/原默认一致与保护释放优先验证，才新diagnostic完整物理组。当前v2合同仍绑定旧源/profile，禁止覆盖后沿用旧合同或直接把诊断变pilot。未实现这个交接、未执行任何离线q。
- **覆盖**：本profile原12组3完整拒绝、1运行、8未开始、0合格，全四族/难例/split保留；当前depth01完成后原lateral04等。接近候选在隔离目录继续准备，不影响采集。没有合格新训练组/转换/新模型；独立未调参192push+3wait、多seed、原h10实际模型图审仍必须。磁盘约110GiB。上一主goal轮progress；本轮完整组核验拒绝、真实接触力矩证据、新候选实作/真实几何与拒绝测试、下一组实际启动都是progress，goal active。

## 2026-09-30 最新：反斜向完整3/4拒绝；第三原左右组运行；接触区域首次接近仍失败

- **当前唯一物理任务 fresh_lateral_00_trial_v2_r1**：runner810966/control811741，07:41:50UTC实际启动并ps核活；840000/840001×盒袋四推+841000普通wait，原随机布局seed/split/train和1200/70帧不变。首840000盒step90已top_press。TRIAL_V2_LATERAL_RUNNING_PROCESS合同SHA `2cc99798c9f6a06b4ab0e0dab9adcddac11cd1f0113a60994ddcd40044eb75cf`；07:43:01UTC STARTUP_SOURCE_CHECK实核post-AppLauncher设置与44归档/40合同源码，yaw-hold=false。**生产核心保持冻结**，无训练/其他Isaac/后继自动队列，当前新组尚无完整quality。
- **反斜向 fresh_reverse_diagonal_03_trial_v2_r1 已真正完整关闭**：726034/726100均已退出；840006盒150.304mm、袋150.080mm过；840007盒284.212mm过、袋0.224mm失败。push3/4，841003wait通过，整组拒绝。四推非目标maxXY全0；五条首上半身q/action精确0、assist0。wait双掌2.098291mm、腰3.08745e-9rad。40实际控制/raw/report/auditorSHA核验，四推各8RGB+4external、wait8RGB真正查看并绑定；实际生产来源审计3push+wait过，失败袋被原质量门拒绝；未写approved review/转换/训练半组。RESULT SHA `aa55945f80761542e778ba8ccb75c12dbebbc0d70646357a94329d3ac67145f7`，已被下一运行记录绑定，不随意改RESULT。
- **好/差视觉与余量**：首盒/袋仅比150mm门多.304/.080mm，不是多seed稳定证明；首盒342起仅右缘残片，首袋685起缺失，交换盒685起两物缺失。失败交换袋反而全部8采样两物可辨（手遮挡/盒856左裁），不能用图像丢失统一解释失败。图审完成不等于逐帧全部可见或模型可学。
- **新直接失败原因 FRONT_CORRIDOR_FAILURE_DIAGNOSIS.json / CAUSE_REPORT.md**：交换袋138步触发front_corridor_no_table_margin，前137步top_push有实测4.690N载荷。袋yaw -.155139→-.261696rad（转6.105°），X包络半径85.302→91.233mm；动态规划前侧桌边余量16.727→4.864mm，低于原5mm保护门。当时实际袋桌边余量13.610mm、手/另一物体面间距204.213mm、非目标0，因此是旋转后计划通道失效，不是实际掉桌/撞另一物体/没接触。真实最低点局部XY[-20.303,-46.995]mm提示偏心，但不是COP，不能断言唯一转矩来源。保护锁存到1199，无重试裁剪。只读诊断首次日志列表索引错，已按step索引修复重跑，不影响物理代码。
- **隔离新区域QP（未安装/无q执行）**：screen_causal_contact_region.py保持原关节/步长界与另一掌锚点，允许真实最低点在原10mm内缩顶面区域内移动；物体固定、理想跟踪、逐候选真实FK保护。末态起点盒无缓冲260步卡6.032mm，袋19步到4.552mm；增加0.5mm内部线性化余量后末态盒96步到4.838mm、袋19步到4.552mm。**关键反证**：从首次因果可启动frame117盒/frame100袋开始，同候选都失败，78/66步卡19.476/36.122mm。不能据末态改善安装或叫物理按压成功。
- **QP失败已记录候选步**：最低顶点盒1290→1268、袋1178→1231，即使1/128步局部X仍越原区域.284/.627mm；不是手桌/非目标碰撞。原状态最低高度10微米内均有3竞争顶点，.1mm带内20/17个，部分区域外。下一应处理近共面支持顶点/接触面集合与连续接近、再真实加载/推阶段，不只追当前argmin或加帧/放宽界。CAUSAL_CONTACT_REGION_FINDINGS.md和EVIDENCE.json完整保留正负报告；不包含全臂/连续碰撞、力学、视野或分拣成功证明。新close_reviewed_trial_group.py实际用于关闭反斜向，按每条路由动态核全控制集合、真源审计及已人工绑定图审，绝不自动生成review批准。
- **覆盖台账**：原12固定profile组中2完整拒绝、1运行、9未开始、0合格，所有四族/困难组与split保留。当前左右完成后继续原depth01等；只有合格全交换+wait才进现有pair/split转换准入与共享RGB+11D阶段训练。最终独立未调参192push+3wait、多seed、原h10实际模型闭环图审仍全保留。仍无合格新训练组、转换或新模型。磁盘约112GiB。
- 本goal轮progress：完整反斜向审核拒绝、真实旋转/通道原因、区域QP早期反证、下一原组实际启动并源核。前一主goal轮也是progress；Git支线已完成并重新核private/remote32e390c，不再要求授权。goal保持active。

## 2026-09-30 最新：原斜向3/4+wait通过但整组拒绝；原反斜向正在采集

- **当前唯一物理任务 fresh_reverse_diagonal_03_trial_v2_r1**：runner726034、control726100，07:20:15UTC实际启动，随后ps两进程核活；原840006/840007×盒袋四推+841003普通wait、1200push帧、environment seed0、布局seed2026093004/split=train不变。首840006推盒step0实际开始，reset请求与实际位置/朝向相符。TRIAL_V2_REVERSE_RUNNING_PROCESS绑定合同SHA `eba926bd364571751b717dad6b1e26f6bf0249b8b73cfae7a4fc73efdcabcb24`。STARTUP_SOURCE_CHECK实核44归档/40合同依赖与post-AppLauncher设置，yaw-hold=false。**生产核心继续冻结**；没有其他Isaac/训练/后继自动队列，尚无新终态。
- **父 fresh_diagonal_02_trial_v2_r1 完整push3/4，wait通过，整组拒绝训练**：840004盒281.796mm过、袋40.570mm失败；840005盒150.301mm/袋150.039mm过。全四推非目标maxXY0，全部五条首上半身q/action精确0、assist0。普通wait70帧双掌最大漂移2.098mm、腰3.09e-9rad，原门过。577428/577492已实际退出；40控制实际报告及raw/report/auditorSHA核验，四推各8RGB+4external和wait8RGB实际查看/绑定，RESULT.md/json与PILOT_ADMISSION_RESULT完成。RESULT SHA `089aa680c5946f4e41e6e49039df3ea69bb5ff6bf42030b66bb5b311ab111d6c`。
- **实际生产数据准入证据**：新增review_completed_trial_episode.py用真实load_episode+audit_waist_pilot_episode，3成功push与wait完整来源/合同/原质量+pose过；失败袋被原`Pilot failed original task/waist/pose gates`拒绝。不是合成fixture验证。未写任何approved review.json、未转换、未训练成功半组。4条件和等待都完成，没有因首袋失败而停止或裁剪。**好：**原未测斜向三推成功、非目标/等待稳定。**差：**一条后绕袋卡住足以拒绝整组；交换盒/袋仅超150mm门.301/.039mm，不能叫多seed鲁棒。
- **实际图像风险**：首281.8mm盒全部8RGB可辨，但手遮挡、底/右裁；失败袋171起两个物体皆画外；交换盒171起目标缺失，交换袋513后左边裁切。WAIT8RGB空桌/双手稳定。数值成功不等于逐帧可见或模型可学，未另加可见性硬门。成功三条query阶段start/active/terminal分别3/1131/66、3/547/650、3/654/543，活动曝光很不均；失败袋无合格settled尾段，不裁失败数据补标签。
- **新真实原因**（父CAUSE_REPORT.md）：失败袋末虚拟支持点X.593401 vs固定目标X.603864，误差10.464mm>原10mm下降门；真实最低点(.627640,-.073088,.813802)，袋顶.789976，仍高23.826mm；load0/腰-.98，卡top_descend。首盒front路径成功，袋rear路径失败，不能统称相同接触策略成功或放宽下降门。
- **新静态合法接触区域筛查（未安装/未执行q）**：screen_rear_top_contact_region.py在已结束898001后绕盒，真实最低顶点可在10mm内缩顶面内选落点时，原界/另一掌锚点下存在接近+4mm和顶面0间隙静态候选；腰.858/.969，投影bbox0。加50%bbox约束后综合误差19.3/21.5mm仍失败。screen_top_contact_region.py在新840004失败袋，含50%bbox约束仍有静态几何候选，腰-.545/-.555，bbox投影1，手与另一物体面gap31.8/25.8mm。固定物体/局部优化/无力学，50%仅诊断不是新增质量门；不证明全局不可达或实际压持成功。
- **对静态结果再限制**：screen_contact_region_path.py从袋真实末q到8个几何候选，用原步长界2–30步插值，采样活动手未见物/桌穿透，但不含连续扫掠/全臂/自碰撞/另一掌全程锚定/真实跟踪，不能执行q。更关键screen_causal_contact_capture.py不用优化q，仅当前最低顶点冻结参考+当前合法区域投影、原有界IK/另一掌锚点/1.5mm下降：袋由原400步仍高23.9mm→224步接近4.84mm，但21次支持顶点切换、腰仍-.98/画面问题未解；盒候选400步仍高73.6mm，**仍失败**。CAUSAL_CONTACT_CAPTURE_SCREEN.json保留全部负面，不能直接安装为通用解决方案或称物理成功。初次通用探针有inactive变量名覆盖，已修复并成功运行，不影响生产源。
- **覆盖台账 TRIAL_V2_COVERAGE.json**：本profile原12组中1组完整拒绝、1组实际运行、10组未开始，合格0组；全四族/原split/所有困难组保留。下一按TRIAL_COLLECTION_V2_PLAN继续其余原组，合格必须完整交换+wait及所有原门/实际图审；不先要求专家所有布局完美才试采，也不将阶段模型或容易族代替整体目标。
- 下一步：收原反斜向完整结果/真实图审/来源，继续原多样计划；并隔离设计可因果执行的区域选点→稳定接近/按压→持续推动，处理后绕盒/袋及视野，当前源不改。只有合格全组才能转换/共享RGB+11D训练；最终未调参独立192push+3wait、多seed、原h10/真实闭环图审仍须完成。**当前仍无合格新训练组、转换或新模型**。本轮progress：完整物理组闭合与拒绝、真实准入验证、接触区域正负证据、新原组实际启动；前一goal轮也是progress，goal active。

## 2026-09-30 最新：朝向保持完整0/8拒绝；试采v2已安装，首原斜向组实际运行

- **当前唯一物理任务 fresh_diagonal_02_trial_v2_r1**：runner577428、control577492，06:56:06UTC实际启动并ps核活；最新首840004推盒step210进入top_push。原fresh_diagonal_02几何/朝向/seed2026093003/split=train未改，environment seed0，完整840004/840005×盒袋四推+841002普通wait，push1200帧。没有其他Isaac/训练/后继自动队列。TRIAL_V2_RUNNING_PROCESS.json绑定合同SHA `57ddf9c1199357fe3f0407a0ce475e597b4fe116819c0984340a5ff904a1dd0d`。**生产核心冻结至该组/审计退出。**尚无新终态或可训练完整组。
- **真实启动后验证 STARTUP_SOURCE_CHECK**：post-AppLauncher语义设置与合同精确一致，role=pilot、yaw-hold=false；实际44归档source逐byte/hash过，覆盖40合同控制/物理依赖，case合同与签发合同一致。这是实际新进程写档证据，非模拟fixture；但完整raw首零位、原质量/姿态/非目标/wait与图审仍待采完验证。最初一次只读验证误用无numpy系统python退出，改Isaac环境完成，不影响采集。
- **上一轮contact_bout_yaw_groups_r1真正完整0/8（父5/8）：前后0/4、左右0/4，两组拒绝训练。**原runner306492/batch306764/control306765与最后hand-clearance子进程542760均已实际消失；80控制实际report+raw+auditor SHA核验、9批exit0、8条各8RGB+4external实际查看并精确绑定RESULT完成。RESULT SHA `1236dfea63ff85ee1674f65d2054b187ff7bcdab9499143df05ad7989631ac21`，RESULT.md保存。未生成approved review/转换/训练。
- 原8推进mm：正常盒86.482/袋73.021，交换盒65.029/袋88.913，近盒70.020/远袋125.478，远盒30.361/近袋60.121。全8非目标maxXY0。**好：**非目标稳定门保留。**差：**所有任务失败、正常任务也退化；交换盒仍top_cross；机载RGB正常袋171起缺失、正常盒342起缺失、交换盒171起两物缺失，交换袋685/856缺失、1027后底裁返回。未新增可见性门。详细匹配前后接触/载荷退化见DEPTH_REGRESSION_DIAGNOSIS，不能统一归因重接触或直接加压修复。**决定：该yaw候选不用于扩采，明确off**，保留其代码以可复现实验；默认off对照及原控制质量门不改。
- **v2仅试采许可已安装06:54:52UTC**：备份before_trial_collection_v2，TRIAL_COLLECTION_V2_INSTALLATION.json。collector `fa8abb62dd3eeccd9ec88429f0374caa866b82c1f96cdc7dfd3b456b6783200c`，waist_pilot_protocol `5f87452f459e088d15f42bbea3f73851697576fbb2a0bd09924bce76d9680cf7`，新增waist_trial_collection `bab63f559f405a1627fce896241784a2d481dcc8c30e9528199f9893fc15c5d8`。waist_coordination/contact/route物理helper保持上轮已验证默认off路径。v1失败feasibility仍拒绝，diagnostic不能提升pilot；新v2只允许PROPOSAL SHA e6435d54绑定的原12组精确计划、feasibility=[]/collection_admission_only=true/training_ready=false。不再以先前专家整组成功阻止试采，但实际训练仍严格整组原数据门与图审。
- **本轮软件验证**：DATA_ADMISSION_CHECK实际完整10文件/2组、train5+val5，真实load_episode→v2合同/源码→原audit_rollout/pose→pair→checked_sources/make_split全过，无mock；19负例含缺/未批/错hash图审、diagnostic、失败质量、首q/action非零、非目标20mm、任务未完成、tilt.21、wait20mm漂移、source篡改、test泄漏、错prompt、初RGB差、即使改counts仍缺swap/wait、swap泄漏、真正覆盖预分配split拒绝。**全部是显著标记的合成软件fixture/模拟review且临时删除，不是物理合格样本、实际图审或LeRobot导出。**修正过一个split负例，最终明确触发requested split differs，而非只触发空训练集。
- COLLECTOR_LIFECYCLE_CHECK新增真实builder/runner12组36命令与实际snapshot/provenance写档：40合同依赖逐字节过、8pre/post篡改负例；隔离源完整语义检查，不启动AppLauncher/physics。初次测试发现合同还绑定URDF/USD而原snapshot清单未含，已修collector按合同追加所有依赖并实际写档检验；不是删除source gate。安装后top_contact_bypass/waist_pilot_protocol/waist_pilot_audit/converter **41项真实回归过**。先前SCHEMA12计划/19负例/20旧回归过。stage MANIFEST installed=true；部分安装前检查脚本假定旧源，不要直接重跑并把其expected-old-source失败当生产故障。
- 已签发 `fresh_trial_contracts_v2_r1/` 全12合同、36启动命令prepare通过（都是试采许可，不是质量认证）。TRIAL_COLLECTION_V2_PLAN保留原四族48push+12wait，先未测diagonal02→reverse03，再其余原清单含已知失败lateral/depth，**没有重采易例/改split/删难族**。目前只启动第一个完整组，下一组须根据本组实际运行/质量/图审推进，普通wait由runner自审并渲染。watch_fresh_pilot_controls继承当前完整控制审计并跳过wait，wait另独立稳定性审计；无旧纯diagnostic9批watcher并行干扰。
- **下一步**：核当前首episode原门与首零位/无助推、完整4push+wait及逐条真实画面；全组通过才准入/转换，失败半组不训练；继续原其余随机族，逐族保留覆盖缺口与失败原因。合格完整组用于共享RGB+11D阶段训练，但不冒充整体完成；未调参独立192push+3wait、多seed、原h10和实际闭环画面仍必须。尚无合格新训练组、转换或新模型。磁盘约113GiB。本轮与前一goal轮均progress；整体goal active。

## 2026-09-30 接续：朝向保持前后完整0/4退化；试采v2真实启动前接线通过但未安装

- **当前仍唯一物理任务 contact_bout_yaw_groups_r1**：runner306492/batch306764/control306765实际ps核活elapsed28:25；当前898001最终交换两条运行，原8条件继续，源码保持冻结。已完成6条原任务全失败：前后4条+正常盒86.482mm+正常袋73.021mm；最终交换2条未终态。正常两条实际画面尚待复核，不能把前后4条图审套用于它们。最新60控制报告actualpass且逐raw/report SHA实核；控制实现正确不等于任务成功。未启动新Isaac/训练/后继队列。
- **差：完整前后由父3/4→0/4**：近盒151.875→70.020mm，远袋227.191→125.478mm，远盒174.490→30.361mm，近袋150.785→60.121mm。四条非目标maxXY全0；原质量门未放宽，整组拒绝训练。各8RGB+4external已真正查看并EARLY_REVIEW/ACTUAL_REVIEW_BINDINGS逐raw/image/frame绑定；DEPTH_INTERIM_RESULT.md保存。
- **新退化证据 DEPTH_REGRESSION_DIAGNOSIS.json / analyze_contact_bout_regression.py**：实际reset positions/quats/seed一致；首轮push前q差<1e-6rad，进入候选后分叉。近盒5次倾角重接触→13次丢接触；近袋6→12次丢接触；但远盒1047push帧/仅1重接触仍只30.4mm，不能全部归因于恢复开销。载荷中位近盒2.619→1.409N、近袋2.894→1.513、远袋5.000→2.217、远盒4.440→3.086，多数push帧偏置到原−6mm下限。垂直残差变化部分很小，不能断言唯一因果或直接增加下压量；均最后子步力记录而非积分。只读比较，无控制改动。
- **实际视觉**：近盒/近袋采样仍可辨但底裁/手遮挡；远袋中后段手遮挡及左裁；远盒171起目标缺失、342起另一物体也缺失。朝向保持未修复视觉学习风险。未新增可见性硬门。**决定：不将yaw-hold候选用于新鲜扩采；完整8条仍跑完保留对照。**默认off路径保持，下一profile显式off。
- **隔离staged_trial_collection，未安装/未发正式合同**：提出v2 frozen_trial_collection只授予原冻结12组试采许可，collection_admission_only=true/training_ready=false/feasibility=[]；固定PROPOSAL SHA e6435d54，原几何/类别交换/ID/split/wait不变，禁止事后重采易例；失败任一条整组仍拒绝训练。v1失败feasibility仍拒绝。无需先让专家在所有布局完美才允许试采，但不能把成功半组或容易族覆盖缺口冒充完成。
- SCHEMA_CHECK已实读passed：12原计划、19拒绝例、20旧回归（converter用mock，非端到端证据）。**本轮新COLLECTOR_LIFECYCLE_CHECK通过**：临时完整源码树执行真实collector prefix全部AppLauncher前校验，12组prepare/layout/finalize通过；8拒绝例包括role、layout、混源、pre/post设置、collector/helper字节、launcher期间contract更改。临时合同已删除，生产collector/protocol哈希不变。finalize使用已记录resolved settings，未启动AppLauncher/physics、写档或转换；不能称完整运行证明。首次工具未设现有OMNI_KIT_ACCEPT_EULA环境在导入处结束，采用当前任务同环境后通过，无物理启动。
- stage collector仅追加新waist_trial_collection.py到source snapshot清单；MANIFEST installed=false。**下一步必须**：真实完整数据/转换positive+negative验证（原质量/姿态/非目标/wait/缺交换/缺实际review/篡改源/diagnostic/split泄漏），新v2 builder与runner不再读取feasibility[0]，明确选off profile；当前8条及审计全退出后才能评估安装。尚无v2正式采集、合格完整新训练组、转换或新模型。
- 本轮为progress（四条件真实图审+匹配物理退化证据+隔离真实接线测试），前一goal工作也是progress。整体goal active：全四族随机组/普通wait→严格合格全组→共享RGB+11D训练→未用于调参独立192push+3wait多seed h10和实际画面，范围不变。Git私有代码快照备份已另完成，不等于分拣目标完成。

## 2026-09-30 最新：原8条完整5/8拒绝；每轮接触朝向保持新8条已启动

- **当前唯一物理任务contact_bout_yaw_groups_r1**：runner306492、batch306764、control306765，06:13:14UTC实际启动并ps核活，首898002近盒step0。顺序898002/898003原前后→898000/898001原左右，原几何/yaw/seed0、1200帧、完整8条件。最新实际ps仍三PID存活elapsed2:28；首近盒step630仅推进约38.267mm、仍top_push，存在效率退化信号，尚无终态。当前无新终态，不能称候选成功。新预期80控制实际报告（父72+8heading）+9批+8条actual图审；无训练/额外后继队列。
- **已安装单一功能开关**`--expert-top-contact-bout-yaw-hold`，diagnostic-only、默认off；同规则两臂/全部top_push，各轮push入口锁定水平投影最大的手局部轴world heading，其他mode含recontact/guard/release清空。保留原.15normal task，再加.15m heading task/.72gain/.1rad项限幅；原位置/关节步长/质量/零位/无助推/相机/释放保持。后绕盒尚未进入接触时该开关不生效，不能声称覆盖其可达性问题。
- 新collector SHA `f51f69dcca5079a18a92a0d3120272a7f75fcd200b062d67ff599eae359ba1d3`，waist_coordination `01cf60d279178d5918c4af79d550ea09520e436b8e0b8a3ff342792dae30165b`，新增contact_bout_yaw `1e2a3d5c7be4f22278dbe8d0322c17a2ecc8e9e433789016d986737df765b689`。initial_top仍8e6a11fc，near.5未变。before_contact_bout_yaw备份/INSTALLATION/RUNNING_PROCESS齐全，PLAN SHA `9a68e8f14678ce133a7dea650dd8556b011b79cc4c7df3aac92fc4d4bb982868`。**生产核心冻结至新完整组及审计全部退出。**未来pilot启用还需显式协议/合同升级，不能绕过当前diagnostic-only门。
- 候选证据：PURE40姿态/440有限差分列max3.25e-11；实际staged parser6例、18双臂真实solver fixture默认动作精确、10实际collector AST lifecycle；独立URDF heading审计真实off+284帧合成on/6篡改负控（合成不是物理结果）。实际安装后top_contact_bypass+waist_pilot_protocol+converter_waist_admission **40项过**。首次准备plan用系统python缺numpy只生成layouts、未改生产；改用Isaac环境完整生成后检查通过。
- **候选风险明示**：LOADED_HAND_TWIST真实近袋每轮21–26mm推进而COP后→前滑，6lost，后续firstCOP X逐轮变大；手worldZ每轮约.26–.37rad，但不能推定扭转唯一因果。旧全程姿态固定后段不可达，不能复用其成功叙述。新7真实bout×off/on有界IK筛查heading max.373→.0242rad，位置误差max5.56→7.48mm；固定外生目标/即刻q，不是物理重放/碰撞/力学证明。初轮末态全姿态静态拟合仍4.37mm/3.5°、最低点略出顶面，未将5个抽样点全称完美。物理完整8条验证决定保留/回退。
- **父y_path_nearhalf_groups_r1真正完整5/8：前后3/4、左右2/4，两组拒绝训练。**72控制actualpass、9批exit0、8条各8RGB+4viewer actualview/精确raw/image/frame合并RESULT，近袋另8guard图。31356/31530/31531已实际全退出。RESULT SHA `bba3f6c0de13598d68eb6fa2492a2990a8a0d8be703d47caa3b38feb183ab3c6`，RESULT.md与PARENT_COMPARISON闭合，无approved review/转换/训练。
- **好：**正常袋113.040→150.032mm由失败转通过，重接触9→2；正常两物firstgoalX保reset，不再104.7mm绕行。盒finalX−100.347→−.445mm，袋+31.738→−7.815mm。近袋80.577→150.785mm，但仍失败。**差/代价：**正常盒recontact3→6、腰max.266→.536；正常两条推进仅比150mm多.032/.050mm，不是鲁棒性证明。交换盒65.824mm停top_cross；交换袋167.024mm、终点Y+.013639未到+.20。父全8非目标maxXY0。
- 图像风险未解决：正常袋171起目标缺失、正常盒513起缺失，交换盒171起两物不可辨；远袋/盒同原后段离画。近袋/交换袋在采样可见但遮挡/底裁。没有新增可见性硬门，也不把专家成功等同可学习。磁盘约115GiB可用。
- 本轮为progress：完整父闭合、接触迁移证据、候选实际检查/安装及新完整物理启动。整体goal active：后绕真实接触可达性仍另解；新组结果后推进完整多样fresh+wait合同/准入/转换/共享训练，独立未调参192push+3wait多seed原h10/实际画面全范围不变。尚无合格完整新训练组或新模型。

## 2026-09-30 最新：当前前后子组仍3/4；近袋改善到150.8mm但保护失败，左右继续

- **当前y_path_nearhalf_groups_r1未结束**：runner31356、batch31530、control31531实际ps核活elapsed20min；已到897000正常盒step510。原8条/预算1200/seed/全门不变，所有核心仍冻结。当前前后4条完成，36控制实际pass，4条各8RGB+4viewer实际view/hash绑定；近袋另8guard事件实际view。9批全局审计尚未完成，不能叫整批已收尾。
- **前后原task+pose仍3/4，拒绝入库**：近盒151.875mm/.052961rad、远袋227.191mm/.002988、远盒174.490mm/.047921通过；近袋150.785mm/.002936失败、终点Y+.075203未到+.20。四条非目标maxXY0。DEPTH_INTERIM_RESULT.md、PARENT_COMPARISON（显式几何/朝向/assignment逐字段相等检查）、EARLY_REVIEW/ACTUAL_REVIEW_BINDINGS完整。
- **好：**near .5让近袋80.577→150.785mm，首次保护367→755；NEAR_HALF_CONTACT_COMPARISON区分真正首轮press，COP X+11.641→−3.000mm；lateral中位X12.618→5.002mm、手r×F yaw矩.034195→.013855Nm、正比例95.49→77.36%。不同后续轨迹/最后子步采样，非积分/唯一因果。
- **差：**近袋仍逐渐转至yaw.363120，755同planned_corridor_no_table_margin_5mm。独立几何计划桌边4.877mm<5，实际桌边8.471mm/X物距20.406mm；没放宽或解除保护。8事件0/570/650/700/754/755/830/1199已实际看图绑定。初落点改善≠持续接触/防旋转解决。远袋/盒目标离画风险仍保留。
- 当前继续原左右全4条；不改运行核心、不筛难例、不准入成功半组。之前接触可达性/前绕效率新诊断及其负结果详见下段。下一步针对持续接触滑移/旋转及后绕真实接触可达性，同时保留全部随机族+wait→严格准入/转换/共享训练/独立多seed h10完整目标。无合格完整新训练组或新模型，goal active。

## 2026-09-30 接续：8条件前三条通过；真实接触参考与前绕耗时诊断新增

- **当前仍唯一物理任务 y_path_nearhalf_groups_r1**，runner31356/batch31530/control31531本轮实际ps核活，elapsed15min；897003近袋step360推动，前三条已完整。核心冻结、原8条件不变，未启动其他Isaac/训练或后继队列。此前goal工作属于progress；本轮新增实际图审/数值与离线失败机制证据，不是完成。
- **前三原task+pose过，27控制实际报告pass**：897002近盒151.875mm、max tilt.052961；远袋227.191mm/.002988；897003远盒174.490mm/.047921。三条各8RGB+4viewer已实际view，EARLY_REVIEW与ACTUAL_REVIEW_BINDINGS逐raw/image/frame绑定。盒near后半段右/下裁切；far袋513左裁切685起缺失；far盒342边缘、513起缺失。未新增可见性硬门，视觉可学习性风险仍在。近袋未完成，不将3/3误称完整组通过。
- **新current_lateral_profile_r1/REAR_TOP_MULTISTART_REACH**：真实895001交换盒末帧FK两掌误差<.1mm，当前projected reference/原界三起点非线性IK；cross约9.9mm，contact(+4mm)保留或解除inactive anchor均约42.9mm。部分解到200次上限，非全局不可达；不支持仅取消另一臂锚点即可解决。
- **REAR_TOP_REFERENCE_REACH负结果**：固定切向中心改末态最低顶点可让虚拟参考残差近零，但新姿态真正最低顶点在盒局部(-91.7,+57.2)mm，超盒顶半宽(70,45)mm。没有安装。REAR_TOP_ACTUAL_VERTEX_REACH改瞬时真最低点，最佳9.115mm残差、实际最低点仍在顶面上8.855mm，未证明接触/连续路径；也未安装。这些是离线hindsight探针，不能直接执行求出的q，旧接触中心校准退化保留。
- **FRONT_WORK_EFFICIENCY新证据**：真实895001交换袋lateral623帧仅212帧top_push，另411帧接近/恢复；8次recontact里7次lost_contact，1045一次独立tilt.033894。front推动累计X-109.223mm/yaw-.353585；lateral推动+163.588mmY/yaw+.461950，终点+.012314未达区。按pre-action mode/载荷与下一帧位移归因，非持续接触/积分力证明。优先处理滑移/接触迁移；旧12mm object-relative曾导致另一难盒257.202→13.360mm，不能机械重开或只延长预算。
- 详见current_lateral_profile_r1/CONTACT_AND_EFFICIENCY_DIAGNOSIS.md与3个screen_rear_top脚本/audit_front_work_efficiency.py，均只读诊断未改冻结生产源。磁盘约116GiB可用。全目标不变：当前8条完整证据→解决剩余失败/视野→原随机四族完整组+wait合格→重建合同/转换/共享训练→独立多seed原h10。无合格完整新训练组或新模型，goal active。

## 2026-09-30 最新：左右完整1/4退化；已启动去多余绕行+近落点.5的双组8条件

- **当前唯一物理任务 y_path_nearhalf_groups_r1**：runner31356、batch31530、control31531，05:29:49UTC实际启动；按897002/897003原前后组→897000/897001原左右组，8条各1200帧、seed0，完整类别交换，development诊断。Y_PATH_NEARHALF_PLAN SHA `658e11392f0ef8f67bc311533beac7b685b2970608663889e659ba765ab14439`；源initial_top_route.py由c7ff8306变为`8e6a11fc2fdcd25111d40c976e3c4be13c8fb0ddc13165a7c66f795df5f13904`，collector仍fdf890af。before_y_path_repair备份、INSTALLATION/RUNNING_PROCESS绑定。核心冻结。预期72控制实际报告（8×8基础+6initialtopY审计+1front×2）及9批、8条实际图审。无新训练或进一步自动队列。
- **本次明确是两项功能修正，不是单变量消融**：①剩余targetY→goalY整段与另一物体旋转footprint有>=24mm净距才保resetX，否则仍24mmXcorridor；原10mmparcel/5mmtable/5mmhand/10mmother guards全部保留。②已有显式near fraction .7→.5，两near类别一致，针对残留COP X约12mm；far/其他route该开关不生效。已在4方向例+2真实多余绕行+2真实nearbagguard中核对，并复用11完整状态机检查；实际安装后40接触/协议/转换回归过。独立Y_PATH_CLEARANCE审计拒绝旧错误goal与篡改goal；.5审计拒绝冒充.5的真实.7记录。启动不代表效果已好。
- **父current_lateral_profile_r1完整1/4（比legacy2/4退化）**：正常盒150.793mm/tilt.045721通过；正常袋113.040mm/.001775、交换盒64.701mm/.003885、交换袋165.699mm/.033894均失败。四条非目标maxXY0。34控制实际pass、9批exit0、原三个进程全退出，4条8RGB+4viewer实际view/精确hash并入RESULT/ACTUAL_REVIEW_BINDINGS；RESULT.md完成，整组拒绝无approved review/转换/训练。
- **明确代码级数据问题 UNNECESSARY_X_DETOUR_DIAGNOSIS**：原正常两物体Y净距约138.5mm、沿任务方向远离，initial direct proposal本来允许直推；ClearanceFeedback却不分Y路径，firstpush强制盒X .507799→.403056、袋.585791→.690542，各多绕104.7mm。正常袋新增9重接触、腰约.9824、推距不足。隔离Y路径修正已装入上述8条件测试；只是移除无必要绕行，不声称涵盖所有失败。
- **交换盒仍是独立可达性问题**：后绕后停top_cross，末supportX.623593/goal.636843，误差13.250mm、腰约.98，尚未接触顶部。REAR_TOP_CONTACT_REACH_SCREEN实测末态固定物体IK，20默认/10/5mm inset均400步未到press，handminZ约.901/.874/.860而top约.795；没有采用未通过screen的farinset改法。非全局不可达/全臂碰撞/物理证明。当前两修正未声称解决它。
- **交换袋局部改善但仍失败**：front使8RGB目标都在画内（手遮挡、底部裁切），旧rear171起画外；但finalY约+.0123未到+.20。front_x576/lateral_y623帧，首次575才完成前移，8recontacts，1198一次净空恢复；原guard未触发，仍需提高有效推动/规划质量，不能直接宣称加长预算可成功。正常两条及交换盒仍目标离画明显。
- 近.5隔离screen真实近盒/袋初始cross各可到press，gap≥80.796/107.407mm；最低顶点不是真实COP，未证明物理抗旋转。前后父.7整组3/4拒绝与视觉工作期离画证据保留。下一步先收当前8条按组/类/路线逐项结果，再解决rear reach/front效率/视野；全部原随机族、普通wait、完整准入/合同重建/转换/共享训练/独立192push+3wait多seed h10仍待。无合格完整新训练组或新模型，goal active。

以下为历史记录，以本段为准。

## 2026-09-30 最新：近落点完整3/4拒绝；原随机左右完整组已启动

- **当前唯一物理任务 current_lateral_profile_r1**：runner4075204、batch4075378、control4075379，05:06:00UTC实际启动。895000/895001复用fresh_lateral_00的原几何/yaw/environment seed0、各1200帧四推，明确development、无wait/训练。当前source仍collector fdf890af/initial_top c7ff8306，核心冻结。CURRENT_LATERAL_PROFILE_PLAN SHA `601bd670525979140af2ef313c5930e7ca506b04e096dd1b993245597d7945f7`；run/watch_current_lateral_profile已接线。预期32通用+交换袋FrontTop额外2=34实际控制报告、9批、4条实际图审。无后续自动队列。
- **当前左右profile含多项变更，不能称单变量**：原正常两任务现在选InitialTop，交换袋FrontTop/fraction.9，交换盒TopContact后绕/fractionNone，projected support/法向/.010alignment等继承当前profile。两slot均X>=.48，所以near .7不生效。原legacy左右2/4已4条实际审查与20control；紧前near完整32control/9batch/4图审已闭合。下一步看四条件任务+姿态+实际图像，不用旧失败推定新profile或只看交换袋。
- **父initial_near_contact_depth_r1完整3/4、严格拒绝入库**：近盒150.317mm(max tilt.032185)、远袋227.094mm(.003087)、远盒174.530mm(.047290)通过；近袋80.577mm(.002837)失败。四条非目标maxXY全0。32控制实际pass、9批exit0、原三个进程均退出；全部8RGB+4viewer实际查看/精确hash合并RESULT，近袋另8guard事件实际view。RESULT.md已闭合，无approved review/转换/训练。原门/初始零位/无助推保持。
- **好与差同时记录**：near .7使近袋55.372→80.577mm、首次保护259→367帧，前三条件保留；但总数仍3/4。第367帧同planned_corridor_no_table_margin_5mm，yaw .361845rad，24mm规划桌边4.964mm<5，实际桌边9.898mm/物距19.066mm；未真实掉落，不放宽保护。NEAR_CONTACT_COMPARISON用正确父短恢复、区分真正首轮press：COP X32.961→11.641mm（2/3实际样本），lateral median手r×F yaw矩.078991→.034195Nm，仍95.5%正向。不同后续轨迹样本/最后子步力包，非总积分/唯一因果。旧叙述把全部press中位数称“首次press”不准确，以本次明确定义为准。落点调整起效但未消除转动，不称解决。
- **视觉数据问题已深化**：父短恢复VISIBILITY_DURING_WORK显示远盒379push中248(65.4%)、远袋504中164(32.5%)投影bbox全画外；其中239/155尚未满足任务位置。VISIBILITY_ACTIVE_WORK_REVIEW各8真实事件view/hash绑定，确认未完成时离画、偶尔回画；比例是几何估计、非逐帧分割。CURRENT_CAMERA_CONTACT_REACH保留实际projected reference、.15法向/另一掌/原界，4实录状态两个起点：盒frame840保1%/50%bbox位置误差17.409/29.999mm，袋850为9.272/20.744mm。只离线固定物体位置拟合、非全局不可达/碰撞/动力学，不能执行q或简单限制腰当解决。没有新增可见性门或删除难例；需结合接触路径/正式模型验证可学习性。
- **前侧审计已验证**：audit_front_recovery_height_live.py三真实前侧记录过（approach/3或12recontact/guard覆盖），6内存错标负例拒绝；另原audit_recovery_and_anchor在真实guard轨迹过。只有front-selected轨迹调用额外两项，不能把不适用初始top高度检查当front验证。
- **本轮隔离候选staged_initial_near_half，未启动/未排队**：只将既有near flag .7→.5、两类别统一，目标消除残留~12mmCOP X偏心。真实890002近盒/890003近袋frame6×.7/.5离线4/4到press；.5盒76/袋90步，采样手/另物gap≥80.796/107.407mm，最低顶点相对目标X+19.625/−.225mm（不等同真实COP）。实际parser合法、旧.7记录拒绝误标.5，独立审计脚本准备。当前生产source/profile与左右运行均未改变；完整左右结果闭合后再决定原前后全4物理复测，不能把离线按压当任务成功。
- **完整目标/下一步不变**：当前原左右全组→按实际失败机制继续专家/视野质量；合格完整随机多族+普通等待后重建严格合同、转换、共享训练、独立192push+3wait多seed原h10与实际画面。无合格完整新训练组或新模型，整体goal active。当前工作是progress（完整组闭合/接触与视觉新证据/下一原失败组实际启动），不是完成。

以下为历史记录，以本段为准。

## 2026-09-30 最新：短恢复完整3/4；近处接触落点完整交换组已启动

- **当前唯一物理任务 initial_near_contact_depth_r1**：runner3933256、batch3933376、control3933377，04:43:30UTC启动并实际ps核活，890002/890003同原随机前后几何/yaw/seed0，各1200帧完整四推。只新增显式`--expert-initial-top-near-inset-fraction .7`，initialX<.48且initial-top路线时袋盒统一生效；其余路线/远物体保持。collector SHA `fdf890af67b2d2a24b7c3ae4f0b7b2e84d2ea829d60b6e7014d479db29b6e383`，initial_top_route仍c7ff8306；未改质量/guard/物理。before_initial_near_contact备份，INITIAL_NEAR_CONTACT_PLAN/INSTALLATION/RUNNING_PROCESS绑定。安装后协议+转换**实际19项**测试通过，候选7CLI/32默认等价条件（11near override）通过。期望32控制实际报告+9批审计+四条实际图审。核心冻结，无并行仿真/训练/后续自动队列。
- **新接触版首890002近盒已完整通过**：推进150.317mm、max tilt.032185rad、非目标0；实际fraction.7生效，8控制报告pass。8RGB+4viewer实际查看/EARLY_REVIEW+ACTUAL_REVIEW_BINDINGS绑定；盒右下裁切、袋全采样可见。首次释放485、4重接触；不能据此宣称近袋/完整组改善，其余3仍待。
- **父initial_top_short_recovery_depth_r1完整3/4，整组拒绝**：880002近盒150.604mm/远袋227.058mm、880003远盒174.480mm原task+pose通过；880003近袋55.372mm失败。四条非目标maxXY0，28控制报告实际pass、9批exit0、全部source一致。原三个进程均已消失。4条各8RGB+4viewer实际查看并精确raw/image/frame合并到RESULT与ACTUAL_REVIEW_BINDINGS；近袋另8guard事件实际查看。RESULT.md闭合，无approved review.json/转换/训练。
- **好：**远盒仍9重接触，短恢复使其在同预算内通过，整体由2/4→3/4。**差：**近袋较父70.589mm降至55.372mm；第259帧同planned_corridor_no_table_margin_5mm，独立yaw .117468→.364515rad、规划桌边4.817mm<5、实际桌边8.250mm/物距20.567mm。保留原保护，不以未跌落或低tilt替代成功。远盒终点越区仅0.795mm，RGB513帧后画外；远袋685帧后画外，均保留数据质量/鲁棒性风险，没新增可见性门。
- **接触候选依据及局限**：父margin24的INITIAL_TOP_YAW_CONTACTS记录nearbag首次press法向加权COP X+23.391mm；lateral108样本中92.6%手部r×F yaw矩正、median+.034975Nm。只最后子步力包/非总积分因果证明。fraction.7名义朝机器人偏22.5mm袋/21mm盒，针对初次偏心而非后期迁移；stage MANIFEST已修正当前选择为.7（早期scope曾写.8，已更新）。APPROACH_SCREEN两实际reset状态×fraction1/.8/.7，全部6到press；.7采样手/另一物gap袋93.283mm、盒68.183mm。最低顶点不是真实COP，离线固定对象/瞬时IK不是物理成功证明；新接触审计按实测姿态独立重算surface point，拒绝错标fraction。
- **本轮新增左右实际factory核查** CURRENT_LATERAL_PROFILE_PRECHECK：原840000袋盒当前均选InitialTop；交换840001袋选FrontTop（fraction.9）、盒仍TopContact后绕（fractionNone），全部alignment10mm。旧legacy失败不能冒充当前profile失败。CURRENT_LATERAL_PROFILE_PLAN/895000..895001冻结原左右几何待验证；仅准备，未启动/未排队，须先收当前前后全组及实际审核。多项profile差异明确记录，不能称单变量消融；两slot均X>=.48，本轮near .7在左右组不生效。
- **新数据质量证据 VISIBILITY_DURING_WORK**（短恢复父组）：远盒379推动帧中248（65.4%）投影bbox完全画外，其中239帧任务位置尚未满足；远袋504中164（32.5%），其中155帧未到位。远盒首次投影离画311时仅推进63.102mm；远袋612时158.036mm但y=.131721未到+.20。各8事件RGB实际查看、VISIBILITY_ACTIVE_WORK_REVIEW精确绑定：目标确实在未完成时离画并偶尔回画（盒342、袋630极左细边）。这是训练视觉纠偏风险，不是只撤手后空帧；比例是几何估计不是逐帧分割真值，也没新增质量门/裁去困难帧。已有visible-corner开关绑接触角且与projected互斥，不能机械打开当视野单变量；当前核心仍冻结。
- **左右复测审计准备完成**：run_current_lateral_profile.py与watch_current_lateral_profile_evidence.py未启动。只有front-selected条额外执行FRONT_RECOVERY_HEIGHT与RECOVERY_AND_ANCHOR（其余32报告），预期34控制报告；当前前后全组/32控制/9批/4图审闭合后才可绑定preceding_depth_result_sha256启动。新height auditor在3真实轨迹（无恢复+guard、3恢复+guard、12恢复无guard）通过，6错标/低高度/不适用负例拒绝；已有前侧阶段审计在真实62013过。无新物理左右结果。
- **本轮视野/接触离线筛查** CURRENT_CAMERA_CONTACT_REACH（父短恢复）：4真实状态、当前projected reference随姿态变化、.15法向约束/非活动掌anchor/原关节界，两个起点least-squares；保留1%bbox时远盒后期frame840最小筛得位置误差17.409mm，50%为29.999mm，远袋850对应9.272/20.744mm。无视野约束分别1.512mm/近0。说明简单限制腰可能破坏当前接触目标；不是全局不可达证明，没有全臂/桌/连续路径/力学，不执行离线q。先完成当前近袋和左右组；之后需结合接触路径保持视野或通过正式模型评估验证可学习性，不能假定有成功专家就能学会。
- **完整目标保持**：原随机左右/前后/两类斜向/交换和train-val/test划分全部保留。左右交换袋front/盒接近可达性与相机风险仍需解决；当前profile未在该随机左右组物理验证。合格完整新组→普通wait/合同重建→冻结多样fresh采集→严格转换→共享策略训练→独立192push+3wait多seed原h10/实际画面。没有合格完整新训练组或新模型，goal active。

以下为历史记录，以本段为准。

## 2026-09-30 最新：24mm完整2/4拒绝；近袋规划通道冲突已定位，短恢复完整组已启动

- **当前唯一物理任务 initial_top_short_recovery_depth_r1**：runner3762595、batch3762762、control3762763，04:15:49UTC已实际启动核活；880002/880003同原随机前后几何/朝向/seed0，各1200帧完整4推。新source initial_top_route.py `c7ff8306aaa89aebc3d70c5d13165b10d1623538908114c4bc1e7263989d6718`，只在InitialTopRouteState override recontact_travel_z=.86；首次接近/外层紧急/释放仍.91，24mm规划与原所有质量门不变。before_initial_top_short_recovery备份及INITIAL_TOP_SHORT_RECOVERY_PLAN/INSTALLATION/RUNNING_PROCESS绑定。11候选+29接触+6短恢复测试通过。核心冻结，未启动训练或其他后续队列。
- **父clearance_margin24_depth_r1完整2/4**：近盒150.673mm/远袋227.000mm原task+pose通过，近袋70.589mm/远盒162.614mm失败；非目标maxXY全0。4条各8RGB+4viewer已实际查看，RESULT/ACTUAL_REVIEW_BINDINGS按raw/image/帧精确合并；近袋另8事件实际查看。9批审计exit0、24控制实际pass，父所有进程退出；RESULT.md完整，整组拒绝、无approved review.json。较22mm1/4提升为2/4，但不能扩采训练或声称解决交换。
- **近袋新根因证据CORRIDOR_GUARD_DIAGNOSIS**：第325帧planned_corridor_no_table_margin_5mm；SciPy独立rotation/AABB复算，yaw初始.117468→.364593rad，24mm规划X点桌边余量4.712mm<5，实际物体桌边7.959mm、X物距20.753mm，5mm桌边下当时最多容23.712mm物距。不是实际已经掉落/碰箱，不可把保护放宽当成功。0/140/220/270/324/325/400/1199事件已实际查看：袋旋转、手压/遮挡后抬起，物体未分拣。实际最高tilt.003401rad，主要yaw/通道宽度冲突；缩短恢复候选未声称解决此问题。
- **远盒当版9重接触**：仍因倾斜恢复、未到-.20区；两版本各9真实姿态离线0.86均到press，当前74..77→37..42步，仅瞬时IK证据。下一物理主要验证远盒有效推动时间，同时看另3是否回退；近袋还有一次lost-contact，恢复改变可能改变后续轨迹但无成功保证。不能只看远盒通过就准入。
- **新增实际高度审计audit_initial_top_recovery_live.py**：独立检查已记录初始.91/恢复.86/紧急与释放>=.91及expert waypoint映射；真实父.91轨迹按.91过、错标.86被拒绝，AUDITOR_CHECK留证。watch_initial_top_recovery_evidence.py每条7报告，预期28actualpass+9批，尚无新物理结果前不称通过。
- 前述左右LATERAL_TRACKING_RESIDUAL/MINIMAL_LATERAL_ROUTE_PRECHECK证据保持：袋几何front可行、盒必须另解接近；legacy10mm容差在现有parser要求projected，没绕过。原冻结所有随机族/split/独立测试范围保持。待当前完整组→近袋yaw/通道策略与左右交换→fresh完整准入→转换/训练→独立多seed原h10/实际画面。仍无合格完整新训练组/转换/新模型，整体goal active。

以下为历史记录，以本段为准。

## 2026-09-30 接续：24mm首对2/2通过；交换远盒失败、近袋新保护抬手待定位

- 当前仍唯一物理任务clearance_margin24_depth_r1，runner3610514/batch3610692/control3610693已实际核活。前三完整：870002近盒150.673mm、远袋227.000mm原task+pose通过；870003远盒162.614mm任务失败，tilt.044775rad仍在原门内。前三各8RGB+4viewer已实际查看，EARLY_REVIEW/ACTUAL_REVIEW_BINDINGS逐raw/image/帧绑定，最终renderer后只准精确hash合并。末近袋step1050已initial_top_guard_lift，目标x=.383877/y=-.004994；尚未完整写盘时未确认具体reason，不能猜成桌边或间距。所有核心冻结，未启动短恢复或训练。
- FIRST_PAIR_COMPARISON：近盒旧67lateral/954clearance_x，新188lateral/0clearance_x并释放，余量提前保住间隔而非在旧停滞后恢复；原远袋518→514lateral、都释放，首对未退化。单seed诊断不等于一般鲁棒性。新成功远袋max tilt.003004rad，原质量门全保留。
- 870003远盒当版INITIAL_TOP_RECOVERY_SCREEN又用9真实触发姿态复核：0.91为74..77步、0.86为37..42步到press，18/18局部瞬时IK过，采样手/非目标≥49.595mm。仅固定物体/采样间隙，非接触/物理/连续全臂证明。staged_initial_top_short_recovery MANIFEST绑定新screen，仍未安装/未排队；需等近袋guard定位及整组审查决定下一实验。
- 新左右实录证据LATERAL_TRACKING_RESIDUAL.json（audit_lateral_tracking_residual.py）：840001盒末实际控制点距目标11.807mm，已有command关节角假想完全追踪的FK误差4.394mm；袋20.511→18.218mm，腰分别±.98饱和。URDF FK对实测掌<.1mm。说明盒存在执行残差，但不证明唯一重力/摩擦/IK原因；假想FK不是物理回放，未新增servo/助推/动力学修改。
- MINIMAL_LATERAL_ROUTE_PRECHECK真实parser+原reset：仅开启front route允许且只改变840001袋的几何分支（其他3不选front）；拟同时把legacy对准容差8→10mm被现有parser拒绝，因为要求projected support。保留该拒绝、不绕过约束、不把多项contact变化称为单一容差消融。旧approach_compensation两条皆失败、bounded_servo0/8，均不机械重跑。该front-only候选只是隔离准备，未启动/排队，不能宣称能解决盒。
- 目标与范围不变：全部原随机族、类别交换、split及独立测试均保留；没有合格完整新训练组、转换或新模型。非目标全程稳定/首零位/无助推/h10/原姿态门不变。当前剩余约118.8GiB，存储不是阻塞。

以下为历史记录，以本段为准。

## 2026-09-30 接续：间距反馈全组仍1/4；24mm余量复测正在运行

- **当前唯一物理任务 clearance_margin24_depth_r1**：runner3610514、batch3610692、control3610693，03:51:41UTC启动，实际ps核活。870002/870003复用原失败随机前后坐标/朝向/seed0，完整4推各1200帧。首近盒完整原quality已通过：推进150.673mm、终点y=-.226255、非目标0，首6控制实际pass；原姿态评分也过，max tilt.032329rad；实际8RGB+4viewer已查看并EARLY_REVIEW/ACTUAL_REVIEW_BINDINGS哈希绑定。盒右边裁切、撤手后可见部分稳定，袋全采样可见；完整RESULT生成后须精确hash合并，不能自动批准其他3条。此单条不代表完整组成功。远袋已实际采集中。核心冻结，无并行Isaac/训练或后续自动队列。
- **clearance_feedback_depth_r1全组1/4，完整拒绝训练**：远袋227.082mm通过；近盒55.773mm、近袋26.448mm、远盒163.620mm失败。目标max tilt依次.003257/.045614/.003388/.052768rad，非目标maxXY全0。9批审计全exit0，24控制实际报告pass；四条各8RGB+4viewer已实际查看并精确raw/image/帧SHA绑定，远盒另8重接触事件实际view。全部父进程退出。RESULT.md完整留证。成功数未提升，不用改善倾角或保护触发替代任务通过。
- **新同因证据 FEEDBACK_FAILURE_DIAGNOSIS.json**：近盒954/近袋1059帧clearance_x，最后300帧漂移11.93/16.84微米；Xgap约20.977/20.610mm，恢复要求21mm，对22mm规划目标剩余1.023/1.390mm误差。远盒335帧top_push但9次incipient_tilt重接触，终点y=-.189935未到-.20区；另一独立问题。脚本diagnose_clearance_feedback_run.py已保存，不改原门；仅远盒新event sheet实际查看，其他新event sheet保持pending，区别于已完成uniform审查。
- **已安装唯一变化 initial_top_route.py b8e280aa→93fea6f3**：X规划间距22→24mm；触发18/恢复21/紧急10mm及原外层/姿态/任务门不变。before_clearance_margin24备份、CLEARANCE_MARGIN24_INSTALLATION/PLAN/RUNNING_PROCESS绑定。7实际候选检查、29安装后unittest过；Isaac环境无pytest后改用原unittest runner，不是假报pytest过。runner新预检严格要求父4图审+24controls+9批和hash；无改布局挑容易样本。
- **新远盒恢复离线证据**：screen_initial_top_recovery.py + 860003远盒INITIAL_TOP_RECOVERY_SCREEN.json，9个真实倾斜触发状态，独立URDF FK<.1mm，原工作关节界/投影support/非活动掌anchor/已捕获法向anchor/实际far接触fraction。0.91高度到press74..76步，0.86为37..39步，18/18到press，采样手/非目标面间隙≥49.450mm、手minZ≥.793269m。只固定倾斜物体、瞬时IK，不是动态/全臂/连续路径/视野/物理成功证明。实际--expert-front-recontact-z=.86只传FrontTopRouteState，InitialTopRouteState仍.91，代码分支已核。
- **隔离候选 staged_initial_top_short_recovery，未安装/未排队**：基于当前24mm只将InitialTopRouteState的recontact_travel_z默认.86；初次接近与外层紧急guard仍.91。11实际类检查过（首次/恢复/倾斜触发当帧/紧急高度、原guards/XY/释放）；首次测试3error源于测试夹具缺margin，已补齐，没改生产逻辑来过测试。待当前24mm全4完成、图审/全部审计后再决定，不能中途替换。
- **后续保持完整目标**：先收24mm全4，重点判断两个近物体是否恢复及远袋是否退化；再按远盒重接触证据选择恢复策略。随机左右交换袋front可行、盒front越桌边，应分别处理；相机/腰可达性冲突仍未解决。全部原随机族/split与独立测试保持，无合格完整新训练组/转换/模型，goal active。上个用户Git备份支线已完成并重新核private/remote32e390c一致，不重复授权。

以下为历史记录，以本段为准。

## 2026-09-30 接续：间距反馈首对1/2；发现纠偏停滞与腰/视野可达性冲突

- **当前 clearance_feedback_depth_r1 仍在真实运行**：runner3466641、batch3472001、control3472002核活，已进入860003交换条件。首860002远袋227.082mm原task+pose通过、最高tilt.003257rad；近盒55.773mm失败、tilt.045614rad仍合格。首12控制实际pass。两条8RGB+4viewer已真正查看、ACTUAL_REVIEW_BINDINGS精确raw/imageSHA；近盒另8事件实际view绑定。正式RESULT待完整组/九批，不能让renderer后续pending覆盖此前实际绑定。所有冻结sourceSHA又核一致，无训练/新后续队列。
- **近盒停滞新证据**CLEARANCE_STAGNATION_DIAGNOSIS：1200帧末仍top_push中的clearance_x，最后300帧对象maxXY漂移11.93微米；Xgap20.970..20.977mm，低于恢复门21mm仅约.023mm；相对22mm规划目标X误差约1.024mm。末已测竖向载荷3.346N、bias−6mm限位、support-X命令差1.023mm。只是实录稳态/阶段证据，不证明唯一静摩擦或IK原因。原10mm间距guard未触发，非目标0，但不能当分拣成功。
- **隔离候选staged_clearance_margin24，未安装/未排队**：只把初始顶部规划X间距22→24mm，触发18、恢复21、紧急10mm及所有原质量门不变；旨在给实测~1mm稳态误差增加2mm余量。7实际类guard/释放/重接触/单update/步长/滞回检查过，当前全4物理完成后再决定。不要中途修改运行源，也不要称已改善。
- **新CAMERA_REACH_SCREEN.json**（fresh_lateral_00_pilot_r1）：screen_lateral_camera_reach.py对两真实交换失败终态，以原URDF独立FK核对掌位置<.1mm、实际工作关节界、多起点离线位置IK。无相机约束时袋最优控制点误差17.700mm、盒2.555mm，腰均到±.98；保持原相机目标bbox≥50%投影时腰窗口最近端袋−.695、盒+.655，误差分别44.324/34.520mm。移除非活动掌固定位置约束几乎不改善。只两个状态的局部多起点筛查，不是全球不可达证明；没有姿态/全臂桌碰撞/连续路径/动力学，不能执行解出的q，也没有新增50%质量门。这支持优先改路径/接触，不能只减小转腰。
- 查阅历史确认旧bounded_servo已0/8且差于父4/8，不机械重开关节目标累积方案；本次新协调器不同仍需因果证据，尚未新接线。
- 后续：完整860003双任务、全部24控制/9批/实际图审→判断24mm余量或其它必要修正，再回到左右交换袋front与盒rear难例，全部原随机族/split保持。尚无合格完整新训练组、转换结果、新模型；整体goal active。

以下为历史记录，以本段为准。

## 2026-09-30 接续：direct-clear完整1/4淘汰；间距反馈完整四条件复测正在运行

- **当前唯一物理任务 clearance_feedback_depth_r1**：runner3466641 / 整批3472001 / 控制3472002，已实际核活、真实采集860002近盒。860002/860003复用失败随机前后坐标/朝向/seed0，1200帧/条件完整四推。最近step180仍top_push，越过父step120原间距guard，但尚无完整quality，不能报改善。源码冻结，无新训练/其他Isaac/后续自动队列。
- **direct_clear_repair_depth_r1完整原task+pose仅1/4，整组淘汰**：850002远袋232.744mm过；近盒27.616mm失败（父162.857mm过）；850003远盒164.808mm仍未到−.20区失败；近袋20.462mm失败，虽然max tilt从父.6009降至.003397rad。三失败都parcel_clearance_10mm：近盒120、近袋130、远盒1164。非目标maxXY均0。四条8RGB+4viewer均真正查看、RESULT/ACTUAL_REVIEW_BINDINGS逐raw/imageSHA绑定，近盒8事件另绑定。9批审计全exit0、20控制实际pass。所有旧进程已退出，完整RESULT.md，未准入训练。
- **新候选已安装，仅改 initial_top_route.py**：旧891035f0...备份before_clearance_feedback，新b8e280aa...。在原initial_top opt-in路由内，只覆盖已加载top_push的XY目标；保持原外层10mm物距/10mm非目标/5mm手/5mm桌guard，superclass抬手/下降/按压/失联重接触/释放先行且一次update。当前旋转footprint确定22mm间距目标，重叠Y时Xgap<18mm先保Y纠X，≥21mm恢复侧推；以实际support和物体误差给±12mm期望偏移、command逐步≤3mm。不能当接触稳定或成功保证；原任务/姿态门未改。
- **staged_direct_clearance_feedback证据**：RECORDED_REPLAY在四原记录上shadow，三失败分别提前9/13/407帧发纠偏、无无效规划点，成功远袋不进恢复阶段；仅旧状态回放，非反事实物理。7实际候选类guard优先级/释放与重接触/单次父调用/XY界/滞回/坏输入测试过；安装后29原top_contact测试过。CLEARANCE_FEEDBACK_INSTALLATION、REPAIR_PLAN和RUNNING_PROCESS留证。
- **增加实际控制独立审计**：audit_clearance_feedback_live.py重算记录的旋转包围盒间距、原外层门、实际expert目标映射与3mmXY界；watch_clearance_feedback_evidence.py每条加此项，预期四条24报告。未产生报告前不称通过。整批9审计和actual图审仍必需。
- **Git备份支线已完成，勿重复登录/上传**：用户授权创建私有 https://github.com/daisyzoo/sim-code-backup ，main提交32e390c45b95d397d3d721570fd29db567690d5c，8415文件（源码8411、68.6MiB），远端private和commit一致已核。独立快照位于 `/home/user/Documents/zoo/sim/.code-backup/repository`，BACKUP_STATUS/manifest在父目录；原工作区非Git根。该快照早于本次间距反馈改动，不宣称持续自动同步。原应用连接和SSH属其他账号，不可拿来写daisyzoo仓库；本次按用户完成GitHub设备授权，未使用/保存其明文密码到仓库。后续扫描应排除.code-backup。
- 后续继续整体目标：收当前四推完整数值/24控制/9批/实际图审，判断纠偏是否恢复全组而非只延后guard；再修左右交换袋前路、盒后路可达性与腰/视野冲突。原12随机组与split不变，失败不训练，不选容易布局冒充。尚无合格完整新训练组、转换数据或新模型；goal active。

以下为历史记录，以本段为准。

## 2026-09-30 接续：左右图审完成；direct-clear 同几何完整组已启动，近盒出现退化信号

- **实际当前物理任务 direct_clear_repair_depth_r1**：runner3305181、整批审计3307741、控制3307742，03:02:34 UTC启动。850002/850003为fresh_depth01完全相同坐标/朝向/种子、不同diagnostic ID；四推1200帧。850002近盒完整写盘失败：推进27.616mm，父同条件侧推162.857mm通过。第120帧parcel_clearance_10mm触发，X后移9.579mm、yaw+.117468→−.168668rad令间隙21.141→9.729mm，独立重算与guard一致。TOP_ROUTE_GUARD_REGRESSION和8事件RGB已实际查看/哈希绑定。当前接续850002远袋，完整组仍待；不得直接扩采该候选。核心冻结至完整组结束，无其他Isaac/训练/后续自动队列。
- **fresh_lateral_00_pilot_r1完整图审与数值收尾**：四推2/4，wait原门+独立门过；20控制实际pass。各8RGB+4viewer真正查看并RESULT/ACTUAL_REVIEW_BINDINGS逐raw/imageSHA绑定，wait8RGB另ACTUAL_REVIEW_BINDING。原旧renderer误遍历wait无POSE文件而退出，后用已存在partial renderer显式840000/840001生成4条再写最终RESULT，没有假装第一次成功。整组拒绝，无approved review.json/转换/训练。
- **左右失败机制与视觉风险**：交换袋rear_push1163frames，X后移186.852mm，实际后绕目标约.7668m未到；交换盒top_descend1046frames，末support与目标XY差约8.55mm，原alignment8mm，load0。两条非目标maxXY0。全部840001采样RGB171起两物体均画外；840000成功两条也目标171起画外。只判为数据风险，未新增可见性硬门。原相机安装不改。
- **SWAPPED_ROUTE_AND_VISIBILITY_DIAGNOSIS.json真实记录几何复算**：袋front可行、路径.448m比rear.604m短；盒front跨前桌边16.284mm、不合格，rear仍可行。不能两任务一律front。相机原姿态投影在末轨迹分别存在waist−.695/+ .655rad可保留目标bbox约50%的候选，而实际约−.98/+ .98；只是投影，不证明IK/接触/遮挡可行。audit_fresh_lateral_routes.py保存，未接线新相机控制。
- **已实际安装三候选（备份before_direct_clear_repair_install）**：initial_top_route_candidate ad84f7ef...（far_x.36/min_transfer.15），waist_pilot_protocol4896bd63...、waist_pilot_audit752f12eb...（已记录数据核历史快照，新采集仍严格live源码）。DIRECT_CLEAR_REPAIR_INSTALLATION记录。26安装后测试通过（8协议、12转换、6路由）；路由旧near/short默认预期随明确实验变更更新，另保留显式旧阈值/障碍负控。
- **INSTALLED_FROZEN_DATA_VALIDATION真实安装后检查通过**：旧合同用于新采集被当前源码变化拒绝；历史完整snapshot验证通过；旧840002近盒单条仍通过，840003两失败仍被原task/pose门拒绝。无mock hash，仅单条/来源正确性，不是整组准入。历史隔离11+20测试报告仍保留。
- 下一步：收当前完整四推、九批审计、20控制、实际事件/均匀图审。先解释near盒保护抬手（等待完整frontal日志），核near袋与far盒是否改善；不能放宽guard补分。左右新失败的front可达性与camera/waist冲突仍待针对性修复。全部冻结12随机组和train/validation切分保留，未筛掉难例。整体goal active，无合格完整新训练数据或模型。

以下为历史记录，以本段为准。

## 2026-09-30 进度同步：首两个随机组均 push 2/4，当前采集已退出

- fresh_lateral_00_pilot_r1 已于 02:52:46 UTC 完成全部四推及等待，STATUS=numeric_complete_actual_visual_review_pending，original_tasks_passed=3/5（含等待）。四推中 840000 袋/盒通过，840001 交换后盒/袋分别推进 65.316/119.147 mm、均未通过原任务门；整组不准入。完整实际画面复核仍待，不把数值完成当作图审完成。
- 本次同步实际 ps 核验：run_fresh_waist_pilot、watch_fresh_pilot_controls、continue_fresh_pilots、collect_paired_sorting 均无运行进程。R2 队列仅安排此组，现已收尾；当前没有后台采集或新训练。
- fresh_depth_01_pilot_r1 已完成实际图审及准入复算：四推 2/4、等待通过，完整组拒绝训练。两组随机结果不能由之前固定模板 4/4 替代。尚无合格完整新训练组、转换结果或新模型。
- 新准备但尚未安装：staged_frozen_data_validation 的历史快照验证候选，11 个真实数据/负向检查及 20 个回归测试通过；新采集仍严格核 live 源，历史数据逐项核冻结快照，不放宽质量门。生产文件仍旧版。
- 新准备但尚未执行：DIRECT_CLEAR_REPAIR_PLAN.json、run_direct_clear_repair.py，复用失败前后几何与种子、完整交换组 850002/850003；真实 CLI preflight 通过。direct-clear 顶部接触路由候选仍隔离，尚无物理改善结论。须先完成刚结束 lateral 的实际图审，再备份安装候选、同几何复测。
- 下一步保持整体目标 active：完成 lateral 画面/原因定位；验证接近与接触修正能否同时解决前后组远盒推距不足、近袋倾起回退及左右交换可达性；整组原门合格后再继续冻结多样布局采集、转换训练及独立多种子 h10 验证。

以下为历史记录，以本段为准。

## 2026-09-30 最新：首随机前后pilot完整2/4拒绝；两种侧推失败定位，左右pilot正运行

- **当前真实物理任务 fresh_lateral_00_pilot_r1**：runner3131934 / control3132068 / scheduler3118772，02:34:06 UTC启动，840000推盒已完整原门通过，袋仍采集中；整个4push+wait未完成。核实际/proc后续确认，不以STATUS当存活。源码仍e165 collector及原38物理依赖，不修改当前冻结源。
- **fresh_depth_01_pilot_r1已完整结束，2/4原task+pose、wait通过；整组拒绝训练。**840002近盒162.857mm、远袋231.873mm通过；840003远盒134.037mm失败、近袋260.643mm但最终Y=.185061m且tilt.600912rad失败。20逐条控制实际pass，不能代替轨迹质量门。4条各8RGB+4viewer、近袋事件8RGB、wait8RGB均实际查看/哈希绑定，RESULT.json/md、PILOT_ADMISSION_RESULT.json完整留证。失败两条真实生产audit明确拒绝，没写任何approved review.json；原成功半边+wait不单独训练。
- **远盒原因证据**SHORT_TRANSFER_ROUTING_FAILURE.json：direct路径几何允许（间隙22.304mm），因到goal-.205的转移178.684978mm≤启用阈值180mm，initial_top_selected=false；侧推58帧后hold1099，最终signedY=.160352，X后移60.604mm，非目标0。这是分支证据，非顶部一定能成功的因果证明。
- **近袋更严重独立问题**TIPPING_RELEASE_REGRESSION.json：第73帧goal_release时中心抬高32.450mm，Y=.205305；之后回退20.245mm至.185061，最高tilt.600912rad超原.20。实际事件0/69/72/73/74/75/80/1199看见倾起/落平，uniform171+图会漏掉瞬态。非目标盒maxXY=.254379mm仍合格。只增加释放余量无法修复之前姿态失败，不能放宽门。
- **当前隔离候选（均未应用/未物理验证）：**initial_top_short_transfer_candidate.py只把route transfer阈值改.15，实际远盒reset几何+near/blocked负控过；随后发现near袋失败，单这一改动不完整。initial_top_direct_clear_candidate.py从原helper把far_x=.48→.36、min_transfer=.18→.15（验证允许.15），在路径clear时覆盖near/far顶部接触，仍保留object envelope/原guard。DIRECT_CLEAR_TOP_CANDIDATE_CHECK对两真实失败reset/quats均变为proposed且blocked反例拒绝，只几何回放；REQUIRED物理核心未改。
- **队列调整有明确证据：**原FRESH_PILOT_QUEUE_R1（3051696）仅waiting、未启动下一组，因上述新失败已核身份SIGTERM并确认退出；旧state备份BEFORE_RESCHEDULE，最终cancelled_before_next_start_for_routing_fix。新R2（3118772）只串行接续lateral00，现真实运行；无重复Isaac。剩余原随机布局/切分保留，未重采/删难例，待修正profile再安排，避免已知边界缺陷下继续盲扩前后。
- watch_fresh_pilot_controls.py已接入：跳过wait、精确合同hash、每push五项真实报告pass+退出码；首depth20全过，lateral自动同审。run_fresh_waist_pilot自动保留完整质量失败并继续其交换条件及wait，运行异常停止无重试。没有附加旧9批watcher（其假设纯diagnostic push协议）。实际newpilot图可用prepare_partial_visual_review，wait单独EVENT_REVIEW，不能自动批准图审。
- 12份r2合同已全部生成，但只允许首次尝试采集，绝非成功/训练认证。新增6斜向/反斜向依normal完整depth+ordinary wait同profile证据允许新几何试采，FRESH_DIAGONAL_PROFILE_SCOPE明示外推风险，未启动/排队。连续布局48push+12wait/12组四族，各2train+1validation，种子与split全保留；未读独立测试几何调参。
- **下一步务必整体推进**：收当前lateral完整结果/实际图审；在其全部退出后，验证direct-clear顶部候选的完整相同几何交换组（保留原始布局/seed/预算/质量门，新的diagnostic ID/新目录），确认near袋倾起与far盒不足一起改善，再fresh同预先布局，不只修一条。当前partial新数据已提示仅旧模板4/4不足以保证随机范围。
- **接续实现注意（尚未改，非阻塞）：**现validate_feasibility默认核当前物理源SHA；生产audit_waist_pilot_episode调用同validate_waist_contract，所以将来改helper会让旧合格pilot仅因当前源码变化而不能转换。收新profile前需做隔离、严测的历史快照验证模式：采集准入继续严格核live源码；已记录数据的转换核精确合同、采集snapshot/provenance、原始质量与图审，不以当前helper替代历史代码。每个曾记录源有snapshot时逐SHA核；没snapshot的资产继续要求live匹配，否则不能证明。不得简单删除全部source gate。当前尚无合格整组新训练数据/转换/模型，此项准备可与当前lateral并行，不改运行中的冻结核心。
- 保留目标active，未完成非阻塞。后续合格全组/切分→转换、train-only统计与任务/阶段曝光→共享RGB+11D模型→冻结独立几何多seed h10/实际图审。新成功near盒3/73/1124、远袋3/844/353显示有效活动严重不均，不能按1200帧均匀采样或裁剪失败。

以下为历史记录，以本段为准。

## 2026-09-30 最新：左右复测4/4恢复，普通等待通过；新鲜pilot已经真实开采

- **当前唯一物理任务 fresh_depth_01_pilot_r1**：runner3009930，02:15:11 UTC启动。真实AppLauncher/环境启动成功，case_840002的pilot provenance、合同快照已核；840002近盒step90已goal_release，但完整1200帧尚未写盘，不是通过结论。run_fresh_waist_pilot依次840002/840003各双任务+841001普通wait，共4push+wait；每布局独立进程，完整质量失败保留并记录交换条件，运行异常停止、不自动重试。核心源码冻结，不并行Isaac/训练。
- **好结果 legacy_lateral_return_r1完整4/4，normal同组2/4。**62000袋355.665848mm/盒356.155053mm，62001袋160.023004mm/盒160.796016mm；非目标maxXY全0。9批审计全部exit0，20控制实际reportpass+exit0，4条各8RGB+4viewer已实际看完并raw/imageSHA/帧列表绑定，完整group readiness=true。全部旧采集/审计PID已完成。RESULT.md/PARENT_COMPARISON.json留证。
- **机制证据：**normal困难袋1044帧top_descend、盒1056帧top_cross；legacy分别236/215帧top_push并释放。两版均rear route，非front选择导致；接触参考/姿态等设置组合改变，非单因素因果。源/布局/seed0/1200帧与normal相同；历史baseline为960且旧source，不混称逐字复现。实际目标后段裁边/画外仍保留风险。phase4800=start12/active1974/terminal2814（58.625%tail），不同难度活动曝光差异大。
- **legacy_lateral_wait_r1已完整通过**：63200，70帧seed0，无probe/force/idle，原门+独立重算passed，双掌spread2.098291mm，腰state3.087e-9rad、action0。真实8RGB已查看空桌稳定，EVENT_REVIEW/WAIT_STABILITY_AUDIT绑定raw/imageSHA；runner2989622已结束。这仍是诊断等待。
- **生产collector准入已实际安装**：旧SHA fde8f293...备份before_fresh_waist_admission，安装e165e7809e8aa34da0e47aa3698eceade962841924778a1c88637dbc3465f971，FRESH_WAIST_ADMISSION_INTEGRATION留证。collect函数除合同metadata外AST完全一致，main只准入/合同布局/快照变动。真实启动前/后配置修复在生产路径CLI及实际首pilot启动均过；未改物理/专家依赖。旧诊断仍旧source证据，后续勿重跑需要旧collector当前SHA的老runner/audit来覆盖已冻结readiness；正式合同validator允许仅collector准入变化。
- **6份新鲜合同可用、只准许采集：**fresh_pilot_contracts_r1 的depth01/05/09_r2（normal完整depth+normal普通wait，2train+1validation）与lateral00/04/08_r2（刚通过legacy完整组+同设置wait，2train+1validation）。旧fresh_depth_01.json仍被r2替代未用。四摆放族12组连续随机提案预先冻结，FRESH_PILOT_COLLECTION_PLAN记录意向profile，斜向/反斜向6组尚无合同/新物理证据，不能悄悄缩小目标或按成功改split。
- **执行准备：**run_fresh_waist_pilot.py已实际运行；FRESH_PILOT_EXECUTION_PREFLIGHT对3次独立调用的真实pre/post配置通过，FRESH_INSTALLED_COLLECTOR_CLI_CHECK对生产路径正/负控通过。新runner自动做contacts/pose以及wait audit/render；并未附加旧9批审计watcher（它们假定纯push协议/目录）。后续实际新数据必须做原task+pose/全组/实际图审及来源核验；可用prepare_partial_visual_review仅取已完成push cases渲染，wait有独立REVIEW_EVENTS，禁止凭生成sheet自动approve。
- 后续持续：完成当前fresh全组真实数值/图审/控制检查，整组合格才写每case review.json；生产转换器checked_sources严格核全部合同覆盖、train/validation/task/wait，不接受diagnostic/失败。再按固定随机计划采其他组，保留失败与范围缺口；汇总合格数据后转换、train-only统计与任务/阶段采样、共享RGB+11D模型、冻结独立几何多seed h10。**尚无合格新训练数据、转换数据或新模型**。目标active、非阻塞，不以本次专家成功或启动pilot作为完成。

以下为历史记录，以本段为准。

## 2026-09-30 最新：normal 前后4/4合格、左右2/4回退；旧接触方案左右复测真实启动

- normal_return_depth_a_r1 完整4/4原task+pose，9批审计和20控制实际pass、4条真实8RGB+4viewer复核及SHA绑定完成；COMPLETE_GROUP_READINESS=true。推进215.292/215.765/197.041/190.655mm，非目标均0；远盒终态只超原.20m门.655mm，不新增/放宽门。4800帧中保持尾段2907（60.56%），目标裁边/画外仍需在模型中验证。
- normal_return_lateral_a_r1完整2/4：62000袋92.998mm、盒138.358mm失败；62001袋160.073mm、盒161.178mm通过。非目标均0，9批审计+20控制真实pass和4条实际图审齐全；整组不准入。RESULT.md已汇总。旧normal所有进程已退出，未继续报为运行。
- **当前真实运行 legacy_lateral_return_r1**：2026-09-30 01:51:54 UTC启动，runner2861973 / batch2862185 / control2862186。62000/62001双任务4条，1200帧seed0，38源不变。返回历史baseline左右4/4的接触设置，加terminal joint hold；历史是960帧，非单变量/逐字复现。两版实际均rear route，不能归因于front route选择。期间不应用collector候选。
- **真实准入修正：**AppLauncher原地改写Namespace，旧入口把启动前args与启动后provenance比，真实会误拒绝；隔离stage现在分别核prelaunch和resolved配置。真实AppLauncher注册/配置解析+完整物理证据validator检查通过，改布局/seed/physics_gpu/腰界拒绝，无app/物理pilot。staged collector SHA e165e7809e8aa34da0e47aa3698eceade962841924778a1c88637dbc3465f971，未应用。
- **首份可用合同已创建**fresh_pilot_contracts_r1/fresh_depth_01_r2.json，SHA32506af17d67555f30882fa59d71930d580feb39a170dd32a0b71fa316a26924，绑定normal完整depth+普通wait、fresh840002/840003、wait841001，train split；只准许新采集，training_ready=false。旧fresh_depth_01.json被替代、未使用，保留证据。REAL_CLI_CHECK绑定真实前/后配置检查；9 helper tests和8 wiring checks通过。
- 连续随机摆放提案fresh_pilot_layout_proposal_r1已冻结：12完整交换组48push+12wait，四布局族各2train+1validation，位置/yaw采样，seed2026093001；跨split槽位最小.046582m，未参考独立测试几何。proposal不是物理合格；当前仅第一depth合同可用，其他待合格证据/新合同，不按成功情况重分split。
- 后续：完成legacy左右完整数值/实际图审；全部采集退出后备份并应用已验证准入candidate，实际fresh depth全组4+wait，原门/实际图审；继续其他布局族并转换、train-only统计/阶段曝光、共享模型及独立多seed h10。没有新pilot物理数据/转换训练数据/新模型。整体goal active，未完成、非阻塞。

以下为历史记录，以本段为准。

## 2026-09-30 最新接续：normal前后首对2/2通过，lateral_a已安排串行接续；新鲜合同生成器准备

- normal_return_depth_a_r1仍真实运行，runner2590798/完整审计2591018/control2591019；已进入62005。62004两条完整原task+pose **2/2**：袋215.292403mm、盒215.764636mm，非目标均0；整批planned4未完成。没有新训练数据/模型。
- 62004两条各8RGB+4viewer真正看完，ACTUAL_REVIEW_BINDINGS共2；袋0/171/342可见、513后画外，盒下/右裁切，晚段采样稳定。仍需整批RESULT精确SHA/帧列表合并。SETTLED_QUERY_PHASE_AUDIT：袋start3/active974/terminal223（release950）；盒3/87/1110（release74）。不能按帧数量把两任务保持曝光混为均衡。
- **新增真实串行接续任务**continue_normal_group.py，scheduler2641810已核活；NORMAL_RETURN_LATERAL_A_CONTINUATION.json为waiting_for_existing_collector。它等待当前runner2590798实际退出且STATUS完整，再确认无遗留collect_paired_sorting进程，执行normal_return_lateral_a_r1（62000/62001×双任务4条）。不会自动重试运行异常；超时只记录需检查，不认定进程已停。新组真实PID将在其RUNNING_PROCESS写出；当前尚未启动第二个Isaac。运行/控制/整批审计会自动附带。当前两组使用同38冻结源，不可中途应用pilot/eval候选。
- **新鲜合同入口已准备而未激活：**build_fresh_waist_pilot_contract.py与FRESH_PILOT_EXECUTION.md。先重算完整可行性和真实普通wait，核实际图审/raw/source/semantic settings、完整新ID/split布局与pilot collector SHA；验证.pending完整合同后发布，不覆盖，不将诊断晋升pilot。真实normal_return_wait复算过、篡改腰范围拒绝、真实失败bounded12拒绝且无合同输出；FRESH_CONTRACT_PREPARATION_CHECK绑定当前builder。成功合同/真正pilot仍未测或创建。
- builder最初要求全部全局资产都有snapshot而在hand_collision.usda拒绝，已修正为正式validator的REQUIRED_SOURCES快照；其余全局非collector冻结文件仍逐SHA核当前源，原门无变化，失败首次未写合同。每合同允许单完整组/单split（生产转换器支持多合同，并在合并后要求train/validation各任务与wait覆盖），没有新增“每个合同必须双split”的捆绑关口。
- 后续完整depth_a与lateral_a结果/实际图审→合格全组准入新鲜随机多样pilot，继续其余开发/困难布局范围，避免无限只调专家；真实转换/train-only统计/任务阶段采样、共享模型、独立未调参几何多seed原h10仍待。整体goal active；本轮有实际新2/2结果/图审、下一组串行调度和真实准入拒绝检查，非阻塞。

以下为历史记录，以本段为准。

## 2026-09-30 最新：限超前完整6/12淘汰；普通等待通过；normal新鲜depth_a正在运行

- **当前真实运行**normal_return_depth_a_r1：runner2590798、整批审计2591018、控制审计2591019，01:09 UTC启动，62004开始。三PID核活，38源SHA全匹配；normal设置关闭center/lead，62004/62005×双任务完整4条、1200帧seed0。不是旧源码逐字复现、不是pilot；新结果尚待。RUNNING_PROCESS、PROTOCOL和三个normal_return_depth_a日志已落盘，无训练/其他Isaac队列。当前冻结核心不改。
- **已完整淘汰bounded_top_lead24_groups_r1：6/12，normal10/12、直接center父6/12。**六top全失败、六side通过，三个交换组各2/4。新62008袋17.303996mm/盒−.379123mm失败；62009袋161.018737mm/盒161.968000mm通过。12非目标maxXY全0；六same-scene任务对及三完整交换组覆盖过。完整readiness false精确六task/pose失败；失败不入库。
- 全12各8RGB+4viewer真正看完，ACTUAL_REVIEW_BINDINGS和最终RESULT逐raw/imageSHA+帧列表精确合并。62008推盒两物体全部抽查RGB可见仍停滞；62009袋左下裁切、盒171后画外，视觉风险逐条留证。RESULT.md/PARENT_COMPARISON完整好差结果；INTERIM_RESULT/PARTIAL仍保留早期10条快照，不覆盖最终。9整批审计全exit0；72逐条control报告实际pass且exit0，全手-非目标记录接触0、61帧/条件手hull间隙正（非全子步证明）。旧三个PID2193532/2193574/2193575已完成，不再当后台采集。
- SETTLED_QUERY_PHASE_AUDIT完整更新：六成功7200帧start18/active1567/terminal5615（77.986%tail）；其中62004近盒原门通过但未额外goal_release，3/1143/54，active不是有效推动。其他五条terminal共5561，须真实新训练按任务/阶段曝光，不裁失败、不凭标签认定可学。
- **新好结果normal_return_wait_r1已完成：**普通空桌70帧seed0，无probe/force/idle，原门+独立WAIT_STABILITY_AUDIT passed，双掌spread各2.098291mm<15mm，腰maxabs3.087e−9rad<.01rad，action全0。0/9/19/29/39/49/59/69八RGB已实际查看，空桌双手稳定；EVENT_REVIEW及WAIT_STABILITY_AUDIT均raw/imageSHA绑定。runner2554264已退出。这是诊断等待，非模型/训练准入；RESULT.md留证。
- 模型评测1.0rad入口仍仅隔离staged_waist_policy_evaluation，23实际CLI前缀检查通过、执行后半除metadata字节一致；未应用/无模型物理验证。现生产policy范围.80限制仍在，不能忘记正式模型评测前按最新pilot源码小补丁整合（不要整文件覆盖），冻结model/processor/预算/工作界。normal新鲜采集期间保持源码冻结。
- 下一步收新depth_a完整4/原门/实际图审/审计，完整合格交换组可按B→C推进fresh隔离pilot；其余开发组及困难范围仍继续，不无限围绕已淘汰lead调参。然后真实转换/train-only统计/任务阶段曝光、共享RGB+11D训练、独立未调参几何与多seed原h10。整体goal active，未完成，没有新训练数据或模型。本轮有完整淘汰结论、真实普通等待通过、下一鲜测运行，非阻塞。

以下为历史记录，以本段为准。

## 2026-09-30 最新接续：限超前8条仅4通过，已实际图审8；模型评测范围接口隔离准备

- bounded_top_lead24_groups_r1三PID2193532/2193574/2193575核活；62008袋仍运行，未整批终态。38核心冻结未改，当前无其他Isaac/训练。COMPLETED_CONDITIONS实际复算8/12、4通过；新62004远袋仅6.306900mm失败、末top_push，近盒213.874320mm通过、末hold。全8非目标0；候选不采用的决定保持，不再盲调lead。
- 62004两条各8RGB+4viewer已真正查看并raw/imageSHA绑定，ACTUAL_REVIEW_BINDINGS共8。远袋0/171可见但手遮，342后大部左画外仍有部分边缘；近盒底右裁切，袋始终可见，晚段视角缓慢变化。失败不训练，数值通过不冒充视觉学会。
- 62004近盒未goal_release：末signedY .20387432满足原.20门但不达专家额外.205释放界。原phase已有hold，按真实q/action尾段稳定重算start3/active1143/terminal54；不把active标签等同有效推动，也不静默放宽稳定门。需鲜测normal后重新审实际曝光。
- 新发现模型执行CLI无法使用专家1.0rad范围：enabled分支正确传腰且默认无slew，但extended开关排policy，普通上限.80。隔离staged_waist_policy_evaluation已备默认off显式policy评测选项，23实际CLI前缀检查全过，执行后半除新增metadata字节不变。拒绝h50/无seed/旧锁腰/force/probe/expert/slew/越界/nan等。未应用、未启动模型或物理，不是端到端结论。合并应对届时最新pilot源码做小补丁，不能整文件覆盖；README/MANIFEST/CLI_CHECK留证。
- 当前12完整数值/实际图审/9批审计与control真实pass收尾后，执行已备normal新鲜完整depth_a及普通wait，再其余开发组与fresh隔离pilot；随后真实转换/train-only统计及任务阶段采样、共享模型、独立多seed原h10。整体goal active，没有新可训练数据或模型；本轮有实际新失败/图审及执行接口准备，非阻塞。

以下为历史记录，以本段为准。

## 2026-09-30 最新接续：限超前已有3失败，上界9/12低于normal10/12，确定不采用

- 当前bounded_top_lead24_groups_r1三PID2193532/2193574/2193575仍真实运行，已进入62005袋保持；38核心源SHA再次全一致，无额外Isaac/训练队列。原task+pose完整写盘5条2通过；全12尚未终态，禁止报最终分。
- **新坏结果：**62005远盒仅13.938673mm失败（原normal195.341mm通过），center114，971top_push、actualreference轴偏22.7899mm、独立lead误差1.12e-7m，最高tilt.1472°；仅初次对中，无lost/tilt恢复，未release。与62013袋/盒相同停滞类型，所有已完成非目标0。
- **决定已由实测支持：**REJECTION_BOUND_COMPLETED_5固定快照与REJECTION_BOUND绑定本批PROTOCOL、5条raw及normal完整readiness。3失败使剩余全过也最多9/12，严格低于同固定12/1200/seed0的normal10/12；确定reject_as_default_expert，非最终总分/多seed因果宣称。保留既定整批证据后回normal，不再无证据调lead参数。
- 新62012袋161.211737mm/盒162.248351mm均原门通过；各8RGB+4viewer已真正查看并SHA绑定。ACTUAL_REVIEW_BINDINGS现4，62012袋171后大部左画外、盒底右裁切，采样末姿态稳定。62013失败两条与盒事件图审保留。最终RESULT仍待全12哈希精确合并。
- 当前逐条31项审计真实pass+exit皆过（5条件，3top×7+2side×5）；原normal/hold-input审计修正保持。目标停滞不是日志没有启用限制。
- **后继准备仍未执行：**run_normal_return_group新增实际case完整性核验（两个1200×23任务/raw/quality均完整才记录；退出码0缺项拒绝，完整写盘的明确质量失败exit0/1保留；其他运行异常停止、不自动重启）。真实62013失败双任务+缺项负控通过，NORMAL_RETURN_COMPLETION_CHECK绑定，8组实际只读CLI重新核验当前runner，NORMAL_RETURN_GROUP_PREFLIGHT更新。
- **正常等待入口已备，无物理结果：**run_normal_return_wait.py、audit_normal_wait.py、NORMAL_WAIT_PREFLIGHT/PREPARATION_CHECK。normal设置，layouts0/wait1/ID63000/70帧/seed0，原双掌15mm/腰10mrad/零位/无助推门保留；不接受旧主动转腰probe作为稳定等待。实际collector CLI通过、历史probe负控拒绝，临时fixture删除。推动review_diagnostics固定索引120不适用于70帧wait，新等待按实际0/9/19/29/39/49/59/69取RGB且actual review仍pending；普通等待未启动/排队。需本批完整结果/实际图审后再执行。
- 下一步整批余7条与full audit/actual图审→回较好normal鲜测完整depth_a及其余开发组/空桌wait→fresh合格pilot、真实转换/train-only统计/任务阶段曝光、共享RGB+11D模型、独立几何多seed原h10。整体goal active，未完成，没有新训练数据或模型；此turn有新实际失败、明确淘汰决定与等待/采集完成性准备，非阻塞。

以下为历史记录，以本段为准。

## 2026-09-30 接续：限超前首个困难布局0/2，证实有效限制却推进停滞；返回normal完整组入口已备

- **当前仍真实运行**bounded_top_lead24_groups_r1：2193532/2193574/2193575已再次核活，62012盒约1020帧保持中；38冻结源SHA全部不变。未排其他Isaac/训练队列。已完整62013双任务，原task+pose**0/2**，不能提前报完整12。
- **坏结果明确：**62013盒推进30.151807mm失败，对中父159.402587mm失败、normal父父325.549327mm通过。center158，931top_push帧，独立lead误差4.16e-8m/实际reference轴偏22.7195mm；无倾斜/失联恢复（仅初次对中），最高tilt.2206°。330..1199盒XY范围仅约.00131/.21993mm，水平手接触力norm中位.004512N、向下约4.99994N，维持接触却停滞。BOUNDED_STALL_RESULT、LOADED_CONTACT_OFFSETS、CONTACT_LEAD_DRIFT保存，不将减少recontact当成功。
- 62013袋推进−.559524mm失败、非目标0，center106、1035front_x top_push（未进入后续lateral排序），独立lead误差6.49e-8m/实际reference轴偏20.2094mm，最高tilt.0456°；仅初次对中，无lost/tilt恢复。法向约5N、水平力极小，CONTACT_LEAD_DRIFT/BOUNDED_BAG_STALL_RESULT保存。控制限制本身执行正确，不足以持续驱动物体。
- 两条共14实际报告pass+exit核验均过（含新lead独立FK重建和修正后的hold-input），不是未启用开关。实际查看盒0/158/269/300/330/600/900/1199八事件并EVENT_REVIEW raw/imageSHA绑定；两条均匀各8RGB+4viewer也真正查看，ACTUAL_REVIEW_BINDINGS共2。袋手遮/底裁，盒右裁、bag画外，后段图像姿态近静止；失败不训练。最终完整RESULT仍待按全部SHA/帧列表合并。
- **返回较好设置的准备，未执行：**run_normal_return_group.py、NORMAL_RETURN_DEPTH_PREFLIGHT/NORMAL_RETURN_GROUP_PREFLIGHT、NORMAL_RETURN_GROUPS.md。使用normal设置与当前38源，关闭center/lead，每个完整交换组4条独立新输出，不将混合失败整批切片宣称合格；原8组62000..62015全部实际CLI只读验证过，未知/独立测试组拒绝，无队列。此为新源码默认关闭两特性的鲜测，不能称字节同旧源码或拼同批32/32。运行须当前12全终态/实际图审/9审计/实际控制pass；runner通过编译，尚无新鲜normal结果。
- 按BOUNDED_LEAD_EXPERIMENT_DECISION继续完整12对照；若整体仍回退，不继续无证据调lead参数。优先鲜测normal已完整通过的depth_a，再其他开发组/等待；完整合格组可按B→C进入fresh隔离pilot，困难组保留目标范围。用户原整体共享策略目标active，未完成，没有新训练数据/模型。本turn有真实负面物理证据/实际画面与执行入口准备，非阻塞。

以下为历史记录，以本段为准。

## 2026-09-30 最新：对中完整6/12回退；两项审计修正留证，限超前24mm真实新批运行

- **当前真实运行**bounded_top_lead24_groups_r1，runner **2193532** /完整审计 **2193574** /逐条控制审计 **2193575**，00:07 UTC启动，62013运行中。三PID已核活，新PROTOCOL全部38源SHA一致；同62013/62012/62005/62004/62008/62009×双任务、1200帧seed0，只比对中父版新增`--expert-top-object-relative-lead-m .024`。无训练/其他后继队列，核心冻结到本批结束。未有新候选成败结论。
- **父contact_center_groups_r1已完整收尾：原task+pose6/12，normal父父10/12，明确回退。**depth/diagonal/reverse_diagonal三组各2/4，完整组均不具备准入。6条顶部校准任务全失败，6条普通侧推通过；全部非目标maxXY0。新62008袋201.836mm失败，盒170.497mm失败；62009袋160.413mm/盒161.913mm通过。12条各8RGB+4viewer实际看完，全部raw/imageSHA及帧列表合并RESULT；9整批审计完成，六同场景配对一致/三交换组完整。父三个PID1771898/1771957/1771958均已退出。RESULT.md/PARENT_COMPARISON/COMPLETE_GROUP_READINESS完整保留失败。
- 62008盒独立center102commit；1lost+11tilt，最高2.441°，原门未放宽。front命令lead56.408mm、lateral65.420mm/接触偏移61.306mm，13段push有独立URDF姿态/force记录，CONTACT_LEAD_DRIFT/CONTACT_PATCH_REACQUISITION。支持接触迁移假设，非确定动力学因果。
- **数据风险：**本版6成功条7200帧，start18/active503/terminal6679=92.764%保持尾段；SETTLED_QUERY_PHASE_AUDIT与TRAINING_EXPOSURE_RISK保存，不是可训练集。远物体画外/近物体裁边/手遮挡仍明示，62009盒171后采样RGB画外。后续必须保留完整轨迹、任务/阶段采样及train-only统计。
- **两项审计修正已完整留证，不能再仅看exit0：**①旧normal同float32法向量造成acos假角，原失败备份，修正审计/真实/10mrad与NaN负控过；终态reconcile_control_evidence已执行，保留before_reconciliation和原returncode。②第一次integrate_bounded_top_lead严格pass字段检查被拦，发现6个TERMINAL_HOLD_INPUT报告false但旧脚本exit0。根因它在contact校准后仍用几何中心；备份全部12旧报告/脚本于hold_input_old_reference_diagnostic，加入独立force+URDF校准center再重建参考，阈值不变。12重审全过（六普通side未变），真实positive、+10mm、NaN三fixture过，后两exit1，临时fixture删除。HOLD_INPUT_CORRECTION_CHECK/EXECUTION/AUDIT_CORRECTION及before_hold_input_correction保留全链。旧“60项通过”应解释为旧退出码完成，严格实际字段复核在此次更正后才全过。没有改物理/原质量门或删除失败数据。
- 修正后integrate_bounded_top_lead已成功应用：before_bounded_top_lead备份、BOUNDED_TOP_LEAD_INTEGRATION绑定，helper加入REQUIRED_SOURCES；8pilot协议/拒绝回归及源码编译通过。后继watch_bounded_top_lead_evidence现在逐项检查报告pass+进程returncode，绑定auditor/report/rawSHA，不能exit0掩盖报告false。原6pure/7CLI/两真实轨迹AST/3独立lead审计fixture仍绑定有效。实际enabled物理/lead重建证据待当前batch写盘。
- staged_waist_collector已备份staged_waist_collector_before_bounded_top_lead并按新bounded PROTOCOL重生成，8真实CLI/layout/tamper/raw绑定检查过（完整physics validator仍fixture mock，非真实准入）。不要用旧stage覆盖新控制器。
- **决策边界**BOUNDED_LEAD_EXPERIMENT_DECISION.md：24mm须与normal10/12及直接父6/12都比较，仅超过退化父版不称改善。若仍退化，停止无证据围绕该路线调参，回较好专家补其余开发条件/等待；完整合格交换组按原B→C推进fresh隔离pilot，困难组仍保留目标范围，不无限追求专家100%而迟迟无模型证据。诊断数据绝不直接训练。
- 整体goal active：仍需其余20开发条件与wait、fresh合格pilot、真实转换/训练曝光/train-only统计、共享RGB+11D模型、冻结独立几何多seed原h10与实际图审。没有新训练数据或模型；当前真实新批运行，非阻塞、未完成。

以下为历史记录，以本段为准。

## 2026-09-30 接续：对中方案已完成8条仅4通过，后继限超前方案仍隔离

- 当前contact_center_groups_r1三进程1771898/1771957/1771958已再次核活，62008运行中。8条原task+pose4通过/4失败，非目标maxXY全0；新62005远盒186.492mm失败（父195.341mm通过），62004远袋185.790mm失败（父216.050mm通过），不能将对中候选称为改善。前后组2/4，镜像2/4。没有新训练数据或模型。
- 新远盒center114确实commit，9次tilt恢复、最高3.441°，无release；远袋center118、1次tilt与6次lost恢复，最高1.727°，末top_descend。原质量门未放松。
- 实际均匀画面已看62004/62005四条，当前ACTUAL_REVIEW_BINDINGS共8；远目标在342以后的采样RGB画外，近目标下缘裁切，均保留视觉风险，不以数值成功替代可学习性。
- **更正旧段“袋normal审计过”：**62013袋101帧同一float32法向量范数.9999999736，原acos(dot)出现.000324758rad而独立归一化角0，造成审计假阳性。已保留旧失败报告/旧脚本，修正仅诊断审计，逐项验证原始角公式、独立向量/修正/Jac并拒绝NaN。真实重审324帧/16Jac通过；实际记录/+.01rad角篡改/NaN负控通过。CONTROL_EVIDENCE_CORRECTIONS绑定raw/报告/审计SHA。**当前watcher内存仍保留旧returncode1，须其终态后运行reconcile_control_evidence.py，禁止运行中覆盖或抹去原失败。**
- bounded24候选独立live审计与3例fixture已完成（2真实top轨迹的合成动作+1普通side，10mm篡改/未校准假top拒绝），最大误差1.51e-7m；不是enabled物理结果。integrate_bounded_top_lead.py、run_bounded_top_lead24_groups.py、watch_bounded_top_lead_evidence.py已编译，**未应用/排队**。完整父12/实际12图审/9审计/控制证据修正合并通过后，才整合/8pilot回归并执行唯一新24mm开关的完整同12诊断。
- 继续完整目标：合格多样类别交换示范、fresh pilot、转换/任务阶段曝光与train-only统计、共享策略训练、独立几何多seed原h10/实际视觉评测。当前goal active，真实物理实验运行，有新失败机制证据，非阻塞。

以下为历史记录，以本段为准。

## 2026-09-30 最新接续：对中版镜像2/4；真实中心生效但后续接触迁移，限超前候选隔离

- 当前contact_center_groups_r1仍真实运行，runner1771898/完整审计watcher1771957/逐条control watcher1771958已核活，已进入62005远盒；PROTOCOL所有核心SHA一致。已完整62012/62013四条、原task+pose **2/4**；62012袋161.048mm/盒162.442mm通过，62013袋39.105mm/盒159.403mm失败；非目标全0。不是整批终态，无新训练/后继队列。
- **差结果：**62013盒父normal325.549mm通过→159.403mm失败；center第158帧commit，经独立force+URDF中心重建/生命周期、1129帧projected参考/56Jac全过（最大Jac2.98e-7），normal1046帧/52Jac也过。初始对中后9次tilt恢复294/416/528/638/746/854/962/1070/1180，最高3.528°仍小于原.20rad，没有release/hold。实现符合候选，但物理效果回退。
- **袋失败机制变化：**center106commit，独立center/projected/normal/guard检查过；165..253首次push、254/364两lost。425帧触发**target_table_margin_5mm**：yaw−10.0629°，实际桌边4.983mm（计划仍6.729mm）、物体间轴gap16.746mm。非旧front_corridor_no_table_margin。最高tilt仅.149°；袋主要yaw/滑移而非倾覆。FRONT_GUARD_GEOMETRY、LOADED_CONTACT_OFFSETS、CONTACT_PATCH_REACQUISITION已写。
- **新关联证据 CONTACT_LEAD_DRIFT：**62013盒第一次push269→293命令相对物体Y从−1.71→−49.42mm，实际接触COP从约+2.6→−33.55mm，随后294 tilt抬手；205push帧总max轴lead53.654mm，带载命令-参考Y中位−18.798mm，而盒每帧Y仅−.830mm，命令累加3mm。袋front_x/lateral命令轴lead最大66.178/89.448mm、接触点最大63.344/72.859mm。初次对中后无物体相对lead限制，手参考可持续滑向边缘，尚非确定因果。
- TOP_TIPPING_BALANCE盒nearflat推算CoP外界计数0，不能假装静态支撑计算解释了9次恢复；table/hand实录水平力近互抵但盒仍慢移。袋初步CONTACT_TORQUE_COMPONENTS_PRELIMINARY发现intrinsic接触couple全0，不能把yaw归因于未证实的扭转摩擦；lateral r×F中位tau_z−.011903Nm、front+.003831Nm，记录仅末tick非全子步积分。
- **实际图审：**62013盒154/158/190/260/269/293/294/1199八事件已真正查看，CENTER_EVENT_REVIEW绑定；62012/62013四张各8RGB+4viewer均已真正查看并ACTUAL_REVIEW_BINDINGS共4。失败袋底裁/手遮、盒右裁/部分bag画外；成功62012袋左缘、盒底右裁。最终RESULT仍需按全部raw/imageSHA及帧列表精确合并。当前PARTIAL_RESULT仅62012两条。
- **隔离新候选未应用：**bounded_top_lead_candidate.py、prepare_bounded_top_lead_staging.py、staged_bounded_top_lead/{collect_paired_sorting.py,bounded_top_lead.py}。默认off --expert-top-object-relative-lead-m，要求center已启用且无旧front-relative开关；暂提24mm（诊断范围12..30）desired相对物体中心/原路线目标，每帧slew3mm；原guard和center先执行，仅校准top_push改XY，Z原载荷控制、state.command同步，保护/释放重置记忆。desired有界不等于突动物体时实际slew命令/接触硬有界。
- 旧projected_object_relative_r1的12mm offset-anchor曾困难盒13.360mm停滞，已重新读取RESULT，不能忽略。新center基准/直接目标不同，24mm只基于约19mm带载追踪误差的待测假设。replay_bounded_top_lead.py在两实录做12/24/30固定轨迹shadow，各maxdesired合设定、slew3mm；不预测新力/对象运动。BOUNDED_TOP_LEAD_SHADOW在两个episode。
- 新候选6纯测试、7实际CLI（off/on/缺center/冲突旧front/低高/nan）、实际collector AST两条2398行default精确/340push新XY/其余guard-release-ready不变均过，WIRING_CHECK绑定。**未实际状态动力学重放或solver连续/物理验证；live lead独立审计、integrator和runner尚未写**。README明确剩余工作。首写使用重复相对workdir失败未创建文件；checker漏required out-dir、盒rear段无center日志导致fixture两失败，修正fixture后通过，生产核心未改。
- staged_waist_collector保持上一段按新center PROTOCOL重生的8CLI证据，不可用旧stage覆盖。后续当前12全数值/actual图审/审计→确认新限制方案→全部开发与wait/fresh合格pilot/转换曝光train-only统计/共享训练/独立多seed h10。整体goal active，当前有新真实失败定位和隔离候选进展，非阻塞；没有新训练数据或模型。

以下为较早阶段记录，以本段为准。

## 2026-09-30 最新：normal完整10/12收尾；接触对中候选已应用，新12物理运行中

- normal_contact_groups_r1完整12，原task+pose **10/12**，父terminal_hold_front09也是10/12。depth4/4、diagonal3/4、mirror3/4；新62009袋160.577mm/盒161.979mm均过，全部非目标maxXY0。仅62008盒260.607mm、62013袋40.074mm失败，完整group false精确这两项。六同布局双任务配对、三交换组覆盖过；**不能宣称整体改善或训练准入**。
- 全12各8RGB+4viewer已实际查看，最终RESULT与ACTUAL_REVIEW_BINDINGS全部raw/imageSHA/帧列表一致。9整组审计exit0；12×4逐条control审计完成48/48且真实pass字段核过。手-非目标接触记录0，61采样/条件fullhull间隙正，min37.326mm，非全子步证明。原runner1367389/控制watcher1395180/完整watcher1369908均完成后才改源码；RESULT.md、PARENT_COMPARISON记录好/差和单seed局限。
- 新数据风险量化：成功10条12000帧，start30/active4397/terminal7573=**63.108%稳定尾段**。SETTLED_QUERY_PHASE_AUDIT、TRAINING_EXPOSURE_RISK和ACTIVE_VISIBILITY_EXPOSURE：62005盒top_push126/170全bbox画外，62004袋122/242、62013盒69/297、62009盒sweep27/47。投影不含遮挡，不是新增原硬门，不直接证明模型失败，但不得隐瞒或把整条专家成功当可学证明。
- **已经应用integrate_contact_center.py**，默认off --expert-top-contact-center-calibration：首次top_press三稳定载荷包测量handlocal接触中心，原guard/update优先，commit时以新参考实际XY抬手防横跳，fraction1空中对中后下降推；固定localcenter投影全手最低平面，正常normal保持保留。未校准top_push回到press等有效测量；guard/release不能commit。无助推/零位/原质量门不变。before_contact_center备份和CONTACT_CENTER_INTEGRATION绑定，helper加入正式REQUIRED_SOURCES与collector快照。应用后8pilot协议/拒绝单测与4源编译过。
- **真实新进程**contact_center_groups_r1：runner **1771898**、完整审计watcher **1771957**、逐条审计watcher **1771958**。2026-09-29T23:01 UTC已核活、已进入62013盒step0，所有新PROTOCOL源SHA一致；run_contact_center_groups.py按62013/62012/62005/62004/62008/62009×两任务、1200帧seed0，唯一新增center开关，原normal/front0.9/terminalhold/物理相机原门保持。没有后继队列或训练任务；核心继续冻结至本完整批证据结束。RUNNING_PROCESS记录真PID，不能用旧Isaac号判新进程。
- 新watch_contact_center_evidence.py在每条完整quality写盘后跑normal/hold live/input/contact control；有center日志再跑独立contact-center和projected live。**完整enabled center审计仍待真实轨迹**，现只有三真实首接触片段独立重建误差0、stale/wrongmode负控。audit_contact_center_live.py不导入控制helper，force+URDF重建测量/三包/锁存/模式/抬手XY；projected审计先独立重建center再算reference/Jac，不信任日志center。旧disabled袋1199ref/59Jac默认映射检查过。
- 新62008失败盒也可在102提出稳定center[.237186626,.026970513,-.041296726]；连续离线抬手/对中/下降IK位置/normal筛查过，normal最大1.935°、采样hand-other face≥74.981mm、waist≤.65325。不是接触动力学成功；CONTACT_CENTER_CALIBRATION_SHADOW / MEASURED_CONTACT_RECENTER_SCREEN在该episode。其他三屏与staged WIRING_CHECK均保留。
- staged_waist_collector已按**新contact_center PROTOCOL**重新生成，旧stage备份staged_waist_collector_before_contact_center；8实际CLI/layout/tamper/raw绑定检查过（完整physics validator仍mock，非真实准入）。禁止用旧stage覆盖新核心。
- 下一步：新12真实centercommit/对中轨迹/旋转/恢复和原门、完整actual图审与pair→其余20开发条件及wait→fresh合格pilot、真实转换与train-only统计/任务阶段曝光→共享RGB+11D训练→冻结独立几何多seed h10+实际画面。**整体goal active，未完成，没有新训练数据/模型**。此轮有真实物理批结束、新候选已启动，不是阻塞，不停在脚本或专家结果。

以下为历史记录，较早“未接线/未应用/当前进度/PID”不覆盖本段。

## 2026-09-30 接续：10条原门8通过；对角盒回退，接触对中隔离接线完成

- 用户再次明确持续到整体共享策略目标完成；goal active。normal_contact_groups_r1 runner1367389/完整九审计watcher1369908/逐条控制watcher1395180仍运行，已进入最后62009。最新10/12完成、原门8/10；所有冻结源SHA再次一致，无训练/后继队列。
- **好：**前后组62004/62005完整4/4；62004远袋216.050mm、盒215.762mm。62008袋325.327mm通过。已完成10条非目标maxXY均0。
- **差：**新增62008盒260.607mm失败，未稳定到原目标区，终态top_lift无release/hold；12恢复（2lost+10tilt），最高tilt4.42249°仍小于原.20rad。normal1102frames/55Jac映射通过max9.65e-8，maxnormal9.746°；单纯normal不能称整体改善。62013袋40.074mm失败不变。剩62009未终态，不提前算整组。
- 62004、62008四张均匀8RGB+4viewer已真正查看并SHA绑定；ACTUAL_REVIEW_BINDINGS现在10条。62004远袋513后选帧画外，近盒底右裁切；62008袋685后左裁切，盒反复接触/末期yaw旋转，保留失败与可见风险。不能用采样证明每帧稳定/可见。
- contact_center候选已在staged_contact_center实际接线，**未应用live、未物理执行**。默认off新增CLI，前置三真实载荷包测量→先原guard/update→显式commit→以新参考实际XY抬手→fraction1高位对中→下降。固定手local center投影全手最低平面，正常倾斜保持、释放/guard优先；未校准不允许top_push横推。第一帧/质量门/无助推不变。
- 最新WIRING_CHECK绑定当前三源码SHA：8CLI、4原projection测试、默认4姿态相同、校准Jac有限差分3.99e-10、实际measurement/transition AST、实际front guard优先、无横跳抬升、未校准回press、bounded solver限位均过。三真实例首次测量106/158/114；离线连续IK袋与两盒都通过位置/normal筛查，含新参考重接近，不等于动力学/碰撞成功。
- 新audit_contact_center_live.py独立从force/URDF重建中心、三包/锁存/guard模式/抬手XY/参考绑定；三真实首包片段中心误差0，stale/wrong-mode负控过，CONTACT_CENTER_INDEPENDENT_MEASUREMENT_CHECK。**完整enabled生命周期审计仍待真实运行**。audit_projected_support_live.py有center日志时先调用独立审计取得center，无日志默认不变；旧失败袋1199ref/59Jac核过。原contact_stability审计无需改门。
- integrate_contact_center.py / run_contact_center_groups.py / watch_contact_center_evidence.py已备并编译，无执行无排队。应用前须当前完整12/9审计/实际12图审/完整组/逐条四控制证据及源码检查，之后备份并加入REQUIRED_SOURCES、8pilot回归，才启动新完整12同1200/seed0、只新增center开关。切勿现在修改冻结核心。
- 接下来仍需其余20开发条件与wait、fresh合格pilot、真实转换/阶段曝光/train-only统计、共享训练、独立几何多seed h10。没有新训练数据或模型，不以专家阶段为终点。

以下较早状态保留为历史，以此段为准。

**进程补充：**最新完整落盘已6/12，原门5/6；已转62004，当前Isaac1542769。62005袋也通过，具体进度见COMPLETED_CONDITIONS；本段覆盖下文稍早5/4及62005运行描述。

## 2026-09-30 最新接续：normal前5条4通过；远盒改善、困难袋回退，接触对中候选未接线

- 当前normal_contact_groups_r1仍真实运行，runner1367389/watcher1369908；新增逐条控制证据watcher **1395180**（watch_normal_contact_evidence.py）。三PID已再次核活、全部PROTOCOL源SHA一致；已进入62005，盒已完成、袋还在跑，不能按旧首Isaac1367439判定当前进程。所有控制核心继续冻结，没有新队列或训练任务。
- 已完成5条原task+pose **4/5**：62012袋162.079mm/盒161.537mm，62013盒325.549mm通过、袋40.074mm失败，62005远盒195.341mm通过。非目标全0。4项逐条normal/hold live/input/contact control各5条全exit0；是记录/映射核验，不是完整组或数据准入。
- **好结果：**62005远盒从父176.692mm失败变为195.341mm通过，恢复12→6，最大tilt3.036°，820原margin释放，844起356帧hold，目标0漂移。normal710frames/35Jac映射max1.04e-7核过，maxnormal13.42°含抬升动态误差；projected参考独立核过。8事件RGB实际看并EVENT_REVIEW SHA：110右缘盒，143后选帧盒画外，视觉风险未解决。原contact_stability父父193.899mm也通过，不能把本次当从未成功过或保证重复性。
- **取舍：**62013盒仍通过，但release703→1044，recontacts4→6；normal890frames/45Jac映射过，接触push最大6.186°/全部12.873°，不能称实际姿态严格固定。hold1067起133帧，目标0漂移。相机几何bbox全画外688→306，push90/217→69/297；8事件及均匀RGB/viewer实际看，NORMAL_PARENT_COMPARISON绑定。盒yaw从约−13.6°转到+50.9°，只是倾斜门通过，旋转机制仍存在。
- **差结果/机制：**62013袋从父122.856mm回退40.074mm，179帧front_corridor_no_table_margin；yaw−11.232°，实际前桌边6.805mm、计划4.375mm<原5mm。normal只78frames/3Jac，最大2.405°，控制确实生效但不能解决物体旋转。首次top_push106..178，yaw+6.314→−10.912°；最初front_x实际COP y偏−48mm。CONTACT_YAW_MOMENT按每个原接触求Σ(r×F)，front_x中位tau_z−.139727Nm/Fx−2.8836N，几何零力矩平移(+2.31,+48.14)mm；lateral_y tau_z−.096474Nm，对应(+33.91,+1.18)mm。只是固定力的几何诊断，不含桌摩擦/惯性，不等于移动手后的预测。FRONT_GUARD_GEOMETRY/LOADED_CONTACT_OFFSETS/CONTACT_PATCH_REACQUISITION/PROJECTED_SUPPORT核过，8事件RGB实际看/SHA。
- 镜像四条均匀各8RGB+4viewer实际查看，ACTUAL_REVIEW_BINDINGS现4条，原partial renderer只输出62012最后两条；最终RESULT必须按raw/image SHA与帧列表完全一致才转实际批准。62005远盒只有事件图审，整组剩8的均匀图审待。audit_run_camera_visibility.py新增单episode支持和quality完成过滤，算法未改；首盒episode camera报告已生成，非自动视觉批准。
- **新候选未接线/未应用：**contact_center_calibration_candidate.py测初次轻触连续三包的法向载荷加权接触中心，手local固定切向参考，仍投影到全手实际最低支撑平面。拟先原guard判断→显式commit→用新参考当前XY抬手（防换参考横跳）→高位对中COM→下降推；配套新reference/Jac、顶面中心fraction1，重建front relative/X锚点，保留normal与全部原守卫，不能带载直接平移或双调update增加确认计数。未完成实际collector/state接线与独立中心审计，不能直接采纳。
- helper4纯测试已过，CONTACT_CENTER_CANDIDATE_TESTS记录SHA。replay_contact_center_calibration.py用独立URDF及真实force包，袋106/62013盒158/62005盒114可提出三包稳定中心；各episode CONTACT_CENTER_CALIBRATION_SHADOW，均无动作执行。首次写helper时用了错误相对工作目录，文件没创建且测试import失败，纠正路径后4测试过，无生产更改。
- screen_measured_contact_recenter.py用当前实际bounded solver+独立FK/Jac，袋第一轻触3包局部scatter44.86µm；假设抬至.86m后平移(−18.64,+48.98)mm到COM再下降/front/lateral。222waypoints/888solversteps：参考最大3.943mm、inactive.172mm、normal1.910°、waist.734rad、采样全手对他物face间隙≥81.70mm。瞬时q跟踪，无真实力/碰撞/其他臂/桌验证，888solver步不是物理预算。MEASURED_CONTACT_RECENTER_SCREEN记录，CONTACT_CENTER_CANDIDATE.md详细待办；仍需其他路径筛查/实际接线/新完整物理组。
- 下一步：收齐当前12数值/actual图审/九审计/配对，并准备隔离对中接线；之后全部开发交换组和wait、fresh合格pilot、真实转换/train-only统计与阶段曝光、共享训练、独立几何多seed h10。视觉缺失不是新增无限期硬门，失败原门不可入训练。整体goal active，本turn有新物理证据与候选验证进展，不是阻塞。

以下为历史阶段记录，较早的“当前/最新”或运行PID不覆盖以上状态。


## 2026-09-30 最新：父组完整10/12已收尾，全top倾斜保持新12物理运行中

- terminal_hold_front09_groups_r1完整12、原task+pose10/12（前后3/4、对角4/4、镜像3/4），非目标全0；62005远盒176.692mm、62013袋122.856mm失败。所有12实际均匀8RGB+4viewer已查看，最终RESULT逐一raw/imageSHA/帧列表一致；六配对和三交换组覆盖过。9自动审计全exit0，完整group false只两task/pose失败。手-非目标记录接触0、61采样/条件fullhull间隙全正，非全部子步证明。十成功hold且目标0漂移、两失败无hold，12hold live/input/control检查全过。旧runner969578/watcher969648/手hull1324891均已退出；RESULT.md完整。
- **已经应用**integrate_contact_normal.py：默认关闭--expert-top-contact-normal-hold，手local世界up锁存，秩2倾斜约束、世界yaw自由，top lift/cross/descend/press/push启用、guard/release关闭，普通侧推不启用；不改质量门/物体/外力。备份before_contact_normal，CONTACT_NORMAL_INTEGRATION绑定。helper加入正式REQUIRED_SOURCES和collector快照。应用后8pilot protocol/rejection单测与4文件编译通过。
- **当前真实运行** normal_contact_groups_r1，runner **1367389**、watcher **1369908**、首Isaac **1367439**，已核进程及PROTOCOL所有源SHA。脚本run_normal_contact_groups.py，62013/62012/62005/62004/62008/62009×双任务完整12、1200帧seed0，唯一新增top normal约束，front0.9/terminal hold/原物理相机保留。当前没有终态结果，不可宣称改善。所有核心继续冻结到本完整批证据结束，没有下一队列/训练任务。
- 新audit_contact_normal_live.py独立URDF localup/有限差分normalJac/锁存生命周期校验已备，父disabled记录1199帧负控通过；**enabled真实记录待**。完成首条后须跑此检查、原质量/pose/control/hold、projected mapping、实际事件及均匀图审；最终9审计/完整配对继续。
- staged_waist_collector已经按新normal PROTOCOL重生并8实际CLI/layout/tamper/raw绑定检查通过（完整physics validator仍mock，非真实准入）。旧stage备份staged_waist_collector_before_contact_normal；不得用旧stage覆盖新normal代码。没有fresh pilot/真实转换/新训练。
- 数据质量结论已写父TRAINING_EXPOSURE_RISK与ACTIVE_VISIBILITY_EXPOSURE：十成功12000帧中稳定终态8453（70.44%），有效动作3517，启动30；需明确任务/阶段/几何训练采样，不能裁失败或末尾。出画也发生在实际推送：62009盒48sweep中28全画外，62013盒217top_push中90全画外；投影不含遮挡，不保证有效可见像素。专家成功仍不等于视觉泛化可学。原逐帧可见非硬门，但风险不能省略。
- 目标active：新控制物理复测→其余开发完整交换组和wait→fresh合格pilot→真实转换/对齐/train-only统计与采样→共享RGB+11D训练→独立几何多seed h10与实际图审。此处只是阶段推进，整体尚未完成，不以启动作业为终点。


**最新进度：**已重算10/12，原task+pose8/10；新增62008袋326.050mm、盒321.362mm均过，非目标0，hold分别706/899起且目标0漂移。实际均匀图审共10条，剩62009双任务运行中。三项hold/control独立审计对新两条通过。接触normal物理记录独立FK/有限差分审计脚本已备，当前disabled负控通过，待新控制器真实数据。

## 2026-09-30 本轮完整终态：10/12，待最后两审计；下一物理候选未启动

- terminal_hold_front09_groups_r1已1200帧完整12终态，runner969578完成。原task+pose10/12，depth3/4、diagonal4/4、reverse_diagonal3/4；两失败62005盒/62013袋，非目标全0。六对初始配对通过、三交换组覆盖通过，完整group false仅两task/pose失败。12均匀图审已实际查看并最终RESULT逐一核raw/image SHA/帧列表；十成功hold、两失败无hold，全部12的hold live/input及contact stability独立检查通过。
- watcher969648的前7审计exit0，手hull1324891仍跑，最后phase待；需完成后检查实际数值再integrate_contact_normal，不可现在改冻结核心。没有下轮队列/新训练。RESULT.md已写当前完整数值，审计段仍pending。
- 数据质量新证据：十成功12000帧，start30/active3517/terminal8453，均匀采样70.44%为稳定终态。TRAINING_EXPOSURE_RISK和SETTLED_QUERY_PHASE_AUDIT已完整重算；ACTIVE_VISIBILITY_EXPOSURE按phase/mode合并camera：62009盒48sweep中28全画外，62013盒217top_push中90全画外。不是只在收尾出画；投影不保证可见像素，更不含手遮挡。未新增硬门，但视觉泛化风险必须保留。

## 2026-09-30 当前接续：深度组出现回退；全顶部倾斜保持候选接线与连续IK完成

- `terminal_hold_front09_groups_r1`已实际复核mirror/depth八张8RGB+4viewer，`ACTUAL_REVIEW_BINDINGS.json`共8条绑定raw/image SHA和帧列表；最终RESULT只在hash一致时转录。八条原task+pose **6/8**，镜像3/4、深度3/4；62013袋122.856mm失败、62005远盒176.692mm失败，非目标均0。当前62008已到袋1170/1200 top_release，完整数值以COMPLETED_CONDITIONS最新审计为准，不提前算12终态。runner969578/watcher969648真活，62008 collector1200432；核心继续冻结。
- **好结果：**已完成的六成功条均触发terminal hold且保持目标0漂移，两个失败无hold。独立hold状态/实际输入复算八条全过。62004远袋681起519帧hold，最大q范围.003068rad、腰.00010034rad、双掌<.499mm；62004盒87起1113帧，62005袋79起1121帧保持。初始收敛范围不冒充全程零运动。
- **差结果：**62005远盒从父193.899mm通过回退到176.692mm失败，12次恢复、最高tilt4.324°（仍低于原.20rad），未到目标区。首q/action/xyz相同、quaternion仅极小数值差；action第17帧开始>1e-7差异，不能把新轮当确定性续跑或认定单一原因。front override未启用、hold从未触发；手相对首接触最终旋转57.61°、COP向边缘迁移。FAR_BOX_REPEATABILITY_FINDING/CONTACT_PATCH_REACQUISITION及独立TOP_TIPPING_BALANCE_AUDIT落盘；静态CoP只能解释少数时刻，不能证明12次恢复原因。8事件RGB和viewer155/890已实际看并绑定；目标出画继续报告。
- 候选已改为全top路径默认关闭`--expert-top-contact-normal-hold`，适用于front/initial_top/rear-top，普通侧推不启用；首次top_press锁存手local世界竖直，仅约束倾斜两轴、全局yaw自由，guard/release关闭。旧front-only在staged_contact_normal_front_only备份。4数学、5实际CLI、7真实记录staged solver default完全等价/限位、7模式生命周期/off/no-plan/非front-top接线检查通过；live核心未改。
- 当前候选SHA下含3次假设升降的连续IK：front袋483waypoint/1932步，最大位置1.268mm、normal .955°、inactive49.2µm；far盒475/1900步，位置3.295mm、normal1.525°、inactive.162mm，腰.97827rad接近原.98命令界。即时q跟踪、无碰撞/接触动力学，不能当物理成功。`integrate_contact_normal.py`及`run_normal_contact_groups.py`已备但未应用/未排队；须父12完整终态、9审计、实际图审、完整配对复算后应用，再8pilot回归/编译与新完整12物理验证。
- 用户再次明确持续至整体目标；goal active，无新pilot/真实转换/训练。后续仍须其余开发布局和wait、fresh合格pilot、真实训练统计/阶段曝光、共享训练、独立几何多seed h10及实际画面；不以单项结束，不放宽原门或缩减目标。


**图审补充：**新terminal_hold_front09的mirror四条均匀8RGB+4viewer已实际查看，ACTUAL_REVIEW_BINDINGS四条绑定raw/imageSHA；partial renderer会话6264完成，不再运行。最终watcher生成RESULT后只按一致hash合并，不自动批准后续8条。当前Isaac1085033在62005，runner969578/watcher969648仍真活。

## 2026-09-30 接续：关节保持已有物理好结果；袋仍失败，接触姿态候选隔离中

- 新`terminal_hold_front09_groups_r1`完成mirror四条，原task+pose **3/4**：62012袋162.593mm/盒162.334mm，62013盒325.943mm通过；62013袋122.856mm失败，非目标全0。整批仍跑，runner969578/watcher969648真活、冻结SHA核一致，已转62005，当前不是完整12、模型或数据准入。
- **好结果：**62013盒727..1199连续473帧terminal hold，action完全不变，腰q范围1.25e−5rad、最大上身q范围.002717rad（初始跟踪收敛）、双掌各轴<.245mm、目标0漂移；850..1199所有q/action/palm记录范围0，旧同窗口腰漂.06285rad/最大上身.08482rad。FIRST_TERMINAL_HOLD_COMPARISON绑定两run raw，非确定性因果ablation。盒max tilt3.186°，原门通过；控制/projected1129ref56Jac/X锚点均独立核过。8事件RGB+viewer850实际看/SHA，目标342起出画问题仍保留。
- 新独立`audit_terminal_hold_live.py`检查计数、条件/撤销、q/action绑定与实际保持；`audit_terminal_hold_inputs.py`不导入控制helper，用URDF/fullhull/两物体真实姿态/前动作force独立复算保持输入。四条均通过，误差<3e−7m。62012盒79起1121帧、袋92起1108帧持续hold，无撤销，目标0漂移，双掌各轴<.375mm。失败62013袋无hold，未掩盖guard。全组均匀RGB/viewer仍待；prepare_partial_visual_review前四条正在前台渲染，需poll会话并实际看，不能自动批准。
- **差结果：**62013袋front0.9比旧0.7的31.986mm、center的91.889mm更远，但551帧仍front_corridor_no_table_margin；yaw+11.0585°，实际桌边7.654mm、计划4.726mm，原5mmguard正确。前三段yaw6.326→−9.826、−9.823→.190、.193→9.786°；四次top_push起点106/251/365/532，手相对首接触姿态旋转0/19.13/22.65/29.15°，实际COP/力矩方向改变。CONTACT_PATCH_REACQUISITION、FRONT_GUARD_GEOMETRY、LOADED_CONTACT_OFFSETS、hold/control/projected/recovery均写；8事件RGB实际看并EVENT_REVIEW SHA。是关联机制证据，不证明姿态单因果；固定fraction不保证实际接触点稳定。
- 离线`screen_fixed_contact_pose.py`：四实际接触姿态×七假设front路径点，全姿态固定均无法覆盖后段（最优位置/角度仍大残差），不能当全球不可达证明；仅保持手local world-up（两姿态轴，世界yaw自由）28点位置/normal均可解，真实COP参考/现有virtual+front0.9两版均试。FIXED_CONTACT_POSE_SCREEN、FIXED_CONTACT_NORMAL_SCREEN、FIXED_VIRTUAL_NORMAL_SCREEN在新失败袋目录。无动力学/碰撞路径/物体旋转控制证明，不能直接采纳。
- **隔离候选**`staged_contact_normal`已创建（未应用）：默认关闭--expert-front-contact-normal-hold，只front首次top_press锁存local world-up，top lift/cross/descend/press/push维持normal，guard/release解除；coordinated_step新增秩2倾斜任务，原6行位置Jacobian日志保留，normal另列。4纯数学有限差分/yaw自由/坏输入/纠偏测试通过，manifest绑定当前冻结源码。**实际staged CLI/anchor生命周期/solver接线与default等价/连续有界IK均未检验，物理未运行**，不得凭screen应用；README明确。
- 整体目标仍active；新12完整终态与原门/实际图审→姿态候选验证及全部开发组/等待→fresh合格pilot→真实转换/train-only统计与阶段曝光→共享训练→独立多seed h10。无新训练数据或模型，未缩小目标。

## 2026-09-30 最新：完整12原门11通过；关节保持+front0.9新完整组已启动

- `contact_stability_groups_r1`已完整终态，原task+pose **11/12**：depth_a4/4、diagonal_a4/4、reverse_diagonal_a3/4；唯一62013袋31.986mm失败，非目标12条均0。最后62009袋161.019mm/盒162.395mm通过。六个配对/三完整交换组覆盖通过，COMPLETE_GROUP_READINESS=false精确袋任务失败；不是模型或训练准入。
- 全12条各8RGB+4viewer均已实际查看并在RESULT/ACTUAL_REVIEW_BINDINGS绑定raw与图像SHA；先看前10的partial与最后2，最终renderer生成的同图hash完全一致后合并。缓存RGB一次替代每图重复解压，像素hash不变。九项自动审计已全exit0；所有hand-other记录力事件0，61帧/条件手hull SAT间隙正（非全子步证明）；原物体core路径无重叠/接触记录。RESULT.md已突出好/差及出画风险。旧runner555930/watcher560200/Isaac842100均真退出后才改核心。
- `integrate_terminal_hold.py`检查原12完整证据和stage hash后应用默认关闭终态保持；helper加入正式REQUIRED_SOURCES及collector快照。5纯helper、已有5CLI+3实录AST、应用后8pilot回归/编译通过。仅逻辑接线，物理尚待；原质量门未变。整合记录TERMINAL_HOLD_INTEGRATION，备份before_terminal_hold。front0.9是修正0.7实际接触偏置的未验证假设，不能假定COP线性插值。
- **当前真实任务** `terminal_hold_front09_groups_r1`，runner**969578**、watcher**969648**、首Isaac**969622**已核活。run_terminal_hold_front09_groups.py，62013/62012/62005/62004/62008/62009×双任务12条，1200帧/seed0，唯一控制组合变化front fraction0.7→0.9和显式terminal joint hold；先困难镜像。所有PROTOCOL源再次冻结到整批结束。没有后继队列、无训练GPU进程。
- `audit_terminal_hold_live.py`已准备独立复算原位置确认/other max/q-action绑定/计数与撤销/真实保持命令，报告实际q/palm/target漂移；尚无新轨迹可跑，clearance/load inputs仍是记录值，不能冒充独立几何证明。其他原门/物理/实际图审继续必需。short recontact height审计已按recorded threshold和真实quaternion允许独立tilt重接触；62008盒通过，原lost也保留，不是改门。
- pilot collector隔离版本已基于**新hold live源码**重新生成，旧版本备份staged_waist_collector_before_terminal_hold；8实际CLI/布局/合同copy/tamper/raw绑定重跑通过。staging script现在可指定冻结PROTOCOL，checker核protocol hash；完整物理validator仍在接线测试mock，无真实pilot合同/数据准入。严禁把旧stage覆盖新hold。
- 下一步：检查新12的袋接触/旋转及hold后关节漂移→完整图审/原门/接触→其余开发组与等待→fresh qualified pilot→转换实际相位/数据对齐、train-only统计与明确曝光配置→共享RGB+11D训练→冻结独立几何多seed h10闭环及画面。没有新数据转换/新模型，整体goal active，不以脚本或专家结果结束。

**终态补充：**62008袋也已原task+pose通过，推进325.283mm、非目标0、max tilt0.982°，683原margin释放，三次lost contact214/391/574；独立控制/姿态复算通过。当前已完成**10/12、9通过1失败**，剩62009双任务仍真实运行。该袋均匀/事件实际图审及完整12终态九审计待，不能提前称完整对角组通过或新数据已准入。

## 2026-09-30 接续：终态保持隔离接线完成；对角困难盒原门通过

- 新62008盒原task+pose通过，推进321.337mm，非目标0，max tilt3.183°；1142十帧原位置确认释放（父1200组此条件始终未release）。7次恢复含2lost+5tilt，独立控制/位置确认/姿态复算及projected live核过。8事件RGB实际看/SHA，后段盒仍在下/右边缘重裁切。已落盘9/12、原门8通过1失败，尚未整批终态；62008袋实际日志已到release，需终态复算，不提前计分。
- `staged_terminal_hold/{collect_paired_sorting.py,terminal_joint_hold.py}`已准备默认关闭CLI。**5纯测试+5实际CLI+3真实记录AST重放通过**，62012盒/62005盒/62013失败袋首次hold=79/758/无；输出精确上一帧11D、下肢不变，保护模式能撤销保持。源码/helper SHA与生产冻结hash均核一致，物理尚未应用。日志新增terminal_joint_hold与协调求解器覆盖标识；README/MANIFEST/CLI_AND_REPLAY_CHECK在stage。
- 已修正候选hold优先级：保持期间任一条件失效（新接触、目标不稳、原guard等）立即撤销保持，原控制器接管，不让锁存压过guard。旧`TERMINAL_JOINT_HOLD_SHADOW`记录的是首次触发，修改不影响首次条件，但旧文件candidate SHA属旧版本；以当前stage实际重放为接线证据，后续再重跑全面影子或真实审计。未修改任何原质量门。
- runner555930/watcher560200再次真活，全部PROTOCOL核心仍冻结；磁盘约136GiB。下一批候选需先完成当前12全部证据，再应用hold并把helper加入正式source合同；袋前侧fraction0.9只是下一物理假设，不是已成功方案。pilot隔离接线基于当前live collector，hold应用后须重新生成/测试，不能覆盖掉新控制逻辑。没有新数据转换/训练，整体goal active。

## 2026-09-30 最新接续：8/12完成、7通过；depth完整4/4；发现终态关节漂移

- `contact_stability_groups_r1`完成mirror+depth共8条原门**7/8**，其中depth62004/62005 **4/4**：62004袋215.787mm/盒215.295mm，62005袋196.979mm/盒193.899mm，非目标全部0。mirror3/4，62013袋失败不变。整批12仍运行，runner555930/watcher560200真活、全部核心SHA再次核一致。剩余对角组待，不称整批/模型通过。
- 62004远袋独立倾斜/释放/恢复复算通过：max tilt0.255°，五次lost contact180/304/414/526/644，753原margin释放；projected live审计已跑，8事件RGB实际复核/SHA绑定，后段目标出画风险保留。全部12终态后仍要均匀RGB/viewer实际审查、九审计和完整group复算。
- **重要数据质量发现：**`SETTLED_QUERY_PHASE_AUDIT`无法把release状态直接视为稳定。`POST_RELEASE_JOINT_DRIFT_FINDING`：62012盒200帧后手掌范围<1mm，腰却净漂0.17085rad、右肩yaw−0.31412rad；62005远盒850后腰+0.06661、右肩yaw−0.37552rad，末10帧q步长约.001rad。原任务门通过，但持续Cartesian IK在已撤离时仍改变关节，不宜掩盖为静止示范。新phase标记识别该问题：容易条件terminal仅末53–92帧，远盒没有连续10帧满足声明的关节稳定标签。**标签不是新增原任务门，也没有裁数据或放宽判定**。
- `terminal_joint_hold_candidate.py`未接线：原位置确认、release模式、双手实际hull都高于两物体最高点≥20mm、接触载荷<.2N、工作参考误差≤12mm/另一掌≤15mm、原非目标≤15mm、q跟踪前动作≤.015rad，连续5帧才锁定上一帧完全相同11D命令。4纯测试过；`TERMINAL_JOINT_HOLD_SHADOW`在8条实录上候选时刻62004袋786/盒87、62005袋79/盒758、62012袋92/盒79、62013盒727，失败袋无触发。未执行新命令，不证明动力学保持成功。shadow首写JSON遇np.bool序列化已转原生bool修复，未改条件。
- 实际转换/训练准备：`query_phases.py`+converter可选`--export-query-phases`已接线（不在冻结核心），默认关闭，保留原全部帧/动作；标签绑定raw/expert log SHA。训练新增可选`PI05_PHASE_SAMPLER_POLICY`及`paired_phase_sampler.py`：完整metadata/源码绑定、明确task-phase配额、内部geometry/episode平衡、train-only、与prefix互斥；无开关默认不变，无激活配置。30转换/标签回归+12实际sampler与合成DataLoader检查通过，后者在真实训练Python也重复通过。`QUERY_PHASE_PIPELINE_TESTS.json`记录。尚无新转换数据、真实训练quota或新模型，不能把fixture配置当批准训练。
- 下一步完成当前12及全部证据，候选修正袋接触偏置并物理验证终态关节保持；再其余完整开发组与wait，fresh pilot准入（staged collector已备但未应用）、实际转换对齐与冻结采样/统计、共享训练、独立几何多seed h10。整体goal active，无外部阻塞。

**最新实测好结果：**新62005远盒已1200帧终态，原task+pose通过，推进**193.899mm**（旧baseline146.074mm失败），max tilt**2.995°**、非目标0。InitialTop从开始接近，155/256/351/448/545/641/737七次tilt恢复，744由十帧原位置确认在恢复中转release。独立控制/姿态/位置确认复算通过；1199ref/59Jac mapping通过（max ref3.02e−7m/Jac4.04e−7m/rad）；X锚点独立审核log已跑。8事件RGB+viewer255实际看/SHA绑定，盒155帧已画外，不能隐去视觉风险。当前完成5/12，原门4通过1失败，不是完整depth组或新模型。runner/watcher再次核活，核心SHA一致。

## 2026-09-30 接续：镜像原门3/4；后侧路径可达性不支持直接采用；pilot接线已隔离完成

- `contact_stability_groups_r1`已完成62012/62013四条，原task+pose重算**3/4**，62012袋160.861mm/盒162.334mm通过，62013盒326.518mm通过、袋31.986mm失败；非目标全0。`COMPLETED_CONDITIONS.json`只统计已完整落盘条目，不是完整12条、配对/全部图审或训练准入。runner555930/watcher560200真实存活，已进入62005远盒，整批仍跑，所有PROTOCOL核心保持冻结。
- 后侧顶部路线离线连续IK四变体全未完成：约目标X.59/.63m就失去跟踪，腰到−.98rad界。端点10初值、多种耦合情况进一步筛查，所需X.744556m处最优误差约111mm，终点Y.205约94mm；去掉非工作臂world anchor未明显改善。`REAR_TOP_PATH_KINEMATICS.json`、`REAR_TOP_MULTISTART.json`在新62013袋目录。只是位置IK/假设物体坐标，不是全球不可达证明、真实物理或已执行新路线；不能因桌边余量更大就采纳。
- `staged_waist_collector/collect_paired_sorting.py`已准备准入接线，**未应用**。新增合同开关，完整validator在仿真启动前审核；内联准入helper受collector SHA绑定，准确push/wait注册布局、合同快照/元数据hash、role保留pilot。7 helper单测+8实际CLI检查、实际两种layout AST、snapshot篡改负控与raw绑定通过；全物理validator在接线测试中mock，不能当真实准入证据。README/MANIFEST/CLI_AND_LAYOUT_TESTS记录。无活跃pilot合同、无新转换/训练；生产核心未动。
- 全目标继续active：完整当前物理/图审、袋接触控制及其他组/等待、fresh pilot、train-only数据统计/阶段曝光、共享模型和独立多seed h10均未完成。不要自动采纳退化0.7接触偏置，也不要将3/4或启动作业当完成。

**本轮差结果已落盘定位：**新62013袋31.986mm失败，比旧91.889mm退化；163帧`front_corridor_no_table_margin`（旧418）。yaw初6.30°变−11.275°，旧+11.060°；新实际桌边7.609mm/计划4.295mm，仍正确触发原5mm门。新侧推真实COP X中位−40.07mm，旧+25.27mm，名义接触前移22.5mm没有线性反映在实际接触上。**0.7接触偏置不采纳为修复**。新袋零tilt恢复、从未达到release，所以本条退化不能归因于倾斜门/释放。完整组仍待，不能单条归纳其它几何。FRONT_CONTACT_REGRESSION.json及独立guard/COP/projected/控制审计已写；8事件RGB实际看并绑定SHA。

`YAW_CORRIDOR_RESERVE.json`静态32开发条件复算：62013袋前侧yaw局部允许约±10.92°，初+6.30仅+4.617°余量；任意平面yaw前侧最差桌余−28.869mm，后侧+31.131mm。只是物体包络与12mm间隙/3mm超前的静态分析，不含reach/手臂/动力学，也尚未实现新后侧顶部路径。下一步先完整本批12条，再评估更宽路线及接触控制，勿继续凭IK可达就推断接触有效。原门不降。

截至本条runner555930/watcher560200真实存活，已切62012；全部PROTOCOL SHA再次一致。核心冻结到整批终态。已终态62013盒通过/袋失败，整批仍在运行。

**当前首条新实测好结果：**`contact_stability_groups_r1`62013盒1200帧已落盘，原task+pose复算通过，推进326.518mm、非目标0，max tilt从旧47.99°降至**3.265°**；201/343/464/578四次独立tilt撤力，703原margin释放。独立姿态/恢复/确认重算、1129ref/56Jac、X锚点通过。8事件RGB+viewer200已实看/SHA，后段盒仍画外，不能视觉认证全部接触。此为单条，不是整组/模型通过；当前袋子仍跑，核心继续冻结。

**采样准备：**离线`phase_sampling_candidate.py`6测试通过，用显式task/phase query配额+geometry/episode均衡避免长release挤占起步/等待；不裁原轨迹。只是合成验证，未接生产sampler、未定真实曝光比、没有新数据训练。原prefix权重32限制没有放宽。

## 2026-09-30 最新执行：接触稳定候选完整三组已启动

- 完成旧镜像2/4归档和原源SHA核验后，`integrate_contact_stability.py`已应用：可选front-only inset fraction0.7、独立顶部倾斜0.03rad撤力重接触、十帧原位置确认释放、远距直接路径初始top。全部默认关闭，本轮明确启用；原姿态0.20rad/桌边5mm/他物体15mm/零位/无助推等门不变。组合候选不能拆成单项因果结论。
- 隔离98测试、32开发条件实际factory AST、7CLI接受拒绝检查通过；新helper进collector快照及pilot REQUIRED_SOURCES，pilot8回归过。初始化脚本第一次替换匹配过宽、CLI测试生成第一次替换误中列表，均在应用前修正；没有修改质量门或物理参数。静态检查不代表物理成功。
- 真实runner **555930**，watcher见RUNNING_PROCESS.json，`run_contact_stability_groups.py`→`contact_stability_groups_r1`，按62013/62012/62005/62004/62008/62009完整双任务，共12条，1200帧/seed0，单Isaac。完整mirror/depth/diagonal，所有失败保留；先跑已有两类失败的62013。核心及所有PROTOCOL源冻结到整批终态，不得边跑改接线。没有转换或训练，也不会自动批准视觉。
- 整体目标保持active，后续仍需实际结果/图审、其他开发组与等待、fresh pilot准入、数据曝光与train-only统计、共享模型及独立多种子h10。不得将启动或专家组通过当成完成。

## 2026-09-30 最新：镜像组2/4，已定位两类失败；当前无采集任务

- `projected_hysteresis_mirror1200_r1`完整原task+pose **2/4**，62012双任务通过；62013袋91.889mm未入区，418帧`front_corridor_no_table_margin`；62013盒位置325.976mm通过但倾斜47.99°，超过原0.20rad姿态门。四条非目标最大XY0。对角父组4/4结论保留，不能推广成全多样成功。
- 四条均匀RGB/viewer实际复核，困难袋事件及盒峰值事件RGB/viewer已实看/SHA；九审计exit0，COMPLETE_GROUP_READINESS=false精确两条失败；RESULT.md写明。旧runner339058/watcher339284/queue293712均已退出，无下一候选队列。核心截至本条仍与冻结源一致，可在完整证据归档后实施新候选。
- 袋实际桌边8.057mm，计划4.692mm触发原5mm门；yaw6.30→11.06°，保护前手接触X力臂+28.11mm/τz中位+0.07183Nm。盒普通top未提前按倾斜撤力。没有放宽任何原质量门。候选前侧fraction .7的静态IK可到press，但不是物理改善证明。
- `staged_initial_top_release`隔离候选含可选目标十帧确认释放、几何初始顶部接近；**91单测回归通过**，实际collector factory AST32条件只选62004袋/62005盒/62007盒，4CLI检查通过。未应用核心、无物理实测。后续优先验证接触位置与倾斜撤力，再完整开发组/等待→fresh pilot准入→train-only转换统计及阶段采样→共享训练→冻结独立几何多seed h10。
- 整体goal active，尚未完成，无外部阻塞。没有新合格训练数据或模型；当前磁盘约138GiB可用。下文为历史进程记录，不代表当前存活。

## 2026-09-30 当前：对角完整交换组4/4；同控制镜像组已真实启动

- **完成本轮实质进展：**`projected_clearance_hysteresis_1200_r1`真终态原task+pose **4/4**：62008袋325.472mm/盒323.791mm，62009袋160.165mm/盒161.683mm；四条非目标全过程最大XY0。完整配对、类别交换、11D首state/action0、无助推、原质量及姿态重新审核；COMPLETE_GROUP_READINESS=true/errors空，但training_ready=false。这是开发diagonal_a seed0专家可行性，不是新模型、全多样或最终目标完成。
- 四条各8RGB+4viewer实际查看且RESULT绑定raw/image SHA；62008盒8事件、62009两条各8早期RGB也实际复核/SHA。**九审计全exit0**，旧runner201800/watcher202044及duration队列147812已结束。完整RESULT.md已写。
- 独立控制/几何证据：困难盒1199ref/59Jac、袋1131/56通过；盒17次间距恢复/6次丢接触，min visual-axis gap11.073mm，无紧急stop。盒height/recovery、袋X锚点/slew复算通过。61帧整手SAT gap袋/盒依次24.732/35.301/69.469/76.925mm，无记录手-他物体接触；core最小5.792/22.696/135.685/135.685mm，无XY重叠；无带载非手部记录。仅采样/记录证据，不作全部物理子步连续安全证书。
- **风险仍保留：**困难盒972首次入区、981起位置/稳定条件持续满足，仍190帧top_push，1171再次失接触，末top_descend而未release；追加的1.209mm控制器余量引出多余动作。此轮自身959前缀309.535mm，不能当上一960精确延长。相机center/bbox全画外袋/盒62008为817/77、528/0；62009为1145/0、1166/1151，早期盒45..60就出画，绝非仅最后holding。实际图审不能认证画外接触。
- **当前真实runner339058、watcher339284、queue293712**，`run_hysteresis_mirror1200.py`→`projected_hysteresis_mirror1200_r1`；完整62012/62013×双任务，1200帧，与父组settings/source精确相同，只换登记的开发镜像几何；尚无终态。已核实际PID/source，单Isaac。HYSTERESIS_MIRROR_QUEUE/mirror runner与audit log/RUNNING_PROCESS已更新。**所有PROTOCOL核心冻结到镜像终态，不能现在接线释放或初始top候选。** 无下一候选队列。
- 下一步完整镜像数值/真实图审/九审计→修正已达目标仍推的收尾（离线confirmed_position_release_candidate已6测试/10条影子逐值比对，未接线未实测）及前后远物体initial_top（候选也未接线）→其余开发完整交换组与等待→fresh pilot合同/collector准入（仍未接线）→转换train-only统计/阶段与等待曝光→共享训练→冻结独立几何多seed h10。新converter waist显式分支28+1测试通过是准备工作，没有新数据转换/训练。整个goal active未完成，无外部阻塞。


**释放候选隔离验证已完成（尚未应用）：**`prepare_position_release_staging.py`生成`staged_position_release/{top_contact_bypass.py,collect_paired_sorting.py,confirmed_position_release.py}`；默认关闭，新CLI --expert-top-confirmed-release只允许projected/guarded/continuous diagnostic。原margin释放保留，十帧原位置条件确认仅补充，当前步Top边缘/手guard及Front紧急guard优先，按当前真实XY抬手，release保持。独立进程替换模块跑**71原+9新=80测试过**，6CLI前缀检查过，前后live冻结SHA一致；TESTS/CLI_CHECK/README有证据。CLI首次测试因原nearer-far依赖先拒而断言失败，修正fixture，未改控制。无物理实测、无核心应用、无新增队列。镜像62012盒原numeric已过162.248mm，8事件RGB实际看/SHA绑定；后段目标裁切。完整镜像仍在跑，待实际终态，不提前称4/4。

## 2026-09-30 当前：960完整3/4已收尾；1200困难盒原门首次通过，整组继续

- `projected_clearance_hysteresis_r1` 960帧真终态3/4：62008袋325.850mm过/盒321.245mm失败，62009袋160.092mm/盒161.913mm过，非目标全0。四条各8RGB+4viewer实际查看且SHA绑定，9项审计全exit0，完整group复算唯一困难盒任务失败；RESULT.md已写。旧runner107381/watcher107612已结束（进程复核见后续）。盒953帧首次入区仅7帧而原门10；这批仍失败，不追认。
- 当前真实runner **201800**、watcher **202044**，队列147812等待其结束；`run_hysteresis_1200.py`→`projected_clearance_hysteresis_1200_r1`，完整62008/62009双任务，唯一960→1200帧，核心/相机/物理/seed0/质量门继续冻结。
- **好的结果：1200首条困难盒原任务+pose通过**，推进323.791mm、非目标0；其自身959前缀仅309.535mm，972才首次入区，末228帧均在区内，最后10帧XY变化0。不是前轮轨迹精确续跑。独立恢复/高度/projected参考+Jac核过，17次间距恢复，最小axisgap11.073mm，无紧急stop；6次丢接触。
- **差的结果/训练风险：**困难盒未进入top_release，最终仍top_descend，1171帧再次失接触；虽原门过，动作收尾不理想。8事件RGB实际查看/SHA绑定，后段盒只在右下缘露出，不能用图像认证区内稳定。尚不能称完整4/4、多样可行或模型成功。原质量门不放宽，不新增逐帧完整可见硬门。
- 后续镜像完整组runner已准备`run_hysteresis_mirror1200.py`（62012/62013×两任务），要求当前完整group实际图审及可行性通过才启动；**尚未运行、未排自动队列**。之后仍有前后/其他开发组及等待、fresh pilot、train-only转换统计/采样曝光、共享训练、独立布局多seed h10。
- 转换器新腰显式分支已接线（确认不在live冻结源）：调用waist原门报告而不再误用旧锁腰，合同SHA精确覆盖所有推动/等待轨迹；旧路径、诊断/助推/test/未知/混合协议拒绝保持。12新+16原测试=28通过，另waist episode审计测试通过；REQUIRED_SOURCES补object_relative_push。见CONVERTER_WAIST_ADMISSION_TESTS及log。**collector准入尚未接线/没有激活合同/无新数据转换或训练**。不能把fixture通过当物理准入。


**本轮接续补充：**1200的62008袋也已终态原门通过，推进325.472mm，top_release、非目标0；独立X锚点/投影参考/Jacobian核过（1131参考/56Jac）。困难盒POST_GOAL_CONTROL_FINDING说明第981帧起原目标位置条件持续满足，却仍190帧top_push，1171失接触后末top_descend。新离线候选`confirmed_position_release_candidate.py`及6项边界测试通过；`CONFIRMED_POSITION_RELEASE_SHADOW.json`对10条已落盘轨迹逐帧匹配原位置条件：1200盒首次981、袋579（实际释放679），960失败盒无候选触发。**未接入控制、未做改变动作后的物理验证、不等于完整质量门或安全认证**；未来若接线只作为原release条件的可选补充，紧急guard优先，保持当前XY抬手，不能放宽质量门。当前核心仍冻结，1200剩余62009双任务/完整图审与九审计待；镜像runner已准备但未启动。


**接续排队更新：**`queue_hysteresis_mirror.py`已真实启动PID293712，状态HYSTERESIS_MIRROR_QUEUE.json，日志hysteresis_mirror_queue.log。它等待1200真终态/原task+pose4/4/9审计exit0/实际图审完整group通过/source核验后，串行启动mirror62012/62013完整4条。不会自动批准画面或数据。**核心冻结跨镜像队列**；若父组失败队列报错，不能盲重启。当前1200已到最后62009袋，尚未终态。

## 2026-09-30 当前：短恢复完整3/4已收尾；0.5mm间距滞回版正在实测

- `projected_short_recontact_r1`真终态3/4：62008袋325.070mm通过、盒254.787mm未入区；62009袋161.020/盒161.103mm通过，非目标全0。四条各8RGB+4viewer及盒8事件RGB实际看过/SHA绑定，9审计全exit0，完整group在改核心前重算仅盒任务失败。RESULT.md已写；旧runner4181161/watcher4181396已退出。两困难任务独立projected/恢复锚点通过；盒独立height审计通过。恢复更快不等于任务成功。
- 已执行`integrate_front_clearance_hysteresis.py`：FrontClearanceProgress新增默认0的recovery_hysteresis_m，范围0..1mm且恢复阈值>=11mm；本轮显式0.5mm：初始/恢复侧推仍12mm+3确认（12.5mm立即路径保留），再次纠正在gap<11.5mm，10mm紧急/5mm桌手/其余原门不变。前版front_x268帧、46次恢复；固定记录shadow0.5mm仅56帧/1次，不作物理成功保证。独立audit_recovery_and_anchor按metadata滞回复算，旧缺字段默认0保持。
- **71单测/回归全过**（64原+7新），包括0.5mm实际FrontTopRoute集成、11.5mm触发当前Y锁定、10mm紧急原门；实际CLI前缀6参数接受/拒绝检查通过。证据FRONT_CLEARANCE_HYSTERESIS_INTEGRATION/TESTS/CLI_CHECK与log。
- **真实当前runner107381、watcher107612**，`run_front_clearance_hysteresis.py`→`projected_clearance_hysteresis_r1`，960帧完整62008/62009双任务，单Isaac。保留0.86m短恢复及全部原物理/相机/5N/3mm/seed0；所有PROTOCOL核心再次冻结，新的数值/实际图审待，不称已改善。PID发生系统计数回绕，按实际/proc核验，不依旧数字大小判断。无下一接续队列。
- 转换准备实际修复：新wait布局含geometry_group会被四条推动交换组validator误拒，WAIST_WAIT_SPLIT_INTEGRATION_FINDING.json纯元数据fixture复现。converter新增record_geometry_metadata，等待保留wait_geometry_group/wait_assignment，推动维持原字段；6新测试+3原heldout负控共9通过。未改运行中的diverse_layouts/collector，旧准入/失败/heldout检查保持。**新腰合同分支和collector准入仍未接线/启用，无任何新数据转换或训练**。更新PILOT_INTEGRATION_PENDING和CONVERTER_WAIT_GEOMETRY_TESTS。
- 接续核新batch实际PID/source及困难盒间距切换/真实推进/非目标/触发guard，完成完整组与图审。仍需其他开发完整组（镜像/前后，远处初始top尚未接线）、等待→fresh合格pilot、转换train-only统计与采样曝光→共享训练→独立布局多seed h10。整体goal active未完成，无外部阻塞。

**0.5mm滞回首条960终态：**62008盒推进321.245mm，末Y−.2012455，953帧首次越过原.20入区线，末尾仅7帧在区内（原门10帧），故仍失败；最后10帧XY变化1.922mm，未达controller释放目标−.205，末top_push/lateral_y。非目标0，18次间距恢复、5次丢接触；真实间距恢复并未像固定geometry shadow那样只1次。独立hysteresis/height/projected+Jac复算通过，实测最小axis gap10.433mm，未触发10mm紧急门但接近边界，保留风险。8事件RGB已实际查看/SHA绑定，后段重裁切。TERMINAL_ZONE_TIMING.json有精确末10帧。

**接续队列PID147812** `queue_hysteresis_1200.py`，状态HYSTERESIS_DURATION_QUEUE.json/log hysteresis_duration_queue.log。等待当前runner107381真实退出、完整4条件恰3/4仅盒失败且source匹配，再启动`run_hysteresis_1200.py`→`projected_clearance_hysteresis_1200_r1`，唯一变更960→1200（增加240帧），完整62008/62009双任务，其余冻结。新runner/watcher自动写RUNNING_PROCESS。若其他条件失败则队列报错，需检查，不能盲启动。**核心冻结跨接续实验，不要在当前960终态后修改控制**。新旧预算分开报告，同seed不是精确前缀，不宣称960成功。旧960完整图审/九审计仍须收尾，无数据准入或新模型。

## 2026-09-30 当前：相对超前量版退化已完整复核；0.86m短恢复版正在实测

- `projected_object_relative_r1`完整真终态3/4：62008袋325.637mm、盒仅13.360mm失败；62009袋160.632/盒160.545mm通过。四条非目标全0。四条各8RGB+4viewer与盒8事件RGB实际查看并绑定SHA，9项审计全exit0，完整group在改核心前复算仅盒任务失败。RESULT.md写明**257.202→13.360mm明显退化，不采用该开关**。原runner4052617/watcher4052859已退出。两困难任务projected live/恢复锚点独立检查通过，盒新object-relative重算误差0；实现正确不代表物理方案有效。
- 终态/source/完整图审核完后，已执行`integrate_front_short_recontact.py`：TopContact新增可选recontact_travel_z，默认.91；仅front CLI `--expert-front-recontact-z .86`在丢接触后降低恢复，初次接近.91，紧急guard/release仍.91。恢复过渡首帧原本先计算travel_z再增加recontacts，新增测试揭示仍发.91，已修复为立刻用显式高度；初次失败log保留，之后**64单测/回归全过**，实际CLI前缀5参数接受/拒绝检查通过（无启动sim）。FRONT_SHORT_RECONTACT_INTEGRATION/TESTS/CLI_CHECK有证据。原默认与legacy高度模式保持。
- **真实当前runner4181161、watcher4181396**，`run_front_short_recontact.py`→`projected_short_recontact_r1`，960帧完整62008/62009双任务，单Isaac。关闭退化object-relative开关，相对原confirmed960版仅短恢复高度改变，5N/3mm/seed0/相机/物理/原门不变。已核实际PID与PROTOCOL sourcehash；全部核心再次冻结。最新盒420帧top_push、Y约−.01004（约130mm推进），尚无终态，不宣称成功。无下一接续队列。
- `audit_short_recontact_height.py`已准备，独立核初次/每次恢复/紧急/释放高度，无控制helper；等首raw落盘运行，配合原recovery/projected/force/全组审核。旧relative整手49采样gap24.797/73.711/69.469/76.925mm，无记录物体间力和非手臂载荷；困难袋bbox全画外72帧，62009盒911帧，风险保留且非全子步安全证明。
- 七个真实失接触状态短高度shadow仍只运动学证据（.91需84–90步、.86需49–57、.84需35–43，采样手-他物体gap>40mm），详见SHORT_RECONTACT_CANDIDATE.md。选择较保守.86做真实完整组，不把shadow当物理成功。
- 后续仍需：该组完整原门及实际图审→镜像/前后等其他开发完整组和等待（远处初始top候选仍未接线）→fresh合格pilot/转换train-only统计与阶段采样→共享模型训练→独立布局、多seed、h10及图审。没有新数据入库或新模型，整体goal active未完成，无外部阻塞。

**短恢复首条终态更新：**62008盒仍失败，254.787mm，非目标0；四次重接触207/337/481/831，独立SHORT_RECONTACT_HEIGHT_AUDIT核实立即.86且初次.91。projected/recovery独立审计过，8事件RGB实际看并绑定SHA。对比原confirmed960非推动阶段495→354、前移纠正158→268、侧推306→337，间距恢复30→46；不是确定性前缀因果。省出的时间主要花在反复纠正间距，不能称提升。

下一未接线候选：`/tmp/front_clearance_hysteresis_candidate.py`与5单测过，默认0不变；可选0.5mm滞回让gap<11.5mm时再纠正（初始/恢复仍12mm+3帧，10mm紧急保持）。`shadow_clearance_hysteresis.py`固定短版记录重放纠正46→1、带载纠正268→56；1mm仅再少8帧，故优先保留更大缓冲的0.5mm。旧长版46→0。只重放，非实际安全/进度证明；无新接续队列。详见RECOVERY_HYSTERESIS_FINDING.md。当前完整短版仍运行，核心冻结，先收尾再接线。

## 2026-09-30 当前：延时完整组仍3/4；物体相对超前量候选已运行

- `projected_confirmed_clearance_r1`960终态3/4，四条各8RGB+4viewer实际图审完成，九审计exit0、完整group唯一62008盒失败；RESULT.md已补。旧runner3779673/queue3833580均退出。
- `projected_confirmed_clearance_long_r1`1440也真终态3/4：62008袋325.144mm通过、盒299.358mm失败（距原入区20.642mm），62009袋160.412/盒160.414mm通过，非目标全0。四条8RGB+4viewer及困难盒8事件RGB均实际查看/SHA绑定；9审计全0；完整group在改源码前完成，唯一盒任务失败。两困难任务独立projected live/恢复锚点审计通过。详见本批RESULT.md；旧runner3873613/watcher3873842均退出。
- 新`FRONT_CONTACT_DRIFT_DIAGNOSIS.json`：盒1440中侧推435帧贡献297.131mm、恢复间距245帧贡献2.696mm；抬手/对齐/下降/压紧759帧；7次丢接触时虚拟reference相对物体Y偏差82–114mm。代码每帧用当前tip+12mm继续走，存在累积相对滑移。手/物体记录摩擦1.0、桌/物体.55，未改材料。实际事件图前段可见滑离，后段裁切，非全画面接触证书。
- 待旧全组终态/hash/9审计/完整group后，已应用`integrate_object_relative_front.py`：显式`--expert-front-object-relative-lead`，每次建立接触锁reference-object XY偏移；desired=实测object+锁定offset+最多12mm lead，仍3mm slew；丢接触后重置，原默认/紧急门不变。新helper进入collector源码快照及run PROTOCOL。**58相关测试通过**（55项+route_parameters3项）；测试只验证控制契约，不证明物理成功。新只读`audit_object_relative_front.py`准备，等raw后独立复算。
- **真实当前runner4052617、watcher4052859**，`run_object_relative_front.py`→`projected_object_relative_r1`，已核实际PID和source。960帧62008/62009双任务完整4条，单Isaac，所有PROTOCOL核心再次冻结。最新困难盒600帧top_push，X约.39625（仅前移3.7mm）、Y约.11996，明显推进不足；新候选有停滞风险，**尚无终态、不能称改善**。要等真实force/raw看有限lead与接触/关节跟踪，不能立刻继续盲加阈值。无下一接续作业排队。
- 另一个未接线候选`initial_top_route_candidate.py`及5tests通过，audit_initial_top_route_proposals已评全部32开发条件，选择62004袋/62005盒/62007盒（far>=.48、transfer>.18、direct envelope合法），不读类别/ID决策、不碰heldout。只是几何/零位局部IK启发，尚未接线或实测；后续仍完整depth交换组，不先侧扫再从失败姿态恢复。
- 接续：当前完整组终态/源核/独立control+force+实际图审；继续解决接触和多样开发组（含镜像、前后）/等待；fresh pilot准入、正式转换train-only统计与阶段/等待曝光、共享训练、独立几何多seed h10仍未完成。没有新训练数据或模型，goal active。磁盘约142GiB可用。

**本轮接续更正：**物体相对版62008盒已终态失败，仅13.360mm（同960旧版257.202mm）；857帧top_push全front_x、无重接触。独立新anchor/desired/slew审核误差0，旧恢复/投影/Jacobian亦过；新LOADED_CONTACT_OFFSETS对齐post-action/下一pre-action坐标误差0，法向载荷median4.998N而X推力median+0.0043N。8事件RGB实际查看并绑定SHA：持续压在盒上，非有效前移。不是改善。该组现已到62009，剩余完整结果/九审计/四条图审待。

新只读`audit_front_short_recovery_kinematics.py`以旧长批7个真实丢接触姿态，隔离shadow比较travel Z0.91/0.86/0.84：7/7局部IK均到press；步数分别84–90/49–57/35–43，整手-非目标面轴min41.206/40.388/40.579mm、手worldZmin.7898。固定物体/瞬时q/无力无动力学/非全臂连续扫掠，不能作成功证据。下轮候选恢复原continuous front push关闭object-relative，仅发生丢接触后高度.86，初次.91不变；**尚未接线或排队**，先等当前完整冻结批收尾。详见SHORT_RECONTACT_CANDIDATE.md。

## 2026-09-30 当前：三帧恢复版实测推进257mm但未入区，延时对照已排队

- 本轮有实际进展：原长批projected_recovery_xhold_long_r1真终态仍3/4；四条各8RGB+4viewer、62008两条各8事件RGB实际已看，RESULT/EVENT_REVIEW raw/imageSHA绑定；九项自动审计全0。完整group审计在核心修改前运行，实际图审绑定通过，仅62008盒任务失败。73帧整手SAT最小gap24.833/55.990/69.469/76.925mm；物体间记录力0、core投影不重叠；非手臂无载荷记录。详见长批RESULT.md，非全部子步保证。
- 队列3701405按核source/终态/9审计后应用3连续名义间距修正，**48测试全过**。当前`projected_confirmed_clearance_r1` runner **3779673**、watcher **3779839**，已核实际PID与源码hash；960帧完整62008/62009双任务，所有核心再次冻结。62008已两条终态：袋task+pose过；盒推进**257.202mm**（前960版218.532mm），仍未到区。30次恢复（其中30个3帧确认事件）、4次lost_contact；末lateral_y/top_push、无guard、非目标0。独立恢复逻辑/几何重算过，最小axis gap11.747mm；projected live959参考/47Jac过，max物理点2.69e-7m/Jac3.20e-7m每rad。尚在62009，本批未终态、全组实际图审待。
- **接续队列PID3833580** `queue_confirmed_duration_diagnostic.py` 已验活，CONFIRMED_DURATION_QUEUE.json/log confirmed_duration_queue.log。等当前runner3779673退出且完整恰3/4仅盒失败、source匹配，再启动`run_projected_confirmed_clearance_long.py`→`projected_confirmed_clearance_long_r1`；只960→1440，控制不改，仍完整4条。新PID/watcher自动更新RUNNING_PROCESS。若其他任务也失败则队列报错需处理，不能盲启动。源保持冻结跨接续实验；不以预算改变冒称960成功，同seed非精确确定性复现。
- 数据准备新校准：SAMPLING_BASELINE_TARGETS.json直接绑定实际两版保存sampler audit。22/39对应160帧，prefix3条件概率23.4146%、等待query占比15.4185%；7/39对应320帧，13.1507%/8.3532%。原960数学weight48.30只匹配后一版，不能误称对齐22/39；匹配前者需97.5287，均超现API<=32（960cap32首3最多9.1168%，weight16仅4.7761%）。未改训练配置/API或开始训练。更新WAIST_ENABLED_PLAN与PILOT_INTEGRATION_PENDING要求基于新合格train冻结可执行任务/阶段/等待曝光，不擅裁原始记录。
- 提前研究未解决depth_a62005远盒hold：普通侧扫110帧到hold后未完成，frontal_plan.required=false故没有top恢复。新只读audit_direct_hold_recovery_kinematics记录真实失败120帧初态下四个顶部接近候选400步均不收敛（腰.98），扩大10→12mm容差仍失败；从真实0帧零位/初始物体姿态则四者101–113步到press。前缘20mm方案腰.5334、真实最低0.2mm顶点core边距19.073mm；中心腰.9194。优先研究从初始就top接触而非侧扫后补救，但**只是固定物体/瞬时关节的局部IK，无动力学/力/碰撞/成功证明；未实现**。详见DIRECT_HOLD_RECOVERY_FINDING.md及baseline62005/…frame0、frame120 JSON。不可改当前冻结核心或写死类别/layoutID，后续仍完整depth交换组。
- 接续先核当前batch+duration队列、收尾完整结果和实际画面/力/非目标；长对照若完成盒剩余67.8mm，继续镜像/前后/其他开发完整组与等待。fresh pilot准入/生产转换新协议/训练专用统计/阶段采样/共享训练/独立多种子h10全部未完成，没有新数据入库或模型，goal active。

## 2026-09-30 当前：连续三帧名义间距候选已排队，长批最后任务仍运行

- 本轮有实质进展：长批62008袋原task+pose通过，first-to-last顶推X+0.974mm，3次重接触；盒1440失败机制与上一节一致。新PREFIX_REPRODUCIBILITY_AUDIT核两次配置只steps/out_dir不同、源码相同；初始q/action/物体完全一致，104帧接触后浮点小差出现，约114帧超1e-6，208帧模式分歧；前960物体XY最大差29.897mm。因此不称同seed精确续跑或严格单因素轨迹因果，仍需后续多次/多seed验证。
- 离线候选 `/tmp/front_clearance_confirmed_candidate.py`：保持默认12.5mm立即恢复；仅显式confirm_nominal_clearance允许连续3次实测gap>=名义12mm后恢复。任何低于12mm会清零计数，不以超时放行；前侧重新纠正继续锁当次Y，10mm紧急门/5mm桌手门不改。5项离线测试过，旧默认100次12.49mm仍保持front_x；unsafe插入清计数/低间距2000次不放行/重新恢复都覆盖。固定长批poses shadow尾480中477帧可侧推，仅影子不是物理成功。尚未应用核心（排队脚本稍后自动应用）。
- **新排队任务PID3701405** `queue_confirmed_clearance.py`，状态CONFIRMED_CLEARANCE_QUEUE.json，log confirmed_clearance_queue.log，已验活。等长批runner3618118真正退出、4条件恰为仅62008盒失败、source hash/终态timestamp一致、watcher3618346九审计全exit0，先运行旧完整group审计保留数值/源码证据，然后调用`/tmp/integrate_confirmed_clearance.py`，运行七模块预期48项相关测试，全过才启动`run_projected_confirmed_clearance.py`→`projected_confirmed_clearance_r1`。新实验回960帧完整62008/62009双任务，只有nominal confirmation开关相对原960版本变化。新PID及watcher会自动写RUNNING_PROCESS.json；测试日志confirmed_clearance_tests.log；失败则queue_failed，不能盲重启。**期间禁止手改任何冻结核心，队列会自行更新并再次冻结**。无需再次授权，不自动视觉批准/训练入库。
- 长批62008两条独立projected live与recovery/anchor过：盒1439ref/71Jac max2.80e-7m/3.21e-7m每rad；袋1371/68 max3.11e-7m/2.68e-7m每rad。盒900..1439八事件RGB已实际看，后段盒裁切手向下缘移，EVENT_REVIEW绑定SHA。长批全四条uniform actual review尚未做（等watcher图片）；自动队列允许先开新诊断，不冒称旧批视觉通过。新候选独立恢复auditor已支持plan.nominal_clearance_confirmation_frames，未调用控制helper。
- 另完善未激活的waist_pilot_protocol准入：REQUIRED_SOURCES加front_top/front_clearance/tabletop_candidates/projected_reference/hand_support_vertices；wait字典必须完整并通过validate_diagnostic_layout，不许只ID缺seed/坐标。8单测过（原6+2负控），未改当前冻结物理源码或开放准入；历史准备audit仅历史证据，新正式合同须本版完整多样成功+wait审核。WAIST_PILOT_INTEGRATION_PENDING已更新。
- 接续先核两个队列/实际PID，收尾长批3/4（以实际终态为准）完整数值、画面、force/非目标；观察候选应用测试/新完整组。若新4/4，再继续完整镜像reverse_diagonal、depth远盒/其他开发组/等待，然后fresh合格pilot/正式转换train-only统计及阶段曝光/共享训练/冻结独立几何多种子h10。没有新数据准入或模型，整体goal active未完成。

## 2026-09-30 当前：完整对角交换3/4；仅延时的完整组已接续

- `projected_recovery_xhold_r1`真终态，原task+pose **3/4**（前版2/4），只有62008盒未入区。困难袋325.434mm、首次至末次顶推X−0.370mm、腰max.727731；盒218.532mm，18次front恢复、4次丢接触，visual-AABB最小轴分离11.621mm，无紧急stop。其余62009袋/盒160.092/161.356mm。四条非目标XY0、上半身首state/action0、助推0；完整pair/交换复算通过但COMPLETE_GROUP_READINESS=false，唯一错误困难盒任务未完成。未挑成功子集训练。
- 四条各8RGB+4viewer及62008两条各8事件RGB已实际查看，RESULT.json和EVENT_REVIEW带raw/imageSHA（`review_sheet_sha256`字段已统一）。困难袋前段接触可见改善，但center画外806→576、bbox全画外0→71帧，不能只报好指标。盒后段裁切/遮挡；62009视觉问题保留。不是新增逐帧全可见门。RESULT.md有详细好/差与下一步。
- 新独立audit_recovery_and_anchor不导入控制helper，实测18次恢复与当前Y、gap复算一致；袋锚点跨3次重接触不变/X2mm slew一致。初版auditor误用Y3mm导致假失败，INITIAL_ERROR保留后修正，未改控制或轨迹。两条projected live参考/物理vertex/Jacobian独立核过，误差<=2.875e-7m/2.723e-7m每rad。九项自动审计已全exit0；旧watcher3553264收尾完成。fullhand49帧SAT最小gap困难袋24.573mm/盒57.432mm，其余>69mm，非全子步认证。parcel core最小SAT分离袋5.570mm、盒32.032mm，无XY重叠、记录物体间力0；非手臂无载荷记录（非全子步证明）。
- **当前真任务**`projected_recovery_xhold_long_r1` runner **3618118**，watcher **3618346**，queue **3607546**，已核实际PID/sourcehash，单Isaac。queue等前runner3523627退出并确认完整3/4后启动。唯一变更steps960→1440，完整62008/62009双任务4条；所有核心保持冻结，原控制/物理/质量门不变。延时结果单列，不能声称960通过。新第一条1320帧仍top_push，盒Y约−.09918（约1080帧后接近不变），几乎停滞；仅延时不是充分解释，需EP写盘核恢复阶段/间距/接触力。暂无终态新成功。脚本run_projected_recovery_xhold_long.py；queue状态RECOVERY_DURATION_QUEUE.json。
- 接续：新批完整终态/hash→实际画面+原任务/姿态/接触/非目标/独立projected和恢复锚点审计；若通过再镜像reverse_diagonal/depth远盒和其他开发完整组/等待。fresh合格pilot、生产转换新协议接线、train-only统计/阶段采样、共享训练和独立几何多种子h10全部仍待，无新模型。goal active未完成，无外部阻塞。

- 延时第一条盒已1440终态仍失败，最终进度219.222mm、非目标0。该次959帧进度196.776mm，额外480帧仅22.446mm；与前960运行同配置seed但前缀最大XY差29.897mm，不能冒称精确确定性续跑或用两run直接隔离时间因果。collector检查steps只决定循环/环境episode_length（waist_probe关闭），未见阶段按总时长缩放；重复性仍需多次实测。`EXTENDED_STALL_DIAGNOSIS.json`：最后120帧均top_push/front_x，有3.527–3.616N载荷但物体XY仅0.045mm；gap12.459–12.490mm高于12mm规划要求，却一直差12.5mm恢复门，末差9.890微米，手命令X继续走到.2915/物体X.3718。提示恢复阶段额外裕量造成数值/摩擦稳态卡住，接触力存在不等于有效平移。可离线研究已满足安全间距时的有界防卡恢复或无额外裕量；**尚未实现/未物理验证，核心在长批运行中仍冻结**。当前长批正在62008袋，仍须完整四条及审计，不提前称整批通过。

## 2026-09-30 当前：间距恢复+固定接触X+远处近缘接触完整组实测

- 上版projected_clearance12_alignment10_r1终态2/4，九项审计全exit0；四条各8 RGB+4 viewer及62008各8事件RGB已实际查看并绑定raw/image SHA。盒推进171.15mm但632帧parcel_clearance_10mm停止；袋推进78.88mm、首次顶推X后移41.95mm然后重接触卡住。袋实际接触阶段出画，盒裁切；两类独立projected live映射/Jacobian通过，不证明物理成功。详见该批RESULT.md。
- 修正有证据的控制问题：原front恢复门clearance-3mm=9mm晚于10mm紧急门；新可选helper低于12mm提前恢复、到12.5mm恢复侧推，恢复保持当前Y。非front可选锁首次surface commandX且跨重接触保留；初始targetX>=.48的远物体可选20mm近缘接触，近物体仍center。旧默认/10mm紧急/5mm桌边和手gap/5N/3mm/960/seed0/原门不变，38项相关测试通过。组合候选，静态/影子分析不作物理成功。所有改动都在前批终态source核验之后。
- 当前projected_recovery_xhold_r1，实际runner3523627，审计收尾3553264，两者已验活、source hash匹配，单Isaac且所有核心冻结。62008盒已960帧：推进218.53mm，非目标0，但未入目标区仍失败，结束top_push；正跑62008袋，随后62009双任务。收尾不自动批准画面，projected live独立核验需手工跑。
- 后续完整组及镜像/深度/其他开发交换组、等待→fresh pilot明确准入→转换train-only统计及阶段采样→共享训练→独立布局/多种子h10仍全部保留。没有新数据入库或模型，整体goal active未完成，无外部阻塞。

## 2026-09-30 当前：实测支撑映射核过；12mm前侧间距+10mm接近容差完整组运行

- 上轮实际进展：新`audit_projected_support_live.py EP`独立URDF+全hull支撑平面与有限差分，不调用控制reference函数，对projected_support_group_r1的62008盒959参考帧/47Jacobian点、袋891/44点核验。virtual位置、offset FK、真实最低vertex成员/世界坐标/最低平面高度误差均<=3.54e-7m；Jacobian max盒2.58e-7/袋3.21e-7m/rad，nonsmooth样本0，mapping_passed=true。全过程负face margin含未接触抬手/接近，不能冒称穿透；另按loaded phase解读。
- `projected_support_group_r1`终态runner3320571退出，source证实timestamp16:16:49 UTC后才改核心，仍2/4(62009双任务过)。62008盒侧向进度0.526mm、袋7.863mm、非目标均0；真实看四条各8RGB+4viewer并写RESULT raw/imageSHA，盒另8事件RGB90/99/103/110/120/125/130/160已实际看并EVENT_REVIEW绑定。袋center参考明显出画加重：137裁切，274后只边角，不能只报参考改善。
- 盒保护具体`front_corridor_no_table_margin`，125帧。FRONT_GUARD_GEOMETRY独立复算：yaw7.448→16.434°，当前真实桌边余量23.06mm；20mm物体规划余量对应**未来**前侧goal .364571，仅剩4.647mm桌边余量，触发5mm提前guard。静态12mm余量候选goal .372571，桌边12.647mm，未证明动态成功。28个top_push末tick接触的载荷加权Y力臂41.35mm，有旋转力矩来源；非全子步冲量。
- 袋最后120帧真实参考XY误差X=8.727–8.734mm/Y~3.92mm，Z gap~4.35mm；真实近支撑0.2mm顶点群离collision core边界至少46.0067mm，载荷0。DESCENT_RESIDUAL_GATE_AUDIT：原XY8mm+Z8mm条件0/120，候选XY10mm条件120/120。只记录条件检查，不能当物理成功，也未证明稳态位置偏差的根因。
- 在上一批真终态核source之后，新增显式`--expert-front-clearance-m`(默认.02，12..30mm，非默认必须front diagnostic)与`--expert-top-alignment-tolerance-m`(默认.008，3..12mm，非默认必须projected diagnostic)。TopContact默认保持8mm，FrontTopRoute默认20mm；新实验12/10，固定10mm紧急对象间隙/5mm桌边/5mm手他物体guard、实测force确认、原任务/pose/15mm非目标/零位/无助推/动作门不变。3新单测包括8.7mm残差default仍卡/10mm可press但无载荷不push、静态转角guard差异及手guard仍工作；原7front+21top全过，核心编译过。不是放宽训练质量验收门。
- **当前真任务** `projected_clearance12_alignment10_r1` runner **3419538**，收尾 **3432092** 已验活与source hash，脚本run_projected_clearance12_alignment10.py，完整62008/62009×双任务4条，960/environment seed0/5N/3mm/center投影参考不变，组合参数候选非单变量。全核心冻结至终态。最新62008盒step870又进入front_guard_lift，X .379270/Y -.051152，侧向进度约171.15mm，但未到-.20目标区；非目标在日志采样仍原位。之前已跨过旧125帧保护并进入侧推、数次重接触；这次guard具体原因待EP写盘，不预判。**尚未入区/未完成**。仅一个Isaac。
- `audit_run_support_mapping.py`纯审计更新了projected_reference_frames/reference_kind/max_control_reference_change字段，旧vertex-change字段保留兼容但明确是reference别名，不把virtual当mesh点。独立live auditor尚未纳入自动watcher，需要新批完成后手工跑有projected记录的EP；ordinary无需该检查。之前watcher3325906已退出，九项AUDIT_EXECUTION全部exit0已核，不据旧RUNNING字段假报活。新watcher3432092不是自动视觉批准。
- 接续核live与冻结；完整4条终态后原质量+pose/force/非目标轨迹/实际RGB及viewer/独立projectedJacobian。若组过继续镜像完整reverse_diagonal与depth远盒恢复/其他development组及wait，不因单盒进步就扩采。袋camera风险需要按实际任务运动阶段报告，不能用固定center方案的成功数掩盖视觉退步；可根据证据再考虑近/远接触位置，但尚未新改。随后fresh pilot合同/转换train-only统计和阶段采样/共享训练/冻结独立多种子h10仍完整保留。无新训练数据或模型，goal active、未达标，无外部阻塞。

## 2026-09-30 当前：连续支撑参考已开始实测；前侧原版2/4

- 上轮是实际进展：多样基线12条九项自动审计全exit0，旧watcher2945123退出。12条又实际查看各8早期RGB(0/15/30/45/60/75/90/120)，EARLY_RGB_REVIEW.json保留图SHA/raw绑定和逐组备注。容易方向通常0..30/45帧可见，45–75逐渐出画，不能把所有画外只算最终hold。fullhand SAT采样62008盒/62013袋最小−0.986/−0.372mm，真实手-他物体力事件148/79个，其他条件0。非手臂接触审计无记录项。7/12、完整0/3结论不变。
- `front_route_group_r1`已真终态，runner3223351退出，terminal source timestamp 2026-09-29 16:01:40 UTC核一致后才改下一版。原任务+pose **2/4**（62009双任务过），62008双任务失败；盒maxXY0.230mm、进度0.211mm、921帧top_descend，非目标0，不能把无干扰称成功；袋进度.059149m，仍卡。四条各8RGB+4viewer已实际看并在RESULT写raw/imageSHA绑定；62008盒两物大多可见但手遮挡盒顶，62008袋卡顿，62009目标仍出画。watcher3233667的九项审计已全部exit0，AUDIT_EXECUTION已核。新旧数据依旧diagnostic。
- 新独立`projected_support_reference.py`定义连续**虚拟**控制参考：固定手hull bbox中心的切向坐标+实际hull最低支撑平面的法向高度；该点不一定在mesh或凸包内，不是真实接触点。正确Jacobian为(I−nnT)J_center+nnT J_lowest，不能把随q变化的虚拟offset当固定刚体点。4单测验证精确最低高度、最低顶点切换连续性、有限差分Jacobian、非法输入。
- `audit_support_reference_kinematics.py EP [start_frame]`独立缓存URDF/解析Jacobian，真实q/parcel/姿态/非工作掌anchor初态，400步立即施加关节命令，**无动力学/碰撞/力**，只看下降接近。三个输入：front62008盒firstdescend39；baseline62008袋frame396；baseline62013盒frame400。actual-vertex达到press步数=失败/192/19；projected_front20=72/73/26；projected_center=74/83/39；原顶点加0.10m角运动惩罚=92/失败/19。因此没有采用角惩罚。projected_center最终真实近最低0.2mm顶点群对collision core边距=**1.825/31.954/35.652mm**，近盒接触很靠边，必须查真实载荷/转角/滑脱。原front20只有0.674mm。报告在各EP `SUPPORT_REFERENCE_KINEMATICS*.json`；只离线，不证明物理成功。初期float32影子已以float64复跑覆盖，最终报告一致。
- 在front原版终态/hash核验后，collector加显式`--expert-top-projected-support`仅bounded/coordinated/top diagnostic可用，不与hysteresis/corner混用。从top阶段启用虚拟reference，记录真实最低vertex/point另列；coordinated_step按混合Jacobian解，default行为保留；新模块入source快照。collector/waistcoord编译、4单测过，真实运行已进入控制，无runtime错误。改动还包括顶面目标从front20改**center fraction1**，是明确组合候选，非单变量。
- **当前真任务** `projected_support_group_r1` runner **3320571**，收尾 **3325906** 已验活/hash；完整62008/62009×双任务4条，单Isaac，960/seed0/5N/3mm，与原front路线选择/物理/相机/零位/无助推/所有质量门一致。核心（collector、waistcoord、front、projected等）冻结至终态。最新62008盒step360 `front_guard_lift`，盒X .383015/Y .119474，实测向前约17mm，非目标0；**已建立接触但保护抬手，未成功**。确切guard reason待EP raw/frontal写盘，不要根据此猜测宣布原因；可能与旋转后的通道几何有关，仅假设。
- 接续首先核live与source；该组继续完整4条，读第一条guard原因/真实顶点/接触载荷/姿态，补独立投影reference与实测Jacobian有限差分审核（尚未写/跑这个live auditor），再实际图审。现有support_mapping能算FK/平面高度但其“actual mesh point”解释对虚拟reference不适用，需明确区分，勿直接套结论。front原版剩余审计也需收尾。一般hold远盒恢复仍待；完整多样组+等待→新鲜pilot明确准入/转换train-only统计和阶段采样→共享训练→独立多种子h10全范围仍待。无新训练数据或模型；goal active，未达标，无外部阻塞。

## 2026-09-29 当前：多样基线7/12、完整组0/3；前侧路线完整组实测已启动

- `baseline_diverse_groups_r1`已终态，runner2937924退出，冻结source在新collector修改前核一致，终态证明timestamp 15:45:44 UTC。原任务+pose：depth_a3/4、diagonal_a2/4、reverse_diagonal_a2/4，合计7/12，完整交换组0/3。62004双任务、62005袋、62009双任务、62012双任务过；62005远盒未入区，62008袋/62013盒top_descend卡顿，62008盒/62013袋rear_push干扰非目标36.475/22.592mm且未入区。不能只挑7条建训练集。RESULT.md/JSON已写。
- 12条每条8RGB(0,137,274,411,548,685,822,959)+4viewer(0,315,635,955)已实际查看，RESULT每条写completed/raw绑定/REVIEW_EVEN图SHA和差异备注。大量目标后段画外，62008袋/62013盒手遮挡目标且姿态变化，不能认证全程穿模/接触安全。均匀采样未覆盖短任务早期，仍需早期补图。62005近袋桌边footprint余量0.626mm保留风险。旧watcher2945123仍收尾，最近AUDIT_EXECUTION前7脚本exit0，fullhand/phase尚需接续检查。
- 新`simfoundry/data/front_top_route.py`仅在物体包络最短合法候选为front时用顶部接触替代rear_push；先实测X间隙>=20mm再侧移，接触丢失继承重接触，手/他物体<5mm、他物体移动>10mm、对象间隙<10mm、桌边<5mm均锁定抬手；每步XY最多3mm，实测support lead12mm。阈值是提前撤力guard，原任务/15mm质量门未改。虚拟实际support vertex仍会切换，未解决参考跳变。
- 新控制7单测、原top21、路线候选6均过，collector编译过；尚非动态安全/成功证明。核心待上一批真终态+source验证后才改，已新增显式`--expert-front-top-route`，仅diagnostic baseline top组合可用，真实整手/非目标visual AABB面轴gap每步观测，两个新模块已入源码快照。
- **当前真任务**：`front_route_group_r1`runner PID3223351、收尾PID3233667均已验活，`run_front_route_group.py`，固定960/seed0/5N/3mm，仅加front route，完整62008/62009双任务共4条件，失败照留，单Isaac。原rear/direct条件保持原控制。所有PROTOCOL核心包括新front和候选模块再次冻结，终态前不要改。最新62008盒已到840帧top_descend，盒仅约0.23mm移动，非目标尚0；**前侧路线还未建立稳定接触，不能称已解决干扰/成功**。须按完整组继续并定位接触控制。
- 接续：核live与冻结hash；旧12条余下全套审计/早期补图；新前侧完整组终态和真实图审。优先研究top支持参考XY跳变/接触姿态：0.2mm迟滞、近支持质心shadow此前不足，勿盲目重复调阈值。可考虑独立离线验证控制参考或角运动约束，但未实施、不预称有效。远盒hold仍需实际重接触恢复。完整多样组+等待→新鲜pilot显式准入/转换train-only统计和阶段采样→共享训练→冻结独立多种子h10全部仍待。无新训练数据/模型；整体goal active，未达标、无外部阻塞。

## 2026-09-29 当前补充：斜向两种失败已定位；前/后候选模块准备

- 当前`baseline_diverse_groups_r1`PID2937924、收尾2945123仍在运行，到62012（须接续核验）。固定源码未改。除depth_a的3/4外，62008两任务均失败：盒非目标袋最大XY **36.475mm**（超过15mm门）且未入区，袋未入区；62009结果已写盘后继续按终态pose/图审核，不提前宣称全三组完成。
- 62008盒干扰时间链已从真实force/trace区分：盒-袋首>0.05N在step129、max1.313N；袋>1mm位移133；右手-袋首143、max1.767N；袋>15mm158。都在rear_push，既有物体间碰撞也有手直接干扰。实际盒从(.4,.12)在X向后移动时Y漂到-.02一带，尚未到rear_goal_x .727749即碰袋，不能只归因于最后侧推。`NON_TARGET_INTERFERENCE_FOCUS.json`保留逐事件。
- 已实际看62008盒6事件RGB+3viewer；143后目标/非目标接触区域大多画外，视频不能独自证明接触细节；因果区分依赖原始接触与位移时序，不冒称图中全可见。`INTERFERENCE_REVIEW.json`已写实际范围。
- `audit_front_rear_route_reach.py`独立静态URDF检查62008盒：物体包络前侧x约.372251（初始只向前27.75mm，table margin约17.01mm），后侧x.727749（向后327.75mm）。前侧front20/center/rear20接触点的初始、X移后、同障碍Y、目标区静态点均找到近零解；面轴整手/他物体间隙采样为正。后侧front20各关键点残差约31.6–56.2mm，center/rear更大。仅2起点/点、不作全局不可达或动态安全证明；假想物体坐标仅CPU几何，从未写入仿真。
- 新纯`simfoundry/data/tabletop_route_candidates.py`枚举direct/front/rear，按实际观测姿态AABB检查整段轴向中心路径的对象间20mm余量和原桌面范围；保留拒绝理由，不自动选择机器人动作。6单测过，包括镜像、原lateral前侧不合法、初段碰撞不能被终点间隙掩盖。`DEVELOPMENT_ROUTE_CANDIDATES.json`仅预登记62000..62015的32任务，最短合法对象包络候选20 direct/8 rear/4 front；不是已验证路径。未读取独立测试geometry。
- 62008袋top_descend总702帧，其中396..959连续564帧，末帧实际support与surface XY误差约19/27mm、Z高35.5mm。新`STALL_HYSTERESIS_SHADOW.json`固定实测q/pose：原selector与记录逐值一致；卡段>3mm虚拟切换179次/max53.50mm，0.2mm迟滞83次/max49.79mm，0.5mm61次/max49.76mm。仅加迟滞仍有近5cm参考点跳变，不足以声称解决。可继续研究接触姿态/控制参考稳定性，勿无限仅调阈值。当前迟滞CLI与core/corner绑定，尚未解除、更未在本批应用。
- 接续完整批次及所有审计/图审后，再对前侧顶部物理移近/绕行做实测；同时解决普通far hold未完成及顶部参考切换卡顿，不以只修一个容易条件替代全目标。新准入模块未接线，所有新数据仍diagnostic，总goal active。

## 2026-09-29 当前补充：depth_a 3/4，远盒缺恢复；新准入模块准备完成但未启用

- `baseline_diverse_groups_r1`仍真实运行PID2937924、收尾2945123，已到62008；核心source冻结。62004两任务原数值+pose过；62005近袋过、远盒失败，完整depth_a **3/4**。远盒最终(.663841,-.156074,.772476)，方向进度.146074m，从第110帧hold到959，物体XY不再移动；原入区门失败。近袋虽过，最小完整visual footprint桌边余量仅.6256mm；需要突出而非只报成功。新三组仍未终态/全图审，不称12条件完成。
- 新`audit_incomplete_hold_recontact_reach.py`对62005远盒记录末态独立11D URDF静态多起点IK：上方接近误差~1e-11m，当前顶面2.477mm；保持当前X的名义目标区接触残差11.940mm。若假设真实接触把物体向机器人移20/40mm，再到目标区，静态误差~1e-12m；**只是假想几何，不改仿真物体位姿，不是动力学/碰撞/可见性/全局不可达证明**。下一控制候选可在普通sweep结束却未入区时增加测量目标重接触，并研究物理向前移近；当前不改冻结代码、不把延长hold当恢复。
- 新`simfoundry/data/waist_pilot_protocol.py`和`waist_pilot_audit.py`独立准备：保持原零位/无助推/.015m/.08rad/h10；完整槽位交换与train/val预分、显式wait、设置/seed/预算/工作界精确匹配、控制/物理source、真实raw/trace/orientation及实际review图像hash、冻结collector snapshot。推动feasibility重新计算原门+pose；fresh pilot episode先拒diagnostic/assist，再核合同/source/布局/提示词/时序/新腰原门，wait独立审双掌/腰/空桌。6项单元测试过。
- `WAIST_PILOT_ADMISSION_PREPARATION_AUDIT.json`实际对lateral_a4条重新验证通过，变更seed/steps/腰界3个负控拒绝；冻结原collector snapshot也核过。**collector和converter尚未接线，没有激活pilot合同，没有新训练数据/模型**。schema测试与真实可行性审计都不替代正式pilot链路。接线步骤见WAIST_PILOT_INTEGRATION_PENDING.md，需等当前冻结批次结束后再改核心；旧锁腰和诊断禁入保持。
- 总goal active。继续完整多样组/等待/新鲜pilot转换train-only统计/采样曝光冻结/共享训练/独立多种子h10；独立测试geometry未用于调参。

## 2026-09-29 当前：完整lateral_a专家4/4；三类多样开发组继续实测

**好：baseline_complete_swap_r1完整62000/62001×两任务4/4原数值+pose通过，非目标maxXY均0，首state/action0，无助推。** source终态核一致，runner2810924/收尾2826556均已退出。原袋/盒进度.355093/.356087m，交换.161539/.161929m；原盒max tilt .178981rad，其余<=.004598。每条8RGB+4viewer实际看过，交换两条额外6早期RGB，原盒峰值6RGB+3viewer。新COMPLETE_GROUP_READINESS重算原门/pose/完整固定槽位交换/首RGB配对与实际raw绑定图审通过；RGB MAE .411094/.436696。**仍仅专家可行性，training_ready=false，没有新模型。**

**差与范围：**camera bbox全画外按原袋/原盒/交换袋/交换盒=63/492/63/909帧（各960），中心=208/620/913/921；原盒第262帧tilt峰值画面裁切，随后恢复，不称全程可见或无穿透。原rear_push手桌载荷max袋4.001N/盒6.626N，未记录非手臂>0.5N。整手/非目标fullSAT每20帧min轴间隙19.54/41.85/90.27/75.37mm，末tick无手-非目标>.05N，非全子步保证。独立FK<=3.22e-7m。

收尾兼容性修复：普通路线frontal rows为空，原review/support两脚本失败，AUDIT_EXECUTION原记录保留，AUDIT_RECOVERY说明；review改用完整expert_control，support对无需绕行明确fixed palm独立FK（不假报support vertex核验），已复跑exit0。phase/arm/parcel/hand审计阶段也改用完整expert_control，避免普通路线全标zero；arm/parcel复跑exit0，hand全SAT阶段重标复跑session83693已exit0（物理数值与首轮一致）。原始数据/控制源码未改。

阶段统计更正：原袋/盒release911/829，交换袋/盒64/65，后者release896/895帧约93%，此前frontal-only计数为0是漏计，已纠正。960帧first3权重16实际曝光4.776%，320帧13.151%；数学等曝光48.30超当前sampler32上限，尚非可执行/批准训练配置。以后合格train数据须冻结阶段/任务/等待曝光，不能复制旧采样。

当前`baseline_diverse_groups_r1`真实PID2937924（已验活/source hash），env_isaaclab运行`run_waist_development_batch.py`，固定父配置，依次62004/05 depth_a、62008/09 diagonal_a、62012/13 reverse_diagonal_a，共12推动条件，960帧、seed0、5N/3mm，失败全保留。source冻结，不能并发新Isaac；收尾watcher PID2945123，通用`complete_swap_audits.py RUN`自动9项数字/抽帧准备但不自动视觉批准。当前62004盒在记录release稳定性，未报本组成功。其余b变体/另一lateral组与等待仍待，不把3组扩测当全部8组完成。

接续：核实际PID/进展；当前运行期间可准备新协议准入与采样工作，但不改冻结核心。终态复核12条件全部姿态/力/画面/完整组，按失败类型决策。通过后仍需新鲜waist pilot合同、合格数据转换train-only统计、共享训练、独立多种子h10。独立测试geometry未使用。整体goal active，未完成、无外部阻塞。

## 2026-09-29 完整组复测阶段更新

`baseline_complete_swap_r1`原62000两任务已完成，原数值+pose **2/2**，盒/袋最大tilt .178981/.004598rad，仍待整个交换组实际图审。当前62001正在运行，真实runner2810924、收尾2826556均再次验活；不要重复启动。source仍冻结。

已补齐新审核工具：`audit_waist_complete_group.py`终态后重算原门/pose/配对首RGB与状态/原始hash图审/完整类别交换，不准入diagnostic；在hand_guard旧失败数据实际负控正确报盒失败+缺交换。`waist_group_audit.py`3项测试过；固定slot XY/yaw交换类别，保留category高度，不能误套旧类别固定yaw的合同。

`audit_phase_exposure.py`已对完成的62000两任务实测：袋top_descend401/960帧，盒329/960；release段49/131帧。沿用历史first3权重16时960帧起步曝光仅4.776%，320帧为13.151%；匹配数学曝光权重约48.30，但**尚未批准该训练采样方案**，未来按合格train切分与等待/实际运动阶段冻结。62001容易条件预计release占比更高，终态需重跑全组统计，不把模式release全称物理静止。

准备了可复用`run_waist_development_batch.py`：只在parent COMPLETE_GROUP_READINESS通过后，以完全相同冻结source/settings在预登记development完整交换组续测，失败照留，不触碰独立test。编译通过，并在env_isaaclab实测未通过parent会拒绝且不建输出目录（系统python无numpy，须用env_isaaclab）。**尚未启动扩组**。若当前完整组通过/实际审图，下一步用该runner扩前后/两斜向开发组，随后新鲜pilot合同/转换/共享训练/独立h10。

## 2026-09-29 当前：整手避让审计1/2；恢复完整交换组验证

- `frontal_hand_guard_r1`终态已核source hash、PID2720480退出，14项审计脚本exit0，每条8RGB+4viewer已实际查看。**好**：袋原数值/姿态通过，非目标盒maxXY0.0971mm；3次handguard(558/808/861)后累计请求内移30mm，独立fullSAT采样min4.133mm，末tick记录无主动手-非目标>0.05N；实现间隙与独立FK面轴误差<=1.90e-7m。盒非目标XY0，两类首state/action0、无助推、pose过。**差**：盒仍失败，最终y=-.181810m，缺18.19mm；311帧连续descend和末尾192帧descend，1440帧不能完成。袋/盒方向进度.355105/.331810m，倾角.004502/.013908。camera center画外77/978、bbox全画外0/110，实际盒后期不可见，袋后期裁切。整对仍diagnostic不训练。
- 支撑平面0.2mm内凸组合参考点离线影子：最大局部跳变减少但>3mm次数增加（袋54→137、盒62→100）；未采纳，不据此继续叠控制。该点是虚拟内部参考非真实mesh顶点，原物理未改。
- 推进重点调整：不再无限停留在62000可见角点策略；此前`frontal_top_load5_long_r1`已有原数值+pose2/2/非目标0，主要风险是视觉缺失。按计划B→C不新增逐帧完整可见硬门，**新鲜复测此前成功配置并验证完整lateral_a类别交换**，原全部任务/姿态/零位/无助推/非目标门不变，视觉风险仍逐项报告。历史diagnostic数据不转正。
- 当前`baseline_complete_swap_r1`真实PID2810924（已验活/hash），runner `run_baseline_complete_swap.py`，62000/62001每个两任务，共4条件，960帧/5N/3mm、显式environment seed0、额外整臂接触记录；使用当前兼容代码，非历史逐位复现/非单因素对照。失败条件保留并继续完整组，无训练准入。独立冻结geometry未使用。源码冻结到终态，下一步完整组实际图审+原全部门/姿态/手臂接触/相机/支撑映射；需要显式新鲜waist pilot合同才能转换，不只改role。
- 总goal active。没有新合格训练集、没有新模型；完整多样交换组/等待、正式转换统计/共享训练、独立多种子h10均仍待。新版review_frontal_run支持多case汇总，仅生成pending抽帧，不自动视觉批准。

## 2026-09-29 当前：已证实整手碰非目标；整手5mm间隙＋接触点内移候选实测中

- frontal_hysteresis02_seed0_r1已终态0/2/PID退出/source hash核一致，每条8RGB+4viewer实际已审。960帧袋/盒进度.277716/.317924m、非目标XY0、首state/action0、support/upright过，tilt.004305/.007847。真实支撑点高度界<=.2mm，FK<=3.27e-7m，顶点切换30/39；未复现250帧卡段，但组合seed/迟滞更新不可作单因素结论。差：盒bbox65/960、center499帧画外，实际裁切，袋0/0。拒训练。全部原力/X/core40mm/guard/支持映射/路径审计完成。
- 旧1440帧干扰进一步定位：袋任务左手对非目标盒有15个>0.05N末tick接触样本，max3.632N，首1113；盒>1mm位移1114，max4.630mm，不能只归因于包裹间max.247N接触。HAND_OBSTACLE_CLEARANCE_AUDIT独立URDF FK+真实手2044顶点凸包/盒core完整SAT，采样最小轴间隙-.807mm，接触窗口几何重叠；静态整手+X10/20/30mm假想平移可改善但不保证IK/接触/动态。右手盒任务未见该类接触。
- 新hand_obstacle_clearance.py缓存真实手凸包面轴＋盒面轴，正间隙证明该轴分离，省略edge-cross轴只会保守低估，非相交证明不能用负值替代。独立全SAT抽帧对照验证保守性；旧长袋轨迹5mm影子预警首761，手-盒真实力首1113；旧盒任务无预警。只影子，未证明退让效果。
- 新TopContactBypassState可选hand_obstacle_guard：top_descend/press/push间隙<5mm先lift撤力，下一局部接触点沿投影+worldX内移10mm，累计<=30mm，且裁剪在真实10mm XY内缩与40mm forward margin可行矩形内；重接触点仍每周期锁定，shift跨周期保留。只调整机器人命令，物体不助推。CLI显式开关、live USD另测非目标core并核spawn尺寸，记录间隙/shift/饱和。默认0保留旧路径。36 top测试+3凸体几何测试通过、编译通过。
- 当前frontal_hand_guard_r1真实PID 2720480（已验活/源hash），seed0/0.2mm/5N/3mm/40mm等保留，加上述guard并用1440帧覆盖旧1113接触窗口；控制+预算候选，不称单变量。BLAS/OMP线程1显式记录，原物理/材料/相机/质量门不变，核心冻结。终态务必查触发提前量、实际非目标受力/位移、内移后可达性与图像，可能保守卡住。
- 新独立整手审计将同时输出face-axis gap，与live日志核对（独立FK/矩阵投影，不只调用observer）；完整SAT采样加入guard邻域。guard事件审计已认识hand_obstacle_clearance原因。所有源改动在上个run源hash核验/进程结束后；整体goal active，无新训练准入/模型，完整多样交换组/等待/转换共享训练/独立h10仍待。

## 2026-09-29 当前：延时仅1/2，支撑点卡顿与环境seed问题已定位；0.2mm/seed0实测中

- frontal_forward40_long_r1已终态/PID退出，每条8RGB+4viewer实际已审。1440帧原数值+pose1/2：袋进度.355140m成功、盒.322774m失败；support/upright两类过。袋任务非目标盒maxXY.004630m（仍原.015m门内），真实记录包裹间力max.247N、XY投影轻微交叠2帧，不能称零干扰。盒bbox53/1440、center939帧画外，实际重裁切；袋bbox0/center3。整对不训练。
- 同预算prefix比较：盒本轮前960进度.243807，旧960版.305577；从第61帧接触时出现>1e-6状态/动作/物体微差，79帧>1mm物体差，130帧阶段分叉；初始11D/目标位置完全一致。袋前960 .279587 vs .281965。collector日志Environment seed=None；layout.seed只用于numpy parcel reset/外观，不能称固定物理随机性，更不能把帧预算当唯一原因。REPEATED_PREFIX_AUDIT已两任务完成。
- 盒878..1127连续250帧descend，25次>3mm支撑身份跳变，多次约13mm伴随对准误差。BOX_SUPPORT_HYSTERESIS_SHADOW：0.1→0.2mm使该窗口25→1，全程53→24；max单次14.59→14.90mm反而略大，离线回放不是闭环成功。只允许真实mesh顶点，非修改手/物体。long全套原始力/姿态/FK/高度/core40mm/guard/臂接触/路径audit齐，source hash在后续collector编辑前已核一致。
- 当前frontal_hysteresis02_seed0_r1真实PID 2614865（已核活/source hash）。回到960帧，保留高度界0.1→0.2mm并显式environment-seed0；这是控制+可复现性组合更新，不称单变量。collector新增可选--environment-seed，None保留旧行为；cfg.seed与每episode env.reset(seed)一致，runtime_randomization已实证configured0。layout外观seed与policy eval seed分开记录，不宣称GPU位级确定性。4真实顶点迟滞测试通过、编译通过。核心冻结至终态。
- independent_geometry_r1冻结16组（左右/前后/两斜向各4）、32assignments×2tasks，拟3推理seed共192推动+3等待；连续随机位置、±.35rad类别朝向，完整交换，仅按原初始几何合法性和固定分层配额筛选，未运行/不用于调参。JSON逐hash冻结；初始manifest误称physics seed已更正并保留原稿，布局不改。evaluation_ready=false，预算/模型/腰范围须首次执行前冻结。
- converter新增通用layout.planned_split=test拒绝，train/validation标记传递给make_split；旧仅twopass拒测试，现防generic空间入口漏网。3回归测试过，diagnostic仍拒用。没有新数据准入/模型。整体goal active；完整开发交换组、等待、正式转换共享训练及独立h10仍待。

## 2026-09-29 当前：40mm袋改善/盒裁切退步；1440帧延时诊断运行中

- frontal_forward40_r1终态0/2、PID退出、source hash核一致，每条8 RGB +4 viewer实际已审，拒训练。袋方向进度.281965m（25mm受力修正版.222796）、盒.305577m（.305214）；非目标XY0、首state/action0、support/upright两类过，tilt袋.004681/盒.014409。好：袋恢复推进，重接触袋9/盒8，均edge margin。差：盒center498/bbox27帧画外（25mm版234/0），实际后段裁切，不能只看袋改善。
- raw-force crossaxis/X参考/真实core40mm余量和锁定/FK/近支撑界/guard/臂接触审计齐且通过。整手恢复cross保守clearance袋42.467/盒39.644mm，臂接触只末tick非全子步。新增PARCEL_PATH_CLEARANCE按实际core8顶点XY凸包分离轴：袋最小间隙6.960mm、盒30.453mm，无投影重叠、末tick包裹间力0；不是欧氏距离/全子步证明。袋后段靠近另一物体，继续需重点查干扰。
- 当前frontal_forward40_long_r1真实PID 2528305（已核活/source hash，输出重定向），仅预算960→1440帧/96s，原控制/材料/相机/全部门不变，核心冻结。检验剩余行程是否能完成及后段是否扰动；延时成功必须单列，不能冒称960帧或共享模型h10通过。
- SAVED_WAIST_PIPELINE_AUDIT补足真实配置：ACTION MIN_MAX、STATE QUANTILES、VISUAL IDENTITY；之前standalone QUANTILES动作audit范围不足。14个实际非零腰h10 query，真实factory/registry/tokenizer、相对编码紧邻归一化、train显式stats overrides→save→server式reload一致，动作最大误差8.20e-8rad。单传dataset_stats不能替换旧checkpoint统计（负控约1.2014e8）；现有lerobot_train已显式覆盖，正控确认正确，非历史22/39→7/39原因。临时副本删除，无模型weights预测/仿真执行结论。
- 生产collector新协议仍仅diagnostic，converter合同/审核仍旧；待可行性完整组后明确新协议准入，不能绕诊断禁入/完整交换组/原门/画面hash。整体goal active，无新训练准入/模型；多样完整交换组、等待、正式转换训练及独立多种子h10仍待。接续long真终态→原门+实际抽帧/全程相机/原始力/pose/支撑/guard/parcel path复核。

## 2026-09-29 当前：受力修正消除完全画外但袋退步；40mm接触余量实测中

- frontal_cross_admittance_r1 全部终态审计完成，每条实际查看8 RGB +4 viewer，仍0/2，拒训练。好：袋/盒原support/upright过、非目标XY0、首state/action0；bbox完全画外两类均0（盒原146），盒方向进度.305214m（原.261874）。差：袋进度.222796m（原.269459）退步，盒中心234/960画外且实际后段裁切；tilt袋.004278/盒.044467。袋10次均边缘撤力；盒9次边缘+1次倾斜。
- 原始上一tick力/当前姿态独立审计crossaxis符号/滤波/偏置界/清零通过，实际maxbias袋6.343/盒6.491mm；X anchor/FK/近支撑界/core余量/guard/臂接触报告齐。FK<=2.88e-7m，整手recovery cross最小保守clearance袋42.592/盒39.425mm；只末tick采样非全子步认证。盒平均top_push向后Fx .523→.286N，但各段不同不能称单一因果证明。
- collector完成后runner收尾audit_contacts exit120，重新重定向输出复跑contacts/pose都exit0，原异常保存在INITIAL_RUNNER_FAILURE.json；源hash仍一致、PID已退出。疑似detach输出流关闭，无完整stderr定论，不重写轨迹。
- 45mm配置被collector既有40mm参数上限在启动阶段拒绝，无物理轨迹，失败目录保留。没有扩大参数上限，改为40mm并实际重做静态首/中/末可见腰角IK，max手点误差8.83e-8m（非动态路径保证）。
- 当前frontal_forward40_r1，PID 2459930，已核真实活/source hash；setsid stdout/stderr重定向runner.log。同960/5N/3mm/受力修正等，仅初始前方余量25→40mm，edgeguard12mm不变，目标减少边缘撤手。核心冻结到终态，原材料/相机/全部质量门不变。
- 独立CPU WAIST_VIDEO_LOADER_AUDIT通过：640行状态/动作/时间戳、14处RGB解码/指令/h10动作及padding一致，最大RGB MAE1.392，临时副本已删除、没有训练入库。生产checked_sources仍默认锁腰、合同仍旧，已在计划A注明后续需显式新协议准入合同；不能只改默认值绕门。完整模型配置重载/执行仍待。
- 接续核40mm终态→所有原门和实际抽帧/相机/力/支撑/接触margin/guard审计，分别报告两类，不以盒进步掩盖袋退步。整体goal active；无新训练/数据准入，完整交换组、等待、转换共享训练、独立多种子h10仍待。

## 2026-09-29 当前：固定 X 改善后退但仍 0/2；有界横向受力修正正在实测

- hold_push_x 已终态并实际审阅每条 8 RGB + 4 viewer。好：两类 support/upright 过、非目标 XY 0、首 state/action 0，盒 tilt .008874 rad，盒方向进度 .261874 m（guarded .235393），bbox 完全画外由 528 降为 146/960。差：仍 0/2；袋进度 .269459 m 略退，盒中心仍 501 帧画外，拒训练。具体 RESULT.md 已落盘。
- 当前 frontal_cross_admittance_r1，真实 runner PID 2381540（setsid，已核活与源 hash）。保持同 960/5N/3mm、core/25mm margin/0.1mm 支撑迟滞/12mm edge guard/50mm recovery/X anchor，仅加有界机器人 X 受力修正：目标受力符号由原始 contact shape 顺序定，滤波 .25，gain .0008m/N，单步 .5mm、总偏置 10mm；有效法向载荷 >.3N 才作用，重接触清零。不是对物体施力，材料/相机/门不变。34 top 测试及 4 独立 admittance 测试通过、编译通过。运行期间核心源码冻结。
- 接续独立原始 contact 力/时序/偏置界审计，终态后原任务/姿态/非目标/相机与实际抽帧、整手支撑/近支撑高度、guard/全臂记录接触等复核；再据证据优化。现阶段无新数据准入，无新模型；完整类别交换组、空桌等待、转换共享训练与独立多种子 h10 尚待，整体 goal active。

## 2026-09-29 当前：提前撤力控制住倾斜，但后退/视野退化；推动X锁定对照运行中

- frontal_guarded_recovery_r1已终态0/2/PID退出，每条8RGB+4viewer实际已审，拒训练。好：原support/upright两类过，袋max tilt .003915/盒.014878rad，非目标XY均0、首state/action0。差：盒bbox528/960帧完全画外、中心669，袋bbox0/中心102；盒实际后半程看不到，不能以姿态过掩盖退化。方向总进度袋.274771、盒.235393m（相对forward25的.286904/.262181退步）。
- 新GUARD_EVENT：袋8/盒6次均loaded_edge_margin，原因/切换top_lift/vertical bias清零记录一致。后续top_cross整手collision hull最低世界Z相对两物体保守visual AABB最高Z至少袋42.58/盒40.18mm。ARM_CONTACT末tick记录仅手-桌rear_push与手-目标有>0.5N载荷，未出现非手部arm有载荷；不是所有子步/全臂几何无碰撞证明。FK≤3.34e−7m、真实core margin/周期锁定/0.1mm近支撑界审计过。
- CROSS_FORCE_DRIFT：guard版盒首top_push X约.6454，六段push后X到.6943，最后接近重复press/descend卡住，腰峰值.9198。各段手命令X增加10–19mm、物体X增加2–16mm，平均向后Fx .35–1N；追随物体后退/yaw可能形成不利反馈，非唯一因果结论。forward25有部分top_push物体X反而向前，不能把所有版本后退归为同一原因。
- 当前frontal_hold_push_x_r1（exec6363，PID见RUNNING_PROCESS，已验活/source hash）：同guarded960/5N/3mm/forward25/0.1mm迟滞/补偿/腰偏好/12mm edge guard/50mm recovery/全臂力观察，仅top_push首次把compensated worldX参考锁定，本段不再跟随目标X或yaw引起的surfaceX变化；2mm/frame命令收敛保持，recontact清空并重新接近。物理/材质/相机/原质量门不变，32top相关测试过、编译过；核心冻结至终态。
- 新audit_push_x_anchor.py待终态：独立核每段初始锁定值、段内恒定、2mm slew、recontact清空；仍须结合实际手/目标轨迹和force才解释是否改善。新audit_guarded_recovery_events.py和audit_run_arm_contacts.py继续用于后续版本。
- 接续核真PID/终态→review_frontal_run实际图审→原pose/任务/非目标/相机/wholehand mapping+近支撑界/forward geometry/guard事件/ARM_CONTACT/新X latch/分段推进/横向力漂移。若仍后退再用真实力与跟踪证据修控制，不能仅扩数据或放宽原门。整体goal active，无外部阻塞，无新训练准入/模型；完整类别交换组、等待、转换共享训练和独立多种子h10仍未完成。

## 2026-09-29 当前：25mm余量改善但0/2；提前撤力＋较低重接触对照运行中

- frontal_forward25_r1已终态0/2/PID退出，每条8RGB+4viewer实际已查看，拒训练。好：非目标XY均0、首state/action0；目标bbox整块画外均0（中心画外袋12/960、盒263/960），原surface锁定/真实core25mm初始前方余量/0.1mm近支撑界独立审计过。方向总进度袋.286904、盒.262181m，比迟滞版.246444/.194336增加；盒tilt .509604→.294439。差：仍未进目标区，盒upright失败，袋tilt .151234虽过但升高，盒实际仍明显裁切。不能当数据准入或模型成功。
- 新EDGE_GUARD_SHADOW：上一步力packet + 当前物体pose，用target受力符号（静态mg校验过）法向载荷加权实际接触中心，前方边缘距离<12mm且load>.3N或tilt>.03rad预警。盒前两段预警246/373，tilt>.2是251/379，提前5/6帧；仅影子时序，未证明撤力够快。曾因np bool/float JSON序列化失败，helper显式转原生float、audit转bool后完整生成；没有坏版物理运行。
- WAIST_PRIOR_TASK_TRADEOFF对迟滞版记录的J/q重放bounded IK，动作误差<1.84e−7rad，晚期偏好单步手点差袋<.007mm、盒<.726mm；尚不足以把厘米级卡顿归因于腰偏好，当前未改solver。仅一步线性对照，非闭环消融。
- 当前frontal_guarded_recovery_r1（exec41505、PID见RUNNING_PROCESS，已验活/source hash）：**组合控制变更，不称单变量**。沿用forward25/core/hysteresis/960/5N/3mm/原全部门，仅加loaded edge guard12mm或tilt .03触发top_lift撤力/重接触；首次跨越、最终release仍.91m，之后travel=max(目标当前最高AABB,非目标中心Z+.03)+.05m，实际tip至travel−.015后cross，缩短恢复。默认0完全保留旧路径；新30top/visibility/contact tests过、编译过。物理/材质/相机不变，未给物体施力/位姿帮助。
- 新read-only --trace-arm-contact-forces记录所有shoulder/elbow/wrist命名shape的已解力，保留每次efc力buffer未变断言；原手/parcel数组不改语义，新增arm_contacts。终态运行audit_run_arm_contacts.py检查较低路径的前臂/上臂/桌面/物体接触，不把手部无接触当全臂认证。仅末tick采样，不保证所有子步。
- 接续核真实PID/终态→review_frontal_run实际图审→原全部质量/pose/非目标/相机/支撑geometry+height/实际loadedguard时序/新ARM_CONTACT/分段推进。留意撤力是否太迟、恢复是否引入接触，以及新函数loaded margin是否全程记录。所有source冻结直到终态。整体goal active，无外部阻塞、无训练准入/新模型；完整类别交换组、等待、转换共享训练及独立多种子h10仍待。

## 2026-09-29 当前：迟滞减少切换但0/2；前缘接触余量25mm对照运行中

- frontal_support_hysteresis_r1终态0/2、每条8RGB+4viewer实际已审；非目标XY均0，首state/action0。好：真实mesh顶点/0.1mm支撑高度界独立核对过；袋最大虚拟点切换44.19→14.13mm，顶点总切换袋178→51/盒240→85；方向总进度袋.246444、盒.194336m。差：仍未到目标区；盒最大切换10.53→14.59mm未改善，tilt .509604rad仍upright失败，bbox44/960/center400帧画外；袋tilt .026306过且bbox/center全在画内。全部拒训练。
- 映射audit旧rear无offset字段时假设精确min，迟滞后初报18mm是假设错误，已修：旧rear核最邻近真实mesh顶点和高度；active显式offset仍独立FK，≤3.26e−7m。新collector记录observed_support_offset_local用于全部rear/top观察点，后续不再依赖此回推。新高度界audit误差≤1.47e−9m、无非mesh点。修正范围和间接性在报告明确，不隐藏误报。
- TOP_TIPPING_BALANCE（core和hysteresis均完成）：接触shape0→shape1力符号由静态桌面向上力=mg核对；接触力矩+重力的准静态CoP仅近水平、末tick、忽略惯性/阻尼，不作因果证明。关键几何：旧min worldX角点在首次推动均选到沿任务方向的前缘，box起推仅约11.7mm余量；第237帧约7.2mm余量时开始tilt，244仍有载荷，而控制器等失联才lift。顶面法线正确不等于稳定接触。
- VISIBLE_TRAILING_CORE_CORNER_REACH_AUDIT：完全换到后缘角点，固定≥50% bbox可见腰角下末段静态残差袋约35mm/盒55mm，未执行。VISIBLE_FORWARD_MARGIN_REACH_AUDIT：保留XY真实内缩10mm，令worldY前方至少25mm余量，取可行矩形上min worldX点；首/中段近零，盒末段约6.75mm残差，仍只是静态多起点、无路径/全臂/动态证明。
- 当前frontal_forward25_r1（exec86076，PID见RUNNING_PROCESS，已验活/source hash）：与hysteresis同960/5N/3mm/0.1mm迟滞/补偿/腰软偏好，只接触点上述forward margin25mm；每周期锁定局部点，日志记录实际forward distance；未加提前撤力/tilt反应门以保留本次接触位置对照解释。core/材料/相机/原质量门不变，6新几何测试+既有top/visibility共22过、编译过。冻结源到终态。
- 接续核终态→review_frontal_run实际查看→原pose/非目标/接触法线/手桌载荷/相机/支撑mapping+hysteresis界、新audit_forward_contact_geometry（真实pose/尺寸/每周期锁定/初始25mm余量）、分段推进与tipping。若靠近前缘仍先倾斜，再依据真实余量/倾角研究提前撤力及更短安全重接近；不得因单指标改善准入数据。goal active无外部阻塞，无新训练准入/模型，完整类别交换示范、等待、转换共享训练及独立多种子h10仍待。

## 2026-09-29 当前：真实core角点仍0/2，顶点选择迟滞物理对照运行中

- frontal_core_corner_r1已终态0/2、PID退出，8RGB+4viewer每条实际查看；live USD Cube测量袋(.135,.1276,.04)/盒(.1344,.0864,.045)与spawn核对过，真实10mm内缩，原物理/材质/相机/门不变。好：非目标XY均0，袋support/upright过，目标中心/bbox画外均0；top_press/top_push >.5N记录袋181/181、盒97/97法线15°内。差：两任务均未入区，盒max tilt .613237rad仍upright失败，bbox38/960帧画外、中心384帧画外，实际后段严重裁切，拒训练。方向总进度袋.201569m、盒.152989m，不可当已到目标区。
- 支撑FK≤3.23e−7m、首state/action0；控制点跳变袋44.19mm/盒10.53mm是虚拟点身份变化，真实刚体运动另列SUPPORT_SWITCH_EVENTS。盒600帧后334帧top_descend，360帧205帧实际XY<3mm，但间歇点切换触发抬高；末段影子回放0.1mm迟滞将>3mm切换37→0，非闭环证明。袋也有接近震荡和滑脱，不能归为唯一因素。HAND_FORCE显示手桌载荷仍在rear_push，全部保持报告。
- 当前frontal_support_hysteresis_r1（exec74510、PID见RUNNING_PROCESS，已验活和源码hash）：与core960/5N/3mm/补偿/腰偏好完全相同，仅改support vertex选择：真实mesh上一顶点距精确支撑平面≤0.1mm则保留，否则选距平面≤0.025mm候选中最近者。选择真实顶点，不修改手网格/物体受力；日志明确support_plane_excess和上限，不再宣称选点必为精确极小值。默认0仍逐值旧selector，新4单测过，collector编译过；核心冻结直到终态。
- 新audit_support_hysteresis_live.py待终态执行：独立FK/原顶点集合/物体姿态核对真实顶点身份、高度界与日志，允许1um数值误差（非新增物理容差）。离线离散和插值两种shadow报告仅开发证据；实际采用离散真实顶点方案。core的BOX部分早期audit现已用两任务完整重算；source hash在后续改代码前已核一致。
- 接续：核新run终态/实际PID→review_frontal_run实际审图→原pose/非目标/法线/手桌力/相机/支撑映射/新height界/连续推进审计。若仍失败按真实接触/姿态/回收证据决定下一改动，不能只叠预算或不停同质扩采。整体goal active、无外部阻塞、无训练准入/新模型，完整类别交换组、等待、转换共享训练和独立多种子h10仍待。

## 2026-09-29 当前：发现外观/碰撞尺寸错配，真实碰撞核心角点对照运行中

- frontal_corner_compensated_r1已终态0/2；非目标XY均0，袋原support/upright过、相机bbox与中心全在画内；盒max tilt .629709rad导致upright失败，bbox71/960帧画外。8RGB+4viewer每条实际审完，RESULT记录；拒训练。实际top_press/top_push >.5N样本袋172中162、盒99中99法线在15°内，接触改善但任务没成功，不能只看接触指标。
- 关键新证据：isaac_cfg.py给袋核心scale(.90,.88,1)、盒(.96,.96,1)，可见外壳无碰撞。旧顶角按外观尺寸内缩10mm，对真实袋核心仅X2.5/Y1.3mm、盒7.2/8.2mm。COLLISION_GEOMETRY_FINDING.json记录源码与尺寸，不宣称唯一原因。
- 新parcel_collision_geometry.py从live USD enabled analytic Cube测root-local bounds（忽略隐藏状态），要求唯一/中心对齐，和实际spawn.size核对；3单测过。collector显式--expert-frontal-top-collision-core仅改top接触size，visual size仍用于相机/障碍，元数据记录实测与外观尺寸；原物理/材质/相机不变。纠正visible-corner元数据旧surface_front_inset误标，corner_inset仍10mm。
- frontal_core_corner_r1正在真实运行（exec43856、PID见RUNNING_PROCESS，已验活和source hash），同compensated960frames/5N/3mm/补偿/腰软偏好，仅真实接触几何变化；core源码冻结到终态。live测量或spawn核对失败会中止，不凭离线尺寸继续。VISIBLE_CORE_CORNER_REACH_AUDIT离线显示修正后盒末段10mm静态残差约3.47mm，仅静态多起点，无动态/路径保证。
- 下一步核core终态/实测几何→实际画面→全部原门/法线/力/支撑点/相机审计，继而完整类别交换组。若仍失败另查接触支撑顶点切换（compensated最大44mm仅虚拟点身份跳变，非手瞬移）和姿态/控制。无新训练准入或新模型，goal active，整体目标仍待，不能在专家小样本停止。

## 2026-09-29 当前：可见角点0/2且斜边接触；实际接近误差补偿对照运行中

- frontal_visible_corner_r1终态0/2，非目标0、support/upright过。bbox完全画外均0但袋/盒中心画外379/684帧，实际8RGB+4viewer已审，长期只剩目标一小部分可见，不能以bbox交集判合格。袋最终rearX位移.2180、盒.2447m（不是排序进度）；两类top_descend卡住。
- 原始实际接触证据：top_press/top_push >.5N采样袋62、盒38，**均0个平顶法线15°以内样本**；角点10mm内缩被实际XY跟踪误差吃掉，触斜边后物体继续往后走。盒step218 actualX lag6.60mm、command FKlag2.62mm；step219 6.67/3.44mm；同时存在求解残差和执行跟踪差，不能都归为重力。第223..250物体X约.646→.675，回收更难；非源坐标映射故障（FK≤3.04e−7m）。
- 当前frontal_corner_compensated_r1（exec30968、PID见RUNNING_PROCESS，已验活和source hash）：同960/5N/3mm/可见角点/腰软偏好/原门材料相机，只增加接近XY积分补偿与3mm实际对准门。cross/descend且load<.2N、实际距顶面>15mm才积XY误差，单步≤.5mm、各轴bias≤10mm；接触时冻结，失联抬起清零。near误差>3mm抬高重新对齐，press前实际XY必须<3mm。初始默认旧路线不变；16top/visibility单测通过、编译通过（启动前修复了一处替换导致的缩进错误，没有坏版本物理运行）。核心冻结到终态，Isaac仅一份。
- 新EXPERT_PHASE_EXPOSURE：均匀帧query时960帧的first30占3.125%，320为9.375%；long top接近/恢复占袋58.85%/盒50.83%。此first30是明示统计窗口，不是历史23.4/13.2%的分类器；未来训练要匹配任务/布局/阶段曝光，不能只拼episode数量，也不能删掉恢复段再拼不连续动作。
- 当前最好物理证据仍是frontal_top_load5_long_r1在62000的960帧2/2（非目标0/原pose过），但袋81/960盒484/960完全画外，已拒训练。不得把新角点0/2隐去，也不得把单布局专家2/2写成共享策略目标完成。完整类别交换组、等待、真实转换/训练、独立多种子h10仍待，goal active无外部阻塞，无新训练准入/模型。
- 接续：核compensated实际终态/PID→review_frontal_run实际图审→CONTACT_FACE看是否真平顶、SUPPORT_MAPPING/Jacobian、相机实际裁切、原全部质量和分段进度。如果仍失败应根据对齐/接触证据改策略，不循环宣称启动就是进展。

## 2026-09-29 当前：可见角点接触＋腰姿态偏好物理验证运行中

- 最新已完成frontal_top_load5_long_r1在960帧原62000两任务原数值+support/upright 2/2、非目标0，但相机bbox画外袋81/960、盒484/960；真实抽帧已审，训练不准入。这个物理可行性突破不等于整体目标或同320预算成功。
- VISIBLE_TOP_CORNER_REACH_AUDIT：原相机≥50% bbox投影面积对应的腰角，实际首/中/末top_push姿态，顶面向机器人角点两边内缩10mm，盒末段790帧静态残差从原面中接触约3cm降到.794mm，其他近零。仅多起点静态端点，无整臂/路径/动态/遮挡证明；不直接执行离线q。
- 当前frontal_visible_corner_r1，exec64446/PID见RUNNING_PROCESS；新复合策略，不称单变量消融：top corner局部坐标每次接触周期锁定、失联抬起才清空，防yaw过零角点跳变；保持20mm旧面中默认不变。新top_contact_visibility.py用原标定和实时intrinsics求≥50% bbox投影的最近腰角，仅作软姿态偏好、相机不改。coordinated_step/有界IK新增preferred_step，腰偏好速度clamp(.15*(desired-current),±.015)，原每步/关节限位不变；默认prior0与旧结果逐值一致。14top/visibility+5bounded测试过、编译过。
- 同960frames/5N/3mm/guarded descent/62000/全部原门、材料、机器人、相机。新--expert-frontal-top-visible-corner要求continuous top，排斥inset fraction；元数据/协调trace记录偏好，源码hash含新module/IK/协调器，冻结到终态，不并发Isaac。检查实际结果能否同时改善成功与视野，不能只看规划目标50%。
- 接续核终态/PID→review_frontal_run实际图审→原数值+pose+非目标/相机/支撑点/实际法线/接触力/Jacobian。若通过再完整类别交换组和重复验证；无新训练准入/新模型，goal active无外部阻塞，最终共享策略训练及独立多种子h10仍待。

## 2026-09-29 当前：960帧原62000数值+姿态2/2，但相机长时间丢目标；可见接触几何诊断

- frontal_top_load5_long_r1已终态/PID退出，**两任务原数值+support/upright均通过、非目标0、首state/action0**。袋方向进度.355107m，盒.355397m；袋第911/盒830帧开始release，分别5/4次重接触。严格标明960帧（64s）专家诊断，320帧同策略仍0/2；不是模型h10通过、完整交换组或训练准入。
- **数据仍拒用：**袋81/960、盒484/960帧bbox完全画外，actualRGB[0,137,274,411,548,685,822,959]+viewer[0,315,635,955]均实际查看，盒后半程大段失去目标。虚拟支撑顶点最大切换袋13.29mm/盒7.36mm（非手瞬移）；独立FK≤3.18e−7m。原action连续性门通过，盒max tilt.181rad、袋.00542rad。hand-table力仅rear阶段，HAND_FORCE/分段推进/力臂/相机/映射报告齐。
- 新VISIBLE_TOP_REACH_AUDIT检查实际首中末推送pose、保持原相机至少50% bbox投影面积（诊断偏好，非新增硬门），固定可见腰角并解整手顶面支撑IK。袋3阶段可近零；盒首/中用前缘5或10mm可近零，末段790帧即使5/10/20mm仍残差2.4–3.0cm。不是全球不可达证明、不是已验证路径，不能简单加腰回中就假定修好。
- 当前CPU audit_visible_top_corner_reach.py进一步查靠机器人前角点（两轴都内缩5/10/20mm），希望减小所需前伸；无Isaac运行。角点如果采用必须按接触周期锁定局部角点，防止yaw过零时跳另一角。任何离线q都未执行，原相机/桌面/机器人不变。
- WAIST_PROCESSOR_ROUNDTRIP_AUDIT已追加实际safetensors存取，输出逐值一致；旧统计负控改用实际relative训练文件state_relative_chunk10_20260929_r1/label_preflight/train_only_relative_stats.json（腰q01=q99=0，非零腰归一化约1.31e8）。不是历史22/39→7/39因果；完整LeRobot视频/dataloader/模型执行仍待。计划A已更新具体已证/未证范围。
- 下一步根据可见角点可达性决定新姿态/接触路径物理小样本，再优化恢复时长与完整类别交换组。goal active、无外部阻塞，无新训练准入/模型；不能停在本次物理2/2，完整共享策略目标仍待。

## 2026-09-29 当前：5N有推进收益但仍0/2；960帧重复接触诊断运行中

- frontal_top_load5_r1终态0/2，非目标0，方向总进度袋.148009/盒.165711m。相对3N/3mm基线，单段顶面净移袋3.79→5.67cm、盒2.17→3.27cm；两类仍滑脱重接近，原support/upright过，盒max tilt.164rad（比基线.023大）。各8RGB+4第三视角已实际查看；bbox完全画外均0，盒50帧中心画外。无新训练准入。
- 当前frontal_top_load5_long_r1，exec10681/PID见RUNNING_PROCESS：只录制预算320→960，动作5N/3mm/前缘20mm/失联重接触均同load5，原场景材料相机质量门不变。用足够重复周期判断能否最终完成，不把960结果算作320/h10模型通过。collector环境timeout现在max(40s,(max steps/waits+90)*实际cfg.sim.dt*decimation)，覆盖60帧warmup，runtime_budget.json显式记录；旧<=320行为不变。runner要求恰960帧，源hash冻结，Isaac仅一份。
- review_frontal_run已支持非320长度：320原采样不变，其余均匀8RGB/4已有viewer，RESULT记录具体帧号；必须实际查看，不能自动改visual完成。
- WAIST_PROCESSOR_ROUNDTRIP_AUDIT：实际640帧非零腰[-.622,+.654]，实际converter INDICES/stats+QueryRelativeArm10+QUANTILES正反+同query state解码，6310有效h10标签，action误差8.94e−8rad、state1.19e−7rad，腰维保持绝对。旧coverage80 train_only_stats腰q01=q99=0，负控使归一化腰最大1.312e8；不可复用。只CPU诊断统计/失败开发轨迹，不是新训练数据、不是完整视频/序列化处理器/模型执行认证。
- 下一步看long真实终态/PID→全程阶段/是否release/原姿态及非目标/图审/支撑点/视野，再根据重复接触进度决定优化恢复还是放弃单纯顶面拖动。goal active，无外部阻塞；完整配对多样示范/转换共享训练/独立多种子h10仍未完成。

## 2026-09-29 当前：中心接触减小偏心但新增姿态/视野失败；前缘慢速5N对照运行中

- frontal_top_center_r1终态0/2，各8RGB+4第三视角已实际查看。实际接触偏心X从约5.5–5.8cm降至约2cm，单段yaw变化袋−19.14→−11.91°/盒27.43→15.01°，顶面净移4.74/5.28cm，但盒最大倾角.2398rad使原upright失败、bbox完全画外68/320帧；不能采用此版。非目标0、FK≤3.30e−7m、首state/action0。
- 新audit_top_contact_lever.py逐连续top_push段报告实际接触力臂、绝对Z力矩（非净转矩/冲量）和yaw，近似下一帧postpose。audit_top_tangential_drive修正跨失联段的统计解释。
- 当前frontal_top_load5_r1（exec44936/PID见RUNNING_PROCESS），比较frontal_top_drag_r1仅垂直载荷目标3→5N；恢复3mm/frame、前缘内20mm、同320frames/62000/guarded descent/腰1.0/全部门材料相机。显式--expert-frontal-top-load-n，范围.5..5且非默认限top route；利用既有ContactLoadControl范围，不扩力控制界。5力控制测试与编译过，核心源码hash冻结到终态，不并发Isaac。
- 同时CPU audit_waist_processor_roundtrip.py正在核实际诊断非零腰轨迹的converter INDICES/stats、QueryRelativeArm10、QUANTILES正反处理和同query state解码，留在diagnostic；不绕过训练准入，不宣称完整LeRobot视频/dataloader/模型执行链已过。
- 下一步核终态/PID→实际图审/原pose/非目标/分段推进/力/支撑点/相机，判定更大下压力是否有效（也可能增大桌摩擦）。整体goal active，无新训练准入/模型、无外部阻塞；完整类别交换示范/转换训练/独立h10仍待。

## 2026-09-29 当前：8mm侧驱仍0/2；顶面接触点移近中心对照运行中

- frontal_top_drag_fast_r1结束且PID已退出，两任务原门0/2，非目标0，方向总进度袋.133422/盒.180022m，仍未进±.20区。各8RGB+4第三视角实际查看，盒部分裁切；bbox完全画外均0。支撑点FK≤2.79e-7m，首state/action0；袋顶点变化最大1.42mm，盒.72mm。
- 逐段推进审计已修复跨重接触段混算：袋209..227净移.041484m、手命令.144m，319是第二次推的首帧；盒228..247净移.049107m、手命令.152m。两类仍滑脱。新continuous_push_segments保留原series，首末跨段差不能当连续推进。
- 偏心旋转机制：袋首top_push到末yaw6.43→−12.70°、盒−8.62→18.83°；盒最大倾角.193rad较3mm版.023增大但仍过原upright门。不能继续只加速。
- 当前frontal_top_center_r1，exec35529/PID见RUNNING_PROCESS：只接触位置从前缘内20mm改为沿实际物体朝机器人方向半宽的80%内移（剩20%半宽偏心），同8mm/frame/3N/320帧/62000/腰1.0/.822后推/原材料相机全部门。新--expert-frontal-top-inset-fraction仅top route，范围(0,1]；默认旧20mm不变。新增旋转选择轴/尺寸/非法值测试，10top单测与编译过。所有核心source hash冻结到终态，不并发Isaac。
- 接续核终态/PID→review_frontal_run实际两条图审→力/连续段推进/姿态/顶面法线/支撑点/相机审计。新接触位可能更难达到，不能把静态IK当动态保证。整体goal active、无外部阻塞、无新训练准入/模型；后续完整类别交换数据/转换训练/独立h10仍待。

## 2026-09-29 当前：顶面接触建立但滑脱；连续侧驱速度对照运行中

- frontal_top_guarded_r1终态0/2，非目标0，但两类真正顶面法线接触、均top_push；支撑点独立FK≤2.40e-7m、首11Dstate/action0、顶点变化<.72mm。腰峰值袋.623/盒.689。CAMERA_VISIBILITY全320帧bbox完全画外均0（非遮挡认证），袋中心始终画内、盒101帧中心画外。每条8RGB+4第三视角实际查看，盒仍部分裁切。Jacobian独立审计已生成。
- 固定12mm提前量导致手停住：top_push阶段袋仅.00817m/盒.00561m，末横力.0374/.0170N、垂直约3N。故改连续侧驱并设置失联抬起。
- frontal_top_drag_r1终态0/2，两类均失联后重接近，非目标0；top_push净移袋.03795m/盒.02168m，手命令移动.135/.093m，滑脱明显。手-物μ1、桌-物μ.55来自实际contact buffer，材质不变。各8RGB+4第三视角已实际审阅。
- 当前frontal_top_drag_fast_r1，exec81446/PID见RUNNING_PROCESS：同62000/320frames/3N load/guarded descent/.822居中后推/腰1.0，只连续侧向步长3→8mm/frame。explicit--expert-frontal-top-drag-step-m，范围1..12mm、非默认要求continuous模式，原joint相邻步.08rad门不变。9top FSM单测/编译通过。连续模式已含load<.2N连续3次抬起重接触；source hash冻结至终态，不并发Isaac。
- 接续核终态/PID→review_frontal_run.py并实际逐条图审→audit_top_tangential_drive.py、HAND_FORCE/CONTACT_FACE（实际顶面法线15°）/SUPPORT_MAPPING/pose质量；看实际物体跟随/滑脱/倾角，不能只看手命令移动。若速度无效，应根据法向/切向力和接触位置改策略，不随意改摩擦系数。
- 当前turn为progress（新真实力/视野/坐标证据与新控制器物理对照），整体goal active未完成，无外部阻塞，无新训练准入/模型。完整类别交换数据、转换训练及独立多种子h10仍待，目标不缩小；相机问题可选意见未回复，继续原配置。

## 2026-09-29 当前：顶面接近仍撞边缘，分段下降验证运行中

- frontal_top_contact_r1终态0/2，袋.066369/盒.123526m，均top_press；非目标0。每条8RGB+4第三视角已实际查看，末段目标裁切。
- SUPPORT_MAPPING_AUDIT：638实际支撑点独立FK误差≤3.24e-7m，顶面法向支撑极值误差近0，顶点切换最大<.72mm，首11Dstate/action0。无证据支持映射错误/大幅点跳变。
- 接触主轴Z不足以证明平顶接触：通用contact face审计增加真实法线15°夹角检查，两类top阶段>0.5N样本均没有近垂直顶面法线。盒垂直载荷曾3.83N，但点X落后约2cm、目标后移至.698，最终失联。顶面以下table加载已主要限于rear阶段（3.97/6.87N、21/28帧>0.5N）。
- 当前frontal_top_guarded_r1，exec84914/PID见RUNNING_PROCESS：同320帧/62000/腰1.0/.822居中后推/3N顶面接触，唯一动作变化为分段下降：XY<8mm才每帧降1.5mm到表面+4mm；靠近时XY>15mm抬起，press追踪丢失退回descend并清bias。不降质量门。7top FSM单测与编译通过，applied_z_bias记录在抬起/descend阶段正确置0。source hash冻结，不并发Isaac。
- 接续核终态/PID→图审→HAND_FORCE/CONTACT_FACE（看法线夹角而非仅主轴）、SUPPORT_MAPPING/Jacobian/完整质量→判断是否建立真正顶面接触与侧向推进。当前仍无新训练准入/模型，goal active无外部阻塞，原相机不变。

## 2026-09-29 当前：上方支撑点接触新策略物理验证运行中

- frontal_press_clearance_r1终态0/2，非目标0。手-桌峰值袋20.59→6.79N、盒20.82→8.54N，但仍有230/80帧>0.5N；袋停rear_push、盒tip_press，进度.065612/.174907m。每条8RGB+4第三视角实际查看。压桌减轻不是充分修复。
- TOP_SUPPORT_REACH_AUDIT在真实后移物体pose上，用完整clipped hand沿物体顶面法向的最低支撑顶点，顶面前缘内2/4/6cm：两类均找到静态点误差近零候选、hand minZ约.790/.795、腰≤.98。没有整臂/非目标/动态/相机保证，未执行离线q。
- 新top_contact_bypass.py：exact clipped-hand USD凸包顶点写入assets/robots/g1_hand_support_vertices.json（左2044/右2043，source hash核验）；实际手quat与物体quat均XYZW，本地Isaac math已核。每帧选择顶面法向最小投影点；后移间隙后抬高/XY8mm内接近/下压/力确认/推送/目标释放。垂直3N反馈，bias[-6,+25]mm、表面上2mm基础，推Y lead12mm且XYZ有界；不修改物体pose/force。5单测含XYZW顺序、支撑极值、无力不得推、bias界/释放通过，collector编译通过。
- 当前frontal_top_contact_r1，exec22596，PID见RUNNING_PROCESS：原62000/320帧/腰1.0，恢复居中rearY、保留.822后推高度，然后新top路径；这是复合新策略可行性，非单变量消融。来源hash含新模块/顶点json/clipped USD，冻结到终态，不并发Isaac。
- 接续：核终态/PID→review_frontal_run.py实际8RGB+4第三视角/条→audit_run_hand_forces.py、audit_run_contact_faces.py（现支持top阶段期望Z面）、audit_run_control_jacobian.py、audit_run_support_mapping.py（动态顶点FK/支撑极值/顶点切换/首零位）。旧audit_run_control_point_mapping只支持固定tip，不可直接套top。
- 仍无训练准入/新模型；原目标、非目标1.5cm、无助推、首零位/h10门不变，goal active，无外部阻塞，相机意见未回复则保持原配置。

## 2026-09-29 当前：实测持续压桌约20N，接触高度对照运行中

- 上一goal turn为progress：完成换接触点/严格下降/偏心物理对照、真实图审、FK/Jacobian/完整手轮廓证据，非空转。整体goal active未完成，无外部阻塞。
- frontal_object_frame_rear_r1终态0/2，均rear_push；非目标0，袋进度.066774m/盒.125269m、末yaw31.99°/-38.85°。每条8RGB+4第三视角实际查看，末段目标裁切。
- 新HAND_FORCE_AUDIT：实际手-桌面峰值袋20.59N/盒20.82N，>0.5N有275/269个采样帧；手-目标峰值仅1.90/1.70N，盒另手-桌沿12.03N/6帧。原掌代理0没有覆盖实际指部压桌。末tick力不是冲量/全substep，observer确认force buffer不变；不能仅凭力大小称唯一根因。
- 当前frontal_press_clearance_r1，exec80414，PID见RUNNING_PROCESS：同62000/320帧/物体坐标3cm偏心/腰1.0/严格下降，仅rear掌目标高度.810→.822m。新--expert-frontal-press-z默认保持.810，非默认需frontal诊断且范围.800..850。编译通过；既有FSM高度参数不变。PROTOCOL源码冻结到终态，不并发Isaac。
- 接续：核实际终态/PID→review_frontal_run.py并实际查看图→audit_run_hand_forces.py、audit_run_yaw_contact.py、原完整pose质量→判断桌面加载下降时目标接触是否仍有效。若接触消失也按失败记录，不靠放宽门过关。
- 仍无新训练准入/新模型，完整目标不缩小；可选固定相机意见未回复，原相机保持。后续仍需合格完整类别交换组、端到端转换/归一化验证、共享训练与独立多种子h10。

## 2026-09-29 当前：偏心转角增加但仍0/2；物体坐标接触杠杆对照运行中

- frontal_offcenter_rear_r1终态0/2，非目标0。相对strict baseline，袋末yaw18.92→27.64°、进度.114715→.126737m；盒yaw-19.19→-31.71°、进度.152313→.168287m。每条8RGB+4第三视角实际查看，仍严重相机裁切。物理偏心确有转动机制信号，但仍非成功/泛化/训练准入。
- 当前frontal_object_frame_rear_r1（exec77953，PID见RUNNING_PROCESS并复核）：同3cm偏心，只将rear_push Y杠杆从固定世界Y改为实际quat变换的object-local front(-sizeX/2,-direction*.03,0)；后移X/2mmYslew/320frames/62000/腰1.0/strict descent不变。collector显式--expert-frontal-rear-object-frame，要求tip route和正偏心。14frontal+9tip FSM测试、编译通过。
- 只读--trace-hand-contact-forces扩展solved_contact_trace：原parcel_contacts保持原筛选，另hand_contacts收录手对桌面/其他的接触力，仍检查solver force buffer不变。observer源码已加入本run PROTOCOL hash与collector源码快照。源冻结到终态，不并发Isaac。
- HAND_TABLE_GEOMETRY_AUDIT(strict run)：exact clipped-hand顶点/真实pre-action FK，主动手有约1.9mm落在桌面以下的几何记录（袋81帧/盒91帧>1mm）；只顶点/固定桌面表面、未覆盖面/全部substep/引擎碰撞余量，不直接认定物理穿透或根因。原掌代理为0不能证明全手净空；本run补录实际hand-table力。
- 接续：核STATUS/实际PID→review_frontal_run.py+实际8RGB/4第三视角逐条审→audit_run_yaw_contact.py、audit_run_contact_faces.py、audit_run_control_jacobian.py→审新增hand_contacts中的table接触/force/distance及发生阶段。不要只比较末姿态或总位移。
- 完整手支撑/角点离线候选未获得两类共同可执行证明，未执行任何离线q。侧距8cm低位不可可靠达到，未盲扫物理。整体goal active、无外部阻塞、无新训练准入/模型；原相机意见尚未回复，维持原配置。存储约156GiB。

## 2026-09-29 当前：偏心真实接触转物诊断运行中

- 整体目标仍active；最新已完成接触点改版与严格下降版均0/2、非目标0，均实际图审，无新训练准入/模型。不能把本次专家结果写成模型效果。
- 严格下降对照的坐标/Jacobian已核验，接触仍正面。完整手轮廓SAT显示1.2cm侧距下降会几何重叠；8cm侧距几何可分离但低位接触IK残差袋3.43cm/盒1.83cm，因此未执行扩大距离版本。
- SUPPORT_CONTACT_REACH、CORNER_SUPPORT_REACH、CORNER_FIXED_TIP_REACH均仅离线多起点姿态诊断。整手支撑面限制强、顶点切换目标不光滑，不能把较大残差当全球不可达；右盒30°前侧角找到点误差近零候选，但袋未成对可行，未直接执行任何q。没有全臂/动态/相机保证。
- 当前frontal_offcenter_rear_r1（PID1449516、exec69070，须复核）：同原62000/320帧/腰1.0/strict descent，唯一动作变化rear_push掌Y追踪targetY-direction*3cm，仍2mm/frame，意图物体较近时通过物理偏心接触产生朝所需方向的yaw。指定手不变、无物体助推、不改相机/桌面/质量门。13frontal FSM单测与编译通过，源hash冻结到终态，Isaac仅一份。
- audit_run_yaw_contact.py已生成strict baseline：袋换面时yaw+15.11°、末18.92°；盒-15.75°、末-19.19°。对照需核新run的yaw变化、接触法线方向、targetXY与非目标，不凭规划意图称转物成功。
- 接续：核STATUS/实际PID退出→review_frontal_run.py生成结果并实际看8RGB+4第三视角/条→通用audit_run_contact_faces.py、audit_run_yaw_contact.py、audit_run_control_jacobian.py→比较机制与原全部门。泛化/转换/训练关口尚未达成，不能扩采失败示范。
- 可选相机问题仍无答复，继续原配置；无外部阻塞，存储约156GiB。此turn持续取得真实失败对照和几何/运动映射证据并完成下一受控实验启动，不以启动为完成。

## 2026-09-29 当前：完整手轮廓证实下降路径冲突，进入接触姿态诊断

- frontal_strict_descent_r1终态0/2，非目标0；袋进度.114715m、盒.152313m，均未稳定进区。每条8RGB+4第三视角实际查看；后半段目标裁切。已退出，无Isaac在运行，不要把旧RUNNING记录当活进程。
- CONTROL_JACOBIAN_AUDIT独立URDF中央差分核验30个实际6×11矩阵，最大误差2.44e-7m/rad。无证据支持坐标/关节映射错误；接触仍全部localX而非规划Y。收紧下降并非充分修复。
- HAND_DESCENT_GEOMETRY_AUDIT使用exact clipped-hand USD points凸包与真实物体OBB的SAT：固定记录姿态，规划1.2cm侧外距离下降会轮廓重叠；8cm外距离才有5.2–11.7mm分离余量。只固定姿态假想轨迹，非实际引擎/碰撞余量/整臂保证。
- WIDE_SIDE_APPROACH_REACH_AUDIT：8cm外侧高位Z.92近零残差；低位Z.79袋残差3.43cm/盒1.83cm，均腰.98饱和。故未直接启动8cm物理扫参；需改手姿态/真正接触点，不能只放大距离。
- PAD_INACTIVE_WEIGHT_REACH_AUDIT把另一掌权重1→.2→0，末接触残差基本不变（袋1.79cm/盒1.53cm），无依据放弃另一臂避让。
- 当前CPU audit_support_contact_reach.py（exec33831）探索真实完整凸手沿物体侧面法向的支撑顶点与table高度约束，离线多起点姿态候选。尚无可执行路径/全臂避障证明；不直接执行解。下一步根据可达与轮廓结果选择姿态/接触规划，再物理小样本，不扩采失败数据。
- 9项FSM单测通过；原0位、无助推、h10及其余门不变。goal active，整体未完成，仍无新训练准入/新模型，存储约156GiB可用。相机可选问题仍无答复，维持原配置。

## 2026-09-29 当前：换接触点仍0/2；收紧下降条件与独立Jacobian审计

- frontal_contact_pad_r1终态0/2，非目标0，袋进度.077496/盒.136822m；每条8RGB+4第三视角已实际查看。独立CONTROL_POINT_MAPPING_AUDIT误差≤3.02e-7m，首11Dstate/action0。换点没解决侧接触，袋tip采样无>0.5N接触，盒仍localX。
- 新通用audit_run_contact_faces.py不仅看localX，还对照每帧规划面：extended和nearer两run所有采样有效接触均不匹配所需侧面；不是旋转坐标误判。仅lasttick/下一帧近似pose。
- 旧cross-to-press容许XY20mm，原extended实测下降时X落后14.7/18.5mm，规划距物体前缘仅15mm。当前frontal_strict_descent_r1恢复max-X指尖，唯一动作变化为下降前XY误差需<5mm；原62000/320帧/腰1.0/其余门不变。9FSM单测+编译通过，不宣称全手避障已证明。
- 加只读--trace-control-jacobian-every20，返回6x11Jacobian、实际upperq/active side，未改求解。audit_run_control_jacobian.py用独立URDF中央差分核验；待本run终态后执行。真实PID/session見RUNNING_PROCESS（exec24655），PROTOCOL源码冻结，不并发Isaac。
- CPU补审PAD_INACTIVE_WEIGHT_REACH：探索固定另一掌anchor是否限制可达性，仅静态候选，不可直接执行。相机可选意见仍待答复，继续原配置。goal active，无新训练准入/模型，无外部阻塞。

## 2026-09-29 当前：定位到正面误接触；实测接触部位控制对照运行中

- extended tip、盒初始旋转90°62020、双物体移近5cm62022均0/2、非目标XY0；三run每条8RGB+4第三视角已实际查看，后半段目标离开随身相机。末态/抽帧不能认证全程碰撞。近布局没有替代原62000失败测试。
- TIP_CONTACT_FACE_AUDIT：extended run的tip阶段、手-目标>0.5N采样法线全部以物体localX为主，Y/Z均0。证据仅末物理tick，使用下一帧pose近似；力幅和不是冲量。说明规划侧推未获得预期侧面接触，不能再把前述“顶部接触”作为已确认事实。
- 实际接触手局部位置更居中且低于maxX指尖；OBSERVED_CONTACT_PAD_VERTEX记录最近真实STL顶点（与中位接触位置差左6.07mm/右2.12mm）。新增显式--expert-frontal-contact-pad，仅tip路线；测量/控制统一frontal_state.control_vertex。旧默认不变，8项单测含真实STL顶点/状态转换通过，collector编译通过。
- 当前frontal_contact_pad_r1：原62000/320帧/腰界1.0、命令.98，只改rear结束后的手部控制点。exec26748，真实PID见RUNNING_PROCESS；PROTOCOL源hash冻结至终态。只运行一份Isaac。
- 下一步：核终态/PID→结果/实际图审→比较目标localX/Y接触法线、后移漂移、最终方向进度和非目标；必要时独立验证Jacobian。不得以更换控制点本身当修复。
- 相机是否允许增加固定视角已异步询问，未有答复则保留原相机/机器人/桌面配置；不等待该可选意见而停止现有动作诊断。整体goal active，仍无新训练准入/新模型，无外部阻塞。

## 2026-09-29 当前：.98实转预检完成，1.0工作界同指尖路线对照运行中

- waist98_probe_r1实测[-.979687,.979815]rad，单步跟踪误差.009918rad，首上半身state/action0、max action step≤.08、双掌桌面穿透代理0。4RGB+4第三视角实际查看。故意转腰，正确拒为wait数据；仅空桌预检，不是全身碰撞/部署认证。通用audit_empty_waist_probe.py保存RESULT与图，不要对已审阅run无故重跑（会重置visual pending）。
- 当前frontal_tip_extended_smoke_r1（PID/session见RUNNING_PROCESS.json，exec17888）：同62000两任务/320帧/真实指尖侧接触路径，仅工作腰界.80→1.0，命令保留.02余量=.98；显式extended诊断开关，禁止policy或训练。PROTOCOL列出的源码/网格hash冻结至终态，不同时启动第二个Isaac。
- 下一步：核终态/实际PID→review_frontal_run.py生成全pose汇总与8RGB+4第三视角图→实际逐条查看→audit_tip_mapping.py目前硬编码旧tip run，若审新run应另副本参数化保留旧证据→按原门检目标进区/方向进度/非目标/姿态/连续性并评估相机裁切。
- 本turn取得真实控制/力/可达性/坐标证据，判定progress；仍无新训练准入/新模型，goal active未完成，无外部阻塞。不得以预检通过或启动实验作为目标完成。

## 2026-09-29 最新：指尖坐标核验通过，物理仍0/2；.98实转空桌预检运行中

- frontal_wide_load_smoke_r1（腰界.80）0/2。frontal_tip_side_smoke_r1改实际STL指尖控制后也0/2：袋停tip_press，盒tip_sweep但目标未进区；非目标0。两run共4条各8RGB+4第三视角均实际查看，相机裁切明显，均拒训练。
- 新pure模块fingertip_bypass.py包装原FrontalBypassState：后移逻辑不变，测得间隙后切实际maxX网格顶点控制，抬/横移/降至真实quat变换的物体上侧前端表面，再worldY内侧4mm有界追踪。没有写物体位姿/力。waist_coordination接受optional active_point_offset，inactive仍原掌anchor，返回原掌与控制点两种坐标；默认不变。collector flag --expert-frontal-tip-recontact排斥旧flank/track/load变体。6单测+编译通过，真实STL顶点校验通过。
- TIP_MAPPING_AUDIT逐帧638记录，独立URDF FK误差≤3.15e-7m，首11D状态/动作0。TIP_ACTUAL_POSE_REACH_AUDIT用本次真实物体姿态：腰命令±.78时末接触点残差袋1.72cm/盒1.59cm，±.98静态候选近0；没有碰撞/动态保证，不可直接执行解。袋未tip_sweep，初版报告frame319重复两次，不是独立姿态。
- 当前waist98_probe_r1（PID/session见RUNNING_PROCESS.json，exec74822）：180帧空桌sin amplitude.98、工作界1.0，故意转腰必须拒为wait。新增 --extended-waist-diagnostic显式开关才允许界到1.0，仅expert/probe diagnostic、禁止policy；未把离线1.18用于物理。不静默扩大默认.80。当前PROTOCOL的源hash（含新tip模块/STL）冻结到终态。
- 下一步：核probe实际终态/PID，审零首帧/最大动作步/跟踪误差/掌穿透代理及实际RGB+第三视角；通过后再仅将tip路线腰界.80→1.0作同预算对照。先解决实际接触，保留裁切风险；无新训练准入/新模型，goal active未完成，无外部阻塞。

## 2026-09-29 最新：接触恢复仍失败，±.78实转预检完成；宽腰域对照运行中

- frontal_lead1_smoke_r1与frontal_load_recovery_smoke_r1均0/2，非目标0；每条8RGB+4第三视角实际查看。末段force0；下探版bias饱和-.025，腰命令饱和±.63，不能靠继续调XY/Z宣称修复。相关RESULT.md/json齐全。
- 相同上侧指尖接触点、同物体姿态下，静态多起点IK腰界±.63→±.78：左残差2.206cm→.502cm，右1.144cm→近0。见FINGERTIP_REACH_COMPARISON.md；未验证全臂碰撞/动力学，未实现指尖控制器。
- waist78_probe_r1实际范围[-.779751,.779853]rad，单步跟踪误差.007894rad，首11D状态/动作0，max action step.027378rad、掌桌面穿透代理0。4RGB+4第三视角实际看过；故意转腰，正确被拒为wait数据，非部署认证。collector新增显式probe amplitude，不改旧默认。
- 当前frontal_wide_load_smoke_r1：同320帧/布局/负载3N/lead1cm，仅腰工作界从.65到.80（命令.78）。实际PID/session见RUNNING_PROCESS.json（exec37376），8源hash冻结到终态。新工作界仅隔离诊断，原其余质量门不变。
- 下一步：核终态/PID→生成和实际查看图审→检查有效接触、全过程非目标/倾角/相机覆盖，再判断是否值得完整交换组复验。不要把低FK误差或已启动当完成。
- Goal active，整体共享策略未完成，仍无新训练准入/新模型，无外部阻塞。EXPERT_EVIDENCE_SUMMARY.md汇总已完成物理证据，不能当模型成绩。

## 2026-09-29 XY反馈仍0/2：几何接近不等于接触力；1cm提前量对照运行中

- frontal_tracked_sweep_smoke_r1终态0/2，非目标0。盒末Y=-.013822、掌相对Y=-.0435，记录末两帧active-target force0；接近251帧不代表有效推送。两条8RGB+4第三视角实际看过，RESULT已记录。
- 当前frontal_lead1_smoke_r1（PID/session见RUNNING_PROCESS.json），仅Y提前量4cm→1cm，同320帧/.65腰限/布局/观察器；12单测与编译通过。推盒已失败，袋仍运行，不提前当总体结论。当前8源hash冻结。
- 接下来检查最后真实力与手-物Z距离；如果仍无负载，不继续盲扫Y，而考虑有界下探/接触反馈。原ContactLoadControl只允许上抬bias>=0，不会自动压下建立失去的接触。尚未实现下探版本。
- 上一goal turn为progress：实际完成多个受控物理试验、测得错误接触、修复轨迹，非目标位移降至0；整体目标仍未完成，无外部阻塞，新数据未训练准入。

## 2026-09-29 最新：该交换布局非目标扰动降至0，仍未完成；物体XY反馈横推运行中

- **好：frontal_sweep_x_smoke_r1两任务非目标全过程XY位移均0。差：仍0/2，袋方向进度.103864m，盒.165169m，未稳定进区。** 后移X不可算分拣进度；完整姿态审计和每条8RGB+4第三视角实际复核保存RESULT.json/md。
- 当前frontal_tracked_sweep_smoke_r1，runner/session见RUNNING_PROCESS.json（exec27793）。320帧/.65腰限/同62000，仅横推控制器改实测XY反馈（X=目标X-.06，Y=目标Y+dir*.04，3/6mm每帧上限，Z保持实测起点），避免定时扫走后失去接触。11项FSM单测及collector编译通过；物理结果待定。8源hash冻结至runner终态；Isaac只运行一份。
- 下一步：确认终态和实际PID退出→review_frontal_run.py生成图/RESULT（会重置visual为pending，不要覆盖已完成审阅）→实际逐张查看→比较目标方向进度、非目标、全姿态、力/接触与视野。前述脚本支持当前固定320帧/62000；不能任意套不同长度。
- 本阶段尚无新训练准入和新模型，goal active且未完成，无外部阻塞。开发depth_a4/4与depth_b3/4结论仍保留；近桌边/镜头裁切风险未消除。FRONTAL_PATH_COMPARISON.png绘制三版真实轨迹，不是全手避碰证明。

## 2026-09-29 抬手换面仍0/2；修复横推X冻结跟踪残差

- frontal_recontact_smoke_r1已完成并实际查看每条8RGB+4第三视角；0/2。非目标扰动降低，目标侧推不足。不是训练结果，不入库。
- 推盒sweep开始掌X=.549741但规划flankX=.579431；旧横推锁实际掌X，抹掉仍需补偿的约3cm误差。目标接触短暂，随后碰非目标。手指方向变化已用FK量化，但尚未更改姿态控制，不宣称单一根因。
- 当前frontal_sweep_x_smoke_r1，同320帧/.65腰限/布局/观察器，仅sweepX用30帧平滑回到规划flankX。10项单测及编译通过；结果待定。实际PID/session见RUNNING_PROCESS.json；8源hash冻结至终态。
- Goal active，继续以共享策略多样布局最终闭环为目标；当前仍专家物理阶段，未新增训练准入或模型。

## 2026-09-29 已实现后移间隙，但横推撞非目标；抬手换接触面诊断运行中

- frontal_follow_y_smoke_r1两任务都完成实测后方间隙，进入横推，但最终0/2。非目标位移盒任务12.07cm/袋任务8.10cm。盒任务step173右手-黑袋7.83N直接接触；物体包络间隙不足以保障整手安全。每条8RGB+4第三视角已实际查看，见RESULT.md/json。
- 当前frontal_recontact_smoke_r1：相同布局/320帧/.65腰限，追加抬手→侧面接近→下压→横推阶段。接近点取当前目标X-.06、Y-direction*.06，Z=.92后压向.84；按实测掌位置切换，未证明避障或有效接触。9项FSM单测/编译通过。实际PID/session见RUNNING_PROCESS.json，8源hash冻结至终态。
- FRONTAL_RECONTACT_REACH_AUDIT/WIDE_AUDIT仅静态多起点位置可达性；没有把离线.78腰域解用于物理控制，当前仍.65。
- Goal active，未完成目标，未有新训练准入、未训练新模型。下一步先完整质量/接触/图审，再决定参数，不能凭进入阶段当任务通过。

## 2026-09-29 后推端点反馈仍0/2；实际Y对中对照运行中

- frontal_feedback_smoke_r1同预算320帧完成，仍0/2；袋后移.11780m、盒.13870m，另一物体0；实际查看每条8RGB+4第三视角。仅X端点修复不解决接触可达性。
- FRONTAL_REACH_AUDIT位置IK：X=.54/Y=±.15/Z=.81残差约4.19cm；Y减半约1.02cm、Z=.88约.84cm。无姿态/碰撞/动态保证，不是可执行解。
- 当前frontal_follow_y_smoke_r1，仅rear_push掌Y从初始物体Y改为跟踪实测Y（每帧最多2mm）；尚未增加人为斜向提前量。8单测/编译通过，真实结果待定；实际PID/session见RUNNING_PROCESS.json。运行期间8源文件冻结。
- 整体goal active，未训练/未有新训练准入；下方运行中条目均是各时点记录。

## 2026-09-29 最新：首个完整组4/4，但换位置3/4；阻挡路线继续物理诊断

- goal active，整体目标未完成。新数据均diagnostic/training_ready=false，未转换准入、未训练新模型；旧暂停和下方旧运行记录仅历史。
- goal_release_pair_r1：释放组3/4；远盒倾角从同观察器对照.56521降至.19865，但远袋未到区。
- **好：far_endpoint_pair_r1（depth_a，62004/62005）4/4数值+全pose+任务配对通过。差：depth_b_confirmation_r1（62006/62007）仅3/4，远盒倾角.725775。** 全部标准抽帧已实际查看；far_endpoint另看第三视角。近袋支持余量仅.461mm且与3mm凸边接触最高7.39N，仍不入训练。
- contact_load_pair_r1负载反馈0/4；远盒倾角降至.004629但接触/进度不足；不推广。画面实际查看，见各RESULT.md/json。
- frontal_bypass_smoke_r1已完成：交换阻挡62000两任务均后推目标且非目标位移0，但终点不足/跟踪残差导致rear_push停滞，最终0/2；已看每条8RGB+4第三视角帧。
- 当前frontal_feedback_smoke_r1同布局/320帧/观察器，仅rear_push端点改实测掌-物X反馈（3mm/帧、掌超前最多2cm）；7项单测与编译通过，实机仿真结果待定。实际PID/session见RUNNING_PROCESS.json，不要仅凭此历史条目认定仍运行。新run的8个源hash冻结，终态前不要编辑。
- TABLE_EDGE_QUALITY_FINDING.md记录凸条实际接触，不擅自删除资产。WAIST_POSTURE_REDUNDANCY_AUDIT.json仅离线位置IK：抬掌可减少必要腰转，未实现/验证镜头回正控制。
- 下一步：审查反馈端点是否真获得间隙及横推是否再次干扰；解决路线接触后完整交换组复验、镜头/边缘审核，再转数据、共享训练、独立几何多种子h10。不能用单组通过代替最终目标。

## 2026-09-29 弧形路径完整组仍失败；到位释放与第三视角诊断运行中

- reach_sweep_pair_r1已完成并实际看过24标准抽帧/全pose。近2/4通过，远袋进度.20713但末Y≈.19713仍fail；远盒进度.18615/末Y≈-.19615，且frame108倾角.71968rad失败。近袋支持余量仅.350mm，保持隔离。RESULT.json/md保存；不能凭最终平放或差3mm而放宽门。
- 确认reach runner terminal/PID消失后增加collector --expert-goal-release与--trace-viewer-every；专家在sweep/hold测到 direction*Y >= max(.205,direction*initialY+.16)时保存实际掌XY并抬到stagingZ，保持物体物理运动，无包裹写入/助推。不改变原审计门，也尚未证明成功。reach_sweep.py新增纯predicate，5项unittest通过/编译通过。
- 第三视角使用现有viewer_cam，每5个pre-action帧保存实际JPEG到viewer_layout_*，不作为策略输入；每条viewer_observer.json还记实际d435i相机pose/intrinsics。API为ProxyArray.torch，已核本地源码，当前运行正常。
- 当前run_goal_release_pair.py，exec session94738、PID673340（须复核），输出goal_release_pair_r1。顺序baseline62005带相同viewer→release62004→release62005，160帧。STATUS最近release62004。**冻结PROTOCOL的6个源直至runner结束，不同时启动Isaac。** 源快照包含reach_sweep。先看完整结果与实际第三视角再改路径。
- 新baseline62005数值盒passed，但全pose仍fail：倾角.56521rad；近袋通过仍支持余量.519mm。图审实际看过第三视角frame30及90/100/105/110/120/150裁剪图，盒较小且未采精确峰值，不能称视觉已认证峰值。该组其余标准图仍可补看。
- CAMERA_FK_ACTUAL_CHECK在32真实记录相机pose上验证离线投影坐标链：最大position差2.70e-8m、rotation差3.17e-7rad。仅姿态链，非遮挡/像素渲染时序证明。
- 此goal turn有实质progress：完成反馈对照、弧形新专家与物理验证、可达性/力/相机证据、启动实际goal-release对照。goal仍active，无外部阻塞；未训练新模型，未发布任何本轮数据。

## 2026-09-29 Y反馈无收益；弧形接触路径正在实测

- object_feedback_pair_r1完整对照结束：baseline和feedback均2/4，完整depth_a组均fail；远袋.12971→.04380m、远盒.15735→.11242m，非目标均0。6新+2复用各6实际抽帧/全pose已审。反馈末段接触仍在但主要Z约4.88N，Y仅.15N，袋停止。见COMPARISON/RESULT.md及FEEDBACK_CONTACT_LOCATION_AUDIT.json。
- TERMINAL_REACH_AUDIT用已FK验证源做离线位置IK：腰±.63，末端(.60,.23,.84)最优残差约2.6cm，改X=.55可精确解；加入另一掌anchor也同样。不是全局不可达或无碰撞证明。
- 等反馈runner确认terminal且PID消失后新增reach_sweep.py、专家state.far_sweep_retreat_m与collector --expert-far-sweep-retreat-m；只允许bounded coordinated diagnostic、无cap/bypass/Y反馈。late goal-side Y从.08到exit时平滑退X最多.08m，floor .50；近物X≤.50不改变。源快照已加入该模块。新3项unittest与原4项腰协议测试通过，编译通过。pytest在两个环境均未安装，已用项目既有unittest风格运行，未安装依赖。
- 当前run_reach_sweep_pair.py（exec session75668，PID见RUNNING_PROCESS并复核），reach_sweep_pair_r1依次62004/62005各两任务，160帧，与uncapped baseline比。62004远袋已推进.20713m，但末Y≈.197，仅差约3mm仍按原门fail；另一物体0，不能放宽验收。62005还在运行。**冻结其PROTOCOL列出的6个源码直至结束，不并发Isaac。**
- CAMERA_VISIBILITY_AUDIT真实相机标定+waist FK+物体pose投影，两组各6叠框图已实际检查。uncapped远袋中心78/160帧画外、bbox仍边缘相交，纠正之前“完全出视野”可能误读；feedback远盒bbox76/160完全画外。仅几何视锥，无遮挡/像素级误差认证。训练前需处理关键阶段图像覆盖，不能只数值通过。
- goal仍active，已取得证据并修改验证新专家路径，非阻塞。未训练、未发布新训练数据。

## 2026-09-29 接触上限对照完成，物体反馈完整配对比较已启动

- contact_x_ablation_r1已结束；远袋取消.50上限后进度0→.12971m，记录手袋最大力0→8.10N，盒不动，但仍未达到原任务门。近盒均通过，重复控制仍有约1.05cm轨迹差异。不能称整体解决或统计显著。COMPARISON.json/RESULT.md保存对照。
- 四条全姿态+实际24抽样帧复核完成；uncapped远袋末段主动手/目标离开相机左缘，不能把RGB裁切当成功，亦是后续视觉数据隐患。ACTUAL_VISUAL_REVIEW.json有SHA/帧号。
- 已实际启动run_object_feedback_pair.py，exec session51139，实际PID见最新RUNNING_PROCESS.json并复核/proc。输出object_feedback_pair_r1。顺序feedback62004→baseline62005→feedback62005，复用上轮baseline62004；唯一新干预--expert-object-feedback-lead .04，预算仍160，保留记录器。比较同完整类别交换组，不选单条成功入训练。
- **该runner继续冻结同一组watched源码，结束前勿修改collector/waist_coordination/bounded_ik/paired_sorting/sorting_cartesian_expert。** 不另启Isaac并发。质量/pose报告结束后仍需实际查看新图；所有数据training_ready=false。
- 此goal turn有实质progress：32全批+192实际抽帧、非零腰320帧真实I/O/归一化往返通过、上限单变量物理对照给出局部接触改善并启动后续。整体goal仍active，无外部阻塞；未训练新模型。

## 2026-09-29 development32已完成，接触上限对照正在运行

- development32_r1数值+姿态12/32（盒6/16、袋6/16），完整类别交换组0/8。20条未达原最终任务门，其中8条非目标移动超1.5cm。32条192抽样帧均实际显示，SHA/帧号/观察见visual_groups/ACTUAL_REVIEW.json。两条通过袋样本支持余量不足1mm，不能直接推广。详见development32_r1/RESULT.md。
- 自动接续contact_x_ablation_r1已实际开始，runner PID437003。仍冻结原watched源直到其结束；没有新训练。脚本记录接触力是只读last-tick，不是全物理子步。
- 新waist_transport_diagnostic_r1实际完成320帧raw→LeRobot写入/读回、6张视频帧解码、arm10相对编码+真实QUANTILES processor往返。最大状态误差7.45e-8、动作4.10e-8、腰2.24e-8rad。只为诊断I/O，training_ready=false；模型推理/完整pilot合同/新归一化正式训练链仍未验收。不可把此目录作为训练集。
- CONTACT_ORIENTATION_FEASIBILITY.json用已FK验证源做有限多起点IK，当前±.63rad命令域下6个平掌远接触候选均未精确满足位姿。不是不可达证明；暂不引入强平掌约束，先看X单变量物理对照。
- 持续goal仍active，整体目标未完成，没有外部阻塞。

## 2026-09-29 持续目标续跑：远距接触几何审计与排队对照

- 上一目标turn分类为progress：新增真实源网格审计与持续goal。当前确认PID344981确实在运行development32_r1，未重启。
- HAND_CONVEX_CONTACT_AUDIT.json对已完成样本，用URDF FK变换实际手部STL凸包、在记录物体坐标中以线性规划检验与物体盒的几何交叠。最先两个depth组：近处成功任务交叠约120–123帧；远处失败任务约0–9帧。近/远与类别交换均覆盖。仅几何包络，不等于实际接触力，也不覆盖物理子步；不能把重叠样本自动批准。DEPTH_CONTACT_SUMMARY.json记录明细。
- 下一具体假设：现有expert-max-contact-x=.50使位于X=.60m的目标缺少持续接触。已启动等待队列 `demo/waist_enabled_20260929_r1/run_contact_x_ablation.py`（exec session54851），等待development32终态且验证其实际PID；随后同62004布局、两任务、160帧、相同观察器依次比较capped .50与uncapped 0，记录真实接触力，结果写contact_x_ablation_r1。
- 此排队实验也冻结同一份源hash。**development32及contact_x_ablation均完成前不要修改被监控的collector/专家/审计/有界IK源码。** 不同时启动两个Isaac，不转换或训练。等待队列失败时查看STATUS和runner日志，不能仅因观察超时重启仿真。

## 2026-09-29 用户要求持续至整体目标：自动目标已登记为 active

- 用户明确“请你一直进行下去，直至完成目标”。本次get_goal返回null，因此按更新后的目标创建持续goal，返回status=active；不是把旧任务标为完成。新objective包含多样摆放、类别位置解耦、指定手/方向、非目标1.5cm稳定、空桌等待、首帧零位、后续双臂+腰yaw、无助推、h10、合格完整配对组、共享策略训练和独立布局/多种子闭环及实际画面验证。
- 当前继续现有development32_r1，不重启、不覆盖、不修改其冻结源码。下文有关paused或“工具仍paused”的记录已过时。不能仅结束一批采集即停止整体推进。
- 本turn另做只读手部网格接触几何审计：`audit_hand_mesh_contact.py`与`audit_hand_convex_contact.py`，结果写HAND_MESH_CONTACT_AUDIT/HAND_CONVEX_CONTACT_AUDIT。AABB重叠不等于接触；凸包与物体盒交叠也不等于有负载接触力，不能据此直接标训练合格。用于定位远处目标为何不动。

## 2026-09-29 最新运行位置：development32_r1 正在执行

- 已完成宽腰角空桌probe（实际约±0.640rad，单步跟踪误差≤0.00974rad）及宽腰域绕行对照，后者仍0/2；不是模型结果，不发布数据。URDF FK对仿真误差1.41e-7m；多起点IK在±0.65rad下对当前X≈0.622m绕行掌位仍差约10cm。只说明当前路径有问题，不证明所有分拣策略不可行。
- 当前按8个冻结开发布局组展开32条**专家可行性诊断**，先前后、再斜向、再左右；不是扩采训练。runner `scripts/run_waist_development_feasibility.py`，输出 `demo/waist_enabled_20260929_r1/development32_r1`，STATUS/RESULT逐对更新。源码hash冻结，运行期间不要修改collector/waist_coordination/bounded_ik/paired_sorting/sorting_cartesian_expert。
- 参数：160帧、waist limit .65（命令留.02余量）、bounded coupled IK、另一臂退后.10m/外侧.08m、staging .92、near offset -.13/crossed -.04/far -.11、contact X cap .50。不启用rear bypass。整体专家可行性，不是单变量腰收益比较。
- 所有数据training_ready=false；每几何组保留2交换×2任务，只有完整组数值+姿态通过才进入待图审清单，脚本不会转换或训练。运行结束仍需查看实际画面、非目标全过程和分层失败；不能把单条通过当完整组。
- 最新阶段结论、好/差结果及限制统一见 `demo/waist_enabled_20260929_r1/PROGRESS.md`。原模型与数据未改，整体目标未完成；旧暂停条目已被用户恢复指令覆盖。

## 2026-09-29 实际诊断续报：已定位接近限制与直接推错物体

- `demo/waist_enabled_20260929_r1` 是本轮唯一工作根，所有数据仍diagnostic/training_ready=false，未训练或修改模型。17项配对/腰协议/有界IK测试通过。
- `paired_compare_r2` 四组八条完成：正常布局锁腰/协同各2/2，类别交换各0/2，未证明腰部改善泛化。帧数全160，MATCHED_DIAGNOSTIC.json逐例记录；协同交换停在cross，锁腰交换停press。八条六帧样本已实际查看；锁腰四条缺完整quaternion，不冒称同等姿态验收。
- `crossed_approach_r1`（降低接近高度、缩短侧向准备）两条均停press；真实指定手-目标接触约5–6N，双掌最近约3.4cm。`inactive_retract_r1` 单改另一臂后退/外撤，双掌分离到约15cm，但仍停press，不能将失败直接归因于另一臂。
- `bounded_retract_r1` 修复无约束IK后截腰角不重分配的问题，改有界求解后两条都进入sweep。随后指定手直接接触非目标：袋任务step86左手-盒>1N，frame87盒开始移动；盒任务step88右手-袋>1N，frame89袋开始移动。非目标最大位移17.06cm/8.06cm；两条拒绝，盒子倾角0.643rad另失败。详见CONTACT_AUDIT、姿态与已实际查看的六帧图。只采最后物理tick，不作全子步接触穷尽证明。
- 已进入`rear_bypass_r1`：320帧诊断，先向后方移动目标再横推，阶段切换看实际目标X，无包裹位姿助推。小角度腰域下尚不能实现后移；正在核可达性，不扩采32条或训练。接下来先验证更大腰角空桌运动，再单变量比较可达性。根PROGRESS.md可能早于这条，以各run状态/报告为准。
- 新collector从inactive_retract修订起两协议都保存物体姿态；从bounded_retract修订起保存源文件快照。原等待70默认保留，wait-steps入口已落实，历史320wait补测仍未运行。

## 2026-09-29 用户授权按新版继续：已恢复实际诊断

- 最新用户“行，基于此版更新继续做吧”已撤销此前停止实验的要求；下文paused是历史状态。工具保存goal若仍显示paused，不代表本轮没有执行；本轮按用户明确授权推进，不擅自把未完成目标标为完成。
- 工作目录 `demo/waist_enabled_20260929_r1`。collector新增显式新旧motion_protocol、等待帧数入口、诊断腰角范围和等待漂移门；旧默认锁腰保持可复现，新协议暂限diagnostic。旧配对10项+新腰协议4项测试通过。
- 空桌120帧物理probe完成：初始state/action全零，实际腰角约±0.160rad，一步跟踪最大误差0.00244rad；纯转腰导致双掌最大移动约5.7cm。quality正确拒绝作为wait示范；训练ready始终false。EMPTY_PROBE_RESULT.json及六帧实际图审材料已保存/查看；观察到视角变化。
- 实际非零腰样本的Unitree纯映射函数（AST隔离执行）与arm10相对编码往返误差0；完整导出I/O、归一化和模型推理尚未核验，见WAIST_MAPPING_AUDIT.json。
- 正在做coordinated_smoke：诊断耦合双掌位置IK，腰与双臂共同控制，另一掌保持初始世界坐标。仅为机制探索，未具备全臂避碰保证，不能入训练。首条推盒已完成：目标进区且非目标位移0，但实际腰角0.20149超过预设0.20，按门拒绝；需控制器预留跟踪余量，不放宽质量门。
- 后续：完成本对两任务及图审→加控制余量修复越界→同布局锁腰对照及类别交换诊断→再开展多样布局。不能宣称已解决任务干扰或开始训练。

## 2026-09-29 最新用户约束：允许双臂和腰部运动（本次仅更新文档）

- [硬约束 §2](PROJECT_CONSTRAINTS.md) 已更新：首帧11维零位，之后双臂可运动、腰 yaw 可转动；不增加腰pitch/roll。指定手分拣、非目标稳定、无助推、h10及其余质量门保留；示范首动作零位与模型首预测不强制零的区别已明确。
- 恢复后的执行顺序以 [WAIST_ENABLED_PLAN_20260929.md](WAIST_ENABLED_PLAN_20260929.md) 为准：显式新旧协议与端到端腰角核验 → 小规模腰臂协同配对物理诊断 → 保留旧覆盖并扩多样合格数据 → 受控训练 → 新独立布局验证。既有22/39与7/39均锁腰，不能用放开腰部直接解释旧退化。
- 当前代码尚未启用新协议：collector仍强制腰动作0，audit仍要求腰锁零，专家尚无经验证的腰臂协同；11D相对动作实现前10维相对、第11维绝对，不必未经验证改成relative11。
- 自动goal仍paused，目标文本中的“腰动作零位”已被最新用户约束覆盖；本次不恢复采集/训练/评测。没有把旧实验欠项标记完成。历史条目中的锁腰、active和运行中描述仅反映当时状态。

## 2026-09-29 用户要求原因分析、项目瘦身与计划回顾（保持暂停）

- 完整复盘见 [PROJECT_REVIEW_20260929.md](PROJECT_REVIEW_20260929.md)。空间同协议旧22/39、新7/39；16条由成功变失败，仅1条改善。旧版为coverage80相对动作模型，并非最初300条版本。两版都从pi05_base重新训练，不是旧模型继续训练后的遗忘。
- 新证据：PREFIX_EXPOSURE_COMPARISON核保存sampler审计与实现，推动前三帧实际概率23.4%→13.2%，虽同prefix3/weight16仍因160→320长度改变曝光；此前“配置相同”不足代表训练分布匹配。新数据Y仅3.12cm、固定yaw/单外观、每类轨迹24→12、保持/等待比例改变，多个因素同时变化，因果尚未隔离。
- 项目瘦身实际净释放85.23GiB，可用约159.7GiB：退役10组被后续实验替代的checkpoint（last与编号目录成套移除，元数据另存）；408条旧demo原RGB删除，保留逐数组核验的非RGB状态/动作及5帧图、既有报告；删除临时dist/_build_venv310。细目demo/project_slim_20260929_r1/REPORT.md及manifest/deleted/rollout_archives。
- 当前两版及必要历史参考共11份模型保留，10个last有效；8份配对dataset provenance的120个源raw保护并做SHA复核。本轮全部评测raw/关键证据、训练数据和冻结布局保留。历史已退役模型和RGB不再可加载，不要运行旧脚本尝试找回。
- 目标和恢复后计划：补证据收尾→新开发几何接近/可达性诊断→保留旧覆盖并按全配对组扩多样数据→单变量采样/数据消融→新独立布局确认。当前自动goal仍paused，未启动任何采集/训练/评测。


## 用户要求暂停：自动推进与后台任务均已停止

- 2026-09-29用户“你停下后跟我说”后，已向核实的本轮runner/子进程发送TERM，全部确认不再运行（含policy server与Isaac collector）。模型、已完成数据和报告保留。USER_PAUSE.json记录PID/starttime、原状态及恢复位置。
- 空间39已完整审查，旧22/39、新7/39；local推动旧4/12、新3/12。原分布seed0已采完7条但尚待fullpose/实际图审；seed1被用户中断并标interrupted_by_user，部分文件不可当完整结果，恢复时新建目录；seed2尚未运行。
- wait-duration修补未应用，新旧6条320wait补测未执行；完整目标未达成。不要重跑原training orchestration；恢复需独立接续评测。等待用户明确恢复，不再启动任何实验。


## 2026-09-29 专家接近状态切换接口核对

- 同session57246 verifiedwait40s返回live，原分布seed0继续；未重启、未更改运行源码。
- EXPERT_APPROACH_INTERFACE_AUDIT.json保存真实AST函数参数/state字段/源码SHA和限制：CartesianSweepState接近/下降切换依据掌位误差与高度（cross X<.060/Y<.050；press X<.110/Y<.035+高度），这些不是实际接触证明。cartesian_sweep_palm没有显式非目标物体姿态参数或非目标全臂间隙检查。
- 仅专家函数源级观察；策略直接用RGB出动作、不调用此专家函数，不能据此把模型失败归因于专家接口。旧natural_coverage24已测接近偏移/高度等且无完整组，不能重复参数扫动冒称新方案。后续需新开发布局记录接近阶段非目标运动与手臂几何，先诊断路径机制，再按原门/全配对组验收数据。
- 原分布21回归+后续320wait补测仍进行中/待执行，整体目标未完成。


## 2026-09-29 spatial39完整结论：旧22/39，新7/39，明显退化

- 同session57246持续，进入new_original160_seed0。本turn补seed2/58004两条和58005+wait三条fullpose/25实际标准帧，所有rawSHA核并记录；seed2push0/12、wait1/1。
- NEW_SPATIAL39_FULL_POSES审计39条：组合7/39。SPATIAL39_MATCHED_RESULT.json逐一核同39个seed/layout/task、原h10/cap0/160push/70wait，完整新39条195标准帧图审覆盖+两tilt异常18峰值帧。
- 同原质量门旧22/39、新7/39：旧bag9/18、box10/18、wait3/3；新3/18、1/18、3/3。推动旧19/36、新4/36。新所有pose审计不增加通过，旧缺同等姿态记录，不能把旧原数值成功当严格posepass。
- SPATIAL39_RESULT.md明确拒绝promote/直接扩同窄集；新覆盖不足/片段跳变/接近干扰为受控诊断依据，非唯一原因。原分布21仍继续，结束后pendingwaitpatch+6条320wait+预算/fullpose/真实图审仍必做。整体goal未完成。


## 2026-09-29 seed2/58002–03四条完整复核

- 同PID3041791继续；CPU24519 exit0，四条summary/fullpose和20张实际显示标准RGB/rawSHA/visual_review保存。
- 58002 bag .15923/zonefail、box .24019但actionjump.1024fail且bag固定；58003 bag .25075但带box.1041fail、box仅.07974并带bag.0156fail，原.015非目标门不因接近阈值而松动。四条pose均支持/tiltpass。
- seed2前8push0/8（仅部分结果），当前58004/05/wait后仍original21回归，原runner不改；等全部退出后执行已准备wait320补测链。整体goalactive未达成。


## 2026-09-29 seed2/58001及三seed运动先后证据

- 同PID3041791仍运行；CPU3403正常退出，58001两条fullpose+10真实标准帧/rawSHA/visual_review完成。bag带盒.0932/actionjump.0841/终点不稳；box仅.1168且带袋.2297，均fail，pose均门内。
- LAYOUT58001_BOX_MOTION_ORDER.json及源码核三seed完整trace。失败seed0非目标bag位移>5mm在77，目标box在84；失败seed2分别75和80；成功seed1 box在67，bag全程未超过2mm。2/5/15mm三个阈值均记录，先后方向一致。
- 说明两条失败中非目标出现可测移动早于目标，提示接近/建立有效推动阶段值得定位；不是精确接触起点/受力因果证明，不能把位移阈值冒称接触检测。下一轮仅在新开发布局检验接近路径与目标接触，旧heldout不转训练/调参。
- 当前完整回归及320wait补测仍待完成，整体goalactive。


## 2026-09-29 seed2首pair已审，320wait完整补测编排准备完成

- 同PID3041791原runner继续seed2。CPU51051 exit0；58000两条10真实标准帧/全pose/rawSHA审查完成。bag .15126/zonefail，box .24346但actionjump.0865fail，非目标均固定，pose全pass；不能按到位豁免动作门。
- 新scripts/complete_short_first_wait320.py独立编排6条wait（新旧各3seed，使用各自checkpoint/config/normalizer），合并每model已有12push生成15成员正式local320报告，并跑duration/membership/fullpose与生成图审素材。源及prepare JSON已保存。
- syntax通过；对当前真实stage preflight正确拒绝，不创建输出或启动任务。完整运行尚未测试、未启动；还需等原runner/collector/server退出并应用pendingwaitpatch。不会自动标图审或goal完成。
- 原回归及正式320wait未完，整体目标仍active。


## 2026-09-29 spatial seed1全13条复核完成，推物1/12

- 同session57246 verifiedwait返回live，后台已进入seed2。CPU8521 exit0，58005+wait全pose/15张完整实际RGB审查完成。bag目标.21988m但带box.1124m失败；box .19068m/zonefail另有tilt.52226rad/frame120。
- review_new_spatial_seed1_58005_box_tilt_peak九帧[112,115,117,119,120,121,123,125,128]已真正显示/rawSHA核/visual_review：盒在右手旁明显抬边，袋分离稳定，未见完整翻倒；不据抽帧宣称全视频/精确力来源。
- NEW_SPATIAL_SEED1_COMPLETE_NUMERIC保存：bag0/6、box1/6、legacy70wait1/1，seed1全65标准帧及9峰值帧审查完成。seed0是bag3/6、box0/6、wait1/1；保持全seed计划，不选最好种子。
- 完整spatialseed2+original21仍在原runner中，结束后才应用pendingwaitpatch并补新旧各3条local320wait。整体目标未完成，不promote当前窄集模型。


## 2026-09-29 seed1/58004实际复核完成，推进足够仍会干扰

- 同runner PID3041791仍live，seed1/58005进行中。CPU40129正常退出，58004两条summary/全pose/10帧实际显示审查+rawSHA核+visual_review完成。
- bag目标零位移，手接近后抬起，box也不动；box目标.29127m但带bag.1048m/actionjump.1081失败。所有parcel pose均支持/tiltpass，不豁免干扰和jump。
- 当前seed1前10push1/10，不代表完整最终统计；不能仅加大推程来解决已有任务干扰。完整回归+待collector退出后local320wait修补补测仍需完成，整体goalactive未达成。


## 2026-09-29 seed1/58003实际复核：两项失败

- 同runner PID3041791继续运行，CPU93329 summary/pose/review exit0。58003两条10张实际标准帧已显示、rawSHA核验、visual_review落盘。
- bag目标.33199m但带box.1001m/actionjump.0930/末动，不能仅按大位移当成功；box .18967m且bag固定，但稳定侧区未达，boxtilt.17493rad门内。两条allpose支持/tiltpass不豁免原任务失败。
- 当前seed1前8push只有58001box通过（1/8），其余布局和等待仍继续，未改协议或collector；完整回归和后续320wait补测未完成，整体goalactive。


## 2026-09-29 spatial动作片段衔接检查与seed1/58002实际复核

- 同PID3041791仍live，seed1/58003进行中。CPU47506 exit0，58002两条全pose+10张真实标准图审完成/rawSHA核；bag仅.04202m/actionjump.0810，box零位移/actionjump.0874，均原门fail，pose均门内。
- SPATIAL_FIRST18_ACTION_JUMPS.json及源码保存：只读取完整seed0六布局和seed1前三布局18条，原raw23 action diff与quality max逐条一致。5条有>.08 jump，7次超限中6次在frame%10==0边界；例外seed1/58002 bag frame2/rawjoint19为非工作右臂。
- 这是关联证据，不证明归一化/标签/sampler有bug，也不等于实际关节瞬时跳变。后续开发诊断需兼顾重规划衔接和非工作手稳定，不靠smoothing/cap松过原门；当前运行参数不改。
- 当前原完整回归、pendingwaitpatch及新旧各3条320wait补测仍未完成，整体目标active。


## 2026-09-29 spatial seed1首两布局1/4，已有同布局成功/失败对照

- 同PID3041791继续，CPU53763 exit0。NEW_SPATIAL_SEED1_58000_58001_NUMERIC/POSES和20张实际显示图审完成/rawSHA核；4条pose均门内。
- 58000 bag仅.14359m/zonefail、box晚推进并带袋.1398m/actionjump.1126/终点不稳；58001 bag目标.27509但带盒.0890/actionjump.0927/末动fail；58001 box .20823m/pass、bag不动、boxtilt.12287rad门内。
- SAME_LAYOUT_EXECUTION_VARIABILITY.json核验seed0/1请求layout58001完全相同、h10/cap0/160相同。seed0 box失败带袋.2261，seed1 box通过，说明该摆放至少存在成功执行路径；不应把它一概判为不可达/袋挡死路，不外推所有布局。需要在新开发布局诊断接近路径/接触时序，不将heldout成功rollout转训练。
- 原runner继续，不改当前collector；完整回归和mandatory local320wait补测仍待，整体goalactive未完成。


## 2026-09-29 训练覆盖缺口审计完成

- CPU28986 exit0，对新旧实际train split推动数据按provenance核验raw SHA并读源manifest，TRAIN_GEOMETRY_COVERAGE.json/.md及审计源保存于short_first_model40_20260929_r1。
- 新每类12轨迹/6完整几何组、近远各6，Y跨度3.12cm、朝向固定；旧每类24轨迹，盒/袋Y跨度15.75/15.97cm。类别与前后位置已解耦，但横向/朝向覆盖不足，不满足随意摆放目标。旧geometry_group部分缺失用layout fallback，旧yaw部分缺失且跨±pi，不把这些原始计数/角跨度误称物理独立覆盖。
- 这是数据覆盖不足证据，非唯一退化原因证明。后续应保留已有合格覆盖、在新的开发几何诊断改进专家，按完整配对组扩展Y/朝向并保留失败分母，控制训练曝光；旧heldout不转训练。当前runner继续seed1，原完整回归+320wait修补尚待完成，整体goalactive。


## 2026-09-29 13:24 spatial seed0完整实际复核

- 同PID3041791仍运行，已进入seed1；没有重启。CPU33029完整退出，补58003–05及wait7条全pose与35张实际标准图审，rawSHA核对并记录review_new_spatial_seed0_remaining/visual_review.json。
- 完整seed0共13条：bag3/6、box0/6、legacy70wait1/1。65张标准帧及58000倾斜峰9帧已实际审查。NEW_SPATIAL_SEED0_COMPLETE_NUMERIC.json和BEHAVIOR_BREAKDOWN.json保存，不以单seed代表完整39条。
- 58004 box虽然progress .20753m且bag不动，仍侧区稳定门失败；58000/58002 box零有效推进；另外多条误带动物体。至少需要区分无有效推进/末态侧区不足/非目标干扰/动作jump，不可把所有问题归为堵路。剩余三布局pose均门内，原质量门保持。
- 等原runner完整退出后再应用pending wait patch，补正式local320wait；目标未达成。


## 2026-09-29 13:22 继续旧布局160回归实际图审（前三布局）

- 上一轮清理属于实际进展：r3释放37.47GiB，约75.4GiB可用；当前runner PID3041791复核仍live，未重启。
- 补齐new seed2 wait实际五帧审查、rawSHA记录，70帧短等待仍不满足冻结320wait，后续补测不取消。
- new spatial seed0/58000两项均fail，bag带动box约.0837m，box最大tilt.240405rad/frame93。标准10帧及峰值9帧[85,88,90,92,93,94,96,98,101]已真实显示、校验rawSHA并保存visual_review。左前臂紧邻非目标盒，盒移动/倾斜，未见完整翻倒；不能仅凭画面断言不可达或精确力来源。
- 58001/58002四条summary+全pose审计+20实际标准帧复核完成（CPU36793 exit0）。58001近袋pass/progress.26592、box漂移<1mm；farbox目标仅.09254m且袋被带动.2261m。58002袋progress.17976但侧区fail，盒任务物体零位移。四条pose均门内，合并1/4；本轮前三布局共1/6，仅部分seed0，不作全回归结论。
- 所有评测继续原h10/actioncap0/无助推；不将邻近/视觉重叠自动判为障碍堵路。待完整回归退出后，仍须应用pending wait-duration patch并做新旧各3条320wait，以及全量报告/复核。整体目标未完成，当前窄域训练未改善总体局部结果。


## 2026-09-29 用户要求清理无关数据/checkpoint（r3）

删除 4240 个文件，释放文件分配空间 37.47 GiB；清理后磁盘可用 75.40 GiB（后台验证仍在写盘）。

- 清理 18 个 9月29日之前历史 checkpoint 的 optimizer_state.safetensors；保留全部模型权重、配置和归一化信息，并逐目录标注仅推理、无法原样恢复优化器续训。
- 清理 9月21日 blackcollision_clean32 视觉质量未通过先导数据：保留 000/011/012/023/024/031 六条代表 NPZ，以及每条 Unitree 五张关键帧和所有 JSON 元数据。该数据集已不完整，不得再作为训练集。
- 当前新模型和 relative_chunk10 对照 checkpoint（包括续训状态）、当前训练数据、本轮验证、冻结对照集保持不变。
- 校验 21 份权重文件大小/inode/mtime 未变，20 个 last 链接有效。
- 完整删除清单见 manifest.json、deleted.jsonl；删除前验证无打开文件句柄且文件身份未变。

详细清单：`demo/storage_cleanup_20260929_r3/REPORT.md`。后台 short_first 回归仍运行，未停止或修改。


## 2026-09-29 13:09 局部推物完整结论：新3/12 vs旧4/12，无总体提升

- 同session57246继续，CPU67798 summary/pose/review exit0，新seed2/70015两条fail：nearbag目标.26728m但box移.0776m/actionjump.1369，farbox仅.06995m且bag移.1989m。全parcelpose支持/tiltpass，两行10标准帧实际显示/rawSHA核/visual_review。画面可见nearbag推左带盒，farbox停后右手将袋明显往右带动；不是依靠末态猜测。
- NEW_LOCAL_PUSH_REVIEWED.json全12/60标准帧审查完成，LOCAL_PUSH_MATCHED_COMPARISON.json逐12seed/layout/task匹配rawSHA、LOCAL_PUSH_RESULT.md保存结果：旧nearbox1/3 farbox0/3 nearbag3/3 farbag0/3，总4/12；新2/3、1/3、0/3、0/3，总3/12。新nearbag3条全部干扰box。旧两个farboxtilt峰值额外18帧已审，新parceltilt均门内但动作/干扰门不豁免。
- 明确本次训练未提高总体局部推物率，不将expert32/32通过等同学会，不扩采同样数据或promote。完成旧布局回归和mandatory320wait补测后继续针对袋子退化/训练覆盖与时序差异诊断、修数据/策略；单一因果尚未证明，广泛位置/外观泛化未完成。
- 当前仍原runner继续，newseed2短wait待图审、之后legacy60；等当前collector全部退出才应用pendingwaitpatch并补6条wait320、budget/fullpose/图审，不能遗漏。整体goalactive未完成。

## 2026-09-29 13:06 新seed2首pair0/2：box到位但actionjump，farbag仍侧区不足

- 同session57246live。CPU38854 summary/pose/review exit0，NEW_SEED2_70014_NUMERIC/POSES：nearboxprogress.235726m但actionstep.0868>.08失败（原门不松），farbagprogress.186641m但final未到.20侧区。pairresetpass，所有pose支撑/tiltpass（maxbox .005726rad）。
- review_new_seed2_70014两行10标准帧实际显示/rawSHA核/visual_review：nearbox最终到右区，不能凭末态豁免动作jump；farbag左移旋转后停，手抬起/离开、盒不动。最大actionjump精确帧/joint/h10边界字段已从raw计算写入review；未加smoothing/cap隐藏问题。
- 新nearbox最终2/3原门通过，farbag0/3；剩余seed2交换组/短wait与legacy继续。待补正式320wait后完成全量对照，整体goalactive未完成。

## 2026-09-29 13:03 新seed1短等待实际图审完成，seed2运行中

- 同session57246 live，stage evaluating_new_local320_seed2，70014box实际progress日志推进；磁盘约39GiB。
- review_new_seed1_wait5frames[0,17,34,51,69]真正显示/rawSHA核/visual_review：空桌双手基本静止，掌spread3.98/6.48mm、70frame numericpass。仍protocol_durationfalse，不能代替后续新旧各3seed320wait补测。新前2seed各4push+1shortwait的50标准帧已实际复核（重复firstbox不累计）。
- 无源/配置修改，继续同runner直到新seed2/legacy完成再按WAIT_DURATION_CORRECTION_REQUIRED实施补测；整体goalactive未完成。

## 2026-09-29 13:01 新seed1交换组1/2：farbox首次通过，nearbag重复干扰退化

- 同session57246 live。CPU65052 summary/pose/review exit0，NEW_SEED1_70015_NUMERIC/POSES：farboxprogress.2453317m/pass、bag不动、maxboxtilt.019382rad；nearbagprogress.2330286m但non-targetbox .0927m失败，pose均支持/tiltpass。旧同seed farbox失败且tilt.65969，newfarbox是明确单条正向。
- review_new_seed1_70015两行10标准帧实际显示/rawSHA核/visual_review：farbox后期继续向右，bag固定；nearbag到左区同时box明显被带动、后期手臂抬起。farbox159/319分段位移已量化写入review，不把抽帧当全视频。
- 新前2seeds8push3pass（nearbox2/farbox1，bag0），旧相同8push2pass（nearbag2）。这体现类别间转移/近袋重复退化，非整体问题解决；剩余seed2/legacy必须完整。原mandatory320wait/预算门/全pose/图审仍需执行，goalactive。

## 2026-09-29 12:58 新seed1首pair1/2，farbag位移0，不能统归因于第二段

- 同session57246live。CPU81639 summary/pose/review exit0，NEW_SEED1_70014_NUMERIC/POSES。nearboxprogress.2233366m/pass、bag0，farbagprogress0/zonefail、box0，pairresetpass，全部pose支撑/tiltpass（box max.017225rad）。
- review_new_seed1_70014两行10帧实际显示/rawSHA核/visual_review：nearbox向右稳定；farbag始终不动，左臂接近后抬高/移开，未形成有效首次推动。与seed0前段推进/后段停不同，不能把所有farbag失败都说成第二段转换问题，更不能将TRAIN_RECONTACT_OBSERVATION_TIMING当确定因果。
- 近盒在seed0/1匹配对照从旧fail变pass，这是局部正向；远袋仍0/2、首seed近袋退化，整体改善未证。继续交换组/seed2/legacy，原mandatory320wait补测保持，goalactive。

## 2026-09-29 12:56 新训练数据切换时序审计完成，new seed0短wait已图审

- 同session57246 live，newseed1首pair仍运行。review_new_seed0_wait5frames[0,17,34,51,69]实际显示/rawSHA核/visual_review：双掌spread3.36/6.43mm、numeric70pass，protocol_durationfalse；320补测仍必须做。
- CPU44366 TRAIN_RECONTACT_OBSERVATION_TIMING实际exit0，对新train split12far episodes（val/test未读）比较t140/150/155/159 vs160及实际next10 query-relative labels。t150最大q差.024765–.028911rad，下半画面MAE.575–.720/255，对应next10标签maxdiff.265466–.267136rad；t159 q差.002466–.002874、标签差.031921–.032549。记录rawSHA，不改标签/切分。
- 这是当前新数据切换附近小观测变化对应大未来动作差异的证据，不是相同观测/标签矛盾证明，也不是模型失败根因定论；fullimage MAE背景敏感，补bottomhalf。勿据此直接松门/删数据/引入时间标签作捷径。与已观察farbag后半程几乎无新增推进一起作为后续诊断线索，先完成多seed/legacy。
- 整体goalactive；当前runner不改，mandatorywait320修补/预算门/全pose/图审照旧。

## 2026-09-29 12:53 新模型seed0交换组0/2，首seed总1/4与旧相同且任务退化

- 同session57246 live。CPU21947 summary+pose+review exit0，NEW_SEED0_70015_NUMERIC/POSES：nearbag目标.269583m但non-targetbox .0786m/actionstep .0891失败；farbox目标.067435m且non-targetbag .0347m、right palm/table overlap proxy61frames失败。parcel全pose支持/tiltpass（最大box.009858rad），不豁免手桌/干扰门。
- review_new_seed0_70015两行10标准帧实际显示/rawSHA核/visual_review保存：nearbag前期基本不动，后推左同时盒明显挪动；farbox仅短移、袋挪动、后期右手低。图像不足证明精确几何穿透，只称numeric proxy触发。
- 新seed0四push1/4，旧同seed也是1/4：近盒改善但近袋从pass变fail，远两类仍fail，不能称总体提升。新seed0全部4push20独立标准帧已审，继续seed1/2与legacy，不据单seed停止/改配置。mandatory320wait补测及budget门仍要求，整体goalactive。

## 2026-09-29 12:50 新模型seed0首pair1/2；farbag后半程几乎无新增推进

- 同session57246 live。CPU31201 summary+pose+review exit0，NEW_SEED0_70014_NUMERIC/POSES保存：nearbox.218216m/pass，farbag.1679225m/侧区fail、box位移0。pairresetpass，两物体allpose支持/tiltpass（bag最大.004074rad）。review_new_seed0_70014两行10标准帧实际显示/rawSHA核/visual_review，box5帧重复前review不重复累加。
- NEW_SEED0_FAR_BAG_TIMING对exact matched baseline/new/heldout expert只读trace：新bag frame159 progress.1673394m，final.1679225m，后160只加.0005831m；专家后160加.1138697m（final.2925255）；旧后160加0。新前160推进接近专家，但没有有效完成后半段再推；239/319手继续移动、末掌Z.989m且未带动物体。图像确认后期接近/抬臂，不能据此说两段控制学会。此是单seed行为缺口，不证明训练数据冲突/全局因果；heldout专家仅诊断不入训练。
- 正向近盒同seed0消除旧袋6.8cm干扰，但farbag仍fail。继续完整seed0交换组/其余seeds/legacy，mandatory320wait补测仍在，整体goalactive。

## 2026-09-29 12:48 新模型首nearbox通过，实际5帧和全pose复核

- 同session57246持续live，stage evaluating_new_local320_seed0，policy serverPID3410036实际ready，70014 box完整320numericpass：targetprogress.2182161m、non-targetbag位移0、maxactionstep.063524rad。NEW_FIRST_BOX_POSES全320姿态support/uprightpass，maxboxtilt.00433883rad。
- CPU70436首boxreview exit0，review_new_first_box5frames[0,79,159,239,319]真正显示/rawSHA核/visual_review保存：nearbox右推进侧区稳定，bag不动。与相同seed0旧nearbox失败（袋6.8cm/actionjump）是单条正向匹配结果，不等于整体提升/泛化完成；farbag正在继续。
- baseline seed2短wait70frames也真正看5frames[0,17,34,51,69]，review_baseline_seed2_wait记录pass但protocol_durationfalse；旧baseline全部15原轨迹75标准帧+18tilt峰值已图审，短wait仍须补320。
- 当前计划/参数不变，继续完整新模型和legacy评测，最后pendingpatch+wait320补测+budget/fullpose/图审。整体goalactive未完成。

## 2026-09-29 12:46 baseline全部12push已数值/全pose/真实图审，4/12通过

- 同session57246持续。CPU23752 summary/pose/standardreview exit0，seed2/70015近袋.271141m/pass，farbox.126648m/zonefail且全pose tilt.64303493rad at107。CPU93060峰值9frames[99,102,104,106,107,108,110,112,115]已真正显示/rawSHA核/visual_review保存：盒104–108右手旁抬边后110–115回平，袋分开静止，未见全翻倒；不是袋堵路证据。
- review_baseline_seed2_70015两条10标准帧也真正显示并记录。BASELINE_LOCAL_PUSH_REVIEWED.json整合6组/12push：nearbag3/3、nearbox1/3、farbag0/3、farbox0/3，总4/12，60独立标准帧+两个倾斜峰值18帧全部实际看。原numeric成功数与额外pose组合一致（倾斜case原本已经zonefail），但不忽略倾斜风险。
- 等待项不计入12push；seed2短wait仍需看图，所有local70wait必须后续新旧各3seed补320并跑budget门。当前不是完成模型优化，新模型评测接续runner。整体goalactive。

## 2026-09-29 12:43 baseline seed2首pair1/2已完整图审/pose检查

- 同session57246继续live。CPU23997 summary+pose+review exit0：BASELINE_SEED2_70014_NUMERIC/POSES；近盒progress.271409m/pass、袋基本不动，远袋progress.0074436m/失败，pairresetpass，所有pose支撑/tiltpass（最大box.005617rad）。
- review_baseline_seed2_70014两条10标准帧真正显示/rawSHA核/visual_review已写。nearbox右推后稳定、farbag几乎没推进，后段左手已离开袋；样本未见box挡路，不作全局物理可达性结论。baseline同布局不同seed差异明显，不稳定，但新模型尚未评测。
- 继续70015与seed2短wait后新模型；mandatory320wait补测与budget/fullpose/image审计仍按前条，不能以当前混合320push/70wait summary当正式local320通过。整体goalactive未完成。

## 2026-09-29 12:41 baseline seed1短wait已图审，320wait补测入口准备好

- 同session57246 live，stage evaluating_baseline_local320_seed2，seed2/70014盒已numericpass，袋仍运行；未对未完成pair作总体结论。
- review_baseline_seed1_wait5frames[0,17,34,51,69]真正显示/rawSHA核/visual_review保存：空桌双手基本静止，原70frames pass，掌spread左2.02mm/右8.02mm。protocol_duration_passedfalse，短wait不计320验收。
- 新scripts/run_pi05_wait320_sim.sh由localrunner隔离生成，移除push循环，仅wait，显式--wait-steps320并核实际raw q/action/RGB和quality.frames全320；bash -n通过。WAIT320_RUNNER_PREPARATION源SHA/未运行/依赖pendingcollectorpatch。当前运行collector/原orchestration未改。
- 当前批次终止后核原sourceSHA、应用pending_wait_duration_fix.patch（default70保留）、新旧各3seed用新入口freshdirs补wait320；先实际runtime验证，最后新组合15episode summary跑audit_local_evaluation_budget.py和pose/image审计。不能遗漏该补测，也不需重训。整体goalactive。

## 2026-09-29 12:37 baseline seed1交换组1/2，发现盒瞬时38度倾斜并实际峰值图审

- CPU60896 summary/pose/review exit0：70015近袋progress.43259m/pass，farboxprogress.17722m/侧区失败。新增allpose抓到farbox max tilt.65969094rad（约37.8度）at101，超过.20；standard5frames未表现峰值。support仍pass。
- review_baseline_seed1_70015两条10标准帧已真正显示并记录；CPU44253生成额外9峰值frames[93,96,98,100,101,102,104,106,109]、显示后review_baseline_seed1_70015_box_tilt_peak/visual_review绑定rawSHA。可见盒在右手旁98–102抬边立起后104–109回平，未见完整翻倒；袋静止且分开，不是袋挡路证据。原numeric侧区fail同时有额外tilt风险，不忽略瞬时姿态。baseline前2seeds8push仅2pass（均nearbag），非新模型结果。
- 新scripts/audit_local_evaluation_budget.py对正式local报告强制15成员、实际q/action/RGB长度、h10/cap/seed与冻结协议；BUDGET_GUARD_CHECK用真实seed0数据验证拒绝70wait并接受4条320push。全15positive runtime待补齐wait后运行，不能把局部check当完整通过。原WAIT_DURATION_CORRECTION_REQUIRED/pendingpatch仍必须在当前collector退出后实施，补baseline/new各3seed320wait，原70wait仅诊断。
- 同session57246未停止/重启，继续原批次。整体goalactive，未达成泛化目标。

## 2026-09-29 12:34 baseline seed1首pair0/2，10标准帧与全pose已复核

- 同session57246仍live。CPU34147 summary+pose+review terminalexit0：BASELINE_SEED1_70014_NUMERIC/POSES保存。bag进度.167877m但final侧区不足.20所以失败（不是低于.15进度）；box进度.375924m但non-targetbag移动.1873m及actionjump.1556失败。pairresetpass，全pose支撑/倾斜pass，最大box .036515rad。
- review_baseline_seed1_70014实际显示10frames[0,79,159,239,319]/rawSHA核/visual_review记录。bag转动向左后停、box静止；box任务袋被明显带动旋转，159右手临近袋，但不作精确接触力归因。未改运行中的collector或参数。
- 原WAIT_DURATION_CORRECTION_REQUIRED仍必须执行：当前批次结束后补新旧各3seed320wait，短wait不可作为正式local320验收。继续runner后续seeds/new/legacy，goalactive未完成。

## 2026-09-29 12:32 重要：local等待时长协议缺口，正式对照必须补320帧wait

- 本轮发现frozen heldout_protocol.wait_steps=320，但collect_paired_sorting.py horizon硬编码wait70，run_pi05_short_first_sim.sh只传--steps320所以不覆盖。baseline seed0 wait实际frames70/pass，双掌spread1.69mm/7.28mm。不能称完成320frame等待。推物实际320未受影响，旧legacy等待本来70保持原对照。
- review_baseline_seed0_wait标准帧[0,17,34,51,69]已真正显示/rawSHA核，空桌双手基本静止；visual_review明确protocol_duration_passedfalse。不把短等待通过冒充长等待通过。
- RUN/WAIT_DURATION_CORRECTION_REQUIRED.json强制后续：当前orchestration/collector全部退出后应用pending_wait_duration_fix.patch（增加--wait-steps default70；idle仍70、push不变），baseline/new各3seeds在fresh dirs用layout73000/--wait-steps320补做；正式local320最终汇总使用每模型原12push+新3wait320，原70wait仅诊断留存，不删除/替换源记录。patch已生成/编译但未应用，当前训练/评测shell及运行collector未改。检查patch原sourceSHA再应用；运行进程退出后再做，绝不重启训练。
- 当前同session57246 live，stage evaluating_baseline_local320_seed1。必须在最终模型结论前解决时长缺口，以及原有POSE_AUDIT_FOLLOWUP全pose/实际图审。整体goalactive。

## 2026-09-29 12:31 baseline seed0两布局推物1/4，交换组完成图审

- 同session57246继续，70015 pair已evaluation_complete/resetpass；CPU75966 summary+pose+review exit0，BASELINE_SEED0_70015_NUMERIC/POSES和review_baseline_seed0_70015写盘，两行10帧实际显示/rawSHA核。70015近袋通过progress.2315585m、盒静止；远盒失败progress.0710457m，160至319零XY变化。全pose支撑/tilt均pass，bag最大.002967rad、box.001353rad。画面远盒略后移/右移后停，右手分离、nearbag静止；无样本中可见挡路，不作力因果或全局结论。
- baseline seed0当前4push中1pass，两个远物体都推程不足，近盒带动袋失败，近袋成功。只是单seed局部趋势，不是新模型结果。等待空桌及其他seeds，runner持续不重启。全4push20独立标准帧已实际看（firstbox重复review不累加）。
- 整体目标仍未完成；待完整基线、新模型、原布局回归、四份fullpose及实际视觉复核。

## 2026-09-29 12:28 baseline首pair 0/2，10帧已图审，pose检查完整通过

- 同session57246仍live，baseline seed0 70014两任务已evaluation_complete：bag推程.08673m/zonefail，box进侧区但袋移动.0678m及actionjump.0971失败，pair reset通过。BASELINE_SEED0_70014_NUMERIC/POSES保存局部完整2ep（不是全15summary）；所有320frame姿态support/upright通过。后续70015正在执行，未改任何参数。
- CPU47047 make_review exit0，review_baseline_seed0_70014两行/10标准帧真正显示，rawSHA核后visual_review保存。box5帧与上一review重复，不计新增独立帧。bag短距旋转推进后停止、后段左手可见分离，box静止；不支持这一个case被盒子挡住，不是全局障碍结论/接触力证据。前160与最终推程、后160运动量已写visual_review，检验延长时间是否有帮助。
- 整体goalactive；继续同runner，完整新旧对照/allpose/图审后再作模型结论。

## 2026-09-29 12:26 baseline首条闭环失败已实际图审，姿态捕获运行验证通过

- 同session57246持续live；baseline_local320_seed0/layout70014，collectorPID3264783实际运行，首box完整320frames失败：non-target bag移动.0677986m，actionmaxstep.0971067rad，目标progress.41597m。不是新模型结果。后续bag仍运行，暂无全批汇总。
- FIRST_POLICY_POSE_CAPTURE实际确认新policy parcel_orientation.npz捕获320帧/2物体有效；首box轨迹两物体support/upright均通过，max tilt box.006867、bag.008126rad；sourcehash记录。没有据首条声称全评测覆盖。
- make_rollout_review session64644 exit0，review_baseline_first_box包含1条/5frames[0,79,159,239,319]已真正显示并写visual_review/rawSHA。79右手盒子与袋邻近；后盒出相机右边、袋明显移位；pose仍桌内，所以不是掉桌证据，抽帧不证具体手/物体接触路径。全评测后仍做POSE_AUDIT_FOLLOWUP及完整实际复核。
- 继续原训练评测runner，不重复启动；整体goalactive未完成。

## 2026-09-29 12:22 新模型训练保存/检查完成，baseline local320闭环已开始

- 同session57246/runnerPID3041791持续运行，没有重启。train.log实际14480步完成，12:22:01 End of training；final validation1420frames/loss .0079358943（随机flow loss，不等于闭环成功）。新checkpoint已保存于lerobot/outputs/short_first_relative_chunk10_20260929/package_sorting_pi05_1gpu_20260929_114146/checkpoints/014480/pretrained_model；last有效，整checkpoint约9.1GiB。
- CHECKPOINT_STATS passed，保存的normalizer统计与train-only relative统计一致；EFFECTIVE_SOURCE_ACTION_CHUNKS_AUDIT passed，8380查询/10步/921800标量，源标签maxerror0、跨episode0、val未读。实际参数/prefix/finalval门均通过后runner自动进入evaluating_baseline_local320_seed0；evaluation/baseline_local320_seed0.log显示policy server ready PID3261298。新模型尚无闭环结果。剩余约40GiB。
- 继续同57246监控，baseline/new各15local320、new60legacy160按冻结计划。必须完成POSE_AUDIT_FOLLOWUP四份完整汇总的allpose检查（新collector policy quaternion捕获尚待实际输出验证）、真实关键帧及失败peak复核；不能以训练/数值结束为总体完成。局部geometry/单外观数据限制仍在，整体goalactive未完成。

## 2026-09-29 11:48 训练同进程持续；数据指令重复率差异已量化

- 同session57246实际poll仍live，runnerPID3041791/accelerate3041939存在，磁盘约49GiB。训练未变更。
- 新TRAIN_COMMAND_EXPOSURE.json对新旧训练split所有源action计算相邻11D指令差<1e-7（不是物体或关节静止）。新push每task12ep×320=3840frames，与baseline24ep×160=3840相同；新push各25%指令完全重复，旧0%，来自near后160exacthold。wait新10×70=700，旧20×70=1400。独立轨迹数减半/等待占比减少/推完hold增加都是已确认分布差异，不能把后续变化唯一归因于专家两段推；若提前停或wait退化可据此定位。当前不改已运行训练，不将描述性统计当坏数据或失败证据。
- 后续仍完成原冻结评测和POSE_AUDIT_FOLLOWUP/实际看图；整体goalactive，尚无新模型闭环结论。

## 2026-09-29 11:46 训练持续；补齐策略闭环物体姿态记录缺口

- 同session57246持续live，实际train.log已约1K步/14480，未报错。无重新启动或额外GPU采集。
- 查明collect_paired_sorting.py之前只在expert_front_reposition时记录parcel_orientation.npz，普通策略评测缺姿态，不能仅凭位置和5抽帧排除短暂倾斜。已仅将两处记录/序列化条件扩展为expert_front_reposition or policy_port；无动作/物理/门限修改。当前只有训练运行，collector未在运行。RUN/collector_before_pose_recording.py及POSE_RECORDING_CHANGE存前后SHA；实际策略capture runtime待评测核实。
- 新scripts/audit_policy_parcel_poses.py独立检查所有pre-action姿态的nominal cuboid XY支撑及tilt<=.20，保留原numeric结果、组合结果、peak帧及源SHA；wait隐藏物体不适用pose门；缺push姿态直接报错。已合成upright/瞬时.25tilt/边缘越界验证，并对现有32expert的64物体pose与独立审计精确一致，POSE_AUDITOR_REGRESSION记录。这不是策略运行测试。
- 未编辑运行中的训练评测shell。POSE_AUDIT_FOLLOWUP要求4个EVALUATION汇总完成后逐一跑新增pose audit，再真实看图；若新增记录缺失，需定位而非默认为pass。新旧baseline/local与newlegacy均调用同collector，因此均会记录。整体goalactive，广泛泛化尚未证明。

## 2026-09-29 11:43 新共享策略已实际训练，数据转换/标签审计通过

- 转换session57004 terminal exit0；数据lerobot/lerobot_sim_short_first_pilot40_20260929：40ep/9800frames，34train/8380，6val/1420，test70014/15排除。export audit session56025 exit0：全部state/action/prompt行一致、120解码抽帧maxMAE1.2917、无布局泄漏。relative label stats session38620 exit0：训练窗口源标签误差0、roundtrip5.96e-8，val未读；并非新模型成功。
- RUN=demo/short_first_model40_20260929_r1。prefix policy/DECISION源hash/STORAGE已实际通过后启动run_short_first_training_evaluation.sh：session57246、runnerPID3041791，同handle live；train.log实际step160+，约.15sec/update。输出lerobot/outputs/short_first_relative_chunk10_20260929/package_sorting_pi05_1gpu_20260929_114146。STARTUP_AUDIT核参数范围与baseline相同、prefix实际审计8380frames通过；WANDB关闭、只最终checkpoint。
- runner完成14480后核checkpoint/stats/validation，自动baseline/new各15个local320，再new60个legacy160；最终仍需实际画面复核，不自动目标完成。当前整体goalactive，未证明任务干扰改善，更广位置/外观泛化未完成。继续同57246，不重启训练；日志/tmp/short_first_model40_20260929_r1.log、RUN/train.log。

## 2026-09-29 11:38 freshpilot完整审核通过，转换进行中

- FINAL_AUDIT实际完整32/32、8/8组通过。最后70015两task的10标准帧已真正显示并记录，整批32条160标准帧review完整；最大倾斜仍70006袋 .156829rad。release_short_first_pilot实际正向通过，test70014/15排除转换。不是模型成功，也不是广泛摆放泛化。
- 实际转换session57004/PID2998547运行中（同handle验证live），log在pilot根conversion.log，命令CONVERSION_COMMAND.json。目标lerobot/lerobot_sim_short_first_pilot40_20260929，预期40ep/9800frames。新model RUN已创建仅STORAGE_PREFLIGHT/STATUS；无训练批准/新模型。转换完成后export audit、relative stats、prefix policy与DECISION再训练。SciPy1.15.3安装后converter help实际通过。

## 2026-09-29 11:34 用户要求释放空间：缓存清理完成

- 本次删除旧下载缓存 30.60 GiB / 4061 files，清后约 48.53 GiB 可用。完整清单与结果 demo/storage_cleanup_20260929_r2/manifest.json、REPORT.md。未删除实验数据或 checkpoint；19 个 last 目标存在，独立 keep_32clip_last 未证明可丢弃。基础模型/当前 baseline/先导32及其来源证据保留，§6 未变。
- 当前 freshpilot32 采集已结束；最后70015关键帧仍待实际查看，完整审计结果待读取；尚未转换/训练新模型。整体目标未完成。

## 2026-09-29T11:19:12.695831+08:00 当前：freshpilot24/32、6训练组/120标准帧通过；26条已采，准备70012图审

- 同93120持续live，日志已70000–12完成strict2/2，当前独立审计截至24条6完整train组。CPU84303 audit_partial和8798 review70011同handleexit0；77388 review70010也exit0，两layout各10标准帧真正显示，rawhash核、visual_review+GROUP_5_REVIEW保存。新增组max tilt.040347rad，未超过已有70006.156829风险；aggregate24ep120标准帧/4layouts pending，另9峰值。
- 新scripts/run_short_first_training_evaluation.sh已准备未正向执行：要求实际DECISION approved+export40/34train8380/6val1420+relative label report+sourceSHA+足够storage后才train，继而核14480step/参数范围/保存stats和chunk10，再baseline/new各15local320和newlegacy60×160评测，最后状态numeric_complete_actual_visual_review_required，不会自动宣称目标完成。基线用原relative10 env/dataset/stats，新模型用新env，避免拿新统计给旧模型。bash -n与baseline参数审计路径确认过；实际缺DECISION时拒绝且没创建RUN/训练output，TRAINING_RUNNER_PREPARATION留sourceSHA/负向证据；正向runtime未测。
- CPU新make_rollout_review 70012已启动（当前工具返回的session见后续；尚未显示/记录），70012虽采完但val完整组待70013。继续同93120，val/test全部复核后完整FINAL_AUDIT/aggregate→release→converter/label/export/storage审批→训练。未修改运行物理源码/参数，无新转换/训练，goalactive未完成。

## 2026-09-29T11:12:26.332159+08:00 当前：freshpilot20/32独立审计、5组/100标准帧通过；后台已采到70010

- 本turnprogress：同93120多次确认live。CPU2179独立部分audit同handleexit0：20ep/5completegroups全pass；CPU61303/97794生成70008/9图exit0，两layout共20标准帧实际显示，rawSHA核后visual_review+GROUP_4_REVIEW保存。aggregate20episodes100标准帧/6layouts pending、completefalse；另70006峰值9帧仍单列，不能说全视频审核。新增组max tilt.0055205rad（<.4度），没有超过已有70006峰值.156829风险。
- 最近日志已COLLECTED70010 strict2/2，即22条采集完成，但70010未生成/显示review，独立完整组数仍5。下一步继续70010/11图审及group5audit，不把采完当复核完；同93120后续val/test组也全部保留验收。
- 无源码/参数/原始数据修改，无新转换/训练。空间前turn清理记录和保守projection保留、训练前再查；外观单组合/窄位置fixedyaw/320帧限制继续明确。整体goalactive未完成，完成整批与数据管线后还必须训练并独立h10闭环评测。

## 2026-09-29T11:07:37.956619+08:00 当前：freshpilot16/32、4完整组通过/80标准帧+9倾斜峰值；空间预算已补足

- 本turnprogress；同93120始终live，最新继续70008。CPU3768独立部分审计exit0：16条/4组全原门/合同/phase/pair/supportupright通过。CPU88845/36814生成70006/7标准图exit0，两layout各2task5frames[0,79,159,239,319]真正显示/rawSHA核，visual_review+GROUP_3_REVIEW已存，aggregate16ep80标准帧/8layouts pending。
- **新风险**：70006 farbag max tilt.1568292442rad（约9度），显著高于先前首12条max.02043但仍<.20原门。独立找peak103，真实显示9frames[97,99,101,102,103,104,105,107,111]：左手附近袋短暂抬边/倾斜，随后107–111回平，没看见整体翻倒；box静止。Zpeak.779516（原约.77），firstsweep非160后recontact。无solved force trace不证力因果。review_70006_tilt_peak保存rawSHA/inventory/实际review，GROUP3附peakreviewSHA与风险，不称完全消除倾斜/广泛稳健，不因门内波动删组或松门。
- 磁盘保守完整剩余工作预算：当时7layouts已完，remainingpilot约.98GB、新checkpoint预算11.12GB（实际baseline9.67GB×1.15）、评测19200frames约4.086GB（30×320 baseline/newlocal+60×160newlegacy，25%余量）、dataset.157GB、reserve2.147GB，合计18.49GB，原free18.04GB不足约.45GB。STORAGE_PROJECTION有明细，没直接开训练。
- 经只读定位，W&B31GB对象无法证明是本项目副本，未删；完整HF模型和checkpoint未动。只清理/home/user/.cache/huggingface/xet/.../chunk-cache中预先列清单的218个旧于1天/nlink1/非symlink文件，共2,182,747,525bytes；核两处HF hub模型symlink无引用、/proc观察无openFD，删除前逐项inode/size/mtime再核。CACHE_EVICTION_PLAN保存完整列表和执行结果，auto审批实际通过。清后free20,126,101,504bytes，保守projection now sufficient；训练前仍重查。不要删任何模型/checkpoint/实验数据或把全部cache都wipe。
- 运行collector/runner/protocol未改；仍无新转换/训练，目标active未完成。继续同93120完成后续16轨迹及实际复核，门过全32再release/converter/export/relative stats/space检查/训练/h10；窄位置fixedyaw单贴图限制仍成立。

## 2026-09-29T10:58:15.932446+08:00 当前：freshpilot12/32、3完整组审计与60关键帧通过；转换准入脚本负向检查通过

- 本turnprogress：同session93120持续live，已采70000–05，继续70006。CPU67817独立audit_short_first_pilot部分审计exit0，12条/3完整组全pass，max tilt仍.0204338168rad。CPU53896/20700分别生成70004/5review并exit0，两layout各2task×5帧[0,79,159,239,319]实际显示、rawhash核、visual_review+GROUP_2_REVIEW已保存。aggregate最新12episodes60标准帧/10layouts pending，completefalse。函数cell2375曾观察延迟，最终正常完成图像显示；未因等待超时重启任务。
- 新scripts/release_short_first_pilot.py仅供全32真正完成后使用：先核RESULTcomplete/无ERROR、FINAL_AUDIT完整全组全任务通过、实际visual_review完整/来源SHA和rawSHA覆盖、每case正常STATUS/相同合同/原planned_split，然后才写case/review.json与CONVERSION_INPUTS（显式排除test、保留val；不自动训练）。语法过，实际对当前未完整pilot运行按预期拒绝且零review.json/零CONVERSION_INPUTS创建；RELEASE_INCOMPLETE_GUARD有scriptSHA和结果。完整正向release仍未运行。运行中的collector/runner/protocol模块未改。
- 当前磁盘约18GB，未转换/训练。外观单组合与窄几何的范围限制仍保留；本轮无新增物理失败。继续同93120后续组审核，全32过后完整audit/aggregate→release→排test转换→export+relative统计+空间检查→训练/独立h10；整体goalactive未完成。

## 2026-09-29T10:52:35.355617+08:00 当前：freshpilot8/32、2完整组独立审计/40关键帧通过；确认外观覆盖仅1组合

- 本turn属于progress：同93120多次验证live并完成新增70002/70003审核。CPU57170 audit_short_first_pilot.py --allow-partial同handleexit0：8episodes/2completegroups全pass；CPU64691/55129 review生成均exit0，两layout各2task×5frames[0,79,159,239,319]实际显示，rawSHA核对、visual_review和GROUP_1_REVIEW写盘。aggregatepilot最新8episodes40standardframes、12layouts pending、completefalse；首8条max tilt.0204338168rad。93120最后仍live，继续70004，未改运行collector/runner/protocol模块，未转换/训练。
- 追查fresh盒表面白标与诊断差异：共同provenance物理源码SHA无变化；reset_sorting_parcels在reset末调用_randomize_parcel_photos，rng由layout.seed决定，给定XYZ后rng未用于位置。choose_parcel_albedos可从4box/5bag图池选材。诊断seed2026092931→box_iter_0/mail_iter_1；fresh全32seed2026092937→box_iter_4/mail_iter_1，符合实际已看RGB。APPEARANCE_COVERAGE_AUDIT保存期望贴图路径/SHA/源码SHA/限制；这是代码+种子推导，不是USD绑定转储。不是渲染bug证据，但发现当前fresh全部共享1贴图组合，不能宣称外观泛化。
- 不修改已冻结/运行批次、不以此松门/丢组。当前仍用于局部类别位置交换/任务干扰实验，整体用户要求的更广摆放泛化仍未完成；后续扩展应按geometry组设置不同外观seed，并保持组内2assign×2prompt同seed，避免视觉任务混淆。不要把当前窄位置fixedyaw/单贴图当最终目标或无限停留此范围。
- 接续同93120监控，后续组独立audit+实际图审，完成full32再转换训练h10评测。下文已有准备scripts/env、验证IDs和空间预算说明。整体goalactive未完成。

## 2026-09-29T10:46:08.637003+08:00 当前：freshpilot首完整交换组4/4独立审计+20帧图审通过，93120继续70002

- demo/short_first_pilot32_20260929_r1后台实际runner session93120/PID2635590本轮同handlelive；log已COLLECTED70000/70001 strict2/2各，继续70002。CPU80515 audit_short_first_pilot.py --allow-partial实际exit0：4episodes/1completegroup全部合同/来源/首q/action0/waist0/.055/nearhold/far160recontact/原门/pair/fullpose支撑和倾斜通过。全首组max tilt.0204338168rad，GROUP_0_REVIEW有4hash和2reviewSHA；不是全32准入。
- CPU84946首farbag正向audit和34005首pairreview生成均exit0；review_layout_70000两task各5帧[0,79,159,239,319]本轮真正显示并独立audit_pair。CPU98183第二pairreview生成exit0；review_layout_70001同样两task5帧实际显示，近袋左/远盒右两段，各非目标静止；盒末部分图边由全pose核支撑。盒标签外观与诊断不同、pair内一致，记录观察不推断原因。aggregatepilot最新4episodes20standardframes/14layouts pending，completefalse，无全视频审查声明。
- 首nearbox的FIRST_EPISODE_AUDIT_AND_GUARDS及首farbag FIRST_FAR_EPISODE_AUDIT保留真实正向结果，之前两项内存负向和3项合同负向均过。代码没有在运行期修改；尚未生成训练用review.json/转换数据/新模型。整批诊断32/32/8组已通过的完整证据见short_first_sweep_rtx_r1，勿与当前pilot4/32混计。
- 接续：同93120继续采，完整组齐即AUDIT_PARTIAL，逐layout make_rollout_review然后实际显示再写visual_review；全32真过才FINAL_AUDIT/完整aggregate及训练准入。训练/转换/评测准备脚本与限制见下文。整体goalactive未完成，不以首组成功/后台启动作为终点。

## 2026-09-29T10:41:02.078504+08:00 续作：freshpilot实际首条数值/合同审计通过，持续采集session93120

- 当前真实runner为session93120/PID2635590（前台exec nohup被工具跟踪），首collector70000进程2635905。最初后台shell PID2626572无case/无日志即消失，已证明无轨迹产生后重启；不是失败轨迹重试，LAUNCH_RETRY_RECORD有记录，runner.pid更新。工具同handle93120live，log /tmp/short_first_pilot32_20260929_r1.log。
- 新fresh70000 push_box_to_bin实际320帧已经写盘。CPU19277同handleexit0：用新audit_pilot_episode真正正向检查合同/source/phase/原门/support/upright通过，box max tilt.00308026rad、最小支撑余量.04395m，planned_split=train。FIRST_EPISODE_AUDIT_AND_GUARDS记录rawSHA/fullfitness；两项仅内存修改负向测试（首q非零、near后160hold中改.001rad）均拒绝，原数据未改。尚未显示此freshpilot图片，不能说已画面复核。70000袋正执行，最近step240，pair/全组尚未结束。
- CPU2949正向prepare_short_first_evaluation已exit0：demo/short_first_test_protocol_20260929_r1/heldout_protocol.json冻结fresh test70014/15、wait73000、3seeds、320frames/h10/cap0/solver10，模型尚未评测。实际合同额外3负向测试（重复group成员、非法split、换endpoint）均拒，CONTRACT_GUARD_CHECKS记录；运行collector及模块未修改。
- 下一步：同93120继续，首pair完成后生成/实际显示review_layout_70000；首完整组70000/1齐后audit_short_first_pilot.py --allow-partial。新批32全部原/strict/pair+实际review真过才给case写review.json、converter --source 70000–13的14个case加已审waits，验证IDs70012,70013,63010,63011；test70014/15四条不入训练。新数据预计40ep/9800frames、train34/8380,val6/1420。prefix_sampling_policy新文件尚未生成，relative统计新dataset仍待转换后实际验证。整体goal仍active，没新模型，未完成目标。

## 2026-09-29T10:36:58.392070+08:00 阶段切换：.28诊断完整32/32、8/8通过；freshpilot32实际运行session93120/PID2635590

- short_first_sweep_rtx_20260929_r1原runnerPID2303668已退出，RESULTcomplete16layouts/32tasks、16returncode全0、无ERROR。CPU49477 FINAL_AUDIT同handleexit0：32strictpass/8completegroups。review_layout_69002–13本轮逐个实际显示各10帧并rawSHA核过；全32×5=160标准帧全部实际看完，另原失败69015peak9帧保留。visual_review.json aggregatecomplete/reviewedtrue，8组GROUP_REVIEW全有。DECISION只准freshpilot，诊断不可训练。
- RGB_COMPARISON_FINAL保存完整32同case旧新hash/tilt对照；new最坏.112025402rad（旧.264844401），原失败test组保留pass；69000bag等局部tilt较旧升高，不能说所有更稳。仅fixedyaw窄位置分布，320帧约21秒，不代表广泛泛化/新模型已提高。
- prepare_short_first_pilot实际正向成功（57324exit0），新demo/short_first_pilot32_20260929_r1生成ID70000–15/seed2026092937，8freshgeometry组预分6train/1val/1test，完整合同通过真实evidence validator，未重标诊断数据。初次shell后台PID2626572未持续、零日志/零case已核；LAUNCH_RETRY_RECORD保留。改tracked前台exec nohup启动run_short_first_pilot_batch，session93120/PID2635590（实际ps确认），runner.pid已更新、log /tmp/short_first_pilot32_20260929_r1.log，SOURCE_AT_LAUNCH冻结collector/runner/protocol模块hash，collector_source.py拷贝；尚待首实际episode和独立audit确认。运行期间不要修改这些模块/collector/runner。
- CPU2949实际exit0完成prepare_short_first_evaluation，输入上述freshpilot，输出demo/short_first_test_protocol_20260929_r1（heldout_protocol已冻结，尚未执行模型评测）。新runner run_pi05_short_first_sim.sh只接受2testlayouts/3seeds/320帧/h10/cap0/solver10；baseline与新model同预算比，原160帧benchmark单列。脚本语法过，尚未真实推理。
- 新训练准备：scripts/pi05_short_first_relative_chunk10_20260929.env（未运行）保持原pi05_base初始化、14480steps/batch1/seed42/expert_only/noLoRA/lr2.5e-5/prefix3weight16/chunk10relative；WANDB_ENABLE=false避免重复artifact。预期训练/验证push28+旧已审wait12=40ep（34train8380帧/6val1420帧），test70014/15四条绝不入converter，wait验证63010/11保持原划分。TRAINING_AND_EVALUATION_PREPARATION说明未放行。
- prepare_relative_action_stats.py新增成对--dataset-root/--repo-id支持新数据，用原relative10checkpoint仅读配置；实际在旧coverage80回归9080训练帧，state/action统计与冻结旧结果完全一致，roundtrip5.96e-8、validation未query。RELATIVE_STATS_REGRESSION存证；新数据尚未测。audit_paired_lerobot加强export后geometrygroup/planned_split检查。CONVERSION_PREPARATION更新源码SHA。相关unittest之前10+7过；新pilot正向审计/转换仍未完成。
- 当前磁盘约18GB，GPU训练未启动，baselinecheckpoint保留model7G+state2.1G。整体goalactive未完成。继续监控新PID，完整组即独立audit_short_first_pilot.py+实际review；质量fail停扩采保留全组。全pilot真过再review放行/转换/labelstats/空间检查/训练/h10闭环，不能停在启动任务。

## 2026-09-29T10:16:45.610573+08:00 续作：新RGB16条独立审计全过，18条90标准帧已看；新pilot转换检查已接入但尚未正向运行

- 原33532session句柄在恢复上下文后不可用，但ps确认PID2303668继续运行同一run_twopass_render_groups.py；未重启。日志已完成69014/15及69000–07（20条），69007标准review生成CPU20254尚待显示/记录。独立AUDIT_PARTIAL目前16条4完整组全pass；review_layout_69002–06本轮各两task5帧实际显示并rawSHA核对，aggregate最新18episodes90标准帧、7layouts pending，另原case峰值9帧。后续继续实际图审，不复用旧batch结果。
- 新simfoundry/data/short_first_pilot_audit.py独立检查实际pilot合同/collector来源/精确参数/首q和action0/waist0/.055/near后160hold或far160measuredanchor/全pose支撑及tilt。新增scripts/audit_short_first_pilot.py供真正新pilot完成后用；尚未正向runtime验证。converter新增专用branch，不绕原spatial，拒test并核planned_split，旧分组完整性仍检查。twopass_protocol加强合同groups和layouts精确对应/合法split；当前GPU诊断不import这些模块，collector/runner未改。
- 相关unittest paired10+legacyspatial7通过；实际旧spatial_candidate_pool72_20260928_r1/waits的12条checked_sources重审通过。新pilot尚未采、无新训练。aggregate兼容新pilot group.layout_ids（原diagnostic group.layouts仍原路径）。CONVERSION_PREPARATION存源码SHA和验证边界；freshpilot真实正向测试仍待后续。
- 磁盘约19GB可用；保留baselinecheckpoint约9.1GB（model7+state2.1）。新训练需要先核额外dataset/checkpoint临时空间，禁W&B重复artifact。整体目标仍active未完成；继续全32诊断复核→真正freshpilot→转换/训练/h10闭环，不把小范围专家成功当泛化。

## 2026-09-29T10:01:05.648667+08:00 当前：.28新RGB8/32、2完整组通过、40标准帧+9峰值；pilot批采脚本准备未执行

- 33532同handlelive，69001task/pair完成pass，继续69002。CPU50237 AUDIT_PARTIAL和50986 review生成均exit0；新batch8ep/2组全strictpass。69001标准两task×5frames[0,79,159,239,319]实际显示，近袋左推远盒静止、远盒两段右推近袋静止；末盒部分图边由全pose支撑核。review_layout_69001/visual_review+GROUP_0_REVIEW已绑定rawhash/auditfitness/reviewSHA。
- aggregate新root最新8episodes40标准distinct帧、12layouts pending、completefalse；额外9peak独立保存，旧batch160帧不混计。新已过groups7test和0train，不是原序前两个。
- 新scripts/run_short_first_pilot_batch.py已语法检查、未运行，PILOT_BATCH_PREPARATION记录SHA/runtimefalse。读取真正prepare脚本产生的PROTOCOL+合同，核exactcollector/contractSHA并validate前才启动；每layout新subprocessrolepilot+320+exactparams，禁止覆盖/静默重试；每条quality/frames+trace/orientation全程supportupright即时检查并保存rawSHA；完成整组两assignment后若任何原/pair/strict失败就保留4条记录并停止扩采。运行异常写ERROR，无automatictrainingrelease。无真实合同/新pilot数据，正向runtime仍待全证据。
- 运行中的诊断collector/runner未修改，整体goalactive未完成；继续33532后续组审核，全部真过后再prepare_short_first_pilot及新批采/独立复核/转换训练。

## 2026-09-29T09:57:59.761168+08:00 当前：.28新RGB6/32、30标准帧+9峰值帧；首前后normal也通过

- 33532本turn同handlelive；新root short_first_sweep_rtx_r1已69014/15/69000共6ep原task/pairpass，继续69001。CPU94654生成新review_layout_69000后同handleexit0，两task各5frames[0,79,159,239,319]实际显示；far袋两段左推/平面yaw且盒静止，near盒右推/袋静止，末盒部分图边。独立原audit/pair、fullpose支撑/upright、assist0和meta.first_far_exit_y=.28、rawhash核过。
- 新69000bag max tilt.0551786rad、box任务max.00396391rad，均strictpass；review_layout_69000/visual_review存rows/fitness/pair/hash，aggregate新root最新6episodes30标准distinct帧/13layouts pending、completefalse。另原失败case峰值9帧已实际看，不能混用旧batch160帧。完整组新root仍1（优先test组）。
- 未修改源码/合同/原数据，未新pilot/转换/训练。整体goalactive未完成；继续同33532，69001齐补完整group0 independentaudit及review，再其余组。保持所有预划分用途。

## 2026-09-29T09:55:35.929676+08:00 当前：.28原失败test完整组4/4通过、标准20+峰值9帧已看；freshpilot准备脚本未获准运行

- 33532本turn同handlelive，69014/15任务与pair均完成pass，后续组继续。CPU52126 AUDIT_PARTIAL与84484 review生成均同handleexit0：新batch4ep/1完整test组全strictpass。69015两task标准5frames[0,79,159,239,319]实际显示；near袋左推远盒稳定、far盒两段右推near袋稳定，尾盒部分图边。峰值.112rad前turn另9帧已复核，未淡化敏感性。
- review_layout_69015/visual_review及GROUP_7_REVIEW绑定4rawhash/两reviewSHA，旧失败testsplit不变。aggregate新root4episodes20标准distinct帧、14layouts pending、completefalse，另9peak帧不重复计。
- 新scripts/prepare_short_first_pilot.py已编译：要求evidence RESULTcomplete+FINAL_AUDIT全组strict+visual_review完整、参数.28，再采8新groups16layouts/32task（默认ID70000–15 seed2026092937），canonical nearX.369635±.003/farX.518499±.003、commonY±.012、2frontbackdy±.005、3pos/3negdy10–25mm、固定canonicalyaw；与原diagnostic及先前新slot的maxcoordinate差至少1mm，原inputvalidator过，整体6train/1validation/1test预分。将exactEXPERT、pilotcollectorSHA、全部证据SHA绑定合同，在临时文件调用实际validator成功后才发布输出；只准备不采集、test不得训练。
- 实际用当前未完新RGB root调用prepare脚本，按预期ValueError“Feasibility batch is incomplete; no pilot artifacts created”，/tmp/short_first_pilot_must_not_exist_20260929确认不存在；PILOT_PREPARATION_GUARD保存scriptSHA/负向结果。没有approved真实合同、没有新pilot数据。正向准备/运行/转换/训练仍待完整证据，不将代码准备当目标完成。
- goalactive未完成，继续同33532后续组独立audit和实际review；不得用旧.30pilot入口或旧失败批次证据批准新.28合同。

## 2026-09-29T09:51:39.169908+08:00 当前：.28新RGB原失败case已strict通过但仍敏感；首2标准轨迹10帧+峰值9帧实际复核；新版pilot草稿隔离完成

- 33532本turn多次同handlelive；69014两task/pair完成，CPU85072 review生成exit0且实际显示2×5frames[0,79,159,239,319]，新batch首10标准帧已看。独立原audit/pair/supportupright/assist0/meta.first_far_exit_y=.28/rawSHA核过，review_layout_69014/visual_review保存。aggregate newroot最新2ep10标准帧/15layouts pending，非旧batch数字。
- 原失败69015 push_box_to_bin新RGB320已保存并原quality+support/upright通过，max tilt.112025402rad（旧RGB.264844、新noRGB.005408，仍存在敏感性），firstpeak115。PRIOR_FAILURE_CASE_CHECK.json保存scope为wholegrouppending，不能当全组通过。
- CPU49954生成新review_69015_tilt_peak并exit0，9frames[109,112,113,114,115,116,117,119,123]实际3段读取显示，小幅第一推末段抬起后119–123回平；visual_review绑定rawSHA，未称完全消除倾斜或全局稳健。这9额外帧与标准2ep10帧分开计数，69015标准5帧和配套bag仍需后续完整组审核。
- 新模块short_first_twopass_protocol.py定义独立kind cartesian_twopass_short_first_v1，deepcopy旧EXPERT再first.far_exit_y=.28；旧twopass_protocol重构私有_validate(...expected_expert)，旧public仍严格旧EXPERT（.30）。共同validator新增证据PROTOCOL.first_far_exit_y必须匹配expected，且collector_source.pySHA必须匹配protocol。运行诊断不import这些新模块，未改运行collector/runner。
- 新scripts/collect_short_first_twopass_pilot.py由未运行旧pilot副本构建，仅firstfar.28+meta.first_far_exit_y+.28新版合同import，provenance含两个模块；collect控制/reset段逐字等于short-first diagnostic并语法通过，PILOT_PREPARATION保存SHA/controlidentity/runtimefalse/contractfalse。新旧pilot入口均没有正向采集。
- CONTRACT_VERSION_GUARDS实际3项负向过：旧接口拒新参数、新拒旧参数、新参数拒实际旧.30完整RGB证据。临时合同删除，未生成approved真实合同。旧guard报告SHA对应早期版本，不应误称现版本已全端到端验证。后续全部新RGB真过再正向合同测试、采freshpilot、接converter；goalactive未完成。

## 2026-09-29T09:45:34.873900+08:00 当前：firstfar.28筛查32/32、8/8；最大tilt.059，新RGB全批33532启动且失败test优先

- 68172本turn同handle明确exit0，RESULTcomplete36无ERROR。short_first_sweep_screen_r1 GROUP_AND_INPUT_AUDIT：4canonical+32fresh全原门/支撑/直立通过、8完整valid组；TILT_PHASE_COMPARISON_FINAL逐36case旧/新分first160和second160，SHA/首q/action0/waist0/.055实际核过。全new max tilt.0591304rad；原69015farbox screen旧.149999→新.0054084（第二段.00220984），不是RGB验证结果。DECISION screen_passed_pending_rgb，trainingfalse。
- 新FIRST_PHASE_REPRO_DIFFERENCE.json保存在旧fixed_yaw_local_rtx_r1：旧69015screen与RGBfirstphase切换cross2/press41/sweep56/hold114一致（lift0/1仅记录差异）；初始XYZ差22–24微米，action差>1e-4首次85，first160 maxactiondiff.001429rad/maxqdiff.004124，110时boxXYZ差6.15mm。独立动态专家，不是frozen action；支持敏感性判断，不证明渲染引擎造成力变化。
- prepare_twopass_render.py已改为读取screen/RENDERER_PREPARATION.json并核限定scripts路径+SHA绑定新collector；若first_far_exit_y非.30但无绑定renderer拒绝。renderPROTOCOL记录first_far_exit_y。audit_twopass_render.py新增核meta.first_far_exit_y==protocol（旧缺省.30），其他不变；两个脚本语法通过，旧运行collector/runner未改。
- 实际准备short_first_sweep_rtx_20260929_r1成功，PROTOCOL正确指向collect_short_first_twopass_diagnostic.py/.28及SHA，全8组32条保留。只重排执行先test组69014/15，然后其他原序；split不变，每layout独立新Simulator subprocess。新主33532刚启动，log /tmp/short_first_sweep_rtx_20260929_r1.log，旧68172已terminal，不并行GPU。下一步同33532确认、test完整组优先独立audit/实际keyframes及峰值；全批逐组审核，不能凭数值过就准入。
- 旧batchstrict31/32、7/8失败证据保留未改；旧v1pilot合同/collector草稿firstfar仍.30，不适用于新.28方案，不能直接运行。若新RGB通过需相应精确新版合同/新pilot入口参数再正向验证和fresh采集。尚无新训练，goalactive未完成。

## 2026-09-29T09:40:53.646985+08:00 当前：缩短firstfar到.28筛查运行，基准4过；部分倾斜幅度升高，暂不能判更稳健

- 68172本turn两次同handlelive，short_first_sweep_screen_r1已4canonical全pass，并新10/10条strictpass、2完整组（GROUP_AUDIT_PARTIAL completefalse）。保留全32同布局/同split，不剔除原失败test69015。最后全部结果/ERROR仍待确认。
- 已逐case对比早期倾斜：69000 farbag原screen max.01746→新.05913rad，69001 farbox .00412→.05083rad，仍<.20但增大；已向用户说明不能把当前通过当更稳健。新方案仍须全部group及原RGB失败组复现，不绕门。
- 准备新scripts/collect_short_first_twopass_diagnostic.py（未运行）：隔离复制原320诊断collector，仅初始far targetX>=.48 exit.28，其余near及第二段.30；增加exact默认exit.30guard和collect_meta.first_far_exit_y=.28。所有原诊断/zero/waist/noassist/原质量门保持，旧运行源码未动。RENDERER_PREPARATION.json记录原/新collector SHA、未执行/未准入。后续若screencomplete，需要新render PROTOCOL指向此collector及SHA（不能直接沿用prepare_twopass_render.py默认旧collector而漏改参数）；独立audit原脚本仍可检查所有共同硬门和原/paired/pose，需同时核新metadata/源码。
- 全批旧RGB明确strict31/32、7/8，不是训练准入；全160+峰值9帧审核已完成，失败test仍保留。v1pilot合同/collector草稿未获准正向采集，未转换训练。goalactive未完成，下一步继续同68172。

## 2026-09-29T09:38:01.734521+08:00 当前重要坏结果：整批RGB原门32/32，但严格31/32、7/8组；test远盒短暂抬起，新单变量对照启动

- 86883本turn同handle明确exit0，RESULTcomplete32。CPU43309 FINAL_AUDIT strict实际32条但7/8组；不是全通过！69015 push_box_to_bin original quality/pair通过，supporttrue，但box max tilt.264844401rad>.20，末test组wholegroup拒绝。screen同case max tilt约.149999rad，RGB复现对细微物理差异敏感。已明确向用户highlight坏结果，未批准新pilot/未训练。
- CPU74244生成最后69015标准5frames/task，实际显示，两任务标准抽帧未见峰值；独立全pose检出110/111超阈，peak111 firstsweep mode_step56，boxZ.78295，随后112tilt.06385、115约.00098。失败不是第二次接触造成。CPU65192生成9frames[100,104,107,109,110,111,112,115,120]峰值图并实际3段读取显示，review_69015_tilt_peak/visual_review绑定rawSHA/范围；手附近盒短暂倾斜，未声称已证接触力因果。
- review_layout_69015/visual_review完成但明确strictfailure；GROUP_7_REVIEW numeric_and_pair_passedfalse，split保持test，未剔除失败改分母。aggregate完整visual_review.json实际32episodes160标准distinct帧全部reviewedtrue（含失败），另9峰值帧；FINAL_AUDIT complete与rawhash全绑定。DECISION full_batch_not_approved_transient_tilt:original32/strict31/groups7of8，trainingfalse。prepared v1twopass合同/collector仍不批准，validator会拒全批失败组；不得通过选择仅7成功组绕过test失败。
- 新short_first_sweep_screen_20260929_r1：与fixed_yaw_local screen完全同32布局+4canonical/同预划分，唯一变化first FAR exit_y .30→.28（firstnear仍.30，第二次仍.30，所有height/bias/offset/zero/waist/.055/noassist及原门+supportupright保持）。目的缩短第一次推动末段，避免边缘抬起；不是松门或改物体。PROTOCOL/GEOMETRY_PREFLIGHT/source.py/SOURCE冻结，新scripts/run_short_first_sweep_screen.py未改旧文件。刚启动新GPU task68172，日志/tmp/short_first_sweep_screen_20260929_r1.log。先canonical若fail自动停止，若complete则groupaudit并与原screen逐case tilt/progress比较，再原RGB验证（尤其保留test失败组），不能凭无RGB通过批准。
- 新pilot入口负向测试已过但正向未运行、没有新训练数据；整体goalactive未完成。下一步同新handle轮询，不重启，检查ERROR（Isaacclose可能maskexit）。

## 2026-09-29T09:32:35.184710+08:00 当前：RGB30/32、实际150帧；新批次固定时机标签风险已量化

- 86883同handlelive，69014两task/pair完成pass，最后69015运行。CPU35809生成review_layout_69014后同handleexit0，两task图片实际显示，各5frames[0,79,159,239,319]。远袋两段左推/平面yaw，盒静止；近盒右推/袋静止，末盒靠右图边。原audit+pair+全pose supportupright/assist0/rawSHA独立核，visual_review已存。aggregate最新30episodes150distinct帧，1layout pending，completefalse；完整组仍7。
- 新RECONTACT_LABEL_TIMING_DIAGNOSIS.json分析实际本批69000farbag/69001farbox/69012farbag/69013farbox，均rawSHA绑定，比较t120/140/150/155/159对160的11q maxdiff、RGBMAE、next10 state-relative actiondiff。150对160 qdiff0.0292–0.0334rad，RGB0.50–0.67/255，动作差约.265rad；159对160 qdiff.0029–.0033、动作差.0324–.0329。与旧诊断一致：不能说观察完全相同或已证明标签冲突/模型失败；固定160二次接触可能学习时机困难，仅记录为后续模型闭环关注点，不改动作标签/原数据。
- 最后69015完成后确认86883terminal，严格FINAL_AUDIT、实际最后图、GROUP_7_REVIEW、aggregate完整visual_review；然后才生成批准新pilot合同和正向测试。未新pilot/转换/训练，goalactive未完成。

## 2026-09-29T09:29:18.862211+08:00 当前：RGB28/32、7组含val通过，实际140关键帧；最后test组运行

- 86883同handle持续live及两次30s verifiedwait，69013task/pair完成pass，runner继续69014/15最后test。CPU7804 AUDIT_PARTIAL和40222 review生成均同handleexit0；独立28episodes/7组全numeric_and_pair_passedtrue，completefalse。
- 69013两task图片实际显示，各5frames[0,79,159,239,319]。近袋左推后停稳、远盒静止；远盒两段右推/近袋静止，最终盒部分图边，全pose supportupright已独立核。review_layout_69013/visual_review绑定rawhash并核auditfitness，GROUP_6_REVIEW保存val用途、4hash和两个reviewSHA。aggregate最新28episodes140distinct帧/2layouts pending、completefalse。
- 未改源码/原数据或批准合同，未新pilot/转换/训练。继续同86883，最后32齐需要严格FINAL_AUDIT、最后实际图review、aggregate顶层visual_review完整与全hash绑定，然后才正向合同/freshpilot阶段。goalactive未完成。

## 2026-09-29T09:25:39.002951+08:00 当前：RGB26/32、实际130关键帧，val组normal完成

- 86883本turn同handlelive，69012两task/pair已pass，runner继续69013。CPU34406生成review_layout_69012后同handleexit0，两task图实际显示，各5frames[0,79,159,239,319]。远袋两段左推/平面yaw、盒静止；近盒右推末段部分图外、袋静止。原audit/pair、全pose supportupright、assist0、rawSHA独立核过，visual_review保存rows/fitness/pair及范围。
- aggregate最新26episodes130distinct帧、3layouts pending、completefalse；完整审核仍6组，预划分val组仅normal完成、不得重分train。没有源码修改或新GPU任务、新pilot/转换/训练。继续同86883，69013齐后第7组审核，剩test69014/15；整体goalactive未完成。

## 2026-09-29T09:23:43.231119+08:00 当前：RGB24/32、6组通过、实际120帧；pilot CLI拒绝检查通过

- 86883同handlelive/30s verifiedwait，69011两task/pair完成pass；CPU42596 AUDIT_PARTIAL和56632 review生成均同handleexit0。独立24episodes/6组全numeric_and_pair_passedtrue，全批completefalse。69011图实际显示两task各5frames[0,79,159,239,319]，近袋左推/远盒静止，远盒两段右推/近袋静止；最终盒部分图边，支撑由全pose audit核。review_layout_69011/visual_review、GROUP_5_REVIEW绑定rawhash/auditfitness及reviewSHA。aggregate最新24episodes120distinct帧/4layouts pending。
- 实际负向运行新collect_twopass_pilot.py CLI：第一尝试漏OMNI_KIT_ACCEPT_EULA，import阶段EULA EOF未触及合同，PILOT_PRELAUNCH_REJECTION.json passedfalse保留，不能当准入测试成功；第二次显式使用既有OMNI_KIT_ACCEPT_EULA=yes，实际到validate_twopass_contract并以“Two-pass pilot has not passed feasibility review”ValueError exit1，输出目录未创建，PILOT_PRELAUNCH_REJECTION_R2.json passedtrue。临时unapproved合同自动删除，未创建Simulator实例/新数据。正向pilot运行仍未测试。
- 最后预划分val/test两组69012–15继续86883，保持wholegroup。新contract/module/collector草稿均未上线转换，未生成批准合同、未新pilot/训练。整体goalactive未完成。

## 2026-09-29T09:20:07.700644+08:00 当前：RGB22/32、实际110关键帧，后台继续

- 本turn86883同handlelive及30s verifiedwait，69010两task/pair完成pass，runner顺序69011。CPU10948生成review_layout_69010后同handleexit0，两task图实际展示。袋两段左推且平面转动、盒稳定；盒右推、袋稳定，盒末段靠右图边。各5frames[0,79,159,239,319]新增10。
- 独立原audit_rollout/audit_pair、全pose support/upright、assist0、rawSHA均实际核过；review_layout_69010/visual_review存rows/fitness/pair/hash。aggregate最新22episodes110distinctframes、5layouts pending、completefalse。第6组仅normal完成，完整组仍5。
- 未改运行collector/runner或pilot草稿；没有新pilot数据/转换/训练。整体goalactive未完成。下一步69011齐则独立AUDIT_PARTIAL第6组+实际图片审核，继续同handle86883，不重复启动。

## 2026-09-29T09:16:58.739057+08:00 当前：RGB20/32、5完整组审核通过、100帧；新pilot入口准备但未运行

- 本turn86883同handlelive，69009两task/pair完成pass；CPU66968独立AUDIT_PARTIAL已exit0：20episodes/5组numeric_and_pair_passed全true。CPU52894生成69009 review后exit0，page_0实际显示两task5frames[0,79,159,239,319]。近袋左推/远盒稳定、远盒两段右推/近袋稳定，末盒部分图边由全pose审核支撑；rawSHA与auditfitness核。review_layout_69009/visual_review和GROUP_4_REVIEW已保存，aggregate最新20episodes100distinctframes、6layouts pending、completefalse。
- 新scripts/collect_twopass_pilot.py隔离副本（未运行、未接converter）：由当前diagnostic源复制；强制required --twopass-pilot-contract、rolepilot、1layout/320/no waits/policy/forces；禁止旧spatial/recovery/explicitjson/偏移及所有未登记专家features；要求newton/shortprompt/endpoint.30和原firstparams。AppLauncher前validate_twopass_contract取explicit_layout及hash；新数据collect_meta记录twopass_contract_sha256+完整EXPERT，输出复制合同，provenance增加moduleSHA。旧两处诊断参数限制仅为已验证twopasscontract新入口扩展；其余prototype未改。
- PILOT_COLLECTOR_PREPARATION.json保存两scriptSHA/语法/collect物理控制段逐字一致验证，runtime_testedfalse/contract_approvedfalse/trainingfalse。运行中的诊断collector和runner未编辑。后续必须全证据齐后正向合同与pilot运行核，不得把准备就绪说成已采集，converter仍拒新专家直到专门接入核验。
- 后台仍86883顺序继续69010起，整体goalactive未完成，无新pilot数据/转换/训练。

## 2026-09-29T09:13:42.933226+08:00 当前：RGB18/32、实际90关键帧，后台继续交换布局

- 86883本turn同handlelive及30s verifiedwait；69008两task/pair完成pass，runner继续69009。CPU78592生成review_layout_69008后同handleexit0，两task图片实际显示。远袋两段左推/平面转动、盒稳定；近盒右推袋稳定，最终盒部分超出图边，fullpose支撑另核。
- 独立原audit_rollout/audit_pair、全pose support/upright、assist0/rawSHA核过；review_layout_69008/visual_review.json含rows/fitness/pair/实际5frameIDs[0,79,159,239,319]。aggregate最新18episodes90distinct帧、7layouts pending、completefalse。第5组只有normal，完整审核仍4组。
- 没有修改运行源码、没有新pilot/转换/训练，goalactive未完成。继续同handle86883，69009结束后补第5完整组AUDIT_PARTIAL+画面；全批完成再FINAL_AUDIT和全覆盖review。

## 2026-09-29T09:11:12.810968+08:00 当前：RGB16/32、4/4已完成组审核通过、实际80关键帧

- 本turn86883同handlelive及两次30s verifiedwait后，69007完成task/pairpass，runner顺序继续69008。CPU60366独立AUDIT_PARTIAL已同handleexit0：16episodes/4组均numeric_and_pair_passedtrue，全批completefalse。
- CPU64344生成review_layout_69007后同handleexit0；page_0.b64实际显示：近袋左推后保持、远盒不动；远盒两次右推近袋不动，最后盒部分图边，fullpose支撑独立audit负责。两条各5frames[0,79,159,239,319]新增10，review SHA与audit fitness核，GROUP_3_REVIEW绑定69006/7四rawhash及两个reviewSHA。
- aggregate最新REVIEW_COVERAGE_PARTIAL 16episodes80distinct关键帧、8layouts待审核，completefalse。前2frontback+positive/negative各1轻微斜放完整组完成；仅局部位置/固定yaw，不宣称广泛泛化。全批剩16条原RGB仍在后台86883运行。未改采集器或合同草稿、未新pilot/转换/训练；goalactive未完成。

## 2026-09-29T09:07:43.151506+08:00 当前：RGB14/32、70关键帧，另一方向斜放normal通过，后台继续

- 上一goal turn为progress；本turn86883同handle两次live含30s verifiedwait，69006完成两task/pairpass，最新runnerCOMPLETE69000–06共14ep，69007配套交换继续。无重启/无新增GPU任务。
- CPU56737生成review_layout_69006后同handleexit0，实际两段读取并显示两task图；每条5frames[0,79,159,239,319]新增10。Far袋两段左推带平面内转动、盒稳定；near盒右推、袋稳定。注意此条最终盒在画面内较完整可见，不要沿用前几条“部分超出图边”的观察。全pose支撑/upright、原audit_rollout/audit_pair、assist0/rawSHA已独立实际核过；visual_review保存rows/fitness/pair和范围。
- aggregate最新14episodes70distinctframes、9layouts待审核、completefalse；仍3完整组批准review，第4组只有normal完成。当前可用空间21GiB，未删文件。继续同86883，待69007齐做AUDIT_PARTIAL第4组及review。整体goalactive未完成，未新pilot/转换/训练。

## 2026-09-29T09:05:07.295356+08:00 当前：RGB12/32、首斜放完整组通过，实际审核60关键帧

- 本turn为progress：86883同handlelive，69005完成两task/pairpass；CPU5027独立AUDIT_PARTIAL完成12episodes/3完整组全部numeric_and_pair_passedtrue，completefalse。runner继续69006以后；不重启。
- CPU77303生成69005 review后同handleexit0，page_0.b64实际显示，近袋左推远盒稳定，远盒两段右推近袋稳定；最后盒部分图边，全pose支撑由独立audit核。review_layout_69005/visual_review.json绑定5准确frameIDs/rawSHA并比对AUDIT_PARTIAL fitness；GROUP_2_REVIEW绑定69004/5四hash及两个reviewSHA。
- aggregate_twopass_reviews实际最新REVIEW_COVERAGE_PARTIAL为12episodes60distinct帧/10layouts待审核，completefalse。已通过前2frontback完整组+首positive轻微斜放组；依然是局部位置/固定yaw，不是宽泛自然布局或VLA泛化结论。
- 本turn只读取现有collector参数，未改运行collector/runner或twopass_protocol草稿。prototype强制role diagnostic/320/no waits/policy/forces，后续freshpilot必须用新明确合同入口，不能把现有文件换role。未采新pilot、未转换/训练。整体goalactive未完成。

## 2026-09-29T09:02:33.622355+08:00 当前：RGB10/32、50关键帧；两阶段合同校验草稿与拒绝检查已准备

- 86883同handle仍live，最新runnerCOMPLETE69000–04，10episodesquality/pair都pass，仍只有前2完整组审核。新69004为轻微positive diagonal的normal assignment，交换69005仍在跑。
- CPU70078生成review_layout_69004后同handleexit0，实际显示两task5frames[0,79,159,239,319]共10新增。袋平面内旋转两段左推、盒稳定；盒右推袋稳定、盒终局部分图边。独立原audit+pair+全pose support/upright、assist0、hash实际核过；visual_review子文件存rows/fitness/pair/hash/范围。aggregate实际最新10episodes50distinctframes，11layouts pending，completefalse。当前局部斜放仅1–2.5cm Y差，不能等同宽泛自然布局泛化。
- 新simfoundry/data/twopass_protocol.py是独立、尚未接入collector/converter的草稿，未改运行源码。EXPERT精确固定320/switch160/nearhold/初始X.48阈值/first staging.92 bias0 z.845/.84 offsets-.13/-.11 exit.30/second staging1 bias.04 z.825/.82 offset-.11 measured-anchor/.055/assist0/waist0。validate_twopass_contract要求显式approved/exactsettings、新ID成对换slot且seed/yaw不变、原输入validator、绑定FINAL_AUDIT+visual_review+PROTOCOL SHA、全部4case组成功/实际rawhash/所有source_review记录SHA。不自动批准diagnostic。
- TWOPASS_CONTRACT_GUARD_CHECKS.json保存在fixed_yaw_local_groups_r1：用临时合同和当前真实partial证据做3项拒绝验证，未approved、switch159、不完整真实audit/review均按预期ValueError；临时文件自动删除。仅负向检查，正向完整证据+采集/转换端到端尚未验证，不能说合同已上线或获准pilot。下一步全批review后再完善/连接/正向验证，生成freshpilot合同，保持旧spatial接口不变。
- 整体goalactive，未新训练。继续同handle86883及逐组审核，不能把启动或局部通过视为整体完成。

## 2026-09-29T08:58:38.320457+08:00 当前：RGB8/32、前两个完整组审核通过，40个关键帧实际看完

- 本turn持续确认86883同handle live；case69003两task/pair完成pass，runner69000–03四layouts完成8ep。AUDIT_PARTIAL独立审核实际rows8/groups2，两个numeric_and_pair_passed均true，整批completefalse。
- CPU16300生成review_layout_69003后同handleexit0，实际显示page_0.b64；两个task各5frames[0,79,159,239,319]。近袋左推远盒稳定、远盒两段右推近袋稳定，末盒部分图边仍由全pose支撑审核补充。visual_review绑定rawhash并对AUDIT_PARTIAL fitness核过；GROUP_1_REVIEW存4hash与69002/3review SHA，两个完整组已有20+20distinct帧，非全视频。
- 新aggregate_twopass_reviews.py只汇总已有实际review记录，核protocol期望task/path、inventory2条、rawSHA、quality标记/原因、5个准确帧号、reviewhash匹配且唯一。缺review列pending；只有全部review齐且RESULT/FINAL_AUDIT complete并rawhash集相等才标reviewedtrue，不自动看图、不批准训练。实际REVIEW_COVERAGE_PARTIAL最新8episodes40frames、12layouts待审核、completefalse。避免重复计首条重复查看。
- 后台继续斜放groups，86883不得重启。后续新layouts生成后逐组/批审核；整批完成再严格FINAL_AUDIT、全32实际review汇总。未登记新pilot合同、未改diagnostic角色、未转换/训练新模型；整体goalactive未完成。

## 2026-09-29T08:55:30.364800+08:00 当前：RGB完成6/32，第三layout画面10帧已审核，后台仍live

- 上一turn为progress（首完整组4条/20帧实际审核），本turn新增69002两条完成/quality+pairpass。86883多次同handle live，最新runner已COMPLETE69000/69001/69002，case69002SimulationContext cleared，顺序进行69003，不重启。
- CPU91157实际生成review_layout_69002，同handle确认exit0，page_0.b64两段读取实际展示。袋两段左推有平面yaw，盒稳定；盒右推袋稳定，末段盒部分到相机边界。各5frames[0,79,159,239,319]合计10新增distinct，累计已看6条30distinct帧（不重复计前面首条）。独立原audit_rollout/audit_pair+全pose supportupright均pass，assist0/rawSHA核；review_layout_69002/visual_review.json存rows/fitness/pair/hash/观察限制。仅一个assignment，第二完整组未批准；顶层未visual_review准入。
- 读prepare_paired_sorting_lerobot.py确认：现有converter拒diagnostic直训，geometry_group需spatial_contract并核final expert metadata，而两阶段会改变staging/contact_z/bias，不能套用旧单阶段合同。后续注册独立两阶段合同、采freshpilot并复核再转换；现有诊断不改role，不绕审核。converter train/val还要求两推+wait，扩采时须保留合格等待样本/整体组划分。
- 继续同handle86883+新已完成组AUDIT_PARTIAL，生成未看layouts review并实际显示；全部32结束再FINAL_AUDIT和顶层完整审核。当前没有新训练；整体goal active未完成。

## 2026-09-29T08:52:23.435478+08:00 当前：新RGB首个完整交换组4/4通过，20个独立关键帧已实际审核

- 本turn属于progress+verifiedwait：86883多次同handle仍live，case69000、69001顺序完成，各两task/pair均pass；整批runner继续后续组，不重启。
- audit_twopass_render.py --allow-partial实际AUDIT_PARTIAL现rows4/groups1，completefalse/expected8；首个group numeric_and_pair_passedtrue。独立原audit_rollout/audit_pair、source/provenance、q/action零位、waist0/.055/noassist/no external force、near160后exacthold/far160event、support/upright全核通过。脚本非零案例首次实际执行成功。
- CPU53622和1304分别生成review_layout_69000和69001，两者同handle确认exit0；两页均实际显示，每页2轨迹×frames[0,79,159,239,319]，共4条20个独立帧。69000袋子两段左推有平面内yaw转动；全320pose max tilt.011796rad/supporttrue，非目标盒稳定；69001交换后近袋左推、远盒两段右推、非目标稳定。盒终帧部分到图边，完整支撑由pose独立审核，不宣称画面能覆盖全部。
- 两review子目录visual_review.json已绑定实际rawSHA和审核范围；GROUP_0_REVIEW.json核4个uniquehash等于AUDIT_PARTIAL四条，保存两review文件SHA。仅第0组通过，未写顶层全批visual_review批准，未准入training、未转换训练。原首条review_first_episode与本次重复看盒不重复计数，首完整组共20个distinct帧。
- 接下来同handle86883继续核对，余7组已生成后逐组audit/实际图片review；可批量按6episodes/page。整体目标仍active未完成，不能把局部首组或启动作业当完成。

## 2026-09-29T08:48:36.530846+08:00 当前：RGB首layout两条完成通过；已实际复核第一条5帧，整批继续运行

- 本turn先同handle确认86883 live，原runner/collector实际进程存在；没有重启。最新69000两task各320帧quality都passed，case69000日志SimulationContext cleared，runner顺序继续其余layouts。整批尚未完成，不得声称32已渲染通过。
- CPU61913生成review_first_episode后同handle确认exit0。随后实际展示page_0.b64图：只69000 push_box_to_bin一条，恰好frames[0,79,159,239,319]共5帧，右手向右推盒，袋子不动；末段盒子部分超出相机边缘，不能凭画面确认完整支撑。独立terminal_search_scores全320pose核support/upright均true，box最小margin40.835mm、max tilt.003964rad。review_first_episode/visual_review.json保存rawSHA、实际帧号、范围及限制、training_ready=false；不是全视频，不是完整组审核，也没有顶层visual_review批准。
- audit_twopass_render.py新增--allow-partial：仅对四quality齐全的组审核，complete按已完成/预期组数判断。实际运行目前0组，AUDIT_PARTIAL.json completefalse，不是通过证明。全32输出齐后默认严格执行FINAL_AUDIT；没有改运行中的collector/runner。
- 原RGB源目录现约107MiB；下一步继续同handle86883轮询，4条完整组齐后audit及实际图review逐组做。整体goal仍active：此批局部位置成功候选不能取代所有任务干扰/广泛泛化，也未转换训练新策略。

## 2026-09-29T08:45:46.256940+08:00 当前：固定朝向局部8/8完整组数值通过，32条原RGB复现已启动

- 上一goal turn属于progress（force证据、高度失败排除、新组启动）；本turn继续取得新证据。26161已同handle确认terminal exit0，fixed_yaw_local_groups_r1 RESULT complete36，无ERROR；32/32fresh+4/4canonical、8/8完整组全original+support/upright通过，原输入16layouts均valid。GROUP_AND_INPUT_AUDIT、ACTION_AUDIT_FINAL及DECISION已落盘；36逐条rawSHA、q/action首0、waist0、.055slew、near160后exacthold核过。split预先6train/1val/1test。仅固定canonical yaw和局部X/Y变化，不代表所有交叉/朝向泛化，不代表VLA结果。
- 新scripts/prepare_twopass_render.py实际运行成功：要求complete/无ERROR/canonical4pass，重新组audit，只复制所有eligible完整组并哈希绑定。新demo/fixed_yaw_local_rtx_20260929_r1含8组16layouts，PROTOCOL/sourcecollector冻结，计划32episodes全部原RGB独立动态专家复现，不是frozen动作或VLA。新主86883刚启动，log /tmp/fixed_yaw_local_rtx_20260929_r1.log；只此GPU任务。
- 新scripts/audit_twopass_render.py已语法检查、尚未在新RGB输出执行：独立rerun原audit_rollout/audit_pair、320shape/q/action首0/waist/.055、assist0/无externalforce、source/provenance、nearholdexact/farstep160event实测target、support/upright/rawSHA。保留quality额外reset/RGB错误，不把数值通过当视觉审核。下一步运行 --root上述rtx --out FINAL_AUDIT.json（全输出齐再执行），随后make_rollout_review.py、实际展示图片并绑定hash记录visual_review；全部通过后才注册两阶段专家合同和新pilot，不能把诊断改role转换。
- 32条RGB尚未完成、没有已看图的声明；goal active，整体训练/独立h10仍未完成。当前可用空间21GiB。

## 2026-09-29T08:39:34.603105+08:00 当前：接触力已核实；高度反馈失败；固定朝向局部完整组筛查运行

- 主87594、52322、8091均已同handle确认terminal exit0，不能再说在后台运行。near_feedback_engaged8/8失败；near_sweep_force_comparison4/4失败；near_feedback_height10/10失败，均RESULT complete和DECISION落盘，training_ready=false。没有新训练或新准入数据。
- force比较run_frozen_force_probe四条640绝对动作逐帧exact；520..590共71个末physics tick采样，post_action_object_xyz与下一pre-action trace逐帧误差0；solver force buffer未变。物理回放并非bitwise一致（最多3.33mm位置差）。CONTACT_ANALYSIS.json保存所有窗口及force SHA。筛选Robot路径大小写已正确：原timer手与目标先顶部承载接触、后失去；feedback约551/552切换后normal/tangent迅速近0，即使仍有几何contact。采样中包裹相互normal>0.01N为0；不能推出所有substep均无接触/未来无阻挡，不能据此宣称全局不可达。
- run_near_feedback_height_sweep.py新副本，同first480；先timer实际目标进展20mm后Yfeedback lead60mm，同时contactZ降低0/5/10/15mm，另timerbaseline，两near合计10。源SHA、480动作exact、首q/action0、腰0、.055slew已逐条核；全support/upright过，但0原任务成功。bag末段进展最高39.23mm、box41.82mm，均差于timer109.62/115.94mm，不继续盲扩heightgrid。仅诊断，无RGB复核声明。
- 纠正本turn中一次口头错误归因：先依据压缩摘要误称旧fresh把box90deg改0deg，随后查实际layout67000 box_yaw1.51582、68000 1.54036并立即向用户更正；旧box仍约pi/2，不能把错误归因写成事实。旧扩展确实同时变化位置和yaw幅度，下一轮固定yaw仅测位置。
- 新fixed_yaw_local_groups_20260929_r1：seed2026092931，ID69000–15，8groups×2assign×2task=32fresh+4canonical。围绕通过的66000/1：nearX.3696355±.003、farX.5184987±.003；commonY±.012；2frontback dy±.005、3positive和3negative dy10–25mm。固定实际canonical boxyaw1.586075889、maileryaw-.001069726；所有16输入实际validate_diagnostic_layout过，6train/1val/1test预先整组划分。PROTOCOL/GEOMETRY_PREFLIGHT/source.py/SOURCE及每layoutSHA冻结。
- 新run_fixed_yaw_local_groups.py由已canonical通过的fresh_r3复制：firstbias0、staging.92、exit.30、nearoffset-.13/far-.11；near160后hold，far第二次bias+.04/z降低20mm/staging1/exit.30，320帧全部真实关节控制，无物体助推。这是局部位置稳健性检查，不是广泛泛化，也不是训练准入；若canonical失败立刻中止新组。
- 主26161已启动，log /tmp/fixed_yaw_local_groups_20260929_r1.log；下一步同handle确认+ERROR/RESULT检查，运行audit_twopass_screen_groups.py --root此目录 --out GROUP_AND_INPUT_AUDIT.json。完整新组通过再原RGB独立复现/实际keyframe审核；再走新专家合同和freshpilot，不能把diagnostic改role用于训练。继续整体目标，goal仍active未完成。硬约束首帧零/腰零/无assist/原质量门保持。

## 2026-09-29T08:25:19.230558+08:00 当前补充：起始即Y反馈8条全失败，移动后启用反馈对照已启动

- 主95318随后同handle确认exit0，near_feedback_sweep_r1 RESULT complete8条/0成功，DECISIONreject；lead.02/.04/.06bag仅约.0008/.0035/.0101m，明显少于定时baseline末段.1096m；box也距离不足。未做训练准入。
- 新near_feedback_engaged_20260929_r1 PROTOCOL及run_near_feedback_engaged_sweep.py已冻结：同两个near、同first480 exact、final640，lead0baseline/.04/.06/.08。先原timer sweep，实际物体相对final段起点Y进展>=20mm才启用object_feedback_lead，同时feedback_target_y初始化当前palmY避免重置回contact_y；每条存engagement step/objectY/palmY/lead。80mm是新诊断范围（旧collector CLI只允许20–60），不能直接作为已有采集合同使用。原动作.055/zero/waist/noassist/audit/supportupright不变；只关节控制，无物体写入。
- 主87594已启动且本turn同handle再次确认live，log /tmp/near_feedback_engaged_20260929_r1.log。待完整RESULT/ERROR、8组实际是否engage及0baseline复核；若候选通过需原RGB/完整组，不得仅凭位移改善准入。当前仅87594后台，goal active未完成。

## 2026-09-29T08:23:38.355820+08:00 当前：近端偏移对照有局部改善，两失败640帧已实际回放复核；Y反馈对照运行

- 主84942本turn确认exit0，near_repeated_reposition_r2完整8条640帧全任务fail，但COMPARISON逐条件核：非目标<=15mm从r1的3/8升7/8，upright从5/8升8/8；源码SHA核，DECISION no_task_success。repeat10 nearbag前移28.04mm后横推只约.109m，净任务进展.0825；nearbox同样终区不足。不要把局部改善当成功。
- 新near_reposition_failure_rtx_20260929_r1主17260本turn确认exit0，冻结r2两repeat10源640绝对动作逐帧原渲染回放。collect_frozen_long_diagnostic.py独立副本只diagnostic/640/单task/no policy/no force，episode上限80s，object仅reset，直接frozen动作不RPC、不VLAh10。sourceexpert mode在collector恒lift占位，不能解释源相位。单任务pair未验passedfalse导致expectedexit1但质量正常写。
- audit_long_frozen_replay.py实际FINAL2条：640action exact、q/action首0/腰0/.055/assist0/源SHA/原quality+orientation/supportupright核。两条均fail终区，support/upright过。bagmaxqdiff1.16e−6rad，trace约55微米，未声称物理bitwise相同。
- make_long_phase_review.py实际两条各9frames[0,159,319,479,510,540,570,600,639]已显示（CPU图片生成6591/9508均exit0），合计18帧，review/rawSHA/visual_review/STATUS完成，不是全视频。手短推后越过物体，物体停下；box最后靠近bag，不能排除后续遮挡。
- BAG_CONTACT_GEOMETRY用真实recordedquat名义3D外包络XY投影：bag最后>.5mm移动区间563，t560 gap30.1mm，570至639gap6.155mm，bag最终X.378657/Y−.024634，palmY+.299，支持先丢失接触的解释；仅包络不是力或未来路径无障碍证明。图片仍显示前移后部分目标靠近视野前缘。
- 新near_feedback_sweep_20260929_r1：run_near_feedback_sweep.py主95318已启动且再次确认live，log /tmp/near_feedback_sweep_20260929_r1.log。两near各lead0/.02/.04/.06，共8条640；首480冻结r2repeat10exact，最后新CartesianSweepState bias0/contactZ原.840/.845/staging1/crossed-.04，仅Y扫动从原定时换现有object_feedback_target_y：物体Y+方向lead、最多6mm/帧。helper传实际observedY；无物体助推，全部原gate+support/tilt保留。baselinelead0再现原失败；目前baglead.02几乎不动，尚不能称有效。待完整RESULT/ERROR、baselineprefix/动作/源hash审计、评8候选；当前仅95318后台。
- 若低lead无法建立初始推动，可考虑在实际目标先移动约20mm后才切Y反馈，并初始化feedback_target_y为当前palmY避免回跳；这只是未冻结/未实现的备选，不得说已试过。先看本轮全结果。
- 整体goal active：无新训练准入/转换/模型更新/独立h10。

## 2026-09-29T08:10:34.747432+08:00 当前：合规新布局0整组、远端收回接触点未成功；近端偏移对照运行

- 主33308本turn确认exit0，validated_twopass_screen_r1完整4canonical+32fresh；GROUP_AUDIT_FINAL13/32fitness、0/8完整组，所有布局原collector输入validator均过，DECISIONreject。首far exit.22与geometry较远.538–.544导致多数第一段完全未推动，第二段也距离不足。不能将4canonical过当新范围过。
- 已准备collect_validated_twopass_diagnostic.py未运行：与本轮screen匹配，首far exit.22/near.30，crossedoffset-.04强制，第二段显式bias+.04/height低20mm/staging1/exit.30、反侧仍-.04否则-.11。run_twopass_render_groups.py现从冻结protocol取collector路径+SHA并传crossed_contact_offset；尚无合格组启动此renderer。
- RECONTACT_REACH_DIAGNOSIS：68000/1第二段目标X.58374、实测maxX约.556、平均X误差.0537–.0623m，只是路点误差非全局不可达证明。
- 新far_recontact_reach_probe_r1主20237本turn确认exit0，8条=4canonical+4far失败案例（68000bag/68001box、旧outer66002bag/66003box）。只将当前X>.53的第二段targetX设.52，其余+.04与firstfar exit.22不变。4canonical保住，4probe全fail，DECISIONreject。第二推动分别.10532/.02932/.04468/.02713m；68000bag最后X.62475/Y.12990，向后偏移脱离有效推动，不能将有位移当成功。CONTACT_HEIGHT_DIAGNOSIS表明此时palm最低Z约.8249/.8257，不能继续以“高度未到位”无证据推断。无RGB准入。
- 此前准备的near_repeated_reposition_r2现已启动：主84942当前live，log /tmp/near_repeated_reposition_20260929_r2.log。与r1同8条件/640帧，首160原measured-front源exact，随后hold或2次前移（0/−10/−20mm），最后横推仅contact_x_bias显式0替换原默认+.04，其余不改。原r1全失败+3条tilt超限事实保留。待poll完整RESULT/ERROR、原quality+support/upright、逐条件比较，而非凭默认偏移问题断言可解决。当前仅84942后台。
- 本turn也核对了prepare_paired_sorting_lerobot.py与spatial_protocol.py：转换严格拒绝diagnostic，要求freshpilot/视觉rawSHA/原数值pair/整组split/空间合同和专家settings一致；两段专家最终state metadata不能直接套旧单段合同。当前未修改或绕过转换器。只有将来稳定完整组的原RGB证据后，才可增注册two-pass contract并新鲜pilot，不能直接重标诊断role。
- 整体goal active，未扩采训练/未转换新集/未训练新共享模型/未独立h10；更远和近端干扰仍未解决。

## 2026-09-29T08:01:51.151705+08:00 当前：事件早停对照失败，原采集布局门已接入新采样，短首段筛查运行

- event_recontact_screen_r1主4745实际上terminal exit0且ERROR canonical首条失败（app.close吞错误），不能称live。仅66000nearbox1条：t64进展.106触发抬手二次接触，非目标袋131.7mm/box tilt.799rad，失败；DECISION reject，未跑fresh。data/sorting_event_recontact.py未采用。
- fresh_twopass_render_r1启动后立即exit1，collector参数加载阶段拒绝67000 initial footprint clearance，未创建质量/轨迹。旧screen采样只验实际polygon gap5mm，但原diverse_layouts要求两物AABB至少一轴分离20mm及X>=.36；不得放宽此原validator。COLLECTOR_LAYOUT_AUDIT实际16layout仅67004/05/08/09合法，两个数值成功frontback组都非法。GROUP_AND_INPUT_AUDIT保留24/32数值/2组，但eligible_for_render=0。新audit_twopass_screen_groups.py已加入实际原输入validator，每group记录input_errors与eligible_for_render；旧数字成功不等于采集准入。
- 新validated_twopass_screen_20260929_r1：seed2026092928、IDs68000..15，8组2frontback/3正斜/3负斜，近X.37-.39远.515-.545，Yshared±.025/dy±.01或±.02..06，yaw±.1，采样循环对normal/swapped都调用原validate_diagnostic_layout不改门并加前缘8mm余量，6个布局提议被间距拒绝。GEOMETRY_PREFLIGHT预先固定6train/1val/1test整组分，不取决于后续结果。
- 已观测farbox首段tilt>.2时palmY约−.242/−.259/−.269，故本轮首段仅far exit由.30改.22保留near .30；firstbias0/staging.92，反侧signedY<-.03用-.04接近（否则near-.13/far-.11）；仍160后nearhold、far低20mm/bias+.04/staging1/exit.30重接触。不是已证明成功，依旧先4canonical成功才能32fresh，原audit+support/upright不变。
- run_validated_twopass_screen.py主33308已启动且本turn再次确认live，log /tmp/validated_twopass_screen_20260929_r1.log；待poll RESULT.complete/ERROR，按整组+原inputvalidator审计，再匹配新首段参数的原RGB collector（现有collect_twopass_sorting_diagnostic.py首段far仍.30，必须另建版本才能匹配本轮，勿直接复用）。尚无此版RGB/训练准入。
- 当前仅33308后台；旧两个数值成功fresh组因输入validator不符不能训练。原66000/1完整组4/4原RTX成功事实仍有效。整体goal active，困难范围未解决，尚无新训练/独立h10。

## 2026-09-29T07:55:39.729706+08:00 当前：新布局筛查24/32但仅2/8整组，状态触发短推对照运行

- 主91682本turn确认exit0，fresh_twopass_screen_r3 RESULT complete36=4canonical+32fresh。audit_twopass_screen_groups.py实际逐轨迹SHA/唯一case/整组4成员/预分split，GROUP_AUDIT_FINAL24/32 fitness、仅g0/g1两个frontback train整组过。g2=2/4，g3=3，g4=2，g5=3，valg6=3，testg7=3。未把其他成功siblings准入，未渲染/转换/训练此32条。run_twopass_render_groups.py已准备未运行，准备paired原RGB collector也未运行。
- FAILURE_PHASES实际quat与位置：所有4个倾斜超限都在首160，67004nearbox peak75 .4399rad（首次>.2 at73，progress.1 at67），67007farbox peak110 .3624（首次108，progress.1 at92），67011farbox peak105 .6979（首次102，progress.1 at88），67015farbox peak108 .4538；因此不能仅降第二段高度修复。67009/13farbox全程没移，第一段press卡住；67005nearbag终Y.19836稍差，67009nearbag非目标盒15.8mm越限。
- 旧完整组root的TIMED_HOLD_LABEL_DIAGNOSIS比较t150/160两far RGB mean差.50–.66像素，qmax差.030–.032rad，next10actionmax差.266rad；只是定时等待标签潜在歧义，不是严格同观测或已证明VLA失败。不能声称q相同。诊断轨迹尚未准入训练。
- 新data/sorting_event_recontact.py：EventRecontactController全程只关节目标，first bias0/staging.92；若direction*Y<-.03接近offset-.04，否则near-.13/far-.11。实际进展>=.10或first进入hold就立即newstate recontact，bias+.04/height低.02/staging1；实际signedY>=.23且总进展>=.15立即freeze上帧动作终止，取消固定160帧中间等待。保持320帧/零首帧/腰0/.055/noassist/原audit+supportupright。新策略多处对应已定位失败，未做单因素因果归因。
- 新event_recontact_screen_20260929_r1冻结与r3相同几何/预split，4canonical需全通过才进32fresh；run_event_recontact_screen.py主4745随后确认terminal exit0但ERROR为canonical失败（app.close吞异常），已拒绝，不是live，log /tmp/event_recontact_screen_20260929_r1.log，SOURCE同时存脚本与新controllerSHA，运行中勿改。待poll实际RESULT.complete/ERROR（app.close可吞exit码），先看canonical，再整组结果；任何成功仍需原RGB/图像，不自动训练准入。
- 4745已终止，无该后台任务。near_repeated_reposition_r2显式最后bias0仍prepared未启动；完整困难范围未解决，goal active，无新模型训练/独立h10。

## 2026-09-29T07:46:13.383434+08:00 当前：完整组原RTX4/4复核完成；新布局实时专家筛查运行

- 本turn主60078确认exit0，frontback_inner_group_rtx_20260929_r2全4原quality+support/upright通过。FINAL_AUDIT first160 exact/hold exact/zeroq-action/腰0/.055/assist0/160event；原source与trace链SHA核，provenanceoffset-.02核。两layout实际各10关键帧，共20，review/rawSHA/visual_review/STATUS/DECISION完整。完整1几何组通过但仅诊断，不直接训练。
- fresh_twopass_screen_r1准备随机8组发现缺negative diagonal，未运行即superseded。r2改8组=2frontback/3positive/3negative，近X.355-.390远.500-.535，sharedY±.025，dyfront±.01/diag±.02..06，yaw±.15；同时对两categoryassignment名义初始gap>=5mm/tablefootprint做preflight。固定整组split6train/1val/1test在任何fresh结果前保存。IDs67000..15，seed2026092924。
- r2主93618本turnexit0但ERROR显示首canonical66000boxfail+tilt.4876，fresh未运行。定位首段CartesianSweepState漏contact_x_bias，默认+.04与原collector显式0不同，t2 stagingX.40964 vs.36966，动作max差.4076rad；不是物理同动作不可复现。DECISION留证。
- 新fresh_twopass_screen_20260929_r3保留r2完全相同几何/预分split，只显式首段bias0、第二段bias+.04（成功recontact原默认，保持）；run_fresh_twopass_screen_r3.py主91682当前live，log /tmp/fresh_twopass_screen_20260929_r3.log。单env无RGB从零实时生成首160（.92staging/near-.13 far-.11），near后160hold，far新实测state低20mm/staging1.0/+ .04bias。4canonical控制已全部原+supportupright通过，开始32fresh。前66000两任务firstphase动作max差.000523/.000168rad，CONTROL_COMPARISON_INTERIM保留不是exact声称；源码SHA当前实核。待poll至RESULT complete且无ERROR、按组4条和预split统计，合格整组原RGB采集再复核；不能把无RGB筛查当训练数据。
- 已准备collect_twopass_sorting_diagnostic.py（未运行），原paired collector动态首段+160时far重接触/nearhold，完整双任务audit_pair原逻辑保持、orientation全320、事件记录；要求diagnostic/320/.92staging/-.11far/-.13near，不接受policy/forces/waits。r2的render_collector_preparation含路径SHA。用于筛查后成功完整组的fresh paired原渲染验证，非自动pilot准入。
- 同类默认bias问题也存在near_repeated_reposition_r1的最后横推段（此前用了+.04，frontprimitive忽略此bias）。已独立准备near_repeated_reposition_20260929_r2与run_near_repeated_reposition_r2.py，仅把最后横推bias显式0，其余8条件/640帧完全不改，STATUS prepared_not_launched；旧失败/tilt证据保留，不能归因于0bias版本。当前未启动此分支。
- 当前仅91682后台；整体goal active，完整困难范围（outerfar、crossednear）仍未解决，尚无新训练/独立VLAh10结果。

## 2026-09-29 当前补充：完整组RTX读取源格式问题已修，新r2运行

- r1主46571实际exit1，case66000_hold STATUS报box不在archive；natural原raw仅q/action/rgb，box/mailer在同目录trace.npz，collector原支持search轨迹内嵌trace。这是首帧前输入格式错误，未产出质量，FAILURE保存；不当成功或仍live。
- 新frontback_inner_group_rtx_20260929_r2 first_pass_sources显式打包每条原raw q/action+原trace所有字段。实际np.array_equal核q/action原样，PROTOCOL保留original_source/trace路径及SHA与新包SHA。collector源码不改，全部4case新目录；无覆盖失败记录。run_frontback_inner_group_rtx_r2.py主60078已启动且同handle再次确认live，log /tmp/frontback_inner_group_rtx_20260929_r2.log。当前仅60078后台。
- 下一步对r2四条audit_far_recontact、offset/source链核、实际20图、完整组原audit+support/tilt；仍goal active。

## 2026-09-29T07:33:20.174709+08:00 当前：完整前后内侧组4/4数字通过，原RTX整组复现启动

- 主83160本turn确认exit0，frontback_recontact_groups_20260929_r1/run/RESULT complete8条，6/8原audit+support/upright。66000/66001（inner前后类别交换）全4通过，66002/66003 outer的两far仍失败，两near过。DECISION 1/2完整组；未把成功siblings拆组准入；inner成功也待原RTX。
- 新frontback_inner_group_rtx_20260929_r1，4条320帧完整组，PROTOCOL按原natural first160源SHA，各near后160hold、far后160contactz低20mm重新feedback（与probe同规则，非固定后段RPC）。沿用已验证独立collector collect_far_recontact_lower_diagnostic.py，SOURCE/source.py冻结；run_frontback_inner_group_rtx.py。
- 主46571随后确认exit1，首case在首帧前因原raw缺box字段退出（原trace另存），并非live；log /tmp/frontback_inner_group_rtx_20260929_r1.log，每case目录case66000_hold/recontact、66001_recontact/hold，task路径明确。待同handlepoll、audit_far_recontact.py first160exact/hold等/首qaction腰assist/SHA/320/原quality+supportupright、provenanceoffset核、实际20关键帧。四条全部确认后也还是诊断；可冻结规则做新鲜成组pilot，不要直接把诊断样本当训练集。
- near_repeated_reposition全8失败+部分tilt越限结论不变；左右交换近端及outerfar仍保留为未解决困难案例，不能改最终验收范围来宣称全目标完成。当前仅46571后台，goal active，尚未扩采/转换/训练/独立h10。

## 2026-09-29T07:31:52.932921+08:00 当前：两far原RTX已通过并实际复核；near重复前移失败；完整前后组验证中

- 本turn主76856确认exit0，recontact_lower20_rtx_20260929_r1原渲染两条均pass。FINAL_AUDIT first160exact、event160XYZ、首q/action0/腰0/.055/assist0、support/upright全通过；另核provenance second_contact_z_offset=-.02与源码SHA。两条各5关键帧实际显示，共10，rawhash/review/STATUS/DECISION全保存。盒第二推进.148316m、袋.133820m；maxtilt分别.02643/.00834rad；最终盒部分出相机边界，桌面完整支撑依赖记录位姿逐帧核，不能说全视频看到。只两far组件/每条件一次，不能广泛稳健或整组准入；诊断训练false。
- 新near_repeated_reposition_20260929_r1主35127本turnexit0，8条640帧complete，源码SHA核。首160均原front_reposition_measured近端轨迹exact；之后160..479静持或2次额外前拉（offset0/−10/−20mm），480..639重新横推（高度原值）；控制器重置不物理reset，episode上限80s。8条全fail，无RGB，DECISIONreject。nearboxrepeat0/10非目标干扰门过但进展不足；nearbag仍干扰。pre-sort前移8–30mm，横推又把目标X往后带24–66mm，不能称已避障。
- 额外tilt：nearbagrepeat0 .2239rad/repeat10 .3419、nearboxrepeat0 .3276> .20；其他support/upright过但原任务fail。禁止因前移或干扰减少而准入，不直接增加重复次数。新诊断没有图像，不声称视觉通过；后续可选代表复核。
- 新frontback_recontact_groups_20260929_r1已准备并启动主83160，log /tmp/frontback_recontact_groups_20260929_r1.log，当前live待poll。完整2几何组66000..03×2任务8条320帧；前160原natural_coverage24每条冻结，near initialX<.48后半静持保留，far统一新实测recontact低20mm。几何规则类别无关，不取代左右交换困难组，近端障碍仍保留在最终验证范围。脚本run_frontback_recontact_groups.py来源heightprobe，输出每case任务唯一目录。需RESULT complete、ERROR、逐组4条原quality+support/upright，任何候选原RTX/实际图像后才讨论freshpilot。
- 当前仅83160后台，整体goal active未完成；无新增训练集/共享模型更新，磁盘约22GiB。

## 2026-09-29T07:24:17.243150+08:00 当前：降低二次接触高度20mm首次使两个远端通过，原RTX复现运行中

- 主86494本turn确认exit0，recontact_height_probe_20260929_r1/run/RESULT complete=true共8条。两far offset0与−10mm全fail，second_progress0/约.1–.7mm；−20mm/−30mm四条原audit及support/upright全pass。20mm盒第二推+.148783m/总progress.382812，非目标袋2.015mm、最大tilt.0389rad；20mm袋第二推+.134006m。DECISION选较小20mm进行原RTX复现，不是训练准入。
- 新recontact_lower20_rtx_20260929_r1 root与PROTOCOL/sourceSHA。独立collect_far_recontact_lower_diagnostic.py在先前320帧脚本上仅增加受限--second-contact-z-offset=-.02并写事件元数据。首160仍原gen15case2/5固定，后160重新计算feedback专家，故是原渲染环境重现实验，不可称后160逐动作RPC exact或VLA。两条单任务66009farbox/66010farbag；near未测试/仍未解决。
- 新run_recontact_lower20_batch.py主76856已启动且本turn再次确认live，log /tmp/recontact_lower20_rtx_20260929_r1.log。每case320帧/600s超时，原单任务collector因未成pair expectedexit1但质量正常写。接下来poll至terminal，运行audit_far_recontact.py（只核first160exact、event160实测XYZ、zero/腰0/.055/assist0、原quality+support/tilt），另核provenance second-contact-z-offset=-.02和sourceSHA。实际生成显示两条10关键帧。成功复现也只表示far组件改善，不是完整组或整体目标。
- 当前仅76856后台，整体goal active。不要把2far数值通过或启动复现代替完成。

## 2026-09-29T07:22:11.985986+08:00 当前：二次接触全失败，前后布局残差迁移无增益，接触高度有限对照运行中

- 上turn属于progress（条件残差结束/新对照启动）。本turn主83420确认exit0，far_recontact_20260929_r1四条320帧全失败；FINAL_AUDIT核first160与原gen15exact、hold后160exact、recontact160XYZ实测、首q/action0/腰0/.055/assist0、orientation/support/tilt。四条second_progress均0；各review66009/10实际10图，共4/20，rawSHA/visual_review/STATUS completed_rejected完整。手返回但未推动；不是单纯时间不够。
- SECOND_SWEEP_GEOMETRY：盒sweep218..275实际palmZmin.85753/均.86014，目标.845，平均高15.14mm；袋219..276 min.85329/均.85582，目标.840，高15.82mm；两者maxabsX误差约74mm。仅手掌路点误差，非接触力证据。
- frontback_residual_transfer_r1：自然66000..03前后布局8源，64env零对照严格匹配失败；主78488exit0却无RESULT（app.close掩盖异常），97171retry01加except保存ERROR后定位仅env18/66001box原fail→pass，progress.2024608；64中1条边界波动，原4pass均保持。未执行候选比较，DECISION留证。
- 新r2独立protocol修订为保存每env基线且原pass不得退化，失败边界变化不算策略收益；主44159本turnexit0，BASELINE/RESULT完整。固定8组参数（zero、old15 scales.25/.5/.75/1、conditioned_far .5/1、old07full），仅X>=.48远目标加残差，near动作exact；全8候选均4/8、0完整组，无增益/DECISION reject，不扩训，不声称迁移成功。不是原VLA独立验证。
- 新recontact_height_probe_20260929_r1：主86494已启动并再次确认live，log /tmp/recontact_height_probe_20260929_r1.log。run_recontact_height_probe.py单env无RGB依次2far×offset0/−.01/−.02/−.03=8条320帧。前160固定原gen15case2/5，后160新Cartesian状态仅调contact_palm_z，其余按原recontact；只控制关节无reset物体；首q/action0/.055/腰0、原terminal_batch_audit及support/upright，输出每条q/action/traces/quats/control/report/SHA。原offset0预计同RTX失败，须实际核，protocol不能当结果。任何成功必须再原RTX+图像，near干扰仍未解决。运行异常在ERROR保存（app.close可能exit0，必须查RESULT.complete及ERROR）。
- 当前仅86494后台；整体goal active未完成，尚无新准入数据/训练/独立h10结果。

## 2026-09-29T07:10:34.054389+08:00 当前：条件残差结束无新增，远端二次接触对照运行中

- 主84134本turn确认exit0：20代430080transitions/200.122s，best_gen10 rank[1,0,4,11.6359]，无新增/完整组0，DECISION已reject且源SHA全核。near干扰低于门但进展仅.0868/.0836m，far.1996/.2293m仍区外；CLEARANCE_FINAL四失败nominalXYgap0。该候选未RTX复核，不称准入；不继续同run扩时。
- 新far_recontact_20260929_r1，PROTOCOL四条独立诊断：66009farbox、66010farbag各hold/recontact，320帧；前160都固定原residual best_gen15 case2/5（已原RTX验证的轨迹），后160静持或从当前实测物体XYZ重新创建CartesianSweepState抬手/接触/扫动。只重置控制器状态，不reset物理、不写物体；原quality与零帧/腰0/assist0不变，expert .055slew。双条件同长度，不能把延长时间当策略成功。near未纳入，此实验不能解决near或满足整组准入。
- 独立脚本collect_far_recontact_diagnostic.py拷贝原collector以免改原链；--first-pass/sourceSHA/task/second-pass，单任务诊断，paired audit明确未执行passedfalse，原quality文件照常写；因此collector会因未成对exit1，批runner只在quality存在且frames320时接受为完成，运行错误无quality会中止。帧前orientation全320记录；新audit_far_recontact.py已编译未执行，核first160动作exact、后hold exact或recontact160实测XYZ、zero/waist/slew/assist、原quality+额外support/tilt。还需实际20关键帧复核，不做训练准入。
- 主83420已启动且本turn再次确认live；log /tmp/far_recontact_20260929_r1.log，每case自己的log，当前case66009_hold。runner每case timeout600s。待poll，同GPU无其他任务；实际审计4条、画面复核，再按结果继续。未经检查不能称重接触成功。
- 整体goal active未完成；多样合格数据/共享训练/独立h10仍待完成。

## 2026-09-29T07:06:10.729978+08:00 当前：失败残差RTX全4复核完成，近远条件残差搜索进行中

- 主89681本turn确认exit0；FINAL_AUDIT四条source/actions/policy_raw逐元素exact，全部失败。实际66009/66010共4条20关键帧已显示，各review.json记录rawSHA。近目标带动非目标，远目标过手后停止在区外；原图像不是全视频。近袋回放非目标59.2mm、近盒39.2mm，和vector略有物理差但同失败原因，不能说物理逐位相同。STATUS completed_rejected，无训练准入。
- 新conditioned_residual_search_20260929_r1：仅direction*initialY<-.03者加残差，nearX<.43/far独立两组4x5共40参数，左右镜像；另外4原成功动作exact不改。保持原时序56/80/100/120/140/159、±.25rad/.055slew、原audit+support/upright、pop16/max20代/430080transitions；初始化均为原gen15，每代保留zero/incumbent/原gen15。protocol/sourceSHA冻结。
- 首次命令多余--headless被参数解析拒绝exit2（未创建run），改本地支持--visualizer none启动主84134，log /tmp/conditioned_residual_search_20260929_r1_retry.log。实际PREFLIGHT40随机候选与zero/unobstructed exact通过，BASELINE全部128原状态重现64/128。本turn已再次确认同handlelive；待poll至terminal，RESULT、原SHA与候选质量复核。当前最新中途仍4/8，无新成功。
- KEY_POSES（原residual根）证据：远目标约.24m后停在Y±.12/.13，手已越过；近目标约.14m附近带动他物。NEXT_DECISION是未执行条件计划：若本轮无新增，不直接延长搜索；考虑原firstpass后同物理episode抬手重新接触再推，并以等时长静持对照，专测far。只是假设，near干扰仍需解决。
- 当前只有84134物理搜索后台；整体goal active，合格多样数据/训练/独立h10未完成。磁盘约22GiB，冻结checkpoint未动。

## 2026-09-29T06:54:04.909888+08:00 当前：20轮残差搜索结束4/8无完整组，失败4条RTX回放启动

- 主86712本turn同handle确认exit0。RESULT20代/430080transitions，best_gen15 rank[1,0,4,11.0544]：原4成功保住、0新增/0完整几何组，不准入。DECISION保存，未扩大此run预算。
- gen15远盒66009进展.230678、远袋66010 .241224m但仍未signedY区(.20)；近袋66009 .152137且非目标盒.0522m，近盒66010 .131232且非目标袋.0373m。因此提高连续分不等于质量通过。
- 新analyze_residual_clearance.py实际gen07和gen15，用记录quat的名义3D物体8角点XY convex hull距离：gen15四失败最小/最终投影gap全0；只是几何包络，不能当真实接触力或证明碰撞。gen15近目标deltaX+.00709/+.00434，远目标+.04715/+.04508，记录在CLEARANCE_FINAL。gen07曾接近无干扰但进展仅8–10cm，最终评分更高候选又有近端干扰；不要拿中间gen07替final说全无干扰。
- 新residual_failure_rtx_20260929_r1冻结66009/10各双任务4条（best15 case2..5），未回放其余4条数字成功，故绝不能称其视觉准入。新通用run_frozen_replay_batch.py主89681已启动，log /tmp/residual_failure_rtx_20260929_r1.log，原collector h10/cap0/noassist接固定RPC。待同handlepoll、原动作exact审计、实际20关键帧。
- 后续按画面确定near/far是否需要不同几何条件修正；目前只是推断，不改运行中任务。当前仅失败RTX回放后台；整体goal active，多样合格数据/共享VLA/独立h10尚未完成。

## 2026-09-29T06:48:52.654977+08:00 当前：残差生成预检/128物理零对照通过，有界搜索运行中

- 新data/residual_trajectory.py：20参数/4knots，0..55及inactive/腰腿原样，56anchor0，80/100/120/140自由、159绑140，smoothstep后active关节限位与.055slew，残差abs<=.25。零参数直接copy且模板硬约束先核，不制造零对照差。PREFLIGHT实际8源hash、零残差逐元素exact、40随机候选最大step.055000007、30组FK左右mirror[1,-1,-1,1,-1]位置最大误差1e-5m通过。
- 新run_residual_trajectory_search.py主86712已启动且同handle确认live，log /tmp/residual_trajectory_search_20260929_r1.log，root residual_trajectory_search_20260929_r1/run；128env=16candidate×8cases。实际BASELINE全部128原pass状态一致64/128、动作逐元素exact，才进入搜索。外层EXECUTION/sourceSHA/源码快照保存；不改运行脚本/模块。
- CEM pop16/max20代/seed2026092917，20维共享mirrored残差，zero与incumbent每代保留，elite4、mean/std混合.5、sigma初.08范围.02–.15、params±.25。排序先原4成功case均保留，再完整4case几何组数量，再原audit+support/upright成功数，最后连续progress/zone减non-target/table/tilt分；不以softscore准入。
- 预算最多430080 transitions含128零对照、timeout1200秒，newrun剩余磁盘每代>20.15GiB。改善候选按best_gen各存8q/action/trace/ori+metadata，均training_readyfalse/visualpending；即便只softscore改善也可能存，不得把best目录当成功。结束RESULT后择真正整组通过者原RTX回放。
- 当前后台仅残差物理搜索；整体goal active，最终多样合格数据/共享VLA/h10独立验证未完成。

## 2026-09-29T06:44:08.691384+08:00 当前：从零PPO失败已全画面确认，冻结保留专家前段的残差轨迹搜索

- 主58096本turn同handle确认exit0。新audit_frozen_action_replay.py实际FINAL全4核原轨迹action/收到policy_raw_action/落地action逐元素相同，h10/cap0/zero firstq-action/waist0/assist0/160frames/sourceSHA过；physical q/trace差保留。66008/09各10关键帧实际显示+hash复核，全4/20的visual_review/STATUS/REPORT完整。全0/4。
- 画面：66008右手收回远离盒，左手接近袋后翻转抬起/前臂遮挡；66009袋轻微前移后抬手（Yprogress11.38mm），右手未有效靠近远盒。policy分支expert_mode始终lift是未更新占位，禁止据此解释学习策略相位。确未形成有效推动，不是RPC篡改。
- 新residual_trajectory_search_20260929_r1/PROTOCOL冻结8份crossed_approach8来源hash/布局/原质量，4/8baseline且前零/腰0/assist0实核。计划直接轨迹优化，不把失败诊断当成功监督训练。先零残差逐动作重现且vector4/8原pass一致，再允许搜索。
- 候选保留0..55帧和inactivearm，56残差0，80/100/120/140四自由5关节knots（20维），159绑140，smoothstep段插值、最后20帧残差恒定；幅值<=.25rad/target slew<=.055/原jointlimits/腰腿基座固定。双手mirror符号需先FK验证。pop16、max20generations、seed2026092917，不扩时；共享参数同时评8cases，保住原4passing，优先完整4case几何组。当前只是协议，代码未实现/未启动。
- 下一步实现纯残差生成/零残差与mirror预检、零残差物理对照，再有限搜索。任何成功还需原RTX/实际图像/完整组后准入，最终多样数据/共享VLA/h10独立测试不变。当前无后台任务，整体goal active。

## 2026-09-29T06:38:46.284249+08:00 当前：600更新搜索结束全失败，最终轨迹已分析，代表RTX回放运行中

- 主38839本turn同handle确认exit0，不重启。RESULT/HISTORY121批(120train+1deterministic)/TERMINAL完整；614400训练transitions/3840train episodes成功0、final确定性0/32、候选0。耗时learning+reload729.67s，参数确变化.1270且保存重载预测exact。checkpoint SHA实核4335893e5927a869c6979b1941f3a7564550dcbc5e9a3c855f59099b1762757f，TRAINING_AUDIT/DECISION保存，拒绝自动扩时。
- 训练终止后新export主50504实际exit0，search_final_rollouts_20260929_r1：同训练布局32条deterministic160帧每env完整q/action/原始actor/74维obs/trace/orientation+meta/sourcehash，0/32。不是独立泛化。analyze_search_rollouts实际全32校验原始hash/零位腰0：28目标maxXY<2mm、20无持续接近、32进展<150mm；无non-target>15mm、tableproxy/tilt/support失败。只有66009袋4重复约14.6mm maxXY/11.4mm Yprogress。主要尚未有效推动，不宜凭此称任务干扰已解决。DIAGNOSIS/SHA齐。
- 新search_failure_rtx_20260929_r1冻结2代表布局66008/09各双任务4条，源final env00–03，manifest标failed_privileged_policy_diagnostic非候选成功。新run_search_failure_replay.py主58096已启动（待再次poll），原collector policy_port/h10/cap0/zero/default/noassist接固定RPC动作；每布局server仅localhost，结束显式shutdown。log /tmp/search_failure_rtx_20260929_r1.log。未改当前运行脚本。
- 下一步poll58096、对回收policy_raw_actions/实际action与源逐元素核、首q/action/腰/assist/160帧/质量，并生成和实际显示20关键帧；当前回放未复核，不能称视觉完成。之后根据证据选择有物理先验的搜索起点，禁止直接延长从零PPO或准入失败数据。当前只有RTX回放后台，整体goal active。

## 2026-09-29T06:31:30.758284+08:00 当前：有界搜索仍live，76批2432回合无成功，准备结束后轨迹导出

- 本turn对主38839同handle多次poll确认live，最新HISTORY76批2432episodes success0/numeric0，仍按600updates/1200s上限不扩时。INTERIM_INTEGRITY实际核所有运行源SHA与冻结值相同，success<=numeric且无成功批mean_terminal_score<=1，未将部分reward当完成。
- 新scripts/export_search_policy_rollouts.py已编译，尚未执行（POSTRUN_EXPORT_PREPARATION标executedfalse）。训练结束后以CONFIG+final_search_checkpoint加载OnPolicyRunner，32env同训练布局deterministic160步，保存每env q/action/rawactor74维obs/trace/orientation及原audit+fitness/sourcehash，用于具体失败定位和固定动作RTX回放。不能称独立泛化或合格训练数据；还未经过运行验证。
- 等38839完成/timeout先核RESULT/TERMINAL/HISTORY与checkpoint，再运行export（不可与训练抢GPU），有候选做原RTX冻结动作回放，失败也应挑代表复核。当前只有正式训练后台，整体goal active。

## 2026-09-29T06:28:35.946141+08:00 当前：有界搜索仍live、累计1376episode未成功；固定动作RPC已验证

- 上turn短训/正式启动为progress，本turn主38839多次同handle确认live；最新HISTORY43批1376episodes，success/numeric均0，候选0，checkpoint model_0/100/200存在。尚未跑完600预算，不重启或编辑训练模块；log /tmp/bounded_expert_search_20260929_r1.log。
- 等待期间新frozen_action_replay_server.py完成本地RPC基础验证：loopback127.0.0.1/随机空闲port，manifest源SHA/160x23/零首帧/腰0/关节限位/动作step预检、逐10帧按固定prompt回放、显式reset游标、耗尽拒绝。两个66008历史对照32chunks/320动作经原pi05_rpc逐元素全相同，wrongprompt/nonzero-start/overrun拒绝，shutdown主24055exit0。初次50568 tuple限位减float错误已终止后修复，未写root，未重启训练。
- replay_rpc_verification_20260929_r1/MANIFEST/RESULT/server日志/源码SHA/REPORT齐。此为通信/冻结动作验证，无GPU物理回放，无候选图像。候选后续manifest若缺另任务必须明确companion_control，不能当新成功或整组通过；原collector policy_port h10 cap0可接，但成绩须标轨迹回放非VLA。
- 后续继续监测38839到完成/timeout，检查RESULT与deterministic评测；有候选再原RTX回放+严格动作一致/原quality/实际图像，无候选则按冻结预算结论分析而非自动扩时。当前只有正式训练后台；整体goal active。

## 2026-09-29T06:24:28.933932+08:00 当前：6更新短训练通过，600更新有界专家搜索运行中

- 新search_reward.py完整足迹/倾斜(.20rad)专家fitness：原audit pass且两物体全帧support/upright才10；硬失败-5；仅未到位/接触不足/末端动的安全进展[0,1]。没有修改原quality或准入。search_reward_verification边界6项与gamma.99 terminalphi0望远镜和实际通过。
- SearchEpisode已补同pre-action的orientation缓冲；新SearchVecEnv TensorDict74维/5动作，160帧finite terminal无time_out bootstrap，原audit+fitness后episode reset。gamma.99势函数引导接触及目标距离，terminalphi0；history成功和reward分开。
- smoke_search_ppo.py实际主94258exit0，search_ppo_smoke_20260929_r1：32env、6×32步6144transitions、2epochs、actor128x128、std.3；参数max变化.009704，保存重载同obs预测逐元素相同，1完整批32条success0/numeric0，余32步下一回合，learning+reload6.47s。未认任务成功，smoke_checkpoint为小MLP不是VLA。
- 新run_bounded_expert_search.py正式主38839启动并同handle确认live，log /tmp/bounded_expert_search_20260929_r1.log，root bounded_expert_search_20260929_r1。冻结32env/66008–11两完整组×4重复、seed20260929、600updates×32steps=614400transitions、5epochs、timeout1200秒含启动，tensorboard本地/checkpoint100间隔，无wandb；free需>20.1GiB。首进度实际iteration已更新，约2s/update。勿重启/改运行脚本。
- 保存每layout/task第一个fitness成功候选npz+meta（最多8），均training_readyfalse/画面pending且必须原RTX重放；HISTORY每终局刷新，600更新后同模型保存重载校验+deterministic160步32env评测。只有最终回放和整组审计可准入。
- 正式前追加reset位置/四元数断言和可选on_terminal回调；sources均正式启动时快照，smoke目录POST_SMOKE_NOTE明确其快照比实际smoke多这两项，不冒称逐字smoke来源。源SHA齐。整体goal active，尚无合格新数据/共享VLA训练或独立泛化完成。

## 2026-09-29T06:16:46.236973+08:00 当前：完整160帧适配层通过零策略/历史回放，尚未学习

- 新data/search_episode.py：同步32环境160步，74维privileged观测（11q/qd/前目标、双物体pose/速度、初始XYZ、双掌XYZ、task/time），pre-action记录、原audit仅末帧触发，首q/action0/腰0/有限/限位/步长核验。普通step仅活跃手5维；step_absolute仅诊断回放历史双臂，不能当PPO动作空间。
- 新probe_search_episode.py实际主25313exit0，search_episode_probe_20260929_r1/RESULT/zero.npz/historical_replay.npz/REPLAY_COMPARISON/源码SHA/REPORT齐。32env=66008–11×双任务×4，两整组。零动作0/32，历史回放16/32，实际逐32核pass/reasons同原quality，actions逐元素不变，q/trace差保存。0/80/159帧首末env批量掌XYZ对原scalar误差0。零回合4.88s、回放7.38s。无RGB/准入。
- 已读本地rsl_rl5.4.1 VecEnv/OnPolicyRunner：get_observations为TensorDict，step返回obs/reward/dones/extras，cfg obs_groups actor/critic；160帧有限任务终止不能误标time_out并bootstrap。奖励/学习尚未实现。
- 下一步补orientation、完整支撑/倾斜专家搜索得分，任务进展可供探索但不当通过，短更新/保存重载/重置测试再冻结正式步数/墙钟。最终仍原RTX采集+画面+整组准入+共享RGB11q训练+h10独立验证。当前无后台任务，整体goal active。

## 2026-09-29T06:11:39.538112+08:00 当前：32环境多布局reset及原质量接口通过，待搜索适配层

- 上turn完成YZ候选拒绝/4env探针，本turn新vector_reset_probe_20260929_r1实际主85711exit0。32env=66004–11八布局×双任务×2，四整组；reset位置/XY Z W四元数对请求float32值误差0、首上半身0、单env0重置其他31parcel rootstate/q/qd即时差0。无reset后助推。mj mapping[32,58]。5warmup+128steps4096transitions3.26766s=1253.50/s；own process nvidia428MiB采样非峰值，未含相机。
- 新data/vector_sorting_reset.py只显式episode-boundary env.reset+按origin写parcel pose/zero vel，支持env_ids。probe_vector_sorting_resets.py完整实际验证。源码/SHA/RESULT/REPORT齐。不能把即时状态隔离当未来轨迹/solver warmstart等价。
- 新data/search_expert_interface.py：专家5维活跃手增量映射23绝对targets、腿default、首upper0、腰0、非活跃手0、每步.055和jointlimits，taskids0box1bag2wait。独立于VLA/h10。1080行实际随机饱和/限位积累测试最大.055000007、NaN拒绝。
- terminal_batch_audit直接复用原audit_rollout，不重写近似标准；24已有natural轨迹批处理结果/全部reasons/全部原metrics对保存quality逐项一致，10pass14fail；INTERFACE_VERIFICATION及验证脚本保存。仅numeric search终局，不含RGB/reset provenance/orientation footprint/实际画面准入。
- 下一步episode搜索适配层：privileged观测、pre-action160帧缓冲、原终局audit、受控动作和分组reset；先零策略与已有动作回放验证，再冻结有界PPO/轨迹搜索预算。没有启动训练，当前无后台任务；整体goal active，最终共享RGB+11q/h10及多样合格数据未完成。

## 2026-09-29T06:06:17.850931+08:00 当前：YZ锁定全复核退化拒绝；转向自动物理动作搜索基础验证

- 主91021同handle确认exit0，FINAL_AUDIT/FINAL_FORCES实际全4成功，两个review各10关键帧实际显示及SHA/quality核验，总4/20，COMPARISON/DECISION/REPORT/STATUS齐。袋目标8.035→2.494mm、盒8.643→2.870mm退化，组件0/2、分拣0/4拒绝。袋掌actual30.873mm但Y+3.721/Z-6.305mm；恒YZ指令不是actual恒定。承载>0.01N samples袋40/58、盒43/58（旧均58），法向采样均值3.390/3.516N，切向.747/.852N。默认flag仍false，不训练。
- 已读当前sorting_env_cfg：奖励只有alive和盒距bin，不覆盖袋及非目标，不能直接开RL。本地已装rsl_rl5.4.1/rl_games/skrl/SB3；未启动RL。决定停止当前顶面30mm组件逐参数试验，评估自动物理轨迹搜索/学习专家。仍以最终共享RGB+11q/h10目标为终点。
- 新probe_sorting_vector_backend.py实际4环境基础probe完成CPU52400exit0，vector_backend_probe_20260929_r1/RESULT/源码SHA/NEXT_EXPERIMENT_REQUIREMENTS齐。首11q全0、4独立origins及相对默认物体布局一致，zerooffsetaction/waist0、无reset后物体写入。5warmup+32timed控制步.7467s=171.42 envtransition/s；未训练、无RGB。q物理漂移max.003588rad，非首帧非零；首帧严格0。mj mapping[4,58]。PyTorch峰值内存不涵盖Warp/RTX，不得用来总GPU预算。
- 初次启动误用base python缺lazy_loader即退出（尚未创建root），改conda env_isaaclab后才完成，旧启动terminal不重启。当前无后台任务。下一步按requirements做成组多布局vector reset、动作约束、原quality向量对照，再32环境吞吐/总内存并冻结有限搜索预算；不得拿默认奖励或physics smoke当任务成功。整体goal active。

## 2026-09-29T05:59:48.314227+08:00 当前：发现retreat同时横移下降，实测YZ锁定复验已启动

- 上turn进展为完整力复验及静态筛查，本turn显式碰撞面IK CPU82740exit0，side_contact_pose_20260929_r1/POSES/REPORT/源码齐；两目标各16面×3初值，均0候选，袋最好55mm/.788rad、盒35mm/.715rad误差，未进入SAT/连续路径验证。不是全局不可达。
- 实际CONTACT_POINT_MOTION分析已有force轨迹：用q/FK及orientation将post-action接触点从pre[t+1]刚体推进至pre[t+2]（FK全160核验）。retreat相邻采样累加掌X约-23.7/-24.0mm，掌Y约-12.35/+12.02mm，掌Z约-6.43/-6.26mm；接触材料点估算X约-22.4/-22.9、Y约-24.4/+24.5mm。接触点会换且下一interval可能脱离，不能当瞬时滑速或单点轨迹，但明确原指令仍在纠正YZ误差。
- 新front_reposition_hold_yz_20260929_r1冻结同4条，仅在retreat开始记录实测YZ并贯穿retreat/hold固定；X仍实测anchor后30mm/58步，接触准备/门/forceobserver全同。新--expert-front-reposition-hold-yz默认false、要求measured-start。before/after源码与PROTOCOL/layoutSHA/源码SHA齐。
- 默认helper实际318记录状态输出/phase逐项旧新完全相同；新XYZ首anchor连续、YZ恒定、30mm终点与hold验证通过，pycompile/bash-n通过。free22.18GiB，预算.5+20保留。主session91021已启动并同handle确认live，script run_front_reposition_hold_yz.sh，log /tmp/front_reposition_hold_yz_20260929.log，勿重启或改运行脚本。
- audit_front_reposition已增加holdYZ初始XYZ/记录anchor/后续YZ指令恒定结构核验，附实测palmYZ drift；BASELINE_AUDIT实际全4门与原FINAL逐checks完全相同，旧结果不回写。新结果待完成审计/力/实际20关键帧。诊断不训练；整体goal active。

## 2026-09-29T05:53:08.827274+08:00 当前：力复验全4/20复核完成，顶面接触确定，侧姿态搜索待改进

- 主26077本turn同handle确认exit0；FINAL_FORCES/FINAL_AUDIT实际全4成功，两个review各10关键帧实际显示并rawSHA/quality核验，visual_review/DECISION/REPORT/STATUS齐。组件0/2、分拣0/4，不训练。
- 两近目标retreat58/58有承载接触。袋/盒法向绝对和采样均值8.667/8.962N、切向模和2.066/2.388N。CONTACT_DIRECTION实际手-目标承载点82/124，法线absZ最小.9999966/.9999981，确为顶面；切向/法向中位.24576/.26742、runtime滑动friction1.0。不能直接声称摩擦饱和/滑移识别，禁止无证据增摩擦/压力。只末tick，不冲量。
- BASELINE_COMPARISON逐布局meta相同、4/4分拣结论相同但q/action最大差约1.1e-5，未称bitwise一致或观测器因果证明。post-action->next-pre及坐标变换审计均过。
- 新screen_front_side_contact.py已实际CPU54273exit0，SIDE_CONTACT_SCREEN/NOTES/源码快照保存。真实USD手碰撞凸包，裁切至物体高度，-X支持点靠后侧面，零腰/关节限位/保守全手table间隙，每目标10初值；均0合格。盒最好点在顶边Z.79498而非侧面内部，袋残差28.9mm。局部不光滑搜索及保守几何限制，不能当全局不可达。初版过强全手-X平面及序列化/变量错误已修正，最终完整结果才有效。
- 下一步显式侧面接触点/面姿态求解并验证手-物体几何分离、其他物体/桌面/手臂连续可达，再候选动态小测；不盲调高度或直接扩采。当前无后台任务，整体goal active，合格多样数据/共享训练/独立验证仍未完成。

## 2026-09-29T05:47:28.953122+08:00 当前：近袋58采样均有承载接触，近盒仍运行

- 主26077再次同handle确认live，66009两条INTEGRITY完成，66010接续采集。INTERIM_FORCES已实际2条审计，近袋retreat58/58有手-目标接触且法向>0.01N，法向绝对和mean8.667/max11.062N、切向模和mean2.066/max3.518N。不能称完全未接触，不能将最后tick均值当全程平均或冲量/摩擦识别。
- INTERIM_AUDIT实际首2条，近袋目标frontward8.03465mm仍失败，与未观测基线近似但没有断言逐元素相同；首2条画面尚待实际复核，近盒待完成。已准备audit_solved_contact_trace.py。下一步完成4条力审计/基线比较/实际20关键帧，再分析接触方向与滑移。整体goal active。

## 2026-09-29T05:46:46.833195+08:00 当前：实际求解接触力观测复验已启动，首条接口审计通过

- 新front_reposition_force_20260929_r1冻结同66009/10、相同measured-start专家/材料/门，4条诊断；仅新增--trace-solved-contact-forces默认关闭。主session26077同handle确认live，script run_front_reposition_force.sh，log /tmp/front_reposition_force_20260929.log，勿重启。
- 本地MuJoCo Warp support.contact_force使用solver.mjw_data.contact + efc.force解码至独立输出；不调用update_contacts/forward/step。保存geom映射shape标签、接触坐标系、位置、friction、constraint地址、局部6D力和世界3D力。每次核efc.force读取前后逐元素相等。仅最终physics tick，不是全substep/冲量。
- 新solved_contact_trace.py、collector前后快照、PROTOCOL/layoutSHA/源码SHA/PREFLIGHT齐，编译/bash语法通过、free22.31GiB，预算.5+保留20。API已实际跑完首66009box160帧。
- 新audit_solved_contact_trace.py实际首条通过：post-action XYZ对齐下一pre-action trace<1e-6、坐标系正交/力变换/有限/160帧核验，INTERIM_FORCES保存。按控制相位统计手腕/橡胶手与目标的法向绝对值和切向模，不推断净力方向/摩擦参数/因果。还未拿到近袋近盒结果；本批画面尚未复核。原measured4/20全部复核组件0/2已归档。
- 整体goal active，继续完成观测、与未观测基线比较（不可假定逐元素重现）、画面复核，再决定动作改进；无新训练准入。

## 2026-09-29T05:42:05.120899+08:00 当前：实测起点4条完成，组件0/2，继续接触传递定位

- 主16938已确认exit0，覆盖此前live。FINAL_AUDIT全4通过记录/硬约束审计；66010十关键帧实际显示并校验raw hash，总4/20复核完成，visual_review/DECISION/REPORT/STATUS齐。
- 近盒实测掌24.592mm、目标8.644mm，近袋24.258/8.035mm；两条非目标0，唯一组件失败目标位移<20mm。原分拣0/4，不训练，不扩整绕行。远袋伴随图像中间帧倾斜，orientation最大倾角.39979rad。
- 下一步只读接触与控制接口定位；不得把几何重叠当力、不得盲增摩擦/助推或放宽质量门。整体goal active。

## 2026-09-29T05:35:58.262604+08:00 当前：实测起点近袋掌走24mm/袋走8mm，首2条已复核

- 主16938本turn同handle确认live，case66010仍采集，勿重启。首66009两条10关键帧实际显示/hash+quality核验保存review_66009/review.json。
- audit_front_reposition.py已补实测起点/行程审计并编译：retreat首commandX=trace掌X误差<1e-6、记录anchor保持不变、满58帧指令stroke=.03；新模式额外actual palm>=.02门。旧4条另存BASELINE_STROKE_AUDIT，逐checks和component结果与原FINAL_AUDIT完全相同，不回写旧结果。before/after审计脚本保存。
- INTERIM_AUDIT实际首2条通过硬约束/四元数/新anchor核验。近袋掌actual24.2580mm（指令30mm、anchorerror0）已达20mm，而目标frontward8.0346mm仍未20；maxY6.7722mm、非目标0、末10变化.0118mm、名义全足迹桌边min34.30mm、最大tilt.002247rad。唯一component失败为目标位移不足。
- 起点修正使有效掌行程比旧10.833mm增加，目标由2.976→8.035mm，但仍无合格改道动作。不能宣称旧路径实际30mm，也不能将现在掌完成判成物体成功。剩余近盒及伴随远袋待完整审计/实际复核；整体goal active。

## 2026-09-29T05:32:37.225255+08:00 当前：发现探针实际行程不足，实测起点复验4条已启动

- 上turnprogress（component全复核），本turn只读HAND_GEOMETRY_AUDIT完整4条由新audit_hand_contact_geometry.py实际运行，CPU3236exit0。读取USD instances collision Mesh（非visual），核physics:approximation=convexHull/collision=true/局部变换identity，按q验证FK再将凸包与动态物体OBB做全SAT（面法线、box轴、边叉轴）。文件在front_reposition_probe_20260929_r1。只代表authored理想几何，不是runtime cooked/contactmargin/force。
- 两component的retreat58帧SAT gap始终约-1.0至-1.6mm，最小分离轴为object局部+Z；说明几何在顶面轻微重叠，不是确证接触力。更关键：原30mm指令以尚未到达的名义准备X起算，进入retreat时掌已比名义X靠前18.07/17.13mm，故actual palm retreat仅10.833/11.029mm。此前“走完30mm路径”只能指名义指令，不能当实测30mm；已向用户纠正。
- 新front_reposition_measured_20260929_r1/PROTOCOL冻结同66009/10共4条，仅改primitive起点为相位进入时实测掌X；Y/Z/阈值/58步/30mm终端位移/原质量门不变。新增开关--expert-front-reposition-measured-start必须已有primitive；默认false保留旧诊断对照。state存front_reposition_start_x、控制日志记录anchor、meta记录布尔模式。
- 新helper与旧helper实际102样本默认输出/状态完全一致；测得起点.442时首X指令=.442/终点=.412无X跳变验证通过。py_compile/bash-n通过；before/after源SHA与layouts/protocol/PREFLIGHT齐。
- 新主session16938已启动并同handle确认live，脚本run_front_reposition_measured.sh，log /tmp/front_reposition_measured_20260929.log。预算.4GiB+20保留，free>20.4预检。旧18850/3236均terminal，不重启。
- 下一步扩展audit_front_reposition只对新measured模式核retreat首次anchor=preaction掌X、末指令anchor-.03，并要求actual palm frontward>=20mm以确认真正完成物理行程，再审原component物体20mm/non-target/support门。原脚本当前尚未新增这一实际掌行程predicate，务必补上再做新实验结论；旧实验结果不回填。
- 整体goal active，未训练；先修正探针有效性再判断接触策略，不能无证据下“实际3cm推不动”结论。

## 2026-09-29T05:26:24.016423+08:00 当前：桌前component全完成0/2，拒绝整绕行扩采

- 主18850本turn后续poll确认exit0，已终止不重启（覆盖下条早先live）。FINAL_AUDIT实际4条完整运行通过，66010十关键帧实际显示/hash+quality核验保存review；总4/20实际复核visual_review+DECISION+REPORT+STATUS完整。
- 真正component近袋/近盒0/2；伴随远任务不计component分母。近盒frontward3.9935mm、maxY5.1716mm、非目标0、末10变化.089mm、boxfootprint桌边min70.64mm、max tilt .001554rad；与袋2.9758mm均完整retreat58但<20mm，拒绝扩完整绕行。原sorting4/4fail保持。
- 下一步实际检查手碰撞几何（URDF rubber/wrist collision mesh与Isaac导入近似）、本批q/FK/物体动态四元数，量化接触面/表面距离；不能只以掌心位置继续盲调。几何代理不等于力；优先只读现有数据，必要接触观测另行冻结物理诊断。
- 新flag默认0、原专家AST已保持，源快照完整；无新训练数据。当前无后台任务，整体goal active，合格多样数据/共享训练/独立验证未完成。

## 2026-09-29T05:24:52.817232+08:00 当前：桌前近袋探针仅3mm，首2条已实际复核

- 主session18850同handle确认live，case66010运行。首66009两条完成，十关键帧实际显示/rawhash+quality核验保存review_66009/review.json；累计2/4。
- 新scripts/audit_front_reposition.py编译并实际首2条运行，INTERIM_AUDIT保存。零q/action/腰0/assist0/160frames核验，orientation各160x4有限近单位，首四元数±等价meta<1e-6，首XYZ与meta一致；按collector同步pre-action顺序，而非独立每帧外部时钟验证。以原尺寸3D8角点旋转并投影检查桌面XY完整支撑，非接触力。
- 近袋component实际frontward2.9758mm（要求20mm），maxY3.9156mm、非目标0、末10变化.079mm、目标足迹最小桌边margin40.31mm、最大倾角.000818rad；阶段cross_x27/press_x28/retreat_x58/hold_x45。唯一component检查失败为位移不足，原分拣quality仍zonefail。手路径完成不等于推得动物体。
- 伴随远盒原crossed策略sortingfail，未触发新primitive；最大倾角.45483rad已可由此次orientation量化，仅属本次非旧轨迹。不能按frontward门把未触发任务计component分母。
- 后续等66010实际复核及全4审计，两近目标component要求均达标才考虑整绕行；目前近袋已失败，不扩成训练/不直接扫高度参数。整体goal active。

## 2026-09-29T05:21:31.936568+08:00 当前：桌前短程物理改道探针已实现并启动4条

- 上turn为progress（几何与点IK实际筛查），本turn新增物理component测试front_reposition_probe_20260929_r1。冻结66009/66010两布局各双任务，共4条；仅X<.43且direction*Y<-.03的近目标执行新primitive（66009袋/66010盒），另两远目标保留crossed-.04专家。不是完整分拣或准入实验。
- 新sorting_reposition.py：lift→cross_x（掌心目标parcelX+.06，Y初始物体Y，Z.92）→press_x（左.84/右.845，XY误差<35/25mm且Z<=target+.012连续3帧）→retreat_x（58步smoothstep向桌前.03m）→hold_x。复用原Jacobian/限位/每帧.055/腰0，不写物体pose/加力；未闭合手指。首q/action0保持。
- collect_paired_sorting新增--expert-front-reposition默认0关闭，仅diagnostic push-only .02-.04允许，pilot/policy/idle/wait禁止。CartSweepState新增front_reposition_distance；默认分支原语句AST逐句完全相同已实际验证，原行为保持。新目标轨迹低位3帧门/单调有界/终点数值已实际验证，PREFLIGHT保存，py_compile/bash-n通过。
- 新flag时额外逐pre-action保存parcel_orientation.npz（box/mailer各160x4，原root_quat_w对应metadata xyzw），原trace/raw结构不改。需要后续实际核首orientation vs meta、单位长度、时间对齐，结合尺寸旋转角点检验完整桌面支撑。不得凭XYZ断言倾角。
- PROTOCOL定义component门：目标向桌前>=20mm、absY变化<=20mm、非目标maxXY<=15mm、末10稳定、实测姿态全足迹支撑，加硬约束/动作原门，必须实际画面。分拣quality原门仍开启，component轨迹预计zonefail，绝不把component成功当整体分拣成功；两近目标都成功才设计全绕行。
- 主session18850已启动并同handle确认live，脚本run_front_reposition_probe.sh，日志/tmp/front_reposition_probe_20260929.log。before/after源码/sha/两layout/protocol齐。预算.4GiB+20GiB保留，运行前free>20.4；不编辑运行脚本。后续监测18850、orientation及component实测检查、4条20实际关键帧复核，诊断不训练。
- 旧28126/85362均terminal，不重启。整体goal active，未完成合格多样数据/训练/独立验证。

## 2026-09-29T05:17:47.165644+08:00 当前：物体绕行几何与点IK筛查完成，尚无物理可执行路线

- 上turn为progress（全8复核和路线障碍证据），本turn无仿真后台任务；只读几何规划与CPU IK session85362已exit0，不重启。
- 新scripts/plan_object_detours.py已实际运行：object_detour_planning_20260929_r1/ROUTES.json。真实桌面X.28-.88/Y±.75；固定yaw矩形平移segment扫掠体=端点足迹convex hull，连续精确形状检查两段X→Y，不是稀疏时间点近似；lane grid.5mm。要求桌边5mm/障碍10mm为规划余量，不修改原质量门。
- 四条对侧direct均blocked；66009farbox仅back +49.1mm，nearbag仅back+212.2mm；66010nearbox front-51.5mm或back+212.0mm；farbag back+51.7mm。不含机器人碰撞、动态yaw/桌边凸起、接触动力学，不能称可执行。
- 同脚本支持--table-margin/--clearance并实际零余量运行zero_margin_sensitivity：nearbag出现front-38.8mm路线，说明不是全局几何无路；但不可把无容错边缘通道当可靠数据。默认规划余量与原门明确分开。
- scripts/probe_detour_contacts.py已实际运行POINT_IK.json：用8条记录96点重验证FK通过（max保存在文件），五初值/点；假设掌心落在物体运动方向后方60mm、Z左.84/右.845，每路线X/Y段各3点。max误差：farbox back.103923m、nearbag back.166784、nearbox front.021216/back.166250、farbag back.106461。仅筛查这些假设掌心点，不证明真实接触/连续姿态/全局不可达。
- ROUTES/POINT_IK/两脚本源码/REPORT/STATUS已保存。下一步优先检查桌前改道的接触姿态与短程物理推动是否可实现，再整条绕行；不能把理想物体轨迹直接写pose或转换训练，不应直接启动未设计完整的路径仿真。
- 当前无后台任务，整体goal active：物理合格多样数据、共享训练、独立闭环仍未完成。

## 2026-09-29T05:13:39.634343+08:00 当前：对侧准备8条全复核，候选拒绝；需运输绕行规划

- 旧28126本turn同handle确认exit0，不重启。66010/11各十关键帧实际显示并hash/quality核验存review；全8/40实际复核聚合visual_review。FINAL_COMPARISON实际完整8条核验通过，旧4/8→新4/8，整组均2/4。STATUS complete_reviewed_candidate_rejected、DECISION/REPORT保存，不采用、不训练。
- 66010远袋progress.113421m，近盒.175407m且非目标袋.078661m；两条由press停滞进入sweep但失败。66011不触发规则，袋.168235/盒.211996、非目标0均pass。四条受干预全fail，两条非目标大幅移动；四条未干预全pass。
- STRAIGHT_PATH_FOOTPRINT_AUDIT.json用真实尺寸/初始yaw、2D有向矩形SAT、到最低合格Y的1001采样点检查4对侧任务：全4固定X直线路径与静止非目标足迹相交。仅理想几何规划证据，不是接触力、不含动态旋转/机器人，不能证明全局不可行；具体first_intersection保存。
- 下一步实际做二维物体运输绕行通道规划（需初始到通道横向/纵向段都无碰撞、桌面完整支撑/间隙），再检查手掌接触点可达/推拉方式；几何通道存在不等于固定橡胶手能实现。不要直接继续收紧Z或逐毫米offset盲调。新crossed参数保持默认0诊断专用，旧默认专家不变。
- 本turnprogress：剩余4条复核/全8结论/新几何障碍证据；当前没有后台任务（28126已退出），整体goal active，转换新数据/训练/独立泛化仍未完成。

## 2026-09-29T05:10:22.361534+08:00 当前：短对侧准备偏移解除press停滞，但首组仍2/4

- 主session28126同handle确认live，case66010采集中；compare_crossed_approach.py实际首4条通过metadata/geometry/零位/trace核验，INTERIM_COMPARISON更新。旧2/4→新2/4无成功率提升。
- case66009两条十关键帧实际显示/hash+quality核验保存review_66009/review.json，累计4/8、20关键帧实际复核。盒由旧press95/0推进变press16+sweep58/progress.121516m，非目标0，仍进区/推进失败；袋由旧press116/0推进变press21+sweep58/progress.193197m，但盒maxXY.089904m，最终区差113.92mm。图片明确袋和盒都移动/旋转，不能量化手或袋碰撞贡献。
- 新规则确实令当前两条开始sweep，但不等于可用示范；准备可达性和横向运输干扰是不同问题。尚未完整8条/另组回归，不采用，不扩大参数搜索；等66010/11完整复核后定结论。
- 整体goal active，所有诊断隔离，未训练。

## 2026-09-29T05:08:18.476619+08:00 当前：对侧接近实验首2条回归通过并实际复核

- 主session28126本turn同handle确认live，case66009对侧正在采。不重启。首66008两条不触发新规则，2/2pass，十关键帧确实显示（functions cell1719最终已完成，非未见图），hash+quality核验保存review_66008/review.json。
- 新scripts/compare_crossed_approach.py编译并实际首2条运行，INTERIM_COMPARISON保存：同layout字典、初姿<1mm、q/action0、腰0/assist0/160frames、meta只允许crossed/effective offset及微小resetpose变化。66008effective offset均不变；bagprogress.209410、box.162436、非目标0；旧对照2/2，不能把微小数值变动算新策略效益。
- 比较脚本目前允许reset quaternion差异并原样记录，初XYZ误差<1mm；旧reset四元数差仅约1e-10已输出。后续完整8条需同脚本另存FINAL_COMPARISON.json、实际剩余30关键帧，再决定两wholegroups是否通过。
- 累计2/8实际10关键帧复核，目标规则真正触发的四条仍待结果。整体goal active，未训练。

## 2026-09-29T05:04:49.885764+08:00 当前：自然24条完整10pass/0完整组，启动对侧接近偏移8条

- 旧48964本turn同handle确认exit0，绝不重启。66011十关键帧实际显示/hash+quality核验保存review_66011/review.json，袋progress.168235、盒.211999，非目标0均pass。总24/120关键帧实际复核，12份review哈希聚合visual_review；FINAL_REPORT实际全24审计，10/24，6wholegroups0/6，分别2/2/0/2/2/2通过任务。REPORT/STATUS complete_reviewed_no_complete_passing_group。所有兄弟成功也不单独入训练。
- 新crossed_approach8_20260929_r1冻结横向错落66008–11两完整组，共8条，对照natural24对应8条。本次唯一干预：direction*initialtargetY<-.03时contact offset=-.04，否则保持near-.13/far-.11；X/Z/阶段阈值/exit.30/160frames/.055cap不变。目的测试已实测的press横向到不了准备点；不等于放松centered门，也不加settled/Xcap（与历史near_face不同）。成功条件两组都完整4/4且实际画面无问题，无自动准入/调参重试。
- collect_paired_sorting.py新增默认0关闭--expert-crossed-contact-offset，仅diagnostic expert -.13..-.04允许，禁止policy/pilot/idle；collect_meta新增crossed_contact_offset，同时既有effective contact_side_offset保留。diverse_layouts.py新增contact_offset_for_approach复用distance规则。before/after源码及SHA保存。
- 实际OFFSET_PREFLIGHT运行确认8条default与旧distance完全一致，镜像对称，阈值边界/非法direction检查；新规则恰好改变66009/10四条、66008/11四条保持。py_compile/bash-n通过。未作统计显著性或exact replay声称。
- 新主session28126启动并同handle确认live，脚本run_crossed_approach8.sh，日志/tmp/crossed_approach8_20260929.log。运行前free>20.6GiB，新增预算.6GiB+保留20GiB，每case20.12GiB检查。后续监测28126，逐caseINTEGRITY/实际画面，与自然冻结8条同geometry/配置差异及progress/non-target/阶段比较。旧48964终止。
- 整体goal active，未训练，待合格多样数据/转换训练/独立闭环，不以启动作业替代完成。

## 2026-09-29T05:01:04.923538+08:00 当前：自然22/24已复核，press停滞主要横向未到位

- session48964同handle确认live，case66011最后布局运行。report_natural_coverage.py实际审计22条、8pass，completegroup5/6、wholepass0。
- case66010十关键帧实际显示/hash+quality核验保存review_66010/review.json；累计22/24、110关键帧。袋/盒均0推进、非目标0；press98/115无sweep，保留失败。
- 本turn对66009 trace+control重算press条件保存66009_PRESS_CONDITIONS.json：袋116press帧Xready116/Yready6/downready97/allready0；盒95帧X95/Y0/down89/all0。末Y误差袋+44.38mm、盒-55.74mm超过35mm准备门；末Z虽然高于命令23.4/27.5mm，但低于现有.885 down门。不能单纯归为高度或机械收紧Z；准备点横向难以到达是具体线索。未改门/专家，未作全局不可达证明。
- 剩余最后2条及全24报告/视觉聚合；之后按具体接近路径缺口设计干预，勿继续只扩同失败专家数据。整体goal active。

## 2026-09-29T04:59:09.801985+08:00 当前：横向错落交换两条零推进，20/24已复核

- session48964本turn同handle确认live，进入case66010最后组。report_natural_coverage.py实际审计20条，8pass、completegroup5/6、wholepass0。
- case66009十关键帧实际显示/hash+quality核验保存review_66009/review.json；累计20/24、100关键帧。袋和盒目标/非目标位移均0；袋cross42/press116，盒cross63/press95，均未sweep，quality只有zone/progress失败。原始66008两条pass而swap两条fail，整组2/4，不能仅挑normal入训练。
- 与cross停滞不同，这组已进入press后停滞；下一诊断应区分centered的X/Y和down条件，不把proximity95/74当接触证据。尚未测接触力/不能宣布不可达。
- 剩余66010/11四条仍运行，旧配置/门均保持；整体goal active，未放行新训练数据。

## 2026-09-29T04:57:36.493800+08:00 当前：横向错落首布局2/2，18/24已复核

- 主session48964本turn同handle确认live；短等待后case66008两条完成。report_natural_coverage.py实际审计18条、8pass，completegroup4/6、wholepass0，后两组pending。
- case66008十关键帧实际显示/hash+quality核验保存review_66008/review.json；累计18/24、90关键帧。袋progress.207597m、盒.165351m，两者非目标0、数值pass；画面目标向相应外侧移动，袋top及side可见，未测动态倾角。仅normal assignment成功，不可称解耦组通过；等待66009交换。
- 剩余6条（66009–11）继续运行，冻结参数/门均未改。上一turn和本turnprogress（真实复核）；整体goal active，诊断不入训练。

## 2026-09-29T04:55:14.051769+08:00 当前：自然16/24已复核，四完整组均未通过

- session48964同handle确认live，进入case66008横向错落。report_natural_coverage.py实际审计16条，6pass，completegroup4/6、wholepass0；分组2/4、2/4、0/4、2/4。
- case66007十关键帧实际显示/hash+quality核验保存review_66007/review.json，累计16/24、80关键帧。近袋progress.182582m pass/盒0；远盒.071424m failzone及progress/袋0，图片见短程移动旋转、末大topface可见。
- 反向斜向整组near2/2、far0/2，其中远袋cross停滞、远盒短程推进，仍不能等同于单一根因。剩余横向错落两组8条，原参数/原门不变。前turn、本turnprogress，整体goal active，未放行新训练数据。

## 2026-09-29T04:53:50.210627+08:00 当前：自然14/24已复核，反向斜向远袋cross停滞

- session48964同handle确认live，case66007运行。report_natural_coverage实际审计14条、5pass，completegroup3/6、wholepass0。
- case66006十关键帧实际显示/hash+quality核验保存review_66006/review.json，累计14/24、70关键帧。远袋0推进/active proximity0，cross158帧；近盒progress.319614pass，但非目标袋maxXY.006330m，并非0；原15mm门通过保留，不擅改门或宣称完全无扰动。
- 这与另一斜向66005远盒cross158形成对称失败线索：物体处于对应手的远处对侧时接近停滞。仍只描述该冻结专家，未证明机械臂全局不可达。等待交换66007及横向错落8条全部完成。
- 本turnprogress实际复核/审计；主采集仍运行，整体goal active，剩余10条待完成和复核，不启动新训练。

## 2026-09-29T04:52:11.815219+08:00 当前：自然斜向整组0/4，新增非目标干扰与cross停滞

- session48964本turn同handle确认live，case66006运行。report_natural_coverage.py实际审计12条，4pass，completegroups3/6、wholepass0。
- case66005十关键帧实际显示/rawhash+quality核验保存review_66005/review.json；累计12/24、60关键帧。近袋progress.303165m，但非目标盒maxXY.027018m>15mm，图中后段盒移动/旋转；远盒0位移/active proximity0，cross158帧（lift2），未进入press/sweep。不能只归因距离或统一zone不足。
- 66005_NON_TARGET_MOTION.json保存袋/盒2/5/15mm首次位移（pre-action索引）及当时掌/物体XYZ和mode；只描述顺序，不认定直接手还是袋碰盒，未测接触力。
- 原冻结直线专家在前三自然组已有接近停滞、零推进、推进不足、非目标扰动四模式；所有诊断隔离。继续反向斜向及横向错落剩余12条，完整结果后再冻结有针对性干预，不改门或删失败。整体goal active。

## 2026-09-29T04:50:32.685267+08:00 当前：斜向首布局双失败，近盒已进区但推进不足

- session48964同handle确认live，case66005运行。report_natural_coverage.py实际审计10条，4pass，completegroup2/6，wholepass0。
- case66004十关键帧实际显示/rawhash+quality核验保存review_66004/review.json；累计10/24、50关键帧实际复核。远袋progress.036139m，近盒.138023m，两者均fail，非目标0。图中袋轻微移动、盒右移旋转，不能将全部失败概括成远处问题。
- DIAGONAL_66004_GATE_DECOMPOSITION实际从trace分解原双门：近盒已达absolute signedY>=.20，但推进<.15，因此原组合reason并不意味着未到区；固定终点面对不同initialY存在另一缺口。质量门不改，不依据单条修改默认endpoint。
- 继续剩余14条，完整6组前不另开盲调。前turn及本turnprogress（真实复核和新增gate分解证据）。整体goal active，训练尚未启动。

## 2026-09-29T04:48:51.018546+08:00 当前：自然前后两组完整4/8，远处失败更明确

- 主session48964同handle确认live，采case66004 diagonal_positive，不重启。report_natural_coverage.py实际审计8条；completegroups2/6，wholepass0，任务4/8通过。
- case66003十关键帧实际显示/rawhash+quality核验保存review_66003/review.json；累计8/24实际40关键帧。近袋progress.234016pass；远盒0推进/非目标0，图中右手扫过盒仍原位。第二组与66002合并near2/2、far0/2且皆零推进；第一组far仅推进不足。
- 本turn查阅历史near_face_contact1/8、settled_near_face1/8、bounded_servo0/8、finger_heading0/4实际复核结果。历史已经有宽press阈值/高掌越过物体线索，不能把本次相似证据当全新发现或机械重跑收紧Z/近侧接触点。现同冻结专家完成剩余斜向/错落几何，用全6组辨别覆盖边界。
- 上turn、本turn均progress（实际复核/更新完整分组证据）；整体goal active，仍未新增训练数据或训练。

## 2026-09-29T04:47:16.365048+08:00 当前：自然布局6/24已复核，外侧远袋零推进

- session48964本turn同handle确认live，case66003正在采。report_natural_coverage实际审计6条，3pass，completegroup1/numericpass0，剩余5组pending。
- case66002两条10关键帧实际显示/hash+quality核验保存review_66002/review.json，累计6/24、30关键帧。近盒progress.252266m pass；远袋0位移，非目标0；图片明确左手扫过但袋留原处，proximity34不是实际接触证据。
- FIRST6_SWEEP_GEOMETRY.json只读前6条trace与expert_control，记录sweep起始/10/20/40/159帧XYZ误差。66002袋sweep起点62，掌X.465633 vs命令.549249差-83.62mm，Z.867944 vs.84差+27.94mm；横扫20帧后仍X差-58.17mm/Z+13.40mm。既有press centered容许X<110mm，down阈值max(contact+.02,table+.135)=.885使此位姿可进入sweep。描述性候选原因，不可声称测到接触或绝对不可达。
- 之前settled_contact/recover_contact_height已有失败对照，不立即机械重跑收紧Z；需等所有6组、查历史后设计能实现接触准备的干预。运行中专家/阈值/质量门未改。整体goal active。

## 2026-09-29T04:45:10.061859+08:00 当前：自然首组完整2/4，远处两类均zone失败

- 主session48964本turn同handle确认live，进入case66002；不重启。report_natural_coverage.py再次实际运行审计首4条通过，INTERIM_REPORT完整1组/6、numeric wholepass0；首组远袋和远盒均zone失败，近袋和近盒均pass，非目标0。
- case66001十关键帧实际显示/rawhash+quality核验保存review_66001/review.json。近袋progress.243009、区余量46.30mm；远盒progress.198190、区差3.78mm，旋转但实际大topface可见，无全视频/姿态角声明。累计4/24已实际20关键帧复核。
- FIRST_GROUP_ENDPOINT_DIAGNOSTIC.json基于末pre-action trace和collect_meta/control目标保存4条描述性掌/物体端点：远袋掌Y距.30差12.50mm、末X.48507（目标初X.51850）；远盒Y差11.80mm、末X.48691；近两掌Y误差约1.5mm。属于可达/接触保持候选线索，不是接触力、无碰撞、或因果证明；应等剩余布局，不立即另开盲调。
- 前turn与本turn均progress（实际复核、审计/新轨迹证据），不是阻塞。继续剩余20条、全6组报告，再确定数据覆盖和专家改进。整体goal active，未开始训练。

## 2026-09-29T04:43:20.020110+08:00 当前：自然布局首2条已复核，1pass/1zonefail

- 上turn为progress（拒绝endpoint方案，启动24自然诊断）。本turnsession48964同handle反复确认live，阶段case66001；不要重启或编辑运行脚本。
- case66000两条完成，10关键帧实际显示/rawhash+quality核验存review_66000/review.json。远袋确实接触并向左运动，progress.176481m，但稳定区差21.55mm，非目标0；近盒progress.249666m、区余量46.39mm，袋0，pass。袋和盒均有旋转，末帧大topface可见；未声称全视频/测量倾角。组未完整，不能算通过组。
- 新scripts/report_natural_coverage.py编译并实际读取首2条审计通过，INTERIM_REPORT保存6registered strata（包含pending）；检查layoutSHA/meta、首q/action0、腰action0、assist0/160frames、trace和quality进度/非目标一致、raw对INTEGRITY哈希。报告按整4任务组才计pass。后续命令同脚本--root demo/natural_coverage24_20260929_r1 --out 同目录INTERIM_REPORT.json；完成后另存FINAL_REPORT并实际视觉聚合。
- 已定位下一轮训练WandBConfig原生disable_artifact:bool=False，位于lerobot/src/lerobot/configs/default.py第46行；后续训练配置应显式--wandb.disable_artifact=true或WANDB_ENABLE=false，避免重复7GiB上传staging。当前未改训练配置/未训练。
- 整体goal active，待剩余22条、完整6group和质量覆盖缺口判断，不自动入训练。

## 2026-09-29T04:39:52.263822+08:00 当前：终点候选已拒绝；更宽自然布局24条诊断启动

- 旧69878本turn确认exit0，不重启。audit_expert_exit_margin.py实际完整运行通过；NUMERIC_COMPARISON：.30与.32均3/4，最差稳定区余量-9.15566mm/-7.48768mm，仍远盒58001失败。近盒余量下降3.88mm。全部8条40独立关键帧实际显示，review_layout58000_both和review_layout58001_both rawhash/quality核验保存，总visual_review/DECISION/REPORT/STATUS齐。
- 根据预注册拒绝.32，不继续endpoint逐毫米搜；默认.30不变，新增CLI保留仅diagnostic用途。不能把局部袋多推8.7mm称完整改进。诊断数据隔离。
- 新natural_coverage24_20260929_r1：固定seed2026092904，6group/12layout/24任务。front_back_inner/outer、diagonal_positive/negative、lateral_stagger_positive/negative；槽位中心X.370-.548、Y±.110，另X±.002/Y±.004抖动；盒yaw约pi/2、袋约0各±.025；每组交换完整位置、两条指令，类别空间分布对称。所有12layout实际经validate_diagnostic_layout通过，初始无重叠/无悬空；这不代表运动可行。
- PROTOCOL/12layout+sha/case_inputs/SOURCE_SHA256+代码快照已保存；专家保持staging.92/offset-.13/far-.11/exit.30/160frames/.055cap，无助推，原门。6组全部报告，禁止失败重采替换，不允许悄悄丢掉整个失败stratum后声称覆盖。开发诊断不是最终独立测试，后续需冻结分布新pilot+整组划分。
- 新主session48964已经启动并同handle确认live；脚本run_natural_coverage24.sh，日志/tmp/natural_coverage24_20260929.log。24条预算1.5GiB，启动free>21.5，每case>20.12GiB；23GiB现有可用支持该诊断，未训练。后续每完整case检查INTEGRITY+实际关键帧、最终按6wholegroups报告。旧69878/91394均terminal。
- 整体goal active：自然合格训练数据扩展、共享训练、独立闭环仍未完成，不因诊断启动或数值通过完成目标。

## 当前：基线4条实际复核3pass；清理三份已验证临时副本恢复空间

- 主session69878同handle确认live，进度exit32_58000。基线exit30_58001两条十关键帧本turn实际显示、rawhash/quality核验保存review_baseline58001/review.json；累计4/8实际20帧。近袋progress.261272pass；远盒.175644仅zonefail、非目标0。基线总3/4，尚无endpoint.32结论。
- 发现/home/user/.local/share/wandb/artifacts/staging占526GiB/76文件。只挑最近三份tmprzv3qoz4/tmpotcgfkiz/tmpxxjmb0mg，与保留absolutechunk10/coverage80/spatialprefix模型完整逐字节比较+SHA256完全相同（每份7473096344B）。审计session91394exit0。
- lsof三路径无打开句柄（exit1/空stdout），再核inode/size/mtime及保留模型存在，只删除这三个临时副本。storage_duplicate_audit_20260929_r1/VERIFIED.json和CLEANUP.json保存完整证据。实际free23.4825GiB，所有checkpoint/数据保留。无自动审批拒绝。其他缓存未动。
- 继续69878，完成候选4条后实际复核、运行audit_expert_exit_margin.py做完整8条比较，整体goal active。后续训练仍需关闭W&B模型artifact副本或计入额外7GiB预算，不把剩余23GiB视作无限空间。

## 当前：终点余量对照首2条已实际复核，余6条运行

- 前turn为progress（8接触对照复核/新实验启动）。本turn主session69878同handle确认live，阶段exit30_58001；未重启。
- exit30_58000两任务2/2pass，review_first2十关键帧实际显示、rawhash/quality核验及review.json保存。袋progress.225601、盒.254549m，非目标均0，maxstep.055；仍只是基线不能推断endpoint.32改善。
- 新scripts/audit_expert_exit_margin.py py_compile通过，待完整8条后实际运行：--root demo/expert_exit_margin_20260929_r1 --out 同目录NUMERIC_COMPARISON.json。检查layout/hash/endpoint/160frames/首q action零/腰0/assist0、trace与quality一致，并汇总每组4任务最小稳定Y区余量和progress余量。未实际完整跑之前勿称审计通过。
- 接下来完成剩余6条实际关键帧复核及完整数值比较；训练准入和整体goal仍false。旧自然/compact布局历史失败已查阅，后续不要机械重复旧失败或把终点优化等同于解决学习泛化。

## 2026-09-29T04:29:46.548758+08:00 当前：接触三方对照结束，专家终点余量8条对照已启动

- 旧session4186已exit0，不重启。原eval/带记录/无记录三方四任务pass/fail全部一致（原100袋pass，其余3fail），所有数组均非exact；无记录重复也分歧，单次重复不能估计方差或断言contact logger因果。
- 新compare_contact_control_runs.py已编译并实际运行两case，THREE_WAY_original100_seed2及THREE_WAY_spatial58004_seed1保存。原100盒原→control actionmax .053609rad、首RGB MAE.279911/255；空间盒原→control .320277rad、首RGB MAE.132528/255。不把数值分歧当成失败不可重复。
- control四条20关键帧本turn确实显示，hash/quality核验并存两个control_*/review.json；八条总40帧visual_review、REPORT、两个STATUS complete_reviewed。原100盒control袋maxXY.154515m、progress.124501m、maxstep.080657；画面见袋竖起。空间袋progress.170946failzone；盒袋.081857、progress.110341、maxstep.135554且stillmoving。诊断均隔离。
- 转向示范余量：新expert_exit_margin_20260929_r1/PROTOCOL冻结58000/58001两个类别交换布局×两任务×endpoint .30/.32，共8条，原门/步数160/专家cap.055/staging.92/offset-.13/far-.11不变；唯一endpoint干预，sweep时长相同（因此路径速度也随距离改变）。先整组4/4和画面/最小稳定区余量比较，不能自动调参或准入。
- collect_paired_sorting.py新增--expert-exit-y默认.30保持旧行为，非默认仅diagnostic expert .30-.34，拒绝policy/pilot；既有collect_meta记录exit_y。before/after源快照保存，py_compile/bash-n通过。
- 主session69878启动并待监测，脚本run_expert_exit_margin.sh，日志/tmp/expert_exit_margin_20260929.log。运行前剩余2.8GiB，预算.5GiB+2GiB保留，每case free>2.12GiB检查；没有训练。不得编辑运行脚本。完成后需8条实际40关键帧、质量/余量/默认回归比较。整体goal active，不能以启动任务当完成。

## 2026-09-29 04:19 当前：接触诊断4条已实际复核，未记录接触对照运行

- 旧44794exit0，不重启。第二case PARITY_spatial58004_seed1已实际运行：all_arrays_exact=false，post-action→nexttrace对齐通过；袋fail/盒fail与旧类别一致，但数值不同。两条10关键帧实际显示/rawhash/quality核验保存review_materials/spatial58004_seed1/review.json。累计接触4条/20关键帧复核完成，尚无exact复现。
- 本次空间盒target progress.164742m、非目标袋.120221m、maxstep.120109rad，四门fail。候选active_target58、object_object121、active_non_target125，5mm box116/mailer128（均afteraction索引）；不能据候选顺序量化直接手 vs 物体碰撞贡献。袋progress.171263m未稳进区。
- 按预注册分支启动未记录接触对照：relative_contact_diagnosis_20260929_r1/uninstrumented_control，2case4条完全同config，只移除trace-episode-contacts；新脚本run_relative_contact_control.sh，主session4186，log /tmp/relative_contact_control_20260929.log。运行前free>2.4GiB，原旧/带记录数据保留。
- 下一步监测4186；完成后需原eval/带记录/未记录三方逐raw q/action/RGB+物体/掌trace对照，尤其首RGB差；再实际20帧复核。任何不一致不得改门或伪称确定接触根因。训练数据/模型保持，整体goal active。

## 2026-09-29 04:17 当前：首个模型接触诊断不满足exact parity，需未记录接触重复对照

- 主session44794本turn同handle确认live，已进入spatial58004_seed1。original100_seed2两条完成、10关键帧实际显示/rawhash/quality核验，review_materials/original100_seed2/review保存（2/4），均保持原pass/fail：袋pass、盒非目标/区/突变fail；盒袋maxXY.214676m（旧.154138m），不是精确复现。
- 新audit_policy_contact_replay.py已编译并真实运行，PARITY_original100_seed2记录逐raw q/action/RGB、物体/掌trace及post-action→nexttrace一致性（后者<1e-6通过）。all_arrays_exact=false；盒q最大差.065906rad、action.055785rad、袋XYZ.074167m；袋任务也非exact。same_quality_decision字段比较reason字符串含数值，false并不表示pass/fail类别改变。
- 候选记录本次盒active_non_target46、active_target105（after-action索引），5mm袋91/盒106；仅解释本次诊断，不能直接充作原轨迹因果证据。帧对齐已明确pre raw vs post contacts差1。
- INITIAL_PARITY_original100_seed2：初q完全一致，但首RGB已不同（盒MAE.15224/255，袋.12681/255），首action盒差.000208rad、袋.000446rad，早于第一次contact读取。提示重复运行初始图像差异参与，不能直接归因contact记录器。
- 本turn末session44794已确认exit0，两case采集结束，不再后台运行，不重启。
- 按PROTOCOL，接下来完成第二case parity+实际复核后，在新目录关闭trace-episode-contacts重复相同配置，用三方对照区分运行变化与记录器；勿修改当前运行脚本、勿认为all_arrays_exact=false就可重训或丢弃失败。整体goal active。

## 2026-09-29 04:12 当前：同几何专家18全部实际复核17pass，模型接触诊断已启动

- matched_expert_diagnosis_20260929_r1 STATUS complete_reviewed，所有18条/90独立关键帧实际显示，九review+visual_review hash聚合保存；最后原102袋progress.207827m、盒.181720m、非目标0均pass。COMPARISON_ALL54真实运行通过，全54模型对18专家layout字典同一、实测reset<1mm、零位/腰0/assist0核验；REPORT和EXPERT_SUCCESS_MARGINS齐。旧session66685/70674均terminal，不重启。
- 专家17/18通过、非目标0违规；唯一58001远盒zone差9.16mm。58003/58005远盒成功余量7.57/5.70mm；58000/02远袋余量11.01/19.57mm。完整数值仍不是训练准入，本18诊断永不自动混训练；同帧偏差含时序差，不能直接证明接触因果。
- 新workflow relative_contact_diagnosis_20260929_r1，PROTOCOL冻结2布局4条模型诊断：original100 seed2（非目标先动）及spatial58004 seed1（目标先动后非目标）。同relative checkpoint/h10/cap0/solver10，仅启用既有只读trace-episode-contacts，仍是候选对而非力测量。
- 新主session44794已启动并同handle确认live，脚本run_relative_contact_diagnosis.sh，log /tmp/relative_contact_diagnosis_20260929.log，端口18777。两case分别启动模型、collector，再自动退出。完成后必须逐raw q/action/trace/geometry做parity，差异如存在先未instrumented repeat、不能谎称同轨迹因果；再实际20关键帧和候选接触/位移关联。
- 预算预检free>2.4GiB，4条新增预算.4GiB+2GiBreserve，无训练或专家/质量门改变。goal active，独立泛化/合格多样数据训练仍未完成。

## 2026-09-29 04:08 当前：原场景第二布局专家2/2，累计16/18实际复核

- 新主session66685本turn同handle确认live，STATUS collecting_expert_102。原101 INTEGRITY和COMPARISON_101完成；10关键帧实际显示/rawhash/quality核验保存review_materials/layout101/review.json。累计16专家/80独立关键帧，15pass，余原102两条。
- 专家袋progress.198953m、盒.187519m，非目标0、maxstep.055，均pass。模型盒3seed全fail：seed0/1目标0，seed2袋72帧5mm先于盒118；专家盒5mm onset63。
- 模型推盒第60帧掌比专家差XYZ：seed0[+.013,-.020,+.022]m，seed1[+.014,-.053,+.067]m，seed2[-.005,+.106,+.004]m。高度/横向差模式在原100/101重复，但仍是同帧关联含时间差，不是干预因果证据。
- 下一步原102实际复核、全54同布局比较与全18质量余量汇总；诊断数据不入训练，原门不变，goal active。
- 本turn末session66685已确认exit0，采集终止且原102两条INTEGRITY完成；没有后台采集继续。不要重启，直接复核最后两条并汇总。

## 2026-09-29 04:06 当前：同几何原场景首布局专家2/2，三种模型推盒误差并存

- 新主session66685本turn同handle确认live，STATUS collecting_expert_101，原100 INTEGRITY两条完成。COMPARISON_100实际6policy对2expert核验layout相同/实测reset<1mm/零位/腰0/assist0；10关键帧实际显示、rawhash/quality核验保存review_materials/layout100/review.json。累计14/18专家、70独立关键帧，13pass，余4条。
- 原100专家袋progress.209163m、盒.193843m，非目标0、maxstep.055，均pass。模型盒seed0/1/2全fail，分别推进不足/完全不动/非目标+推进+突变；5mmonset专家box60，模型71/无/110，seed2袋91先于盒110。
- 同帧掌差：seed1第60帧比专家X+.026/Z+.044m，目标不动；seed2第60帧Y+.140m，后续袋先动。仅同帧轨迹证据，含时间错位，不宣称高度或Y差已证为因果。seed0第60Y+.056，亦推进不足。
- 专家无袋扰动说明该原布局不要求先碰袋；仍需其余原101/102完成、全54对照/阶段统计，再设计针对性修正。诊断隔离，goal active，原门不变。

## 2026-09-29 04:04 当前：空间12专家全实际复核11/12，原场景恢复正常运行

- 新主session66685本turn同handle确认live，STATUS collecting_expert_100。旧70674已exit1不要重启；恢复脚本仅确定性sample_layout原三布局，前turn已验证与冻结rawlayout字典完全相同。
- 58005两条COMPARISON_58005及实际10关键帧/rawhash/quality核验完成，review_materials/layout58005/review.json保存。累计12/18专家、60独立关键帧。近袋progress.251600m，远盒.219477m，非目标0、maxstep.055，均pass，图中运输旋转且盒大topface可见。
- SPATIAL_EXPERT_INTERIM：空间12条11pass，唯一58001远盒zonefail，无非目标违规；六份COMPARISON各6policy/2expert共36匹配。58005近袋expert5mmonset50 vs policy68/56/52（pass/非目标fail/pass），远盒78 vs83/80/92（pass/pass/zonefail）。时序差仍非因果证明。
- 原六条仍待完整采集/实际复核，全18后需全54对照、所有专家稳定进区余量统计和结论，不把局部11/12当整体解决。诊断数据仍隔离，goal active。

## 2026-09-29 04:02 当前：专家原场景输入格式故障已恢复，仅续跑未生成六条

- 旧session70674最终exit1（已终止，不重跑）：六空间布局12条全INTEGRITY完成，进入original100时显式诊断schema因缺geometry_group/assignment拒绝，发生在仿真/输出目录创建之前。不是质量门失败，也不是存储不足。原log与RECOVERY.json保留。
- 已用实际sample_layout(100/101/102)与冻结policy raw layout逐字典比对完全相同（含seed/XYZ），三输出目录均不存在。新脚本continue_matched_expert_original.sh仅original_inputs三布局走原collector确定性sample_layout路径，参数/几何/门均未改，不放宽schema，不重跑完成12条。
- 新主session66685启动后同handle确认live，log /tmp/matched_expert_original_recovery_20260929.log。后续监测此session，不再70674。STATUS正在collecting_expert_100。每layout仍完整性和零位/腰0/assist0/候选接触验证。
- 已实际复核10/18，58005两条虽INTEGRITY数字pass尚未实际看，接下来先补58005 review+COMPARISON_58005，再原三布局。全18之后全54对照/汇总，goal active。

## 2026-09-29 04:01 当前：同几何第五布局专家2/2，三个远袋布局专家均成功

- session70674本turn同handle确认live，STATUS collecting_expert_58005。58004两条INTEGRITY及COMPARISON_58004已完成；10关键帧实际显示/rawhash/quality核验保存review_materials/layout58004/review.json。累计10/18专家、50独立关键帧，9pass，余8条。
- 专家远袋progress.216788m、近盒.246099m，非目标0、maxstep.055，均pass；同layout模型两任务三seed全fail。远袋5mm onset expert75 vs policy40/65/31；近盒expert56 vs policy62/68/无，policy种子0/1后袋75/121帧开始5mm移动。
- 58000/02/04三个远袋布局专家3/3成功，模型1/9：不能将这些失败统一归因于物体挡住导致不可完成，但不证明无任何接触影响。继续诊断路径/时序偏差；此前专家58001远盒fail和58003余量7.57mm仍保留。
- 剩余58005两条和原100/101/102六条待实际复核，全18完成后运行全54对照和完整结果报告；最近磁盘3.2GiB，诊断不入训练，goal active。

## 2026-09-29 03:59 当前：同几何第四布局专家2/2，远盒成功余量偏小

- session70674本turn同handle确认live，STATUS collecting_expert_58004。58003两条INTEGRITY/COMPARISON_58003已完成；10关键帧实际显示/rawhash/quality核验保存review_materials/layout58003/review.json。累计8/18专家、40独立关键帧，7pass，余10条。
- 专家近袋progress.249047m、远盒.209257m，非目标均0、maxstep.055，pass。模型近袋3/3、远盒2/3；远盒5mmonset expert77 vs policy80/79/89。同帧相近onset不代表后段足够。
- 新FAR_BOX_ZONE_MARGIN_INTERIM读取实际trace最后10帧：58003专家最小signedY=.207570（余量7.57mm），模型seed0/1/2余量4.56/18.14/-5.16mm；58001专家余量-9.16mm，模型28.04/19.48/3.73mm。严格原.20门，描述两个远盒布局，不全局泛化；绝不可把progress当absoluteY。
- 新证据支持审计专家成功余量及后段推进，不只查早期高度。未更改专家参数/数据/质量门，诊断不入训练，整体goal active，继续其他布局。

## 2026-09-29 03:57 当前：同几何第三布局专家2/2，远袋早移不足现象重复

- session70674本turn同handle确认live，STATUS collecting_expert_58003。58002两条INTEGRITY完成，10关键帧实际显示/rawhash/quality核验保存review_materials/layout58002/review.json；累计6/18专家、30独立关键帧，5数值pass。
- 专家远袋progress.217880m、近盒.247387m，非目标0、maxstep.055，均pass。COMPARISON_58002实际运行6policy对2expert，layout字典相同/实测初始物体差<1mm/零位/腰0/assist0核验。
- 远袋5mm onset expert78，模型seed0/1/2为42/62/31，pass分别false/true/false。失败seed0/2第30帧掌比expert低.063/.064m，第60帧Y提前.188/.323m；通过seed1第30帧低.026m。仅关联/同帧偏差（含时间错位），不能把所有早动认定失败因果，因为passseed也早动。
- 近盒expertonset52，policy87/78/66，其中seed1有后袋123帧运动。继续其余12专家与完整54匹配对照；诊断不入训练，整体goal active，原门不变。

## 2026-09-29 03:55 当前：同几何第二布局专家1/2，暴露专家自身远盒泛化短板

- session70674本turn同handle确认live，STATUS collecting_expert_58002，首两layout INTEGRITY齐。58001两条10关键帧实际显示、rawhash/quality核验保存review_materials/layout58001/review.json；累计4/18专家、20独立关键帧，3数值pass。
- 近袋专家progress.257854m，盒约0，pass；远盒progress.175641m、袋0但stablezonefail，maxstep.055，画面正确右推伴旋转。失败完整保留，不入训练。模型同58001三个种子均数字pass（seed0视觉翻立担忧仍保留）。不能假设专家总优于模型或把失败expert作gold label。
- COMPARISON_58001已运行6policy对2expert，layout字典/实测reset差<1mm、零位/waist0/assist0通过；近袋5mm onset expert55，policy50/50/44；远盒expert74，policy73/68/85。仅描述时序，不声称因果。
- 结论边界：58000远袋专家成功说明该摆放不必然受阻，58001远盒专家失败表明现专家边界与余量也需审计。继续其余14专家及全54匹配对照，未新增训练数据或放宽门，整体goal active。磁盘最近3.3GiB。

## 2026-09-29 03:53 当前：同几何专家首布局2/2通过并实际复核，模型远袋3/3失败

- 新主session70674本turn同handle确认live；matched_expert_diagnosis_20260929_r1继续。58000两条INTEGRITY通过，10关键帧实际显示、rawhash/quality核验，review_materials/layout58000/review.json保存（2/18，不自动进训练）。专家远袋progress.226192m、近盒.252992m，非目标均0，maxstep.055；画面对应手/目标运输。
- 新scripts/compare_matched_expert_rollouts.py已实际运行首布局6policy对2expert，COMPARISON_58000.json保存：layout字典严格相同、实测初始XYZ差<1mm、首q0/waistaction0/assist0核验，逐专家phase和固定帧比较，不做时间扭曲。脚本编译与实际6例运行通过。完整18专家完成后需运行全54对照。
- 同58000远袋专家5mm位移onset79帧；policy seeds0/1/2为59/无/31，全部原门fail。seed0/2第30帧掌比专家低.053/.064m，seed1低.009m，说明不能简单归为同一早接近误差；seed2后续向左运动远早于专家，仍推程不足。只描述时序/轨迹，未证接触因果。
- 近盒专家onset51帧，policy88/67/87；模型时序也明显不同。专家contact日志候选含手盒及袋盒（袋实际0位移），因此候选对不等于有效接触力。若加policy接触诊断须做instrumentation parity。
- 整体goal仍active；同几何expert证实本布局远袋并非必然被盒挡死，但不可外推其他布局。后续余16专家需实际复核/对照，原h10等硬约束与训练数据不变。

## 2026-09-29 03:49 当前：同几何专家18条诊断已启动，用于拆分接近与接触后误差

- 上一turn为progress：relative完整60review/比较/报告及54轨迹motion-order完成；整体goal仍active。本turn查80源数据56push对18评测geometry/task，完全同XY（1um）匹配0，最近max坐标差2.10–7.68mm；EXPERT_GEOMETRY_AVAILABILITY已保存。不能把近邻当同几何控制。
- 新workflow demo/matched_expert_diagnosis_20260929_r1，PROTOCOL冻结9布局18条、layouts从已完成relative seed0 raw collect_meta原样提取。空间6布局使用原训练专家staging.92/contact-.13/far-.11，原场景3使用default staging1.0/contact-.13/far0。没有调策略。诊断role，training_ready始终false，不进训练。
- 新主session70674已用同handle确认live，脚本scripts/run_matched_expert_diagnosis.sh，log /tmp/matched_expert_diagnosis_20260929.log，当前collecting_expert_58000。旧评测session27249已exit0，不要重启。新任务会逐layout验证两条raw、首q/action0、waist action0、assist0、contacts文件，并保留已知质量失败继续其他预注册布局；运行/完整性失败停，不重试/不自动推广。
- 采用既有只读trace-episode-contacts（last physics tick候选接触对，不是力测量）；原策略没有全episode接触记录，因此专家数据 alone不能证明策略接触因果。如后续需policy接触诊断应加control parity检查，不能直接夸大。
- 预检free3.654GB，预算新增1GiB+剩余2GiB，每layout检查free>2GiB；新18条需完整图像和trace对比，启动不代表诊断完成。下一步监测70674并复核专家结果，与对应三seed策略比较几何/接近/运动起止；失败数据仍隔离。

## 2026-09-29 03:45 当前：relative10完整60复核32/60，开始干扰时序定位

- 主session27249已返回exit0，结束；不重启评测。最后seed2原场景4/7，layout102袋pass/盒三门fail+waitpass；last3实际15帧、formal seed2review、全六reviewaggregate60rawhash均已完成。累计60条/300独立关键帧，非全视频。
- 两份严格同60比较：relative32/60 vscoverage50 11/60（22胜1负）、absolute10 4/60（31胜3负）。空间22/39（近袋8/9、远袋1/9、近盒3/9、远盒7/9、wait3/3）；原10/21（袋6/9、盒1/9、wait3/3）。REPORT/ADOPTION_DECISION/FAILURE_GATE_BREAKDOWN已保存；workflow STATUS complete_reviewed只代表本试验完成，整体goal仍active。
- 相对动作作为研究基线保留，但不作为完成方案；空间seed0远盒58001数值pass却翻立和原seed2盒100袋侧立均保留。无动态姿态/接触力，不夸大推断。
- 已新增并实际运行audit_rollout_motion_order.py对全部54push：8非目标违规中，原seed2三个推盒在2/5/15mm三阈值均袋先动盒后动；其余5空间违规均目标先动。MOTION_ORDER_AUDIT记录全部轨迹hash和中心距，描述时序不证明接触因果。
- NEXT_DIAGNOSTIC_PLAN：优先既有专家/策略同几何轨迹对比，区分错误接近和接触后推进不足；必要时被动接触/姿态诊断并验证control parity；据结果改专家多样布局，再合格数据训练及独立泛化。不要盲目改门/裁动作/扩采/延长训练；训练需重新核算artifact存储，最近仅3.6GiB。

## 2026-09-29 03:40 当前：原场景第三轮第二布局1/2，累计57条

- session27249本turn两次同handle确认live，relative10_original_seed2继续。layout101两条10关键帧实际显示、rawhash/quality核验保存interim_visual/original_seed2_layout101/review.json。累计57条/285独立关键帧，余layout102两条+wait三条。
- 袋通过progress.204141m，非目标盒0，maxstep.044820rad。盒任务再次先进入袋区域并带动袋.034586m，targetprogress.118569m不足且末段仍运动，三门fail保留，maxstep.077045rad。画面确认非目标移位，不用抽帧代替接触力证据。
- 第三轮当前2/4，仍非完整结果；推盒干扰在两个原布局重复，整体goal未达。下一步完成末三条与formalreview，再运行两份严格60比较和reviewaggregate，保留所有视觉担忧。

## 2026-09-29 03:38 当前：原场景第三轮首布局1/2，推盒严重带动袋

- session27249本turn两次同handle确认live，relative10_original_seed2继续。layout100两条10关键帧实际显示、rawhash/quality核验保存interim_visual/original_seed2_layout100/review.json。累计55条/275独立关键帧，余5条。
- 好：袋progress.190028m、非目标盒0、maxstep.043132rad，pass。坏：盒任务右手先进入袋区域，袋明显移位且后段侧边竖起；非目标袋.154138m、targetprogress.139017m、maxstep.085578rad，非目标/区推程/突变三门fail全部保留。无动态姿态/接触力测量，不声称量化倾角或已证根因。
- 新增视觉担忧记录在interim review，正式seed2汇总需带入；不只记录空间seed0远盒翻立。后台继续，最近空间3.6GiB，整体goal active，全60与独立泛化未完成。

## 2026-09-29 03:36 当前：原场景第二轮仅1/7，最后一轮运行

- session27249本turn同handle确认live，STATUS已进入relative10_original_seed2（19:34:48UTC）。实际显示layout102袋/盒+wait共15关键帧；interim original_seed1_last3/review与formal seed1全7review保存，全rawhash/quality核验。正式review来自两pair+last3已显示页，不谎称另显示formalpages。累计53条/265独立关键帧，余7条。
- 第二轮原场景袋0/3、盒0/3、wait1/1，总1/7（首轮5/7）。袋102progress.065945m不足，盒102完全不动；非目标均0、maxstep.059964/.050397，无突变。wait掌spread.002053/.007975m、maxstep.003025pass。原场景六push全部区/推程fail，平滑/未动非目标不等于会做任务。
- 继续最后seed2后做全60严格对照、实际reviewaggregate、好坏报告/采用判断；独立泛化仍未完成，goal active，原门/硬约束不变。

## 2026-09-29 03:34 当前：原场景第二轮第二布局0/2，累计50条实际复核

- session27249本turn两次同handle确认live，relative10_original_seed1继续。layout101两条10关键帧实际显示、rawhash/quality核验保存interim_visual/original_seed1_layout101/review.json。累计50条/250独立关键帧，余10条待完成/实际复核。
- 袋推进.138305m不足.15，非目标盒0、maxstep.060448rad；盒完全不动，袋0、maxstep.049294rad；均原zone/progressfail。画面任务手臂接近对应目标，但运输不足/没有运输，不能以手臂选择正确代替任务成功，也不从抽帧断言接触根因。
- 第二轮当前前4条0/4，首轮5/7的好结果不稳定。继续layout102/wait及第三轮，整体goal active，未放宽门/剪裁动作/改训练数据。

## 2026-09-29 03:32 当前：原场景第二轮首布局0/2，累计48条实际复核

- session27249本turn两次同handle确认live，relative10_original_seed1继续。layout100两条10关键帧实际显示、rawhash/quality核验保存interim_visual/original_seed1_layout100/review.json；累计48条/240独立关键帧，余12条。
- 袋progress.147387m未达.15最低推程、原zone/progressfail；非目标盒0、maxstep.059344rad。虽差距小仍不放宽门。盒完全不动（target0），袋0、maxstep.049247rad，zone/progressfail。画面右手接近后离开盒仍在原位；不凭抽帧断言接触力根因。
- seed0本布局袋pass变seed1fail，原场景袋也有种子敏感性；不外推首轮袋3/3为稳定能力。最近磁盘3.8GiB，后台继续后续回归；goal active，完整60与独立泛化未完成。

## 2026-09-29 03:29 当前：原场景首轮全部实际复核5/7，第二轮运行

- session27249本turn同handle确认live；STATUS已进入relative10_original_seed1（19:28:34UTC）。本turn实际显示layout101/102共20帧及formalpage1 wait5帧，分别保存interim和正式seed0review，全7rawhash/quality核验。累计46条/230独立关键帧，余14条。
- 原seed0袋3/3、盒1/3、wait1/1，总5/7。layout101盒完全不动、袋.198726m pass；layout102袋.258450m/盒.165593m均pass，非目标均0，maxstep.069330/.056340；wait掌spread.001632/.006780m、maxstep.004124pass。
- layout101画面右手靠近盒后离开但盒没动，不能凭抽帧声称已知接触力根因；layout102盒旋转运输且大topface可见。原首轮袋改善与盒短板并存，不用局部替代完整21。保留空间seed0翻立担忧。
- 整体goal active，完整60对照与独立泛化尚未完成，原门/数据/模型不变；下一步seed1/2原场景实际复核后汇总。

## 2026-09-29 03:26 当前：原场景首布局1/2实际复核，累计41条

- session27249本turn同handle确认live，relative10_original_seed0进行。原layout100两条10关键帧实际显示、rawhash/quality核验保存interim_visual/original_seed0_layout100/review.json。累计41条/205独立关键帧，余19条。
- 袋pass：progress.179353m、非目标盒0、maxstep.067819rad；盒正确右推但progress.130804m不足，原区/推程fail，袋0、maxstep.056358rad。不用原场景首两条替代全21回归结论。
- 新SPATIAL39_FAILURE_BREAKDOWN：袋18条9pass，8区/推程fail+1非目标；盒18条10pass，4非目标/6区推程/2末运动/3突变（可重叠）；wait3/3。这是门分类，不是接触根因证明。
- 剩余original评测继续，磁盘最近3.9GiB；无新训练/门修改，完整60及独立泛化未完成，goal active。

## 2026-09-29 03:24 当前：空间39条全部实际复核22/39，原场景回归开始

- session27249确认live，STATUS evaluating_relative10_original_seed0（19:22:16UTC）。seed2末layout58005近袋pass/远盒zonefail，wait实际显示formalpage2并pass；formal seed2review全部13hash保存，源review为六pair，58002用_complete。累计39条/195独立关键帧，余original21条待完成及实际复核。
- SPATIAL39_INTERIM_COMPARISON严格同39keys：relative10 22/39，coverage50 6/39，absolute10 2/39；本模型seeds9/13、7/13、6/13。近袋8/9、远袋1/9、近盒3/9、远盒7/9、wait3/3。改善明确但不足目标；保留seed0远盒58001视觉翻立担忧。
- 第三轮末远盒58005progress.189607m、袋0、maxstep.054335仍zonefail；近袋progress.367337m、盒.003948m、maxstep.067559pass；wait掌spread L.003220/R.005680m、maxstep.003786pass。
- 完整原场景回归、完整60采用判断及独立自然泛化仍未完成；不把22/39当最终目标完成。goal active，原门和硬约束不变。

## 2026-09-29 03:20 当前：第三轮第五布局0/2，远袋三条全失败

- session27249同handle确认live；58004两条10关键帧实际显示、rawhash/quality核验保存interim_visual/seed2_layout58004/review.json。累计36条/180独立关键帧，余24条。
- 远袋仅推进.004566m，区/推程fail，非目标盒0，maxstep.053493rad；近盒仅推进.001034m且maxstep.118864rad，区/突变两门fail，袋0。画面两条目标基本不动，不能等同于已证实接触/遮挡根因。
- 第三轮前10条4/10；远袋本seed0/3，三seed合计1/9，跨seed稳定性明显不足。还差58005两条/wait及original21条；完整原场景回归/独立泛化未完成，goal active，原门不变。

## 2026-09-29 03:18 当前：第三轮第四布局1/2，远盒也出现区失败

- session27249本turn同handle确认live；58003两条10关键帧实际显示、rawhash/quality核验保存interim_visual/seed2_layout58003/review.json。累计34条/170独立关键帧，余26条。
- 近袋原门pass：progress.285094m，非目标盒.002986m，maxstep.052481rad；远盒正确右移但progress.196528m未满足原稳定区门，非目标袋0，maxstep.054339rad，仍fail。后段盒大topface可见，不混用seed0翻立担忧。
- 第三轮前8条4/8，仍非整轮结论。远盒前两seed6/6不能推成所有seed稳定；继续剩余空间及原场景回归，无门修改/裁动作/新训练。goal active。

## 2026-09-29 03:17 当前：第三轮第三布局1/2，累计32条实际复核

- session27249同handle两次确认live，seed2继续。58002先完成盒后完成袋；完整两条10关键帧已实际显示，rawhash/quality核验保存在interim_visual/seed2_layout58002_complete/review.json。旧seed2_layout58002仅单盒材料、无review，正式汇总须用_complete；重复盒帧不重复计数。累计32条/160独立关键帧，余28条。
- 好：近盒右推.254527m、袋0，maxstep.079151rad接近.08但原门pass，未剪裁。坏：远袋仅推进.107649m，左手移袋后离开，仍区/推程失败，盒0，maxstep.053852rad。
- 第三轮目前3/6，仅部分结果；原场景21条回归未完成。上一条handoff人工时间03:16可能稍快于实际系统时间，本条采用系统当前时间。整体goal active，硬约束不变。

## 2026-09-29 03:16 当前：第三轮第二布局2/2实际复核，累计30条

- 本turn开始同handle session27249确认live，STATUS evaluating_relative10_spatial_seed2。58001两条10关键帧实际显示、完整quality/rawhash核验，interim_visual/seed2_layout58001/review.json保存；累计30条/150关键帧，余30条待完成及实际复核。
- 近袋通过progress.263694m、非目标盒.000305m、maxstep.054388rad；远盒通过progress.188551m、非目标袋0、maxstep.049569rad。注意progress不是绝对finalY，不因小于.20错判原稳定区门；画面远盒末段大topface可见，未见seed0那样明显侧边翻立，仍保留seed0质量担忧。
- 当前第三轮前4条2/4，非完整seed结论；后台继续，完整原场景回归/独立泛化未完成，goal active。无数据、模型、硬约束修改。

## 2026-09-29 03:14 当前：第三轮首布局实际复核0/2，主任务继续

- session27249仍为主job，STATUS evaluating_relative10_spatial_seed2；第三轮58000两条已实际显示10关键帧且rawhash/quality核验保存interim_visual/seed2_layout58000/review.json。累计28条/140关键帧，余32条待完成及实际复核。
- 远袋仅移动.009142m，左手伸向后袋后离开，区失败；近盒正确右移.222041m、袋仅.002834m，但maxstep.084217rad超过.08门，保留失败，不剪裁。两条都不能以动作方向正确代替合格。
- 第二轮formal13已完成7/13，第一轮9/13。尚未原场景21条回归，不作最终采用判断；整体goal active。

## 2026-09-29 03:12 当前：第二轮正式复核完成7/13，第三轮运行

- session27249确认live，STATUS evaluating_relative10_spatial_seed2。seed1全部13条/65关键帧已实际复核，formal review保存并核验全部rawhash/quality；12push来自4份双条interim及last_two四条页，wait单独显示formalpage2。累计26条/130关键帧，剩34条，非全视频。
- 好：seed1为7/13（seed0为9/13），近袋2/3、远袋1/3、近盒0/3、远盒3/3、wait1/1。远盒本seed三条均数字pass，关键帧未见seed0那种明显侧边翻立，但seed0质量担忧仍保留。
- 坏：58004近盒同时带动袋.129630m、动作突变.148994rad、稳定区与末段运动失败；58005近袋带动盒.074619m，失败；58004远袋推进.174990m仍未稳进区。近盒seed1三条全失败，任务干扰未解决。不得外推局部改善或放宽门。
- 后台继续seed2及original三轮，磁盘约4.3GiB；无新训练，无质量门或首帧零位等硬约束修改，整体goal active。

## 2026-09-29 03:04 当前：第二轮第三布局1/2，远袋首次通过但推盒严重干扰

- session27249确认live，relative10_spatial_seed1继续；58002两条10关键帧实际显示、完整quality/rawhash核验，interim_visual/seed1_layout58002/review.json保存。累计19条/95关键帧真实复核，第二轮当前3/6，仍非整轮结论。
- 好：远袋58002seed1通过，progress.201439m，非目标盒0，maxstep.063318；画面左手确实移袋。这是本模型当前已复核远袋首次成功，不说明远袋稳定。
- 坏：近盒58002seed1带动后袋.124589m，目标progress.204073m但未满足stablezone且末段仍运动，三原因失败保留，maxstep.063463，无突变失败。画面后袋明显右移；不能把目标末位移>.20误称稳定进区或抹掉非目标扰动。
- 其余41条仍待完成/实际复核；完整原场景回归和独立泛化未完成。整体goal active，h10/cap0/solver10/原门不变。

## 2026-09-29 03:02 当前：第二轮第二布局实际复核2/2，仍继续完整评测

- session27249确认live；58001两条完成后实际显示10关键帧、核验rawhash/quality，interim_visual/seed1_layout58001/review.json保存。累计17条/85关键帧实际复核，第二轮当前2/4，非完整seed结果。
- 近袋progress.262526m、非目标盒0、maxstep.067289；远盒progress.204281m、非目标袋0、maxstep.047186，均原门pass。画面确认手臂与目标运输；本seed远盒末段topface明显，未见seed0同layout那种明显侧边翻立，不把不同seed画面混写，也不抹去已有seed0担忧。
- 第二轮首布局两失败依旧保留，仍需剩余43条及原场景。无新训练/数据改动/质量门变化，整体goal active。

## 2026-09-29 02:59 当前：第二轮首布局实际复核0/2，首轮改善尚不稳定

- session27249同handle确认live，relative10_spatial_seed1运行。58000两条10关键帧实际显示，rawhash/quality核验，interim_visual/seed1_layout58000/review.json保存。模型累计15条/75关键帧实际复核；首轮formal13已完成，第二轮仅subset2，不要提前完成本seedreview。
- 坏：远袋58000seed1左手接近并向左移，但目标仅.000244m，几乎不动，盒0，maxstep.064253rad；nearbox目标仅.057437m且非目标袋.060566m> .015，两门失败，maxstep.073665rad。画面右手进入后袋区域、袋确实移位；无接触力/动态姿态记录，不能凭关键帧定接触根因。两条都无突变门失败，说明平滑不等于完成任务。
- 同布局seed0近盒pass在seed1变fail，随机噪声种子敏感性仍存在。继续全60，不将首轮9/13宣布稳定改善或任务干扰已解决。剩余45条仍待完整结果/实际复核，整体goal active。

## 2026-09-29 02:58 当前：relative空间首轮13全部实际复核9/13，对旧各2/13；第二轮进行

- session27249仍live，02:56:05已进入relative10_spatial_seed1。首轮最后58005近袋/远盒2/2通过（progress.282673/.220149m，非目标0，maxstep.073545/.044168），实际显示10帧并保存第六interimreview；wait实际显示formalpage2五帧，L/R掌spread.001717/.007138m、maxstep.004549，pass。
- evaluation/visual_materials/relative10_spatial_seed0/review.json已正式保存13hash：12push通过六份此前实际显示的interim共60帧，wait通过本turn显示5帧；全部rawhash/quality新核验，明确没有谎称另显示formalpage0/1。总65实际关键帧，非全视频。
- SEED0_INTERIM_COMPARISON严格同13 episode键、相同evaluation_protocol字节：coverage50 2/13、absolute10 2/13、relative10 9/13。relative近袋3/3、远袋0/3，近盒2/3、远盒3/3、wait1/1。三远袋区失败，近盒58004带动袋.037174m失败；远盒58001虽数值pass但实际翻立保留质量担忧。全部13无>.08突变。不要外推单seed结果。
- 尚余47条闭环及实际图像复核，第二轮已运行，原场景回归尚未开始。新独立泛化未做，整体goal active。不采用或扩采前先完成所有60和好坏结果报告。

## 2026-09-29 02:54 当前：第五布局实际复核0/2，出现非目标袋超限

- session27249同handle确认live，relative10_spatial_seed0仍进行。本turn实际显示58004两条10关键帧，rawhash/完整quality核验，interim_visual/seed0_layout58004/review.json保存。累计10条/50关键帧，6/10数值通过，仍无完整seed结论。
- 坏结果必须highlight：远袋58004仅推进.109207m，区/推程失败，盒0，maxstep.070224rad；本seed前三远袋58000/02/04均未进区。近盒58004目标推进.337939m但非目标袋maxXY.037174m> .015，失败，maxstep.069446rad。画面中段/后段袋位置姿态确实变动；无法仅凭关键帧区分手直接带动与盒间接碰撞，不声称已证实接触根因。
- 所以连续性改善不等于任务干扰解决。仍完成全部60及完整图像复核，不放宽非目标门。下一布局和wait尚待本seed完成，随后seed1/2及原场景。整体goal active。

## 2026-09-29 02:52 当前：第三/四布局已实际复核，累计8条6数值通过

- session27249确认live，relative10_spatial_seed0继续运行。本turn为progress：interim_visual/seed0_layout58002和58003各10关键帧实际显示、四条rawhash和quality核验、分别review.json保存。累计8条/40关键帧实际复核，尚非完整seed13，更非full60。
- 58002：近盒pass（progress.206064m、非目标袋0、maxstep.067339）；远袋仅区/推程失败（.136100m、非目标盒0、maxstep.066176）。画面显示左手确实推远袋并旋转、盒未明显移动。不能仅凭这两条远袋推进不足归因于数据。
- 58003：近袋pass（.284825m、非目标盒.002988m、maxstep.075673）；远盒pass（.206249m、非目标袋0、maxstep.051855）。画面确认任务/手臂正确，后段盒topface仍大面积可见，与58001明显侧边翻立区别记录，不把既有翻立结论套所有远盒。
- 累计前四布局6/8数值通过，两失败均远袋区门；仍保留58001远盒数值pass但视觉翻立的质量担忧。其余52条尚待完成/复核，完整结果未知，goal active。后续正式每seed材料全13/7要实际核验并汇总，不以subset替代。

## 2026-09-29 02:50 当前：第二布局实际复核2/2数值过门，远盒翻立须highlight

- session27249同handle确认live，relative10_spatial_seed0正在58002；58001两条完整。evaluation/interim_visual/seed0_layout58001/page0实际显示10关键帧，2rawhash+完整quality核验，review.json保存。累计本模型4条/20关键帧实际复核，仍非正式完整seedreview。
- 好：近袋58001左推.252328m、非目标盒0，原门pass；maxstep.078321rad接近.08。远盒58001右推.212840m、非目标袋0，maxstep.047819rad，原数值门pass。
- 坏：远盒后段实际关键帧明显翻立/侧边竖起，已记录visual_quality_concern，不能只认进区而宣称动作质量完全合格。保持原数值结果不偷偷改门；raw/trace没有动态quaternion，不声称测得倾角。以后候选采用和专家优化必须考虑此画面问题，不能忘记。
- 前两布局共3/4数值通过（远袋58000区失败），不能外推整60成功率；其余试验仍运行。目标active，需全部正式材料复核/比较及新独立泛化。

## 2026-09-29 02:48 当前：relative首布局2条已实际复核，近盒通过/远袋区失败

- session27249仍live，relative10_spatial_seed0运行中，layout58000两条完成，已进入58001。新evaluation/interim_visual/seed0_layout58000材料生成后实际显示10关键帧，2 rawhash和完整quality核验，review.json保存。仅subset2/13，不是正式seedreview或full60，自动材料目录仍待完整轮完成。
- 好：近盒58000通过，右手将盒右移并伴随转动，targetprogress.211158m，非目标袋maxXY.005734m，maxstep.073225rad；未剪动作。坏：远袋58000左手移袋约.161907m但未满足稳定越±.20m区，保持失败；非目标盒0，maxstep.067953rad，无突变失败。5关键帧可见动作，不能以图代全量物理门或接触力证据。
- 其余58条仍待完成/实际复核，完整结果未知。整体goal active；等待后续同一作业，不重复启动，不据局部1/2采用新模型。

## 2026-09-29 02:44 当前：恢复验证/审计完成，连续性有改善但20/24仍突变，闭环已开始

- 新主session27249同handle确认live，STATUS evaluating_relative10_spatial_seed0，02:42:56进入第一轮；port18777。旧93005保存后artifact磁盘故障已经恢复，禁止重训。checkpoint固定014480，所有权重保持已训练14480结果。
- 保存模型成功加载，补做完整1560帧native validation loss .008580988353790021；相对表示改变loss量纲，不直接与absolute loss比较。CHECKPOINT_STATS全部passed；EFFECTIVE_SOURCE_ACTION_CHUNKS_AUDIT验证9080×10×11=998800原始标签逐值一致、612正确padding、无跨ep/val查询，强调这是encode前source窗口。encode及savedprocessor一致性先前另有全量roundtrip和136首尾检查。
- 同8专家×3seed、原始hash和seed严格配对的CONTINUITY_COMPARISON已生成：relative20/24轨迹突变、52事件且全chunk边界/主动臂，非主动0；absolute10为24/24、127事件125边界、非主动5；absolute50为24/24、101事件98边界、非主动3。relative mean11q RMSE .0165268，boundarymean .0484066/p95 .128245，优于两旧模型但仍大量>.08失败。训练袋4/6(10事件)、盒6/6(16)；验证袋4/6(9)、盒6/6(17)。只属于teacher观测诊断，不是闭环成功。
- 完整空间39+原21评测及材料由恢复脚本继续自动执行。逐seed要实际显示65/35关键帧、核验rawhash及数值，最终aggregate prefix relative10和两个baseline比较。不能因开环改善、个别seed或物理数值通过提前宣布goal完成。
- 本turn为progress：定位W&B staging漏算、只清理经逐字节证实的截断临时副本、从保存模型恢复验证而非重训、完成新连续性比较。剩余空间约5GiB，eval前空间门已通过。原质量门与零位/腰0/无助推均保持，整体goal active。

## 2026-09-29 02:41 当前：14480已保存，W&B临时复制写满后恢复验证，严禁重训

- 主session93005已exit120并关闭：02:36:16完成14480步并保存checkpoint/last后，W&B log_policy离线artifact staging再复制模型，磁盘avail0，日志/STATUS也被截断。此次空间核算漏掉W&B临时副本，不是训练数值失败，也不是模型效果结论。
- 完整检查checkpoint内5个safetensors的header/data_offsets与文件长度一致（模型7473096344B，optimizer2195136504B），training_step=14480，last指014480。源checkpoint完整保留。对/home/user/.local/share/wandb/artifacts/staging/tmp7hnejjfq逐字节与模型前缀对照，确认5274976256B截断副本后只删除此临时文件，恢复5.0GiB；无旧数据/对照/last目录删除。SAVE_RECOVERY、STORAGE_PREFLIGHT_CORRECTION保存。
- 新活跃session27249：continue_relative_chunk10_saved_checkpoint.sh，日志/tmp/relative_chunk10_saved_recovery_20260929.log。只从现有保存模型补做native validation(未更新权重/未恢复优化器)，随后原下游stats/实际sourcewindows/teacher连续性/60闭环。STATUS recovering_saved_checkpoint_validation，recovered_validation.log已显示成功加载完整模型。禁止重跑原training脚本。
- validate_saved_relative_checkpoint.py同12验证episodes/1560帧，batch1/seed42000/bf16/原顺序、实际savedprocessor，输出原run/validation.jsonl以供下游检查。此前训练因artifact失败尚未运行该验证，不能填造loss。恢复值仍非跨表示loss比较或闭环成功。新进程不调用W&B。
- 后续仍需全部60实际300关键帧、rawhash/质量门审查和新独立泛化，整体goal active。未来空间预算必须加artifact完整副本或显式禁artifact，仅offline不足。本turn为progress（定位并恢复保存后故障），原实验参数、h10/cap0/solver10和零位/无助推硬约束不变。

## 2026-09-29 02:01 继续：实际推理入口补充检查通过，原训练仍运行

- 上一goalturn属于progress（动作编码实现+全部训练标签/processor审计+受控训练启动）。本turn确认同session93005存活，约02:01到1.3K/14480；不要重复启动，STATUS training。训练完成前无新闭环成功结论。
- 补充test_joint_relative_actions.py两个CPU测试，直接调用真实Pi05Server.infer，以stub神经输出和明确postprocessor缩放验证还原顺序/同query锚点/腰0/旧absolute输出/输入state不变；全部该文件8项通过，SERVER_INFERENCE_TESTS.log及EVALUATION_INTERFACE_AUDIT.json保存。不是完整模型或物理评测。之前15项回归仍保留，不把新文件8项与旧含重复6项相加当23独立测试。
- 只读复核run_pi05_spatial_sim.sh和run_pi05_paired_sim.sh均调用当前server和精确checkpoint；h10/cap0/solver10不变。没有改正在运行的shell脚本或生产训练代码，没有并发采集/推理GPU作业。
- 后续仍由原脚本依次完成训练/保存审计/teacher连续性/60闭环材料；实际显示及复核要另外做。总体goal active，数据多样化与独立泛化目标未完成。

## 2026-09-29 01:58 当前：相对动作10步实现/审计已过，真实训练运行

- 本goalturn为progress：实现可选joint_action_representation=state_relative_arm10（默认absolute不变）。训练在归一化前减同query q[:10]，整个chunk锚点相同；Pi05Server后处理后加回同query q[:10]。腰保持绝对action0；不裁剪/滤波、无专家/物体策略改动。注册QueryRelativeArm10随processor保存重载；server校验config和step匹配。实现hash在state_relative_chunk10_20260929_r1/IMPLEMENTATION_SHA256.json。
- prepare_relative_action_stats.py真实读取全部9080训练query的10×11标签及padding，与raw q/action逐值相同。仅有效未来步统计residual，原state stats不变；encode/normalize/decode/restore maxerror5.96046e-8。label_preflight/REPORT.json通过；未读val统计。check_relative_processor_integration.py真实68训练episode首尾共136个数字输入，实际factory+tokenizer+保存重载一致、语言state tokens与旧模型相同、padding不变，stats表示/horizon不匹配拒绝。processor_preflight/REPORT、PREFLIGHT_SAVED_STATS通过。
- 15项unittest全部通过，REGRESSION_TESTS.log保存。pytest未安装改用原生unittest；首次自定义配置重载测试用了错误PI05Config入口，改PreTrainedConfig后通过；旧padding测试fixture缺已有use_frame_loss_weights=False，补fixture后通过，没有改生产loss。这些初次失败不伪称训练失败。
- 磁盘preflight可用14.95GB，参考checkpoint9.668GB、完整eval1.575GB，含5%/25%扩余和2GiB剩余安全预算要求14.268GB，门通过，无删除。单次最终checkpoint，save_freq100000>14480；脚本在eval前再核对空间。训练不保存多个中间副本。
- 活跃主session93005，脚本run_relative_chunk10_training_evaluation.sh，日志/tmp/relative_chunk10_20260929.log，真实train.log在workflow根。01:58已step200/14480，01:57开始；输出/home/user/Documents/zoo/sim/lerobot/outputs/paired_relative_chunk10_20260929/package_sorting_pi05_1gpu_20260929_015655。STARTUP_AUDIT确认与绝对chunk10参数inventory完全相同、首epoch每episode采样完全相同。数据同coverage80、freshbase/seed42/batch1/prefix3weight16/14480步；只表示与配套stats不同。训练loss量纲有变，不当改善证据。
- 脚本后续自动保存→stats（新--stats参数）、原始998800窗口审计→同8专家×3seed teacher连续性→空间39+原21 h10/cap0/solver10→材料。正式server port18777。自动不会实际复核；必须逐seed实际显示300关键帧、核验数值/rawhash，最终再aggregate --prefix relative10。numeric_complete_actual_visual_review_required不是整体完成。
- 新compare_paired_model_results.py支持任意baseline/candidate前缀；已用旧两模型复核11/60对4/60一致(COMPARISON_PARSER_CONTROL_CHECK只是旧对照，不是新模型结果)。新eval结束后分别比较coverage/relative10及chunk10/relative10，并写完整报告。不仅超过短模型4/60，还要与50步11/60检查各任务回退；新独立布局泛化仍未做。
- 原§1零位、腰action0、assist0、质量门全部保持。整体goal active；不要重复启动当前训练，不得以启动或单项审计完成宣称整体完成。

## 2026-09-29 01:45 当前：新增三项诊断结束，下一项相对动作小对照待实现

- 梯度session54449 r1因无梯度参数断言失败已关闭/保留FAILURE；r2 session70254正常exit0已关闭。REPORT/INTERPRETATION在paired_task_gradients_20260929_r2。24对8负，mean.01995，range[-.09386,.10196]，接近正交，无强稳定负向证据；不是全训练期因果证明。48后向唯一无梯度是专家lm_head，动作使用hidden状态，因此全声明693422112梯度向量中该张量按0计，其余有限。没有optimizer或权重更新，不据此上梯度投影。
- state_relative_labels审计完成。50步相对范围变大故不采用relative50；10步范围明显变小，允许做明确对照假设，但不能保证改进。新state_relative_chunk10_20260929_r1/PROTOCOL.json已写，stage implementation_planned_not_training。下一步实现显式保存的representation选项、训练前归一化前减同query q、推理还原同query q、仅训练集有效10窗口统计，并做实际9080窗口完整roundtrip/legacy测试；未过前不得训练。
- 计划同80数据/split/base/seed42/14480steps/batch1/prefix3weight16，仅与短chunk10的4/60比较动作表示；还须超过50步11/60且无任务回退才考虑采用。正式h10/cap0/solver10和原门保持，腰action绝对0，无动作裁剪/滤波。完整60+实际300帧与新独立泛化仍需做，整体goal active。
- 当前没有训练/评测/诊断进程运行。磁盘约14GiB；实测单已保存checkpoint9.1GiB(模型7.0+training_state2.1)，不能把该数当保存峰值或忽略评测所需空间。新训练前先核实容量，不删除last目标或冻结对照。本turn只改新增审计脚本/报告/协议/handoff，未改生产训练/推理/专家。

## 2026-09-29 01:42 当前：短预测完整拒绝；继续训练数据与任务梯度诊断

- coverage_chunk10_20260928_r1 完整60条/300关键帧已实际显示并核验全部hash，STATUS complete_reviewed，REPORT.md、NUMERIC_COMPARISON、FAILURE_GATE_BREAKDOWN、ADOPTION_DECISION齐全。短预测4/60，对coverage50的11/60；空间2/39对6/39，原2/21对5/21；wait1/6对6/6。少量远袋/原盒成功不能覆盖整体退步，拒绝采用。主session47658 exit0已关闭，无模型训练/闭环评测仍运行。
- 腰state全连续性审计session49726 exit0：coverage原预测精确重放maxerror0；置零后突变101→102、24/24仍失败，不采用。报告coverage_model80_20260928_r1/waist_state_continuity/REPORT.json。
- near_observation_conflicts_20260929_r1/REPORT.json：只读68训练集/9080帧，近q且动作差>.08的袋/盒各108对，叠加固定视觉阈值后均0候选。session11185 exit0已关闭。不说明全局无歧义，不改阈值找预期结果、不删除数据。
- 新audit_state_relative_action_labels.py已结束(session18434 exit0)，报告state_relative_labels_20260929_r1/REPORT.json。训练集50步相对当前q的arm10标签可精确还原，腰仍绝对0；前10步范围变小，但50步两肘span约2.18/2.17rad，大于绝对1.758rad，故不据此启动相对动作训练。未修改训练/推理生产代码。
- 新只读GPU audit_paired_task_gradients.py 已启动，session54449，日志/tmp/paired_task_gradients_20260929.log，输出paired_task_gradients_20260929_r1。实际训练数据/processor/native flow loss，训练group03negative+07center、两类别布局、帧0/30/60、seed0/1，共24任务对，比较全693422112可训练参数梯度(无optimizer/无更新)。需确认完成、核验结果，不能把局部负cosine直接当根因；未完成前不得称有结论。
- 磁盘约14GiB；新标准训练前必须核对checkpoint临时峰值及评测空间，保留冻结基准和last目标；本轮无删除。所有§1零位/腰action0、assist0、h10/cap0/solver10及原质量门保持。整体goal active，任务干扰和独立布局泛化仍未解决。

## 2026-09-29 01:24 当前：短预测原第二轮0/7实际复核，最后一轮运行

- session47658同handle确认live，01:23:05进入evaluating_chunk10_original_seed2。original seed1的35关键帧实际显示、7 rawhash与指标核验，review已保存。六推动全区失败（四条另突变），box0100中段翻转，wait右掌drift.0156m失败，不放宽.015门。原前两seed0/7+0/7。
- 本模型已实际复核53/60条265关键帧，剩最后7条35帧。空间2/39已完整，原当前0/14；完成最后seed后运行aggregate_model_visual_reviews.py、全60FAILURE_GATE_BREAKDOWN、解释NUMERIC_COMPARISON并写REPORT，最后STATUS complete_reviewed。不要把候选拒绝或审计完成等同整体goal完成。
- 无新训练、专家策略变化或数据删除；goal active，下一干预仍需以完整证据安排。

## 2026-09-29 01:18 当前：短预测原场景首轮0/7已复核，第二轮进行中

- session47658同handle确认live，01:16:52进入evaluating_chunk10_original_seed1。original seed0全部35关键帧实际显示并核验完整数值/hash，review在evaluation/visual_materials/chunk10_original_seed0。总0/7：box0100/0101仅突变，三袋和box0102突变+区；wait左掌drift.0207m。无非目标超限。本模型累计46/60条实际复核，余14条70帧。
- 当前空间2/39已完整，原第一轮0/7，不支持短预测采用；继续原seed1/2和完整60比较，不提前结束或放宽质量门。无新训练/策略变体，整体goal active。

## 2026-09-29 01:12 当前：短预测空间39全部复核2/39，原21开始

- session47658仍live，01:10:38进入evaluating_chunk10_original_seed0。空间三seed2/13、0/13、0/13，全部195关键帧已实际显示、三份review+39 rawhash验证。SPATIAL_INTERIM_COMPARISON.json和SPATIAL_FAILURE_GATE_BREAKDOWN.json保存，后者仅空间，最终60另存FAILURE_GATE_BREAKDOWN。
- 短chunk空间袋1/18（coverage50 2/18）、盒0/18（1/18）、wait1/3（3/3），总2/39对6/39。新增seed0远袋58002一次，失去seed2近袋58003/58005、seed0近盒58002及seed1/2wait。不是改善。三轮推动36条仅1通过。
- seed2实际复核：近盒58000仅突变失败，其余11推动全区失败；近袋58005改推盒.2111m，远盒58005带动袋.0192m，远盒58003竖起；wait左掌drift.0177m。画面与数值均保留，不能只看缩略图等待似稳而放行。
- 原21尚待运行/实际复核，不提前complete_reviewed；全部60后使用aggregate_model_visual_reviews.py --prefix chunk10核验六份review再写最终报告。短chunk开环127事件及当前闭环退步均不支持采用，完整对照继续。无新训练/采集/删文件，goal active。

## 2026-09-29 00:59 当前：短预测第二轮0/13已真实复核，第三轮运行

- session47658仍live，已进入chunk10_spatial_seed2。seed1全部65关键帧实际显示、完整指标与hash核验，review在evaluation/visual_materials/chunk10_spatial_seed1。前两轮2/13+0/13=2/26，coverage50对应3/26。
- **明显退步**：seed1三条近袋58001/58003/58005后段改推后盒，非目标盒位移.2074/.1921/.1951m，画面确认；所有12推动均目标区失败。远盒58001/58003画面竖起翻转。远袋58002缺持续目标接近。等待左掌drift .0232m失败；缩略图看似稳定不得覆盖数值门。此前seed0另有掌桌proxy8帧和误碰。
- 短chunk暂不适合替换现有模型，仍完成预设空间39+原21和实际画面复核，保留坏结果；不剪动作或改质量门，不选择性停止失败seed。无新训练、数据扩采或专家变体。整体goal active。

## 2026-09-29 00:46 当前：短预测首轮实际复核2/13，第二轮运行

- session47658仍live，00:44:35进入evaluating_chunk10_spatial_seed1。chunk10首轮13条×5帧已实际显示65关键帧，review在evaluation/visual_materials/chunk10_spatial_seed0，rawhash全核验。只有远袋58002和wait通过，盒0/6。首轮与coverage50同2/13但新增远袋、失去近盒58002；SEED0_INTERIM_COMPARISON.json保存。
- 坏结果：11条失败推动全部目标区失败，无仅突变案例（coverage50同seed有5）；近盒58004使袋移动.0477m、远盒58005使袋.0173m；近袋58003掌心/桌重叠proxy8帧，不能称接触力证据。远盒58001画面可见翻转竖起。短chunk当前不支持采用，但继续完整60，不选seed。
- 其余47条尚待运行/实际复核，后续仍按六份review汇总+完整比较。无新训练，无专家策略改动，无数据扩采或删除。总体goal active，禁止凭首轮总数相等宣称任务达成。

## 2026-09-29 00:37 新只读动作尺度证据；chunk10闭环仍运行

- session47658确认live，仍chunk10_spatial_seed0。上一turn完成coverage80整60报告及放行，本turn未改训练/数据/推理。总体goal active。
- 新audit_action_dimension_scales.py及chunk10workflow/ACTION_DIMENSION_SCALES.json，用同24 rawhash/seed、相同coverage80训练stats分析保存预测。肘范围约1.758rad，腕.134–.142rad；同物理误差右腕/右肘的归一化平方误差系数比173.18。但实际腕归一化误差总占比仅约7–8%，不能说训练被手腕主导。coverage两肘实际平方误差42.4%、60/101突变；chunk10两肘48.8%、76/127突变。只分析推理动作误差，不等同测量native训练flow-velocity loss，不构成因果证明。未启新维度加权训练。
- 只读检查delta_action_processor.py是笛卡尔teleop增量字典，不是现成11关节相对状态动作编码，未改表示。现有绝对角语义和归一化仍保持。
- 下一步仍按完整chunk10六seed评测、实际看图、同60比较推进，不重复旧语言LoRA/恢复方案、不剪动作、不提前宣称改善。

## 2026-09-29 00:32 当前：coverage80完整60已复核，chunk10闭环已开始

- 主session21004已exit0并poll关闭。coverage_model80_20260928_r1/STATUS complete_reviewed，REPORT.md、NUMERIC_COMPARISON、FAILURE_GATE_BREAKDOWN、visual_review齐全。全部60×5=300关键帧实际显示，六份review+rawhash和quality/inventory严格核验，aggregate_model_visual_reviews.py成功。最后原seed2仅wait1/7，推动六条全部区失败；box0102中段竖起明显。原三seed2/7、2/7、1/7。
- 最终coverage80空间6/39（袋2/18盒1/18wait3/3），原5/21（袋1/9盒1/9wait3/3），合计11/60。prefix为5/39+2/21=7/60。推动共5/54对旧3/54，wait6/6对4/6；空间推动仍3/36。远袋0/9远盒0/9，未达到任务干扰/多样化泛化目标。数据与训练步数同时翻倍，非纯数据归因；已重复布局仅开发基准。
- session47658已解除等待，00:31:31进入evaluating_chunk10_spatial_seed0；port18776服务器ready(pid3190359)。脚本自动同空间39+原21、h10/cap0/solver10，再数值对照。每seed材料在chunk10workflow/evaluation/visual_materials/chunk10_{spatial|original}_seedN，需要另行实际显示并存review；未复核前禁止complete_reviewed。日志/tmp/coverage_chunk10_20260928.log，分seed日志在evaluation。
- chunk10训练及998800标签审计已过，但同专家24条127突变比coverage101更差。完整闭环结论仍未知。没有新训练正在进行，无新增专家物理变体；磁盘16GiB。整体goal active，不以本模型复核完成或下一作业启动代替终点。

## 2026-09-29 00:24 补充：原场景第二轮实际复核完成

- coverage80主session21004已evaluating_coverage_original_seed2（00:22:54开始）。original seed1为2/7（box0100+wait），35关键帧已实际显示及rawhash核验，review写入evaluation/visual_materials/coverage_original_seed1。bag0100/box0101仅突变；bag0101/0102突变+区；box0102末段可见竖起/翻转，数值为区失败、无突变。全部53/60真实复核，剩原seed2七条35帧。
- chunk10 session47658同handle确认live，仍trained_waiting_for_coverage80_review；00:16:50起最多等2h。不要提前放行，不重启训练。其127边界问题证据已记录，完整闭环仍待执行。旧语言LoRA8/21与恢复先导10/21等已有实验，未开启重复方案。
- 本turn新增第二轮真实复核，属progress。整体goal active，最终独立泛化未完成。

## 2026-09-29 00:19 当前：短预测训练及审计完成，连续性更差；主原场景第二轮进行中

- session47658已完成chunk10训练14480步、checkpoint保存于lerobot/outputs/paired_coverage_chunk10_20260928/package_sorting_pi05_1gpu_20260928_232338/checkpoints/014480/pretrained_model。native val1560 loss .0057539875；窗口10/50不同，不能直接比较loss。checkpoint统计40/40相同训练集正确；EFFECTIVE_ACTION_CHUNKS_AUDIT真实9080×10×11=998800标量逐值一致、612终端padding、无跨episode或valquery。
- **坏结果**：同8专家×3seed教师观测h10拼接仍24/24突变，共127事件（125边界），coverage50为101（98边界）；主动臂122、非主动5。CONTINUITY_COMPARISON四模型严格rawhash/seed对齐。平均RMSE .02065略低于coverage .02130，但边界mean .07347/p95 .16976比coverage .06064/.14560更差。REPLANNING_PHASE_ERROR：短chunk offset0 RMSE .01542、offset9 .02983；coverage .01863/.02596。不支持仅缩预测窗解决问题，尚需闭环检验。
- session47658现在trained_waiting_for_coverage80_review；自动等待2小时，从00:16:50开始，要求coverage80/STATUS complete_reviewed且visual_review全部60hash匹配才启动chunk10闭环。无训练仍运行，主要GPU为主coverage80评测。
- 主session21004已evaluating_coverage_original_seed1。original seed0 2/7（bag0101+wait），35关键帧实际显示并保存review。bag0100/box0100/0101仅突变；bag0102末端仍移动；box0102突变+区失败。未见非目标超限。本模型累计空间39+原7=46条实际复核，仍差原seed1/2共14条70关键帧，不能提前汇总放行。
- 16GiB可用，模型已保存。无删文件，无新训练/专家变体。下一步完成原14复核和完整60比较，按脚本让chunk10闭环跑完并实际看图；不要据坏开环结果伪造闭环结论。整体goal active，最终独立布局泛化仍未达成。

## 2026-09-29 00:10 当前：空间39全部实际复核，原21进行中，短预测训练收尾

- 主session21004正在evaluating_coverage_original_seed0（00:08开始），此前空间seed0/1/2分别2/13、1/13、3/13，全部195关键帧已实际显示，当前仅空间三份review，原三份尚待。共39 rawhash已核验，SPATIAL_INTERIM_COMPARISON.json保留证据；勿将STATUS提前改complete_reviewed，chunk10闭环需全部60复核。
- 空间coverage80 6/39：袋2/18（prefix3/18，失去seed0/58002）、盒1/18（prefix0/18，新seed0/58002）、wait3/3（prefix2/3，新seed2）。推动总通过仍3/36，不可宣布实质任务改善。seed2袋58003/58005及wait过门；box58004误碰袋.0571m，seed1同布局.0651m。
- SPATIAL_FAILURE_GATE_BREAKDOWN：袋16/18突变、6仅突变、10目标区失败、0非目标超限；盒15/18突变、7仅突变、9目标区失败、2非目标超限、1末端运动。辅助分类不改失败，不剪动作。
- chunk10 session47658约13K/14480训练正常，尚未保存checkpoint；保存后脚本自动真实10窗口审计、同8专家×3seed连续性，然后等待coverage80完整review。服务器读取config.chunk_size、collector接受10输出并保持h10，已核查，无需接口改动。训练/评测未重复启动。
- 当前等待正常计算，不是blocked。之前数轮为已核验同handle的等待，本轮新增第三轮完整画面复核及空间汇总，属progress。无新专家变体、无删文件。目标active，原场景回归、短chunk对照、真正独立布局泛化仍未完成。

## 2026-09-28 23:55 继续：同观测预测片段误差分析完成

- 上一目标turn归类progress：完成seed1实际65关键帧及hash绑定复核、新连续性比较与汇总核验。本turn已poll同session21004/47658均live，未重启。
- 新analyze_replanning_phase_error.py只读精确rawhash标签+保存predictions，三模型同24对齐。REPLANNING_PHASE_ERROR.json在coverage80根。专家边界最大step .03085rad；coverage预测边界max .23376rad，原门.08。coverage10个执行offset RMSE从.01863增至.02596rad；prefix .02046→.02962；uniform .02081→.04005。此为描述性分解而非随机噪声或数据问题的因果证明，未改动作或验收；chunk10出审计后可以同脚本加第四报告，新文件保存。
- 主coverage80仍seed2，chunk10仍训练，两者已确认同handle存活。完成本轮后继续原21和实际复核，再放行chunk10闭环。没有更多新训练/专家变体；不要重启现有作业。总体goal active。

## 2026-09-28 23:50 第二轮已真实复核，第三轮开始

- coverage80 seed1完整1/13仅wait，全部65关键帧实际显示并保存hash-bound review；5推动仅突变。box58004误伸向后袋并使袋移动.0651m；bag58005后段伸向盒但盒XY0，不可称实际推错盒。bag58002目标位移0。空间前26条合计3通过，主session21004已seed2；原21待跑。
- chunk10 session47658继续训练约7K/14480；不要中断或另启重复训练。全目标仍未完成。

## 2026-09-28 23:48 补充诊断与复核工具

- coverage80第二seed推动12条均未通过，wait尚未完成，完整材料待生成；第一seed已真实复核2/13。chunk10约7K/14480正常训练，显存约24/49GiB。仍需持续主60复核，再短chunk60；未结束任务。
- compare_replanning_continuity.py同24 rawhash+seed严格对齐三模型已存预测：uniform99事件/93主动臂、prefix97/97、coverage101/98；边界事件99/97/98。均值动作RMSE .02903→.02403→.02130，但超限未解决，不能只看平均改善。结果coverage80/CONTINUITY_COMPARISON.json。此脚本可在chunk10审计完成后加入第四报告比较，不要覆盖旧结果。
- waypoint_reachability_map_20260928_r1已完成，只做离线诊断。INTERPRETATION.md强调专家press实际容许X误差110mm，不要求精确点可达；7/63精确点低残差不得等同仅7slot可用，远端有真实成功轨迹。全局不可达/避障/力学无结论，不扩采。
- 新aggregate_model_visual_reviews.py仅验证六份人工实际显示后的review，不替代看图；核对每份inventory/rawhash/quality及全60实际目录，输出合并review但不改STATUS。已验证prefix60通过，coverage80未复核完整时拒绝且不产出。完成全部材料后可用--workflow ... --prefix coverage或chunk10 --out .../visual_review.json；完整解释报告后另行设置complete_reviewed。勿提前放行。

## 2026-09-28 23:40 当前：覆盖模型已保存并评测，短预测对照训练中

- 主session21004：coverage_model80_20260928_r1已14480步训练完成，checkpoint为lerobot/outputs/paired_coverage80_20260928/package_sorting_pi05_1gpu_20260928_222718/checkpoints/014480/pretrained_model。native val1560帧loss .0044221。9080×50×11真实标签4,994,000逐值一致，saved及实际loaded stats40/40正确；参数清单不变。24条专家观测拼接仍全部突变，101事件/98边界（prefix97事件），未解决连续性。
- 当前evaluating_coverage_spatial_seed1。seed0 2/13：近盒58002和wait通过，袋0/6；5条推动仅动作突变失败，仍算失败。65关键帧已实际显示复核，review在evaluation/visual_materials/coverage_spatial_seed0。全部60最终数值和300关键帧尚未完成；整体未达标。
- session47658：run_short_chunk_training_evaluation.sh，coverage_chunk10_20260928_r1实际训练约5K/14480；相同80条数据、采样、seed、步数，只把训练/预测chunk50→10，实际执行h10仍10/cap0，不平滑。MATCHED_TRAINING_PREFLIGHT通过同参数及首epoch采样计数。新DECISION明确取代旧NEXT_DECISION_DRAFT仅关于启动时间的等待条件；候选闭环仍等待coverage80全部60实际复核和STATUS complete_reviewed，并验证visual_review全部hash。不要误称短chunk未启动。训练脚本新增可选chunk参数默认50，真实窗口审计适配10/50；备份在chunk10workflow。配置预检查10窗口998800标签一致，不是已训练checkpoint审计。
- CPU session16170 waypoint_reachability_map_20260928_r1已产出63slot REPORT；当前专家点位三起点IK，需谨慎解释：不含朝向、碰撞、受力、整段动态；局部残差不证明全局不可能，零残差不代表成功。尚未由此扩采，training_ready=false。
- 所有共同准备/后段反馈物理诊断已结束，仍隔离且不入训练；后段反馈4/8较对照7/8更差，拒绝。无新的专家物理变体在运行。
- 剩余磁盘33GiB，短chunk尚未保存，后续预计下降约17GiB；保留原模型和对照、不删除。新数据首帧11q/action零位、腰动作0、无助推、原质量门均保持。整体goal active，需完整闭环与真正新布局泛化，不以启动作业结束。

## 2026-09-28 23:11 当前：覆盖模型训练收尾，只剩主训练及保存后审计等待

- session21004仍在run_coverage_training_evaluation.sh，约13K/14480，run目录lerobot/outputs/paired_coverage80_20260928/package_sorting_pi05_1gpu_20260928_222718。输出workflow demo/coverage_model80_20260928_r1。数据80条10640帧，9080train/1560val；同prefix3权重16，步数随数据翻倍，不能仅归因数据。h10/cap0/solver10不变。保存后自动39空间+21原场景并生成材料，实际300关键帧还需另行复核。
- session43552：run_coverage_posttrain_audits.sh正在等待checkpoint.txt；日志/tmp/coverage_posttrain_audits_20260928.log。新checkpoint后自动检查9080真实future50动作窗口，再同candidate07train/candidate14val共8专家×3seed的h10教师观测连续性。脚本audit_demonstration_replanning.py已改为读取checkpoint真实repo_id，适配coverage80；原算法不变。该helper没有ERR状态trap，若异常需按session/log手工记录失败，不要只读stale阶段。
- 后段反馈session51964完成并拒绝：tail_feedback_20260928_r1，8条4通过，近4/4远0/4，对照7/8；40关键帧实际复核+完整hash。BASELINE_COMPARISON/REPORT/STATUS complete_reviewed_rejected。前段物理repeat有小幅q差（首组近max.00108rad，远pretrigger.000215rad），不能宣称逐位相同。无更多专家变体在跑，所有诊断不入训练。
- 视频对照session86200已完成：8专家seed0，原RGB36次突变、真实训练解码37次，8/8均突变；128帧mean像素MAE1.268/255，预测first10变化RMS均值.00217rad。不支持压缩是连续性主因。DATA_DIAGNOSIS_UPDATE已保存。
- FAILURE_GATE_BREAKDOWN完整：prefix空间袋3/18通过、2条仅突变；盒0/18通过但5条仅突变（seed0近盒3条，seed2远盒2条），其他13条目标区/推进不足。原场景推动无仅突变案例。辅助分类不改原失败判定。
- 覆盖位置图coverage_positions.png及COVERAGE_POSITIONS.json：28个独立push布局；旧X.441–.469/Y±.146，新X两簇.361/.507/Y±.014。两类空间XY配对只在空间子集成立，合并后非全局类别位置均衡、不是任意摆放。
- NEXT_DECISION_DRAFT.json approved_for_training=false：只有当前60完整数值+实际复核+连续性诊断后，才考虑预测/训练chunk50→10的单因素候选；实际执行h10仍10，不是改验收。尚未改训练接口或启动短chunk训练。不要跳过当前结果。
- 整体goal active，任务干扰及新独立泛化未解决；剩余磁盘约49GiB，模型尚未保存所以后续会下降。训练完成后持续实际评测复核和决定下一干预，不得只启动作业就结束。

## 2026-09-28 22:54 当前：覆盖训练半程，准备段15/16但余量不足，后段反馈诊断中

- 主训练session21004正常，coverage_model80_20260928_r1/train.log约7K/14480，约50GiB可用（尚未保存新checkpoint）。实际prefix_sampler审计通过9080train，无valdraw，完整首epoch起始推动1787、wait1400；最终训练含部分epoch，不宣称全run严格任务计数相等。后接60条h10/cap0评测和实际画面复核。
- 共同20帧准备段合计16条15通过、4完整组3通过，全部80关键帧已实际复核：shared_preparation_4/4、variation7/8、positive4/4。首20q跨组差<1e-9，动作相同/物体XY0。全部仍diagnostic/training_ready=false，未扩大正式采集。
- **分层标注错误已显式纠正**：variation原protocol误称candidate10_positive，实际candidate10_center；原字节未改，PROTOCOL_STRATUM_CORRECTION.json记录，后补真正candidate05_positive四条67200/1。保留中心重复与所有失败。旧22:29段“正Y”描述已被本段更正。
- 负Y远盒67101最终signedY=.199116，差.884mm；X向远端漂5.53cm，非目标袋XY0，画面未见被前方物体堵住。中心67103虽然过门，区余量仅1.52mm；正Y67201余量7.98mm，故不凭15/16扩正式数据。中心67001余量15.3mm。
- CONTACT_GEOMETRY_COMPARISON.json位于shared_preparation根：四个远盒FK重新对照实测掌心<1e-4m，失败67101手盒接触候选最后129帧，130之后掌心与盒XY相差约7–9cm；其余仍有候选。候选非力/冲量，不能说已测得接触力。
- 新session51964：run_tail_feedback_diagnostic.sh，demo/tail_feedback_20260928_r1，日志/tmp/tail_feedback_20260928.log。隔离collector及sorting_cartesian_tail_feedback_diagnostic.py；原生产collector/expert未改。共享准备20不变，远物体扫动>=30步且已推动>=8cm才切后段Y跟随，lead4cm/6mm每步/12帧渐入，达到signedY>=max(.23,start+.18)hold。近物体原轨迹不变。中心+负Y完整8条67300–67303，无助推/原门/160帧，全部诊断隔离。触发边界、镜像方向及步幅helper检查通过。接下来实际复核及与原近物体逐值对照。
- small_state_perturbations诊断session43143完成：traincandidate07+val14的10/30/60帧24点，原观测、腰置零/反号、臂std.005rad(截.01)、腰+.0005各24/24仍匹配任务及近远分支；单点动作最大变化约.098rad。不能认定小扰动直接切换任务，也不改正式输入。
- ROLLOUT_STATE_COVERAGE只读：真实空间540个replan帧均超专家val95近邻距离.00429；成功45帧平均.02368、失败495帧.02709，差异不够作因果结论。原场景更偏，但几何本来缺训练覆盖。最近状态标签非模型真实选择。
- 新独立session86200：audit_video_inference_parity.py，prefix模型上8专家轨迹seed0，同RGB原帧与真实LeRobot解码帧、相同q/prompt/噪声比较h10预测；检查压缩敏感性。日志/tmp/video_inference_parity_20260928.log，输出prefixworkflow/video_inference_parity。正式训练和RPC输入未改。
- 旧90132/91588/89177/5089/43143等均exit0并poll关闭。整体goal仍active，模型任务干扰及独立泛化未解决。

## 2026-09-28 22:29 当前：80条覆盖模型训练中，准备段扩大复验

- prefix40全部60评测完成，STATUS complete_reviewed，全部300关键帧实际复核并rawhash核验。空间5/39（袋3/18盒0/18wait2/3），原2/21（全部推动0/18，仅wait2/3）。REPORT.md完整。原session90132结束，不再运行。
- 新主session21004：run_coverage_training_evaluation.sh，根demo/coverage_model80_20260928_r1，日志/tmp/coverage_model80_20260928.log，真实train.log已到320/14480。数据lerobot/lerobot_sim_paired_coverage80_20260928，80条10640帧/9080train/1560val；同base、seed42、batch1、专家only、前三帧权重16。步数随数据翻倍，维持同名义samples/frame但计算预算不同，不能纯数据归因。正式h10/cap0不变。输出lerobot/outputs/paired_coverage80_20260928。训练后自动stats+39空间+21原场景+材料+严格比较，仍须实际复核。
- shared_preparation_20260928_r1完成4/4原门、20关键帧实际复核。前20action四条逐值相同、q最大差2.33e-10rad，物体前20XY位移全0；首帧/腰0，保持无助推。STATUS complete_reviewed_feasibility_pass，diagnostic/training_ready=false。不是模型学习结果。
- 新session89177：run_shared_preparation_variation.sh，根shared_preparation_variation_20260928_r1，日志/tmp/shared_preparation_variation_20260928.log。训练candidate03负Y及candidate10正Y几何，四布局67100–67103共8条，同共同20帧准备/160总帧/原门。全部记录，失败不重试，不用heldout调专家。完成后需8条实际复核及前缀一致性，再决定是否准入新正式数据。
- 同期GPU约15.5/48GiB，训练与sim分进程。没有旧诊断推理还在跑。整体goal active，勿以新4/4或启动训练当完成。

## 2026-09-28 22:22 续作：空间5/39，原场景回归及共同准备段诊断进行中

- 主session90132已完成空间39：prefix5/39（袋3/18、盒0/18、wait2/3），uniform1/39。三轮全部195关键帧实际复核，review在evaluation/visual_materials/prefix_spatial_seed0–2。近盒指令后续仍可转向后袋，初始分支正确不等于持续正确。
- 原场景seed0/1各1/7（均仅wait），70关键帧已实际复核，seed2运行中。主STATUS evaluating_prefix_original_seed2；未完成完整60对照，不能宣称目标达成。主日志/tmp/spatial_prefix_experiment_20260928.log。
- 推理替代诊断均已结束：固定重复噪声更差；半幅噪声仅盒改善袋更差，零噪声更差；内部求解20步teacher-forced突变114次对默认10步97次。全部未采用，正式仍h10/cap0/solver10。原uniform99次。
- EFFECTIVE_ACTION_CHUNKS_AUDIT通过：真实LeRobot4540训练帧×50×11共2497000标签逐值一致、无跨episode/验证查询，1666终端padding正确。未发现标签窗口/导出错误。
- coverage_union80_20260928_r1已转换审计通过、未训练。数据lerobot/lerobot_sim_paired_coverage80_20260928：80eps10640frames，68train9080/12val1560。原普通40+空间40，不创造新几何，原类别位置相关仍存在，不能称全局平衡。
- 新session91588：run_shared_preparation_diagnostic.sh，4条诊断67000/67001，复制训练candidate07原几何与seed。隔离fork collect_shared_preparation_diagnostic.py，前20帧共同平滑抬双掌约3cm，首帧仍零，余140帧原专家。源码/布局hash、关节限位已核对，原collector未改。所有role diagnostic/training_ready=false，绝不直接导出。日志/tmp/shared_preparation_20260928.log。完成后需测量前20q一致性/物体稳定、原质量门及实际20关键帧复核。
- 固定橡胶手没有夹紧自由度，此诊断只测试准备/接近，不能叫抓取。整体goal active，数据/模型/新独立泛化均未达最终目标。磁盘约50GiB。

## 2026-09-28 当前：起始采样修复开环任务/位置选择，闭环连续性仍失败

- 主session90132仍在run_spatial_prefix_experiment.sh，当前prefix_spatial_seed0已完成10条推动、1条通过，待最后布局及wait。前两布局有盒推进.23m仅动作突变失败，袋仍有扰动盒/推程不足。首组10关键帧已实际复核：early_visual_seed0_layout58000/review.json，后续完整13条材料还需实际看。
- **好结果**：新prefix模型初始近远分支train72/72、val12/12（uniform42/72、6/12）；全11关节左右任务及距离分支也84/84。原盒指令13/42更近袋任务→0/42。frame30专家RGB+q仍84/84。BRANCH_COMPARISON.json完整；只是一training seed和一validation几何组的开环诊断，不是闭环成功。
- 新初始SENSITIVITY：噪声/换图动作变化比train袋.271盒.192、val袋.370盒.307，原约1.65/3.68/3.40/5.22。图像条件增强，噪声影响下降。
- **坏结果/排除项**：独立replanning_noise_audit对首组2条逐项精确复现原50步预测（maxerror0）；每次复用初始噪声使盒突变.103→.278、袋.133→.194，不能采用这简单策略。主服务及正式评测未改变。session13489已结束。
- 两模型的demonstration_replanning_audit均完成：train candidate07 + val candidate14共8episodes x3seeds，在专家每10帧RGB+q上重预测并拼接前10；uniform24/24有99次超限，prefix24/24有97次，全部在边界。prefix动作RMSE约.023-.025低于uniform尤其盒.032，但连续性仍不达标，不能只归因于新采样或闭环偏离。session15966/30463已结束。
- 正在独立只读求解精度诊断session26089：同prefix模型/相同专家观测/seed，仅num_inference_steps20（执行h10不变），输出demonstration_replanning_steps20_audit，日志/tmp/spatial_prefix_demonstration_steps20_20260928.log。当前正式60条仍默认求解10、h10/cap0不变；不要改正在跑的脚本或服务器。
- checkpoint：lerobot/outputs/paired_spatial_prefix40_20260928/package_sorting_pi05_1gpu_20260928_210152/checkpoints/007240/pretrained_model；7240训练完成，780帧native val loss.00673197079（uniform.0070353），参数清单相同/训练stats通过，磁盘52GiB左右。主日志/tmp/spatial_prefix_experiment_20260928.log。接下来seed1/2空间及原21自动串行；材料在evaluation/visual_materials/prefix_{spatial|original}_seedN，由runner直接生成，不用旧watcher。
- 同期只读COVERAGE_UNION_PREFLIGHT验证ordinary40+spatial40的80raw哈希/零位/腰0/无助推/原split，无评测ID混入，未合并或新训练。旧X.44-.47/Y±.13-.15与新X两簇.36/.506/Y±.014覆盖不同，采样不创造旧布局覆盖。后续根据完整结果单独决定覆盖与连续性改进，整体goal仍active。

## 2026-09-28 当前执行：起始帧采样对照训练中，session90132

- 前轮session9626与材料session98371均exit0。comparison STATUS complete_reviewed，60条x5关键帧实际复核+哈希全部核对。最终新空间1/39对旧0/39；原场景新4/21对旧10/21，盒0/9对7/9、袋3/9对3/9、wait1/3对0/3。不得替换旧模型或宣称改善达标。REPORT.md和NUMERIC_COMPARISON.json已完整。
- 已完成证据评估，激活demo/spatial_prefix_experiment_20260928_r1/prefix_sampling_policy.json（原draft保持false不改）。DECISION.json绑定原因和风险；baseline比较与visual_review哈希绑定policy。run_spatial_prefix_experiment.sh启动前核验60旧raw复核hash、40训练rawhash、磁盘和原导出审计。
- 当前训练session90132，主日志/tmp/spatial_prefix_experiment_20260928.log，训练日志demo/spatial_prefix_experiment_20260928_r1/train.log；output lerobot/outputs/paired_spatial_prefix40_20260928/package_sorting_pi05_1gpu_20260928_210152。已到280/7240；真实prefix_sampling_audit通过，首epoch推动前三帧903次，wait700次不变，validation隔离。训练目标同base/同40数据/seed42/7240步/优化器，不从前模型续训，唯一干预episode内部采样。
- 训练后脚本自动检验参数清单、780验证帧与checkpoint stats，再独立初始及frame30分支诊断（含左右任务匹配），然后prefix_spatial_seed0–2共39+prefix_original_seed0–2共21，均h10/cap0/原门。各seed结束自动生成关键帧材料；不是实际复核。输出evaluation/下，必须实际打开图再写review。无需启动旧材料watcher（它只认spatial_名称且已结束）。
- compare_sampling_evaluations.py最后对比本轮uniform空间40与prefix模型，明确复用58000系列已是开发基准，不是新独立泛化证据。整体goal active，模型改进与独立布局验证未完成。
- 采样已知代价：7240步预演中后段唯一帧2706/3768（71.8%），前三帧1413次，全部unique3478/4540，wait700全覆盖；保持的是完整epoch各episode抽样数，7240含不完整epoch。原场景盒布局仍缺训练覆盖，采样不创造新几何。不要夸大因果或泛化。

## 2026-09-28 当前：空间新模型1/39；采样对照草案已准备，尚未启动

- 当前队列9626已完成新模型空间39，结果袋1/18、盒0/18、wait0/3；三个seed为1/13、0/13、0/13。各65关键帧已实际检查并保存comparison/visual_materials/spatial_spatial_seedN/review.json。原场景首轮4/7（袋3/3盒0/3wait1/1）已复核，第二轮0/7刚结束，第三轮正在跑；材料watcher98371仍运行。
- 完整ACTION_CONTINUITY_FULL.json：36推动里24条突变、45事件全部在h10边界，块内最大.06243rad；突变前同关节跟踪误差最大.04467rad。原门不变。
- 独立诊断已结束：initial_visual_branch_audit、demonstrated_frame30_branch_audit，各84预测，未用heldout；BRANCH_DIAGNOSIS.json对照起始分支48/84与frame30专家RGB+q下84/84。注意frame30同时改变图像和状态，是teacher-forced，非图像纯因果实验。
- 全11关节四专家分支TASK_CHOICE.json：初始盒指令42次中13次更接近袋任务，袋指令42次全部匹配任务但近远仍不稳；frame30所有84次任务与距离分支匹配。SENSITIVITY.json显示噪声影响大于换图，尤其盒任务。
- demo/spatial_prefix_experiment_20260928_r1/PLAN.md、STATUS为draft。同base/数据/seed42/7240步，仅推动前三帧权重16；每完整epoch各episode精确总数、wait700保持，7240包含不完整epoch不能宣称全run计数严格相同。原草案approved=false，尚无prefix_sampling_policy.json，不可启动。
- 准备scripts/run_spatial_prefix_experiment.sh（bash-n通过）：要求当前baseline STATUS complete_reviewed和6份真实hash绑定review后才能训练；新output paired_spatial_prefix40_20260928；自动训练→初始/frame30诊断→39空间+21原场景→数值对照，画面必须另行实际复核。6项采样单测通过，默认训练无变化。对照复用布局仅是开发基准，最终需新增独立布局。
- 下一步复核当前original_seed1/2、生成完整报告并判断后，复制草案为明确激活policy并留决策证据，再启动单因素实验。整体goal仍active，不得将草案或启动当完成。

## 2026-09-28 续作：新模型出现随机种子依赖，起始视觉分支诊断失败

- 当前完整评测仍由session9626运行，已到spatial_seed2；seed0 **1/13**、seed1 **0/13**，两轮各65关键帧已实际显示检查，review.json绑定raw哈希。seed0远盒误推前袋，seed1近盒误推后袋，表明随机种子影响明显；不是单一固定近/远偏向。仍待seed2和原场景21条，不能认定改善。
- ACTION_CONTINUITY_PROGRESS.json：前24条推动有17条出现>.08rad突变，29个事件全部在h10重新预测边界；禁止用动作限幅或改horizon掩盖。
- 独立初始图像反事实已完成：initial_visual_branch_audit/REPORT.json，固定q0/指令/噪声，只换类别位置图像；train72次仅42次更接近正确专家分支、完整配对6/36；val12次6次、完整配对0/6。是开环轨迹距离诊断，不是闭环成功率；图像有影响但不足以稳定选择目标。未使用heldout输入。
- 训练数据前缀审计SPATIAL_PREFIX_AUDIT.json：同prompt近远配对第0–2帧state token相同，第3帧起state可区分。真正相同状态需要视觉决策的72训练帧仅占1.586%。这是监督稀释假说，不是因果证明。
- 已准备可选EpisodePrefixSampler与5项通过测试，默认训练行为不变；草案prefix_sampling_policy.draft.json approved=false。真实数据dryrun4540次采样中前3推动帧72→903，逐episode/任务总数及wait700次保持，validation无泄漏。尚未激活或训练；必须先完成本轮39+21及实际复核，再决定是否做相同7240步从base启动的单因素对照。
- 独立中段teacher-forced诊断已启动：audit_demonstrated_branch_phase.py --frame30，日志/tmp/spatial_frame30_branch_20260928.log，使用专家RGB+对应q（两者都变，不是纯图像反事实），判断起始决策与后续拟合差异。当前额外进程只推理不训练，不访问主评测RPC。

## 2026-09-28 最新：新空间40模型训练完成、闭环评测中；旧模型空间基线0/39已复核

- 新训练7240步已完成，780验证帧/native flow loss .0070353，不作为成功证据。checkpoint为lerobot/outputs/paired_spatial_pilot40_20260928/package_sorting_pi05_1gpu_20260928_194203/checkpoints/007240/pretrained_model，last有效。新checkpoint的state/action统计40项精确匹配train_only_stats，CHECKPOINT_STATS_spatial.json通过。保存后磁盘约69GiB。
- 自动串行队列session9626已接run_spatial_model_comparison.sh，根demo/spatial_model_comparison_20260928_r1，当前新模型spatial_seed0，策略端口18774服务已ready。新39空间+21原场景，旧39和原21复用已核对源结果。主日志/tmp/spatial_training_evaluation_20260928.log。尚无新模型完整评测结论。
- CPU材料watcher session98371：prepare_model_review_materials.py，日志/tmp/spatial_model_review_materials_20260928.log。每轮13空间或7原场景完整结束后，生成comparison/visual_materials/spatial_{spatial|original}_seedN。只生成材料，绝不自动审批。实际复核后另存review和hash。整体goal active。
- 数据已转换并审计：lerobot/lerobot_sim_paired_spatial_pilot40_20260928，40条5320帧，34训练4540帧/6验证780帧。5320状态/动作行核验、120解码图像抽检、maxMAE1.3335、layout_leakage=false、training_ready=true。meta/spatial_position_balance_audit.json证实train/val各自两类别XY位置集合相同；原物理硬约束保持。
- 72候选全部完成实际5关键帧/条共360帧，推动54/60单条通过、9/15完整组通过，6失败组全拒；等待12/12。RAW_SELECTION选train candidate_03/09_negative、07/10_center、02/05_positive，val candidate_14_center（62028/62029）+wait63010/63011。补采草案保持approved=false未用。原候选池session69853和材料session97609均结束。
- 数据限制：训练Y仅约±1.4cm、近物体底部部分裁切，训练62021远盒末10帧目标区余量只有0.666mm；原门通过但鲁棒余量有限。候选REPORT.md完整记录好坏结果，不能宣称任意摆放泛化。
- 旧ordinary冻结基线session50367已完成，demo/spatial_baseline_heldout_20260928_r1 STATUS complete_reviewed。**0/39**（盒0/18袋0/18wait0/3），18配对复位全通过，195关键帧全部实际看过并绑定raw哈希，不是全视频复核。36推动有14非目标位移超门、6动作突变、4目标推进>=15cm但未过完整门，原因可重叠。画面持续伸向后方槽位，类别交换后会推错物体；支持位置偏向，不证明完全不识别类别。REPORT.md/visual_review.json完整。
- 新旧训练参数清单精确一致，693422112可训练/3616757520总参数，无LoRA，证据TRAIN_PARAMETER_COMPARISON.json；训练预算7240、seed42/base/优化器保持。INPUT_AUDIT哈希40/组7已通过。训练完成后checkpoint stats还会自动检查与train_only_stats一致。
- compare_spatial_evaluations.py会严格核对39空间+21原场景键覆盖、配对复位，报告近远任务、整几何组、胜负、非目标扰动和目标推进（辅助指标不替代原成功门）。新模型结果尚无。旧原21复用审计过的ordinary10/21源产物；不重复39旧baseline。
- 后续持续监控完整新模型闭环→实际画面复核→新旧分任务/近远/原场景胜负分析→报告好坏并继续解决不足。不可到训练或数值汇总就结束整体目标。

## 2026-09-28 最新：训练候选分层配额已齐；采集与旧模型冻结评测并行

- 候选池62000–62021已完成11组，其中7组数值+实际20关键帧复核通过，4组远盒目标区门失败整组拒收；所有11组画面已实际看过。按冻结顺序的训练6组：negative candidate_03/09，center candidate_07/10，positive candidate_02/05。candidate_08虽通过但不替代其他层，保留未选；最终RAW_SELECTION尚不存在，仍等独立validation及12wait。
- GPU采集session69853、CPU材料生成session97609仍在跑，正在62022之后。所有review.json绑定完整4条raw哈希。report_spatial_candidates.py生成全候选CANDIDATE_REPORT，含成败、阶段、近远分组、目标区余量/前向漂移；截至10组，近盒/近袋/远袋各10/10，远盒6/10。
- 新增旧ordinary模型冻结heldout39评测：run_spatial_baseline_heldout.sh，session50367，demo/spatial_baseline_heldout_20260928_r1，日志/tmp/spatial_baseline_heldout_20260928.log，策略端口18775。与采集分进程并行，显存实测约15/48GiB，内存可用106GiB；不运行训练。固定3seed，58000–58005及58010，不用评测结果改变候选选择。首条数值失败，尚不可汇总结论。
- 后续连续对照脚本run_spatial_model_comparison.sh已准备：新模型39空间+21原场景；复用独立旧模型39及已核对原21（重读原artifact汇总，不复制分数）。新训练启动前需等待旧评测释放GPU，避免训练与评测争用。旧原21审计OLD_ORIGINAL_REUSE_AUDIT.json、候选/heldout隔离CANDIDATE_SPLIT_PREFLIGHT.json已通过。
- audit_checkpoint_training_stats.py核对保存的state/action归一化与train_only_stats逐项精确一致；旧模型40项通过，已接新评测入口，新checkpoint生成后还要检查。对照脚本bash -n通过，未执行新模型评测。
- 当前没有新转换数据、没有新训练。整体goal active；继续完成剩余候选/wait实际复核→完整选择→转换/导出审计→7240训练→完整新旧闭环及真实画面复核。固定首帧11q/action零位、腰0、assist0、h10与原质量门不变。

## 2026-09-28 当前：预登记候选池持续采集，尚未转换或训练

- 后续反馈诊断结果：object_feedback 2/4；contact_confirmed_sweep 3/4，修复远盒但远袋退步，均已实际复核20关键帧，不采用。当前只用原距离策略 near -.13 / far -.11、staging .92，其他实验开关关闭。
- 当前GPU任务 run_spatial_candidate_pool.sh，session69853，demo/spatial_candidate_pool72_20260928_r1；日志/tmp/spatial_candidate_pool72_20260928.log。30布局62000–62029共60推候选+12wait63000系列。已完成前4组，其中两组远盒失败整组排除，两组数值与实际20帧复核通过。源失败STATUS不改，不重试失败布局。
- CPU prepare_candidate_review_materials.py --watch，session97609，仅生成材料，绝不自动审批。实际看过candidate_02_positive和candidate_03_negative，两组review.json绑定4条raw哈希。近物体底部裁切仍是已知限制。
- 冻结contract和selection_protocol在spatial_generalization_20260928_r1/candidate_pool_protocol。每个train负/中/正Y层按登记顺序取前2个完整合格组，另取独立validation前1组，合计28push+12wait=40；配额不足必须阻止转换，不可借层或拼单条。所有失败率与保留空间范围需报告。
- select_spatial_candidate_groups.py --select-out RAW_SELECTION.json会验证实际完整组复核与哈希。convert_spatial_pilot.sh读取选中源并导出审计；train_spatial_pilot.sh已改为读取动态验证ID（下方旧硬编码说明已过时）。新数据目录lerobot/lerobot_sim_paired_spatial_pilot40_20260928目前不存在，尚未训练。
- 下一步持续采集并实际复核，满足配额才转换/审计/7240步训练，再新旧checkpoint独立冻结heldout39条和新模型原21条h10验证。整体goal active。原失败spatial_pilot40保持隔离、旧合同已撤销，不能续跑。

## 2026-09-28 正式首组出现新失败，已隔离；物体反馈策略诊断中

- `spatial_pilot40_20260928_r1`首完整组3/4，60001远盒失败：推进17.62cm、finalY=-.19244；X从.50755滑到.5706（+6.3cm）。模式正常cross34/press19/sweep58/hold47，不是接近卡住，属于固定时间横扫失去接触。该组20关键帧已实际看并存failure_visual_review.json。
- 发现IsaacLab启动器可返回0但child STATUS=blocked_quality_or_runtime，原set-e脚本继续至60002。已明确TERM父采集脚本与该case进程，root STATUS quarantined_quality_failure，case60002部分产物保留，整批不转换不训练。不是任意清理数据。
- 已新增scripts/check_collection_quality.py独立读取child STATUS/manifest/quality/raw数量，在run_spatial_pilot.sh每个case及wait后强制调用；真实60000通过/60001拒绝，4项回归通过。后续绝不可只依赖IsaacLab退出码。
- 原正式合同已原字节改名`spatial_generalization_20260928_r1/pilot_contract.revoked_after_fresh_failure.json`，原pilot_contract.json不存在；CONTRACT_REVOCATION记录理由。不能重跑旧合同或续跑已失败批次。冻结heldout58000系列未改。后续正式新批需新布局ID/新合同；train_spatial_pilot.sh目前仍硬编码旧验证ID60012/60013/61010/61011，换新ID时同步更新。
- 当前 `object_feedback_20260928_r1`在跑60000/60001四条diagnostic：近物体完全保留旧-.13定时轨迹；远物体-.11接近后，用当前物体Y+方向*.04为掌心目标，targetY每帧最多6mm、12帧渐入；物体达到signedY>=max(.23,initialSignedY+.18)才hold。X/Z仍原目标，不直接写物体，assist0，160帧及原质量门。既改变反馈又限制扫动速度，不能单因素归因。
- 新--expert-object-feedback-lead默认0，仅diagnostic不能pilot；collector只读parcel_xyz传observed_parcel_y给专家；元数据和expert_control记录feedback/targetXYZ。模型训练输入仍原RGB+11q，不含oracle物体坐标。原servo2测试+反馈边界2测试通过。转换器拒绝非零object_feedback_lead，除非未来另行正式审查接入，现阶段不允许直接训练。
- 当前脚本run_object_feedback.sh，日志/tmp/object_feedback_20260928.log，session74330；只有该诊断在运行，没有采集正式数据/训练。下一步完成4条实际复核，比较前向漂移与接触保持；若有效，复验更广样本后才建新正式合同。整体goal仍active，不以启动/局部12/12结束。

## 2026-09-28 距离规则12/12复核通过，全新40条正式采集中

- `distance_offset_20260928_r1` **12/12原门+6/6配对通过，60关键帧实际复核**；STATUS complete_reviewed_feasibility_pass。三个完整几何组都支持类别交换×双指令。负Y远袋Y≈.205仅5mm余量，明确记录，不宣称广泛稳定。诊断仍training_ready=false。
- `spatial_generalization_20260928_r1/pilot_contract.json`已根据上述真实证据批准全新精确布局采集（不是训练批准）；草案另存未改。baseoffset-.13，目标X>=.48时faroffset-.11，staging.92/160帧。新布局60000–60013＋等待61000–61011，共40；原首帧零位/腰0/assist0/物理门不变，失败立即停。
- `/tmp/integrate_spatial_protocol.py` **已经执行，不要重跑**。collector/converter已接入严格合同；geometry/meta/effective/base/far参数和证据hash匹配，禁止diagnostic转pilot。6布局+9配对转换+5整组分割+7合同=27测试通过；全部14新布局校验通过，真实collector prelaunch AST准入通过。代码快照collection_source/以及source_before/after_integration。
- 正在运行 `run_spatial_pilot.sh`，根 `demo/spatial_pilot40_20260928_r1`，日志 `/tmp/spatial_pilot40_20260928.log`，session14580。每case600xx两个episode；最后waits目录12条。当前60000开始；持续监控root STATUS，不要以启动完成目标。
- 后续：全部数值通过→实际40条画面复核→每case/waits生成review.json（approved+method+精确raw路径hash，不是visual_review.json格式）→prepare_paired_sorting_lerobot.py --source全部15roots --validation-layouts60012,60013,61010,61011 --out-root lerobot/lerobot_sim_paired_spatial_pilot40_20260928 --repo-id local/paired_spatial_pilot40_20260928 →审计40/5320总帧、34/4540训练、6/780验证→train_spatial_pilot.sh（同7240步seed42专家only，不加LoRA）→新旧模型冻结39条空间h10对比+新模型原21场景。
- 独立heldout_protocol.json 58000–58005+wait58010、3seed，共39/checkpoint已冻结；SPLIT_PREFLIGHT证实无layout/seed/精确XY重复。旧ordinary checkpoint保留：lerobot/outputs/paired_ordinary_pilot40_20260928/package_sorting_pi05_1gpu_20260928_102242/checkpoints/last/pretrained_model。
- 目前仍**没有新转换数据或新训练模型**；已准备脚本但未越过质量与人工实际审查。剩余磁盘约88GiB，goal active，继续到整体模型验证。

## 2026-09-28 距离规则验证中，正式工作流仍未准入

- rotated_offset12最终10/12，60关键帧+5非目标盒放大帧实际复核，STATUS complete_reviewed_mixed_result；中心和正Y两组完整4/4，负Y组近盒/远袋失败。近盒退步14.87cm/Y=-.17228，远袋20.89cm但Y=.19222未进区。放大图确认非目标盒主体轮廓稳定，缩略图疑似旋转实为手臂遮挡/纹理；不新增未证实故障。
- `distance_offset_20260928_r1` 正在12条同布局复验：新 `--expert-far-contact-offset -.11`，初始目标X>=.48m用-.11，近物体仍-.13，staging.92。规则不看类别，原阶段门/质量门不变。6布局测试通过；默认far=0时完全旧行为。当前前两组8/8数值过门，55004/55005待完成；尚未图像复核。脚本run_distance_offset.sh，主日志/tmp/distance_offset_20260928.log，当前运行session53004。
- collector新增far参数现在仅diagnostic，实际base/far/effective offset写meta。helper在diverse_layouts.py `contact_offset_for_distance`，源码before/after在distance目录。
- `/tmp/integrate_spatial_protocol.py` 已更新兼容far参数但仍未执行，等当前诊断结束后再接入collector/converter；需跑回归/边界检查。spatial_protocol.py已支持exact far setting，7项测试通过。run_spatial_pilot.sh已读取合同far offset，尚未运行。
- 若distance完整12条通过并实际复核，可将已有pilot_contract.draft.json另存正式合同，expert设置base-.13/far-.11、staging.92/160帧，绑定distance视觉复核hash。草案farY实际[-.01621,.01445]，在本轮随机诊断范围内；不要改已冻结heldout_protocol。
- 若失败继续如实定位，不可批准草案或自动把diagnostic改pilot；训练仍未启动。

## 2026-09-28 完整可行几何组4/4，随机复验10/12，接近偏移对照中

- rotated_front_back_20260928_r1 **4/4原门通过、2/2配对通过**，20关键帧实际复核。STATUS complete_reviewed_feasible_nominal，训练仍false。首次证明同一前后几何交换类别后两任务都可行，推进21–26cm。不是模型训练结果，也不证明任意布局。
- rotated_variation_20260928_r1 3组随机中心/正Y/负Y，木盒±90°小扰动，袋0/90/180不同朝向，共12条，**10/12**，60关键帧实际复核。仅中心完整4/4；55003远盒press56帧、t106才sweep，最终12.83cm；55004远袋press109帧，0推进。STATUS complete_reviewed_boundary_failure。
- rotated_offset12_20260928_r1正在串行跑同12条，唯一改offset-.13→-.12，无新代码/门限更改。已修复55003远盒（22.7cm、hold稳定），但55004近盒出现新失败（14.87cm、Y=-.172）。必须同时报告改善/退步，不能只挑成功任务。脚本run_rotated_offset12.sh，日志/tmp/rotated_offset12_20260928.log；当前55004/55005尚待全部完成和图像复核。
- 可见性补充：audit_initial_visibility.py固定URDF/相机投影，实际对照visibility_overlay首帧，近物体下部裁切、bbox内框占比最小约65.8%，主体类别仍可见。非可见表面积/遮挡度估计，不是模型识别证明，未改变相机/机器人。
- 工作流目录spatial_generalization_20260928_r1含PLAN.md、pilot_contract.draft.json（approved=false）、预注册7几何组28推动+12等待的40条草案（新ID60000–60013/61000–61011），验证60012/60013/61010/61011；保持旧5320总帧/4540训练/780验证、seed42/7240步。独立heldout_protocol.json已冻结3新几何组58000–58005、3seed及wait58010，共39条/checkpoint，不可看结果后调布局。
- 已准备run_spatial_pilot.sh（失败即停）、train_spatial_pilot.sh（输入hash/组/帧审计）、run_pi05_spatial_sim.sh（h10无裁剪复用server）；新env只改dataset/split/stats/output/repo/日志名，其余和ordinary40一致。**未采正式新数据、未转换、未训练。**
- 新spatial_protocol.py和6项准入测试已写、通过；当前尚未接入collector/converter。待诊断结束后运行/tmp/integrate_spatial_protocol.py（已生成未执行），接入后需要回归检查再放行真实合同。若采用依距离分段的offset，需同步合同/collector/converter/测试，不能直接用草案。诊断源文件永远不改role进入训练。

## 2026-09-28 接触策略诊断复核与旋转前后布局

- near_face_contact 1/8、settled_near_face 1/8，分别40关键帧已实际复核并归档 visual_review/REPORT，STATUS complete_reviewed_quality_failed。前向稳定接触远袋推进9.17cm/远盒4.28cm，但未到目标区；旧近侧点会带动前方物体，无完整几何组通过。
- finger_heading_20260928_r1：只加软世界X手指朝向约束weight=.08，与forward_settled完全同布局参数，0/4且所有目标位移0，实际20关键帧复核。姿态改变丢失接触，STATUS complete_reviewed_hypothesis_failed，默认关闭、停止扩此方案。新增控制函数有限差分导数/边界2测试+旧servo2测试通过。
- rotated_front_back_20260928_r1正在运行4条，layout54000/54001，同中心前后位置(.36,-.008)/(.505,.005)交换类别，木盒yaw90°、袋yaw0°；物体原尺寸不变。窄边减小X占地，旋转AABB仍保持2cm额外间距，桌边全支撑。专家用staging.92/offset-.13、不加cap/settled/heading。是新几何可行性测试，不作单因素归因。脚本run_rotated_front_back.sh，日志/tmp/rotated_front_back_20260928.log，等待全部结果和画面审查。
- reset_sorting_parcels/_write_pose新增初始yaw默认0，只在warmup前设置；每条实际初始xyzw四元数写入collect_meta，配对审计检查朝向，指定yaw重置漂移>0.03rad失败。load_diagnostic_layout使用原尺寸旋转AABB+原2cm间距，新增完整桌面支撑检查。5布局+9原配对/转换测试通过。首帧零位/腰0/assist0仍守原约束。
- 无新训练数据放行，无新训练启动，整体goal active。接下来以完整交换类别×两任务几何组为最小单位推进，禁止只挑近物体成功填数据。

## 2026-09-28 运动学定位完成，改为可达接触点并先稳定接触

- `probe_sorting_kinematics.py`只读URDF FK/多初值点IK。96个真实轨迹掌心点最大误差2.58e-7m，模型可靠。跨身/远处指定掌心接触点残差约6–11cm；原正常点可解。注意多初值数值求解不是全局不可达证明，也不包含碰撞/朝向/动力学；中心掌心点不可达不等于物体不可操作。结果`spatial_failure_review_20260928_r1/kinematic_probe.json`。
- compact_natural 3/8，40关键帧已实际复核、完整geometry组无一通过，STATUS complete_reviewed_quality_failed，不训练。
- bounded_servo 0/8，40关键帧已实际复核，比对照4/8差，STATUS complete_reviewed_hypothesis_failed，默认关闭不扩此方案。
- `near_face_contact_20260928_r1`正在运行8条：compact几何不变，staging.92/offset-.07，新增expert-max-contact-x=.445（仅远物体掌心目标偏近侧），bounded memory关闭。近侧方案与compact基线改了两几何因素，不能单因素归因。初步远袋只推进4mm、带动前盒1.84cm>1.5门，仍失败。
- 手网格+记录FK近似分析显示：far袋t35 palmZ.861、网格尚未接触，t50 palmZ.839但Y已推进到.005附近，随后滑过；AABB近似非接触力。旧press门max(contact+.02,table+.135)=.885，可能过早横扫。
- 下一项`settled_near_face_20260928_r1`已排在near_face后：settled(.445,-.07)与forward_settled(.47,-.04)，均staging.92，启用已有settled_contact（距接触高度6mm内稳定3帧），布局53000/53001两个类别互换×两任务，各变体4条共8条，trace_episode_contacts。新前向点IK可解，但碰撞/实际推进仍需验证。脚本run_settled_near_face.sh，日志/tmp/settled_near_face_20260928.log；未训练新数据。
- collector现有新增参数均默认保持旧行为、diagnostic专用；当前collect_meta也记录staging/offset/servo/max_contact_x。以前几批新增参数在provenance里，不能伪改旧raw。整体目标仍active，继续实验审查→有效多样性正式采集→转换/训练/独立验证，不停在单项启动。

## 2026-09-28 接近几何复核完成，紧凑前后/有界控制继续

- approach_geometry两变体各4/8，80关键帧已实际复核，STATUS complete_reviewed_quality_failed。lower_closer交换场景由cross进入press，但仍无有效推进。远处前后目标仍失败。默认专家未改，全部diagnostic不训练。
- `compact_natural_layouts_20260928_r1`正在采8条：两组x约.365/.535及.37/.54，类别互换、前后摆放；expert staging.92/offset-.13，原质量门。
- `bounded_servo_20260928_r1`排在compact后，8条复用50000/50001/51000/51001，和lower_closer对照仅新增bounded_servo_memory。前一目标累积IK增量，lead限±.10rad，原collector每帧.055、URDF限位及腰0仍保留。验证是否实测锚定IK在负载下稳态停滞，尚未证明；2项模拟停滞有界/默认无累积测试通过。默认false、仅diagnostic；源码快照在目录。脚本run_bounded_servo.sh，日志/tmp/bounded_servo_20260928.log。
- 转换器新增 geometry_group/assignment 传递及整组分割检查，5测试通过：必须同时有两种摆放×两指令，不能只保留成功位置或跨train/val拆互换版本；历史无group记录行为不变。新审计脚本audit_spatial_category_binding.py确认普通40的14推动布局仅凭Y符号可100%区分类别，这只是数据支持偏差，不是模型行为证明。
- make_rollout_review.py仅生成复核材料，绝不自动设置reviewed；实际看图后另写visual_review。view_image工具受沙箱挂载故障无法读图，已用exec只读base64分段再image显示实际检查，不得把生成图当看图。

## 2026-09-28 持续整体目标执行：实际复核完成，接近路径修正中

- 用户要求自行安排并持续到整体目标；当前 active goal 已创建，不能以启动作业/单项完成结束目标。无 subagent 授权，不用多agent。
- `spatial_failure_review_20260928_r1`：24轨迹120关键帧已实际看过，配全帧轨迹/mode，visual_review含hash。原两批各4/12不变，STATUS complete_reviewed_quality_failed；近处前后可成功，左右交换和远处常卡cross。
- 语言LoRA实验21轨迹105关键帧也已实际看过，`task_language_adapter_20260928_r1/failure_review/visual_review.json`。严格8/21，screen失败，停止扩该方案。
- `obstacle_isolation_20260928_r1`6轨迹30关键帧已复核：保持目标不变，仅移另一物体X至.62。袋掌全程差0、盒掌差3.58e-7m，均cross150帧、目标位移0；所以先前两例首次失败不是另一物体挡住手，后续推送障碍仍未知。REPORT/ANALYSIS/visual_review完整，失败禁止训练。
- `approach_geometry_20260928_r1`在运行：lower(.92m,offset-.13)、lower_closer(.92m,offset-.07)，各布局50000/50001/51000/51001两任务，共16条。旧对应轨迹已留为对照。仅diagnostic开关，默认staging1.0/offset-.13不变；960默认路径点等价，8+16回归通过。源码前后快照在目录。脚本run_approach_geometry.sh，日志/tmp/approach_geometry_20260928.log，各case日志及STATUS；待逐项复核与可达性/接触推送判断，再继续正式多样数据与训练。不能放宽质量门或仅筛选同侧成功造成捷径。

## 2026-09-28 用户补充：前后与自然错落摆放

- 继续多样性数据目标，用户明确不希望刻意左右排列。新增 `demo/natural_layout_feasibility_20260928_r1`：中心前后、偏侧前后、斜向散放3组随机几何，各交换类别，两条指令，共6布局/12轨迹。编号51000–51005，seed2026092802；坐标/协议已冻结。normal/swapped仅指槽位分配，与左右无关。
- `scripts/run_natural_layout_feasibility.sh` 等上一批空间诊断正常结束再串行采集，避免GPU并发。STATUS标记queued；未开始训练。所有布局先过原物理门和实际画面审查，再确定可行空间。正式扩采应在空间分区内均衡类别、连续随机位置/间距，同几何的互换版本不得跨train/val。不把12条诊断视为泛化数据集。

## 2026-09-28 用户指出类别/位置混淆：优先打破空间绑定

- 用户要求更丰富摆放数据训练，质疑固定左袋右盒学到位置捷径。代码证实 sample_layout 只取 box x .44-.47/y -.15至-.125、mailer x .44-.47/y .125-.15。现有数据无法排除类别-位置混淆；不能把窄范围结果称泛化，也不能据此直接断言唯一根因。
- `demo/spatial_diversity_feasibility_20260928_r1` 已启动6个明确布局（3种几何各normal/swapped）×2指令=12条物理诊断。控制同X左右交换可能受路径阻挡，另有X=.40/.58前后错开以分离推动走廊。编号50000–50005，未动预留40000系列。所有失败如实保留；某种位置/类别失败不能只丢掉它再称平衡数据。
- collector新增默认关闭 `--diagnostic-layout-json`，仅diagnostic单配对、禁止offset/wait/contract。校验坐标/高度/初始间距/geometry_group，原零位/腰0/assist0/非目标稳定/步长门不变；8项原测试+3项新测试通过。新loader `simfoundry/data/diverse_layouts.py`。此入口不允许直接生成pilot训练集。
- 脚本 `scripts/run_spatial_diversity_feasibility.sh`，主日志 `/tmp/spatial_diversity_feasibility_20260928.log`，各case日志及STATUS在实验目录。预定布局质量失败后可继续下一个预定case；运行错误停止，无重抽。必须待完整轨迹和画面审查后确定可行空间，再建立独立新多样性训练集，整geometry_group的类别交换和两条指令不得拆分train/val。
- 语言适配实验数值最终8/21（盒5/9袋3/9wait0/3），不优于普通10/21，仍待实际画面复核。先不扩大该方案。下一步同数据预算比较旧位置分布与通过质量门的均衡位置分布，同时报告旧场景与新未见位置指标；不混旧300。

## 2026-09-28 用户纠正方向：直接解决任务干扰

- 用户确认“最简单场景可以学会”已验证，禁止重复该验证；当前重点改为共享模型的任务干扰，暂缓接触恢复专家扩展和新数据采集。
- `demo/task_interference_20260928_r1` 完成 192 次固定图像/state/noise 的指令交换。B/ordinary 起始 prompt 动作差 MAE 约 .061/.059 rad，t40约 .0033/.0038，t90约 .0015；状态中段可能已编码任务，不能单独认定忽视指令或因果干扰。详见 REPORT/SUMMARY/results；没有用预留确认布局。
- 新实验 `demo/task_language_adapter_20260928_r1`：同 ordinary40、同 split/stats/base/seed42/7240步/batch1/优化器，增加语言模型 rank8 alpha16 dropout0 LoRA，保持全动作专家及 action/time projections 训练；原语言权重和视觉冻结。不是分成多个模型，不重采数据。严格 h10 三seed21条，筛选预设 total>=13/21、盒>=7/9、袋>=4/9、wait>=1/3 且无错手；最终必须实际看图，不自动放行扩采。
- 新 `train_expert_with_language_lora` 默认 false；原专家模式行为保持。配置检查和参数范围审计加入，5项边界测试通过，真实训练参数审计已通过：原 693,422,112 个可训练参数全部保留，只新增 9,805,824 个语言 LoRA 参数（252 张量），见 PARAMETER_COMPARISON.json。修改前后源码已存 source_before/source_after，脚本 `scripts/run_task_language_adapter.sh`；主日志 `/tmp/task_language_adapter_20260928.log`，训练日志在实验目录。已启动串行训练→h10评测，按 STATUS.json 核实进度。
- 现有40条数据已审查，仍满足 PROJECT_CONSTRAINTS §1 首帧零位；无新数据。LoRA初始化会改变随机流，语言层也处理图像/state上下文，单轮改善不能单独证明文本路由是根因。

## 2026-09-28 用户授权清理历史测试数据

- 清理 25 个旧预览目录的影像等产物、16 个 0917 diag 诊断目录（含空目录），共 886 文件 / 251.60 MiB。清单：`demo/historical_test_cleanup_20260928_r1/manifest.json`，说明见同目录 REPORT.md。
- 旧预览 summary/日志原位保留，原视频/图片链接不再有效；当前配对实验、近期诊断、正式训练集和旧300对照保留。本次不改变模型/训练数据，也未启动新实验。

## 2026-09-28 用户授权清理旧 checkpoint，容量阻塞解除

- 用户明确要求删除无用 checkpoint。本轮删除 11 个已替代/启动测试权重，约 99.05 GiB；清理后可用 106.99 GiB，以 df 实时值为准。
- 清单与配置归档：`demo/checkpoint_cleanup_20260928_r1/REPORT.md`、`manifest.json`、`metadata/`。旧 last 随权重退役，另移除一个原有悬空 last；保留模型文件和 last 已核对。没有删除数据、评测、日志或基础模型。
- 当前六组模型及关键历史对照全部保留。仅清理明确已替代的旧权重，本授权不扩大为任意删除数据。下文容量不足为历史状态；匹配训练所需至少 25 GiB 已满足，未自动启动新训练。新数据仍须遵守 PROJECT_CONSTRAINTS §1 零位要求。

## 2026-09-28 本轮完整收尾与后续容量约束

- 总报告`demo/model_quality_progress_20260928.md`。三类新增模型各10/21，基线本轮4/21；84回归420关键帧、192离线图像推理、14物理诊断70关键帧均完成审查。没有后台作业。
- 高度暂停专家`demo/contact_height_pause_20260928_r1`也失败：control2/2通过；Z60盒11.79cm、袋10.75cm均失败。41–48/49提前暂停改变扰动前路径，后期63/69帧暂停；不是可靠接触恢复器。选项默认关闭且diagnostic专用，不部署/不用于pilot。REPORT/ANALYSIS/visual_review/STATUS完整。
- 关键数据结论：格式/标签/转换/归一化未见明显错；接触阶段状态覆盖缺口、专家无法可靠纠偏已有物理证据。下一步需真实物体位置/相对几何反馈的恢复专家，先保证无扰动/扰动前路径不变并通过小对照，再全新pilot和匹配训练。禁止直接扩200、混旧300、提升失败示范。
- 当前新训练容量不足（单checkpoint9.1GiB，剩余不足此量；最后请以df为准），匹配两组训练至少预留25GiB。已异步询问其他可写磁盘目录，未收到答复；不得擅自删除旧数据/权重。低存储诊断与报告已完成。

## 2026-09-28 接触阶段专家恢复失败已确认，暂停横推诊断运行中

- `demo/contact_recovery_feasibility_20260928_r1`6条30关键帧复核完成：control盒18.86/袋19.88cm均pass，negativeX60盒18.61/袋19.66cm均pass（实偏11.6–12.3mm）；Z60盒14.39/袋14.06cm均fail（实偏19.0–19.7mm）。力轨迹/首q,a0/腰a0审计通过；失败隔离，不训练。STATUS=complete_reviewed_failed_z_recovery。
- 新假设：接触抬高后横推时钟仍前进，错过有效推进。只给专家增加默认关闭`--recover-contact-height`，仅diagnostic可用：sweep掌高>goal+.010暂停mode_step，<=goal+.006连续3帧后恢复；不重规划物体、不改质量门。注意也可在首次进入sweep时等待下降，故必须带无扰动对照。
- 当前运行`demo/contact_height_pause_20260928_r1`，布局60 control/z60共4条，源快照与protocol齐全；脚本`run_contact_height_pause.sh`，日志`/tmp/contact_height_pause_20260928.log`和各variant.log。待分析pause轨迹、同力核对、原门和20关键帧。未训练任何新接触数据。

## 2026-09-28 接触诊断完成，接触阶段恢复可采性运行中

- `demo/contact_buffer_diagnostic_20260928_r1`4条20关键帧已复核：专家盒19.03cm/袋20.15cm均pass；普通模型盒14.37cm/袋0.50cm均fail。袋候选专家109步(51–159)、模型38步(42–79)，模型主阶段掌高+1.7cm且末X靠后约3.3cm。盒模型候选107仍不够推程，不能候选数=有效力。
- 只读最后物理碰撞候选，不是接触力，不排除子步瞬态。REPORT/ANALYSIS/visual_review/STATUS完整。
- 继续`demo/contact_recovery_feasibility_20260928_r1`：布局60双任务，control/negative_x60/z60三组，60N真实手部外力在70–75步，6条总量；默认专家/原门不变。脚本`run_contact_recovery_feasibility.sh`已启动，日志`/tmp/contact_recovery_feasibility_20260928.log`及各variant.log。需要分析扰动幅度、恢复、原质量门和30关键帧，全部diagnostic禁止训练。
- collector新增`--push-force-axis {x,negative_x,z}`和`--push-force-start`，默认仍x/5；非默认只允许diagnostic专家，pilot契约不能使用新profile；记录force向量与元数据。源快照保留。模型和图像诊断均已退出，当前只有此专家采集。

## 2026-09-28 图像诊断完成，接触缓存诊断运行中

- `demo/image_input_diagnostics_20260928_r1`完成192次离线预测：同图/q/prompt/noise重复差0；旧新首块均精确复现误差0。只换真实首图首10动作差中位max0.002851rad、最大0.006493rad。说明首块差异由图像解释，但非全部闭环失败因果证明。
- raw/训练解码同帧54配对：像素MAE中位1.224/255，动作差max中位0.003636rad、最高0.008780rad。解码图像对袋平均略更差、盒/等待略更好，没有统一方向。REPORT/SUMMARY/STATUS已归档，不归咎于压缩、不盲目重训。
- 继续低存储诊断`demo/contact_buffer_diagnostic_20260928_r1`：布局20、专家双任务→普通模型seed0双任务，h10/原门不变。`run_contact_buffer_diagnostic.sh`已启动，主日志`/tmp/contact_buffer_diagnostic_20260928.log`。需监测expert/model日志、实际审查4条关键帧。
- collector新增默认关`--trace-episode-contacts`仅diagnostic允许；每控制步后只读既有Newton接触缓存，不调用update_contacts、不加外力、不改动作。只记录last physics collision candidates，非全子步或力/冲量，不能将候选存在当有效力证据。8+2回归通过，旧结果和源快照未改。

## 2026-09-28 等待单项消融完成，继续图像输入诊断

- `demo/wait_only_recovery_comparison_20260928_r1`：严格10/21（盒5/9、袋4/9、wait1/3），各seed1/7、4/7、5/7；105关键帧已实际复核，STATUS=evaluation_reviewed_screen_failed。四组对照与REPORT.md完整，总体不优于普通/联合恢复，不满足预设推进门槛。
- 当前新增三组均10/21，原B本轮复测4/21。不得扩200、不得动预留确认集。
- 下一步`run_image_input_diagnostics.sh`将串行运行同输入复现/首图交换（冻结B）和同帧raw-vs-training-decoded（普通组）离线探针，输出新目录`demo/image_input_diagnostics_20260928_r1`，不执行预测动作。
- 磁盘只剩约8GB，不足新训练；已用异步工具询问用户其他可写磁盘目录，尚未收到答复。不得自动删除已有权重/数据。当前评测已全部结束，可以开始离线GPU诊断。

## 2026-09-28 三组对照完成，继续等待恢复单项消融

- `demo/recovery_comparison_20260928_r1`：STATUS=`evaluation_reviewed_screen_failed`，63条315关键帧已实际复核。当前同入口：baseline4/21（盒3袋1wait0）、ordinary10/21（盒7袋3wait0）、recovery10/21（盒4袋3wait3）。REPORT.md/COMPARISON.json/各组视觉哈希完整。
- 恢复未优于普通，不扩200、不用预留确认。等待右漂移1.407–1.491cm，余量小。推动恢复只早期扰动，未覆盖失联接触，尚不能证明总体收益。
- 历史B5/21→复测4/21；同seed初始q相同但图像MAE约0.25–0.28/255，首动作有差，接近门限案例可翻转。使用当前对照，不能声称因果已完全隔离。
- 下一项探索协议`demo/wait_only_recovery_protocol_20260928_r1`：普通push+恢复wait，只有4条等待raw改变，28push与验证全不变；导出`lerobot/lerobot_sim_paired_waitonly_pilot40_20260928`审计5320行+120图通过，train4540/val780、40ep。
- `demo/wait_only_recovery_comparison_20260928_r1`12:00:16开始、12:20:08完成7240步，验证loss0.00676209（780帧），12:20:55开始h10seed0；40项checkpoint统计核对通过。日志`train_waitonly.log`和`/tmp/wait_only_recovery_comparison_20260928.log`；脚本`run_wait_only_recovery.sh`、配置`pi05_paired_waitonly_pilot40_20260928.env`，7240步seed42；启动前要求上轮全审查及精准数据替换审计。新示范真实首帧q/action零位、腰0、assist0继续满足约束。磁盘启动前约25GB，不删除旧权重/数据。

## 2026-09-28 用户要求持续推进：新数据审计完成，训练对照运行中

- `demo/push_recovery_feasibility_20260928_r1`已完成：布局30/31共8条全部通过；40关键帧已看，visual_review.json绑定哈希。40N早期扰动约0.0111rad，专家仍推到18.48–20.87cm；只证明早期抬臂纠正，不代表失去接触后重规划。
- 正式小先导协议已在采集前冻结：`demo/recovery_training_protocol_20260928_r1/protocol.json`。普通/恢复各新增2配对布局50/51（640帧）+4wait31000–31003（280帧），每组新增920帧；叠加原B32条总40条5320帧，训练4540、验证780不变。
- 两组从同base+seed42训练7240步；原B同预算checkpoint作基线。配置 `scripts/pi05_paired_{ordinary,recovery}_pilot40_20260928.env`；流水线 `scripts/run_recovery_training_comparison.sh`，需两组导出审计通过才可启动。
- 恢复正式采集只有 `--recovery-pilot-contract`匹配已审查登记范围才允许pilot；推动全数+画面已过门，契约已批准固定采集范围；正式采集已启动，日志`/tmp/recovery_pilot_collection_20260928.log`。转换器增加契约哈希/受力逐帧核对。`simfoundry/data/recovery_protocol.py`纯逻辑与2项测试通过，原8项转换/质量回归通过。
- 两组新先导各8条920帧全部通过、80关键帧已看。普通/恢复导出各40条5320帧：全部state/action/text核对、各120解码帧maxMAE1.27975、无泄漏。cross_variant_audit.json初态q差0，首RGB最大MAE.413/255，wait末段q相对控制误差<8e-9rad。
- 普通新增组7240步完成，验证loss0.00676078（780帧）；h10三seed严格10/21：盒7/9、袋3/9、wait0/3（各轮2/7、3/7、5/7）。105关键帧已审查并保存哈希 `failure_review/ordinary_visual_review.json`。恢复组7240步于11:21完成，验证loss0.00675741（780帧），11:21:55开始seed0闭环；基线B同入口复测待后续自动执行。两组各40项checkpoint归一化统计与训练统计完全一致。不能据此宣布恢复数据有效。
- 恢复组h10三seed完成严格10/21：盒4/9、袋3/9、wait3/3（各轮2/7、2/7、6/7）。105关键帧实际复核；三次袋动作跳变均第30帧。总数不优于普通组，不满足扩展条件；等待改善但右掌1.407–1.491cm贴近1.5cm门限。11:39:53开始原B同入口复测。下一步准备普通push＋恢复wait单因素小消融，非宣称恢复方案成功。
- 已启动 `demo/recovery_comparison_20260928_r1`，主日志`/tmp/recovery_training_comparison_20260928.log`。10:22普通组训练开始，后自动h10三seed→恢复组训练/h10三seed→冻结B同入口三seed复测。每组7240步，原验证780帧不变。继续监控STATUS/train_ordinary.log/train_recovery.log与每seed评测，并实际看图；预留40000系列确认布局尚未用。不得自动批准未看的画面；不混旧300；不改预留确认集。

## 2026-09-28 执行新计划：等待恢复可采性验证完成，尚未训练

- 本阶段协议/报告：`demo/recovery_protocol_20260928_r1/{protocol.json,REPORT.md,STATUS.json}`。原h10/质量门不变；预留新确认布局40000–40009、41000–41002和推理seed3/4/5，未执行候选测试、不得用于开发调参。
- 42轨迹执行核对：chunk起点均0/10/20…，推理state与记录q误差0，前10动作对应误差约1.11e-9rad；未发现执行切片错位。39/42在首次换块前出现持续状态偏离；8条成功也偏离，不能将此直接当失败根因。等待首块双肩pitch目标约-0.016～-0.028rad，示范应0。
- 同布局30001的0/8/20N单左手及40/80N双手诊断全部完成并通过原质量门，25关键帧复核。80N双侧肩pitch约-0.02026rad、掌相对首帧漂移5.73mm<15mm，末10帧相对无扰动关节误差<8e-9rad。真实首帧上半身q/action全0、腰action0、无包裹助推。
- 物理恢复状态令已知模型等待前1–9帧最近状态距离中位数0.01684→0.01086rad，全程0.05218→0.03828rad，仅表示已知记录的覆盖改善。5条数据仍diagnostic、不得直接训练。
- `--wait-force-side left/right/both`默认left，诊断力上限改80N；默认无扰动行为不变，原8+16项回归通过。源代码v1/v2快照和协议哈希已保留。
- 冻结B模型24探针：受力t23/26仍预测双肩约-0.033～-0.037rad，专家实际零动作可恢复；无扰动同阶段约-0.003～-0.007rad。是离线证据，非模型闭环改善。
- 当前本阶段进程均完成，无新训练；下一步推动纠偏专家可采性、多样化正式恢复先导与导出审计，再做原B/普通增量/恢复增量同预算对照。全局目标尚未完成；B5/21、C4 3/21结论不变。不混旧300、不扩200。

## 2026-09-24 数据覆盖专项诊断（审计与两项小对照完成）

- 报告 `demo/paired_data_coverage_20260924_r1/REPORT.md`，可复现脚本 `scripts/audit_paired_state_coverage.py`。训练等待6条同刻q最大差5.82e-11rad、action全0，缺乏偏离恢复覆盖；盒/袋约36%/34%动作相邻变化<.001rad。格式审计通过不代表有效分布覆盖充分。
- C4共21条×5关键帧已复核并记录原始哈希，STATUS改为 `evaluation_reviewed_quality_gate_not_met`；17次动作超限全部发生在h10块边界。严格3/21不变。
- 专家加入默认关闭 `--settled-contact` 诊断开关：原press门0.885m；新门目标+.006m且连续3帧。仅diagnostic允许；每帧expert_control.json保存阶段。原默认行为及质量门不改。
- 同布局30接触对照4/4过数值门、20关键帧复核完成；新门确实将起推掌高降低约4cm，但最终盒/袋推程变化<1mm，未证明收益。`contact_comparison.json` / `contact_visual_review.json`在覆盖报告目录。开关默认关闭，不扩大采集。
- `--wait-force-n`仅diagnostic等待允许：第20–25帧真实左手外力，逐帧external_force.json，不改动作标签。8N参数测试 `demo/wait_physical_recovery_20260924_r1` 已完成并复核；通过原等待门，但相对无扰动仅0.00206rad/0.993mm状态变化，覆盖增益不足，禁止训练。实际首帧q/action全0，无包裹助推。
- 当前两项实验均结束，无新训练在跑。下一步应分级设计物理恢复覆盖并逐条验收，再做同预算训练对照；不得宣称本轮已提升模型。
- 现有8+16项unittest通过。当前没有新模型训练，不扩200、不混旧300；下一步重点是物理可追溯的恢复示范。保持新数据真实首帧上半身零位、assist=0、h10评测。

## 0a.【训练、数值评测和关键帧复核完成，尚未过门】双物体配对短指令 / 零位先导（2026-09-24）

**最新结果（2026-09-24 12:57完成）**：A/B均完成7240步训练和h10三个seed的未见布局评测，各21条。`demo/paired_zero_ab_experiment_20260924_r1/EVALUATION.json`为结果来源；STATUS=`evaluation_reviewed_quality_gate_not_met`；42条均已逐条检查5个关键帧并结合全帧轨迹，审查方法和哈希在 `failure_review/visual_review.json`。非逐像素审查全部帧。

| 预先固定的全部数值门限 | A统一指令 | B短指令 |
|---|---:|---:|
| 右手推盒 | 0/9 | 3/9 |
| 左手推袋 | 0/9 | 2/9 |
| 空桌等待 | 0/3 | 0/3 |

B的18次推动中，几何接近记录均为指定手、非目标XY位移均0；主要失败是推程不足及动作跳变。B盒另2条、袋另1条仅因动作步长超门限失败，仍按失败保留，不放宽标准。B空桌左掌漂移6.8–10.5cm（门限1.5cm）。A有3条袋仅因动作跳变失败，不能把严格0/9误解为袋一次都未推到位。A是双物体同指令的歧义消融，不代表旧300模型同条件复现。

验证loss：A .007951、B .007094（各780帧），不能替代闭环结果。当前结论：短指令有选任务改善迹象，但整任务成功率不足；**不扩200、不混旧300**。下一步先复核失败画面及接触/推程、等待与动作跳变，不能直接宣布实验成功。

### C4最新状态：14:35训练及数值评测完成，闭环关键帧待复核

- C4：14480步全部完成，验证loss .005003（B两轮为.007094）。目录 `demo/paired_c4_experiment_20260924_r1`；`EVALUATION.json` / `COMPARISON_B_C4.json`。
- 严格通过：盒2/9、袋1/9、wait0/3，总计3/21；原B为盒3/9、袋2/9、wait0/3，总计5/21。增加轮数未提升整体严格成功率，不能凭更低loss宣布改善。
- 等待稳定性有改善：C4左掌最大偏移1.28–1.59cm、右掌2.19–2.41cm；原B左6.80–10.48cm、右3.17–3.49cm。仍超过1.5cm门限，不放宽。
- 推动仍有推程不足与动作跳变；C4有3条盒、2条袋仅因跳变失败。模型画面尚未逐条复核，STATUS保持 `numeric_evaluation_complete_visual_review_pending`。
- 不扩200、不混旧300。下一阶段优先复核C4画面并设计稳定接触/物理可追溯纠偏的小批示范，不盲目继续延长训练。

### 2026-09-24 用户授权继续后的失败诊断

- 报告：`demo/paired_failure_diagnosis_20260924_r1/REPORT.md`；114次原模型离线探针在 `probes.json` / `probe_summary.json`。入口 `scripts/diagnose_paired_policy.py`。
- 动作跳变：A 30次、B 6次超.08rad，全部在h10动作块边界；图表/逐条分析在原实验 `failure_review/trace_analysis.json`。
- 黑袋推动掌心中位高度：专家.8352m，B seed0/1 .8490/.8505m，B seed2 .8151m。高度误差与推程不足相关，尚不是单因素因果结论。
- 空桌状态/图像受控探针：初始图像+初始state预测动作幅度均值.02622rad；固定图像改为失败t60 state变.22719rad；仅改图像仍.02232rad。支持状态误差反馈放大。40项checkpoint归一化统计与训练stats一致。
- 已完成验证布局20两任务+空桌10006、seed0的原始控制/0.055rad限幅对照，两组均0/3；限幅后盒14.63cm、袋12.89cm、wait左掌9.81cm，未解决任务失败。6条关键帧已复核。新增 `--policy-max-action-step` 默认0，只允许policy诊断；保留 `policy_raw_actions.npz` 和实际执行raw.action，不能当作模型自行变平滑。旧评测结果不改。
- C4配置已准备：`scripts/pi05_paired_pilot32_c4_20260924.env`，入口 `scripts/run_paired_c4_experiment.sh`；冻结B数据，从同base+seed42重训14480步（4轮，原B为7240步/2轮），余弦调度终点随总步数变。控制器限幅关闭，h10三seed同原固定测试布局做回归，非新的盲测。2026-09-24 13:36已启动，目录 `demo/paired_c4_experiment_20260924_r1`；STATUS.json / train.log；主日志 `/tmp/paired_c4_experiment_20260924_r1.log`。训练后自动运行114次同输入离线探针和h10 seed0/1/2回归评测，结束仍需画面复核。
- 不扩采、不混旧300，不按等待指令硬编码动作0。若增加训练仍不能解决反馈漂移，再设计物理可追溯的纠偏示范。

以下为采集及启动阶段记录（时间早于上述完成结果）：

用户批准先做32条先导（12布局×2任务+8 wait），强调数据质量。已按授权修订 `PROJECT_CONSTRAINTS.md` §3，允许本实验使用固定任务短指令；旧统一prompt与旧300保持对照。

- 新入口：`scripts/collect_paired_sorting.py`；质量门：`simfoundry/data/paired_sorting.py`；8项纯逻辑测试 `tests/test_paired_sorting.py` 已通过；旧采集16项回归也通过。
- 新零位选项：`u1_sorting_default_qpos(zero_upper_body=True)`。真实仿真关节首帧state/action上半身全0，非修改日志。零位分支同时修正旧helper腿部通配串写问题，旧分支未改。
- 方案与预设质量阈值：`demo/paired_pilot_protocol_20260924.md`。
- **32条先导已完成数值+逐条关键帧审查，A/B导出审计均通过，A组已启动训练（2026-09-24 11:42），尚无模型闭环结论。** 原目录 `demo/paired_zero_pilot32_20260924_r1` 在首条wait失败后保持blocked。全部12对推动未更改原始数据，完整复核后复制到 `demo/paired_zero_push24_release_20260924_r1`（带release_script/来源与哈希）；没有挑选成功重试。正式wait新目录 `demo/paired_zero_wait8_20260924_r2`（8/8通过，review approved）。其他idle/push烟测诊断目录不得混入训练。
- 空桌失败根因：旧空桌门仅看Y，误判x=15m的场外隐藏物体；隐藏刚体在(5,5,3)堆叠也产生弹开。新入口将隐藏刚体分开放置，空桌门改查真实工作区XY footprint；新增回归测试覆盖场外Y接近0/场内真残留两种情况。原失败wait永不训练。
- 零动作基线r2失败：录制期间盒最大XY漂移2.41cm，袋4.31cm；同布局两次重置位置差3.28cm。首帧11维零位通过。
- 向桌内平移12cm的r3仍失败；落稳后物体x仍接近0.36，不能靠移远解释为手臂碰撞。
- r4真实碰撞对记录显示初始只有包裹—桌面接触，没有手臂；滑到前缘后出现table_edge_wear接触。运行时物理后端实际为Newton MJWarp，RTX渲染器为PhysX；旧文档“PhysX推”的表述不可照搬为当前引擎证据。
- r7 单变量切换 `--newton-contacts`（`use_mujoco_contacts=False`）后：2次零动作均通过，物体XY漂移为0（float32记录精度）、配对xyz误差0、RGB MAE=0.450/255。当前新采集需显式使用此选项；旧入口未改。
- 推动烟测r1：盒净推程12.46cm失败、袋15.31cm通过；非目标XY位移均0，wrong-way=0。延长外推到36cm的r2反而失去接触（盒11.45cm、袋13.34cm），已停用；r3恢复30cm终点、contact_x_bias从+4cm改0后盒19.24cm通过，袋14.98cm未达15cm门限。r4进一步按袋厚度将左掌接触高度降5mm至.840m，盒19.24cm、袋20.94cm均通过；160帧前缀已稳定完成。旧专家参数默认不变。
- 新转换入口 `scripts/prepare_paired_sorting_lerobot.py` 已执行；保留短指令、按layout分组、检查原始NPZ哈希绑定的visual review，拒绝失败/idle诊断数据。两组 `../lerobot/lerobot_sim_paired_zero_pilot32_{a,b}_20260924` 各4400帧state/action/text全数核对；每组96帧视频解码max MAE=1.280/255，无layout泄漏。A/B原始哈希、split、训练统计、编码视频哈希完全一致。
- 正式采集：布局10–21各2任务×160帧，空桌10000–10007各70帧。验证布局预定20/21/10006/10007，同布局两任务不可跨split。转换后必须再跑 `scripts/audit_paired_lerobot.py` 全帧动作/语言检查及视频抽样解码。
- A/B训练配置：`scripts/pi05_paired_pilot32_{a,b}_20260924.env`；同base、seed42、7240步，仅文本不同（A旧统一指令、B任务短指令）。训练/评测串行总入口 `scripts/run_paired_pilot_ab.sh` 已启动；实验目录 `demo/paired_zero_ab_experiment_20260924_r1`（STATUS.json、train_a/b.log、AB_INPUT_AUDIT.json）；主日志 `/tmp/paired_zero_ab_experiment_20260924_r1.log`。评测入口 `scripts/run_pi05_paired_sim.sh` 复用零位/布局/Newton接触，h10、未见布局100–102、空桌20000、seed0/1/2；尚未实际验证模型评测。
- 数据质量总表 `demo/paired_pilot32_quality_20260924.json`：盒净推18.22–19.74cm、袋19.77–21.31cm，非目标XY位移与wrong-way均0（记录精度）；配对位置误差0、首RGB最大MAE=.457/255。训练仅26条3620帧；6条780帧验证。
- **仅数据质量已通过；模型效果必须待h10未见布局、seed0/1/2完成并审查画面。未过前不扩200、不混旧300。**
- r1/r5为启动错误诊断目录，无训练数据；不要将任何这些诊断目录拼入32条正式先导。

---

## 0.【最新】路由诊断完成：混合 300 训黑袋必败，mailer-only 可过（2026-09-24）

300 条 `_r2` 采集质量 OK，但 **混合训练无法同时过 h10 盒+袋**。五件套诊断（`demo/diagnostic_routing_verification/`，2026-09-23 23:51 完成）已钉死根因：

| 层面 | 结论 |
|---|---|
| **数据** | 120/120/60 推程、选手、wrong-way 全 0 问题；**不是标错** |
| **视觉** | frame0 线性分类 **100%** → 能分清盒/袋 |
| **混合训 h10** | unweighted + weighted 各 3 seed：**3/3 黑袋右手、Δy 负** |
| **任务干扰** | mailer-only 108 条重训 → **黑袋 ✓**（左手 Δy +0.43 m），但 **纸盒 ✗**（变左手 +y） |
| **语言 prompt** | 长 prompt 离线几乎不敏感；h10 换 oracle/wrong 短 prompt 行为相近 → **闭环不路由** |
| **open-loop** | 黑袋 f0 预测更接近 mailer GT → 非首帧单步坍缩，是 **闭环多步 + 盒任务主导** |

**禁止**：续训同分布 300、单纯重排 episode、再赌帧加权。**下一步**：改训练策略（task-specific 短 prompt / 分任务训 / task-balanced batch）+ 按约束零位小 pilot 验证。

### 路由失败五件套诊断（完整）

目录：`demo/diagnostic_routing_verification/`（`REPORT.md` + `CONCLUSIONS.json`）  
脚本：`scripts/run_routing_diagnostics.py`、`scripts/run_routing_verification_h10_and_train.sh`

| # | 测试 | 结果 |
|---|---|---|
| ① | Open-loop 首帧 | 黑袋 pred vs mailer GT L2 **0.078** < vs box GT **0.366**；prompt 消融 L2≈**0.014** → 语言几乎不敏感 |
| ③ | Per-task val loss | box **0.00345** / mailer **0.00561** / wait **0.00069**（4162 val 帧） |
| ⑤ | Frame0 分类 | 240 ep（盒+袋）**100%** → vision→action 绑定失败 |
| ② | Oracle h10（原 ckpt `20260922_140103`） | 默认：右手 91 触、Δy **−0.29**；oracle/wrong 短 prompt：无接触、Δy ≈ **+0.12**（均未过 +0.20 m） |
| ④ | Mailer-only 训 + h10 | ckpt `package_sorting_pi05_1gpu_20260923_222034`（108 ep，34518 step）；黑袋 **左手 87 触、Δy +0.43 ✓**；纸盒 **左手 110 触、Δy +0.38 ✗** |

记录目录：② `02_h10_{default,oracle_mailer_prompt,wrong_box_prompt}/`；④ `04_h10_mailer_only_train/`

Mailer-only 训练 env：`pi05_sim_sorting_mailer_only_pilot_20260923.env`；meta：`meta/mailer_only_train_episodes.json`、`mailer_only_train_stats.json`

---

## 0b.【背景】official-hand inactive-park 300：混合训 h10 未过门（2026-09-23）

300 条 `_r2` 已完成 h10 公平闭环 **seed 0/1/2 三轮**（`horizon=10`）。**不能宣称数据对 VLA 闭环已验证成功**。

### h10 闭环（绝对目标区：纸盒 `y≤−0.20 m`，黑袋 `y≥+0.20 m`）

命令：`run_pi05_sorting_sim.sh --horizon 10 --viz none --no-realtime`  
权重：`../lerobot/outputs/package_sorting_pi05_1gpu_20260922_140103/checkpoints/last/pretrained_model`

| seed | 记录目录 | 纸盒 Δy / 手 | 黑袋 Δy / 手 | 空桌 | 判定 |
|---|---|---|---|---|---|
| 0 | `demo/preview_pi05_sorting_officialhand_inactivepark_300_r2_fair/` | −0.382 m / 右手 97 | **−0.221 m / 右手 41** | 通过 | 2/3 |
| 1 | `demo/preview_pi05_sorting_officialhand_inactivepark_300_r2_fair_seed1/` | −0.397 m / 右手 93 | **−0.403 m / 右手 78** | 通过 | 2/3 |
| 2 | `demo/preview_pi05_sorting_officialhand_inactivepark_300_r2_fair_seed2/` | −0.381 m / 右手 86 | **−0.398 m / 右手 81** | 通过 | 2/3 |

结论：**3/3 黑袋均为右手接触、Δy 负向**（应左手、Δy≥+0.20 m）；与 pilot44 同类系统性退化，非单次随机噪声侥幸。离线 held-out loss **0.00445 / 4162 帧** 不能代替上述结果。

### 数据（采集层仍可用作对照，非 VLA 成功证明）

- NPZ：`datasets/sorting_station_g1_23_vla_officialhand_inactivepark_300_r2_20260921`（300）
- Unitree：`datasets/sorting_station_g1_23_unitree_vla_officialhand_inactivepark_300_r2_20260921`（episode 000–299）
- 配比：120 box / 120 mailer / 60 wait。纸盒 Δy 0.339–0.481 m，黑袋 0.212–0.435 m；wrong-way ≤3.5 cm；`table_pen=0`、`assist=0`。写盘前拒绝 237 次（偏心 124、反向 72、靠桌前沿 41），未写入。
- 作废、不要混训：v4 pilot 15 条、黑手碰撞 clean32、所有 smoke、第一份编号错位的 300、V3 pilot32/44、0918 及更早。

### 初始位姿：300 条一致（**不符合** `PROJECT_CONSTRAINTS.md` §1）

采集不随机化机器人。首帧 23 维 `q` 跨 300 条最大差 **4.5e-8 rad**（float32 噪声）。基座不进 npz，场景固定为 `SORTING_ROBOT_POS=(0.08, 0.0, 0.793)`、`SORTING_ROBOT_ROT_XYZW=(0,0,0,1)`，朝 +X，距桌前缘 0.20 m。

本批数据用的是 `U1_REAL_REST_*` 视觉休息角，**双臂非零**；仅腰 yaw=0。新数据须按 [`PROJECT_CONSTRAINTS.md`](PROJECT_CONSTRAINTS.md) 改为 11 关节首帧全 0。以下为该批历史记录（rad）：

| 关节 | 左 | 右 |
|---|---|---|
| hip pitch / roll / yaw | -0.1845 / 0.0004 / -0.0001 | -0.1845 / -0.0004 / 0.0001 |
| knee / ankle pitch / ankle roll | 0.4163 / -0.2224 / ~0 | 0.4163 / -0.2225 / ~0 |
| shoulder pitch / roll / yaw | -0.6478 / 0.2158 / -0.0505 | -0.6478 / -0.2158 / 0.0505 |
| elbow / wrist roll | 1.0025 / 0.2000 | 1.0025 / -0.2000 |

腰 yaw = 0。Unitree 11 维就是上表双臂加腰。

### 加权训练 pipeline（2026-09-23）

- 帧权重：`meta/sorting_frame_weight_policy.json`（`write_sorting_frame_weight_policy.py`）
- 训练代码：`lerobot/utils/sorting_frame_weights.py` + `PI05Config.use_frame_loss_weights`
- 启动：`SimFoundry/scripts/run_pi05_weighted_train_inactivepark_300_r2.sh`
- env：`pi05_sim_sorting_vla_officialhand_inactivepark_300_r2_weighted_20260923.env`（45950 step ≈ 2 加权 epoch）

**加权训练已完成（2026-09-23 18:18）**

- run：`../lerobot/outputs/package_sorting_pi05_1gpu_20260923_161433`（约 2h，45950 step 正常结束）
- checkpoint：`checkpoints/last/pretrained_model` → `045950`
- 末步 train loss ≈ **0.002–0.007**；held-out `validation/loss` **0.005435 / 4162 帧**（加权口径，不可与 unweighted 0.00445 直接比）
- **加权 h10 闭环**（权重 `package_sorting_pi05_1gpu_20260923_161433`，horizon=10）：

| seed | 记录目录 | 纸盒 Δy / 手 | 黑袋 Δy / 手 | 空桌 | 判定 |
|---|---|---|---|---|---|
| 0 | `demo/preview_pi05_sorting_officialhand_inactivepark_300_r2_weighted_fair/` | −0.42 m / 右手 82 | **−0.23 m / 右手 32** | ✓ | 2/3 |
| 1 | `..._weighted_fair_seed1/` | **−0.01 m / 右手 6** | **−0.43 m / 右手 78** | ✓ | 1/3 |
| 2 | `..._weighted_fair_seed2/` | −0.37 m / 右手 83 | **−0.12 m / 右手 26** | ✓ | 2/3 |

结论：**3/3 黑袋仍为右手、Δy 负向**；帧加权 loss 未修复选手路由退化（见 §0 诊断）。

### 加权数据审计（2026-09-23）

脚本：`scripts/audit_inactivepark_300_r2_weighted.py` → `demo/audit_inactivepark_300_r2_weighted/report.json`

帧权重（建议训练/验证 loss 口径）：wait **0.1**；push lift+approach (0–36) **0.25**；press+sweep (37–104) **1.0**；hold (105+) **0.5**。

| 段 | 原始帧占比 | 加权后占比 |
|---|---|---|
| lift+approach | 21.1% | **8.7%** |
| press+sweep | 38.8% | **64.0%** |
| hold | 31.4% | 25.9% |
| wait | 8.6% | **1.4%** |

原始 42028 帧 → 加权等效 **25506** 帧。质量门：推程/选手/wrong-way 仍 **0 问题**；首帧 **action** box vs mailer L2 **0.42 rad**（state 完全相同）。h10 黑袋 3/3 仍失败 → **低 unweighted loss 不能当成功依据**。

### 视觉闸门：通过，可以训练

抽帧在 `demo/audit_inactivepark_300_r2/`。纸盒 episode 0000/0060/0119，黑袋 0120/0180/0239，等待 0240/0270/0299；每条看开始、接触附近、结束。

- 双臂不交叉。非工作手停在画面侧缘，主动手从包裹侧缘向外推。
- 头显画面是台面，未见桌下黑斑。
- 接触是掌侧贴着包裹，个别纸盒帧掌心挡住包裹近缘，不是双臂穿模。
- 末帧包裹常已离开画面。推程 0.3–0.45 m，符合「进入可见侧区」而不是停在画面中央。这不是拒绝理由。

### LeRobot（已完成）

- `../lerobot/lerobot_sim_sorting_vla_officialhand_inactivepark_300_r2_20260921`
- 300 条、42028 帧、15 Hz；train 270 / val 30（按任务 12/12/6）；训练帧 37866；两轮 **75732 step**
- `meta/train_validation_split.json`、`train_only_stats.json`、`recommended_train_steps.json`、parquet、视频都在
- 转换脚本仍是 `prepare_sim_sorting_vla_0915_lerobot.py`，新增 `--task-name`。这次用的 task name 是 `sorting_station_officialhand_inactivepark_300_r2`，repo id `local/officialhand_inactivepark_300_r2`

### 训练（已完成）

- env：`../lerobot/unitree_lerobot_yth_repro_20260908/unitree_lerobot_yth/scripts/pi05_sim_sorting_vla_officialhand_inactivepark_300_r2_20260922.env`
- 从通用 `models/pi05_base` 初始化。expert-only、bf16、batch 1、workers=0、LR `2.5e-5`、warmup 200、decay `2.5e-6`、75732 step
- run：`../lerobot/outputs/package_sorting_pi05_1gpu_20260922_140103`（9/22 17:14 正常结束）
- checkpoint：`checkpoints/last/pretrained_model` → `075732`
- held-out：`validation.jsonl` → loss **0.004448899 / 4162 帧**

### 下一步（诊断后，未过门前禁止扩 300）

1. ~~h10 seed 0/1/2~~、~~加权训~~、~~路由五件套~~ **均已完成**（见 §0）。
2. **训练策略实验**（优先级高）：
   - 写入 **task-specific 短 prompt**（盒/袋/等各一句，非一条长 prompt）
   - **分任务交替微调** 或 task-balanced batch（batch>1 时）
   - 验证 mailer-only + box-only 两 ckpt 能否 **推理时按场景切换**（工程 workaround）
3. **数据**：按 `PROJECT_CONSTRAINTS.md` **11 关节零位** 重采小 pilot（24–32 条）；不要续训同分布 300。
4. **已排除、勿再试**：episode 块重排、帧 shuffle 问题、单纯帧加权、低 offline loss 当成功依据。
5. 只有 h10 三门 **seed 0/1/2 重复通过**，才宣称本批对 VLA 有效或扩到 300。

---

## 0.【已过时】official-hand pilot32 采集中止，先查零动作漂移（2026-09-21 12:25）

- 已创建主目录 `datasets/sorting_station_g1_23_{,unitree_}vla_v4_officialhand_pilot32_20260921`，当前 **15条**：9 box / 4 mailer / 2 wait；不是32条，**暂勿转换或训练**。
- 首批4+4+2审计10/10通过，抽看首/中/末帧正常；随后补录5条box也均严格过门。
- 修复了续录会重放episode-0随机序列的问题：`master_rng` 现在按首个新 `global_ep` 偏移。
- 官方掌侧缘下降间隙从10 cm增至13 cm；独立3 box + 3 mailer smoke用8次尝试完成，6/6审计通过，接受率75%。目录：`...unitree_vla_officialhand_sidepush_offset13_smoke6_20260921`。
- 但继续主集时出现关键反证：手掌尚在 `z≈0.95–0.98 m`（比包裹高约18–21 cm）时，纸盒/黑袋已反向漂移2–5 cm；把settle从30延长到60帧仍无效，且会让部分包裹先漂到 `x<0.35`。因此已停止采集并恢复30帧settle，不能靠多次attempt筛幸运样本。
- 下一步必须先跑 `--sorting-expert idle` 的纸盒/黑袋零动作基线，逐帧记录前80帧XY、速度和接触；若零动作也漂移，修包裹/桌面摩擦、碰撞核心或reset姿态；若零动作稳定，再查高位移动时前臂/手掌完整convex hull是否隔空碰撞。根因修复前不要补齐32条。

---

## 0.【最新、从这里继续】官方 U1 手掌迁移诊断（2026-09-21）

场景于 09-21 换成官方 U1 橡胶手掌视觉/碰撞网格，并同步修改掌心参考和机器人站位。这不是纯外观替换：`PALM_OFFSET` 已从旧代理附近改为官方黑色掌心质心 `(0.20,0,0.007)`，完整碰撞网格 AABB 约为 `x=0–0.253 m, z=-0.0415–0.0650 m`，机器人也由 0.30 m standoff 前移至 0.20 m。因此旧 V3 视频、动作与当前场景同时存在视觉域和接触动力学域偏移，旧模型只作迁移基线，旧数据不要直接混入新训练集。

### 本轮代码与物理标定

- `simfoundry/data/sorting_cartesian_expert.py`：放弃不适合官方楔形 convex hull 的“正上方压住再横扫”，改为从包裹躯干侧 `10 cm` 处下降、用掌侧缘向外扫；接触掌心高度为 `TABLE_TOP_Z+0.095 m`。
- 失败证据：原中心压法10次纸盒尝试全部失败，多次向桌前掉落；单纯把接触高度调到 `+9.5 cm` 虽不掉落但侧移仅2.5 cm，`+8.5 cm`仍向桌前掉落，证明继续调高度是死胡同。
- `scripts/pi05_policy_server.py` / `run_pi05_sorting_sim.sh`：新增 `PI05_EVAL_SEED`，固定 PI0.5 flow noise。
- `scripts/demo_pi05_sorting.py`：summary 新增左右手分别接触帧和掌心最大位移，便于区分“识别/选手失败”与“接触控制失败”。
- `tests/test_sorting_vla_collect.py` 已同步侧缘路径；当前 16/16 通过。

### 新专家最小证据

- 初始 1 box + 1 mailer：`datasets/sorting_station_g1_23_unitree_vla_officialhand_sidepush_smoke_20260921`，2/2 审计通过；纸盒 Δy=41.5 cm、黑袋 Δy=29.1 cm。
- 独立确认 2 box + 2 mailer：`datasets/sorting_station_g1_23_unitree_vla_officialhand_sidepush_confirm4_20260921`，4/4 审计通过：
  - 纸盒 Δy=36.1/40.6 cm，接触84/99帧；
  - 黑袋 Δy=40.1/40.1 cm，接触87/93帧；
  - 全部 `table_pen=0`、`assist=0`；一条纸盒 attempt 因错误方向峰值2.2 cm被门控拒绝，随后重采通过。

### 固定 seed=0 的低成本因果诊断

- E2：`demo/diagnostic_officialhand_e2_seed0/summary.json`
  - 纸盒选对右手（右手8接触帧），但 Δy=+0.5 cm、Δx=-9.0 cm：**动作几何迁移失败**；
  - 黑袋选对左手（左手11接触帧），Δy=+10.0 cm：类别/选手仍在，但官方手掌下接触不足；
  - wait 通过。
- pilot44：`demo/diagnostic_officialhand_pilot44_seed0/summary.json`
  - 纸盒右手5接触帧，Δy=-4.1 cm，失败；
  - 黑袋错误地由右手接触26帧，Δy=-9.3 cm：**24 box / 12 mailer 的 box-boost 导致明确的任务路由退化**；
  - wait 通过。

结论：问题已拆成两条独立因果链：（1）官方手掌使旧动作/接触分布失效；（2）pilot44 类别不平衡使黑袋选手退化。不能用几条旧式 DAgger 轨迹修补，也不能混用旧 V3 作为主训练数据。

### 已选定的数据路线

1. 下一批建立全新的 **official-hand pilot32**，只使用新侧缘专家：12 box + 12 mailer + 8 wait；box/mailer 不仅 episode 数相等，训练帧也应近似相等。上面6条只作 smoke/标定证据，不直接拼接，避免目录与随机序列混乱。
2. 先采 4+4+2 并审计/抽帧；通过后在同一新目录续到12+12+8。不要混 pilot32/pilot44 旧手掌数据，不从 pilot44 checkpoint 续训。
3. 首个训练对照应从同一个通用 base 初始化；若成本必须压缩，可用 E2 作额外迁移对照，但不能把其结果与从 base 训练混为一组。
4. 新 pilot 训练后用 seed 0/1/2 做 h10；每个 seed 均要求正确主动手、box `y<=-0.20`、mailer `y>=+0.20`、wait静止，才扩大到新300条。

---

## 0.【最新、从这里继续】pilot44 已训练但闭环不稳定（2026-09-18 16:39）

用户恢复任务后，已完成上一节要求的 pilot44 训练和两次独立 `horizon=10` 公平闭环。**当前没有运行中的训练、PI0.5 server 或 Isaac 进程，GPU 空闲。项目尚未达到扩采 300 条的门槛。**

### 本轮完成项

- 新训练配置：`../lerobot/unitree_lerobot_yth_repro_20260908/unitree_lerobot_yth/scripts/pi05_sim_sorting_vla_v3_clean_pilot44_boxboost_20260918.env`
  - 数据：`../lerobot/lerobot_sim_sorting_vla_v3_clean_pilot44_boxboost_20260918`
  - 基座：E2（pilot32 累计 4 epoch）checkpoint；expert-only、bf16、batch 1、LR `1e-5 -> 1e-6`、11368 step。
  - `DATASET_REPO_ID` 使用短标签 `local/v3_pilot44_boxboost`，因为原目录名超过 W&B 64 字符 tag 限制。
- 新模型 run：`../lerobot/outputs/package_sorting_pi05_1gpu_20260918_155954`
- checkpoint：`../lerobot/outputs/package_sorting_pi05_1gpu_20260918_155954/checkpoints/last/pretrained_model`
- 训练正常结束，无 NaN/OOM/数据错误；held-out flow loss = **0.0053083247 / 505 帧**。
- 两个启动前失败且无 checkpoint 的空 run（可忽略）：`..._155906`、`..._155927`。

### h10 闭环结果（绝对目标区门槛：纸盒 y<=-0.20 m，黑袋 y>=+0.20 m）

1. `demo/preview_pi05_sorting_v3_clean_pilot44_boxboost_fair/summary.json`
   - 纸盒：y `0.000 -> -0.3281 m`，**通过**；33 touch frames。
   - 黑袋：y `0.000 -> +0.1438 m`，**失败**；9 touch frames。
   - 空桌等待：无物体接触、物体零位移，**通过**。
2. `demo/preview_pi05_sorting_v3_clean_pilot44_boxboost_fair_r2/summary.json`
   - 纸盒：y `0.000 -> -0.0246 m`，**失败**（x 同时前移约 25.5 cm）；
   - 黑袋：y `0.000 -> +0.0970 m`，**失败**；10 touch frames。
   - 空桌等待：**通过**。

结论：pilot44 的离线 loss 虽比 E2 更低，但两次闭环仅 wait 为 2/2；纸盒 1/2、黑袋 0/2，且接触帧很少，表现对随机采样明显敏感。24 box / 12 mailer 的 box-boost 修好了某次纸盒轨迹，却使 E2 原本通过的黑袋退化，存在任务失衡/遗忘；**不能宣称成功，不能开始 V3 300 扩采，也不应继续追加同分布 epoch。**

### 下一步（按顺序，不要直接重跑训练）

1. 先做一个 6–12 条的 **纠错/恢复状态 pilot**，不要只复制现有成功轨迹。采集器需要支持在 press/sweep 初段注入可控偏差（手掌偏高、偏内侧或接触丢失），随后专家根据测得 palm/parcel 位姿持续向下并向正确外侧恢复；纸盒和黑袋等量，避免再次类别失衡。
2. 修改后先跑单测和 2 box + 2 mailer smoke；必须检查前 50 帧已有低位有效接触、无错误方向、无穿模，再录 6–12 条。
3. 新建独立 repair 数据目录，勿覆盖 pilot44；训练时建议与 pilot32/pilot44 做平衡采样，不能简单让新增类别数量主导梯度。
4. repair 模型至少连续 3 次 h10 都满足 box/mailer/wait 三门，才创建全新的 V3 300（120 box / 120 mailer / 60 wait）；正式 300 同样必须保持任务平衡并逐批审计。

---

## 0.0【最新、最高优先级】V3 clean 项目暂停点（2026-09-18 14:00）

用户要求先暂停并写清交接。**当前没有运行中的采集、转换、训练、PI0.5 server 或 Isaac 进程；GPU 空闲。** 下次从本节继续，不要按后面的旧 `0918`/V2 历史段落误操作。

### A. 本轮目标与不可放宽的验收

目标是重新采一批能改善 PI0.5 闭环的物理分拣数据；旧 `0918` 300 条冻结为 V0 对照，不修补、不覆盖。新成功定义：

- 纸盒用右手推到右侧（世界坐标 `y <= -0.20 m`）；
- 黑色塑料袋包裹用左手推到左侧（`y >= +0.20 m`）；
- 空桌双臂保持静止；
- 正式评测固定 `horizon=10`；`h=50` 只可诊断，不能当通过；
- 只有三类闭环都过门，才扩成新 300 条。

### B. 已完成的代码/场景修复

本轮已经落地并通过单测的主要变化：

- Cartesian 分拣专家改为 lift → cross → press → sweep → hold 的位姿门控状态机；当前关键量：`CONTACT_PALM_Z=TABLE_TOP_Z+0.050`、`STAGING_PALM_Z=TABLE_TOP_Z+0.250`、`CONTACT_SIDE_OFFSET=0`、`CONTACT_X_BIAS=0.040`、`EXIT_Y=0.300`。
- 质量门要求侧向位移至少 18 cm、最终稳定进入 `|y|>=0.20 m`、错误方向峰值不超过 1.5 cm、无穿桌、`assist_frames=0`。
- 新增采集前检查：包裹起点 `x>=0.35 m` 且 `|y|<=0.04 m`；过滤 settle 后向桌前/侧面漂移的样本。
- 添加 `--sorting-expert idle` 静置诊断；零动作包裹漂移约 4 mm，场景并非持续自发滑动。
- 当前测试：`tests.test_sorting_vla_collect` 26/26 通过。

相关实现：

- `simfoundry/data/sorting_cartesian_expert.py`
- `simfoundry/data/sorting_quality.py`
- `scripts/collect_seed.py`
- `tests/test_sorting_vla_collect.py`

### C. V3 clean pilot32 数据（已完成）

数据路径（名字保留 `pilot32`，但后面已安全追加到 44 条；见 D）：

- NPZ：`datasets/sorting_station_g1_23_v3_clean_pilot32_20260917`
- Unitree：`datasets/sorting_station_g1_23_unitree_v3_clean_pilot32_20260917`
- 初始 32 条配比：纸盒 12、黑袋 12、等待 8；4267 帧。
- 纸盒 Δy min/median/max = 0.247/0.295/0.397 m；黑袋 = 0.224/0.238/0.267 m。
- 全部 `table_pen_frames=0`、`assist_frames=0`；错误方向峰值最大约 1.4 cm。
- Unitree 11D 审计 32/32 通过，active action 最大单步约 0.0842 rad，state 最大单步约 0.0313 rad。
- NPZ 23D 审计会因录制开头腿部 settle（约 0.1359 rad）提示 review；训练只使用 Unitree 11D 双臂+腰数据，因此训练输入审计是干净的，但交付时要保留这个说明。

原 pilot32 LeRobot：

- `../lerobot/lerobot_sim_sorting_vla_v3_clean_pilot32_20260917`
- train 29 / val 3，训练 3878 帧，2 epoch = 7756 step。

### D. pilot44 box-boost 数据（当前最新数据，已转换完成）

因为续训模型已能正确推黑袋但纸盒接触不足，本轮向上述 NPZ/Unitree 目录**安全续录**了 12 条严格过门纸盒轨迹，episode 032–043；没有覆盖 000–031。

当前原始数据总计：

- **44 条连续 episode 000–043**；纸盒 24、黑袋 12、等待 8；
- NPZ 与 Unitree 均为 44 条；
- 新增纸盒仍要求错误方向 `<=1.5 cm`，无辅助、无穿桌；有效 Δy 大致 0.236–0.316 m，接触约 70–102 帧；
- 采集时有不少 attempt 被质量门拒绝（反向偏移、无有效位移、settle 后起点越界），这些 reject 没有写入数据集。

最新 LeRobot 已完整生成并核对：

- `../lerobot/lerobot_sim_sorting_vla_v3_clean_pilot44_boxboost_20260918`
- train 40 / val 4；验证 episode `[8,19,24,36]`，按任务分层；
- train frames = 5684；推荐 2 epoch = **11368 step**；
- `data/chunk-000/file-000.parquet`、17 MB 视频、split、train-only stats、recommended steps 均存在。

注意：用户中断时看见的是转换监控被打断，但转换进程随后已经正常完成；不要无条件重转。下次先读上述 `recommended_train_steps.json` 和 split 即可。

### E. 已训练模型与闭环证据

#### E1. pilot32 首版（2 epoch）

- run：`../lerobot/outputs/package_sorting_pi05_1gpu_20260918_095428`
- checkpoint：`checkpoints/last/pretrained_model`（step 7756）
- held-out flow loss：**0.01148236 / 389 帧**。
- h10 两次：
  - 纸盒 Δy `+1.74 cm`、`+4.23 cm`（方向错），且 Δx `-36.45/-26.59 cm`，被带向桌前；
  - 黑袋 Δy `+11.29/+10.96 cm`（方向对但未过 +20 cm）；
  - wait 2/2 通过。
- 记录：`demo/preview_pi05_sorting_v3_clean_pilot32_fair`、`..._fair_r2`。
- h50 诊断也失败：纸盒 +1.56 cm，黑袋 -29.77 cm 反向，证明不是单纯 h10 前缀循环。目录：`demo/preview_pi05_sorting_v3_clean_pilot32_h50_diagnostic`。

#### E2. pilot32 低学习率续训（累计 4 epoch）

- 续训 env：`../lerobot/unitree_lerobot_yth_repro_20260908/unitree_lerobot_yth/scripts/pi05_sim_sorting_vla_v3_clean_pilot32_continue2_20260918.env`
- run：`../lerobot/outputs/package_sorting_pi05_1gpu_20260918_102921`
- checkpoint：`checkpoints/last/pretrained_model`
- 从 E1 权重继续 7756 step，LR `1e-5 → 1e-6`；held-out loss 降到 **0.00922805 / 389 帧**。
- 正式 h10：
  - 纸盒：Δy `+1.98 cm`，失败；触碰仅 17 帧，横向传力不足；
  - 黑袋：Δy `+26.91 cm`，成功，97 触碰帧，并且已学会左手主动/右手静止；
  - wait：通过。
- 记录：`demo/preview_pi05_sorting_v3_clean_pilot32_continue2_fair`。

结论：追加训练解决了视觉类别→左右手分工，但**没有解决纸盒接触/传力**。离线 loss 下降不能代替闭环过门。目前绝对不能宣称项目成功，也不能扩 300。

### F. 已排除的误诊

- GPU/驱动健康；先前 `/dev/nvidia*` 不可见是 Codex 沙箱隔离，主机 RTX PRO 5000 48 GB 正常。
- LeRobot 视频不是错位：episode 视频时间段连续单调；用实际 loader 抽取 episode 0/12/24 分别确认为纸盒/黑袋/空桌。
- h50 不能救该模型，说明不是仅由 h10 重规划造成。
- 黑袋训练纹理常有明显白色面单，而闭环默认黑袋面单不明显，存在一定视觉分布差异；但续训后黑袋已通过，当前首要问题仍是纸盒接触。

### G. 下一次恢复时的精确顺序

1. **不要再采数据，先训练 pilot44。** 新建一个 env（尚未创建），以 E2 checkpoint 为 `PI05_BASE_MODEL_ROOT`，数据改为 `lerobot_sim_sorting_vla_v3_clean_pilot44_boxboost_20260918`，split/stats 指向该目录，`PI05_STEPS=11368`，建议 LR `1e-5`、warmup 100、decay `1e-6`、expert-only、bf16、workers=0、val freq 大于 steps（末步仍自动验证）。
2. 训练完成后先看完整 4-episode held-out loss，但**只用 h10 闭环决定成败**。
3. 跑 `scripts/run_pi05_sorting_sim.sh --horizon 10 --viz none --no-realtime`。至少要求纸盒 `y<=-0.20`、黑袋 `y>=+0.20`、wait 静止；首轮通过后再跑 r2/r3 排随机性。
4. 若 pilot44 仍然纸盒失败：停止追加 epoch/追加同分布轨迹；先修改专家使纸盒在前 50 步内产生更低、更长的有效接触，并采 DAgger/纠错状态（手已经偏高或偏到包裹内侧时，目标动作仍向下并向外）。先做 6–12 条修复 pilot，再训练。
5. 只有 h10 三场景重复通过后，才新建 V3 300 目录，建议配比 120 纸盒 / 120 黑袋 / 60 wait。不要继续往 pilot44 目录扩 300。
6. 项目最终完成时再更新本节，写入新 300 路径、审计、训练权重、三次闭环结果。

### H. 暂停时的重要文件

- 当前最有希望的已有权重（黑袋/wait 过，纸盒不过）：`../lerobot/outputs/package_sorting_pi05_1gpu_20260918_102921/checkpoints/last/pretrained_model`
- 最新待训练数据：`../lerobot/lerobot_sim_sorting_vla_v3_clean_pilot44_boxboost_20260918`
- 初始训练 env：`../lerobot/unitree_lerobot_yth_repro_20260908/unitree_lerobot_yth/scripts/pi05_sim_sorting_vla_v3_clean_pilot32_20260917.env`
- 续训 env：`../lerobot/unitree_lerobot_yth_repro_20260908/unitree_lerobot_yth/scripts/pi05_sim_sorting_vla_v3_clean_pilot32_continue2_20260918.env`
- 最新正式闭环 summary：`demo/preview_pi05_sorting_v3_clean_pilot32_continue2_fair/summary.json`

---

## 0.0 分拣场景 V2 重采状态（2026-09-16，优先于旧300条结论）

用户已确认：**旧300条不修补，冻结为 V0 对照；按 V2 场景重新采集；成功定义为包裹稳定进入左右侧分拣区，不要求落入画面外料箱。**

本轮已完成代码侧改造：

- 修复采集因果对齐：保存 `(observation_t, action_t)` 后才执行动作，不再把 post-step 图像配给前一动作。
- 终止帧在写入前隔离，避免 Isaac 自动 reset 返回的默认姿态混入 episode。
- 推动轨迹从约195帧缩短到约120帧（完整94步 sweep + 稳定保持），减少约一半无效尾帧。
- 新质量门：纸箱进入 `y <= -0.26 m`、黑色包裹进入 `y >= +0.26 m`，最终连续保持至少10帧；掉桌一律失败；仍要求正确主动手、有效接近和无穿桌。
- 黑色包裹改为“内缩刚性碰撞核心 + 独立不规则塑料视觉外壳”；纸箱改为刚性核心 + 倒角硬纸板外壳。主纸箱尺寸升级为 `0.14×0.09×0.045 m`，黑色包裹为 `0.15×0.145×0.040 m`。
- U1 手掌碰撞块从脱离可视手掌的 `x=0.16 m` 移到 `x=0.06 m`，宽度由10 cm缩到6.4 cm，并同步 `PALM_OFFSET`，降低“隔空碰撞/视觉穿模”。
- 地面安全平面下移3 cm，消除其与地毯顶面共面造成的 RTX z-fighting（桌下黑斑闪烁的直接嫌疑）。
- 新入口：`scripts/collect_vla_sorting_v2.sh`；默认新目录标签 `v2_smoke_20260916`，不再用容易误解为日期的 `0918`。
- 静态测试：`tests.test_sorting_vla_collect` + `tests.test_scene_package` 共24项通过。

对旧300条重新运行增强审计后，只有191条直接通过，109条需复核；其中大量198帧轨迹检测到 `0.84–0.93 rad` 的 state 突跳，证实终止自动重置污染。旧数据因此不再作为推荐主训练集。

**GPU状态已澄清：** 主机GPU健康；沙箱外 `nvidia-smi` 正常识别 RTX PRO 5000 Blackwell、驱动580.105.08和48 GB显存。此前失败是Codex默认受限沙箱未映射 `/dev/nvidia*`，不是驱动或硬件故障。Isaac/RTX需在获准的主机执行环境中运行。下一步仍必须按顺序执行：2+2+1 smoke → 人工看首/中/末帧和碰撞 → 12条 → 32条 → 训练公平闭环；过门后才采新300条。

---

## 0. 0918 项目最终状态（本节覆盖下方旧状态说明）

面向模型训练师的数据交付、利弊、混训建议和真机验证说明见：`PI05_SORTING_DATA_TRAINER_GUIDE.md`。

真机 A/B 尚未执行：现有 `real-only` 权重，但 `real+sim32`、`real+filtered-sim300` 权重不存在；主机GPU正常，但仍未连接可确认的 G1/RTC，详见上述说明第 10 节。不得把离线或仿真结果写成真机闭环证明。

本轮已完成 **300 条 Cartesian-Jacobian 物理分拣数据**，并完成转换、两轮训练和重复公平闭环评测。旧 0916/0917 接触状态机失败结论仅作为历史记录；当前采集专家是 `sorting_cartesian_expert.py`。

### 数据与质量

- NPZ：`datasets/sorting_station_g1_23_vla_0918`，300 条，episode 0..299 连续
- Unitree：`datasets/sorting_station_g1_23_unitree_vla_0918`，300 条
- 配比：纸盒 120、黑袋 120、空桌等待 60
- LeRobot：`../lerobot/lerobot_sim_sorting_vla_0918`
- 总帧数 47,758；train 270 / val 30；训练帧 43,035
- 全部 `assist_frames=0`、腰 action=0、无穿桌、统一英文 prompt
- 纸盒 Δy：min 8.02 cm / median 16.71 cm / max 24.91 cm
- 黑袋 Δy：min 8.56 cm / median 13.40 cm / max 35.32 cm
- 主动关节最大单步 <0.034 rad，action-state MAE 中位约 0.004

### 模型结论

**推荐/当前最佳模型（32 条质量试点）：**

`../lerobot/outputs/package_sorting_pi05_1gpu_20260915_160015/checkpoints/last/pretrained_model`

- 8844 步，held-out loss 0.01034（420 帧）
- 公平闭环 h10 三次：纸盒 −18.10 / −10.56 / −7.65 cm（方向 3/3，过 8 cm 2/3，中位 −10.56）；黑袋 +12.28 / +14.20 / +15.18 cm（3/3 过）；wait 3/3 无误触
- 相对 0915 的纸盒 **+19.6 cm 反推**，已改为稳定正确方向；这是本项目实际闭环改善最大的权重

**300 条全量模型（保留作研究，不替换推荐模型）：**

`../lerobot/outputs/package_sorting_pi05_1gpu_20260916_092142/checkpoints/last/pretrained_model`

- 86070 步（2 epochs），held-out loss 0.00445（4723 帧）
- 公平闭环 h10 三次：纸盒 −4.77 / −9.44 / −6.91 cm（方向 3/3，过门 1/3，中位 −6.91）；黑袋 +8.98 / +26.07 / +8.71 cm（3/3 过）；wait 3/3 无误触
- 离线 loss 更低，但纸盒闭环稳定性弱于 32 条模型。不要仅按 val loss 宣称它更好

评测产物：

- 试点：`demo/preview_pi05_sorting_vla_0918_fair`、`..._pilot_fair_r2`、`..._pilot_fair_r3`
- 全量：`demo/preview_pi05_sorting_vla_0918_300_fair`、`..._300_fair_r2`、`..._300_fair_r3`

实现与入口：

- Cartesian 专家：`simfoundry/data/sorting_cartesian_expert.py`
- 安全续录：`scripts/collect_seed.py`（自动找下一 episode，不覆盖）
- 采集入口：`scripts/collect_vla_sorting_0918.sh`
- 训练配置：`../lerobot/unitree_lerobot_yth_repro_20260908/unitree_lerobot_yth/scripts/pi05_sim_sorting_vla_0918.env`

---

## 1. 现在处在哪一步

**脚本 stump BC 这条路已经停。** 最后一遍「接触状态机专家」烟测未过门：掌心扫到 y≈−0.30，但 z 一直 ≈0.90（空中挥），纸盒 Δy 只有 2–6 cm。按约定 **没有采 32 条，没有转 LeRobot，没有开训。**

Isaac 采集进程已停，GPU 空闲。

当前仍可评的最后一套权重是 **0915**（时间表专家、开环 32/32 过、公平闭环纸盒反推）。**0915 不能当可用闭环策略。** 不要用 0916/0917 smoke 训。不要 `--wipe` 0911/0912/0914/0915。

成功标准只认：**公平闭环 horizon=10，双臂 Δy≥8 cm 且方向对，wait 静止。** 这之前不扩 300。

---

## 2. 目标与硬约束

目标是 **采集能提升 VLA 闭环效果的仿真数据**，不是把开环过门率刷高，也不是盲扩到 300。

统一英文 prompt（真机 `lerobot_v3.0`、采集、闭环必须同一句）：

```
Sort the package on the table by type. If there is no package on the table, keep both arms still and wait. If it is a black bag, press and hold the bag down with the left hand, then push it to the left sorting area. If it is a box, press and hold the box down with the right hand, then push it to the right sorting area.
```

几何：

- 机器人朝 **+X**；桌前缘 `TABLE_FRONT_X=0.28`；桌面 `TABLE_TOP_Z=0.775`
- 纸盒推 **−Y（右）**；黑袋推 **+Y（左）**
- 单包裹休息位 `SORTING_BOX_REST_SINGLE=(0.40,-0.18,TABLE_TOP_BOX_Z)`、`SORTING_MAILER_REST_SINGLE=(0.40,0.18,…)`
- 旧双包裹位 `SORTING_BOX_REST=(0.30,-0.16)` **不要再当评测/采集摆位**
- 纸盒尺寸 `(0.13, 0.08, 0.025)`（高 2.5 cm）
- G1 EDU **23DoF**（不是 29）：腰只有 yaw；每臂 5 DoF（无腕 pitch/yaw）
- `+pitch` 抬/收回；`−pitch` 伸向 +X
- 动作是相对 `u1_sorting_default_qpos()` 的 offset
- **`--push-assist` 关**（`assist_frames` 必须为 0）
- 腰采集时锁 0（D435i 在躯干上；真机 v3.0 腰 yaw std≈0.87°）。`collect_seed.py` 里 `act_np[_TORSO_I]=0`
- Isaac `soft_joint_pos_limit_factor=0.92`。`|shoulder-roll offset| ≳ 0.80` 会把掌抬到 z≈1.1

运行：

- IsaacLab：`conda activate env_isaaclab`，在 `IsaacLab/` 下 `./isaaclab.sh`
- `OMNI_KIT_ACCEPT_EULA=yes DISPLAY=:1`，**不要 `--headless`**，用 `--viz none` 或 `--viz kit`
- Isaac 与 PI0.5 **不能同进程**；训练与 Isaac 串行；评测可以 PI0.5 server + Isaac 两进程同 GPU
- GPU：1× RTX PRO 5000 ~48GB。不要杀别人的 GPU 进程
- 长任务用 `setsid`/`nohup` 写 `/tmp/collect_vla_*.log`
- `PI05_PYTHON=/home/user/Desktop/project/vla/env/.venv/bin/python`

质量门（`sorting_quality.py`）：`MIN_PUSH_DISPLACEMENT_Y=0.08`，`OUT_OF_FRAME_Y=0.22`，桌上 `PARCEL_DROP_Z=桌面−10cm`，主动手 `Δy≥8cm`，`assist=0`。触碰统计从 **phase≥0.35** 才计。掉桌且侧向 Δy&lt;5 cm 不算成功。

公平闭环：`demo_pi05_sorting.py --horizon 10`（模型 chunk=50，只执行前 10 步再按新图重问，对齐真机 RTC 默认 horizon=10）。`--viz none --no-realtime`。

checkpoint 的 `last` 是 **symlink**，删编号目录会掏空 last。根分区曾 100%；已删部分旧 run 的非 last 编号 ckpt。**不要动** 0912 `20260912_155545`、0914 `20260914_140656`、0915 `20260915_090502` 的 last。

---

## 3. 已经完成的内容

### 3.1 场景与采集动作

采集入口仍是 `scripts/collect_seed.py`。物理路径会清零 scripted 关键帧再调 `press_and_sweep_palm`。当前代码是 **接触状态机**（`ContactSweepState`：press → sweep → hold），`calibration_tag=sorting_station_vla_contact_sweep_2026-09-15b`。

活位姿只用来切模式；关节仍是 feed-forward（冻结 `plan.sign` + mode + `t_mode` / `sweep_s`），不要 IK 追包裹 XY（0910b 教训）。

代码现状（烟测未达标，不要用这些条训）：

- `_parcel_reached_bin`：**只认 |y| 过料线**，掉桌不切 hold（0916 曾把前缘掉桌当到达）
- 包裹未过 `plan.y_bin` 就继续 sweep（不要 timeout 切 hold）
- 右手正 roll = 向里。`_PRESS_ROLL=-0.08`、`_EXIT_ROLL=-0.28`（对齐 `real_keyframes` `RIGHT_CONTACT`→`RIGHT_DRIVE`）
- 采集脚本：`scripts/collect_vla_sorting_0917.sh MIX TAG [ATTEMPTS]`，默认 attempts=10，**不要 `--wipe`**
- 测试：`tests/test_sorting_vla_collect.py` 的 contact-sweep 用例已过

掌垫碰撞（画面不可见、碰撞在）：USD `Cube "box"` `size=2`，`scale=(0.028,0.050,0.032)`，`translate=(0.16,0,-0.018)`，`visibility="invisible"`。`PALM_OFFSET=(0.16,0.0,-0.018)`。休息掌大约 `(0.35, ±0.19, 0.84)`。

### 3.2 数据与训练（保留，勿 wipe）

| 数据集 | 条数 | 说明 |
|---|---|---|
| `unitree_vla_0910` | 32 | 旧停扫。开环抽查差、掉桌。不要训、不要 wipe |
| `unitree_vla_0910b` | 28 | 每帧追包裹 XY，记角开环回放丢接触。不要训 |
| `unitree_vla_0911` | **300** | 0911 脚本扩到 300。val loss 0.009→0.0045，**公平闭环几乎不变** |
| `unitree_vla_0912` | 32 | 贴合 0.32。开环过。公平闭环：纸盒 −8.9 cm 过，黑袋 −20.5 cm 反 |
| `unitree_vla_0914` | 32 | 贴合 0.12。公平闭环：纸盒 +3.1 cm 反，黑袋 +11.1 cm 过 |
| `unitree_vla_0915` | **32（12+12+8）** | 纸盒贴合 0.28 / 黑袋 0.12。开环 32/32。公平闭环：**纸盒 +19.6 cm 反**，黑袋 +10.0 cm 过，wait 过 |
| `unitree_vla_0916_*` / `0917*_smoke` | 烟测碎片 | **不要训**。空挥、掉桌、80 次抽奖幸运条 |

不要训 / 不要混：`unitree_0902`、0910/0910b、灰块可见的旧 smoke、0916/0917 smoke。

PI0.5（0915 是最后训完的一套）：

- LeRobot：`lerobot/lerobot_sim_sorting_vla_0915`（train 29 / val 3，4424 帧，2 epoch=8848）
- env：`lerobot/.../scripts/pi05_sim_sorting_vla_0915.env`
- `PI05_STEPS=8848`（2 epoch），**`PI05_NUM_WORKERS_PER_PROCESS=0`**
- 权重：`lerobot/outputs/package_sorting_pi05_1gpu_20260915_090502/checkpoints/last` → `008848`（val loss ≈0.015）
- 对照：0912 `20260912_155545` last→008820；0914 `20260914_140656` last→008842
- 0911 扩 300 的 run 在 `20260911_*`（其中 `215024` last→085956）

转数据模板：复制 `prepare_sim_sorting_vla_0915_lerobot.py`，不要覆盖 0914/0915。

### 3.3 公平闭环对照（同一协议，horizon=10）

目录：`demo/preview_pi05_sorting_vla_091{2,4,5}_fair/`，0914 另有 `..._h50`。

| 集 | 纸盒 Δy | 黑袋 Δy | 说明 |
|---|---|---|---|
| 0912 贴合 0.32 | −8.9 cm 过 | −20.5 cm 反 | 大贴合救纸盒、毁黑袋 |
| 0914 贴合 0.12 | +3.1 cm 反 | +11.1 cm 过 | 缩小贴合对调成功的手 |
| 0915 纸盒 0.28 / 黑袋 0.12 | **+19.6 cm 反** | +10.0 cm 过 | 拆开贴合纸盒更差；右手停在 y≈−0.06 |
| 0911 32→300 | 闭环几乎不变 | 同左 | loss 下降无用 |

h50（0914 权重）：纸盒手扫到 y=−0.37、盒到 −0.24 后弹回（掌抬到 z≈0.91）；黑袋从 11 cm 退到 5.8 cm。**horizon 不是银弹。**

评测命令骨架（0915）：

```bash
export PI05_LOCAL_CONFIG=/home/user/Documents/zoo/sim/lerobot/unitree_lerobot_yth_repro_20260908/unitree_lerobot_yth/scripts/pi05_sim_sorting_vla_0915.env
export PI05_POLICY_PATH=/home/user/Documents/zoo/sim/lerobot/outputs/package_sorting_pi05_1gpu_20260915_090502/checkpoints/last/pretrained_model
export PI05_RECORD_DIR=/home/user/Documents/zoo/sim/SimFoundry/demo/preview_pi05_sorting_vla_0915_fair
bash /home/user/Documents/zoo/sim/SimFoundry/scripts/run_pi05_sorting_sim.sh --horizon 10 --viz none --no-realtime
```

---

## 4. 卡住的问题

1. **开环时间表专家 + 成功过滤 + BC + 短窗闭环，目标反相关。** 采集门控看整条 ~195 帧峰值 Δy；评测 h=10 时模型看到的是「手按着、东西几乎没动」，时间表里这对应继续贴合，不是外扫。贴合越大开环越好，h=10 越把贴合循环，纸盒推向躯干。
2. **23-DoF 接触–外扫做不到可复现。** 没有腕 pitch。能扫出 ~10 cm Y 的肩 roll 会把垫子抬到 z≈0.90（纸盒顶 ≈0.79）。肘补偿压不回去。0917e 纸盒连续 3 次 REJECT，掌心中段 `(0.36, −0.30, 0.90)`。
3. **VLA 缺的是闭环条件分布，不是条数。** 真机 `lerobot_v3.0` 293 条、11 维、15 Hz、腰几乎为 0。仿真锁腰是对齐真机。0911 复印到 300 不改善闭环。
4. **脚本专家出不了「手在包裹上、东西仍在桌心 → 外扫」的配对。** 这是 receding-horizon=10 真正查询的 (obs, action)。接触状态机改了逻辑，物理没改过来。
5. **Cursor 长任务会 abort。** 用 `setsid`/`nohup`。杀采集时不要误杀他人 GPU 进程。

---

## 5. 下一步计划（按顺序）

不要 `--wipe` 0911/0912/0914/0915。不要混 0902。不要再拧共用 `_START_ROLL`。不要用 h50 当修法。不要把 0915 扩 300。不要 Isaac 与训练同进程。

1. **承认脚本 stump BC 做不稳这条技能。** 0917 最后一遍已试穿：掉桌不当成功、不向里顶、关键帧 roll、少 attempts，烟测仍空挥。
2. **若还要这条技能：** 仿真遥操作，专门录「手压在包裹上且仍在桌心 → 外扫」的配对；再 12+12+8 → 新目录（例如 `unitree_vla_0918`），抽帧检查过再训，公平闭环 h10。金标准：相对 0915，纸盒从反推变成朝 −Y 过门，黑袋仍过。
3. **若不上遥操作：** 停在 0915 对照，不要再开一轮脚本采集/训练。
4. 双臂过门后再谈 300 / 视觉覆盖。

0917 烟测入口（仅当专家物理真的过门后再用；当前不要当训练集）：

```bash
bash /home/user/Documents/zoo/sim/SimFoundry/scripts/collect_vla_sorting_0917.sh \
  "push_box_to_bin:1,nudge_mailer_to_bin:1,wait_no_package:0" 0917e_smoke 8
```

开环回放骨架：

```bash
source ~/miniconda3/etc/profile.d/conda.sh && conda activate env_isaaclab
export OMNI_KIT_ACCEPT_EULA=yes DISPLAY=:1 PYTHONUNBUFFERED=1
cd /home/user/Documents/zoo/sim/IsaacLab
./isaaclab.sh -p ../SimFoundry/scripts/replay_unitree_sorting.py \
  --dataset ../SimFoundry/datasets/sorting_station_g1_23_unitree_vla_0915 \
  --episodes 0,4,8,12,16,20 --device cuda --viz none \
  --record-dir ../SimFoundry/demo/replay_vla_0915_spot6
```

---

## 6. 踩过的坑（按优先级）

### 开环过门 ≠ VLA 有用

时间表 `关节=f(phase)` + 整条峰值 Δy 过滤，训出来的策略在 h=10 下循环贴合。用开环 ACCEPT / val loss 迭代会越改越错。

### 内侧大贴合是闭环毒药

0912 `_START_ROLL=0.32` 开环好、纸盒闭环过、黑袋反。0915 纸盒 0.28 闭环把盒子推向躯干（+19.6 cm）。receding-horizon=10 会把贴合前缀当成「桌上有包裹时该做的事」。

### 正 roll 对右手是向里

`sign * (+0.08)` 把纸盒从 y≈−0.18 拱到 −0.10。应对齐 `RIGHT_CONTACT` roll **−0.08**（向外）。0917c 犯过这个符号错。

### 冻 sweep 等掌降低 = 死锁

0917 第一次：`sweep_s` 只在 z&lt;0.837 时增加。掌一直 0.85，133 帧停在向里 mill，盒子 +5 cm。空挥和冻扫是对称失败。

### 掉桌当到达会提前 hold

`z < PARCEL_DROP_Z` 切 hold → 从前缘掉桌后空气里挥完就停。现已改为只认 y 料线。

### 80 次 `max-attempts` 抽奖

0916_smoke4 纸盒 53 次 REJECT 后写盘 Δy=5.7 cm。幸运带子不是训练集。烟测应少 attempts（8–10），过门率低就改脚本。

### 助推把包裹 Y 写进 pose

`maybe_assist_push` 运动学滑 Y，`assist_frames` 常 >100。质量门过了，PhysX 没推。0902 不能训。VLA 必须 `push_assist=False`。

### 0910b 追包裹 XY

每帧 IK/PD 追活位姿，记下来的关节开环回放丢接触。新专家可以用活位姿 **切模式**，关节必须 feed-forward。

### `|roll|≳0.80` 把手抬到 z≈1.1

Δy 塌掉。23-DoF 侧向主要靠 roll，但 roll 会抬掌。当前 `_ROLL_CAP=0.40`。0917e 在 cap 内仍抬到 z≈0.90。

### 停扫回到休息位 = 反向扫

hold1/hold2 的旧教训：过门后归休息或 offset=0 会把包裹打飞。应冻在出料侧。接触 SM 的 hold 仍是 park roll。

### 评测摆位和采集不一致

采集单包裹 x≈0.40，评测曾用双包裹 x=0.30。不公平评测里纸盒会走左手。已改 `demo_pi05_sorting.py`。

### 掌垫 / 抬掌 / 可见灰块

`size=1` 垫太薄。`correct_palm_height` 把掌停在桌面上约 6 cm，物理采集不要当专家主路径。可见灰块的数据不要训。

### 训练 decoder 崩

AV1 + torchcodec 多进程：`Could not push packet to decoder`。`PI05_NUM_WORKERS_PER_PROCESS=0`。

### `last` symlink 与 `--wipe`

删编号 ckpt 目录会掏空 `last`。`collect_*.sh` 的 `--wipe` 只对空的新目录用。永远不要对 0911/0912/0914/0915 加 `--wipe`。

### Cursor 长任务 abort

`collect_seed.py` 挂在 Cursor shell 上会被标 aborted 并杀掉。用 `setsid`/`nohup`。

---

## 7. 关键文件

| 用途 | 路径 |
|---|---|
| **项目硬约束** | [`PROJECT_CONSTRAINTS.md`](PROJECT_CONSTRAINTS.md) |
| **officialhand 300 h10** | `demo/preview_pi05_sorting_officialhand_inactivepark_300_r2_fair/summary.json` |
| officialhand 300 权重 | `../lerobot/outputs/package_sorting_pi05_1gpu_20260922_140103/checkpoints/last/pretrained_model` |
| 采集动作 / 接触 SM | `simfoundry/data/sorting_push_assist.py` |
| 质量门 | `simfoundry/data/sorting_quality.py` |
| 几何 / 休息位 | `simfoundry/calibration/sorting_station.py` |
| 关键帧对照 | `simfoundry/data/real_keyframes.py`（`RIGHT_CONTACT` / `RIGHT_DRIVE`） |
| 采集入口 | `scripts/collect_seed.py` |
| 0917 采集脚本 | `scripts/collect_vla_sorting_0917.sh`（新树；attempts 第 3 参） |
| 开环回放 | `scripts/replay_unitree_sorting.py` |
| 闭环评测 | `scripts/demo_pi05_sorting.py`、`scripts/run_pi05_sorting_sim.sh` |
| 0915 权重 | `lerobot/outputs/package_sorting_pi05_1gpu_20260915_090502/checkpoints/last` |
| 0915 LeRobot | `lerobot/lerobot_sim_sorting_vla_0915` |
| 训练 env | `lerobot/.../scripts/pi05_sim_sorting_vla_0915.env` |
| 单元测试 | `tests/test_sorting_vla_collect.py` |
| 过期脚本 | `collect_vla_sorting_0910.sh` / `0910b.sh`（会 wipe 或追加，别再跑） |
| 掌垫 USD | `assets/robots/g1_23dof_u1_rubber/g1_23dof_rev_1_0_u1_black/payloads/base.usda` |

相关会话：[分拣采集 PI0.5](99337b84-64fd-4870-a9e3-03bb0f2d72c6)（Cursor agent transcript，不含 `.jsonl` 后缀）。

---

## 8. 2026-09-21 续作：官方手碰撞因果诊断与当前采集

### 已确认

- 零动作诊断证明包裹漂移不全由手造成：旧三角网格碰撞核会自漂；包裹改为解析 `CuboidCfg` 后，黑袋末态漂移约从 11.4 cm 降至 0.7 cm。
- 官方手原碰撞引用包含银色前臂的整手网格，`convexHull` 大于可见黑手。现生成 `payloads/hand_collision.usda`，碰撞只取 x>=0.088 的官方黑手；视觉仍为完整官方手。
- 黑手碰撞烟测 4/4 一次通过：纸箱 Δy=0.418/0.413，黑袋 Δy=0.242/0.440；无桌面穿透，反向峰值 0–2.5 cm。
- 扩展时仍有少量随机种子反向顶动，质量门会拒绝；尝试“掌块裁剪”“凸包内缩”“对侧手不交叉”等方案均产生新的运动学/接触退化，已回退到上述 4/4 基线，不再局部调参。
- `tests/test_sorting_vla_collect.py` 当前 16/16 通过。

### 当前数据与运行状态

- 新干净先导集（不要与旧15条或各 smoke 混训）：
  `datasets/sorting_station_g1_23_unitree_vla_officialhand_blackcollision_clean32_20260921`
- 对应 NPZ：
  `datasets/sorting_station_g1_23_vla_officialhand_blackcollision_clean32_20260921`
- 已写入3条合格纸箱；正在续采剩余 `9 box + 12 mailer + 8 wait`，进程日志：
  `/tmp/collect_vla_officialhand_blackcollision_clean32_20260921.log`
- 为降低落稳后从桌前沿悬出的拒绝，单包裹生成 X 从 0.43 调到 0.46；目标是落稳实测仍约 x=0.36，保持与前三条一致。

### 下一闸门（不可跳过）

1. 先完成32条并统计按类别接受率、wrong-way、推程、桌面穿透。
2. 抽查每类至少3条的开始/接触/结束帧，确认无穿模、抖动、桌下黑斑和双臂异常。
3. 只有32条通过，才在同一最终物理版本新建300条目录；建议配比 `box 120 / mailer 120 / wait 60`。
4. 300条完成后再转 LeRobot；旧官方手15条和所有 smoke/失败实验目录均不可混入训练。

### 32条完成后的审计结论（2026-09-21）

- 先导集已完成：12 box + 12 mailer + 8 wait = 32条，采集进程正常退出，并非GPU或程序崩溃。
- 数值质量：box 推程 0.383–0.441 m（均值0.414），wrong-way 0–0.033 m；mailer 推程 0.235–0.455 m（均值0.377），wrong-way 0–0.025 m；全部 table penetration=0、assist=0。
- 续采日志有18次未写盘拒绝：13次初态偏中心线、4次 wrong-way、1次靠近桌前沿；质量门工作正常。
- 视觉闸门 **未通过**：抽查 episode 0000/0011/0012/0023/0024/0031 的中段和末帧，仍可见双臂交叉，以及手掌与包裹接触区的视觉重叠。桌下黑斑在这些抽帧中未复现，但抽帧不能证明整段无闪烁。
- 因此当前32条仅用于诊断，不应立即扩采300或交给训练；下一步必须修正不交叉动作，同时保持足够侧向推程，并增加逐帧视觉穿模/闪烁审计。

### 不交叉轨迹解决与300条启动（2026-09-21 17:10 CST）

- 对侧手直推方案因五自由度末端工作空间不足，出现峰值到侧区但末态回弹，已停止，不再使用。
- 最终方案：保留已验证的长推程主动手；主动手越过中心线前，将非工作手 shoulder-roll 外移（左手 +0.30、右手 -0.30），停泊约 y=±0.30、z=0.89，避免两臂视觉相交。
- 复验目录：`sorting_station_g1_23_unitree_vla_officialhand_inactivepark_smoke_20260921`。2 box + 2 mailer 全部通过；box Δy=0.435/0.418，mailer Δy=0.374/0.406，table penetration=0。抽帧未见双臂相交或桌下黑斑。
- 成功定义已与用户确认目标对齐：进入可见左右侧区，而非不可见料箱；中心线边界/最小位移均为0.15 m，方向、稳定、穿透和wrong-way门槛未放宽。
- 首次300目录 `officialhand_inactivepark_300_20260921` 因后台启动进程短暂写盘后被回收、再前台启动，造成NPZ/Unitree编号错位；该目录明确作废，不修补、不训练。
- 当前最终采集为全新 `_r2`：
  - NPZ：`datasets/sorting_station_g1_23_vla_officialhand_inactivepark_300_r2_20260921`
  - Unitree：`datasets/sorting_station_g1_23_unitree_vla_officialhand_inactivepark_300_r2_20260921`
  - 配比：120 box + 120 mailer + 60 wait；质量门开启；会话ID 63523。
