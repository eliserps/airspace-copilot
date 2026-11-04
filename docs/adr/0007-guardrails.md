# 0007. Guardrails flag injection; tool design contains it

**Status:** Accepted

## Context

The copilot accepts free text. Pattern matching against prompt injection catches only known phrasings; anyone determined can rephrase, translate or encode around it.

## Decision

- The real boundary is what the agent can do: two read-only tools with validated arguments (`region` is an enum, `icao_code` must be four characters), no secrets in its context and no write path.
- `copilot/guardrails.py` rejects structurally invalid input (empty, over 500 characters) before any model call, normalises Unicode so look-alike characters do not bypass the patterns, and flags known injection phrasings in English and Portuguese.
- Flagged questions are still answered, wrapped in explicit delimiters that mark them as data. They are logged and returned with `flagged: true`.

## Consequences

- A successful injection can at worst make the model say something wrong; it cannot make it act.
- False positives do not block legitimate questions.
- The pattern list is a tripwire for visibility, not a security control, and should not be treated as one.
