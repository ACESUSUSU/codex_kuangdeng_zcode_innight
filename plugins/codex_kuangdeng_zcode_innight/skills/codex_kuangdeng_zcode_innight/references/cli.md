# 官方 CLI

用于 SSH、无图形会话或用户明确选择 CLI 的任务；可见协作使用桌面流程。
scripts/zcode_run.py 仅启动官方安装包的 zcode.cjs，依次查找：

- Linux: /opt/ZCode/resources/glm/zcode.cjs
- macOS: /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs
- 本机服务器安装: ~/.zcode/server/agents/glm/zcode.cjs

非标准安装用 --runtime 指定已确认的官方文件；Node 从 PATH 发现，也可用 --node。
先运行 zcode_task.py doctor，不假设其他机器的安装路径适用。

```bash
python3 <skill-dir>/scripts/zcode_run.py --run-dir /absolute/project/run --check
python3 <skill-dir>/scripts/zcode_run.py --run-dir /absolute/project/run --mode edit --timeout-seconds 1800
```

--check 不发模型请求。启动器读取本机已登录 ZCode 的 Coding Plan profile，将凭据
仅放入官方子进程环境，不复制其他机器凭据、不输出密钥、不伪造渠道。
plan 适用于不要求写文件的任务；prepare 默认要求 RESULT.json，通常使用 edit。
只有任务确实需要命令执行且已有授权时使用 build，不自动升级 yolo。

本机可选暂停规则对 CLI 同样生效。启动器不提供通用绕过开关；明确时段例外的
可见测试可直接走已授权桌面入口。

每个 run 保存 launch.json、runtime.stdout.json、runtime.stderr.log 和 execution.json。
已有 launch.json 时先检查状态，不盲目重发。CLI 每轮独立 run，通过 GOAL、产品文件和
review 续接，不宣称共享 CLI 会话；不要与 GUI 并发写同一个会话。
