# 连锁药店培训内容工厂

内部培训课件 / 视频的金样沉淀、内容驱动组装与业务 WorkBuddy 傻瓜交付。

## 业务怎么用（默认 · 业务 + WorkBuddy）

开源式四步（解压业务包后）：

1. **双击根目录 `index.html`**（主入口引导页）
2. **预览并选择模板**（封面 + 关键页）
3. **下载空白 Word 填报**（可删节、有几条写几条）
4. **上传提交**（拖入 Word/图或放入 `07_业务填报上传/待处理/`）→ 复制口令给 WorkBuddy → **先审初稿，再收成片**

业务包路径：`outputs/业务使用资料包/药店培训内容工厂-业务包.zip`

刷新业务包（制作侧 · 推荐一键）：

```bash
python3 scripts/refresh_business_delivery.py
```

## 关键文档

| 文档 | 说明 |
|------|------|
| [`docs/business-workbuddy-foolproof-delivery.md`](docs/business-workbuddy-foolproof-delivery.md) | 业务 WorkBuddy 傻瓜交付总案 |
| [`docs/workbuddy-system-prompt.md`](docs/workbuddy-system-prompt.md) | 代理系统提示词（粘贴用） |
| [`production-library/templates/settled/`](production-library/templates/settled/) | 已签样正式模板 |
| [`docs/project-brief.md`](docs/project-brief.md) | 项目简报（若存在） |

## 仓库边界

- **纳入 Git**：settled 金样成片与预览、文档、脚本、登记表、业务包、源码与配置  
- **默认不纳入**（体积 / 可本地再生）：`third_party/`、`node_modules`、`.venv*`、validation 下音视频与大量 QA 截图、`tmp/`  

克隆后需按 `AGENTS.md` 与各工程 `package.json` 安装依赖；克隆语音包引擎见 `docs/local-open-source-reuse-audit.md`。

## 硬原则（摘要）

- 金样优先 · 内容驱动（有几条写几条）· 审核文案锁定  
- 无授权不仿包装 · 视频默认模板克隆药师声 · 禁止系统机器人音色作正式旁白  
- 先确认后成片；编辑器端口仅制作返修，非业务默认路径  

## License / 使用范围

公司内部培训制作用途。人声克隆包、品牌包装与医学表述须在授权与合规范围内使用；开源对外前须脱敏。
