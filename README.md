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
# 安装入口仓 → 自动拉取生产仓并打开引导页
git clone https://github.com/lmr1123/chain-pharmacy-content-studio.git \
  ~/Documents/chain-pharmacy-content-studio-installer
cd ~/Documents/chain-pharmacy-content-studio-installer
python3 scripts/install_private_studio.py
```

业务**不需要** GitHub 账号、设备申请或管理员批准。安装器默认用官方 HTTPS 匿名拉取生产仓
`chain-pharmacy-content-studio-private`（当前为 Public），再 bootstrap 打开引导页。
安装与出片命令都由 WorkBuddy 执行。禁止公共镜像。

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

- **安装入口**（`chain-pharmacy-content-studio`）：只含安装脚本与说明。
- **生产仓**（`chain-pharmacy-content-studio-private`，**当前 Public**）：settled 金样、资产、声纹、生成器与业务门户。业务经安装器自动拉取，无需账号。
- **本机不入仓**：`third_party/`、`node_modules`、`.venv*`、运行 workspace、业务上传、日志和正式交付物。

安装后，出片与克隆 TTS 由 WorkBuddy 在生产 checkout 内按 `AGENTS.md` 执行。公开可读仅便于内部业务安装，不等于对外再分发授权。

## 硬原则（摘要）

- 金样优先 · 内容驱动（有几条写几条）· 审核文案锁定  
- 无授权不仿包装 · 视频默认模板克隆药师声 · 禁止系统机器人音色作正式旁白  
- 先确认后成片；编辑器端口仅制作返修，非业务默认路径  
- **业务默认入口 = WorkBuddy 安装句，不是解压 zip**

## License / 使用范围

- 仓库公开可读仅为简化内部业务安装；模板、声纹与素材仅供公司内部培训制作，禁止外传或再分发。
- 不替代商品包装、人声克隆与品牌素材的内部使用授权。
