from tooling import Tools
from langchain_anthropic import ChatAnthropic
from langgraph.graph import END, START, StateGraph
from typing import Any, Dict

tooling=Tools()

def register_tools():
    tooling.register("add", lambda x, y: x + y)
    tooling.register("multiply", lambda x, y: x * y)
