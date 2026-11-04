# Architecture decisions

Short records of decisions that shape the code, in the format *context → decision → consequences*. A new decision gets a new file; an old one is marked superseded instead of edited.

| # | Decision | Status |
|---|---|---|
| [0001](0001-domain-modules.md) | Backend organised by domain, wired through a container | Accepted |
| [0002](0002-async-and-injected-clients.md) | Async I/O with injected clients | Accepted |
| [0003](0003-openapi-contract.md) | OpenAPI is the contract between backend and frontend | Accepted |
| [0004](0004-spa.md) | Frontend is a static SPA, not SSR | Accepted |
| [0005](0005-streaming-answers.md) | Copilot answers stream over Server-Sent Events | Accepted |
| [0006](0006-stale-traffic.md) | Serve stale traffic while OpenSky is failing | Accepted |
| [0007](0007-guardrails.md) | Guardrails flag injection; tool design contains it | Accepted |
