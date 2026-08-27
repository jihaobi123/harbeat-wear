# Flow Wear V0.1 开发文档导航

更新日期：2026-08-27  
适用范围：手环、RK3588 Hub Gateway、音乐引擎适配层  
文档状态：方案已确认，RK3588 全链路仍需真机验收

这份文件是项目文档的入口。新开发者或其他 AI 接手时，先读这里，再按任务进入对应方案。不要只看聊天记录推断协议，也不要把 Mac 模拟结果当成 RK3588 真机结果。

## 1. 建议阅读顺序

1. [总体设计](superpowers/specs/2026-08-27-flow-wrist-field-ready-v0.1-design.md)：产品范围、交互、系统边界和主要决策。
2. [总执行计划](superpowers/plans/2026-08-27-flow-wrist-field-ready-v0.1-master.md)：开发阶段、Gate、依赖关系和交付顺序。
3. [仓库与协议基线](superpowers/plans/2026-08-27-wear-repository-contracts-baseline.md)：目录归属、共享合同和 CI 规则。
4. [Hub Gateway 方案](superpowers/plans/2026-08-27-hub-gateway-vertical-slice.md)：BlueZ、GATT、命令去重、Engine IPC、systemd 和 RK3588 验收。
5. [音乐引擎适配方案](superpowers/plans/2026-08-27-rk3588-music-engine-wear-adapter.md)：Gateway 与现有音乐系统之间的接口和状态同步。
6. [手环现场加固](superpowers/plans/2026-08-27-flow-wrist-field-hardening.md)：触控、离线、重连、功耗、错误恢复和现场误触。
7. [验证与发布](superpowers/plans/2026-08-27-flow-wear-validation-release.md)：端到端验收、证据留档和发布门槛。

手环现有实现的快速说明见 [AI 开发接手手册](AI-DEVELOPMENT-HANDOFF.md)。BLE v1 的具体字段见 [BLE 协议](ble-protocol-v1.md)。

## 2. 已经约定的产品行为

首版只提供两类现场控制：能量和风格。

- 能量固定为 1–5 五档，曲库使用相同分档。
- 风格先支持 `hiphop`、`breaking`、`funk`、`locking`。
- 用户选中后立即发送，不增加二次确认。
- 一次操作应在 3–5 秒内完成；整个音乐切换目标为 10–20 秒。
- 上一次切歌完成前，手环禁止发送新命令，并提示当前阶段尚未完成。
- BPM 和调性暂时不允许手动修改。BPM 可以显示，但不是 V0.1 的高优先级控制项。
- 过渡界面优先显示风格和距离切换完成的时间，能量和 BPM 作为次要信息。
- 屏幕保持暖纸白底。人物使用低像素、粗线条的街舞插画，不使用高成本逐帧动画。

离线状态允许进入主页和二级页面浏览，但点击选项不能生成待发送任务。重新连接后也不能自动补发离线选择。

## 3. 输入与唤醒规则

- 首页点击 `ENERGY` 或 `STYLE` 进入二级页面。
- 二级页面左右拖动切换选项，点击当前选项立即发送。
- 左上返回区域要向屏幕中心内缩，并保留足够大的触摸面积，避免 AMOLED 圆角影响命中。
- 触摸屏幕或短按 BOOT 可以唤醒。RST 只做硬件复位，不能复用成应用按键。
- 普通页面无操作后熄屏；音乐切换过程中只降亮度，不应直接隐藏进度。
- 触控优先于无触控手势。首版交付不能依赖尚未完成现场校准的手势。

## 4. 系统职责

```text
Flow Wrist
  负责 UI、输入、BLE Command、Catalog/Snapshot 展示
        │
        │ BLE v1 / CBOR / 加密 GATT
        ▼
RK3588 Hub Gateway
  负责配对、授权、去重、状态权威、重连和错误映射
        │
        │ Engine IPC v1 / Unix socket / NDJSON
        ▼
Music Engine
  负责选曲、实际切换、目标 BPM 和完成状态
```

手环表达用户意图，不直接决定最终播放结果。Gateway 返回的 Snapshot 是手环 UI 的唯一业务状态来源。BLE indication 成功只说明 Hub 收到了命令，不代表音乐已经切换。

Gateway 是唯一允许连接 Music Engine 的穿戴设备入口。戒指以后接入时复用 Gateway，不要再建一条直连音乐引擎的协议。

## 5. BLE v1 固定内容

| 接口 | UUID | 方向 |
|---|---|---|
| Flow Service | `464C4F57-0001-4F57-8101-000000000001` | 服务 |
| Command | `464C4F57-0001-4F57-8101-000000000002` | Wrist → Hub，Indicate |
| Hub State | `464C4F57-0001-4F57-8101-000000000003` | Hub → Wrist，加密写入 |
| Catalog | `464C4F57-0001-4F57-8101-000000000004` | Hub → Wrist，加密写入 |

连接顺序固定为：Connect、Pair、订阅 Command、写 Catalog、写首次 Snapshot。五步全部完成后才能显示 READY。

命令只有两种：

```json
{"v":1,"kind":"command","id":42,"op":"set_energy","value":5}
{"v":1,"kind":"command","id":43,"op":"set_style","value":"breaking"}
```

Hub 应在 500 ms 内返回带有相同 `ack_id` 的 Snapshot。标准阶段是 `accepted`、`preparing`、`transitioning`、`completed`。执行期间 `locked=true`；完成时先更新 `current`，再解锁。

相同 `command.id` 只能执行一次。重复收到同一命令时，Gateway 返回该命令的最新 Snapshot，不能再次要求 Music Engine 切歌。

## 6. Gateway 与音乐引擎接口

Gateway 使用 `/run/flow-wear/engine.sock` 连接 Music Engine。传输格式为一行一个 JSON 对象，协议版本为 1，单行上限 16384 bytes。

启动顺序固定为：

1. 加载唯一授权手环的信息；
2. 连接 Engine 并完成 `hello`；
3. 用 `get_state` 取得当前真实播放状态；
4. 连接已授权手环；
5. 完成 GATT 初始化；
6. 对外报告 READY。

Gateway 不根据手环选择自行推算目标 BPM。Music Engine 接受请求后返回完整 `target`，后续进度也由 Engine 提供。Engine 断开时，Gateway 不能创建新请求来猜测或重做上一次操作，应先重新查询状态并对账。

## 7. 安全与授权

- 手环使用 LE Secure Connections，Hub 保存 bond。
- Hub 只允许一个主控手环。新设备必须经过显式配对窗口，不能后台自动替换。
- 配对候选需要同时满足 `FLOW-WRIST-` 名称前缀和 Flow Service UUID，再按 RSSI 选择。
- 配对窗口结束后立即关闭 Pairable，注销临时 Agent。
- `flow-wearctl` 只能连接 Gateway 的本地控制 socket，不能绕过 Gateway 直接操作 BlueZ。
- 不得为了绕过 macOS 的配对限制而移除加密属性。安全链路必须在 RK3588 / BlueZ 上验收。

## 8. 开发阶段和 Gate

| Gate | 目标 | 通过条件 |
|---|---|---|
| Gate 0 | 冻结仓库边界与协议 | 文档、Schema、示例和共享测试向量一致 |
| Gate 1 | Hub Gateway 竖切 | RK3588 可配对、自动重连、ACK 小于 500 ms、重复命令只执行一次 |
| Gate 2 | Music Engine 适配 | 两种命令都能驱动真实选曲和 10–20 秒切换 |
| Gate 3 | 手环现场加固 | 触控、离线、熄屏、重启和异常状态稳定 |
| Gate 4 | 端到端发布 | 现场长时间运行、证据归档和回滚方案完成 |

Gate 必须按顺序通过。Fake Engine、Mac BLE 工具和主机测试可以帮助开发，但不能代替 RK3588、BlueZ 和真实音频链路的证据。

## 9. 下一次 RK3588 对接

联调前先让 RK3588 负责人确认这些信息：

- 操作系统版本、BlueZ 版本和蓝牙适配器型号；
- Music Engine 的启动方式、运行用户和 Unix socket 权限；
- Engine 当前状态对象的来源，以及切换过程如何产生进度；
- 日志目录、时间同步方式和现场网络是否可用；
- 谁负责保存 bond、谁可以执行 `pair` 与 `unpair`；
- 故障时允许重启 Gateway、BlueZ 或 Engine 中的哪一层。

首次联调按下面的顺序记录结果：

1. 显式配对并确认 bond 已保存；
2. 订阅 Command，写入 Catalog 和首次 Snapshot；
3. 手环进入 READY，主页显示 Hub 在线；
4. 发送一次能量命令，记录 Command ID、ACK 延迟和完成时间；
5. 发送一次风格命令，记录相同指标；
6. 切换过程中再次点击，确认新命令没有进入 Engine；
7. 重放同一个 CBOR Command，确认 Engine 执行次数仍为 1；
8. 分别重启 Gateway 和 BlueZ，记录恢复 READY 的时间；
9. 保存日志并计算 SHA-256，再填写 Gate 1 报告。

## 10. 交给其他 AI 时可以直接使用的说明

```text
你正在接手 Flow Wear V0.1。先阅读：
1. docs/DEVELOPMENT-PLAN-INDEX-ZH.md
2. docs/superpowers/specs/2026-08-27-flow-wrist-field-ready-v0.1-design.md
3. docs/superpowers/plans/2026-08-27-flow-wrist-field-ready-v0.1-master.md
4. 与当前任务对应的子计划

不要修改 BLE v1 UUID、四个 style id、五档能量或立即发送规则。
不要把 Mac/Fake 测试写成 RK3588 真机通过。
修改前先说明涉及哪个 Gate；完成后把验证证据写入对应报告。
如果需要改变已冻结协议，先提出版本升级方案，不能直接破坏 v1。
```

当前最合理的开发入口是 Gate 1：先完成 RK3588 上的安全配对、GATT 初始化和 Engine IPC 对账。通过以后再做 Music Engine 的真实切歌适配。
