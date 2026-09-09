# 源码与开发

插件目录内容：

```text
.codex-plugin/plugin.json       插件清单
.mcp.json                       Linux MCP 启动入口
skills/codex_kuangdeng_zcode_innight/
  SKILL.md                     协作规则
  scripts/                     官方 CLI、任务包、轮次读取、AppleScript 与测试
skills/linux-desktop/
  scripts/                     构建安装、MCP launcher、stdio SDK 控制台
  assets/                      上游源码归档、Ubuntu 补丁、上游许可证
docs/                          安装、依赖、使用和排错
scripts/package.py             生成插件 ZIP，不上传
```

仓库根目录另有 `.agents/plugins/marketplace.json`，让 Codex 从 GitHub 找到这个插件。插件名与主 Skill 名保留指定的 `codex_kuangdeng_zcode_innight`。当前已测试 Codex 运行时接受下划线；某些通用 Skill 风格检查器只推荐连字符，这项差异在验证说明中单独列明。

## 查看和编译 Linux 后端源码

从插件目录执行：

```bash
work_dir="$(mktemp -d)"
tar -xzf skills/linux-desktop/assets/computer-use-linux-v0.5.0.tar.gz \
  --strip-components=1 -C "$work_dir"
patch -d "$work_dir" -p1 < skills/linux-desktop/assets/ubuntu22.patch
cd "$work_dir"
cargo build --locked --release --bin computer-use-linux
```

这是可编辑的完整上游源码加补丁，不是仅有二进制。修改后应相对于原始上游基线生成 a/、b/ 路径形式的补丁，并验证在全新解包目录仍能应用。保留上游许可证及 Cargo.lock；如果更新依赖或上游版本，记录对应版本与新的验证范围。

## 离线检查与打包

从插件目录执行：

```bash
python3 -B -m unittest discover -s skills/codex_kuangdeng_zcode_innight/scripts -p 'test_zcode_*.py' -v
bash -n skills/linux-desktop/scripts/setup-desktop.sh skills/linux-desktop/scripts/start-desktop.sh
node --check skills/linux-desktop/scripts/desktop-console.mjs
python3 scripts/package.py /absolute/output-directory
```

Python 测试只使用标准库和临时 fixtures，不调用模型、不操作用户桌面。桌面真实输入与模型任务应另行在已授权环境中验证。

打包器只收集插件清单、Skills、脚本、文档和许可证，排除个人 preferences.json、Python 缓存。不要把账户配置、节点依赖目录、构建产物、会话或截图放入源码目录；生成 ZIP 放在仓库 dist 或外部目录。
