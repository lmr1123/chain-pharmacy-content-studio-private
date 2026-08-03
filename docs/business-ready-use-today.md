# 业务今天就能这样用

**包路径：** `outputs/业务使用资料包/药店培训内容工厂-业务包.zip`  
**刷新：** `python3 scripts/refresh_business_delivery.py`  
**代理提示：** `docs/workbuddy-system-prompt.md`（装 WorkBuddy 的电脑粘贴）

---

## 你是业务时（不装开发环境）

1. 解压业务包  
2. 双击 `01_模板货架/index.html` 看 6 个课型封面和关键页  
3. 选一个状态为 **「已签样 · 可换主题量产」** 的课型（第一次建议「绿色单品 PPT」或「商品培训视频」）  
4. 打开 `02_空白Word/<课型>/本课型怎么填.md`，复制空白 Word 填写  
5. 复制 `04_WorkBuddy口令卡.md` 的口令 + 附件 Word/图 → 发给 WorkBuddy  
6. **先验** `06_你将收到的初稿长什么样/` 同结构的初稿/缺口/分镜  
7. 用 `业务验收清单.md` 勾选；通过后才要成片  
8. 成片放 `05_交付物放这里/`

### 硬规则（你有权要求）

- 联合用药写 2 组 → 成品只能 2 行  
- 没有的章节不能硬凑空页  
- 无授权包装不能出假包装  
- 视频不能用系统机器人音色  

---

## 你是 WorkBuddy 代理时

1. 加载 `docs/workbuddy-system-prompt.md`  
2. 读 `production-library/templates/settled/business-catalog.json` 锁定 template  
3. 列表/联合用药调用 `scripts/content_driven_rules.py`  
4. 先交初稿+缺口（模板在 `production-library/templates/business-delivery/`）  
5. 业务确认后再 PPTX/MP4  

---

## 尚未默认全自动（诚实边界）

| 能力 | 现状 |
|------|------|
| 看货架 / 填 Word / 口令 / 验收 | **可用** |
| 初稿·缺口·分镜标准结构 | **可用** |
| 内容驱动 2→2 行规则 | **可用（代码回归）** |
| Word→终稿 PPTX 一键无人工 | 仍依赖代理按 settled 生成器执行；绿色模板有既有流水线 |
| 视频克隆旁白一键 | voice_id 已绑；部分本地 pack 资产仍在 D2 收尾 |

业务侧体验以「包 + 口令 + 先确认后成片」为准；制作/代理侧继续补自动生成深度。
