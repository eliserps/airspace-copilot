from llm import ask
from rag import search

SYSTEM_PROMPT = """You are an aviation weather decoder.

STRICT RULES:
- Decode METAR reports using ONLY the reference documentation provided.
- If a code is not covered by the documentation, say you cannot decode it.
 Never guess.
- Always state the operational meaning: are conditions good or poor for landing?
- Be concise and factual.
"""

def decode_metar(metar: str | None, language: str = "en") -> str:
   """Decodes a raw METAR into plain language, grounded in the reference docs."""
   # GUARDRAIL: never send empty data to the model
   if not metar or not metar.strip():
       return "No METAR available for this airport right now."
   
   chunks = search(metar, n_results=4)
   context = "\n\n---\n\n".join(
       f"[source: {c['source']}]\n{c['text']}" for c in chunks
   )

   language_name = "English" if language == "en" else "Brazilian Portuguese"

   prompt = f"""Reference documentation:

{context}

---

Decode this METAR in {language_name}:

{metar}

Explain each element, then give a one-line operational summary."""
   
   return ask(prompt, system_prompt=SYSTEM_PROMPT)