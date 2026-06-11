import re
import json

from tools.file_tools import (
    create_folder,
    open_downloads,
    open_desktop,
    create_file_on_desktop,
    write_content_to_file,
    open_best_match,
    refresh_file_cache,
)

def handle_file_rules(query, context=""):
    """
    Rule-based file handler — instant, no LLM needed.
    context: previous task output (e.g. essay text) to write into the file.
    """

    q = query.lower().strip()

    if "create folder" in q:
        folder_name = q.replace("create folder", "").strip()
        if not folder_name:
            return "Please provide a folder name."
        return create_folder(folder_name)

    # "save content" / "write content" → use context to overwrite existing file
    elif any(kw in q for kw in ["save", "write content", "write the"]):
        match = re.search(r'["\']?([\w\-]+\.\w+)["\']?', query)
        file_name = match.group(1) if match else "output.txt"
        if context:
            return write_content_to_file(file_name, context)
        return f"Nothing to save — no content from previous task."

    # "create file" → create empty file (or with context if available)
    elif re.search(r"(create|make|new)\s+(a\s+)?(new\s+)?file", q):
        match = re.search(r'["\']?([\w\-]+\.\w+)["\']?', query)
        file_name = match.group(1) if match else "output.txt"
        return create_file_on_desktop(file_name, content=context or None)

    elif "open downloads" in q:
        return open_downloads()

    elif "open desktop" in q:
        return open_desktop()

    elif q == "refresh cache":
        return refresh_file_cache()

    elif q.startswith("open "):
        return open_best_match(q)

    return "I couldn't understand the file request."


def file_node(state):
    context = state.get("context", "")
    state["result"] = handle_file_rules(state["query"], context=context)
    return state
