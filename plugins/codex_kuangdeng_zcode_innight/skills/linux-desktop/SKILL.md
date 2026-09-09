---
name: linux-desktop
description: "Operate Linux desktop apps through computer_use_linux MCP using accessibility trees, screenshots, clicking, typing, hover, scrolling and dragging. Includes Ubuntu 22.04/X11 fixes and portable setup; prefer dedicated browser tools for web pages."
---

# Linux 桌面操作

已验证基线：Ubuntu 22.04、GNOME 42、X11、x86_64，使用本包的 computer-use-linux
v0.5.0 补丁版本。其他发行版、Wayland 和 ARM 未经本包验收。它不是官方 macOS CUA 后端。

## 接入

优先调用宿主已加载的 `computer_use_linux` MCP 工具。插件通常需要新的 Codex 任务
才能加载；当前任务未暴露工具时，使用真实 stdio MCP SDK 控制台：

```bash
node <skill-dir>/scripts/desktop-console.mjs /absolute/evidence-directory
```

运行时由 `ZCODE_DESKTOP_HOME` 定位，默认
`${XDG_DATA_HOME:-$HOME/.local/share}/computer-use-linux`。不要照搬其他机器的
DISPLAY、XAUTHORITY、D-Bus 地址或绝对路径。首次安装/迁移读 [安装说明](references/setup.md)。

控制台每次一条 JSON，等待响应后再执行下一动作：

```json
{"tool":"get_app_state","args":{"app_name_or_bundle_identifier":"zcode","include_screenshot":false,"max_depth":64,"max_nodes":1000},"label":"zcode-state"}
{"tool":"list_windows","label":"windows"}
{"close":true}
```

它持有一条真实 MCP 连接并保存结果和图片。结果不明的变更调用不能重放。

## 观察、输入、核对

1. 用 get_app_state 和 list_windows 识别当前窗口。节点来自当前连接的最新树；
   ZCode 嵌套较深，需要 max_depth:64、max_nodes:1000。
   节点数达到上限时不能视为完整树；可按需增至 max_nodes:2000（当前硬上限），
   仍缺目标控件时结合截图判断，不把未出现在树中当成消息未发送。
2. 点击、输入、按键均指定当前 window_id。后台窗口的节点坐标不能保证点击目标；
   ok:true 只表示工具派发成功。菜单、导航或切换应用后重新读树。
3. 优先最新节点或语义选择器。使用坐标前先截图，窗口截图采用 client-relative
   坐标，点击时传 relative:true。
4. 使用 type_text/press_key；仅对确实支持 EditableText 的控件使用 set_value。
   ZCode entry 文本可能是占位对象，真实内容在 paragraph/static 子节点，
   应与任务文件逐字比较。
5. ZCode 需以 --force-renderer-accessibility 启动才能暴露深层控件。
   helper 的浅层焦点诊断可能误报无焦点，用完整树和实际文本判断，不直接重试。
6. 已验证补丁采用非 ASCII 50ms 输入间隔和随文本长度增加的命令超时。
   12ms 曾在长中文中丢字。149、169、174 字符的实际任务已通过，仍须每次回读。
7. type_text 的换行可能触发编辑器提交。聊天先用单行指令，或确认编辑器行为后
   分段输入并用 Shift+Enter 换行。发送始终作为单独动作。

## 鼠标与收尾

hover 支持 window_id 加 element_index 或桌面 x/y；drag 使用桌面起止坐标加
window_id；scroll 支持四方向。短暂的青色指针/光环跟随真实共享鼠标并透传点击，
不是独立输入席位。每组动作后读回状态，截图默认包含鼠标。

完成后发送 {"close":true}，关闭控制台及其光标层，保留用户应用运行。
锁屏时树仍可能可读，但定向截图和聚焦会失败。观察到锁屏后暂停输入，
等待操作员正常解锁，不通过禁用锁屏或修改认证设置完成测试。
向 ZCode 提交任务时使用 codex_kuangdeng_zcode_innight 的授权、模型和逐轮审阅规则。
历史验证与边界见 [验证说明](references/validation.md)。
