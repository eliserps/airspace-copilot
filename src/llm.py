from groq import Groq
from config import GROQ_API_KEY, LLM_MODEL

client = Groq(api_key=GROQ_API_KEY)

def ask(
   prompt: str,
   system_prompt: str | None = None,
   json_mode: bool = False,
) -> str:
   """Sends a prompt to the model and returns the text answer.

   json_mode=True constrains the model to emit a single valid JSON object.
   The provider requires the word "JSON" to appear in the prompt when this is on.
   """
   messages = []
   if system_prompt:
       messages.append({"role": "system", "content": system_prompt})
   messages.append({"role": "user", "content": prompt})
   extra = {"response_format": {"type": "json_object"}} if json_mode else {}
   response = client.chat.completions.create(
       model=LLM_MODEL,
       messages=messages,
       temperature=0.2,
       **extra,
   )
   return response.choices[0].message.content