# 0008. Send the whole METAR reference instead of retrieving chunks

**Status:** Accepted. Supersedes the ChromaDB part of [0002](0002-async-and-injected-clients.md).

## Context

The METAR decoder used RAG: `knowledge/` was chunked by section, embedded into ChromaDB and the top 8 chunks went into the prompt. The reference is one file of about 360 words split into 10 sections, so retrieval returned almost all of it anyway. In exchange the backend carried ChromaDB, an ONNX embedding model downloaded on first use, a warm-up thread, a readiness check for the index, and an index that was never rebuilt after `knowledge/` changed.

## Decision

- `knowledge/*.md` is read once at startup and sent in full with every decode request (about 500 tokens).
- ChromaDB and the readiness check for the knowledge base are removed.

## Consequences

- Fewer dependencies and a faster cold start, with nothing to warm up.
- Edits to `knowledge/` take effect on the next restart; there is no index to delete.
- The model always sees every section, so a decode can no longer fail because retrieval missed the relevant one.
- If the reference grows past a few thousand tokens, retrieval becomes worth its cost again and this decision should be revisited.
