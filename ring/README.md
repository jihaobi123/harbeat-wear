# Flow Ring

Ring 与 Wrist 是两个独立固件组件。Ring 通过 RK3588 Hub Gateway 接入，不复用 Wrist Command UUID。

- 固件和板级文档：[`flow-ring/`](flow-ring/)
- V0.1 设计：[`flow-ring/docs/2026-08-28-flow-ring-xiao-nrf54l15-v0.1-design.md`](flow-ring/docs/2026-08-28-flow-ring-xiao-nrf54l15-v0.1-design.md)

Ring 开发分支使用 `codex/ring-<任务>`，并且只能修改 `ring/**`。
