"""
Pure rule-based supervisor — zero LLM calls, zero latency.
chat is the universal fallback and can answer general knowledge.
"""

def rule_supervisor(query: str) -> str:
    q = query.lower()

    # ── Planner: multi-step requests ──────────────────────────────
    if any(kw in q for kw in [" and then ", " after that ", " also ", " then "]):
        # Only trigger planner for clear multi-action patterns
        if any(kw in q for kw in [
            "open", "create", "write", "save", "search", "play", "launch"
        ]):
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
    if q.startswith("create ") or q.startswith("make ") or q.startswith("write "):
        return "file"

    # ── Media: open apps / play music / send messages ─────────────
    media_apps = [
        "chrome", "firefox", "edge", "youtube", "spotify",
        "vs code", "vscode", "notepad", "calculator", "word",
        "excel", "powerpoint", "vlc", "whatsapp", "telegram",
        "file explorer", "task manager", "settings"
    ]
    media_verbs = ["open", "launch", "start", "run", "switch to", "go to", "play"]
    if any(app in q for app in media_apps) and any(v in q for v in media_verbs):
        return "media"
        
    # Implicit media actions (don't require app name)
    if q.startswith("play "):
        return "media"
    if q.startswith("send ") or "send it" in q:
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

    # ── Vision: camera / object detection queries ──────────────────
    vision_kws = [
        "what's in my hand", "what is in my hand",
        "what do you see", "what can you see",
        "what am i holding", "what is this",
        "look at", "scan my", "detect",
        "identify this", "identify what",
        "what object", "camera", "show me what",
        "is there a", "can you see",
    ]
    if any(kw in q for kw in vision_kws):
        return "vision"

    # ── Universal fallback: chat handles all general knowledge ─────
    return "chat"


def supervisor_node(state):
    state["agent"] = rule_supervisor(state["query"])
    return state