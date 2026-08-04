# Koboyo Icons — 按需源头（非囤库）

| 项 | 值 |
| --- | --- |
| **源头目录** | https://koboyo.com/icons （制作时在线搜、匹配） |
| 许可页 | https://koboyo.com/icons/license（全文见 `license.txt`） |
| 直链 | `https://koboyo.com/icons/svg/{slug}.svg` |
| 本目录 Git 入库 | 仅 `license.txt` / `SOURCE.md` / `manifest.json`（空缓存清单） |
| 本地 SVG 缓存 | `svg/**` **不进 Git**（见根目录 `.gitignore`）；制作机按需下载 |

## 默认工作流（推荐）

```text
课件/视频制作需要图标
  → 打开 https://koboyo.com/icons 按语义搜索
    （箭头 / bullet / check / pill / pharmacy / stethoscope …）
  → 确认 slug 与画风
  → 仅下载本次要用的 1～N 个 SVG 到本目录 svg/<role>/
  → 改色 / 栅格化 PNG（若 PPTX·Revideo 需要）
  → 用到正式模板前再 candidates → master 签样
```

**原则：**

1. **源头在线上**：7 万图标不镜像、不整包入库；需要时再匹配获取。  
2. **本地缓存不进仓库**：`svg/` 仅本机按需落盘（已 gitignore），可随时删；不要把批量 SVG 提交 Git。  
3. **排版符号 + 物件符号**都适用：箭头、序号底、分行点、勾叉、分隔线、健康物件等。  
4. **纯数字 1.2.3. / ①②③** 优先文本排版；手绘感可用 `circle`/`solid-circle` 作底 + 字。  
5. **不替代** 已签样的多色场景插画（`component-library` 症状/注意事项/药师）。  
6. **禁止** 对外提供「可挑可下全库」的图标浏览器（见 license You can't）。

## 与 component-library 分工

| 层 | 何时用 Koboyo | 何时用既有组件库 |
| --- | --- | --- |
| 排版 / UI 标记 | 需要一致手绘小符号时按需拉 | 无 |
| 健康物件符号 | 列表旁小图标、流程节点 | 无 |
| 场景插画 | 不 | 症状格、注意场景、药师角色 |

## 目录说明

```text
koboyo/
  license.txt       # 许可快照（进 Git）
  SOURCE.md         # 本文件：按需流程（进 Git）
  manifest.json     # 可选本地清单；仓库内默认 empty
  svg/              # 本机缓存，gitignore，不提交
    layout/
    health/
```

`manifest.json` 在仓库里保持 `total: 0` 即可；本机若维护清单可本地改，勿提交大批量 slug。

## 制作时按需获取

```bash
# 1) 站内搜到 slug，例如 arrow-right、dot、pill
# 2) 落盘到对应角色目录
ROLE=layout   # 或 health
SLUG=arrow-right
curl -fsSL "https://koboyo.com/icons/svg/${SLUG}.svg" \
  -o "assets/_intake/open_source/koboyo/svg/${ROLE}/${SLUG}.svg"
# 3) 更新 manifest（或下次批量整理时再扫盘生成）
```

常用入口：

- 全库浏览：https://koboyo.com/icons  
- 健康物件：https://koboyo.com/icons/set/object/health  
- 健康人物：https://koboyo.com/icons/set/people/health  
- 状态标记：https://koboyo.com/icons/set/mark/status  

## 进入成片前

1. 品牌色替换 `currentColor`  
2. 需要 PNG 时导出透明底（建议 ≥512，常用 1024）  
3. 晋升：`_intake` → `component-library/**/candidates` → 签样 → `master`  
4. 模板只引用**已签样路径**，不在渲染时热链 koboyo.com（避免线上依赖与条款变更）

## 本地缓存

默认**不保留**预下载包。需要时再 curl 到 `svg/`，用完可删；成片依赖的正式图应晋升到 `component-library` master（可进 Git 的应是少量签样 PNG，不是 7 万 SVG）。
