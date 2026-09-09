# Ubuntu 22.04 安装与迁移

本包目标是已登录且解锁的 GNOME/X11 桌面。Codex 应从该桌面启动，继承 DISPLAY、XAUTHORITY、
XDG_RUNTIME_DIR 和 DBUS_SESSION_BUS_ADDRESS。不要在 SSH 中猜测这些值或复制他人凭据。
本包不安装官方 ZCode、不替用户登录，也不改变账户或全局审批设置。

## 依赖和安装

需要 Node.js >=18（22 已测试）、npm、Rust/Cargo（1.98.1 已测试）、C 编译工具和 GTK3。
Ubuntu 系统依赖示例，由机器操作员按现有授权安装：

```bash
sudo apt-get install build-essential pkg-config python3-gi python3-cairo python3-gi-cairo gir1.2-gtk-3.0 \
  wmctrl x11-utils xdotool gnome-screenshot
```

Ubuntu 22.04 默认仓库的 Node 版本可能过旧，先确认 node --version；使用已配置的
Node 18+ 安装。Rust 使用已安装的 rustup/Cargo。安装器不会自动运行 sudo、修改
shell profile、全局 Codex 配置或凭据。

```bash
bash <skill-dir>/scripts/setup-desktop.sh --check
bash <skill-dir>/scripts/setup-desktop.sh
```

安装器从随包的上游源码压缩包及 Ubuntu 补丁构建，Cargo.lock 固定 Rust 依赖；
编译依赖和 MCP SDK 首次下载需要网络。运行时默认安装到
${XDG_DATA_HOME:-$HOME/.local/share}/computer-use-linux，可用 ZCODE_DESKTOP_HOME 指定。
上游预编译程序曾要求 GLIBC_2.39，不能直接用于 Ubuntu 22.04 的 GLIBC_2.35。

## 桌面配置

AT-SPI 需要 GNOME toolkit accessibility。检查后按用户已授权的安装范围启用：

```bash
gsettings get org.gnome.desktop.interface toolkit-accessibility
gsettings set org.gnome.desktop.interface toolkit-accessibility true
```

官方 ZCode 以 --force-renderer-accessibility 启动才能暴露聊天控件。先检查现有
进程和任务，不结束用户运行中的任务。可在正常退出后从桌面终端启动：

```bash
/opt/ZCode/zcode --force-renderer-accessibility
```

不同安装位置先定位官方应用。持久化参数时，按实际安装的 desktop entry 创建用户级
副本，保留原 Exec 参数，不直接覆盖系统启动器。此操作不需要改账户凭据。

## Codex 与回读

插件 .mcp.json 指向随包 launcher。安装后开启一个新的 Codex 任务以加载 MCP；
当前任务可用 desktop-console.mjs。不要把注册成功说成当前任务已获得原生工具定义。
已有独立 computer_use_linux 注册时，本机可继续使用它，避免同时启用两个重复服务器。

先用 get_app_state/list_windows 验证树和窗口，再截图；输入测试必须定向一个空的
一次性编辑控件或当前已授权的 ZCode 草稿，并实际回读。ZCode 模型请求不属于安装验证。
环境还没准备好时报告缺少的具体依赖，不隐藏失败或伪造成功。
锁屏时可能仍能读取 AT-SPI，但不能据此断言窗口可聚焦或可输入；整屏截图能辅助
确认锁屏状态。暂停输入并等待正常解锁，不修改屏幕锁定或认证配置。

卸载插件不会删除独立运行时和源码。只在确定无人使用时删除选定运行时目录。
撤销无障碍设置或用户启动器改动前，确认其他工具是否仍依赖它们。
