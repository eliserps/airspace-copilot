import json

import requests

from .llm_tools import chat_with_tools
from .weather import fetch_metar
from .tools import REGIONS, count_aircraft

SYSTEM_PROMPT = """You are an airspace assistant.

STRICT RULES:
- Answer questions about live air traffic and weather ONLY using the tools.
- Never answer from your own knowledge about current traffic, aircraft counts
 or weather. If no tool can answer it, say you don't have that data.
- Data comes from OpenSky (partial volunteer coverage) — mention this when
 reporting aircraft counts.
- Answer in the same language the user asked in.
"""

REGION_CONTEXT = (
   "The user is looking at the map region '{region}'. When the question says "
   "\"here\", \"this region\" or names no place, use that region."
)

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
                       "enum": sorted(REGIONS),
                       "description": "The region to check.",
                   }
               },
               "required": ["region"],
           },
       },
   },
]

def metar_tool(icao_code: str) -> str:
   try:
       metar = fetch_metar(icao_code)
   except ValueError as error:
       return f"Error: {error}"
   if not metar:
       return f"No current METAR is published for {icao_code.strip().upper()}."
   return metar


AVAILABLE_FUNCTIONS = {
   "get_metar": metar_tool,
   "count_aircraft": count_aircraft,
}

MAX_ITERATIONS = 5


def _execute_tool(function_name: str, raw_arguments: str) -> str:
   """Runs one requested tool call and returns its result as text.

   The model's request is untrusted output: it can name a tool that does not
   exist or send arguments that are not valid JSON. Those become an error
   message fed back to the model -- which can correct itself -- instead of an
   exception that would turn the whole request into a 500.
   """
   function = AVAILABLE_FUNCTIONS.get(function_name)
   if function is None:
       return (f"Error: unknown tool '{function_name}'. "
               f"Available tools: {', '.join(AVAILABLE_FUNCTIONS)}.")
   try:
       arguments = json.loads(raw_arguments or "{}")
   except json.JSONDecodeError:
       return "Error: tool arguments were not valid JSON."
   if not isinstance(arguments, dict):
       return "Error: tool arguments must be a JSON object."
   try:
       result = function(**arguments)
   except TypeError as error:
       return f"Error: invalid arguments for {function_name}: {error}"
   except requests.RequestException as error:
       print(f"[agent] {function_name} failed upstream: {error}")
       return (f"Error: the data source for {function_name} is unavailable "
               "right now. Tell the user this part could not be checked.")

   if result is None or (isinstance(result, str) and not result.strip()):
       return "No data available for this request."
   return str(result)

def run_agent(question: str, region: str | None = None) -> str:
   """Answers a question, looping through tool calls until it has an answer."""
   system_prompt = SYSTEM_PROMPT
   if region in REGIONS:
       system_prompt += "\n" + REGION_CONTEXT.format(region=region)
   messages = [
       {"role": "system", "content": system_prompt},
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
           signature = (function_name, raw_arguments)

           if signature in already_called:
               print(f"[agent] step {step + 1} — repeated {function_name}, using cache")
               result = already_called[signature]
               repeated = True
           else:
               print(f"[agent] step {step + 1} — {function_name}({raw_arguments})")
               result = _execute_tool(function_name, raw_arguments)
               already_called[signature] = result

           messages.append({
               "role": "tool",
               "tool_call_id": tool_call.id,
               "content": result,
           })

       if repeated:
           final = chat_with_tools(messages, tools=None)
           return final.content
       
   final = chat_with_tools(messages, tools=None)
   return final.content