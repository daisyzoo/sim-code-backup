# 分拣采集 / PI0.5 交接（更新于 2026-09-30）

给下一个 agent / 人用。一律用中文回复用户。工作区：`/home/user/Documents/zoo/sim`。

**硬约束（新工作必守）**：[`PROJECT_CONSTRAINTS.md`](PROJECT_CONSTRAINTS.md)。其中 §1 要求上半身 11 关节首帧为 **0 位**；本文档下文及历史数据里使用的 `U1_REAL_REST_*` 休息角仅作对照，**不得**用于新采集（采集前核验实际初始状态）。

---

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
