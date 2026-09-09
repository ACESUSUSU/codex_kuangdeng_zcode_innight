# 依赖与平台

Python 脚本还需要系统 IANA 时区数据库；Ubuntu 对应 `tzdata`，下方系统包命令已包含。核心脚本不需要额外的 pip 包。

## 按运行方式区分

| 方式 | 必需 |
|---|---|
| 主 Skill 与只读证据脚本 | Codex、Python 3.9+（zoneinfo、sqlite3 等标准库） |
| 官方 ZCode CLI | 上述依赖、已安装的官方 ZCode、Node、当前机器自己的 BigModel Coding Plan 配置 |
| Ubuntu 可见桌面 | 上述账户/客户端、已解锁 GNOME/X11、Linux MCP、GTK3/Python GI/Cairo/X11 工具 |
| macOS 可见桌面 | 主 Skill、宿主已有的 macOS 桌面工具；AppleScript 仅在获得明确授权时使用 |

Node 22 是推荐环境；适配机使用 Node 22.22.2，Mac CLI 曾使用 Node 24。桌面 SDK/安装器最低检查是 Node 18，不据此保证所有官方 ZCode 版本都可在 Node 18 运行。

Rust 使用能够编译随包 Cargo.lock 的稳定工具链；已记录的构建使用 Rust 1.98.1。源码没有声明可保证的最低 Rust 版本，因此不把测试版本写成已证实的最低要求。可从 [Rust 官方](https://rustup.rs/)准备工具链；Node 发行包见 [Node.js 官方](https://nodejs.org/en/download)。

## Ubuntu 22.04 系统包

```bash
sudo apt-get update
sudo apt-get install -y build-essential pkg-config git curl ca-certificates tar patch tzdata \
  python3 python3-gi python3-cairo python3-gi-cairo gir1.2-gtk-3.0 \
  wmctrl x11-utils xdotool gnome-screenshot
```

其中 `/usr/bin/python3` 必须能导入 GI 和 Cairo；只在虚拟环境里安装同名 Python 包不能替代系统 GTK/GI 依赖。安装器检查这些依赖，但不会自动安装系统包。

## 随包与下载的内容

- 随包：`computer-use-linux` v0.5.0 上游完整源码归档、原许可证、Cargo.lock、Ubuntu 22.04 补丁。
- 构建时下载：Cargo.lock 对应的 Rust crates；npm 的 `@modelcontextprotocol/sdk@1.30.0` 及其依赖。
- 目标机器本地生成：Linux release 二进制、npm 模块与构建目录。
- 不随包：官方 ZCode 二进制/运行时、Codex、模型权重、账户配置、密钥、会话库、截图。

本包不使用上游预编译二进制：已观察到其 GLIBC 要求高于 Ubuntu 22.04，故采用本机源码构建。上游项目可能支持更多桌面，但本补丁包的已验证范围是 Ubuntu 22.04 / GNOME 42 / X11 / x86_64。

## 桌面环境变量

从实际桌面会话启动 Codex，让它继承 DISPLAY、XAUTHORITY、XDG_RUNTIME_DIR、DBUS_SESSION_BUS_ADDRESS 等。不要复制其他机器的值，也不要把它们固定为 `:0` 等猜测值。

`ZCODE_DESKTOP_HOME` 可覆盖运行时目录；未设置时使用 `${XDG_DATA_HOME:-$HOME/.local/share}/computer-use-linux`。启动器识别其下已有的本机兼容依赖，但不会为新机器复制旧机器的系统库。
