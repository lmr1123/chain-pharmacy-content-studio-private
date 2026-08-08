# Private 生产仓与 Public 安装入口迁移方案

**状态：** 已完成远端迁移、双向访问验证与 Public 全历史审计
**日期：** 2026-08-08
**目标：** 完整生产仓、签样模板、声纹和授权资产只对获授权成员开放；业务仍保留一条简单、稳定的 WorkBuddy 安装句。

## 0. 已执行结果

- 迁移前最后公开 commit：`1eb6ae0970d55aed232b000d6a9e423de9cc081d`。
- 原 repository entity 已改名为 `lmr1123/chain-pharmacy-content-studio-private` 并设为 Private；完整历史保留，当前 `main` 为 `de52fb054d42e8514fc0e830eb2e6af72fad64be`。迁移实现经 Private PR [#1](https://github.com/lmr1123/chain-pharmacy-content-studio-private/pull/1) 与 clone 稳定性修复 PR [#2](https://github.com/lmr1123/chain-pharmacy-content-studio-private/pull/2) 合并。
- 原名称已由全新 repository entity `lmr1123/chain-pharmacy-content-studio` 复用；Public 只有根 commit `1fbc06ee1ec5c6071930f8243db7fcde045b3d75`、`main` 一个 ref 和 8 个白名单文件。
- Public Actions `audit` 已成功；`main` 强制该检查、线性历史和对话解决，管理员同样受保护，force push 与分支删除关闭。
- 禁用 Git 凭证帮助器后，Public `ls-remote` 与 clone 成功，Private `ls-remote` 失败；授权账号由 Public installer 拉取 Private、校验 marker/资产、运行 bootstrap 和门户刷新成功。
- 真实大仓 clone 曾复现 `curl 18 / early EOF`；安装器现固定 GitHub 官方 HTTP/1.1、浅克隆单分支/无 tags，失败时清理 staging 后重试一次，不输出 GitHub stderr 或凭证。
- 授权 clean clone 的 `private_production_assets=true`、`validate_production_readiness.py=PASS`；未安装本机依赖时 PPTX/TTS/视频能力继续诚实显示为不可用，不以规划包冒充成品。

迁移停止了后续匿名分发，但无法召回迁移前第三方已取得的 clone、缓存或下载。若权利/法务要求清除旧 SHA 的平台缓存视图，仍需另行联系 GitHub Support；不得以此为由把完整仓重新公开。

## 1. 最终仓库实体

迁移后是两个独立 GitHub repository entity，不是同一仓库的两个分支，也不是 fork。

| 实体 | 地址 | 可见性 | 内容与职责 |
|------|------|--------|------------|
| Public installer | `https://github.com/lmr1123/chain-pharmacy-content-studio.git` | Public | 全新历史的脱敏安装器、登录/授权指引、安全策略；不含模板、预览、声纹、生成器或业务包 |
| Private production | `https://github.com/lmr1123/chain-pharmacy-content-studio-private.git` | Private | 当前完整生产仓、签样事实源、生成器、内部文档和第一阶段授权资产包 |

Private production 默认 **owner-only**：新建后先不给任何团队或外部协作者访问；由仓库 owner 逐个授予最小权限。业务账号至少需要 Private 仓 `read` 权限，制作/维护账号才授予 `write` 或更高权限。

第一阶段不拆第二套制品系统：**完整 Private 仓本身就是授权资产包**。这样可以先关闭 Public 再分发风险，并保持现有固定路径和生成链路不变。大文件迁 Private Release/LFS/对象存储属于第二阶段性能治理，不能阻塞本次隔离。

## 2. 不可妥协的边界

- Public installer 不得包含 `assets/`、`production-library/`、`poc/`、`outputs/`、`samples/`、内部 `tasks/` 或现有生产文档的副本。
- Public installer 不得包含 MP4、音频、PPTX、DOCX、PDF、ZIP、金样预览 PNG、voice manifest、审批记录或授权凭证。
- Public installer 不具备模板预览、内容生成、TTS、渲染、业务包构建或降级出片能力；它唯一负责身份检查、Private 访问检查和启动 Private bootstrap。
- Private clone、拉取和更新不得经过 ghproxy、gitclone 等公共镜像；凭证不得写入 URL、命令参数、日志或配置样例。
- Public 无模板或 Private 无权限时必须明确停止，不得回退公开 ZIP、假模板、系统 TTS、`audio-shell` 或制作代跑。

## 3. 为什么必须使用全新 Public 历史

迁移前的 Public 仓历史已经包含金样视频、声纹、业务包和参考文件。删除工作树文件、更新 `.gitignore`、sparse checkout 或普通新提交，都不会删除旧 commit/blob 中的内容。

因此 Public installer 必须满足：

1. 新建 repository entity，或删除旧 Public entity 后以全新空仓重新创建；
2. 不从完整生产仓 fork、import、mirror、template 或保留 Git object database；
3. 只从经过 allowlist 的 `public-entry/` 源目录生成第一次提交；
4. 发布前检查 Public 的全部 refs 与全部历史对象，而不只检查 `HEAD`。

把旧仓改为 Private 只能阻止后续匿名访问，**不能召回迁移前已经发生的 clone、缓存、索引或下载**。应保留暴露时间窗、资产类别、处置时间和责任人记录；必要时由权利人/法务判断是否需要通知、撤回或换声/换素材。Private 化也不替代声纹、品牌、人物肖像和第三方素材的内部使用授权。

## 4. 迁移顺序与成功标准

### 阶段 A：冻结与留证

1. 暂停向现 Public origin 推送生产资产和业务包。
2. 记录远端可见性、默认分支、refs、完整文件清单、Git blob OID、SHA-256 和迁移前最后 commit。
3. 保存 owner 可访问的本地完整仓和远端备份；不得在验证备份前重写或删除唯一远端。

验证：能够从备份恢复迁移前 commit；资产清单可与该 commit 对上。

### 阶段 B：建立 Private production

1. 创建 `chain-pharmacy-content-studio-private`，初始访问仅 owner。
2. 将完整仓库和所需历史推入 Private；确认默认分支和保护规则。
3. 把 Public 安装 URL、公开镜像和“无需登录”旧话术改为 Public installer → Private production 模型。
4. 在一台没有旧 checkout 的机器上，用获授权账号完成 clean clone、环境探测、门户构建和至少一个真实主路径测试。

验证：Private 远端 `visibility=PRIVATE`；未授权账号无法读取；授权账号 clean clone 后生产就绪校验通过。

### 阶段 C：替换 Public entity

1. 将原 Public entity 转 Private 或停止对外服务，确保完整仓不再匿名可读。
2. 用全新历史创建脱敏 Public installer，并保持业务安装句 URL 不变。
3. Public 首次提交只包含安装器 allowlist；CI 对路径、扩展名、大小、秘密和全部历史做阻断检查。
4. Public README 明示需要 GitHub 登录和 Private 仓授权；不承诺公开 ZIP 或镜像回退。

验证：Public 全历史不存在旧资产路径或二进制；未授权安装诚实停止；授权安装能拉取 Private 并启动门户。

### 阶段 D：切流与观察

1. 业务继续只说：

   ```text
   请安装 https://github.com/lmr1123/chain-pharmacy-content-studio.git，然后指引我使用
   ```

2. WorkBuddy 安装 Public installer，检查 GitHub 登录和 Private `read` 权限，再安装/更新 Private production。
3. 观察一轮授权账号安装、更新、门户、PPT 和视频能力探测；失败不发布降级成品。

验证：业务不需要理解双仓；代理日志能区分网络失败、未登录、无授权、Private 更新失败和生产环境缺口。

## 5. 访问与凭证规则

- Private 仓默认 owner-only，授权必须通过 GitHub repository/team 权限，不共享个人 token。
- 优先使用 `gh auth login`、Git Credential Manager 或 SSH agent；安装器只调用凭证管理器，不读取或打印 token。
- 业务人员离岗、角色变化或声纹授权撤回时，及时移除访问并记录复核。
- 不把 Private ZIP 发送到群聊、公开网盘或 Public Release；离线分发必须是受控渠道，并保留接收人、版本、哈希和有效期。
- 安装器不得自动把 Private origin 改回 Public，也不得把 Private URL 交给公共镜像缓存。

## 6. Public allowlist 与发布门

Public 采用 `distribution/public-installer-policy.json` 的 `default_action=deny`。当前唯一允许的源文件与生成文件为：

```text
README.md
AGENTS.md
SECURITY.md
.gitignore
scripts/install_private_studio.py
scripts/audit_public_tree.py
.github/workflows/public-audit.yml
SHA256SUMS.json  # 仅由 exporter 确定性生成
```

`public-entry/` 是源，`SHA256SUMS.json` 是导出产物；二者不得手工扩容。即使有扩展名 denylist，也不能改成“默认允许”；否则无扩展名媒体、嵌入 Base64、改名制品和授权凭证仍可能漏出。若以后需要公开空白模板，必须先修改机器策略与保护测试，并从中性源确定性生成，通过 DOCX 解包、元数据、嵌入对象、PII 和人工复核，不能直接复制当前 settled Word。

## 7. 回滚方案

回滚只针对安装可用性，不得把完整生产仓重新开放为 Public。

| 故障 | 安全回滚 |
|------|----------|
| Public installer 发布失败 | 回滚到上一版脱敏 installer commit；Private 保持不变 |
| Private clean clone/启动失败 | 保留旧 Private checkout，修复 Private 分支或回滚 Private release；Public 继续提示维护，不提供 ZIP |
| 权限配置错误 | 立即恢复 owner-only，审计 collaborator/team，再逐个恢复授权 |
| Public 检出禁止资产 | 立即下线 Public entity/分支，保留审计证据，用新 entity 和新历史重发；普通 revert 不足以删除 blob |
| 新入口大面积不可用 | 暂停新安装，已授权机器继续使用最后验证的 Private commit；不得把完整仓改回 Public |

迁移完成前保留迁移前 commit 的 owner 私有备份；完成并验证后，再按保留策略处理临时迁移仓和本地副本。

## 8. 验收命令

```bash
gh repo view lmr1123/chain-pharmacy-content-studio-private \
  --json visibility,isPrivate,url

gh repo view lmr1123/chain-pharmacy-content-studio \
  --json visibility,isPrivate,url
```

期望：production 为 `PRIVATE`，installer 为 `PUBLIC`。

在全新 Public clone 中检查全部历史：

```bash
git rev-list --objects --all | \
  rg ' (assets|production-library|poc|outputs|samples|tasks)/'
```

期望零输出。再检查最大历史 blob：

```bash
git rev-list --objects --all | \
  git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | \
  sort -k3nr | head -n 20
```

Public 不应出现 MB 级生产资产。最终必须完成三类安装测试：未登录、已登录但无权限、已授权；前两类诚实停止，第三类成功启动 Private 门户。

## 9. 完成定义

- 完整生产仓匿名访问已关闭，Private 默认 owner-only。
- Public 是独立 entity、独立全新历史，只含安装入口 allowlist。
- 业务安装句保持不变，但文档不再承诺“Public 无需登录、公共镜像或 ZIP fallback”。
- 授权账号在 clean machine 能由 Public installer 拉取 Private 并启动；无授权不产生半安装或伪交付。
- Public 全 refs/全历史安全扫描通过；迁移前公开历史的不可召回边界已留档。
- 第一阶段完整 Private 仓作为授权资产包通过验证，之后才能讨论大文件拆包优化。
