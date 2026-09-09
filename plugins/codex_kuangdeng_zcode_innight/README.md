# codex_kuangdeng_zcode_innight

Codex 插件：在官方 ZCode 桌面中派发任务、等待对应轮次、读取实际结果并持续审阅推进。
包含两个 Skill 和一个 Linux 桌面 MCP 入口。

源码仓库：[ACESUSUSU/codex_kuangdeng_zcode_innight](https://github.com/ACESUSUSU/codex_kuangdeng_zcode_innight)。
本文件位于插件目录（ZIP 解压后的根目录）。新安装请按[完整安装说明](docs/INSTALL.md)操作，
并参考[依赖](docs/DEPENDENCIES.md)、[使用](docs/USAGE.md)、[排错](docs/TROUBLESHOOTING.md)与[源码开发](docs/DEVELOPMENT.md)。

| 组件 | 用途 |
| --- | --- |
| codex_kuangdeng_zcode_innight | 有边界的任务派发、同会话续聊、逐轮审阅及只读执行证据 |
| linux-desktop | 无障碍树、截图、键鼠、悬停、滚动、拖拽及 Ubuntu 安装流程 |

## 平台与准备

完整验证基线为 Ubuntu 22.04、GNOME 42、X11、x86_64。Codex 从已登录桌面启动，
官方 ZCode 在当前机器安装并登录 Coding Plan。默认模型 GLM-5.3-Flash。
其他 Linux 环境未完成同等验收。macOS 可单独使用委派 Skill 配合宿主原生桌面工具，
本插件自带的 MCP 只面向 Linux，不宣称提供官方 macOS CUA 后端。

首次部署先完成 [Ubuntu 依赖与安装](skills/linux-desktop/references/setup.md)：

```bash
bash skills/linux-desktop/scripts/setup-desktop.sh --check
bash skills/linux-desktop/scripts/setup-desktop.sh
```

安装器在当前用户目录从随包源码和补丁构建。需要 Node 18+（22 已测试）、npm、
Rust/Cargo、C 构建工具、GTK3 和 X11 工具。首次构建需要联网下载依赖。
不自动安装系统包，不修改全局审批、shell profile、ZCode 账户或凭据。
可通过 ZCODE_DESKTOP_HOME 指定运行时目录，默认使用 XDG_DATA_HOME 下的 computer-use-linux。

启用 GNOME toolkit accessibility，并在正常退出 ZCode 后加
--force-renderer-accessibility 启动。不要为了配置重启而打断用户运行中的任务。

## 使用

安装插件后开启新的 Codex 任务加载工具。使用 `$linux-desktop` 读取当前窗口；
使用 `$codex_kuangdeng_zcode_innight` 派发已授权工作并逐轮推进。MCP 入口由 .mcp.json 配置，
当前任务工具尚未加载时可用实际 stdio 控制台：

```bash
node skills/linux-desktop/scripts/desktop-console.mjs /absolute/evidence-directory
```

先观察最新窗口/节点，定向 window_id 输入，实际回读后才单独发送。每轮 marker 不同，
同一 GUI 会话保持 session ID。上一轮完成并审阅后，再依据真实结果写下一轮任务。
CLI 只用于无图形会话或明确选用 CLI 的工作，不能冒充可见桌面对话。

如果当前机器已有独立注册且正常工作的 computer_use_linux，可先使用原注册；
不要同时启用两个重复桌面服务器。插件安装成功不代表当前任务已热加载工具。

## 个人规则

分发包不包含运行机器的账户配置、本地用户名、真实 session ID、桌面截图或个人固定派发时段。
用户及项目已有授权始终优先，脚本的时间检查不授予模型调用权限。

可在自己维护的 codex_kuangdeng_zcode_innight Skill 目录下创建 preferences.json：

```json
{"pause_beijing_workdays": true}
```

这会启用北京时间工作日 14:00-18:00 暂停。个人文件不进入发布包，缓存插件升级后
需要按本机管理方式保留自己的偏好；也可以直接在项目/用户指令中约定时段。
本次明确授权的例外记录范围后执行，不反复询问同一授权。
夜间优惠需核对当期官方规则，不能因为历史测试成功就宣称免费。

## 验证和分发

[VALIDATION.md](VALIDATION.md) 区分历史实测、此次打包验证和未测范围。
离线行为检查不会向 ZCode 发请求：

```bash
python3 -B -m unittest discover -s skills/codex_kuangdeng_zcode_innight/scripts -p 'test_zcode_*.py' -v
```

生成上传包：

```bash
python3 scripts/package.py /absolute/output-directory
```

ZIP 根目录包含 .codex-plugin/plugin.json。将生成的 codex_kuangdeng_zcode_innight-0.1.0.zip 用于
Codex 的插件上传/分享流程；上传账号、组织、市场或仓库由发布者自行选择。
打包脚本只做本地构建，不会自动上传或创建远程仓库。manifest 中的发布者和 repository/homepage
对应上方的实际源码仓库。

GitHub 仓库提供独立的 aces-zcode marketplace；本包不携带作者的个人 marketplace 或 config.toml。
源码和补丁以 MIT 发布，第三方归属见
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
