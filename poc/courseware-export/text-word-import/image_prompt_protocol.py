#!/usr/bin/env python3
"""Build guarded illustration prompts for the Dashenlin courseware style."""

from __future__ import annotations

import re


IMAGE_STYLE_ID = "asset-style.dashenlin-medical-flat-illustration-v1"
PROMPT_VERSION = "1.0"
AUTHORIZED_ASSET_TARGETS = (
    "商品主图",
    "产品主图",
    "商品包装",
    "产品包装",
    "说明书",
    "检测报告",
    "检验报告",
    "证据图",
    "批准文号",
)


def normalize(value: str) -> str:
    return re.sub(r"[ \t\u3000]+", " ", str(value or "")).strip()


def requires_authorized_asset(target: str) -> bool:
    compact = re.sub(r"\s+", "", normalize(target))
    return any(term in compact for term in AUTHORIZED_ASSET_TARGETS)


def build_image_prompt(target: str, topic: str, notes: str = "") -> dict[str, str | bool]:
    target = normalize(target)
    topic = normalize(topic)
    notes = normalize(notes)
    if not topic:
        return {
            "style_id": IMAGE_STYLE_ID,
            "prompt_version": PROMPT_VERSION,
            "mode": "none",
            "prompt": "",
            "review_status": "not-requested",
            "requires_authorized_asset": False,
        }
    if requires_authorized_asset(target):
        return {
            "style_id": IMAGE_STYLE_ID,
            "prompt_version": PROMPT_VERSION,
            "mode": "authorized-asset-required",
            "prompt": "",
            "review_status": "source-and-authorization-required",
            "requires_authorized_asset": True,
        }

    extra = f"\n补充要求：{notes}" if notes else ""
    prompt = f"""用途：连锁药店内部医药培训课件的辅助插画，不作为诊断、疗效证明或药学证据。
使用位置：{target or "课件内容插画"}
图片主题：{topic}{extra}

画面要求：
1. 只表现图片主题中明确提到的人物、动作、环境和物件，不自行增加症状、药品、疗效、治疗方案或医学结论。
2. 简洁的二维扁平医药科普卡通，成年人也适用；人物为紧凑圆润的成人比例、头部略大但明显是成年人，五官简化，表情克制、尊重、不污名化。
3. 中等偏粗的深绿色圆润线稿，4–6 种主要颜色，平整柔和色块，几乎不使用渐变、纹理和高光；浅薄荷绿或暖白背景，主色为大参林品牌绿，少量青绿、米黄和珊瑚红用于提示。
4. 方形 1:1 构图，主体居中，所有人物和物件完整收在画面内，四周至少保留 15% 安全区；小尺寸放入 PPTX 后仍能一眼识别主题。
5. 不绘制卡片边框和标题区域，课件程序会另外添加版式和审核文字。

医学与品牌边界：
- 不生成任何文字、汉字、英文字母、数字、药名、剂量、疗程、禁忌、功效结论、Logo、二维码或水印。
- 不仿造真实药品包装、说明书、检测报告、处方或品牌证据；如画面需要药品，只能使用没有标签和识别信息的通用简化药盒或药瓶。
- 不生成写实照片、3D 渲染、日系高光动漫、精细厚涂、恐怖病变、血腥手术、夸张痛苦表情或主题之外的解剖细节。
- 避免错误手指、异常肢体、物体穿插、医疗器械结构错误和不合常识的医患动作。

输出：高清、干净、无文字、无水印的单幅方形 PNG 插画候选图。"""
    return {
        "style_id": IMAGE_STYLE_ID,
        "prompt_version": PROMPT_VERSION,
        "mode": "auto-or-prompt",
        "prompt": prompt,
        "review_status": "candidate-pharmacist-and-visual-review-required",
        "requires_authorized_asset": False,
    }


def copyable_prompt_template() -> str:
    return """请生成一张用于连锁药店内部医药培训课件的辅助插画。
使用位置：【填写使用位置】
图片主题：【填写图片主题】
补充要求：【可选；没有可删除】

只表现主题明确提到的人物、动作、环境和物件，不增加症状、药品、疗效、治疗方案或医学结论。
画风：简洁、亲和、克制的二维扁平医药科普卡通；紧凑圆润的成年人，五官简化；中等偏粗深绿色圆润线稿，4–6 种主要颜色，平整柔和色块，几乎不用渐变和高光；浅薄荷绿或暖白背景，以大参林品牌绿为主。
构图：方形 1:1，主体居中且完整，四周至少保留 15% 安全区；不画卡片边框和标题区。
严禁：任何文字、字母、数字、药名、剂量、疗程、功效结论、Logo、二维码、水印，以及真实或仿造的药品包装、说明书、检测报告、处方和品牌证据。
避免：写实、3D、日系高光动漫、恐怖或血腥表现、夸张痛苦表情、错误肢体、物体穿插、器械错误和不合理医患动作。
输出高清、干净、无文字、无水印的单幅方形 PNG 候选图。"""
