# Repo X-Ray v1.0.3

**Evidence-grounded repository analysis and requirement mutation for Claude Code and other agent/IDE environments.**

Repo X-Ray is designed for a specific problem: repositories contain several competing sources of truth—code, configuration, tests, documentation, Git history, and engineering discussions—and an agent can easily mistake a plausible explanation for evidence.

Repo X-Ray turns repository analysis into an explicit evidence workflow:

```text
Requirement / Claim
        │
        ▼
  Scope + Plan
        │
        ▼
Deterministic discovery
(code/config/tests/docs/Git/GitHub)
        │
        ▼
Evidence ledger
        │
        ▼
Targeted reasoning
        │
        ▼
Deterministic validation
        │
        ▼
VERIFIED / CONTRADICTED / UNVERIFIED / UNCHECKABLE
```

It is inspired by the structural discipline of agent skills such as Arena, but deliberately avoids blind multi-agent fan-out. The default strategy is **deterministic first, targeted reasoning second, adaptive escalation only when needed**.

---

## What Repo X-Ray does

Repo X-Ray answers questions such as:

- **Does the repository actually support this claim?**
- **Where is the evidence?**
- **Do code, configuration, tests, docs, and history disagree?**
- **What evidence was searched before something was marked unverified?**
- **Is the finding operationally or security relevant?**
- **What concrete locations could be affected if a requirement changes?**
- **What does Git history say about the current or previous behavior?**
- **What do GitHub issues and PRs discuss about the requirement?**

It is intentionally an **evidence system**, not an architecture guessing engine.

---

## Claude Skill vs Python engine

This distinction is important.

### 1. Claude Skill

The Claude-facing part lives under:

```text
skills/xray/SKILL.md
```

This file teaches Claude how to use Repo X-Ray: when to invoke it, how to reason over evidence, how to handle uncertainty, how to avoid unsupported negative claims, how to interpret Git/GitHub evidence, and how to present mutation results.

The Claude Skill is therefore the **agent interface and reasoning protocol**.

### 2. Python engine

The deterministic implementation lives alongside the skill:

```text
skills/xray/
├── xray.py
├── evidence.py
├── mutate.py
├── git.py
├── github.py
├── planner.py
├── budget.py
├── risk.py
├── scope.py
├── validation.py
├── requirements.py
├── ci.py
└── schemas/
```

This code performs deterministic repository operations such as file discovery, pattern matching, evidence construction, Git inspection, GitHub collection, mutation candidate discovery, risk calculation, planning, and schema validation.

### 3. Python wheel

### Prebuilt wheel

A prebuilt wheel is included in `dist/`:

```bash
pip install dist/repo_xray-1.0.3-py3-none-any.whl

The wheel is **not required because Claude Skills require Python wheels**. They do not.

The wheel is an optional distribution of the Python engine and CLI:

```bash
pip install repo-xray
repo-xray --help
```

It provides normal Python-package benefits such as versioning, a stable CLI entry point, clean installation, and independent testing of the deterministic engine.

So the architecture is:

```text
                  Repo X-Ray
                      │
          ┌───────────┴───────────┐
          │                       │
    Claude Skill             Python engine
    SKILL.md                 deterministic code
          │                       │
          │                 repo-xray CLI
          │                       │
          └──────────┬────────────┘
                     │
                Repository
```

For a Claude Code user, the **skill/plugin is the important installation artifact**. The wheel is useful when the Python engine is also wanted as a standalone CLI/library.

---

## Claude Code installation

Install the repository/plugin using the normal Claude Code skill/plugin workflow for your environment.

The important files are:

```text
.claude-plugin/
├── plugin.json
└── marketplace.json

skills/xray/
└── SKILL.md
```

Once the skill is available to Claude Code, use the X-Ray workflow described in `skills/xray/SKILL.md`.

The Python implementation is shipped with the repository so the skill can invoke deterministic tooling from the same source tree.

---

## Standalone Python installation

If you want to use the deterministic engine without Claude Code, install the package:

```bash
python -m pip install repo-xray
```

For development from a checkout:

```bash
python -m pip install -e .
```

Or without installing:

```bash
PYTHONPATH=. python -m skills.xray.cli --help
```

The wheel is therefore an **optional standalone-engine distribution**, not a prerequisite for the Claude Skill itself.

---

## Core commands

### Plan

Inspect expected work before execution:

```bash
repo-xray plan .
```

The planner estimates repository scope, claims/evidence work, Git/GitHub lookups, reasoning calls, operations, and a broad token range.

### Scan

Discover evidence across the repository:

```bash
repo-xray scan . \
  --pattern timeout \
  --pattern MAX_TIMEOUT \
  --out .xray/scan.json
```

### Verify a claim

```bash
repo-xray claim . \
  "API timeout is 60 seconds" \
  --pattern timeout \
  --pattern 60 \
  --pattern 30 \
  --out .xray/claim.json
```

### Analyze a requirement change

```bash
repo-xray mutate . \
  "10 MB -> 50 MB" \
  --out .xray/mutation.json
```

### Validate an evidence ledger

```bash
repo-xray validate .xray/claim.json
```

Validation uses the bundled JSON schemas rather than only checking a few fields.

### CI regression policy

```bash
repo-xray ci \
  .xray/current.json \
  --baseline .xray/baseline.json
```

By default CI fails only when **new HIGH or CRITICAL contradictions** appear.

Repo X-Ray does not modify repository files during these operations.

---

# How the analysis works

## 1. Scope first

Repo X-Ray records what it is actually searching.

A scope can include:

- source files
- configuration
- tests
- documentation
- generated metadata
- Git history
- GitHub issues/PRs/reviews/comments when available

The system avoids turning a bounded search into a repository-wide claim.

For example:

> No matching evidence found within the searched `orders/` paths and configured patterns.

is valid.

> The repository contains no implementation of this feature.

is not valid unless the search actually establishes repository-wide coverage.

---

## 2. Deterministic discovery first

The engine first collects concrete evidence:

```text
files
  ↓
patterns / identifiers / values
  ↓
code + config + tests + docs
  ↓
Git history
  ↓
GitHub discussion when enabled
```

Only after evidence exists should model reasoning interpret ambiguous relationships.

This prevents an agent from inventing a plausible implementation path and presenting it as repository evidence.

---

## 3. Evidence ledger

The primary machine-readable artifact is an evidence ledger.

A claim contains:

- claim text
- classification
- evidence
- provenance
- search scope
- risk
- confidence
- notes
- relationships where applicable

Example shape:

```json
{
  "schema_version": "1.0",
  "root": ".",
  "claims": [
    {
      "claim_id": "C-001",
      "claim": "API timeout is 60 seconds",
      "classification": "CONTRADICTED",
      "evidence": [],
      "search_scope": {
        "paths": ["src/", "tests/", "docs/"],
        "patterns": ["timeout", "60", "30"],
        "git_range": null,
        "github_scope": []
      },
      "risk": "HIGH",
      "confidence": 0.95,
      "notes": []
    }
  ]
}
```

The ledger is deliberately machine-readable so another agent, CI job, IDE integration, or later X-Ray run can consume the result without reparsing prose.

---

# Classifications

Repo X-Ray uses exactly four classifications:

| Classification | Meaning |
|---|---|
| `VERIFIED` | Collected evidence supports the claim within the recorded scope. |
| `CONTRADICTED` | Collected evidence contains incompatible behavior, values, scope, or semantics. |
| `UNVERIFIED` | The claim was not established within the recorded search scope. |
| `UNCHECKABLE` | Verification requires unavailable runtime, external, private, or operational evidence. |

There is deliberately no `ASSUMED` classification.

### UNVERIFIED is not “does not exist”

Every `UNVERIFIED` result must preserve:

- paths searched
- patterns searched
- Git range searched
- GitHub scope searched
- collection failures, if any

A failed GitHub request, for example, must never silently become:

> No GitHub evidence exists.

Instead the failure remains part of the provenance.

---

# Contradiction detection

Contradiction detection is the main differentiator of Repo X-Ray.

It compares multiple repository evidence sources rather than treating documentation or code as universally authoritative.

Typical conflicts include:

```text
Documentation        says 25 MB
Runtime constant     says 10 MB
Tests                enforce 10 MB
Git history          shows a reverted 25 MB change
```

Repo X-Ray reports the disagreement and preserves both sides.

Other supported semantic contradiction patterns include:

- optional vs required
- atomic vs separate operations
- redaction before persistence vs persistence before redaction
- universally enforced vs bypassed
- customer-level vs instance-level limits
- numeric/value mismatches
- differently scoped configuration values

The system does **not** use a rigid rule that one evidence source is always correct. Current executable behavior, tests, configuration, documentation, historical changes, and engineering discussion are preserved as separate provenance.

---

# Evidence provenance

Evidence should be anchored whenever possible.

### Repository

```text
path/to/file.py:123
```

### Git

```text
commit SHA
```

### GitHub

```text
issue #123
PR #456
review/comment reference
```

### Important GitHub rule

An issue or PR proves that someone discussed or claimed something. It does **not** automatically prove that the claim is true or that it describes the current implementation.

For important findings, Repo X-Ray can hydrate PR/issue details and inspect relevant reviews, comments, changed files, and commits when access is available.

---

# Git and GitHub integration

## Git

Git history is read through the local `git` executable.

Repo X-Ray uses history to answer questions such as:

- When did this value change?
- Was the change reverted?
- Did documentation and implementation diverge over time?
- Was a requirement previously discussed or implemented?

Git operations are bounded by subprocess timeouts. Git failures are preserved as failures rather than interpreted as absence of history.

## GitHub

GitHub enrichment uses the `gh` CLI when available and scopes requests to the repository's `origin` remote.

The adapter can collect:

- issues
- pull requests
- PR details
- reviews
- comments
- changed files
- commits

Collection failures are surfaced as adapter errors.

For deterministic offline benchmark execution, an explicit local fixture such as `github-fixtures.json` may be used. Fixture-derived evidence is labeled as fixture evidence and is never silently treated as live GitHub data.

---

# Requirement mutation

Mutation is **read-only**.

Suppose a requirement changes:

```text
10 MB -> 50 MB
```

Repo X-Ray does not blindly replace `10` with `50`.

It traces the requirement through:

```text
requirement
   │
   ├── semantic identifiers
   ├── numeric encodings
   ├── configuration
   ├── environment variables
   ├── validation
   ├── application code
   ├── tests
   ├── schemas
   ├── clients
   ├── deployment configuration
   ├── documentation
   ├── Git history
   └── GitHub discussion
```

Each candidate is labeled:

### `direct_value`

The requested value or a concrete encoding of it is actually present.

Example:

```python
MAX_BODY_BYTES = 10 * 1024 * 1024
```

### `semantic_anchor`

The location is strongly related to the requirement, but the exact control point is not proven.

For example, a request-size validation function may be relevant even if the exact limit comes from configuration elsewhere.

**Semantic anchors are candidates, not automatically confirmed dependencies.**

This distinction prevents the mutation engine from overstating what static evidence proves.

---

# Risk model

Risk is independent from classification.

A finding can be `VERIFIED` and still be HIGH risk.

Risk levels:

- `LOW`
- `MEDIUM`
- `HIGH`
- `CRITICAL`

Risk considers factors such as:

- severity
- blast radius
- production relevance
- security implications
- configuration impact
- test coverage
- confidence
- dependency surface
- semantic scope changes

A simple numeric difference is therefore not sufficient to determine risk.

---

# Cost control

Repo X-Ray was deliberately designed to avoid the failure mode of blindly launching large numbers of agents.

The execution planner estimates:

- files in scope
- evidence items
- claims
- Git lookups
- GitHub lookups
- expected operations
- reasoning calls
- broad token range

For expensive work, the caller can inspect the plan before execution.

The design is:

```text
cheap deterministic discovery
          ↓
identify ambiguity
          ↓
escalate selectively
          ↓
reason over collected evidence
          ↓
deterministically validate
```

This is intentionally different from an agent fan-out strategy where dozens of independent agents are launched regardless of ambiguity.

---

# CI integration

Repo X-Ray can be used as a repository governance check.

The default policy is:

```text
baseline contradictions
        ↓
        ignored

new HIGH/CRITICAL contradictions
        ↓
        CI failure
```

This means a repository can establish a known baseline and prevent newly introduced contradictions without requiring every historical issue to be fixed before CI becomes useful.

---

# Agent / IDE integration

The core protocol is model-agnostic.

Current documentation includes:

```text
adapters/generic-agent.md
docs/protocol.md
skills/xray/SKILL.md
```

`SKILL.md` is the Claude Code adapter. The underlying evidence ledger and deterministic engine are not conceptually tied to Claude.

The same protocol can therefore be adapted to other agent environments without changing the evidence model.

---

# Repository structure

```text
repo-xray/
│
├── .claude-plugin/
│   ├── plugin.json
│   └── marketplace.json
│
├── skills/
│   └── xray/
│       ├── SKILL.md
│       ├── xray.py
│       ├── mutate.py
│       ├── evidence.py
│       ├── scope.py
│       ├── risk.py
│       ├── git.py
│       ├── github.py
│       ├── budget.py
│       ├── planner.py
│       ├── validation.py
│       ├── requirements.py
│       ├── ci.py
│       ├── mutations.json
│       ├── rubric.md
│       └── schemas/
│           ├── evidence-ledger.json
│           ├── claim.json
│           ├── git-evidence.json
│           ├── github-evidence.json
│           ├── mutation-result.json
│           └── execution-plan.json
│
├── adapters/
├── docs/
├── examples/
├── benchmarks/
├── tests/
├── README.md
├── CHANGELOG.md
├── LICENSE
└── pyproject.toml
```

---

# Testing and evaluation

Run the complete test suite with:

```bash
pytest -q
```

The suite covers:

- verified claims
- contradiction detection
- bounded `UNVERIFIED` behavior
- `UNCHECKABLE` runtime claims
- evidence validation
- scope handling
- risk classification
- requirement parsing
- mutation tracing
- Git history
- Git subprocess failure modes
- GitHub adapter behavior and failures
- planning and cost estimation
- CI baseline policy
- schema validation
- packaging behavior

The repository also contains a cross-stack public-source smoke benchmark covering:

- Flask
- FastAPI
- Django
- Kubernetes
- Go

The benchmark is intended as a generalization smoke test, not as a claim that five repositories represent the entire software ecosystem.

---

# Examples

See:

```text
examples/xray-scan.md
examples/contradiction.md
examples/historical-conflict.md
examples/requirement-mutation.md
examples/cost-control.md
```

These show the expected evidence workflow and output style.

---

# Design principles

Repo X-Ray follows a few non-negotiable principles:

1. **Evidence before explanation.**
2. **Bound every negative claim.**
3. **Never silently turn collection failure into absence.**
4. **Keep provenance attached to evidence.**
5. **Do not treat discussion as truth.**
6. **Separate classification from risk.**
7. **Separate confirmed dependencies from semantic candidates.**
8. **Prefer deterministic discovery over unnecessary agent fan-out.**
9. **Validate model interpretations against collected evidence.**
10. **Mutation analysis is read-only unless a separate caller explicitly performs changes.**

---

# License

MIT. See `LICENSE`.
