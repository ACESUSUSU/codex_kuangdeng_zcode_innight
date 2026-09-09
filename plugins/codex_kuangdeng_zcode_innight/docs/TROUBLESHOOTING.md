# 故障排查

| 现象 | 检查与处理 |
|---|---|
| `codex plugin` 不存在 | 查看当前客户端版本和 `codex --help`；可使用主 Skill + SDK 控制台方式，或更新支持插件的官方 Codex 客户端 |
| GitHub 仓库无法读取 | 检查仓库可见性与当前 Git 认证；私有仓库必须有读取权限，不把 token 放进命令 URL |
| `Missing prerequisites` | 按报错补齐系统依赖；确保 `/usr/bin/python3` 能导入 GI/Cairo，确认 Node/npm/Cargo 位于 PATH |
| Cargo 提示工具链太旧 | 使用能够编译 Cargo.lock 的稳定 Rust；不要把 Ubuntu apt 的旧 Rust 当作本包已测试版本 |
| `GLIBC_2.39 not found` | 不使用不兼容的上游预编译二进制，运行本包源码构建安装器 |
| `DISPLAY` 缺失或会话不是 X11 | 从实际 GNOME/X11 桌面启动 Codex；无图形 SSH 选择官方 CLI 流程，不猜测桌面变量 |
| ZCode 无障碍树太浅 | 确认 toolkit-accessibility 和 ZCode 的 `--force-renderer-accessibility`；使用深度64、节点预算1000，必要时2000 |
| AT-SPI 有树但截图/聚焦失败 | 检查是否锁屏；等操作员正常解锁，不禁用屏幕锁定来完成测试 |
| 中文、下划线或长文本丢失 | 定向正确 window_id；使用本包已验证的非 ASCII 50ms 输入间隔，填入后完整回读，再单独发送 |
| 工具返回成功但界面没变化 | 成功码不是 UI 结果；重新读取树/截图。未确认接纳前不能重复输入或发送 |
| 焦点警告但输入看起来正确 | 深层 Electron 焦点诊断可能误报；按完整树和实际输入文本验收，不只看浅层诊断 |
| 当前任务找不到 MCP 工具 | 新建 Codex 任务；也可用 desktop-console.mjs。避免重复注册两个控制同一桌面的服务器 |
| SDK 缺失 | 重新运行 setup-desktop.sh，确认 Node 版本和 npm 网络；SDK 安装在 ZCODE_DESKTOP_HOME 对应目录 |
| CLI missing API key / provider disabled | 在当前机器的官方 ZCode 中连接并启用 BigModel Coding Plan / GLM-5.3-Flash；不复制别人的凭据 |
| CLI `Unknown option --max-turns` | 已测试版本存在帮助与实际参数不一致；使用启动器的时间限制，不把该参数当成可用约束 |
| 等下一轮时仍看到旧完成状态 | 使用 zcode_round.py 的唯一 marker 绑定新 user message/turn；不能只查会话最后状态 |
| 优惠未生效或额度耗尽 | 按当期官方规则和服务端响应处理；token 统计、余额百分比和本地 cost 都不是免费凭证 |

分享故障时提供客户端/OS/桌面版本、实际错误、脱敏后的任务标记与工具结果。不要公开账户文件、密钥、完整会话库或包含私人内容的截图。
