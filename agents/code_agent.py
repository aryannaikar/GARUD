"""
Code Agent — uses local Ollama qwen2.5-coder for zero-latency, offline code generation.
Falls back to qwen3:8b if coder model unavailable.
"""
import os
import re
import requests

SYSTEM_PROMPT = (
    "You are an expert coding assistant. "
    "Write clean, correct, runnable code to fulfill the user's request. "
    "Output ONLY the raw code inside a single ```python``` block. "
    "No explanations. No comments outside the block."
)

_MODELS = ["qwen2.5-coder:3b", "qwen2.5-coder:1.5b", "qwen3:8b", "llama3:latest"]


def _ask_ollama(prompt: str, timeout: int = 60) -> str:
    for model in _MODELS:
        try:
            resp = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1, "num_predict": 600},
                },
                timeout=timeout,
            )
            resp.raise_for_status()
            text = resp.json().get("response", "").strip()
            if text:
                print(f"[Code Agent] Used model: {model}")
                return text
        except Exception as e:
            print(f"[Code Agent] {model} failed: {e}")
    return ""


def _extract_code(raw: str) -> str:
    """Pull code out of ```python``` block, or return raw if no block."""
    if "```python" in raw:
        return raw.split("```python")[1].split("```")[0].strip()
    if "```" in raw:
        return raw.split("```")[1].split("```")[0].strip()
    return raw.strip()


def _infer_filename(query: str) -> str:
    """Try to extract a filename from the query, else use default."""
    # Match patterns like "calculator.py", "calculator dot py"
    q = query.lower().replace("dot py", ".py").replace("dot js", ".js")
    match = re.search(r'(\w[\w\-]*\.(py|js|html|css|ts|txt))', q)
    if match:
        return match.group(1)
    # If user says "for X" or "called X", use that
    for pattern in [r'for (\w+)', r'called (\w+)', r'named (\w+)']:
        m = re.search(pattern, q)
        if m:
            word = m.group(1).strip()
            if word not in ("a", "an", "the", "me", "my"):
                return f"{word}.py"
    return "garud_generated.py"


def generate_code(query: str) -> str:
    print("[Code Agent] Generating code via local Ollama...")

    prompt = f"{SYSTEM_PROMPT}\n\nUser Request: {query}\n/no_think"
    raw = _ask_ollama(prompt)

    if not raw:
        return "Sorry, I couldn't generate code right now. Make sure Ollama is running."

    code = _extract_code(raw)

    # Save to Desktop
    desktop = os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop")
    if not os.path.exists(desktop):
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")

    filename = _infer_filename(query)
    file_path = os.path.join(desktop, filename)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(code)

    return (
        f"Done! I've written the code and saved it to your Desktop as `{filename}`.\n\n"
        f"```python\n{code[:800]}{'...' if len(code) > 800 else ''}\n```"
    )


def code_node(state: dict) -> dict:
    state["result"] = generate_code(state["query"])
    return state
