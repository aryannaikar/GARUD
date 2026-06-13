from typing import TypedDict


class GarudState(TypedDict, total=False):
    query: str
    agent: str
    result: str
    tasks: list
    current_task: int
    context: str
    screenshot_path: str   # populated by screen_agent when capturing the display