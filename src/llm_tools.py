from .config import LLM_MODEL
from .llm import get_client, log_usage

def chat_with_tools(messages: list, tools: list | None = None):
    """Sends the conversation to the model. With tools=None it must answer in text."""
    kwargs = {
        "model": LLM_MODEL,
        "messages": messages,
        "temperature": 0.2,
    }

    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"
    response = get_client().chat.completions.create(**kwargs)
    log_usage("agent", response.usage)

    return response.choices[0].message
