# 连锁药店培训内容工厂 · 安装入口

业务只需在 WorkBuddy 说：

```text
请安装 https://github.com/lmr1123/chain-pharmacy-content-studio.git，然后指引我使用
```

## WorkBuddy 做什么（业务不用操作）

```bash
git clone https://github.com/lmr1123/chain-pharmacy-content-studio.git \
  ~/Documents/chain-pharmacy-content-studio-installer
cd ~/Documents/chain-pharmacy-content-studio-installer
python3 scripts/install_private_studio.py
```

安装器默认用官方 HTTPS **匿名**拉取生产仓
`lmr1123/chain-pharmacy-content-studio-private`（当前为 Public），
**不需要** GitHub 账号、设备申请、Deploy key 或管理员批准。

成功后会自动 bootstrap 并打开业务引导页。业务只做：看模板 → 交内容 → 确认 → 取成片。

## 自审计

```bash
python3 scripts/audit_public_tree.py .
```

审计失败时不得发布。

## 使用范围

生产仓虽已公开可读，模板、声纹与素材仍仅供公司内部培训制作；不得外传或再分发为公开商品。
