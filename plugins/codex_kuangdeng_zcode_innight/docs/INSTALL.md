# 安装

## 获取源码

```bash
git clone https://github.com/ACESUSUSU/codex_kuangdeng_zcode_innight.git
cd codex_kuangdeng_zcode_innight/plugins/codex_kuangdeng_zcode_innight
```

以下构建和测试命令均在这个**插件目录**执行。如果使用插件 ZIP，解压后直接进入包含 `.codex-plugin/`、`skills/`、`scripts/` 的目录。私有仓库需要先在自己的 Git/GitHub 客户端完成认证；不要把 token 写入 URL、README 或项目配置。

## Ubuntu 桌面完整安装

1. 准备[系统依赖和工具链](DEPENDENCIES.md)，并在本机安装、登录[官方 ZCode](https://zcode.z.ai/cn/docs/install)。本插件不替用户注册或购买套餐。
2. 在已登录、解锁的 GNOME/X11 桌面终端运行：

```bash
bash skills/linux-desktop/scripts/setup-desktop.sh --check
bash skills/linux-desktop/scripts/setup-desktop.sh
```

安装器在用户目录解包源码、应用补丁、执行 `cargo build --locked --release`，再安装固定版本 MCP SDK。构建目录保留，便于复现或诊断；不会覆盖官方 ZCode。

3. 检查并按本机授权启用 AT-SPI：

```bash
gsettings get org.gnome.desktop.interface toolkit-accessibility
gsettings set org.gnome.desktop.interface toolkit-accessibility true
```

4. 在 ZCode 没有任务运行、正常退出后，从桌面终端启动：

```bash
/opt/ZCode/zcode --force-renderer-accessibility
```

如果安装位置不同，使用实际路径。需要持久化启动参数时，在用户级 desktop entry 中保留原 Exec 参数并追加该参数，不直接覆盖系统启动器。详细说明见 [Linux setup](../skills/linux-desktop/references/setup.md)。

5. 安装本仓库的 Codex marketplace 与插件：

```bash
codex plugin marketplace add ACESUSUSU/codex_kuangdeng_zcode_innight --ref main
codex plugin add codex_kuangdeng_zcode_innight@aces-zcode
codex plugin list
```

新建 Codex 任务，检查是否加载主 Skill、`linux-desktop` 及 `computer_use_linux` 工具。插件注册、工具加载与实际桌面可操作是三个不同步骤。当前任务没有热加载工具时，可使用[SDK 控制台](USAGE.md#sdk-控制台)。

仓库使用 `.agents/plugins/marketplace.json`，插件源在 `plugins/codex_kuangdeng_zcode_innight`。市场名称是 `aces-zcode`，不要与已有的 `personal` 市场混淆。相关格式见 [OpenAI 插件管理文档](https://learn.chatgpt.com/docs/enterprise/plugin-management)。

## 只安装 Skill / macOS / 无界面

这条路径不安装 Linux MCP 到 macOS。仍在插件目录中执行：

```bash
mkdir -p "$HOME/.codex/skills"
cp -R skills/codex_kuangdeng_zcode_innight "$HOME/.codex/skills/"
```

若同名目录已存在，先保存自己的版本和 preferences.json，再更新。旧名 `zcode-delegate` 不会被脚本自动删除；确认不再使用后自行归档，避免重复加载两份同用途 Skill。

- macOS：使用宿主已有 Computer Use；备用 AppleScript 的授权要求见 [Mac 输入](../skills/codex_kuangdeng_zcode_innight/references/mac-chat.md)。
- 无图形 Linux/SSH：使用主 Skill 的官方 CLI 流程，不需要 Rust/GTK/Linux 桌面 MCP。运行 `doctor` 检查官方运行时；当前 CLI 启动器仅支持已启用的 BigModel Coding Plan / GLM-5.3-Flash profile。
- Ubuntu 不支持插件命令的 Codex：也可复制 `skills/linux-desktop` 到同一用户 Skills 目录，完成桌面构建后使用 stdio SDK 控制台。该方式不等于已经注册原生 MCP 工具。

## ZIP 分发

```bash
python3 scripts/package.py /absolute/output-directory
```

生成的 ZIP 根目录包含 `.codex-plugin/plugin.json`。可用于支持该格式的 Codex 插件上传/分享入口。若客户端没有 ZIP 导入入口，使用上面的 Git marketplace 安装方法，不把源码 ZIP 当成已安装插件。

## 更新和卸载

保留源码 checkout。更新时 `git pull --ff-only`；Linux MCP 源码/补丁变化后重新运行 `setup-desktop.sh`。然后按当前 `codex plugin marketplace upgrade --help` 刷新 `aces-zcode` 的 Git 快照，再执行相同的 `codex plugin add ...@aces-zcode` 更新缓存，并新建任务。

卸载命令的具体参数以 `codex plugin remove --help` 为准。卸载插件不会自动删除独立的 `computer-use-linux` 运行时或源码。清理之前确认没有其他 Skill/MCP 正在使用；用户级无障碍设置也可能被其他工具共享。
