# 生产级视觉组件库

本目录只保存重新绘制或重新生成的正式资产。参考视频截图、裁切图和临时占位图不得进入正式组件版本。

公共查询入口为 `production-library/catalog.json` 和
`scripts/query_production_library.py`。本目录的分类注册表只维护图片资产事实，
模板、场景、特效、声音、决策和教训由 `production-library/registries/` 统一索引，
避免在多个文档中重复维护。

主线见 `decision.gold-sample-first` / `docs/project-brief.md` §1.1：完整金样优先，本目录不为囤货而囤货；新增图须服务已签样框架槽位。  
业务「主题」与视觉「系列」不是同一对象；`external_reference_only` 不得进入 `master`。  
原料暂存：`assets/_intake/`（真包装由业务投入 `company_authorized/`）。

可持续增长的同类视觉资产必须额外绑定稳定 `series_id`。系列文件统一定义色板、
材质、构图槽位、提示词变量、动画契约和扩展门槛；新增业务主题优先向现有系列补成员，
不得以单次视频目录代替生产素材沉淀。医学机理系列入口为
`mechanisms/registry.json`。

## 目录约定

```text
<category>/<component-id>/
  component.json
  candidates/       # 签样候选，不得直接标记为 approved
  master/           # 通过签样的高清主图
  transparent/      # 可选透明主体
  thumbnails/       # 编辑器和素材检索缩略图
  prompts/          # 完整生成配方及变量说明
```

系列目录另包含：

```text
<category>/<series-id>/
  series.json         # 视觉令牌、角色和动画契约
  asset-template.json # 新成员清单模板
  README.md           # 新增与审核流程
```

## 状态

- `candidate`：候选图，等待风格或内容签样；
- `selected`：已选为母版，尚未完成生产验收；
- `approved`：通过视觉、内容、来源和技术检查，可进入模板；
- `deprecated`：保留历史引用，不再用于新项目。

## 最低验收

- 主图不小于 1024×1024；
- 不含参考视频像素、文字、Logo、水印或截图压缩痕迹；
- 小尺寸缩略图仍能直接识别主题；
- 画风、线宽、色板、人物比例和背景语法符合指定 `style_id`；
- 记录提示词、生成方式、版本、审核状态和用途；
- 医学含义由公司内部药师审核，视觉审核不能代替内容审核。
