# Repo X-Ray Agent Protocol

Repo X-Ray is model-agnostic at the protocol level. A host agent may be Claude Code, Codex, Gemini CLI, Cursor, VS Code, or a standalone orchestrator.

## Contract

The host MUST:

1. establish repository root and explicit search scope;
2. run deterministic discovery before semantic reasoning;
3. preserve source provenance and exact anchors;
4. classify claims only as `VERIFIED`, `CONTRADICTED`, `UNVERIFIED`, or `UNCHECKABLE`;
5. include search scope with every `UNVERIFIED` result;
6. distinguish discussion from implementation evidence;
7. never mutate files unless the caller explicitly asks for changes;
8. return the evidence ledger as the primary machine-readable artifact.

## Adapter boundary

The Python engine provides discovery, provenance, planning, risk, mutation candidates, and CI policy. The host agent may provide semantic claim extraction and relationship reasoning, but it must ground those conclusions in ledger evidence.

## Recommended loop

```text
request
  -> plan
  -> deterministic discovery
  -> ledger
  -> targeted reasoning
  -> validation
  -> final ledger/report
```
