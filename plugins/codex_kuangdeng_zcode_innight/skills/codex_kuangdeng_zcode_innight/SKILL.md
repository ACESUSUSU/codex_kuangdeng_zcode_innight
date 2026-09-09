---
name: codex_kuangdeng_zcode_innight
description: "Delegate tasks through official ZCode and supervise continuing collaboration: send, wait for the matching round, read actual output, review, and issue the next evidence-based task. Supports visible Ubuntu/macOS desktop chat and the official CLI for headless work."
---

# codex_kuangdeng_zcode_innight

Codex 负责目标、派发、等待、读取、审阅和验收，ZCode 负责实现工作包。
默认模型为 Coding Plan 的 **GLM-5.3-Flash**。用户当前指定的入口、模型、权限和时段优先。

## 选择入口

- **Ubuntu 可见桌面：** 使用同包 `linux-desktop` Skill 和 `computer_use_linux` MCP，
  先读 [Ubuntu 桌面流程](references/ubuntu-desktop.md)。用户要求桌面可见时不以 CLI 代替。
- **macOS：** 使用当前环境的原生 Computer Use；输入故障且已有适用授权时，读
  [Mac 备用输入](references/mac-chat.md)。本包的 Linux MCP 不支持 macOS。
- **SSH、无图形会话或用户明确选择 CLI：** 读 [官方 CLI](references/cli.md)。
  仅用官方安装包运行时，不用第三方同名命令或自写模型 HTTP 请求。

工具尚未加载时，Linux Skill 提供真实 stdio MCP SDK 控制台。它操作可见窗口，
不是 ZCode CLI 派发，也不是官方 macOS CUA 后端。

## 授权与时段

遵守当前用户和项目约束，不把作者的个人偏好推广给其他安装者。
可选本机 `preferences.json` 中 `pause_beijing_workdays: true` 启用北京时间
周一至周五 14:00-18:00 暂停；未配置时不额外限制时段。该文件不随插件发布。

```bash
python3 <skill-dir>/scripts/zcode_task.py window
```

时间报告不授予任务权限。已有明确的本次时段例外时，记录原文和适用范围后执行，
不重复询问。暂停期间可准备任务及只读检查；用户要求稍后继续时使用正式自动化工具，
不声称本回合结束后会自行醒来。使用优惠前读 [活动规则](references/night-promotion.md)
并核对当前官方说明；额度百分比、token 数和 `cost=0` 均不是逐请求零扣额证明。

## 准备任务

写明工作目录、权威输入、允许修改路径、交付物和验收条件。共享项目明确文件归属；
工作包不自动授权发布、对外消息或修改凭据。研究结果保留 verified/reported/planned/blocked。

```bash
python3 <skill-dir>/scripts/zcode_task.py doctor
python3 <skill-dir>/scripts/zcode_task.py prepare \
  --workspace /absolute/project --task-file /absolute/task.md \
  --run-dir /absolute/project/outputs/zcode-unique \
  --expect /absolute/project/outputs/zcode-unique/report.md
```

prepare 创建 marker、packet、manifest、dispatch，并要求 ZCode 写 RESULT.json。
它不派发请求，路径边界是任务约定。纯对话可直接保存带唯一 marker 的任务正文，
不必要求模型读写文件。已有任务包不可覆盖。

## 桌面发送与跟进

1. 观察窗口和输入框。新任务选正确项目；续聊进入当前流程管理的原会话，等上一轮
   结束。不要覆盖用户草稿或向其他运行中任务追加工作。
2. UI 核对模型与本轮权限模式，纯对话可用现有计划模式。
3. 填入但不发送，回读完整文本并与任务文件逐字比较。异常或超时先观察；
   `ok:true` 不证明输入成功，不盲目填入或重发。
4. 点击一次发送，绑定真实 `sess_...`。标题可能变化，不能依赖“最新任务”。
5. 按本轮 marker 等待、读取，再检查真实回复与产物。每次等待不超过 60 秒。
   审批、认证或额度错误按实际状态处理，不无限重试。

```bash
python3 <skill-dir>/scripts/zcode_task.py status --marker UNIQUE_MARKER
python3 <skill-dir>/scripts/zcode_round.py \
  --session-id sess_actual --marker UNIQUE_ROUND_MARKER \
  --wait-seconds 45 --output /absolute/round/execution.json
```

这些脚本只读本机 ZCode 数据库；不兼容时回到 UI，不改写数据库。核对实际模型记录，
不只相信选择器；completed 后仍须独立语义验收。

多轮任务读 [持续交互流程](references/loop.md)。保存 GOAL、LOOP_STATE、每轮任务、
session/turn ID、实际模型、检查和 review。**先读上一轮真实结果，再编写并派发下一轮**，
不要预写全部提示词、制造问题或每轮等用户说继续。GUI 可共享同会话；
CLI 每轮独立 run，靠文件和 review 续接。同一 session 不代表同一 turn。

达到目标、约定轮数、用户暂停或真实阻塞时收尾，报告入口、模型、检查、剩余问题和证据。
历史验证范围见 [验证说明](references/validation.md)，不代表未来请求必然成功或免费。
