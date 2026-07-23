from groq import Groq
from config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

def chat_with_tools(messages: list, tools: list | None = None):
   """Sends the conversation to the model, optionally offering tools.
   When tools is None, the model can only answer with text — this is how we
   force a final answer and break tool-calling loops.
   """

   kwargs = {
       "model": "llama-3.3-70b-versatile",
       "messages": messages,
       "temperature": 0.2,
   }

   if tools:
       kwargs["tools"] = tools
       kwargs["tool_choice"] = "auto"
   response = client.chat.completions.create(**kwargs)

   return response.choices[0].message
