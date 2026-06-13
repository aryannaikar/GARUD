"""
Screen Agent — reads the user's screen.

Pipeline (priority order):
  1. Try local Ollama vision model (moondream → llava) — best quality
  2. If no vision model available, fall back to pytesseract OCR + qwen3:8b
  3. Active window title always read instantly via Windows API

NO NVIDIA — 100% offline, 100% local. Screenshot stays on your machine.
"""

import io
import os
import requests
import tempfile

_OLLAMA_URL = "http://localhost:11434/api/generate"

# Vision models (multimodal) — tried first
_VISION_MODELS = ["moondream:latest", "llava:latest", "llava:7b", "bakllava:latest", "llava-phi3:latest"]

# Text-only fallback models for OCR pipeline
_TEXT_MODELS = ["qwen3:8b", "llama3:latest", "qwen2.5-coder:3b"]

# Tesseract binary path (Windows default)
_TESS_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# ── Windows active window ─────────────────────────────────────────────────────

def _get_active_window_title() -> str:
    try:
        import ctypes
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
        return buf.value.strip()
    except Exception:
        return ""


# ── Screen capture ────────────────────────────────────────────────────────────

def _capture_screen():
    """Returns (PIL_image, tmp_path, base64_str) or raises RuntimeError."""
    try:
        import mss
        from PIL import Image

        with mss.mss() as sct:
            monitor = sct.monitors[1]
            shot = sct.grab(monitor)
            img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")

        # Resize if huge — vision models work well at ~1280px
        max_w = 1280
        if img.width > max_w:
            ratio = max_w / img.width
            img = img.resize((max_w, int(img.height * ratio)), Image.LANCZOS)

        # Save tmp for HUD display
        tmp_path = os.path.join(tempfile.gettempdir(), "garud_screen_capture.png")
        img.save(tmp_path, format="PNG")

        # Base64 for vision model
        import base64
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

        return img, tmp_path, b64

    except ImportError as e:
        raise RuntimeError(f"Missing dep: {e}. Run: pip install mss pillow") from e


# ── Vision model path ─────────────────────────────────────────────────────────

def _ask_vision_model(b64: str, prompt: str, timeout: int = 60) -> str:
    """Send screenshot to local Ollama vision model. Returns '' if none available."""
    for model in _VISION_MODELS:
        try:
            resp = requests.post(
                _OLLAMA_URL,
                json={
                    "model": model,
                    "prompt": prompt,
                    "images": [b64],
                    "stream": False,
                    "options": {"temperature": 0.2, "num_predict": 350},
                },
                timeout=timeout,
            )
            if resp.status_code == 404:
                # Model not pulled — silently try next
                continue
            resp.raise_for_status()
            text = resp.json().get("response", "").strip()
            if text:
                print(f"[Screen Agent] Vision model used: {model}")
                return text
        except requests.exceptions.ConnectionError:
            return "Ollama is not running. Start it with: ollama serve"
        except Exception as e:
            print(f"[Screen Agent] Vision model '{model}' failed: {e}")
    return ""


# ── OCR + text model fallback ─────────────────────────────────────────────────

def _ocr_extract(img) -> str:
    try:
        import pytesseract
        if os.path.exists(_TESS_PATH):
            pytesseract.pytesseract.tesseract_cmd = _TESS_PATH
        text = pytesseract.image_to_string(img, lang="eng")
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        return "\n".join(lines)
    except ImportError:
        return ""
    except Exception as e:
        print(f"[Screen Agent] OCR error: {e}")
        return ""


def _ask_text_model(prompt: str, timeout: int = 30) -> str:
    for model in _TEXT_MODELS:
        try:
            resp = requests.post(
                _OLLAMA_URL,
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.2, "num_predict": 300},
                },
                timeout=timeout,
            )
            resp.raise_for_status()
            text = resp.json().get("response", "").strip()
            if "<think>" in text and "</think>" in text:
                text = text.split("</think>")[-1].strip()
            if text:
                print(f"[Screen Agent] Text model used: {model}")
                return text
        except requests.exceptions.ConnectionError:
            return "Ollama is not running. Start it with: ollama serve"
        except Exception as e:
            print(f"[Screen Agent] Text model '{model}' failed: {e}")
    return ""


# ── Prompt builder ────────────────────────────────────────────────────────────

def _vision_prompt(query: str) -> str:
    q = query.lower()
    if any(kw in q for kw in ["read", "text", "say", "written", "words", "content"]):
        return "You are Garud. Read ALL visible text from this screenshot and report it. Be concise. No markdown."
    if any(kw in q for kw in ["summarize", "summary", "brief", "overview"]):
        return "You are Garud. Give a 2-3 sentence summary of what is on this screen. No markdown."
    if any(kw in q for kw in ["what app", "which app", "what program", "what window"]):
        return "You are Garud. Identify the application or program open in this screenshot. No markdown."
    return f"You are Garud. The user asked: '{query}'. Describe what you see on the screen in 2-4 sentences. No markdown."


def _ocr_prompt(query: str, ocr_text: str, title: str) -> str:
    q = query.lower()
    title_ctx = f"Active window: '{title}'\n\n" if title else ""
    
    # Dramatically reduce snippet size to prevent local LLM timeouts
    snippet_limit = 800 
    snippet = ocr_text[:snippet_limit] + ("\n...[truncated]" if len(ocr_text) > snippet_limit else "")

    if "read all" in q or "read everything" in q:
        instruction = "Read and report the text visible on the screen."
    elif any(kw in q for kw in ["what app", "which app", "what program", "what window"]):
        instruction = "Identify the application or document that is open."
    else:
        # Default to summarizing to avoid reading massive blocks of text
        instruction = f"The user asked: '{query}'. Briefly summarize what you see on the screen based on the text. Do not read all the words."

    return (
        f"You are Garud, an AI assistant. {title_ctx}"
        f"Text extracted from the user's screen via OCR:\n---\n{snippet}\n---\n\n"
        f"{instruction} Be direct and concise (1-3 sentences max). No markdown."
    )


# ── Main entry ────────────────────────────────────────────────────────────────

def read_screen(query: str) -> tuple[str, str | None]:
    """Returns (answer, screenshot_path_or_None)."""
    print("[Screen Agent] Capturing screen...")
    window_title = _get_active_window_title()

    try:
        img, tmp_path, b64 = _capture_screen()
    except RuntimeError as e:
        return str(e), None

    # ── Try vision model first (moondream etc.) ──
    print("[Screen Agent] Trying vision model...")
    answer = _ask_vision_model(b64, _vision_prompt(query))

    if answer:
        return answer, tmp_path

    # ── Fallback: OCR + text model ──
    print("[Screen Agent] No vision model available — using OCR fallback...")
    ocr_text = _ocr_extract(img)

    if not ocr_text:
        msg = ""
        if window_title:
            msg = f"Active window: '{window_title}'.\n"
        msg += "OCR found no text. Try asking about the active window or install Tesseract for full OCR."
        return msg, tmp_path

    prompt = _ocr_prompt(query, ocr_text, window_title)
    answer = _ask_text_model(prompt)

    if not answer:
        preview = ocr_text[:500] + ("..." if len(ocr_text) > 500 else "")
        answer = f"Active window: '{window_title}'\n\nScreen text:\n{preview}"

    return answer, tmp_path


# ── LangGraph node ────────────────────────────────────────────────────────────

def screen_node(state: dict) -> dict:
    answer, screenshot_path = read_screen(state["query"])
    state["result"] = answer
    state["agent"] = "screen"
    if screenshot_path:
        state["screenshot_path"] = screenshot_path
    return state
