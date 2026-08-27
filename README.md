# HarBeat Wear

HarBeat Wear 保存 Flow Wrist、Wear Hub Gateway 和未来 Ring 的设备侧代码。

## 当前状态

- Wrist：Waveshare ESP32-S3-Touch-AMOLED-2.06，V0.1 Alpha 开发中；
- Hub Gateway：RK3588 / BlueZ，V0.1 开发中；
- Ring：只保留未来边界，本轮不实现。

## 目录

- `wrist/flow-wrist`：ESP-IDF Wrist 固件；
- `hub-gateway`：RK3588 BLE 与音乐引擎网关；
- `contracts`：BLE 和 Engine IPC 的唯一协议来源；
- `docs/superpowers`：批准的设计和执行计划；
- `ring`：未来 Ring 的范围说明。

先阅读 `docs/superpowers/specs/2026-08-27-flow-wrist-field-ready-v0.1-design.md`。

## 开发环境

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
```

Wrist host tests 与 ESP-IDF build 分开运行，避免 ESP-IDF 的交叉编译工具覆盖 macOS host compiler。
