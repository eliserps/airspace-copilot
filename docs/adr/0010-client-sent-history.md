# 0010. The client sends the conversation history

**Status:** Accepted

## Context

The chat looked like a conversation, but each question reached the agent alone, so follow-ups such as "and at Guarulhos?" lost their context.

## Decision

- `AskRequest` takes an optional `history` of earlier `user` and `assistant` turns, oldest first.
- The server keeps no session state; the browser sends the last 6 turns, each cut to 2,000 characters.
- The API accepts at most 8 turns of at most 2,000 characters each, and only the `user` and `assistant` roles.
- History turns go through the same normalisation and injection checks as the question. Flagged user turns are wrapped as untrusted data and logged; `flagged` in the response still refers only to the current question.

## Consequences

- Follow-up questions work, and the API stays stateless.
- Every question costs more prompt tokens, bounded by the turn and length limits.
- A client can forge `assistant` turns. That gives it no more power than a crafted question already has: the agent can only call its two read-only tools (see [0007](0007-guardrails.md)).
