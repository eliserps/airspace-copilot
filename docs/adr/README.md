# Architecture decisions

Short records of decisions that shape the code, in the format *context → decision → consequences*. A new decision gets a new file; an old one is marked superseded instead of edited.

| # | Decision | Status |
|---|---|---|
| [0001](0001-domain-modules.md) | Backend organised by domain, wired through a container | Accepted |
| [0002](0002-async-and-injected-clients.md) | Async I/O with injected clients | Accepted, ChromaDB part superseded by 0008 |
| [0003](0003-openapi-contract.md) | OpenAPI is the contract between backend and frontend | Accepted |
| [0004](0004-spa.md) | Frontend is a static SPA, not SSR | Accepted |
| [0005](0005-streaming-answers.md) | Copilot answers stream over Server-Sent Events | Accepted |
| [0006](0006-stale-traffic.md) | Serve stale traffic while OpenSky is failing | Accepted, amended by 0009 |
| [0007](0007-guardrails.md) | Guardrails flag injection; tool design contains it | Accepted |
| [0008](0008-reference-in-prompt.md) | Send the whole METAR reference instead of retrieving chunks | Accepted |
| [0009](0009-single-world-fetch.md) | Fetch the whole world once and filter regions locally | Accepted |
| [0010](0010-client-sent-history.md) | The client sends the conversation history | Accepted |
