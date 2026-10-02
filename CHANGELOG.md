# Changelog

## 1.0.3

- Added bounded Git subprocess execution and explicit Git history error propagation.
- Added bundled schema validation for `repo-xray validate`, including required fields, enums, constants, nested claims, and numeric bounds.
- Preserved GitHub collection errors in the evidence search scope and claim notes instead of treating failed lookups as empty evidence.
- Deduplicated mutation history searches and preserved Git history errors in mutation output.

- Hardened GitHub adapter error handling, command timeouts, remote parsing, and offline fixture reporting.
- Added explicit mutation match kinds and confidence: `direct_value` vs `semantic_anchor`.
- Improved numeric literal matching for separators such as `500_000` and source duration encodings such as `time.Duration(60)`.
- Prevented unrelated identifiers such as `MinRequestTimeout` from becoming numeric contradictions for `RequestTimeout`.
- Added GitHub adapter failure-mode regression tests.
- Added five-project cross-stack public-source smoke benchmark with pinned blob provenance.
- Updated package/runtime version to 1.0.3.


## 1.0.2

- Fixed normalized requirement/value comparison for two-letter units and source-code constants.
- Added precision and rate-scope mutation parsing.
- Improved mutation relevance filtering and risk classification.
- Added deterministic GitHub fixture fallback for offline benchmark runs.
- Added package discovery and runtime asset packaging for wheel installs.
- Added regression coverage for adversarial contradiction and mutation cases.

## 1.0.1

- Improve semantic risk ranking for cross-component timeout contradictions.
- Treat rate-limit scope/capacity contradictions as HIGH impact.
- Treat monetary/currency precision contradictions as HIGH impact.
- Add regression tests for the three risk categories and a low-impact control case.
