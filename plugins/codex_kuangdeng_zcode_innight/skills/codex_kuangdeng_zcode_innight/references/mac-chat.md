# Mac 可见聊天与已授权的备用输入

默认遵循当前 Computer Use 工具的规则。2026-09-09 的现场测试中，CUA 可以读取界面，但键盘/剪贴板输入出现 `noWindowsAvailable`、clipboard timeout、中文与下划线丢失。用户明确允许 AppleScript 后，官方桌面聊天派发成功。

本参考文档不授予任何权限。只有用户已明确指定/授权 AppleScript，且授权适用于当前工作范围时，才使用以下助手；已有适用授权不必每轮重复询问。没有适用授权则使用允许的入口或说明实际输入阻塞。不要改数据库、伪造客户端标识或调用私有 IPC。

1. 用 CUA 确认当前选中的是本循环管理的聊天、模型正确、上一轮已结束；读到空的后续输入框。若有用户未发送的新草稿，不擅自覆盖。
2. 将本轮完整指令写入 UTF-8 文本文件，然后聚焦该聊天输入框。
3. 填入但不发送：

```bash
osascript <skill-dir>/scripts/zcode_chat.applescript fill /absolute/round-2/dispatch.txt
```

4. 用 CUA 实际读取输入框，核对完整中文、文件路径、轮次 marker，避免丢字和重复消息。`FILLED_NOT_SENT` 只表示脚本返回，不能替代这一步。
5. 核对后发送一次：

```bash
osascript <skill-dir>/scripts/zcode_chat.applescript send
```

6. 观察消息进入聊天，再用本轮 marker 查询新 turn。没有消息接纳证据时先检查，不盲目重发。

助手保留并恢复原剪贴板，填入与发送分开。实际验证中 `the clipboard as record` 曾报类型错误，所以实现使用 `the clipboard`；不要把剪贴板内容打印到工具输出。
