from agents.chat_agent import chat_node
from agents.file_agent import file_node
from agents.media_agent import media_node
from agents.math_agent import math_node
from agents.web_agent import web_node


AGENT_MAP = {
    "chat": chat_node,
    "file": file_node,
    "media": media_node,
    "math": math_node,
    "web": web_node,
}


def executor_node(state):
    tasks = state["tasks"]
    idx = state["current_task"]

    if idx >= len(tasks):
        return state

    task = tasks[idx]

    print(
        f"\nExecuting Task {idx + 1}/{len(tasks)}: "
        f"[{task['agent']}] {task['task']}"
    )

    sub_state = state.copy()
    sub_state["query"] = task["task"]
    # Pass the latest result as context so file tasks can write chat output
    sub_state["context"] = state.get("result", "")

    agent_func = AGENT_MAP.get(task["agent"])
    if agent_func:
        sub_state = agent_func(sub_state)

    task_result = sub_state.get("result", "")

    # Accumulate full context log
    state["context"] = (
        state.get("context", "") +
        f"\nTask {idx + 1} [{task['agent']}]: {task_result}"
    )

    # Latest result (used by next file/write task)
    state["result"] = task_result

    state["current_task"] += 1

    return state