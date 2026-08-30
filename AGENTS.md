# HarBeat Wear repository rules

- Wrist AI uses a `codex/wrist-<task>` branch and edits only `wrist/**`.
- Ring AI uses a `codex/ring-<task>` branch and edits only `ring/**`.
- Never mix Wrist and Ring changes in one pull request.
- Shared contracts, workflows, tools, and repository documentation use `codex/shared-<task>` and require manual merge.
- Hub Gateway work uses `codex/gateway-<task>` and does not count as Wrist or Ring firmware.
- Run the component tests named in `docs/REPOSITORY-WORKFLOW.md` before pushing.
