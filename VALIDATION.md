# 发布验证

本仓库整理自 2026-09-09 的 Ubuntu 22.04 适配插件源码。发布包与主 Skill 名均为
`codex_kuangdeng_zcode_innight`，保留用户指定的下划线拼写。

## 本次源码发布检查

- 22 项 Python 离线行为测试通过；不调用模型、不操作桌面。
- Linux shell 脚本语法与 Node stdio 控制台语法检查通过。
- 随包上游源码归档可解包，Ubuntu 补丁可在干净解包目录完整应用。
- 已检查插件文本及补丁后源码，没有操作员用户名路径、真实会话标识或凭据；示例与测试使用占位符。
- Ubuntu 适配机的 setup-desktop.sh --check 通过。
- 插件清单验证、两个 Skill frontmatter 解析、marketplace 路径和文档链接检查通过。
- 最终插件 ZIP 共 37 个文件，manifest 位于归档根目录，五份操作文档齐全，未含 preferences.json、数据库或 Python 缓存。

## 继承的适配记录

适配阶段记录了 Ubuntu 22.04 / GNOME 42 / X11 / x86_64 的桌面发送及同会话续聊，
以及源码重建、SDK 连通、中文输入与截图测试。详情保存在
[插件验证记录](plugins/codex_kuangdeng_zcode_innight/VALIDATION.md)。原始私人桌面证据不进入本仓库。
这些历史记录不是本次发布时重新执行的模型任务。

## 边界

- 本次没有从全新系统安装全部依赖，没有重复桌面输入或发起新的模型请求。
- 未在本次发布中完成新任务里的原生插件工具加载；marketplace/manifest 校验与 MCP 实际加载分别对待。
- 普通 Skill 风格检查器要求连字符，会对主 Skill 的下划线名称报风格错误；适配记录中的 Codex skills/list 已接受该名字。不得把风格例外写成“所有检查器均通过”。
- 不承诺 Wayland、ARM、其他桌面与发行版的同等可用性，也不承诺任意未来请求免费或长期任务必然可靠。

安装、使用和复现入口均在 [README](README.md) 与插件 docs 中。
