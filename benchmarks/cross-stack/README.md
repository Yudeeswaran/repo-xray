# Cross-stack public-source benchmark

This is a **small generalization/smoke corpus**, not a substitute for cloning and replaying complete repositories.

It contains narrow source snapshots from five public projects fetched from GitHub and pinned by blob SHA:

- Flask
- FastAPI
- Django
- Kubernetes
- Go

The benchmark tests two things:

1. claim verification across Python, Go, and infrastructure-oriented code;
2. requirement mutation tracing, including numeric literals encoded with separators and `time.Duration(...)` style source.

The source snapshots are intentionally small so the benchmark is deterministic and distributable. Full-repository evaluation remains a separate production validation step.
