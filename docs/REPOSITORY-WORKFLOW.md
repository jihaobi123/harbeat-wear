# Wrist 与 Ring 提交流程

## 目录

```text
wrist/flow-wrist/   手环固件
ring/flow-ring/     戒指固件
contracts/          共用协议
docs/               仓库级文档
hub-gateway/        RK3588 Gateway
```

## 分支

| 工作类型 | 分支格式 | 允许修改 | 合并方式 |
|---|---|---|---|
| Wrist | `codex/wrist-<任务>` | `wrist/**` | 测试通过后自动 squash merge |
| Ring | `codex/ring-<任务>` | `ring/**` | 测试通过后自动 squash merge |
| Shared | `codex/shared-<任务>` | contracts、docs、tools、CI | 人工合并 |
| Gateway | `codex/gateway-<任务>` | `hub-gateway/**` | 人工合并 |

Wrist 或 Ring PR 一旦修改范围外文件，`component-boundary` 会失败，PR 不会自动合并。

## 自动合并门禁

Wrist PR 必须通过：

- `component-boundary`
- `contracts`
- `wrist-host`

Ring PR 必须通过：

- `component-boundary`
- `contracts`
- `ring-ci`

自动合并器只处理仓库内部、目标为 `main`、非 draft、没有冲突的 Wrist/Ring PR。它会用默认分支上的可信策略再次读取 PR 文件列表，避免 PR 通过修改自己的 workflow 绕过目录检查。

## 给开发 AI 的第一条指令

先确认当前分支和目标组件。Wrist 工作创建 `codex/wrist-<任务>`，Ring 工作创建 `codex/ring-<任务>`。只修改对应目录，运行组件测试，提交并推送 PR；不要在一个 PR 中同时处理两个设备。
