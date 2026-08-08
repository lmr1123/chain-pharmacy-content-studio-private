# WorkBuddy 安装约束

- 只运行 `python3 scripts/install_private_studio.py` 安装获授权的私有生产仓库。
- 不索取、不回显、不落盘 GitHub token；登录交给 `gh auth login --hostname github.com --web`。
- 未登录或无私库权限时诚实停止：Public 入口不含模板、声音或生产资产，不能生成正式 PPTX/MP4。
- 不使用镜像、代理仓库、公开 ZIP 或演示素材代替私有生产仓库。
- 安装成功后由私有仓库 bootstrap 指引业务使用。
