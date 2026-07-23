import json
from llm_tools import chat_with_tools
from weather import get_metar
from tools import count_aircraft

SYSTEM_PROMPT = """You are an airspace assistant.

STRICT RULES:
- Answer questions about live air traffic and weather ONLY using the tools.
- Never answer from your own knowledge about current traffic, aircraft counts
 or weather. If no tool can answer it, say you don't have that data.
- Data comes from OpenSky (partial volunteer coverage) — mention this when
 reporting aircraft counts.
- Answer in the same language the user asked in.
"""

TOOLS = [
   {
       "type": "function",
       "function": {
           "name": "get_metar",
           "description": "Get the current aviation weather (METAR) for an airport. "
                          "Use this when the user asks about weather, visibility, "
                          "wind or landing conditions at a specific airport.",
           "parameters": {
               "type": "object",
               "properties": {
                   "icao_code": {
                       "type": "string",
                       "description": "The 4-letter ICAO airport code, e.g. SBGR for "
                                      "Guarulhos, SBGL for Galeao, SBPA for Porto Alegre.",
                   }
               },
               "required": ["icao_code"],
           },
       },
   },
   {
       "type": "function",
       "function": {
           "name": "count_aircraft",
           "description": "Get live aircraft currently detected over a region. "
                          "Use this when the user asks how many planes are flying "
                          "somewhere, or what traffic looks like in an area.",
           "parameters": {
               "type": "object",
               "properties": {
                   "region": {
                       "type": "string",
                       "enum": ["brazil", "sao_paulo", "rio_de_janeiro",
                                "porto_alegre", "brasilia"],
                       "description": "The region to check.",
                   }
               },
               "required": ["region"],
           },
       },
   },
]

AVAILABLE_FUNCTIONS = {
   "get_metar": get_metar,
   "count_aircraft": count_aircraft,
}

MAX_ITERATIONS = 5

def run_agent(question: str) -> str:
   """Answers a question, looping through tool calls until it has an answer."""
   messages = [
       {"role": "system", "content": SYSTEM_PROMPT},
       {"role": "user", "content": question},
   ]

   already_called = {}

   for step in range(MAX_ITERATIONS):
       response = chat_with_tools(messages, TOOLS)

       if not response.tool_calls:
           return response.content
       
       messages.append({
           "role": "assistant",
           "content": response.content or "",
           "tool_calls": [
               {
                   "id": call.id,
                   "type": "function",
                   "function": {
                       "name": call.function.name,
                       "arguments": call.function.arguments,
                   },
               }
               for call in response.tool_calls
           ],
       })

       repeated = False

       for tool_call in response.tool_calls:
           function_name = tool_call.function.name
           raw_arguments = tool_call.function.arguments
           arguments = json.loads(raw_arguments)
           signature = (function_name, raw_arguments)

           if signature in already_called:
               print(f"[agent] step {step + 1} — repeated {function_name}, using cache")
               result = already_called[signature]
               repeated = True
           else:
               print(f"[agent] step {step + 1} — {function_name}({arguments})")
               function = AVAILABLE_FUNCTIONS[function_name]
               result = function(**arguments)

               if result is None or (isinstance(result, str) and not result.strip()):
                   result = "No data available for this request."

               already_called[signature] = result

           messages.append({
               "role": "tool",
               "tool_call_id": tool_call.id,
               "content": str(result),
           })

       if repeated:
           final = chat_with_tools(messages, tools=None)
           return final.content
       
   final = chat_with_tools(messages, tools=None)
   return final.content
