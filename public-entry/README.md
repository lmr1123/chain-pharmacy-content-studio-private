# 已废弃 · 请改用生产仓

本仓库曾是双仓时代的安装入口，**现已废弃**。

## 新业务请用（唯一生产仓）

在 WorkBuddy 说：

```text
请安装 https://github.com/lmr1123/chain-pharmacy-content-studio-private.git，然后指引我使用
```

WorkBuddy 直接：

```bash
git clone --depth 1 --single-branch --no-tags \
  https://github.com/lmr1123/chain-pharmacy-content-studio-private.git \
  ~/Documents/chain-pharmacy-content-studio-private
cd ~/Documents/chain-pharmacy-content-studio-private
python3 scripts/workbuddy_bootstrap_for_business.py
```

## 兼容：仍粘贴了本仓 URL 时

WorkBuddy 仍可运行本仓转发脚本（会安装生产仓）：

```bash
python3 scripts/install_private_studio.py
```

请尽快改用上面的生产仓安装句；本入口仓将仅作兼容，不再增加功能。
