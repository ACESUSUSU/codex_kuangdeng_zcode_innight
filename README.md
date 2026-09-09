# codex_kuangdeng_zcode_innight

让 **Codex 派发任务给官方 ZCode，等待对应回复，读取真实产物，审阅后继续下一轮**。

本仓库以 Ubuntu 22.04 的适配版本为基础，包含主协作 Skill、`linux-desktop` Skill，以及 Linux 桌面 MCP 的上游源码和补丁。默认使用 GLM-5.3-Flash；名称中的 `innight` 不表示只能夜间使用，也不代表永久免费。

## 支持哪些场景

| 场景 | 入口与范围 |
|---|---|
| Ubuntu 22.04 + GNOME 42 + X11 + x86_64 | 完整桌面流程：观察 ZCode 窗口、填写并回读、发送、等待、读取，同一聊天多轮协作 |
| Linux/macOS 无界面或 SSH | 官方 ZCode CLI；每轮独立 run，通过产物和 review 续接 |
| macOS 可见聊天 | 单独安装主 Skill，使用宿主已有 Computer Use；已有明确授权时可使用 AppleScript 备用输入 |
| Wayland、ARM、其他桌面/发行版 | 本适配包尚未完成同等验收 |

本插件不包含官方 ZCode 软件、Codex 客户端或模型账户。它也不是官方 macOS CUA 后端。

## 依赖

| 依赖 | 用途 |
|---|---|
| Codex + Git | 运行 Skill、从仓库安装；插件方式需要支持 `codex plugin` 的版本 |
| 官方 ZCode + 当前机器自己的有效模型账户 | 执行任务；CLI 启动器目前读取 BigModel Coding Plan / GLM-5.3-Flash profile |
| Python 3.9+ | 标准库脚本和测试；Ubuntu 22.04 的 Python 3.10 已验证 |
| Node.js / npm | 推荐 Node 22；桌面安装器检查 Node >=18，Node 22 已验证 |
| Rust/Cargo、C 编译工具 | 仅完整 Linux 桌面 MCP 需要；从随包源码在本机编译 |
| GTK3 / PyGObject / Cairo / X11 工具 | 仅 Linux 可见桌面需要，安装命令见下文 |
| `@modelcontextprotocol/sdk@1.30.0` | 安装器从 npm 安装到当前用户的运行时目录 |

Rust 依赖由随包 `Cargo.lock` 固定。首次构建需要访问 Cargo registry 和 npm。详细版本、系统包和平台差异见[依赖说明](plugins/codex_kuangdeng_zcode_innight/docs/DEPENDENCIES.md)。

## Ubuntu 快速安装

在**已登录、已解锁的 GNOME/X11 桌面终端**执行，避免把无图形 SSH 环境当作可见桌面。

```bash
git clone https://github.com/ACESUSUSU/codex_kuangdeng_zcode_innight.git
cd codex_kuangdeng_zcode_innight
cd plugins/codex_kuangdeng_zcode_innight

sudo apt-get update
sudo apt-get install -y build-essential pkg-config git curl ca-certificates tar patch tzdata \
  python3 python3-gi python3-cairo python3-gi-cairo gir1.2-gtk-3.0 \
  wmctrl x11-utils xdotool gnome-screenshot

# 先通过你信任的发行渠道准备 Node 22、npm 和 Rust/Cargo。
node --version
npm --version
rustc --version
cargo --version

bash skills/linux-desktop/scripts/setup-desktop.sh --check
bash skills/linux-desktop/scripts/setup-desktop.sh
```

安装器不自动运行 sudo、修改 shell profile、登录账户或更改全局审批。默认运行时目录为 `${XDG_DATA_HOME:-$HOME/.local/share}/computer-use-linux`，可用 `ZCODE_DESKTOP_HOME` 指定。

按机器的既有授权启用无障碍；在 ZCode 正常退出、没有任务运行时重新启动：

```bash
gsettings set org.gnome.desktop.interface toolkit-accessibility true
/opt/ZCode/zcode --force-renderer-accessibility
```

官方软件安装位置不同则替换最后一条路径。之后从同一桌面启动 Codex，使其继承桌面环境。

### 安装为 Codex 插件

```bash
codex plugin marketplace add ACESUSUSU/codex_kuangdeng_zcode_innight --ref main
codex plugin add codex_kuangdeng_zcode_innight@aces-zcode
```

然后**新建 Codex 任务**加载两个 Skill 和 MCP。如果仓库可见性为私有，Git 必须先具备该仓库读取权限。市场与缓存更新、ZIP 安装、只安装 Skill、macOS 和无界面路径，见[完整安装说明](plugins/codex_kuangdeng_zcode_innight/docs/INSTALL.md)。

## 开始使用

把下面内容发给 Codex：

```text
使用 $codex_kuangdeng_zcode_innight，在可见 ZCode 聊天中执行这个任务。
请先检查当前桌面、ZCode 登录和模型，使用 GLM-5.3-Flash。
每轮结束后读取真实回复和文件，独立分析验收，再依据实际结果派发下一轮。
不要预写全部轮次，不要把旧 completed 当成本轮完成。
任务目标：……
允许修改的目录：……
验收条件：……
达到目标或遇到需要我处理的真实阻塞时停止并报告。
```

完整三轮测试 prompt、CLI 样例、SDK 控制台、结果读取和暂停续接见[使用说明](plugins/codex_kuangdeng_zcode_innight/docs/USAGE.md)。

## 时段和个人偏好

分发包默认不强加作者的个人工作时段。用户/项目约定优先；如需北京时间周一至周五 14:00–18:00 暂停，在自己维护的主 Skill 目录创建 `preferences.json`：

```json
{"pause_beijing_workdays": true}
```

该文件不进入 Git 或插件 ZIP。夜间活动只按当期[智谱官方规则](https://docs.bigmodel.cn/cn/coding-plan/notice/event-glm-5.3-flash)判断；活动过期不等于不能按正常套餐使用。UI 百分比、token 统计和本地 `cost=0` 都不是逐请求零扣额凭证。

## 验证、源码与打包

```bash
# 从仓库根目录执行；不请求模型，也不操作桌面
python3 -B -m unittest discover \
  -s plugins/codex_kuangdeng_zcode_innight/skills/codex_kuangdeng_zcode_innight/scripts \
  -p 'test_zcode_*.py' -v
python3 plugins/codex_kuangdeng_zcode_innight/scripts/package.py ./dist
```

插件 ZIP 的根目录包含 `.codex-plugin/plugin.json`。源码树、许可证、依赖与本次验证边界见 [VALIDATION.md](VALIDATION.md)。上游 Rust 源码存于 `skills/linux-desktop/assets/` 的归档中，补丁以独立文件保存；编辑方法见[开发说明](plugins/codex_kuangdeng_zcode_innight/docs/DEVELOPMENT.md)。

这是共享桌面的操作工具，会使用真实鼠标和输入焦点。运行时应协调桌面使用；锁屏后等待正常解锁。常见问题见[故障排查](plugins/codex_kuangdeng_zcode_innight/docs/TROUBLESHOOTING.md)。

项目与适配补丁采用 [MIT](LICENSE)。上游 `computer-use-linux` 的许可证与归属见[第三方说明](plugins/codex_kuangdeng_zcode_innight/THIRD_PARTY_NOTICES.md)。本项目不代表 OpenAI、ZCode 或智谱官方背书。
