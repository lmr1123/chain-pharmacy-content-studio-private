# WorkBuddy 安装约束

- 业务只说安装 URL；由你执行命令，不让业务登录 GitHub、配置 SSH、提供 token 或敲命令行。
- 运行 `python3 scripts/install_private_studio.py`。默认匿名 HTTPS 拉取官方生产仓，**无需**账号或设备授权。
- 安装成功后由生产仓 bootstrap 打开引导页，并按五步指引业务。
- 不使用镜像、代理仓库或演示素材冒充正式生产能力。
- 网络失败时说明真实卡点并停止；仅当 HTTPS 与已登录 gh 都不可用时，才回退设备 Deploy-key 路径。
