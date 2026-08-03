#!/usr/bin/env python3
"""Build the v2 microshot handoff contract deterministically."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent

STYLE_PACK_ID = "style-pack.kekang-pfizer-green-candidate-v1"
VOICE_ID = "voice.reference-pharmacist-qwen-v1"

RECIPE_LAYERS = {
    "R01.hero_reveal": ["background", "environment_shape", "hero_subject", "title", "short_label", "focus_halo"],
    "R02.life_context_sequence": ["environment_back", "adult_character", "foreground_prop", "state_symbol", "short_caption", "ambient_motion"],
    "R03.multi_node_focus": ["background", "path_arc", "node_01", "node_02", "node_03", "focus_indicator"],
    "R04.central_split_orbit": ["background", "central_subject", "orbit", "branch_left", "branch_right", "label_left", "label_right"],
    "R05.pathway_explain": ["background", "source_subject", "path", "process_node", "moving_token", "result_label"],
    "R06.evidence_zoom": ["background", "authorized_evidence", "zoom_window", "measure_line", "data_label", "source_caption"],
    "R07.process_conveyor": ["background", "raw_material", "stage_01", "stage_02", "stage_03", "moving_material", "stage_label"],
    "R08.product_pair_relation": ["context_background", "problem_subject", "product_a", "relation_symbol", "product_b", "approved_role_label", "caution_label"],
    "R09.calendar_progression": ["background", "calendar", "month_01", "month_02", "month_03", "time_path", "caution_label"],
    "R10.summary_convergence": ["background", "central_subject", "summary_path", "summary_nodes", "brand_endframe", "internal_label"],
}

RECIPE_ANIMATED = {
    "R01.hero_reveal": ["hero_subject", "focus_halo"],
    "R02.life_context_sequence": ["adult_character", "foreground_prop", "ambient_motion"],
    "R03.multi_node_focus": ["path_arc", "node_01", "node_02", "node_03", "focus_indicator"],
    "R04.central_split_orbit": ["orbit", "branch_left", "branch_right", "label_left", "label_right"],
    "R05.pathway_explain": ["path", "process_node", "moving_token"],
    "R06.evidence_zoom": ["zoom_window", "measure_line"],
    "R07.process_conveyor": ["moving_material", "stage_01", "stage_02", "stage_03"],
    "R08.product_pair_relation": ["problem_subject", "product_a", "product_b", "relation_symbol"],
    "R09.calendar_progression": ["calendar", "month_01", "month_02", "month_03", "time_path"],
    "R10.summary_convergence": ["summary_path", "summary_nodes", "central_subject"],
}


def shot(
    duration,
    narration,
    subtitle,
    recipe,
    focal,
    action,
    assets,
    entry,
    performance,
    exit_action,
    sfx,
    camera="slow_push_1.5_percent",
    approval="source-aligned-review-required",
    voice_policy="guide-voice-only-until-approved",
):
    return {
        "duration_seconds": duration,
        "narration_candidate": narration,
        "subtitle": subtitle,
        "recipe_id": recipe,
        "frame_mode": "continuous_microshot",
        "focal_subject": focal,
        "visual_action": action,
        "asset_ids": assets,
        "layers": RECIPE_LAYERS[recipe],
        "animated_nontext_layers": RECIPE_ANIMATED[recipe],
        "entry": entry,
        "performance": performance,
        "exit": exit_action,
        "camera_motion": camera,
        "static_hold_max_seconds": 2.0,
        "sfx_events": sfx,
        "content_approval": approval,
        "voice_render_policy": voice_policy,
        "production_ready": approval == "approved",
    }


CHAPTERS = [
    {
        "id": "K01", "title": "产品与课程开场", "status": "asset-blocked",
        "shots": [
            shot(2.5, "这是可可康灵芝胶囊。", "可可康灵芝胶囊", "R01.hero_reveal", "灵芝与产品身份",
                 "奶油白环境先建立，灵芝主体从圆形遮罩内上揭示；授权包装缺失时只保留产品空槽。",
                 ["asset.bg.green-cream", "asset.ganoderma.hero.v3", "asset.packshot.kekang.required"],
                 "环境形状淡入；主体由 0.72 倍回弹到 1 倍", "光环轻呼吸，标题从左侧进入", "主体缩小并右移为课程导航锚点",
                 ["ambient_in", "soft_whoosh"]),
            shot(2.5, "这堂内部培训，将从多个方面认识这款产品。", "一条完整产品知识路径", "R03.multi_node_focus", "课程路径节点",
                 "成分、方向、特点、使用四个短节点沿弧线依次出现；同一时刻只高亮当前节点。",
                 ["asset.bg.green-cream", "asset.icon.ingredients-neutral", "asset.icon.direction-neutral", "asset.icon.feature-neutral", "asset.icon.use-neutral"],
                 "路径由产品锚点向左绘制", "节点逐个聚焦，非当前节点降至 0.68 透明度", "四节点沿路径汇聚成三类状态入口",
                 ["path_draw", "label_tick_01", "label_tick_02", "label_tick_03"]),
            shot(3.0, "先从三类常见状态开始。", "先看三类状态", "R03.multi_node_focus", "三类状态入口",
                 "三个空白状态轮廓从同一锚点分开，为 K02 的三个人物位置预热。",
                 ["asset.bg.green-cream", "asset.audience.young.insomnia", "asset.audience.middle.alcohol", "asset.audience.elder.low-immunity"],
                 "上一镜四节点收束为中央光点", "三个人物轮廓按 01→02→03 快速显现", "镜头跟随 01 人物进入夜间环境",
                 ["converge_soft", "three_node_ticks"]),
        ],
    },
    {
        "id": "K02", "title": "三类状态总览", "status": "medical-blocked",
        "shots": [
            shot(3.0, "第一类，是经常失眠的成人状态。", "经常失眠", "R02.life_context_sequence", "夜间清醒人物",
                 "卧室环境中人物翻身，时钟指针推进；只演生活状态，不做诊断。",
                 ["asset.scene.sleep-night.required", "asset.audience.young.insomnia"],
                 "从 K01 的 01 人物轮廓匹配切入", "时钟、呼吸和被角轻动", "紫色夜间光点沿弧线飞向下一人物",
                 ["night_ambience", "clock_tick_soft"], approval="medical-blocked"),
            shot(3.2, "第二类，是长期饮酒或肝功能较差的成人状态。", "饮酒／肝功能较差", "R02.life_context_sequence", "餐桌旁中年人物",
                 "酒杯仅作生活情境；人物按住右上腹或表现疲惫，不展示体内机制。",
                 ["asset.scene.alcohol-context.required", "asset.audience.middle.alcohol"],
                 "夜间光点变成暖金桌面高光", "酒杯轻放、人物姿态变化", "暖金高光滑向第三人物的环境",
                 ["table_roomtone", "glass_setdown_soft"], approval="medical-blocked"),
            shot(3.8, "第三类，是免疫力低下、容易反复不适的成人状态。", "免疫力低下", "R02.life_context_sequence", "季节变化中的成人",
                 "人物在季节变化中出现打喷嚏或疲倦符号，随后三类人物沿深度轴形成总览。",
                 ["asset.scene.low-immunity.required", "asset.audience.elder.low-immunity"],
                 "暖金高光转为青绿色季节气流", "人物动作与季节符号局部循环", "三类人物缩入弧线节点并把 01 放大进入 K03",
                 ["season_breeze", "focus_shift"], approval="medical-blocked"),
        ],
    },
    {
        "id": "K03", "title": "失眠状态", "status": "medical-blocked",
        "shots": [
            shot(3.2, "失眠可能表现为入睡困难。", "入睡困难", "R02.life_context_sequence", "床上清醒人物与时钟",
                 "镜头从人物眼睛推到时钟，时针移动但人物仍清醒。",
                 ["asset.scene.sleep-night.required", "asset.audience.young.insomnia"],
                 "K02 的 01 节点扩大为卧室圆窗", "眼睛、呼吸、时针持续微动", "时钟圆面扩大成为下一镜时间轴",
                 ["clock_tick_soft", "low_pulse"], approval="medical-blocked"),
            shot(3.5, "也可能出现夜间易醒、早醒或醒后难以再次入睡。", "易醒 · 早醒 · 再入睡困难", "R03.multi_node_focus", "三个时间节点",
                 "凌晨 1 点、3 点、5 点三个时间节点依次点亮，人物姿态随节点变化。",
                 ["asset.scene.sleep-night.required", "asset.icon.clock-neutral"],
                 "上一镜时钟圆面分裂为三个节点", "节点依次聚焦并带动人物姿态切换", "05:00 节点拉出晨光",
                 ["three_clock_ticks", "focus_shift"], approval="medical-blocked"),
            shot(3.8, "第二天，还可能感到疲倦。", "次日疲倦", "R02.life_context_sequence", "清晨工作状态",
                 "晨光进入，人物坐在桌前揉眼或扶额；夜间时间轴缩成背景。",
                 ["asset.sleep.problem.candidate", "asset.icon.fatigue-neutral"],
                 "05:00 节点擦拭转场到办公桌", "人物轻微点头、杯中热气上升", "疲倦符号向右移动并转为 K04 的杯沿",
                 ["morning_roomtone", "soft_transition"], approval="medical-blocked"),
        ],
    },
    {
        "id": "K04", "title": "饮酒与肝脏负担", "status": "high-risk-medical-blocked",
        "shots": [
            shot(3.0, "长期饮酒，是旧课件列出的生活情境之一。", "长期饮酒情境", "R02.life_context_sequence", "餐桌与成人",
                 "由 K03 杯沿匹配切入餐桌，人物与酒杯在真实生活环境中出现。",
                 ["asset.scene.alcohol-context.required", "asset.audience.middle.alcohol"],
                 "杯沿形状匹配转场", "手部放杯、人物呼吸、背景人群虚化移动", "镜头从杯子推向人物身体轮廓",
                 ["restaurant_roomtone", "glass_setdown_soft"], approval="high-risk-medical-blocked"),
            shot(3.4, "旧课件把它与肝脏负担和肝功能较差联系起来。", "肝脏负担", "R05.pathway_explain", "生活情境到肝脏位置的关系",
                 "只用中性身体轮廓和位置高亮建立关系；不展示病毒、炎症或损伤机制。",
                 ["asset.body.torso-neutral.required", "asset.icon.liver-neutral"],
                 "人物轮廓覆盖到画面中央", "位置高亮呼吸，单一光点沿路径移动", "位置高亮缩成肝脏方向标签",
                 ["path_draw", "low_organ_pulse"], approval="high-risk-medical-blocked"),
            shot(3.6, "具体医学表述，应以药师和合规审核终稿为准。", "等待审核终稿", "R03.multi_node_focus", "审核门禁标签",
                 "三个高风险旧词只以模糊占位出现并锁闭，不可作为正式画面输出。",
                 ["asset.bg.green-cream", "asset.icon.review-lock"],
                 "肝脏方向标签移动到锁定节点", "锁定节点轻呼吸，其他文字保持不可读占位", "锁定节点移出，绿色路径进入 K05",
                 ["review_lock_soft"], approval="high-risk-medical-blocked"),
        ],
    },
    {
        "id": "K05", "title": "免疫力低下状态", "status": "medical-blocked",
        "shots": [
            shot(3.0, "第三类状态，是免疫力低下。", "免疫力低下", "R02.life_context_sequence", "季节变化中的成人",
                 "成人从室内进入换季户外，气流与衣物轻动。",
                 ["asset.scene.low-immunity.required", "asset.audience.elder.low-immunity"],
                 "K04 绿色路径变成季节气流", "人物呼吸、衣物和叶片局部运动", "气流卷起两个状态符号",
                 ["season_breeze", "soft_whoosh"], approval="medical-blocked"),
            shot(3.2, "旧课件使用容易反复不适、抵抗力差等描述。", "反复不适 · 抵抗力差", "R03.multi_node_focus", "两个状态符号",
                 "两个短标签围绕人物依次出现，人物不被框进静态卡片。",
                 ["asset.scene.low-immunity.required", "asset.icon.discomfort-neutral", "asset.icon.shield-neutral"],
                 "状态符号沿季节气流进入", "两个符号轮流聚焦", "符号沿弧线汇入三类状态总览",
                 ["label_tick_01", "label_tick_02"], approval="medical-blocked"),
            shot(3.3, "最终称谓与画面范围，以审核结果为准。", "非疾病诊断", "R03.multi_node_focus", "三类状态回扣",
                 "三类状态节点短暂回扣，强调年龄只用于画面演绎。",
                 ["asset.audience.young.insomnia", "asset.audience.middle.alcohol", "asset.audience.elder.low-immunity"],
                 "两个符号汇聚成第三节点", "三节点依次轻亮", "三节点移动到 K06 的三方向位置",
                 ["three_node_ticks"], approval="medical-blocked"),
        ],
    },
    {
        "id": "K06", "title": "三大产品方向", "status": "medical-blocked",
        "shots": [
            shot(3.0, "旧课件把第一类状态对应到睡眠方向。", "睡眠方向", "R03.multi_node_focus", "睡眠方向节点",
                 "第一状态节点沿路径连接到中性月亮与休息符号。",
                 ["asset.icon.sleep-neutral", "asset.audience.young.insomnia"],
                 "K05 第一节点扩大", "路径绘制，睡眠符号轻呼吸", "节点缩到左上导航位",
                 ["path_draw", "label_tick_01"], approval="medical-blocked"),
            shot(3.0, "第二类状态对应到肝脏方向。", "肝脏方向", "R03.multi_node_focus", "肝脏方向节点",
                 "第二状态节点连接到中性肝脏位置图标，不表现治疗结果。",
                 ["asset.icon.liver-neutral", "asset.audience.middle.alcohol"],
                 "第二节点从深度轴进入", "路径绘制，位置图标轻呼吸", "节点缩到左侧导航位",
                 ["path_draw", "label_tick_02"], approval="medical-blocked"),
            shot(4.0, "第三类状态对应到免疫方向，三条最终口径必须逐项审核。", "免疫方向 · 待审核", "R03.multi_node_focus", "免疫方向与三方向总览",
                 "第三节点连接到中性盾牌；随后三方向沿弧线依次聚焦并收束。",
                 ["asset.icon.immune-neutral", "asset.audience.elder.low-immunity"],
                 "第三节点进入", "第三路径完成，三方向轮流聚焦", "三方向收束到产品空槽进入 K07",
                 ["path_draw", "label_tick_03", "converge_soft"], approval="medical-blocked"),
        ],
    },
    {
        "id": "K07", "title": "产品身份与功能主治", "status": "asset-and-medical-blocked",
        "shots": [
            shot(2.8, "回到产品本身。", "回到产品", "R01.hero_reveal", "授权包装空槽",
                 "产品空槽从三方向汇聚点放大；有授权包装后才替换。",
                 ["asset.packshot.kekang.required", "asset.bg.green-cream"],
                 "三方向汇聚成包装轮廓", "轮廓轻旋转后稳定", "局部放大到 OTC 位置",
                 ["converge_soft", "soft_whoosh"], approval="asset-and-medical-blocked"),
            shot(2.8, "包装信息中的 OTC 和规格，需要以高清真包装核对。", "OTC · 规格待核对", "R06.evidence_zoom", "OTC 与规格证据位",
                 "在授权真包装上依次放大 OTC 和规格位置；没有真包装时显示锁定占位。",
                 ["asset.packshot.kekang.required", "asset.evidence.product-label.required"],
                 "包装主体保持，放大框出现", "放大框从 OTC 移到规格位置", "放大框收束为说明书页角",
                 ["zoom_soft", "evidence_tick"], approval="asset-and-medical-blocked"),
            shot(2.9, "功能主治必须以说明书或批准信息终稿为准。", "功能主治 · 以说明书为准", "R06.evidence_zoom", "说明书批准信息",
                 "说明书授权页进入，获准文字区域高亮；不读取低清截图。",
                 ["asset.evidence.product-label.required", "asset.packshot.kekang.required"],
                 "说明书页角展开", "高亮带沿批准文字区域移动", "高亮带变成 K08 的中央轨道",
                 ["paper_open_soft", "highlight_sweep"], approval="asset-and-medical-blocked"),
        ],
    },
    {
        "id": "K08", "title": "两类成分总览", "status": "source-aligned-review-required",
        "shots": [
            shot(2.3, "从灵芝主体，可以认识两类成分。", "从灵芝主体，认识两类成分", "R04.central_split_orbit", "灵芝主体",
                 "复用已完成的中央灵芝主体、光环和虚线轨道；标题进入后让位。",
                 ["asset.bg.green-cream", "asset.ganoderma.hero.v3"],
                 "K07 高亮带转成虚线轨道", "灵芝主体遮罩上揭示，轨道缓慢旋转", "左路径开始绘制",
                 ["ambient_in", "soft_whoosh"], approval="approved", voice_policy="allowed-for-k08-pilot"),
            shot(2.5, "第一类，是灵芝多糖。", "01 灵芝多糖", "R04.central_split_orbit", "灵芝多糖标签",
                 "左绿色路径完成，01 标签从路径末端回弹进入。",
                 ["asset.ganoderma.hero.v3", "asset.icon.ingredients-neutral"],
                 "左路径逐段绘制", "01 标签放大 1.045 后稳定，右路径保持未完成", "右路径开始绘制",
                 ["path_draw", "label_tick_01"], approval="approved", voice_policy="allowed-for-k08-pilot"),
            shot(3.0, "第二类，是灵芝三萜。", "02 灵芝三萜", "R04.central_split_orbit", "灵芝三萜与双标签完成",
                 "右金色路径完成，02 标签进入；两标签轮流聚焦后形成完成帧。",
                 ["asset.ganoderma.hero.v3", "asset.icon.ingredients-neutral"],
                 "右路径逐段绘制", "02 标签回弹；01、02 轮流聚焦；轨道低强度旋转", "02 标签扩大为 K10 预备锚点，01 移入 K09",
                 ["path_draw_gold", "label_tick_02", "focus_shift"], approval="approved", voice_policy="allowed-for-k08-pilot"),
        ],
    },
    {
        "id": "K09", "title": "灵芝多糖", "status": "high-risk-medical-blocked",
        "shots": [
            shot(4.0, "旧课件首先列出灵芝多糖与免疫系统机能的相关表述。", "灵芝多糖 · 相关表述待审核", "R05.pathway_explain", "灵芝多糖节点",
                 "01 标签扩大为来源节点；未审核过程节点保持锁定，不显示具体细胞。",
                 ["asset.ganoderma.hero.v3", "asset.icon.review-lock", "asset.icon.immune-neutral"],
                 "K08 的 01 标签扩大", "光点到达锁定过程节点后停止", "锁定节点移到下一镜左侧",
                 ["path_draw", "review_lock_soft"], approval="high-risk-medical-blocked"),
            shot(4.0, "关于血压和心血管疾病预防的表述，属于高风险内容。", "血压／心血管表述 · 阻断", "R05.pathway_explain", "高风险锁定路径",
                 "路径在进入高风险区前断开并出现审核锁；不得展示血流改善或疾病预防结果。",
                 ["asset.icon.review-lock", "asset.body.circulation-neutral.required"],
                 "上一镜锁定节点展开为路径", "光点到达断点，审核锁呼吸", "路径折返形成审核清单轨迹",
                 ["risk_stop_soft", "review_lock_soft"], approval="high-risk-medical-blocked"),
            shot(4.0, "正式旁白与动画必须等待药师和合规终稿。", "等待药师／合规终稿", "R03.multi_node_focus", "审核状态收束",
                 "可保留、需改写、需删除三个状态节点依次出现，仅用于内部 animatic。",
                 ["asset.icon.review-lock", "asset.bg.green-cream"],
                 "折返路径分成三个审核节点", "节点按保留→改写→删除依次聚焦", "节点收束到 02 标签进入 K10",
                 ["three_node_ticks", "converge_soft"], approval="high-risk-medical-blocked"),
        ],
    },
    {
        "id": "K10", "title": "灵芝三萜", "status": "high-risk-medical-blocked",
        "shots": [
            shot(4.0, "旧课件列出灵芝三萜的多项作用描述。", "灵芝三萜 · 多项表述待审核", "R05.pathway_explain", "灵芝三萜节点",
                 "02 标签扩大；作用节点以模糊锁定圆点呈现，不显示具体结论。",
                 ["asset.ganoderma.hero.v3", "asset.icon.review-lock"],
                 "K09 收束点变成 02 标签", "多个锁定圆点沿路径依次出现", "高风险圆点聚到中央",
                 ["path_draw_gold", "review_lock_soft"], approval="high-risk-medical-blocked"),
            shot(4.0, "其中涉及抗肿瘤和免疫细胞机制的内容，不能直接进入正式片。", "抗肿瘤／细胞机制 · 阻断", "R05.pathway_explain", "高风险机制断点",
                 "在高风险关键词进入画面前以审核锁替代，禁止出现肿瘤细胞消失动画。",
                 ["asset.icon.review-lock", "asset.cell.diagram.required"],
                 "锁定圆点聚合", "路径在机制节点前停止，锁定标识轻呼吸", "机制节点缩为待审核标签",
                 ["risk_stop_soft"], approval="high-risk-medical-blocked"),
            shot(4.0, "只允许使用逐句批准后的终稿，不得自行补充靶点和因果。", "逐句批准后再制作", "R03.multi_node_focus", "逐句审核状态",
                 "三个原则节点：只用终稿、不补靶点、不升级因果；作为内部制作门禁。",
                 ["asset.icon.review-lock", "asset.bg.green-cream"],
                 "待审核标签分成三个原则节点", "节点依次聚焦", "两个成分标签同时返回进入 K11",
                 ["three_node_ticks", "converge_soft"], approval="high-risk-medical-blocked"),
        ],
    },
    {
        "id": "K11", "title": "成分与三大方向对应", "status": "medical-blocked",
        "shots": [
            shot(3.5, "审核后，两类成分知识将与睡眠方向建立对应。", "成分 → 睡眠方向", "R05.pathway_explain", "睡眠对应路径",
                 "两成分标签位于左侧，批准后才绘制到睡眠方向的具体关系。",
                 ["asset.icon.ingredients-neutral", "asset.icon.sleep-neutral", "asset.icon.review-lock"],
                 "K10 的两标签返回左侧", "路径先以锁定虚线预演", "睡眠标签移至总览上方",
                 ["path_draw_dashed", "review_lock_soft"], approval="medical-blocked"),
            shot(3.5, "同样的方法，用于说明肝脏方向。", "成分 → 肝脏方向", "R05.pathway_explain", "肝脏对应路径",
                 "复用路径语法但改变节点位置，不复制整页布局。",
                 ["asset.icon.ingredients-neutral", "asset.icon.liver-neutral", "asset.icon.review-lock"],
                 "上一条路径退到背景", "第二条锁定路径逐段绘制", "肝脏标签移至总览左下",
                 ["path_draw_dashed", "focus_shift"], approval="medical-blocked"),
            shot(3.5, "最后回到免疫方向，三条关系均以审核终稿为准。", "成分 → 免疫方向", "R05.pathway_explain", "三方向关系总览",
                 "第三条路径完成后，三方向围绕两成分形成空间关系图。",
                 ["asset.icon.ingredients-neutral", "asset.icon.immune-neutral", "asset.icon.review-lock"],
                 "第三路径从右侧进入", "三方向轮流聚焦，成分标签保持中心锚点", "关系图折叠成产地地图轮廓进入 K12",
                 ["path_draw_dashed", "three_node_ticks"], approval="medical-blocked"),
        ],
    },
    {
        "id": "K12", "title": "特点一：产地与含量", "status": "evidence-and-asset-blocked",
        "shots": [
            shot(3.5, "第一项产品特点，从产地开始。", "特点一 · 产地", "R06.evidence_zoom", "大别山产地素材",
                 "授权产地图先展示环境，再把区域位置和赤灵芝原料建立关系。",
                 ["asset.origin.dabie.required", "asset.ganoderma.hero.v3"],
                 "K11 关系图折叠成地图轮廓", "地图轻推近，产地区域高亮", "产地高亮缩成原料标签",
                 ["map_open_soft", "highlight_sweep"], approval="evidence-and-asset-blocked"),
            shot(3.5, "旧课件标注每一百克含多糖九点一三克。", "9.13g／100g · 待证据", "R06.evidence_zoom", "含量证据数字",
                 "检测报告或批准材料进入后才显示数字；当前以锁定数据槽表示。",
                 ["asset.evidence.polysaccharide.required", "asset.icon.review-lock"],
                 "原料标签移动到数据槽旁", "数字逐位出现并被证据框圈定", "证据框移向三萜陈述",
                 ["data_count_soft", "evidence_tick"], approval="evidence-and-asset-blocked"),
            shot(3.5, "关于灵芝三萜含量的表述，也必须与可展示证据一致。", "三萜含量表述 · 待证据", "R06.evidence_zoom", "三萜证据槽",
                 "不显示“含量高”结论，直到证据和展示范围批准。",
                 ["asset.evidence.triterpene.required", "asset.icon.review-lock"],
                 "上一镜证据框滑入", "三萜证据槽轻呼吸", "两个证据槽沿折线变成工艺步骤进入 K13",
                 ["review_lock_soft", "process_bridge"], approval="evidence-and-asset-blocked"),
        ],
    },
    {
        "id": "K13", "title": "特点二：双重提取", "status": "evidence-blocked",
        "shots": [
            shot(3.5, "第二项特点，是双重提取工艺。", "特点二 · 双重提取", "R07.process_conveyor", "灵芝原料与第一次提取",
                 "灵芝原料进入第一次提取容器，材料 token 沿路径移动。",
                 ["asset.ganoderma.hero.v3", "asset.process.extraction.required"],
                 "K12 折线路径延伸成工艺轴", "原料 token 进入第一次提取节点", "token 离开第一节点进入第二节点",
                 ["process_start", "liquid_move_soft"], approval="evidence-blocked"),
            shot(3.5, "随后进入第二次浓缩提取。", "第二次浓缩提取", "R07.process_conveyor", "第二次提取节点",
                 "第二节点放大成为唯一焦点，其他阶段降低透明度。",
                 ["asset.process.extraction.required", "asset.evidence.process.required"],
                 "材料 token 从第一节点抵达第二节点", "第二节点局部流动并逐步浓缩", "token 离开第二节点",
                 ["liquid_move_soft", "stage_focus"], approval="evidence-blocked"),
            shot(3.5, "经过两次提取，原料逐步浓缩，最终形成胶囊。", "浓缩完成 · 胶囊成形", "R07.process_conveyor", "胶囊成形",
                 "材料 token 进入胶囊成形，工艺结果成为本镜唯一焦点。",
                 ["asset.process.extraction.required"],
                 "token 进入成形节点", "胶囊轮廓闭合并依次形成", "胶囊轮廓移动到 K14 质量检查位",
                 ["capsule_form_soft", "output_focus"], approval="evidence-blocked"),
        ],
    },
    {
        "id": "K14", "title": "特点三：生产与质量", "status": "evidence-and-asset-blocked",
        "shots": [
            shot(3.0, "第三项特点，回到生产主体。", "特点三 · 生产", "R06.evidence_zoom", "授权工厂素材",
                 "胶囊轮廓落入真实授权生产线画面；没有授权时只保留工厂空槽。",
                 ["asset.factory.kekang.required", "asset.process.extraction.required"],
                 "K13 胶囊轮廓匹配切入生产线", "生产线局部移动，主体名称短标签出现", "镜头推近质量检查区域",
                 ["factory_roomtone", "soft_whoosh"], approval="evidence-and-asset-blocked"),
            shot(3.0, "GMP 和生产技术信息，需要使用当前有效证据。", "GMP／生产技术 · 待证据", "R06.evidence_zoom", "GMP 与生产证据",
                 "只对授权证据做局部放大，不制作通用证书图。",
                 ["asset.evidence.gmp.required", "asset.factory.kekang.required"],
                 "质量检查区域变成证据放大框", "放大框依次移动到有效信息位置", "证据框收成质量标签",
                 ["zoom_soft", "evidence_tick"], approval="evidence-and-asset-blocked"),
            shot(3.0, "最终措辞与素材范围，以公司批准内容为准。", "公司批准后使用", "R03.multi_node_focus", "生产、质量、封装三节点",
                 "三个生产节点沿短路径依次聚焦后收束为产品轮廓。",
                 ["asset.factory.kekang.required", "asset.evidence.gmp.required", "asset.icon.review-lock"],
                 "质量标签分成三个节点", "生产→质量→封装依次聚焦", "产品轮廓移动到 K15 的组合中心",
                 ["three_node_ticks", "converge_soft"], approval="evidence-and-asset-blocked"),
        ],
    },
    {
        "id": "K15", "title": "三套联合应用总览", "status": "high-risk-medical-and-asset-blocked",
        "shots": [
            shot(3.0, "旧课件给出了三套联合应用场景。", "三套联合应用", "R03.multi_node_focus", "三个组合入口",
                 "三个问题节点沿弧线出现，不展示商品表格。",
                 ["asset.icon.sleep-neutral", "asset.icon.liver-neutral", "asset.icon.immune-neutral"],
                 "K14 产品轮廓成为组合中心", "三个问题节点按 01→02→03 出现", "01 节点扩大进入第一组合",
                 ["three_node_ticks", "focus_shift"], approval="high-risk-medical-and-asset-blocked"),
            shot(3.5, "分别对应失眠、肝功能异常和免疫力低下。", "失眠 · 肝功能异常 · 免疫力低下", "R03.multi_node_focus", "三场景标签",
                 "三场景用人物／器官方向短动画依次成为主体，年龄仅用于视觉覆盖。",
                 ["asset.audience.young.insomnia", "asset.audience.middle.alcohol", "asset.audience.elder.low-immunity"],
                 "01 人物进入", "焦点从 01 切到 02、03", "三人物缩入各自商品组合轨迹",
                 ["focus_shift", "three_node_ticks"], approval="high-risk-medical-and-asset-blocked"),
            shot(3.5, "组合及适用情境必须由药师和合规逐项确认。", "逐项审核后使用", "R08.product_pair_relation", "三套组合锁定轮廓",
                 "三套商品组合仅以包装空槽轮廓快速预演，不显示品牌仿图。",
                 ["asset.packshot.kekang.required", "asset.packshot.guweisu.required", "asset.packshot.hugan.required", "asset.packshot.transfer-factor.required"],
                 "三条轨迹拉出商品空槽", "三套空槽轮流聚焦并显示审核锁", "第一组合空槽移到前景进入 K16",
                 ["product_slot_in", "review_lock_soft"], approval="high-risk-medical-and-asset-blocked"),
        ],
    },
    {
        "id": "K16", "title": "三套联合方案解释", "status": "high-risk-medical-and-asset-blocked",
        "shots": [
            shot(3.0, "第一套方案对应失眠场景。", "方案一 · 失眠", "R08.product_pair_relation", "失眠问题与两商品空槽",
                 "先演入睡困难的短动作，再让谷维素片与可可康包装空槽从两侧进入。",
                 ["asset.scene.sleep-night.required", "asset.packshot.guweisu.required", "asset.packshot.kekang.required"],
                 "K15 第一组合空槽扩大", "问题人物先动，商品 A／B 依次进入", "关系符号生成",
                 ["night_ambience", "product_in_left", "product_in_right"], approval="high-risk-medical-and-asset-blocked"),
            shot(3.0, "谷维素片与灵芝胶囊，组成这一方向的联合方案。", "谷维素片＋灵芝胶囊", "R08.product_pair_relation", "第一组合关系",
                 "只建立公司课件给出的商品搭配关系，不扩写剂量、机制或疗效。",
                 ["asset.packshot.guweisu.required", "asset.packshot.kekang.required"],
                 "关系符号稳定", "两个商品角色汇合并形成方案一", "第一组合沿深度轴后退",
                 ["relation_connect", "pair_settle"], approval="high-risk-medical-and-asset-blocked"),
            shot(3.0, "第二套方案对应肝功能异常场景。", "方案二 · 肝功能异常", "R08.product_pair_relation", "肝脏问题与两商品空槽",
                 "先建立肝脏方向，再让护肝片与可可康包装空槽进入。",
                 ["asset.icon.liver-neutral", "asset.packshot.hugan.required", "asset.packshot.kekang.required"],
                 "第一组合退后，暖金路径拉出第二场景", "肝脏方向先聚焦，商品 A／B 依次进入", "关系符号生成",
                 ["path_draw_gold", "product_in_left", "product_in_right"], approval="high-risk-medical-and-asset-blocked"),
            shot(3.0, "护肝片与灵芝胶囊，组成这一方向的联合方案。", "护肝片＋灵芝胶囊", "R08.product_pair_relation", "第二组合关系",
                 "只建立公司课件给出的商品搭配关系，不扩写剂量、机制或疗效。",
                 ["asset.packshot.hugan.required", "asset.packshot.kekang.required"],
                 "关系符号稳定", "两个商品角色汇合并形成方案二", "第二组合沿深度轴后退",
                 ["relation_connect", "pair_settle"], approval="high-risk-medical-and-asset-blocked"),
            shot(3.0, "第三套方案对应免疫力低下场景。", "方案三 · 免疫力低下", "R08.product_pair_relation", "免疫问题与两商品空槽",
                 "先建立免疫方向，再让转移因子口服溶液与可可康包装空槽进入。",
                 ["asset.icon.immune-neutral", "asset.packshot.transfer-factor.required", "asset.packshot.kekang.required"],
                 "第二组合退后，青绿路径拉出第三场景", "免疫方向先聚焦，商品 A／B 依次进入", "关系符号生成",
                 ["path_draw", "product_in_left", "product_in_right"], approval="high-risk-medical-and-asset-blocked"),
            shot(3.0, "转移因子口服溶液与灵芝胶囊，组成这一方向的联合方案。", "转移因子口服溶液＋灵芝胶囊", "R08.product_pair_relation", "第三组合关系与三方案收束",
                 "第三组合关系建立后，前两组合从背景返回，三套同时缩成导航节点而非表格。",
                 ["asset.packshot.guweisu.required", "asset.packshot.hugan.required", "asset.packshot.transfer-factor.required", "asset.packshot.kekang.required"],
                 "第三关系符号稳定", "三组合沿深度轴汇聚并依次点亮", "三组合轨迹弯成 K17 月历轮廓",
                 ["converge_soft", "three_pair_ticks"], approval="high-risk-medical-and-asset-blocked"),
        ],
    },
    {
        "id": "K17", "title": "建议服用周期", "status": "medical-blocked",
        "shots": [
            shot(2.8, "旧课件以一个月作为一个服用周期。", "1 个月 · 1 个周期", "R09.calendar_progression", "第一个月历节点",
                 "月历从审核锁轮廓中展开，第一个月高亮。",
                 ["asset.calendar.code", "asset.icon.review-lock"],
                 "K16 审核锁变成月历边框", "日期格按周轻微推进", "时间路径从第一个月向右延伸",
                 ["calendar_open", "page_flip_soft"], approval="medical-blocked"),
            shot(2.8, "旧课件建议连续服用两到三个月。", "连续 2–3 个月 · 待审核", "R09.calendar_progression", "第二、第三个月历节点",
                 "第二、第三个月沿时间路径依次进入，当前月高亮。",
                 ["asset.calendar.code", "asset.icon.review-lock"],
                 "时间路径绘制", "第 2 月、第 3 月依次翻页聚焦", "第三个月移动到注意事项位置",
                 ["page_flip_soft", "page_flip_soft"], approval="medical-blocked"),
            shot(2.9, "周期和注意事项，必须与说明书或审核终稿一致。", "以说明书／审核终稿为准", "R09.calendar_progression", "周期注意事项",
                 "说明书证据槽与月历并置；不新增剂量和频次。",
                 ["asset.calendar.code", "asset.evidence.product-label.required"],
                 "第三个月缩小", "说明书证据槽进入并高亮", "时间路径弯成 K18 总结环",
                 ["evidence_tick", "summary_bridge"], approval="medical-blocked"),
        ],
    },
    {
        "id": "K18", "title": "六维总结与品牌封底", "status": "content-and-asset-blocked",
        "shots": [
            shot(3.0, "最后，从成分和产品方向开始回顾。", "成分 · 产品方向", "R10.summary_convergence", "前两个总结节点",
                 "K17 时间路径弯成总结环；成分、产品方向两个节点依次返回。",
                 ["asset.ganoderma.hero.v3", "asset.icon.ingredients-neutral", "asset.icon.direction-neutral"],
                 "时间路径闭合成环", "两个节点按课程顺序进入并聚焦", "总结环旋转到下两个空位",
                 ["summary_bridge", "label_tick_01", "label_tick_02"], approval="content-and-asset-blocked"),
            shot(3.0, "再回顾人群和产品特点。", "人群 · 产品特点", "R10.summary_convergence", "中间两个总结节点",
                 "人群、特点两个节点从前述镜头位置飞回总结环。",
                 ["asset.audience.young.insomnia", "asset.icon.feature-neutral"],
                 "前两节点退到环上", "人群、特点依次进入并聚焦", "总结环旋转到最后两个空位",
                 ["focus_shift", "label_tick_03"], approval="content-and-asset-blocked"),
            shot(2.5, "最后是联合应用和服用周期。", "联合应用 · 服用周期", "R10.summary_convergence", "最后两个总结节点",
                 "联合应用、周期节点进入；只引用前镜已批准的短标签。",
                 ["asset.icon.use-neutral", "asset.calendar.code"],
                 "前四节点保持环形位置", "最后两节点进入并轮流聚焦", "六节点沿路径向中央收束",
                 ["label_tick_04", "label_tick_05", "converge_soft"], approval="content-and-asset-blocked"),
            shot(3.0, "以上内容全部通过审核后，完成本次内部培训。", "内部培训 · 审核后使用", "R01.hero_reveal", "产品与品牌封底",
                 "六节点收束到授权真包装；品牌 Logo 与内部培训声明最后进入。",
                 ["asset.packshot.kekang.required", "asset.logo.dashenlin.required", "asset.bg.green-cream"],
                 "六节点汇聚成产品轮廓", "真包装稳定，Logo 与声明依次出现", "音乐尾音收束，末帧稳定 1 秒",
                 ["converge_soft", "brand_end_chime"], camera="stable_with_local_halo_motion", approval="content-and-asset-blocked"),
        ],
    },
]


ASSETS = [
    {"id": "asset.bg.green-cream", "status": "code-generated", "path": None, "rights": "self-made", "allowed": ["animatic", "production"], "notes": "按 scene-recipes.md 色板程序化生成。"},
    {"id": "asset.ganoderma.hero.v3", "status": "candidate", "path": "poc/gold-sample/public/kekang-lingzhi/v3/ganoderma-hero-v3.png", "rights": "project-candidate", "allowed": ["animatic", "k08-pilot"], "notes": "完整金样前需确认视觉与来源；不得自动升级为生产授权。"},
    {"id": "asset.packshot.kekang.required", "status": "authorized-required", "path": None, "rights": "business-must-provide", "allowed": [], "notes": "禁止 AI 仿造；当前低清截图不能用于生产。"},
    {"id": "asset.logo.dashenlin.required", "status": "authorized-required", "path": None, "rights": "business-must-provide", "allowed": [], "notes": "正式封底必须使用授权 Logo。"},
    {"id": "asset.logo.dashenlin.candidate", "status": "candidate", "path": "production-library/validation/courseware/kekang-lingzhi-video-keyframes-v1/assets/dashenlin-logo.png", "rights": "project-candidate", "allowed": ["animatic"], "notes": "只用于内部结构验证。"},
    {"id": "asset.audience.young.insomnia", "status": "candidate", "path": "production-library/validation/courseware/kekang-lingzhi-video-keyframes-v1/assets/audience-young-woman-insomnia-v7.png", "rights": "self-generated-candidate", "allowed": ["animatic"], "notes": "年龄只作画面覆盖，不代表医学适用年龄。"},
    {"id": "asset.audience.middle.alcohol", "status": "candidate", "path": "production-library/validation/courseware/kekang-lingzhi-video-keyframes-v1/assets/audience-middle-man-alcohol-v7.png", "rights": "self-generated-candidate", "allowed": ["animatic"], "notes": "不展示酒类品牌。"},
    {"id": "asset.audience.elder.low-immunity", "status": "candidate", "path": "production-library/validation/courseware/kekang-lingzhi-video-keyframes-v1/assets/audience-elder-woman-seasonal-v7.png", "rights": "self-generated-candidate", "allowed": ["animatic"], "notes": "年龄只作视觉覆盖。"},
    {"id": "asset.sleep.problem.candidate", "status": "candidate", "path": "production-library/validation/courseware/kekang-lingzhi-video-keyframes-v1/assets/sleep-problem-illustration-candidate-v1.png", "rights": "self-generated-candidate", "allowed": ["animatic"], "notes": "只作生活状态，不是医学证据。"},
    {"id": "asset.scene.sleep-night.required", "status": "generate-one-then-review", "path": None, "rights": "self-generated-after-review", "allowed": ["animatic"], "prompt": "16:9 企业培训扁平插画，成年中国女性夜间卧室中清醒翻身，床头时钟可见但无文字数字，圆润低细节造型，奶油白、浅薄荷绿、柔紫夜色，人物自然手部和五官，分层清晰，禁止药品、文字、Logo、诊断符号。"},
    {"id": "asset.scene.alcohol-context.required", "status": "generate-one-then-review", "path": None, "rights": "self-generated-after-review", "allowed": ["animatic"], "prompt": "16:9 企业培训扁平插画，成年中国男性在普通餐桌旁放下无品牌酒杯，表现疲惫但不夸张痛苦，奶油白与暖金环境、品牌绿点缀，圆润低细节、分层可动画，禁止酒类品牌、药品、文字、器官机制和疾病诊断。"},
    {"id": "asset.scene.low-immunity.required", "status": "generate-one-then-review", "path": None, "rights": "self-generated-after-review", "allowed": ["animatic"], "prompt": "16:9 企业培训扁平插画，成年中国女性处于季节变化环境，轻微打喷嚏或疲倦动作，衣物和叶片便于分层动画，奶油白、浅薄荷绿、少量青色，圆润低细节，禁止儿童、药品、文字、病菌恐怖形象和具体疾病。"},
    {"id": "asset.body.torso-neutral.required", "status": "generate-after-medical-review", "path": None, "rights": "self-generated-after-review", "allowed": ["animatic"], "prompt": "中性成人躯干定位插画，企业培训扁平风，只显示器官位置层级，不表现损伤、病毒或治疗结果，透明背景，奶油白、浅绿、柔和赭色，禁止文字、包装和诊断。"},
    {"id": "asset.body.circulation-neutral.required", "status": "blocked-until-medical-review", "path": None, "rights": "not-authorized", "allowed": [], "notes": "只有审核终稿要求时才制作；不得先画血压改善或心血管预防。"},
    {"id": "asset.cell.diagram.required", "status": "blocked-until-medical-review", "path": None, "rights": "not-authorized", "allowed": [], "notes": "不得在审核前制作肿瘤或免疫细胞机制。"},
    {"id": "asset.origin.dabie.required", "status": "authorized-required", "path": None, "rights": "business-must-provide", "allowed": [], "notes": "正式片需公司可用的产地图／视频；不可用通用山景冒充产地证据。"},
    {"id": "asset.process.extraction.required", "status": "generate-after-evidence-review", "path": None, "rights": "self-generated-after-review", "allowed": ["animatic"], "prompt": "横向四阶段工艺插画组件：赤灵芝原料、第一次提取、第二次浓缩提取、胶囊成形；企业培训扁平风、透明背景、无文字、无实验数据、无吸收率、无专利编号，品牌绿与暖金统一色板，节点彼此独立便于动画。"},
    {"id": "asset.factory.kekang.required", "status": "authorized-required", "path": None, "rights": "business-must-provide", "allowed": [], "notes": "禁止 AI 生成虚构工厂冒充中山可可康。"},
    {"id": "asset.evidence.product-label.required", "status": "authorized-required", "path": None, "rights": "business-must-provide", "allowed": [], "notes": "说明书或批准信息终稿。"},
    {"id": "asset.evidence.polysaccharide.required", "status": "evidence-required", "path": None, "rights": "business-must-provide", "allowed": [], "notes": "支持 9.13g/100g 的可展示证据。"},
    {"id": "asset.evidence.triterpene.required", "status": "evidence-required", "path": None, "rights": "business-must-provide", "allowed": [], "notes": "支持三萜含量表述的可展示证据。"},
    {"id": "asset.evidence.process.required", "status": "evidence-required", "path": None, "rights": "business-must-provide", "allowed": [], "notes": "专利／工艺／吸收相关批准证据。"},
    {"id": "asset.evidence.gmp.required", "status": "evidence-required", "path": None, "rights": "business-must-provide", "allowed": [], "notes": "当前有效 GMP／生产技术批准材料。"},
    {"id": "asset.packshot.guweisu.required", "status": "authorized-required", "path": None, "rights": "business-must-provide", "allowed": [], "notes": "谷维素片授权高清包装。"},
    {"id": "asset.packshot.hugan.required", "status": "authorized-required", "path": None, "rights": "business-must-provide", "allowed": [], "notes": "护肝片授权高清包装。"},
    {"id": "asset.packshot.transfer-factor.required", "status": "authorized-required", "path": None, "rights": "business-must-provide", "allowed": [], "notes": "转移因子口服溶液授权高清包装。"},
    {"id": "asset.calendar.code", "status": "code-generated", "path": None, "rights": "self-made", "allowed": ["animatic", "production"], "notes": "程序化月历，不显示剂量频次。"},
]

for icon_id in [
    "ingredients-neutral", "direction-neutral", "feature-neutral", "use-neutral", "clock-neutral",
    "fatigue-neutral", "sleep-neutral", "liver-neutral", "immune-neutral", "discomfort-neutral",
    "shield-neutral", "review-lock",
]:
    ASSETS.append({
        "id": f"asset.icon.{icon_id}",
        "status": "code-generated",
        "path": None,
        "rights": "self-made",
        "allowed": ["animatic", "production"],
        "notes": "仅作中性导航／状态符号，不承载医学结论。",
    })


FORMAL_VOICE_CUES = {
    "K01": [
        "这是可可康灵芝胶囊。",
        "本次课程将从适用状态、核心成分、产品特点和使用方法，完整认识这款产品。",
        "我们先从三类常见状态开始。",
    ],
    "K02": [
        "第一类，是经常失眠、夜间休息不佳的成人。",
        "第二类，是长期饮酒，或关注肝脏健康的成人。",
        "第三类，是免疫力偏低、容易反复不适的成人。",
    ],
    "K03": [
        "失眠常见的表现，包括入睡困难。",
        "有些人还会夜间易醒、早醒，醒后难以再次入睡。",
        "到了第二天，也容易感到疲倦，影响精神状态。",
    ],
    "K04": [
        "长期饮酒，是需要关注的生活情境之一。",
        "酒精代谢会增加肝脏负担，肝功能较差的人群更需要重视日常健康管理。",
        "本段医学口径以公司最终批准资料为准。",
    ],
    "K05": [
        "第三类需要关注的状态，是免疫力偏低。",
        "常见感受包括抵抗力较差，身体容易反复出现不适。",
        "这些表现用于帮助理解健康状态，不作为疾病诊断。",
    ],
    "K06": [
        "针对第一类状态，课程关注睡眠方向。",
        "针对第二类状态，课程关注肝脏健康方向。",
        "针对第三类状态，课程关注免疫方向，具体表述以批准资料为准。",
    ],
    "K07": [
        "接下来，回到可可康灵芝胶囊本身。",
        "产品的标识、规格和包装信息，应以授权的高清实物包装为准。",
        "功能主治等关键信息，应以产品说明书或批准信息为准。",
    ],
    "K08": [
        "从灵芝主体，可以认识两类核心成分。",
        "第一类，是灵芝多糖。",
        "第二类，是灵芝三萜。",
    ],
    "K09": [
        "先看灵芝多糖，它是灵芝中的重要成分之一。",
        "课程将从免疫、血压和心血管健康等方向认识相关资料。",
        "涉及具体作用和疾病预防的表述，必须以批准终稿为准。",
    ],
    "K10": [
        "再看灵芝三萜，它同样是灵芝的重要成分。",
        "关于免疫细胞和肿瘤等高风险医学内容，本金样只验证讲解结构。",
        "正式培训必须使用逐句批准后的口径，不自行补充靶点和因果关系。",
    ],
    "K11": [
        "完成审核后，两类成分知识将与睡眠方向建立对应。",
        "同样的方法，也用于说明肝脏健康方向。",
        "最后回到免疫方向，三条关系都以批准资料为准。",
    ],
    "K12": [
        "第一项产品特点，从原料产地开始。",
        "现有资料标注，每一百克原料含多糖九点一三克。",
        "灵芝三萜含量等数据，也必须与最终可展示的证据保持一致。",
    ],
    "K13": [
        "第二项特点，是双重提取工艺。",
        "原料经过第一次提取后，再进入第二次浓缩提取。",
        "经过两次提取，原料逐步浓缩，最终形成胶囊。",
    ],
    "K14": [
        "第三项特点，回到产品的生产过程。",
        "生产主体、GMP 和生产技术信息，需要使用当前有效的证明材料。",
        "最终措辞与可展示素材，以公司批准内容为准。",
    ],
    "K15": [
        "在联合应用部分，课程设置了三类场景。",
        "分别对应失眠、肝功能异常和免疫力偏低。",
        "每套组合及其适用情境，都必须由药师和合规人员逐项确认。",
    ],
    "K16": [
        "第一套方案，对应失眠场景。",
        "谷维素片与灵芝胶囊，组成这一方向的联合方案。",
        "第二套方案，对应肝功能异常场景。",
        "护肝片与灵芝胶囊，组成这一方向的联合方案。",
        "第三套方案，对应免疫力偏低场景。",
        "转移因子口服溶液与灵芝胶囊，组成这一方向的联合方案。",
    ],
    "K17": [
        "关于服用周期，现有资料以一个月作为一个周期。",
        "并建议连续服用两到三个月。",
        "具体周期和注意事项，应与说明书或最终审核口径保持一致。",
    ],
    "K18": [
        "最后，我们从核心成分和产品方向开始回顾。",
        "再回顾适用状态和三项产品特点。",
        "最后是联合应用和服用周期。",
        "完成内容与素材审核后，本次可可康产品知识培训到这里就结束了。",
    ],
}


def build_formal_voice_contract(timeline):
    segments = []
    cursor = 0.0
    for chapter in timeline["chapters"]:
        chapter_id = chapter["id"]
        cues = FORMAL_VOICE_CUES[chapter_id]
        shots = chapter["microshots"]
        if len(cues) != len(shots):
            raise ValueError(f"{chapter_id}: voice cue count does not match microshots")
        speech_units = [
            len(re.findall(r"[\u4e00-\u9fff]", cue)) + len(re.findall(r"[A-Za-z0-9]+", cue))
            for cue in cues
        ]
        original_duration = sum(item["duration_seconds"] for item in shots)
        chapter_target = max(original_duration, sum(speech_units) / 4.8 + 0.8)
        motion_base = 1.6
        distributable = chapter_target - motion_base * len(shots)
        provisional = [motion_base + distributable * units / sum(speech_units) for units in speech_units]
        rounded = [round(value, 1) for value in provisional]
        rounded[-1] = round(rounded[-1] + round(chapter_target, 1) - round(sum(rounded), 1), 1)
        for item, retimed in zip(shots, rounded):
            item["original_duration_seconds"] = item["duration_seconds"]
            item["duration_seconds"] = retimed
            item["duration_basis"] = "formal-voice-provisional-fit-at-4.8-cjk-units-per-second"
        duration = round(sum(item["duration_seconds"] for item in shots), 3)
        segment_cues = []
        local_cursor = 0.0
        for item, cue in zip(shots, cues):
            item["formal_narration"] = cue
            item["formal_subtitle"] = cue
            item["voice_render_policy"] = "formal-gold-sample-required"
            item["gold_sample_voice_ready"] = True
            segment_cues.append({
                "microshot_id": item["id"],
                "visual_anchor": item["focal_subject"],
                "text": cue,
                "target_start_seconds": round(cursor + local_cursor, 3),
                "target_window_seconds": item["duration_seconds"],
            })
            local_cursor += item["duration_seconds"]
        segments.append({
            "segment_id": f"VOICE-{chapter_id}",
            "chapter_id": chapter_id,
            "microshot_ids": [item["id"] for item in shots],
            "text": "".join(cues),
            "cues": segment_cues,
            "visual_start_seconds": round(cursor, 3),
            "visual_duration_seconds": duration,
            "target_audio_duration_seconds": [round(duration * 0.78, 3), round(duration - 0.35, 3)],
            "generation_unit": "one-semantic-chapter-segment",
            "delivery": "中性、可信、清晰的内部药师培训语气；自然连读，不逐条播报表格",
            "content_status": chapter["status"],
            "gold_sample_voice_status": "must-generate-and-accept",
            "output_file": f"audio/narration/chapters/{chapter_id.lower()}-formal.wav",
        })
        cursor += duration
    return {
        "schema_version": "1.0",
        "project_id": timeline["project_id"],
        "purpose": "formal-gold-sample-voice-validation",
        "voice_id": VOICE_ID,
        "engine": "Qwen3-TTS 0.6B Base BF16 with locked pharmacist reference prompt",
        "reference_prompt": "poc/reference-replica/reference-analysis/audio/reference-clone-prompt.wav",
        "generation_rules": {
            "all_chapters_required": True,
            "segment_count": 18,
            "generate_by": "chapter semantic segment, never micro-word or isolated list number",
            "sample_rate_hz": 48000,
            "channels": 1,
            "max_post_tempo_ratio": 1.18,
            "if_too_long": "extend visual window or tighten non-claim wording; never exceed 1.18x",
            "required_real_duration_probe": True,
            "required_timeline_backfill": True,
            "content_gate_is_separate_from_voice_acceptance": True,
        },
        "pronunciation_lexicon": [
            {"term": "可可康", "expected": "kě kě kāng"},
            {"term": "灵芝多糖", "expected": "líng zhī duō táng"},
            {"term": "灵芝三萜", "expected": "líng zhī sān tiē", "note": "ASR 可能误写为三贴，权威字幕必须保持三萜"},
            {"term": "GMP", "expected": "G M P，逐字母清晰读出"},
            {"term": "九点一三克", "expected": "jiǔ diǎn yī sān kè"},
        ],
        "mastering": {
            "integrated_lufs": [-17, -15],
            "target_lufs": -16,
            "true_peak_dbtp_max": -1,
            "chapter_head_silence_seconds": 0.12,
            "chapter_tail_silence_seconds": 0.18,
            "crossfade_milliseconds": 20,
        },
        "required_deliverables": [
            "18 chapter WAV files",
            "full narration master WAV",
            "SRT and VTT generated from final authoritative text",
            "voice-sync-map.json with real durations and final placements",
            "loudness-report.json",
            "pronunciation-qa.json",
            "review.html with chapter audition and full-master audition",
        ],
        "segments": segments,
    }


def build_formal_voice_markdown(contract):
    lines = [
        "# 可可康金样 v2｜全片正式语音执行稿",
        "",
        "> 本文件是金样声音的正式执行输入，不是 guide voice 备注。K01～K18 必须全部生成、同步并验收。",
        "> 医学／证据审批状态与声音制作验收分开记录，不能用内容门禁跳过语音制作。",
        "",
        f"- 固定音色：`{contract['voice_id']}`",
        "- 生成单位：每章一个完整语义段，共 18 段；禁止按 58 句碎片化 TTS。",
        "- 后处理：整体语速拟合不超过 1.18×；超窗则延长画面或收紧非宣称性措辞。",
        "- 母带：48kHz mono WAV，-16 LUFS，True Peak 不高于 -1 dBTP。",
        "",
        "| 语音段 | 覆盖微镜头 | 视觉时窗 | 正式金样旁白 | 输出文件 |",
        "|---|---|---:|---|---|",
    ]
    for segment in contract["segments"]:
        lines.append(
            f"| {segment['segment_id']} | {segment['microshot_ids'][0]}～{segment['microshot_ids'][-1]} | "
            f"{segment['visual_duration_seconds']:.1f}s | {segment['text']} | `{segment['output_file']}` |"
        )
    lines.extend([
        "",
        "## 强制验收",
        "",
        "1. 每段生成后先读取真实时长，再写入 `voice-sync-map.json`；不能只使用预计时长。",
        "2. 逐段核对声音、字幕、视觉焦点三者同时出现；语音不得提前描述尚未出现的画面。",
        "3. K01～K18 覆盖率必须为 100%；任何章节缺音频均判定失败。",
        "4. 术语重点核对：可可康、灵芝多糖、灵芝三萜、GMP、九点一三克。",
        "5. 字幕只能由本文件的正式旁白生成；ASR 仅用于回听检查，不得反写权威术语。",
        "6. 最终必须提供 18 段试听和全片连续母带试听，不得只提交文件清单或波形截图。",
    ])
    return "\n".join(lines) + "\n"


def build_timeline():
    timeline = {
        "schema_version": "2.0",
        "project_id": "validation.kekang-green-gold-sample-v1",
        "theme_id": "theme.product.kekang-lingzhi-capsule",
        "style_pack_id": STYLE_PACK_ID,
        "voice_id": VOICE_ID,
        "production_mode": "microshot-contract",
        "chapter_is_not_page": True,
        "global_constraints": {
            "canvas": {"width": 1920, "height": 1080, "fps": 30},
            "target_duration_seconds": [225, 250],
            "chapter_microshot_count": [2, 6],
            "microshot_duration_seconds": [1.8, 8.0],
            "max_static_hold_seconds": 2.2,
            "min_layers_per_microshot": 4,
            "min_animated_nontext_layers": 1,
            "forbidden_frame_modes": ["chapter_page", "static_slide", "ppt_page", "fullpage_card"],
            "forbidden_transitions": ["repeated_fullpage_fade", "static_page_cut", "whole_frame_push_only"],
        },
        "chapters": [],
    }

    flat = []
    for chapter in CHAPTERS:
        rendered = {k: v for k, v in chapter.items() if k != "shots"}
        rendered["microshots"] = []
        for index, source in enumerate(chapter["shots"], start=1):
            item = dict(source)
            item["id"] = f"{chapter['id']}-S{index:02d}"
            item["chapter_id"] = chapter["id"]
            item["sequence_in_chapter"] = index
            rendered["microshots"].append(item)
            flat.append(item)
        timeline["chapters"].append(rendered)

    for index, item in enumerate(flat):
        item["transition_to"] = flat[index + 1]["id"] if index + 1 < len(flat) else "END"
        item["timeline_order"] = index + 1

    timeline["summary"] = {
        "chapter_count": len(timeline["chapters"]),
        "microshot_count": len(flat),
        "total_duration_seconds": round(sum(x["duration_seconds"] for x in flat), 3),
        "production_ready_microshots": sum(1 for x in flat if x["production_ready"]),
        "blocked_microshots": sum(1 for x in flat if not x["production_ready"]),
    }
    return timeline


def build_audio_markdown(timeline):
    lines = [
        "# 正式金样旁白、字幕与声音事件计划",
        "",
        "> K01～K18 全部按正式金样标准生成语音；`content_approval` 只记录医学／证据门禁，不能用来跳过声音制作。",
        "",
        f"- 音色：`{VOICE_ID}`",
        "- 语速：默认 1.16×，上限 1.18×；放不下则延长画面。",
        "- 终混：-16±1 LUFS，True Peak≤-1 dBTP，人声比音乐／环境底音至少高 6dB。",
        "- 每个语义段一次生成，不按微词拆 TTS；字幕再按微镜头 cue 切分。",
        "",
        "| 微镜头 | 时长 | 正式金样旁白 | 屏幕短文案 | 内容状态 | 语音策略 | 音效事件 |",
        "|---|---:|---|---|---|---|---|",
    ]
    for chapter in timeline["chapters"]:
        for item in chapter["microshots"]:
            sfx = "、".join(item["sfx_events"])
            lines.append(
                f"| {item['id']} | {item['duration_seconds']:.1f}s | {item['formal_narration']} | "
                f"{item['subtitle']} | `{item['content_approval']}` | `{item['voice_render_policy']}` | {sfx} |"
            )
    lines.extend([
        "",
        "## 音乐与环境底音分段",
        "",
        "- K01：只用 2 秒品牌开场气氛音，不使用持续旋律抢占旁白。",
        "- K02～K06：低密度木质脉冲＋柔和空气垫，夜间段降低高频，三个状态切换不换整首音乐。",
        "- K07～K11：改为中性知识讲解底音；K08 左右路径分别以柔和木音和轻金属点音区分。",
        "- K12～K14：加入极轻工艺节拍，但不得制造医疗科技或实验室疗效暗示。",
        "- K15～K17：弱化音乐，以关系连接音、日历翻页和审核锁提示为主。",
        "- K18：回收前述路径提示音，最后 1.2 秒品牌尾音；授权 Logo 缺失时不播放品牌专属声标。",
        "- 全片音乐不得使用来源不明素材；验证阶段优先程序生成的低密度底音，正式替换须记录授权。",
        "",
        "## 全片正式有声交付",
        "",
        "K01～K18 必须按章节语义段生成完整旁白，并由最终正式旁白生成字幕。K08 可作为术语和音色回归样本，",
        "但不得把 K08 通过当作全片声音完成。任何静音章、guide voice 章或缺少真实时长同步表都判定失败。",
    ])
    return "\n".join(lines) + "\n"


def main():
    timeline = build_timeline()
    formal_voice_contract = build_formal_voice_contract(timeline)
    flat = [item for chapter in timeline["chapters"] for item in chapter["microshots"]]
    timeline["summary"]["total_duration_seconds"] = round(sum(x["duration_seconds"] for x in flat), 3)
    (ROOT / "microshot-timeline.json").write_text(
        json.dumps(timeline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (ROOT / "asset-manifest.json").write_text(
        json.dumps({"schema_version": "1.0", "assets": ASSETS}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (ROOT / "narration-audio-plan.md").write_text(build_audio_markdown(timeline), encoding="utf-8")
    (ROOT / "formal-voice-contract.json").write_text(
        json.dumps(formal_voice_contract, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (ROOT / "formal-voice-script.md").write_text(
        build_formal_voice_markdown(formal_voice_contract), encoding="utf-8"
    )
    print(json.dumps(timeline["summary"], ensure_ascii=False))


if __name__ == "__main__":
    main()
