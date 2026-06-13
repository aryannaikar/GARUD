"""
Pure rule-based supervisor — zero LLM calls, zero latency.
chat is the universal fallback and can answer general knowledge.
"""

def rule_supervisor(query: str) -> str:
    q = query.lower()

    # ── Planner: multi-step requests ──────────────────────────────
    planner_triggers = [" and ", " then ", " after that ", " also ", " notepad", " save "]
    if any(kw in q for kw in planner_triggers):
        # Trigger planner for clear multi-action patterns or file/app combinations
        if any(kw in q for kw in ["open", "create", "write", "save", "search", "play", "launch"]):
            return "planner"

    # ── Math ──────────────────────────────────────────────────────
    if any(kw in q for kw in [
        "calculate", "compute", "solve", "what is ", "% of",
        "+ ", "- ", "* ", "/ ", "^ ",
    ]) and any(c.isdigit() for c in q):
        return "math"

    # ── Code / Programming ─────────────────────────────────────────
    code_kws = ["code", "script", "program", "python", "html", "css", "javascript", "app"]
    action_kws = ["create", "write", "make", "generate", "build"]
    if any(kw in q for kw in code_kws) and any(kw in q for kw in action_kws):
        return "code"

    # ── System / OS Control ────────────────────────────────────────
    sys_kws = ["system", "status", "stats", "battery", "cpu", "ram", "memory usage", "disk", "screenshot"]
    if any(kw in q for kw in sys_kws):
        return "system"

    # ── File operations (checked BEFORE media to avoid 'calculator.py' → media) ──
    file_verbs = ["create", "make", "new", "open", "save", "write", "name ", "read"]
    file_nouns = [
        "file", "folder", "directory",
        "txt", "pdf", "docx", ".py", ".js", ".ts", ".html", ".css",
        "desktop", "downloads", "document"
    ]
    if any(verb in q for verb in file_verbs) and any(noun in q for noun in file_nouns):
        return "file"
    if q.startswith("create ") or q.startswith("make "):
        if any(noun in q for noun in file_nouns):
            return "file"

    # ── Media: open apps / play music / send messages ─────────────
    media_apps = [
        "chrome", "firefox", "edge", "youtube", "spotify",
        "vs code", "vscode", "notepad", "calculator", "word",
        "excel", "powerpoint", "vlc", "whatsapp", "telegram",
        "file explorer", "task manager", "settings"
    ]
    media_verbs = ["open", "launch", "start", "run", "switch to", "go to", "play", "close", "quit", "exit", "kill"]
    if any(app in q for app in media_apps) and any(v in q for v in media_verbs):
        return "media"
        
    # Implicit media actions (don't require app name)
    if q.startswith("play "):
        return "media"
    if any(q.startswith(w) for w in ["close", "quit", "exit"]):
        return "media"
    if any(kw in q for kw in ["close it", "close this", "close that", "close the window", "close app"]):
        return "media"
    if q.startswith("send ") or "send it" in q or q.startswith("introduce ") or "type " in q or "reply " in q or "apologize" in q or "apology" in q or "message her" in q or "message him" in q:
        return "media"
    if "skip" in q and "ad" in q:
        return "media"
    if any(kw in q for kw in ["pause", "resume", "stop the song", "stop playing", "next song", "previous song"]):
        return "media"

    # ── Fallback for "open <file>" if it wasn't a known app ────────
    if q.startswith("open "):
        return "file"

    # ── Web: real-time / current events / live data ───────────────
    if any(kw in q for kw in [
        "latest", "today", "yesterday", "right now", "currently",
        "live", "news", "weather", "forecast",
        "who won", "who is winning", "score", "result",
        "ipl", "cricket", "football", "match", "tournament",
        "stock", "price of", "share price", "crypto",
        "trending", "breaking",
    ]):
        return "web"

    # ── Memory: Save/Delete long-term database ─────────────────────
    if q.startswith("remember ") or " forget " in q or q.startswith("forget ") or "delete memory" in q:
        return "memory"

    # ── Screen Reading: read/describe the desktop display ────────────
    screen_kws = [
        "read my screen", "read the screen", "what's on my screen",
        "what is on my screen", "what does my screen say",
        "look at my screen", "look at the screen",
        "describe my screen", "summarize my screen",
        "what's on screen", "what is on screen",
        "screen says", "read this screen", "read screen",
        "what app is open", "what window is open",
        "capture my screen", "screenshot and read",
    ]
    if any(kw in q for kw in screen_kws):
        return "screen"

    # ── Vision: camera / object detection queries ──────────────────
    vision_kws = [
        "what's in my hand", "what is in my hand",
        "what do you see", "what can you see",
        "what am i holding", "what i am holding", "am i holding",
        "what is this", "what are you seeing",
        "look at", "scan my", "detect",
        "identify this", "identify what",
        "what object", "camera", "show me what",
        "is there a", "can you see", "holding", "in front of"
    ]
    if any(kw in q for kw in vision_kws):
        return "vision"

    # ── Universal fallback: chat handles all general knowledge ─────
    return "chat"


def supervisor_node(state):
    state["agent"] = rule_supervisor(state["query"])
    return state