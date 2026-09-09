# Ubuntu 可见 ZCode 协作

桌面环境由同包 linux-desktop Skill 的 MCP/SDK 控制台操作。
get_app_state 使用 max_depth:64、max_nodes:1000，list_windows 查询当前 window_id。
不要把旧的数字节点、窗口 ID、DISPLAY 或用户目录用于新的环境。

新任务先选项目。纯对话可以选择“不在项目中工作”，ZCode 会使用自己的 default
workspace；不要在这个默认目录中执行其他项目的文件修改。
GLM-5.3 和 GLM-5.3-Flash 是两个选项，必须核对完整名称。查看 Coding Plan 与额度，
账户套餐和余额百分比不证明这次请求免费。

输入显式定向 window_id，entry 的实际文字可能在 paragraph/static 子节点。
填入后逐字匹配才单独点击一次发送。完整树显示输入正确时，不因为浅层焦点警告重发。
工具超时同样先观察 UI 和 marker 接纳状态。

首次派发用唯一 marker 查真实 session 并存入 LOOP_STATE。之后保持 session，
每轮换 marker，等待上一轮完成并实际审阅后再写新任务：

```bash
python3 <skill-dir>/scripts/zcode_round.py \
  --session-id sess_actual --marker UNIQUE_ROUND_2 \
  --wait-seconds 45 --output /absolute/round-2/execution.json
```

命令只读数据库，绑定本轮 user message 和 turn。not_started、pending_turn_record、
running 均不能当成完成；旧 completed 也不能用作新回复。没有接纳证据先看 UI。
逐轮读取真实回复、必要文件和实际模型记录，再保存独立 review、下一步或停止原因。
Markdown 单换行可能在 UI 渲染成一个段落；需要精确文本时同时读取本轮原始回复。

已有验证覆盖两轮依赖前文的可见续聊，不必为 Skill 文档更新重复发模型任务。
新模型请求仍应属于用户当前授权，离线 fixtures 和只读桌面调用优先用于工具验证。
