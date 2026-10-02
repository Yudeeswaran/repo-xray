# Generic Agent Adapter

Use the Repo X-Ray protocol from `docs/protocol.md`.

The adapter should invoke:

```bash
repo-xray plan <repo>
repo-xray claim <repo> "<claim>" --pattern <term> --out .xray/claim.json
repo-xray mutate <repo> "<old> -> <new>" --out .xray/mutation.json
repo-xray ci .xray/ledger.json --baseline .xray/baseline.json
```

Do not invent search results. Use the generated evidence as the factual substrate for reasoning.
