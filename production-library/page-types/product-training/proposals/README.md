# 页型提案（product-training · L1 生长通道）

操作手册：`docs/page-type-growth-channel.md`  
Schema：`production-library/schemas/page-type-proposal.schema.json`

## 用法

1. 复制 `_TEMPLATE.proposal.json` → `<page_type_id>.proposal.json`
2. 按手册步骤 A–F 实现、QA、签样、注册
3. 签样通过后更新本提案 `status` 与 `signoff`

## 索引

| 提案 | 状态 | 说明 |
|------|------|------|
| `_TEMPLATE` | — | 空壳 |
| `hook_pain_data` | settled | M3 签样先例（历史回填） |
| `combination_guidance` | settled | M3 签样先例（历史回填） |
| `precautions` | settled | M3 签样先例（历史回填） |

进行中的提案保持 `draft` / `ready_for_qa`；**不要**在未签样时把 registry 标 `settled`。
