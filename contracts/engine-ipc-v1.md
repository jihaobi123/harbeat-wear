# Flow Wear Engine IPC v1

本合同是 Hub Gateway 与 RK3588 Music Engine 之间的唯一接口定义。Wrist 不直接连接 Music Engine。

## 传输

```text
Socket: /run/flow-wear/engine.sock
Transport: AF_UNIX / SOCK_STREAM
Framing: UTF-8 NDJSON, one object per line
Maximum line: 16384 bytes including newline
Permissions: 0660, group flow-wear
Gateway response budget: 400 ms
```

双方逐行解析，禁止在一行中发送多个 JSON 对象。无效 UTF-8、无效 JSON、超长行、未知 `kind`、错误字段类型或缺少必填字段均返回 `rejected/protocol_error` 后关闭连接。

## 公共规则

- `v` 固定为整数 `1`；
- `request_id` 由 Gateway 生成，最长 64 字符，在去重保留期内唯一；
- `wrist_command_id` 是 Wrist 的无符号 32 位 Command ID；
- Energy 只能是 1–5；Style 只能是 `hiphop`、`breaking`、`funk`、`locking`；
- BPM 是 Engine 选中目标曲后的只读状态，Wrist V0.1 不发送 BPM 调节；
- 所有时间戳是 Unix epoch 毫秒；倒计时 `eta_ms` 使用单调时钟计算；
- Engine 对同一 `request_id` 只执行一次，重复请求返回已缓存的最新结果；
- Gateway 对同一 `wrist_command_id` 只创建一个 `request_id`。

## 建连与状态同步

Gateway 每次连接先发送：

```json
{"v":1,"kind":"hello","client":"hub-gateway","capabilities":["set_energy","set_style","transition_progress"]}
```

Engine 版本兼容时回复 `hello_ok`。版本或必要能力不兼容时回复 `rejected/unsupported`。Gateway 启动或重连后发送 `get_state`，在拿到有效 `state` 前不得向 Wrist 宣告 READY。

`state.current` 是当前正在播放的权威音乐状态；`target` 在没有进行中的切换时必须是 `null`；`locked=true` 表示 Engine 正处理一个方向切换。

## 设置方向

Gateway 把 Wrist 意图转换为：

```json
{"v":1,"kind":"set_direction","request_id":"gw-test-command-1","wrist_command_id":42,"op":"set_energy","value":5,"received_at_ms":1787812345678}
```

`op=set_energy` 时 `value` 必须是 1–5；`op=set_style` 时 `value` 必须是四个 Style ID 之一。Engine 必须在 200 ms 内完成语义校验、候选选择和缓存可用性检查，使 Gateway 能在 400 ms 预算内得到首个结果。

成功受理回复 `accepted`，其中 `target` 是 Engine 实际选中的完整状态，不是 Gateway 推测值。之后同一连接可发送 `progress`：phase 只能从 `preparing` 进入 `transitioning`，不得倒退。完成后发送 `completed`，此时 `current` 成为新的权威状态，连接关闭。

## 拒绝和错误

Engine IPC v1 只使用以下错误：

- `busy`：已有切换正在处理；
- `unsupported`：版本、能力、operation 或 value 不受支持；
- `no_candidate`：本地可播放曲库没有符合主条件的候选；
- `engine_error`：音频服务、缓存或执行线程失败；
- `protocol_error`：消息 framing 或 schema 无效。

`unauthorized_device` 与 `transport_error` 属于 Gateway ↔ Wrist 状态，不从 Engine 产生。

## 重启、断线和去重

- Engine 至少保存最近 256 个 `request_id` 的最新响应，进程内保留；
- Gateway 持久化 Wrist Command 与 Engine Request 的映射，写临时文件并 `fsync` 后原子替换；
- accepted 后连接断开，Gateway 先用 `get_state` 对账，不能自动重发新的 request；
- 如果 target 已成为 current，Gateway 合成为 completed；否则向 Wrist 报 `transport_error` 并解锁；
- Engine 重启后正在进行的任务不保证续跑，Gateway 必须对账；
- 任一侧不得把超时当作再次执行同一音乐操作的授权。

机器可读字段约束见 [JSON Schema](engine-ipc-v1.schema.json)，完整消息集合见 [示例 JSONL](examples/engine-ipc-v1.jsonl)。
