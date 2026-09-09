# 使用说明

## 先做只读连通检查

在新的 Codex 任务中输入：

```text
使用 $linux-desktop 检查当前 Ubuntu 桌面。只读取 ZCode 的窗口列表和无障碍树，
确认当前窗口、模型选择器及输入框，不输入、不发送任务。
```

ZCode 控件嵌套较深，已验证参数为 `max_depth:64`、`max_nodes:1000`。节点达到上限时不是完整树，可按需升到 2000；字段缺失不代表消息未发送。

## 单次任务

```text
使用 $codex_kuangdeng_zcode_innight，在可见 ZCode 聊天中完成一个文件任务。
在当前项目 outputs/ 下创建独立目录，派发一份三项演示计划：阅读15分钟、实现25分钟、检查10分钟。
让 ZCode 写出 Markdown 表格及合计，并在聊天中展示结果。
发送前核对窗口、模型和完整输入；结束后读取实际文件、核对合计并保存回执。
只操作本次目录，不修改其他项目文件。
```

输入和发送始终分开。`ok:true` 只表示工具动作返回；必须实际回读完整中文和路径。异常或超时先观察接纳状态，不重复派发。

## 三轮持续协作测试

```text
使用 $codex_kuangdeng_zcode_innight，在当前机器做三轮真实持续协作。
你负责派发、等待、读取输出、分析和验收；ZCode 负责产品实现。
每轮完成后主动审阅并派发下一轮，不等我重复说“继续”。

目标：实现 render_plan(tasks)，把 name/minutes 任务清单转换为 Markdown 表格并正确汇总。
最终支持空列表、保序、不修改输入、非空名称、非负整数分钟（拒绝 bool）、
竖线和换行处理，并提供使用说明。只使用标准库。

在新的独立测试目录中执行：
1. 第一轮做最小版本，完成后由你读取真实代码并运行基本检查。
2. 根据第一轮真实实现和检查结果，编写具体反馈并派发补齐实际缺口的任务；随后独立验收。
3. 根据第二轮审阅修复剩余问题、补齐说明并收尾，由你最终验收。

使用可见桌面时保持同一 GUI 会话，每轮使用新的唯一 marker；
使用 CLI 时每轮独立 run，明确传递前轮产物和 review，不假装共享 CLI 会话。
不要预写全部轮次提示词，不制造问题凑轮数，不由你代写产品冒充 ZCode 产物。
保存 GOAL、LOOP_STATE、每轮任务、session/turn ID、实际模型、检查和 review。
completed 不等于验收通过。真实阻塞时保存状态和原因；达到三轮后停止，不新增第四轮。
最终报告每轮具体做了什么、你怎样据上一轮结果决定下一轮，以及验收和证据路径。
```

正式任务不必固定三轮：先明确目标与验收条件，再持续到目标完成、用户暂停或真实阻塞。需要跨回合/时段继续时，应使用实际可用的正式自动化工具配置续接，不能只声称会自行醒来。细节见[持续协作规则](../skills/codex_kuangdeng_zcode_innight/references/loop.md)。

## SDK 控制台

原生 MCP 工具没有加载到当前任务时，从插件目录启动：

```bash
node skills/linux-desktop/scripts/desktop-console.mjs /absolute/evidence-directory
```

每次输入一行 JSON，收到结果后再执行下一动作：

```json
{"tool":"get_app_state","args":{"app_name_or_bundle_identifier":"zcode","include_screenshot":false,"max_depth":64,"max_nodes":1000},"label":"zcode-state"}
{"tool":"list_windows","label":"windows"}
{"close":true}
```

控制台保存结果 JSON 和截图，必须放在任务明确允许的目录。点击/键盘参数使用当前工具返回的窗口 ID、节点或截图坐标，不复制示例中不存在的 ID。工具定义保存在该目录的 tools.json。控制台是真实 stdio MCP 客户端，不是官方 macOS CUA，也不是 ZCode CLI 的别名。

## CLI 与轮次读取

以下命令从插件目录执行，示例路径需替换为当前机器真实目录。先把具体要求写成 task.md。

```bash
python3 skills/codex_kuangdeng_zcode_innight/scripts/zcode_task.py doctor
python3 skills/codex_kuangdeng_zcode_innight/scripts/zcode_task.py window
python3 skills/codex_kuangdeng_zcode_innight/scripts/zcode_task.py prepare \
  --workspace /absolute/project --task-file /absolute/task.md \
  --run-dir /absolute/project/outputs/zcode-round1 \
  --expect /absolute/project/outputs/zcode-round1/report.md

python3 skills/codex_kuangdeng_zcode_innight/scripts/zcode_run.py \
  --run-dir /absolute/project/outputs/zcode-round1 --check
python3 skills/codex_kuangdeng_zcode_innight/scripts/zcode_run.py \
  --run-dir /absolute/project/outputs/zcode-round1 --mode edit --timeout-seconds 1800
```

`prepare` 只创建任务包；`--check` 只做预检；第二条 run 才发送模型请求。修改 run-dir 之外的产品目录时，prepare 需显式增加 `--allow-write /absolute/project/product`。RESULT.json 属于 ZCode 自报，仍需 Codex 独立验收。

GUI 续聊使用真实 session ID 和本轮 marker：

```bash
python3 skills/codex_kuangdeng_zcode_innight/scripts/zcode_round.py \
  --session-id sess_actual --marker UNIQUE_ROUND_MARKER \
  --wait-seconds 45 --output /absolute/round/execution.json
```

只收集与该轮真实 user message/turn 绑定的结果。`not_started`、`pending_turn_record`、`running` 都不能当作完成，也不能用上一轮 completed 替代当前轮。
