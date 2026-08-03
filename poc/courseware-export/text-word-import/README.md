# 通用培训课件 Word 导入

正式业务入口是一份记事本式 Word 对应一个课件主题；批量时一次提交多份 Word。

## 业务模板

`outputs/courseware-natural-import/培训课件内容与素材提交_通用模板.docx`

业务只需要：

1. 填写课件主题；
2. 按自然逻辑写任意数量的板块标题和审核正文；
3. 将图片直接粘贴在相关板块下面；
4. 可选填写图片说明／来源。

不填写课件类型、模板、页码、卡片数量、坐标、组件或动画。

## 内容与规划边界

- Word 负责内容整理，不负责套固定 PPT 框架。
- AI 根据板块内容、段落数量和图片数量，从已验收页型库中选择页面结构。
- 只有 2 个要点就使用适配 2 个要点的布局，不生成 5 个空卡。
- 内容超量时拆页，图片数量变化时改用相应图文页型。
- 每个项目仍绑定一个风格包，避免跨风格拼装。
- 生成前应输出章节、页数、页型和图片分配预览供业务确认。

## 批量导入

```bash
/Users/liminrong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  poc/courseware-export/text-word-import/import_universal_courseware_content.py \
  path/to/course-a.docx path/to/course-b.docx \
  --output-dir outputs/courseware-universal-import
```

导入结果保留自然板块、原文和粘贴图片，并给出候选页型；最终页型由 AI 在业务确认前规划。

## 历史入口

`import_courseware_content.py` 及其 5 页／18 页固定课型 profile 只用于旧数据回归。
两份固定业务 Word 和对应生成脚本已经删除，不得恢复为默认业务入口。
