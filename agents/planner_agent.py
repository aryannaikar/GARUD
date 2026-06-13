import os
import json
import re
from dotenv import load_dotenv
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()

_nvidia_client = ChatNVIDIA(
    model="nvidia/nemotron-mini-4b-instruct",
    api_key=os.getenv("NVIDIA_API_KEY"),
    temperature=0,
)


def planner_node(state):
    query = state["query"]

    prompt = f"""
You are Garud's Planner Agent.

Break the user's request into sequential tasks.

Available agents:
- chat   → generates text/content only (NEVER saves files)
- file   → creates files, saves content to files, opens files
- media  → opens/closes apps (Chrome, VS Code, YouTube, etc.) and handles windows
- math   → calculations
- web    → web searches

STRICT RULES:
1. A chat task ONLY generates text. It NEVER saves to a file.
2. If the user wants generated content written to a file, you MUST have a separate file task after the chat task.
3. Always split "write X and save it" into: chat task (write X) + file task (save it).

Return ONLY valid JSON array. No explanation. No markdown.

Example 1:
User: Write an essay on AI and save it as demo.txt

Output:
[
    {{"agent": "chat", "task": "Write an essay on AI"}},
    {{"agent": "file", "task": "Save as demo.txt on Desktop"}}
]

Example 2:
User: Create file demo.txt, write essay on AI in it and open it

Output:
[
    {{"agent": "file", "task": "Create file demo.txt on Desktop"}},
    {{"agent": "chat", "task": "Write an essay on AI"}},
    {{"agent": "file", "task": "Save content as demo.txt on Desktop"}},
    {{"agent": "file", "task": "Open demo.txt"}}
]

Example 3:
User: Open Chrome and search latest AI news

Output:
[
    {{"agent": "media", "task": "Open Chrome"}},
    {{"agent": "web", "task": "Search latest AI news"}}
]

Example 4:
User: Write an essay on AI in Notepad

Output:
[
    {{"agent": "chat", "task": "Write an essay on AI"}},
    {{"agent": "file", "task": "Save content as ai_essay.txt"}},
    {{"agent": "file", "task": "Open ai_essay.txt"}}
]

User: {query}
"""

    response = _nvidia_client.invoke([HumanMessage(content=prompt)])
    output = response.content.strip()

    # Strip markdown code fences if present
    output = re.sub(r"```(?:json)?", "", output).strip()

    # Extract the JSON array even if there's extra text
    match = re.search(r"\[.*\]", output, re.DOTALL)
    if match:
        output = match.group(0)

    try:
        state["tasks"] = json.loads(output)
    except Exception:
        state["tasks"] = []

    state["current_task"] = 0

    return state