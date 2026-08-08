# 连锁药店培训内容工厂

内部培训课件 / 视频的金样沉淀、内容驱动组装与业务 WorkBuddy 傻瓜交付。

## 业务怎么用（默认）

在 **WorkBuddy** 里直接输入：

```text
请安装 https://github.com/lmr1123/chain-pharmacy-content-studio.git，然后指引我使用
```

三步：

1. **看模板**（引导页预览 + 选用）  
2. **输入培训内容**（聊天发主题与要点）  
3. **下载与修改**（可下载 PPT 修改，或输入指令批量修改）

详细协议：

- 业务一页：`docs/business-ready-use-today.md`  
- WorkBuddy 安装与引导：`docs/workbuddy-install-and-guide.md`  
- 系统提示词（粘贴到代理）：`docs/workbuddy-system-prompt.md`  
- 总案：`docs/business-workbuddy-foolproof-delivery.md`

安装脚本（代理执行）：

```bash
# Public 仓只有脱敏安装器；WorkBuddy 首次执行
git clone https://github.com/lmr1123/chain-pharmacy-content-studio.git \
  ~/Documents/chain-pharmacy-content-studio-installer
cd ~/Documents/chain-pharmacy-content-studio-installer
python3 scripts/install_private_studio.py
```

安装器会检查 GitHub 登录和
`lmr1123/chain-pharmacy-content-studio-private` 的授权，随后拉取完整 Private 生产仓并运行其中的 bootstrap。Public 仓**不含**模板、资产、声纹、业务包或生成能力；没有 Private `read` 权限时会明确停止。Private 拉取禁止使用公共镜像，也不提供公开 ZIP 回退。

## 制作侧

刷新业务引导包（含货架 + 空白 Word + 引导页）：

```bash
python3 scripts/refresh_business_delivery.py
# → outputs/业务使用资料包/药店培训内容工厂-业务包/
# → …/药店培训内容工厂-业务包.zip（仅备份/离线拷贝，非业务默认入口）
```

## 关键文档

| 文档 | 说明 |
|------|------|
| [`docs/workbuddy-install-and-guide.md`](docs/workbuddy-install-and-guide.md) | **默认**：安装句 + 三步引导 |
| [`docs/workbuddy-system-prompt.md`](docs/workbuddy-system-prompt.md) | 代理系统提示词 |
| [`docs/business-workbuddy-foolproof-delivery.md`](docs/business-workbuddy-foolproof-delivery.md) | 业务 WorkBuddy 傻瓜交付总案 |
| [`production-library/templates/settled/`](production-library/templates/settled/) | 已签样正式模板 |
| [`docs/digital-human-presenter-mode.md`](docs/digital-human-presenter-mode.md) | 真人数字人侧讲模式 |
| [`docs/seedance-health-edu-video-mode.md`](docs/seedance-health-edu-video-mode.md) | 健康科普 Seedance（生活避险提示词） |
| [`docs/jiugongge-health-edu-video-mode.md`](docs/jiugongge-health-edu-video-mode.md) | 九宫格原版（林医生） |
| [`docs/jiugongge-health-edu-compliance-mode.md`](docs/jiugongge-health-edu-compliance-mode.md) | 九宫格合规版（无医疗） |

## 仓库边界

- **Public installer**：全新历史，只含安装、授权检查和安全说明；不具备生产能力。
- **Private production**：settled 金样、授权资产、声纹、文档、生成器、登记表和配置。第一阶段完整 Private 仓即授权资产包。
- **本机不入仓**：`third_party/`、`node_modules`、`.venv*`、运行 workspace、业务上传、日志和正式交付物。

获授权安装后，出片与克隆 TTS 由 WorkBuddy 在 Private checkout 内按 `AGENTS.md` 与各工程依赖执行。迁移和权限边界见 [`docs/private-public-repository-migration.md`](docs/private-public-repository-migration.md)。

## 硬原则（摘要）

- 金样优先 · 内容驱动（有几条写几条）· 审核文案锁定  
- 无授权不仿包装 · 视频默认模板克隆药师声 · 禁止系统机器人音色作正式旁白  
- 先确认后成片；编辑器端口仅制作返修，非业务默认路径  
- **业务默认入口 = WorkBuddy 安装句，不是解压 zip**

## License / 使用范围

- Public 仓公开可读不等于获得 Private 生产资产或其再分发授权；除非另有明确书面许可，安装入口之外的权利均不随 Public 可见性授予。
- 完整生产系统仅供获授权账号进行公司内部培训制作；Private 化不替代素材、人声和品牌的内部使用授权。
