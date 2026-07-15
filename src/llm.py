from groq import Groq
from config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

def ask(prompt: str, system_prompt: str | None = None) -> str:
   """Sends a prompt to the model and returns the text answer."""
   messages = []
   if system_prompt:
       messages.append({"role": "system", "content": system_prompt})
   messages.append({"role": "user", "content": prompt})
   response = client.chat.completions.create(
       model="llama-3.3-70b-versatile",
       messages=messages,
       temperature=0.2,
   )
   return response.choices[0].message.content