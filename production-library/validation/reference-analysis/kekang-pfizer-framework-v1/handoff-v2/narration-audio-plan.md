# 正式金样旁白、字幕与声音事件计划

> K01～K18 全部按正式金样标准生成语音；`content_approval` 只记录医学／证据门禁，不能用来跳过声音制作。

- 音色：`voice.reference-pharmacist-qwen-v1`
- 语速：默认 1.16×，上限 1.18×；放不下则延长画面。
- 终混：-16±1 LUFS，True Peak≤-1 dBTP，人声比音乐／环境底音至少高 6dB。
- 每个语义段一次生成，不按微词拆 TTS；字幕再按微镜头 cue 切分。

| 微镜头 | 时长 | 正式金样旁白 | 屏幕短文案 | 内容状态 | 语音策略 | 音效事件 |
|---|---:|---|---|---|---|---|
| K01-S01 | 2.8s | 这是可可康灵芝胶囊。 | 可可康灵芝胶囊 | `source-aligned-review-required` | `formal-gold-sample-required` | ambient_in、soft_whoosh |
| K01-S02 | 5.7s | 本次课程将从适用状态、核心成分、产品特点和使用方法，完整认识这款产品。 | 一条完整产品知识路径 | `source-aligned-review-required` | `formal-gold-sample-required` | path_draw、label_tick_01、label_tick_02、label_tick_03 |
| K01-S03 | 3.1s | 我们先从三类常见状态开始。 | 先看三类状态 | `source-aligned-review-required` | `formal-gold-sample-required` | converge_soft、three_node_ticks |
| K02-S01 | 3.9s | 第一类，是经常失眠、夜间休息不佳的成人。 | 经常失眠 | `medical-blocked` | `formal-gold-sample-required` | night_ambience、clock_tick_soft |
| K02-S02 | 4.0s | 第二类，是长期饮酒，或关注肝脏健康的成人。 | 饮酒／肝功能较差 | `medical-blocked` | `formal-gold-sample-required` | table_roomtone、glass_setdown_soft |
| K02-S03 | 3.9s | 第三类，是免疫力偏低、容易反复不适的成人。 | 免疫力低下 | `medical-blocked` | `formal-gold-sample-required` | season_breeze、focus_shift |
| K03-S01 | 3.3s | 失眠常见的表现，包括入睡困难。 | 入睡困难 | `medical-blocked` | `formal-gold-sample-required` | clock_tick_soft、low_pulse |
| K03-S02 | 4.0s | 有些人还会夜间易醒、早醒，醒后难以再次入睡。 | 易醒 · 早醒 · 再入睡困难 | `medical-blocked` | `formal-gold-sample-required` | three_clock_ticks、focus_shift |
| K03-S03 | 3.9s | 到了第二天，也容易感到疲倦，影响精神状态。 | 次日疲倦 | `medical-blocked` | `formal-gold-sample-required` | morning_roomtone、soft_transition |
| K04-S01 | 3.9s | 长期饮酒，是需要关注的生活情境之一。 | 长期饮酒情境 | `high-risk-medical-blocked` | `formal-gold-sample-required` | restaurant_roomtone、glass_setdown_soft |
| K04-S02 | 5.9s | 酒精代谢会增加肝脏负担，肝功能较差的人群更需要重视日常健康管理。 | 肝脏负担 | `high-risk-medical-blocked` | `formal-gold-sample-required` | path_draw、low_organ_pulse |
| K04-S03 | 4.1s | 本段医学口径以公司最终批准资料为准。 | 等待审核终稿 | `high-risk-medical-blocked` | `formal-gold-sample-required` | review_lock_soft |
| K05-S01 | 3.8s | 第三类需要关注的状态，是免疫力偏低。 | 免疫力低下 | `medical-blocked` | `formal-gold-sample-required` | season_breeze、soft_whoosh |
| K05-S02 | 4.5s | 常见感受包括抵抗力较差，身体容易反复出现不适。 | 反复不适 · 抵抗力差 | `medical-blocked` | `formal-gold-sample-required` | label_tick_01、label_tick_02 |
| K05-S03 | 4.6s | 这些表现用于帮助理解健康状态，不作为疾病诊断。 | 非疾病诊断 | `medical-blocked` | `formal-gold-sample-required` | three_node_ticks |
| K06-S01 | 3.7s | 针对第一类状态，课程关注睡眠方向。 | 睡眠方向 | `medical-blocked` | `formal-gold-sample-required` | path_draw、label_tick_01 |
| K06-S02 | 4.0s | 针对第二类状态，课程关注肝脏健康方向。 | 肝脏方向 | `medical-blocked` | `formal-gold-sample-required` | path_draw、label_tick_02 |
| K06-S03 | 5.2s | 针对第三类状态，课程关注免疫方向，具体表述以批准资料为准。 | 免疫方向 · 待审核 | `medical-blocked` | `formal-gold-sample-required` | path_draw、label_tick_03、converge_soft |
| K07-S01 | 3.6s | 接下来，回到可可康灵芝胶囊本身。 | 回到产品 | `asset-and-medical-blocked` | `formal-gold-sample-required` | converge_soft、soft_whoosh |
| K07-S02 | 5.2s | 产品的标识、规格和包装信息，应以授权的高清实物包装为准。 | OTC · 规格待核对 | `asset-and-medical-blocked` | `formal-gold-sample-required` | zoom_soft、evidence_tick |
| K07-S03 | 4.9s | 功能主治等关键信息，应以产品说明书或批准信息为准。 | 功能主治 · 以说明书为准 | `asset-and-medical-blocked` | `formal-gold-sample-required` | paper_open_soft、highlight_sweep |
| K08-S01 | 3.1s | 从灵芝主体，可以认识两类核心成分。 | 从灵芝主体，认识两类成分 | `approved` | `formal-gold-sample-required` | ambient_in、soft_whoosh |
| K08-S02 | 2.4s | 第一类，是灵芝多糖。 | 01 灵芝多糖 | `approved` | `formal-gold-sample-required` | path_draw、label_tick_01 |
| K08-S03 | 2.3s | 第二类，是灵芝三萜。 | 02 灵芝三萜 | `approved` | `formal-gold-sample-required` | path_draw_gold、label_tick_02、focus_shift |
| K09-S01 | 4.2s | 先看灵芝多糖，它是灵芝中的重要成分之一。 | 灵芝多糖 · 相关表述待审核 | `high-risk-medical-blocked` | `formal-gold-sample-required` | path_draw、review_lock_soft |
| K09-S02 | 5.0s | 课程将从免疫、血压和心血管健康等方向认识相关资料。 | 血压／心血管表述 · 阻断 | `high-risk-medical-blocked` | `formal-gold-sample-required` | risk_stop_soft、review_lock_soft |
| K09-S03 | 4.9s | 涉及具体作用和疾病预防的表述，必须以批准终稿为准。 | 等待药师／合规终稿 | `high-risk-medical-blocked` | `formal-gold-sample-required` | three_node_ticks、converge_soft |
| K10-S01 | 4.2s | 再看灵芝三萜，它同样是灵芝的重要成分。 | 灵芝三萜 · 多项表述待审核 | `high-risk-medical-blocked` | `formal-gold-sample-required` | path_draw_gold、review_lock_soft |
| K10-S02 | 5.7s | 关于免疫细胞和肿瘤等高风险医学内容，本金样只验证讲解结构。 | 抗肿瘤／细胞机制 · 阻断 | `high-risk-medical-blocked` | `formal-gold-sample-required` | risk_stop_soft |
| K10-S03 | 5.9s | 正式培训必须使用逐句批准后的口径，不自行补充靶点和因果关系。 | 逐句批准后再制作 | `high-risk-medical-blocked` | `formal-gold-sample-required` | three_node_ticks、converge_soft |
| K11-S01 | 4.5s | 完成审核后，两类成分知识将与睡眠方向建立对应。 | 成分 → 睡眠方向 | `medical-blocked` | `formal-gold-sample-required` | path_draw_dashed、review_lock_soft |
| K11-S02 | 3.8s | 同样的方法，也用于说明肝脏健康方向。 | 成分 → 肝脏方向 | `medical-blocked` | `formal-gold-sample-required` | path_draw_dashed、focus_shift |
| K11-S03 | 4.4s | 最后回到免疫方向，三条关系都以批准资料为准。 | 成分 → 免疫方向 | `medical-blocked` | `formal-gold-sample-required` | path_draw_dashed、three_node_ticks |
| K12-S01 | 3.6s | 第一项产品特点，从原料产地开始。 | 特点一 · 产地 | `evidence-and-asset-blocked` | `formal-gold-sample-required` | map_open_soft、highlight_sweep |
| K12-S02 | 4.4s | 现有资料标注，每一百克原料含多糖九点一三克。 | 9.13g／100g · 待证据 | `evidence-and-asset-blocked` | `formal-gold-sample-required` | data_count_soft、evidence_tick |
| K12-S03 | 5.1s | 灵芝三萜含量等数据，也必须与最终可展示的证据保持一致。 | 三萜含量表述 · 待证据 | `evidence-and-asset-blocked` | `formal-gold-sample-required` | review_lock_soft、process_bridge |
| K13-S01 | 3.1s | 第二项特点，是双重提取工艺。 | 特点二 · 双重提取 | `evidence-blocked` | `formal-gold-sample-required` | process_start、liquid_move_soft |
| K13-S02 | 4.2s | 原料经过第一次提取后，再进入第二次浓缩提取。 | 第二次浓缩提取 | `evidence-blocked` | `formal-gold-sample-required` | liquid_move_soft、stage_focus |
| K13-S03 | 3.9s | 经过两次提取，原料逐步浓缩，最终形成胶囊。 | 浓缩完成 · 胶囊成形 | `evidence-blocked` | `formal-gold-sample-required` | capsule_form_soft、output_focus |
| K14-S01 | 3.6s | 第三项特点，回到产品的生产过程。 | 特点三 · 生产 | `evidence-and-asset-blocked` | `formal-gold-sample-required` | factory_roomtone、soft_whoosh |
| K14-S02 | 5.1s | 生产主体、GMP 和生产技术信息，需要使用当前有效的证明材料。 | GMP／生产技术 · 待证据 | `evidence-and-asset-blocked` | `formal-gold-sample-required` | zoom_soft、evidence_tick |
| K14-S03 | 4.2s | 最终措辞与可展示素材，以公司批准内容为准。 | 公司批准后使用 | `evidence-and-asset-blocked` | `formal-gold-sample-required` | three_node_ticks、converge_soft |
| K15-S01 | 3.8s | 在联合应用部分，课程设置了三类场景。 | 三套联合应用 | `high-risk-medical-and-asset-blocked` | `formal-gold-sample-required` | three_node_ticks、focus_shift |
| K15-S02 | 4.0s | 分别对应失眠、肝功能异常和免疫力偏低。 | 失眠 · 肝功能异常 · 免疫力低下 | `high-risk-medical-and-asset-blocked` | `formal-gold-sample-required` | focus_shift、three_node_ticks |
| K15-S03 | 5.1s | 每套组合及其适用情境，都必须由药师和合规人员逐项确认。 | 逐项审核后使用 | `high-risk-medical-and-asset-blocked` | `formal-gold-sample-required` | product_slot_in、review_lock_soft |
| K16-S01 | 2.9s | 第一套方案，对应失眠场景。 | 方案一 · 失眠 | `high-risk-medical-and-asset-blocked` | `formal-gold-sample-required` | night_ambience、product_in_left、product_in_right |
| K16-S02 | 4.0s | 谷维素片与灵芝胶囊，组成这一方向的联合方案。 | 谷维素片＋灵芝胶囊 | `high-risk-medical-and-asset-blocked` | `formal-gold-sample-required` | relation_connect、pair_settle |
| K16-S03 | 3.3s | 第二套方案，对应肝功能异常场景。 | 方案二 · 肝功能异常 | `high-risk-medical-and-asset-blocked` | `formal-gold-sample-required` | path_draw_gold、product_in_left、product_in_right |
| K16-S04 | 3.9s | 护肝片与灵芝胶囊，组成这一方向的联合方案。 | 护肝片＋灵芝胶囊 | `high-risk-medical-and-asset-blocked` | `formal-gold-sample-required` | relation_connect、pair_settle |
| K16-S05 | 3.3s | 第三套方案，对应免疫力偏低场景。 | 方案三 · 免疫力低下 | `high-risk-medical-and-asset-blocked` | `formal-gold-sample-required` | path_draw、product_in_left、product_in_right |
| K16-S06 | 4.7s | 转移因子口服溶液与灵芝胶囊，组成这一方向的联合方案。 | 转移因子口服溶液＋灵芝胶囊 | `high-risk-medical-and-asset-blocked` | `formal-gold-sample-required` | converge_soft、three_pair_ticks |
| K17-S01 | 4.4s | 关于服用周期，现有资料以一个月作为一个周期。 | 1 个月 · 1 个周期 | `medical-blocked` | `formal-gold-sample-required` | calendar_open、page_flip_soft |
| K17-S02 | 3.3s | 并建议连续服用两到三个月。 | 连续 2–3 个月 · 待审核 | `medical-blocked` | `formal-gold-sample-required` | page_flip_soft、page_flip_soft |
| K17-S03 | 5.0s | 具体周期和注意事项，应与说明书或最终审核口径保持一致。 | 以说明书／审核终稿为准 | `medical-blocked` | `formal-gold-sample-required` | evidence_tick、summary_bridge |
| K18-S01 | 4.0s | 最后，我们从核心成分和产品方向开始回顾。 | 成分 · 产品方向 | `content-and-asset-blocked` | `formal-gold-sample-required` | summary_bridge、label_tick_01、label_tick_02 |
| K18-S02 | 3.4s | 再回顾适用状态和三项产品特点。 | 人群 · 产品特点 | `content-and-asset-blocked` | `formal-gold-sample-required` | focus_shift、label_tick_03 |
| K18-S03 | 3.2s | 最后是联合应用和服用周期。 | 联合应用 · 服用周期 | `content-and-asset-blocked` | `formal-gold-sample-required` | label_tick_04、label_tick_05、converge_soft |
| K18-S04 | 5.2s | 完成内容与素材审核后，本次可可康产品知识培训到这里就结束了。 | 内部培训 · 审核后使用 | `content-and-asset-blocked` | `formal-gold-sample-required` | converge_soft、brand_end_chime |

## 音乐与环境底音分段

- K01：只用 2 秒品牌开场气氛音，不使用持续旋律抢占旁白。
- K02～K06：低密度木质脉冲＋柔和空气垫，夜间段降低高频，三个状态切换不换整首音乐。
- K07～K11：改为中性知识讲解底音；K08 左右路径分别以柔和木音和轻金属点音区分。
- K12～K14：加入极轻工艺节拍，但不得制造医疗科技或实验室疗效暗示。
- K15～K17：弱化音乐，以关系连接音、日历翻页和审核锁提示为主。
- K18：回收前述路径提示音，最后 1.2 秒品牌尾音；授权 Logo 缺失时不播放品牌专属声标。
- 全片音乐不得使用来源不明素材；验证阶段优先程序生成的低密度底音，正式替换须记录授权。

## 全片正式有声交付

K01～K18 必须按章节语义段生成完整旁白，并由最终正式旁白生成字幕。K08 可作为术语和音色回归样本，
但不得把 K08 通过当作全片声音完成。任何静音章、guide voice 章或缺少真实时长同步表都判定失败。
