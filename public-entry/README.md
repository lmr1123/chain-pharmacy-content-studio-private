# 连锁药店培训内容工厂 · 安装入口

这里仅包含脱敏安装器，不包含模板、金样、声音、包装、业务 Word 或生产资产。

## WorkBuddy 安装

首次使用时，WorkBuddy 在本目录执行：

```bash
python3 scripts/install_private_studio.py
```

安装器只通过 GitHub 官方 CLI 检查当前账号权限，并将获授权的私有生产仓库安装到同级目录。未登录或无权限时会明确停止，不会用演示文件冒充正式生产能力。

认证由 GitHub CLI 管理；不要把访问令牌粘贴到对话、命令参数或文件中。需要登录时执行：

```bash
gh auth login --hostname github.com --web
```

指定私有生产目录：

```bash
python3 scripts/install_private_studio.py \
  --target /安全的本机目录/chain-pharmacy-content-studio-private
```

## 自审计

Public 发布树带有确定性 SHA-256 清单。发布前及 CI 均执行：

```bash
python3 scripts/audit_public_tree.py .
```

审计失败时不得发布。

## 使用范围

本入口公开可读不代表获得私有生产仓、模板、声音、品牌素材或业务资料的访问、复制或再分发授权；相关能力与资产仅按管理员授予的 Private 权限使用。
