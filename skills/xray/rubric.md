# Evidence rubric

## Classification
- VERIFIED: current evidence directly supports the claim.
- CONTRADICTED: credible evidence directly conflicts with the claim.
- UNVERIFIED: the claim could be checked, but the bounded search found insufficient evidence.
- UNCHECKABLE: verification requires unavailable runtime, external, private, or non-reproducible facts.

## Risk
- LOW: local/non-production impact and little blast radius.
- MEDIUM: meaningful behavior or test impact.
- HIGH: production, security, data integrity, or broad dependency impact.
- CRITICAL: severe security/data-loss/system-wide impact with strong evidence.

Never convert absence inside a bounded scope into proof of non-existence.
