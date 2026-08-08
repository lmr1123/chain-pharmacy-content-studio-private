# Public 仓库资产权利审计清单

审计日期：2026-08-08

当前结论：**已选择“完整生产仓 Private + 全新历史的脱敏 Public installer”。**
现有生产资产一律按 `private-only` 处理，不再以补齐 Public 逐文件授权作为默认路线。
本清单不是法律意见；Private 化只停止后续匿名分发，不替代内部使用授权，也不能召回迁移前已经发生的 clone、缓存或下载。

## 已锁定处置

- 原业务安装 URL 保持为 `https://github.com/lmr1123/chain-pharmacy-content-studio.git`，但该 entity 重建为全新历史的 Public installer。
- 完整生产仓迁至 `lmr1123/chain-pharmacy-content-studio-private`，初始权限 owner-only，再按最小权限授予业务账号 `read`。
- 第一阶段完整 Private 仓即授权资产包；不因拆 Release/LFS 延误 Public 隔离。
- Public 只负责 GitHub 登录、Private 权限检查、Private clone/update 和 bootstrap 启动；不含模板、预览、声纹、生成器、业务包或公开 ZIP。
- Public 必须是新 repository entity/全新 Git 历史。删除文件、普通 revert、`.gitignore` 或 sparse checkout 均不能清除旧 blob。
- 迁移与回滚权威说明：`docs/private-public-repository-migration.md`。

## 发布原则

- `voice-pack.json` 中的 `user-approved`、`仅用于公司内部` 只说明生产状态，**不等于允许在 Public Git 仓库再分发原始声纹或音频**。
- 业务提供过文件、包装或 Logo，不自动代表可以向公众再分发。
- AI 生成、外部参考、开源下载和内部制作四类资产分别留存来源、许可、生成记录和批准人；无法证明时按发布阻断处理。
- 审计结论必须落到具体文件或可复核的文件清单，不能只写“整体已授权”。

## 待确认资产台账

| 优先级 | 类别与代表路径 | 当前状态 | Public 发布前所需证据 | 可选处置 |
|---|---|---|---|---|
| P0 | 声纹克隆源：`production-library/voices/reference-pharmacist-qwen-v1/prompt.wav`、`production-library/voices/sufuda-courseware-pharmacist-v1/prompt.wav`、`full-clean-mono-24k.wav`，以及 settled 模板内 `voice/` 副本 | `private-only`；禁止进入 Public；内部使用授权仍须维护 | 声音主体身份与书面同意；克隆用途、地域、期限、撤回机制；voice_id 与责任人 | 保留在受控 Private；授权撤回时停用/换声；不得复制到 Public installer |
| P0 | 含品牌、包装、讲师声轨的金样 MP4/PPTX：`production-library/templates/settled/health-video-reference-tech-v1/`、`product-video-faithful-v1/`、`sufuda-mabaloshawei-product-courseware-3-v1/`、`fuler-fanqiehongsu-product-courseware-4-v1/` | `private-only`；多份单文件约 16–55 MB，且存在同内容别名副本 | 品牌/包装/商标授权；讲师、配音、音乐、字体、图片授权；医学文案批准 | 迁入完整 Private 仓；后续可转 Private Release/LFS；Public 仅保留无资产安装说明 |
| P0 | 业务资料包与内部 Word：`outputs/业务使用资料包/` 及 settled 的 `业务提交_填写参考.docx` | `private-only`；可能含业务稿、嵌入图片、作者信息和文档属性 | 文件级 PII/元数据扫描；内部接收范围；嵌入媒体权利；包内不得包含非目标上传、交付物或 workspace | Private 本机构建/受控制品；Public 不发布 Word 或 ZIP；未来空白模板须重新脱敏生成 |
| P1 | 外部参考帧/音频/拆解素材：`poc/reference-replica/reference-analysis/frames/`、`poc/gold-sample/public/audio/`、`poc/gold-sample/public/ganmao-ppt-explain/audio/` | `private-only`；“reference/public”目录名不构成授权 | 原视频/音频来源、权利人、取得方式、许可条款；内部分析与改编范围；引用必要性 | Private 保存或只留不可逆分析摘要；Public 禁止包含 |
| P1 | 品牌与产品图：`production-library/themes/kekang-lingzhi-capsule/refs/`、`poc/gold-sample/public/kekang-lingzhi/packshot.png` 及相关销售案例图 | `private-only` | 包装图、Logo、人物肖像、案例截图的提供人和内部使用授权 | Private 最小权限保存；无内部授权则替换/停用；Public 只允许中性占位说明 |
| P1 | 插画、人物、医学场景和组件：`assets/component-library/`、`poc/gold-sample/public/assets/`、`poc/gold-sample/assets/` | `private-only`；仍需区分自制、AI 生成、开源与第三方参考 | 每个资产的 provenance；模型/工具与生成日期；输入素材权利；开源许可证及署名/NOTICE；人物肖像与医学使用限制 | Private 建 manifest + 哈希并补 NOTICE；Public installer 不携带这些组件 |
| P1 | 仓库级许可 | Public/Private 权利边界必须分离；当前 Public 未声明开源许可证，公开可读不构成再授权 | 若未来开放再分发，补明确许可证与第三方声明；Private 代码/资产/业务资料继续按内部授权 | Public README 已明示可见性不授予 Private 权利；未来变更许可证须独立法务复核 |

## 大文件与重复制品复核

下列是本次只读盘点中优先复核的代表项；大小为约数，最终以发布前哈希清单为准。

- `health-video-reference-tech-v1/风热证_疾病科普视频_可编辑金样_v2.mp4`：约 55 MB。
- `fuler-fanqiehongsu-product-courseware-4-v1/福尔番茄红素_商品培训课件4_金样_v2.mp4`：约 43 MB。
- `sufuda-mabaloshawei-product-courseware-3-v1/速福达玛巴洛沙韦_商品培训课件3_金样_v2.mp4`：约 28 MB。
- 健康视频约 24.6 MB 的两个文件、商品视频约 16.6 MB 的两个文件分别表现为同尺寸别名；须用 Git blob OID/SHA-256 确认重复关系并指定一个权威制品。
- `outputs/业务使用资料包/药店培训内容工厂-业务包.zip`：约 23 MB。重建时必须证明不含 `05_交付物放这里/` 的本地交付物、`07_业务填报上传/` 的业务文件和运行 workspace。

## Public 发布闸门（全部勾选才允许发布资产）

> 以下是“若未来要把某项生产资产重新公开”时的独立门槛。当前路线不发布这些资产；
> `private-only` 资产不得因为 Public installer 已通过而自动获得公开许可。

- [ ] 导出完整跟踪文件清单、字节数、Git blob OID 和 SHA-256；本次审计记录归档。
- [ ] P0 表中每个文件均有“权利人、批准人、用途、期限、公开再分发范围、证据链接”。
- [ ] 声纹主体已单独确认“允许公开原始提示音频/克隆衍生物”；仅内部授权不得通过。
- [ ] 品牌包装、Logo、人物肖像、病例/销售案例和医学文案均有可核验批准。
- [ ] DOCX/PPTX/PDF/媒体元数据、批注、隐藏页、嵌入对象和 PII 扫描为零命中或完成批准豁免。
- [ ] 第三方开源素材逐项对应 LICENSE/NOTICE/署名要求；AI 资产有 provenance 与生成记录。
- [ ] 业务包 zip 解包清单通过白名单校验；无上传、交付、日志、缓存、`node_modules`、模型权重和 workspace。
- [ ] 重复大文件已指定权威制品；其余副本有保留理由，避免 Public 仓库与 clone 成本持续膨胀。
- [ ] 仓库级代码许可证、资产许可证和“内部业务资料不随源码授权”的边界已经法务确认。
- [ ] 最终结论由资产责任人和发布责任人双签；未决项自动阻断发布，不以口头确认放行。

## Public installer 发布闸门（当前必须全部通过）

- [x] 完整生产仓远端已是 Private，当前协作者仅 owner `lmr1123`；后续授权成员按最小权限登记。
- [x] Public installer 是独立 repository entity 和全新历史，未从完整仓 fork/import/mirror/template。
- [x] Public 全部 refs/全部历史中不存在 `assets/`、`production-library/`、`poc/`、`outputs/`、`samples/`、`tasks/` 旧路径。
- [x] Public 不跟踪音视频、PPTX、DOCX、PDF、ZIP、预览 PNG、字体、voice manifest、审批记录或凭证。
- [x] Public README 明示需要 GitHub 登录和 Private `read` 权限；不声称 Public 本身可预览模板或生成内容。
- [x] 安装器不在 URL、命令行或日志中暴露 token；Private clone/update 不走公共镜像。
- [x] 未登录、无权限、网络失败、Private 更新失败四类状态均诚实停止；不回退公开 ZIP 或伪交付。
- [x] 已授权 clean machine 能由 Public installer 拉取 Private，并通过 Private bootstrap、能力探测和门户启动。
- [x] 迁移前最后公开 commit、资产类别和不可召回边界已记录；迁移时间为 2026-08-08。
- [x] Public 安全 CI 采用 `default deny + exact allowlist`，且每次提交扫描工作树、全历史、秘密、大小和禁止扩展名。

## 建议审计记录字段

每条资产记录至少包含：`path`、`sha256`、`git_blob_oid`、`bytes`、`asset_type`、`source_owner`、`provenance`、`license_or_consent`、`allowed_use`、`public_redistribution`、`expiry`、`approver`、`evidence_uri`、`decision`、`reviewed_at`。`decision` 仅允许 `public-approved`、`private-only`、`replace`、`pending`；其中 `pending` 必须阻断 Public 发布。
