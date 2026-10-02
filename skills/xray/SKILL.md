---
name: repo-xray
description: Evidence-grounded repository X-Ray and requirement mutation. Use when the user asks to verify repository claims, find contradictions, inspect implementation evidence, trace requirement changes, or reconcile code with Git/GitHub history.
---

# Repo X-Ray

Treat the repository as an evidence system. Do not substitute plausible architecture for collected evidence.

## Modes

- `/xray scan` — discover repository evidence and produce a ledger.
- `/xray claim "..."` — verify one explicit claim.
- `/xray change "..."` — analyze a proposed requirement change.
- `/xray mutate` — trace a grounded requirement mutation.
- `repo-xray validate <ledger.json>` — validate a produced evidence ledger against the bundled schema.
- `repo-xray ci` — fail CI only for new high-risk contradictions.

## Execution contract

1. **Plan before expensive work.** Determine file count, search scope, expected Git/GitHub lookups, and reasoning work. Show a rough token range for expensive runs. Ask once before a high-cost run. Never silently fan out agents.
2. **Deterministic first.** Search files, tests, configuration, Git metadata, and available GitHub records before model reasoning.
3. **Bound every negative claim.** Every `UNVERIFIED` result must carry exact paths, patterns, Git range, and GitHub scope. If Git or GitHub collection fails, preserve the failure in provenance and notes; never interpret a failed lookup as absence of evidence. Never claim repository-wide absence from a bounded search.
4. **Classify exactly one way:** `VERIFIED`, `CONTRADICTED`, `UNVERIFIED`, `UNCHECKABLE`.
5. **Separate provenance from truth.** A GitHub issue, PR, review, or document is evidence of a statement being made; it is not automatically authoritative.
6. **Detect contradictions explicitly.** A contradiction requires incompatible evidence or opposing polarity after accounting for scope/time. Record both sides.
7. **Anchor evidence.** Prefer file+line, commit SHA, issue/PR number, review/comment identifiers, and URLs.
8. **Risk is separate.** Rank `LOW`, `MEDIUM`, `HIGH`, or `CRITICAL`; explain the concrete factors.
9. **Mutation is grounded.** Trace actual encodings: constants, environment variables, configuration, validation, clients, schemas, tests, and historical changes. Candidate matches are not automatically confirmed dependencies.
10. **Validate before reporting.** Re-check model interpretations against the collected evidence. Do not invent runtime behavior that was not observed.

## Evidence precedence

Do not use a rigid truth hierarchy. Instead preserve provenance and currentness:

- current executable code/config/tests = implementation evidence
- merged commits = historical implementation evidence
- documentation = declared behavior
- open PR/issue/review = engineering discussion
- external/runtime claims = uncheckable unless reproducible

If sources disagree, report the disagreement and why it matters.

## GitHub behavior

Use GitHub only when credentials/access are available and scope it explicitly. Search issues and PRs using requirement terms. For important findings, fetch the full issue/PR details and reviews rather than relying only on list summaries. Never infer that an open issue describes current behavior.

## Cost control

Prefer one deterministic scan over many agents. Escalate only ambiguous or high-risk claims. If the estimated reasoning work is large, show:

- files in scope
- claims/evidence items
- Git/GitHub lookups
- expected reasoning calls
- token range
- cheaper alternatives

## Mutation protocol

For `10 MB -> 50 MB`:

1. Parse old/new values and units.
2. Search semantic names plus both numeric/unit encodings.
3. Inspect configuration, code, tests, schemas, clients, and docs.
4. Inspect Git history for the relevant symbols/values.
5. Search GitHub issues/PRs if enabled.
6. Emit concrete candidate impact locations.
7. Only mark a dependency confirmed when evidence establishes the relationship.
8. Do not modify files automatically.

## CI policy

CI should fail only for **new** `HIGH` or `CRITICAL` contradictions unless the caller explicitly configures a stricter policy. Existing findings should be baselined.

## Output contract

The primary machine-readable artifact is an evidence ledger:

```json
{
  "schema_version": "1.0",
  "root": "...",
  "claims": [
    {
      "claim_id": "C-...",
      "claim": "...",
      "classification": "VERIFIED|CONTRADICTED|UNVERIFIED|UNCHECKABLE",
      "evidence": [],
      "search_scope": {
        "paths": [],
        "patterns": [],
        "git_range": null,
        "github_scope": []
      },
      "risk": "LOW|MEDIUM|HIGH|CRITICAL",
      "confidence": 0.0,
      "notes": []
    }
  ]
}
```
