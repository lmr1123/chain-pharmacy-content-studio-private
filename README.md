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
# 已在仓库内
python3 scripts/workbuddy_bootstrap_for_business.py

# 首次（示例路径；国内直连失败时 bootstrap 会自动换镜像）
git clone https://github.com/lmr1123/chain-pharmacy-content-studio.git ~/Documents/chain-pharmacy-content-studio
# 或：git clone https://ghproxy.com/https://github.com/lmr1123/chain-pharmacy-content-studio.git ~/Documents/chain-pharmacy-content-studio
cd ~/Documents/chain-pharmacy-content-studio
python3 scripts/workbuddy_bootstrap_for_business.py
```

**国内网络：** 仓库 Public，无需登录；但 GitHub 在国内常不稳定。优先让 WorkBuddy 跑 bootstrap（内置镜像回退），不要让业务自己硬扛直连。

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

## 仓库边界

- **纳入 Git**：settled 金样成片与预览、文档、脚本、登记表、业务包、源码与配置  
- **默认不纳入**（体积 / 可本地再生）：`third_party/`、`node_modules`、`.venv*`、validation 下音视频与大量 QA 截图、`tmp/`  

克隆后业务路径只依赖业务包内预览与 Word；出片与克隆 TTS 由 WorkBuddy 在本机按 `AGENTS.md` 与各工程依赖执行。

## 硬原则（摘要）

- 金样优先 · 内容驱动（有几条写几条）· 审核文案锁定  
- 无授权不仿包装 · 视频默认模板克隆药师声 · 禁止系统机器人音色作正式旁白  
- 先确认后成片；编辑器端口仅制作返修，非业务默认路径  
- **业务默认入口 = WorkBuddy 安装句，不是解压 zip**

## License / 使用范围

- 仓库 **Public**，业务可在 WorkBuddy 一句话 clone 使用（见上文安装句）。  
- 用途定位为**公司内部培训制作**；金样中的品牌包装、药学表述、人声克隆包仅限授权范围内使用，不得当未授权对外素材二次分发。
