from langgraph.graph import StateGraph, END

from graph.state import GarudState

from agents.qwen_supervisor import supervisor_node
from agents.math_agent import math_node
from agents.media_agent import media_node
from agents.file_agent import file_node
from agents.chat_agent import chat_node
from agents.web_agent import web_node
from agents.planner_agent import planner_node
from agents.executor_agent import executor_node
from agents.memory_agent import memory_node
from agents.code_agent import code_node
from agents.system_agent import system_node
from agents.vision_agent import vision_node
from agents.screen_agent import screen_node

workflow = StateGraph(GarudState)

# Nodes
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("math", math_node)
workflow.add_node("media", media_node)
workflow.add_node("file", file_node)
workflow.add_node("chat", chat_node)
workflow.add_node("web", web_node)
workflow.add_node("planner", planner_node)
workflow.add_node("executor", executor_node)
workflow.add_node("memory", memory_node)
workflow.add_node("code", code_node)
workflow.add_node("system", system_node)
workflow.add_node("vision", vision_node)
workflow.add_node("screen", screen_node)


# Supervisor → Agent routing
def route(state):
    return state["agent"]


workflow.add_conditional_edges(
    "supervisor",
    route,
    {
        "math": "math",
        "media": "media",
        "file": "file",
        "chat": "chat",
        "web": "web",
        "planner": "planner",
        "memory": "memory",
        "code": "code",
        "system": "system",
        "vision": "vision",
        "screen": "screen",
    }
)

# Simple agents → END
workflow.add_edge("math", END)
workflow.add_edge("media", END)
workflow.add_edge("file", END)
workflow.add_edge("chat", END)
workflow.add_edge("web", END)
workflow.add_edge("memory", END)
workflow.add_edge("code", END)
workflow.add_edge("system", END)
workflow.add_edge("vision", END)
workflow.add_edge("screen", END)

# Planner → Executor (conditional: keep looping until all tasks done)
def executor_route(state):
    if state["current_task"] < len(state["tasks"]):
        return "executor"
    return END


workflow.add_conditional_edges(
    "planner",
    executor_route,
    {
        "executor": "executor",
        END: END,
    }
)

# Executor loops back through executor_route until all tasks complete
workflow.add_conditional_edges(
    "executor",
    executor_route,
    {
        "executor": "executor",
        END: END,
    }
)

# Entry Point
workflow.set_entry_point("supervisor")

graph = workflow.compile()
