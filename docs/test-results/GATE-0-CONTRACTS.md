# Gate 0 Verification

- Date: 2026-08-27
- Git commit: `72e3e269ebf5fbfd616df297a03149ae1f5f2b21`
- Wrist version: `wrist-v0.1.0-alpha.1-candidate`
- Gateway version: `not built (Gate 0)`
- BLE contract: `1`
- Engine IPC contract: `1`
- RK3588 serial / asset ID: `not applicable (contract-only gate)`
- Wrist device ID: `FLOW-WRIST-F892`

## Before repository move

全新 clone 第一次运行时，C host tests 找不到未入库的 TinyCBOR 源码，人物素材测试也缺少 Pillow。这属于开发环境缺项，不是固件失败。按 `dependencies.lock` 用 ESP-IDF 5.5.5 恢复 managed components，并在隔离 Python 环境安装固定版本依赖后，迁移前基线结果为：

- 7 组 C host tests：PASS；
- Hub mock：4 tests，PASS；
- Dancer assets：4 tests，PASS。

缺失依赖已写入根目录 `requirements-dev.txt`；CI 会先恢复 ESP-IDF 锁定组件，再运行 host tests。

## After repository move

Wrist 工程移动到 `wrist/flow-wrist` 后，使用同一依赖、同一测试命令复测：

- 7 组 C host tests：PASS；
- Hub mock：4 tests，PASS；
- Dancer assets：4 tests，PASS；
- 迁移前后行为结果一致。

## Contract checks

- Markdown relative links：PASS；
- BLE v1 Golden Vectors：2 条，PASS；
- Golden Vector CBOR 解码与 semantic 对象一致：PASS；
- Engine IPC v1：9 种消息全部覆盖，PASS；
- Engine IPC JSON Schema 对完整样例校验：PASS；
- Python contract/tool tests：10 tests，PASS；
- `git diff --check`：PASS。

## Frozen boundaries

- Wrist ↔ Gateway：`contracts/ble-v1.md`；
- Gateway ↔ Music Engine：`contracts/engine-ipc-v1.md`；
- BLE 编码样例：`contracts/golden-vectors/ble-v1.json`；
- Engine IPC 机器约束：`contracts/engine-ipc-v1.schema.json`。

后续实现如需改变字段含义、UUID、消息 framing 或错误语义，必须先升级合同版本，不能只改某一端代码。

## Decision

Gate 0: PASS

Gateway implementation may start. BLE v1 and Engine IPC v1 are frozen.
