# HarBeat Wear

HarBeat Wear 保存 Flow Wrist、Flow Ring 和 Wear Hub Gateway 的设备侧代码。

## 当前状态

- Wrist：Waveshare ESP32-S3-Touch-AMOLED-2.06，V0.1 Alpha 开发中；
- Hub Gateway：RK3588 / BlueZ，V0.1 开发中；
- Ring：XIAO nRF54L15 Sense，V0.1 手势音效戒指设计已批准；

## 目录

- `wrist/flow-wrist`：ESP-IDF Wrist 固件；
- `hub-gateway`：RK3588 BLE 与音乐引擎网关；
- `contracts`：BLE 和 Engine IPC 的唯一协议来源；
- `docs/superpowers`：批准的设计和执行计划；
- `ring/flow-ring`：nRF Connect SDK / Zephyr Ring 固件与开发文档。

先阅读 `docs/superpowers/specs/2026-08-27-flow-wrist-field-ready-v0.1-design.md`。

## 提交边界

- Wrist 开发分支使用 `codex/wrist-<任务>`，只修改 `wrist/**`。
- Ring 开发分支使用 `codex/ring-<任务>`，只修改 `ring/**`。
- 两类 PR 都会先检查目录边界和组件测试；全部通过后自动 squash merge。
- 协议、CI 和根文档使用 `codex/shared-<任务>`，由人工审阅后合并。

详细规则见 [`docs/REPOSITORY-WORKFLOW.md`](docs/REPOSITORY-WORKFLOW.md)。

## 开发环境

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
```

Wrist host tests 与 ESP-IDF build 分开运行，避免 ESP-IDF 的交叉编译工具覆盖 macOS host compiler。
