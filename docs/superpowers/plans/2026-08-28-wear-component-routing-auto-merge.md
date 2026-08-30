# Wear Component Routing and Auto-Merge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `harbeat-wear` 固定为 Wrist、Ring 和共享区三个边界，并让内部 Wrist/Ring PR 在只修改对应目录且全部门禁通过后自动 squash merge 到 `main`。

**Architecture:** Python 策略模块是分支命名、允许路径和必需检查的唯一事实来源。Pull Request workflow 调用它阻止越界改动；`workflow_run` 在默认分支的可信代码中读取 GitHub 元数据，确认内部 PR、组件检查和合并状态后调用 GitHub API。Bootstrap、shared 和 gateway 变更永不自动合并。

**Tech Stack:** Git、GitHub Actions、Python 3.12、pytest、GitHub REST API、Markdown

---

### Task 1: 建立组件策略的测试

**Files:**
- Create: `tests/test_wear_repo_policy.py`
- Create: `tools/wear_repo_policy.py`

- [ ] **Step 1: 写分支分类和目录边界失败测试**

测试必须覆盖：

```python
from tools.wear_repo_policy import classify_branch, validate_paths


def test_wrist_branch_accepts_only_wrist_tree():
    assert classify_branch("codex/wrist-power-fix") == "wrist"
    assert validate_paths("wrist", ["wrist/flow-wrist/main/app_main.c"]) == []
    assert validate_paths("wrist", ["ring/flow-ring/src/main.c"])


def test_ring_branch_accepts_only_ring_tree():
    assert classify_branch("codex/ring-gesture-v1") == "ring"
    assert validate_paths("ring", ["ring/flow-ring/docs/design.md"]) == []
    assert validate_paths("ring", ["wrist/flow-wrist/main/app_main.c"])


def test_shared_and_gateway_never_become_component_branches():
    assert classify_branch("codex/shared-contract-v2") == "shared"
    assert classify_branch("codex/gateway-bluez-reconnect") == "gateway"
    assert classify_branch("codex/bootstrap-wear-layout") == "bootstrap"
```

- [ ] **Step 2: 运行测试并确认失败**

Run:

```bash
python -m pytest tests/test_wear_repo_policy.py -q
```

Expected: FAIL，原因是 `tools.wear_repo_policy` 尚不存在。

- [ ] **Step 3: 实现最小策略模块和 CLI**

策略固定为：

```text
codex/wrist-*、wrist/*       → wrist，只允许 wrist/**
codex/ring-*、ring/*         → ring，只允许 ring/**
codex/shared-*、shared/*     → shared，只允许共享路径
codex/gateway-*、gateway/*   → gateway，只允许 hub-gateway/**
codex/bootstrap-*            → bootstrap，一次性人工合并
```

CLI：

```bash
python tools/wear_repo_policy.py validate \
  --branch codex/ring-gesture-v1 \
  --files-from changed-files.txt
```

非法分支或越界文件返回非零退出码，并逐行打印违规路径。

- [ ] **Step 4: 运行测试并确认通过**

Run:

```bash
python -m pytest tests/test_wear_repo_policy.py -q
```

Expected: PASS。

- [ ] **Step 5: 提交策略模块**

```bash
git add tests/test_wear_repo_policy.py tools/wear_repo_policy.py
git commit -m "ci: enforce wear component path boundaries"
```

### Task 2: 实现可测试的自动合并判定

**Files:**
- Create: `tests/test_auto_merge_component_pr.py`
- Create: `tools/auto_merge_component_pr.py`

- [ ] **Step 1: 写自动合并判定失败测试**

覆盖以下规则：

```python
def test_ring_requires_boundary_contracts_and_ring_ci():
    decision = evaluate_merge(
        branch="codex/ring-gesture-v1",
        base="main",
        draft=False,
        internal=True,
        mergeable=True,
        checks={
            "component-boundary": "success",
            "contracts": "success",
            "ring-ci": "success",
        },
    )
    assert decision.merge is True


def test_failed_check_blocks_merge():
    decision = evaluate_merge(
        branch="codex/wrist-power-fix",
        base="main",
        draft=False,
        internal=True,
        mergeable=True,
        checks={
            "component-boundary": "success",
            "contracts": "success",
            "wrist-host": "failure",
        },
    )
    assert decision.merge is False


def test_shared_bootstrap_draft_fork_and_conflict_never_merge():
    for branch in ("codex/shared-contract-v2", "codex/bootstrap-wear-layout"):
        assert evaluate_merge(branch, "main", False, True, True, {}).merge is False
```

- [ ] **Step 2: 运行测试并确认失败**

Run:

```bash
python -m pytest tests/test_auto_merge_component_pr.py -q
```

Expected: FAIL，原因是模块尚不存在。

- [ ] **Step 3: 实现判定和 GitHub REST 客户端**

`main()` 只处理 `workflow_run` 事件，并执行：

1. 工作流结论必须为 `success`。
2. 事件必须关联一个 PR。
3. PR 必须来自 `jihaobi123/harbeat-wear` 内部分支，目标为 `main`，且不是 draft。
4. `wrist` 要求 `component-boundary`、`contracts`、`wrist-host`。
5. `ring` 要求 `component-boundary`、`contracts`、`ring-ci`。
6. shared、gateway、bootstrap 和未知分支退出但不合并。
7. 检查缺失、运行中、失败或 PR 冲突时不合并。
8. 条件全部满足后，以 PR head SHA 调用 squash merge API。

- [ ] **Step 4: 运行测试并确认通过**

Run:

```bash
python -m pytest tests/test_auto_merge_component_pr.py -q
```

Expected: PASS。

- [ ] **Step 5: 提交自动合并模块**

```bash
git add tests/test_auto_merge_component_pr.py tools/auto_merge_component_pr.py
git commit -m "ci: add guarded component PR auto-merge"
```

### Task 3: 接入 GitHub Actions

**Files:**
- Create: `.github/workflows/component-boundary.yml`
- Create: `.github/workflows/ring-ci.yml`
- Create: `.github/workflows/component-auto-merge.yml`
- Modify: `.github/workflows/contracts.yml`
- Modify: `.github/workflows/wrist-host.yml`
- Create: `tests/test_workflow_contract.py`

- [ ] **Step 1: 写 workflow 合同失败测试**

测试读取 workflow 文本并断言：

- 四个稳定检查名存在：`component-boundary`、`contracts`、`wrist-host`、`ring-ci`。
- 自动合并 workflow 使用 `workflow_run`，不使用 `pull_request_target`。
- 自动合并 workflow 不 checkout PR head。
- 自动合并 job 具有 `contents: write` 和 `pull-requests: write`。
- Ring CI 在出现 `ring/flow-ring/CMakeLists.txt` 后强制要求 host test runner。

- [ ] **Step 2: 运行测试并确认失败**

Run:

```bash
python -m pytest tests/test_workflow_contract.py -q
```

Expected: FAIL，原因是 workflow 尚不存在或稳定检查名不匹配。

- [ ] **Step 3: 创建 component boundary workflow**

该 workflow checkout 完整历史，计算 base 到 head 的变更文件，并调用：

```bash
python tools/wear_repo_policy.py validate \
  --branch "$GITHUB_HEAD_REF" \
  --files-from changed-files.txt
```

- [ ] **Step 4: 创建 Ring CI**

Ring 文档阶段运行链接和目录检查。只要出现固件 `CMakeLists.txt`，就必须存在并运行：

```text
ring/flow-ring/tests/host/run.sh
```

- [ ] **Step 5: 创建可信 workflow_run 自动合并**

默认分支代码调用：

```bash
python tools/auto_merge_component_pr.py
```

它只读取 PR 元数据和检查结果，不 checkout 或执行 PR 中的代码。

- [ ] **Step 6: 运行 workflow 合同和全套 Python 测试**

Run:

```bash
python -m pytest tests -q
```

Expected: PASS。

- [ ] **Step 7: 提交 workflow**

```bash
git add .github/workflows tests/test_workflow_contract.py
git commit -m "ci: route and merge wrist and ring pull requests"
```

### Task 4: 写清开发者和 AI 的目录规则

**Files:**
- Create: `AGENTS.md`
- Create: `wrist/AGENTS.md`
- Create: `ring/AGENTS.md`
- Create: `.github/CODEOWNERS`
- Create: `.github/pull_request_template.md`
- Create: `docs/REPOSITORY-WORKFLOW.md`
- Modify: `README.md`

- [ ] **Step 1: 写根目录规则**

根规则必须说明：

- Wrist AI 使用 `codex/wrist-<task>`，只修改 `wrist/**`。
- Ring AI 使用 `codex/ring-<task>`，只修改 `ring/**`。
- Contracts、CI 和仓库文档使用 `codex/shared-<task>`，需要人工合并。
- Hub Gateway 使用 `codex/gateway-<task>`，不冒充 Wrist/Ring 固件 PR。
- 不允许在一个 PR 中混合 Wrist 和 Ring。

- [ ] **Step 2: 添加 CODEOWNERS 和 PR 模板**

`@jihaobi123` 负责 Wrist、Ring、contracts 和 workflows。PR 模板要求选择组件、给出测试证据并确认没有越界文件。

- [ ] **Step 3: 更新 README 和工作流说明**

README 把 Ring 状态改为“V0.1 设计已批准”，并链接到 Ring 目录。工作流文档写清哪些 PR 自动合并，哪些必须人工审阅。

- [ ] **Step 4: 运行链接和全套测试**

Run:

```bash
python tools/check_markdown_links.py
python -m pytest tests -q
```

Expected: `Markdown links: OK` 且全部测试通过。

- [ ] **Step 5: 提交仓库规则**

```bash
git add AGENTS.md wrist/AGENTS.md ring/AGENTS.md .github/CODEOWNERS .github/pull_request_template.md README.md docs/REPOSITORY-WORKFLOW.md
git commit -m "docs: define wrist and ring contribution boundaries"
```

### Task 5: 把 Ring V0.1 设计迁入 Ring 目录

**Files:**
- Modify: `ring/README.md`
- Create: `ring/flow-ring/README.md`
- Create: `ring/flow-ring/docs/2026-08-28-flow-ring-xiao-nrf54l15-v0.1-design.md`

- [ ] **Step 1: 迁移已批准设计**

从 `harbeat-client` 提交 `d5a8697` 读取规格内容，放入 Ring 的唯一目录。把默认源码路径从 `firmware/flow-ring` 改为 `ring/flow-ring`，把外部 App/RK 文件明确标成 `harbeat-client` 集成点。

- [ ] **Step 2: 更新 Ring 入口文档**

`ring/README.md` 只负责组件导航；`ring/flow-ring/README.md` 写开发板、SDK、board target、当前无马达/触摸模块和设计文档入口。

- [ ] **Step 3: 运行占位符、链接和路径检查**

Run:

```bash
rg -n -i 'T[B]D|TO[D]O|FIX[M]E|firmware/flow-ring' ring
python tools/check_markdown_links.py
```

Expected: `rg` 无输出；链接检查通过。

- [ ] **Step 4: 提交 Ring 文档**

```bash
git add ring
git commit -m "docs: add Flow Ring nRF54L15 V0.1 design"
```

### Task 6: 验证、推送和首次启用

**Files:**
- No new files

- [ ] **Step 1: 运行完整门禁**

```bash
python tools/check_markdown_links.py
python tools/validate_contracts.py
python -m pytest tests wrist/flow-wrist/tests/host/test_contract_vectors.py -q
cd wrist/flow-wrist
CC=cc ./tests/host/run.sh
python tests/host/test_hub_mock.py
python tests/host/test_dancer_assets.py
```

Expected: 全部通过。

- [ ] **Step 2: 确认提交不包含另一个工作区的未提交内容**

```bash
git status --short
git diff origin/codex/wrist-field-ready-v0.1...HEAD --stat
```

Expected: 工作区干净；变更只有仓库路由、自动化和 Ring 文档。

- [ ] **Step 3: 推送 bootstrap 分支**

```bash
git push -u origin codex/bootstrap-wear-layout
```

- [ ] **Step 4: 创建首次 PR**

PR：

```text
base: main
head: codex/bootstrap-wear-layout
title: chore: split Wrist and Ring firmware workflows
```

Bootstrap PR 必须人工确认一次，因为自动合并器尚未存在于 `main`。合并后，`codex/wrist-*` 和 `codex/ring-*` PR 才自动执行安全合并。

- [ ] **Step 5: 配置 main 规则**

在 GitHub Rulesets 中禁止直接 push 到 `main`，要求通过 PR。自动合并机器人仍按 workflow 的检查结果执行 squash merge；shared、gateway 和 bootstrap PR 保持人工合并。
