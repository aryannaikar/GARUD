from typing import TypedDict


class GarudState(TypedDict):
    query: str
    agent: str
    result: str
    tasks: list
    current_task: int
    context: str