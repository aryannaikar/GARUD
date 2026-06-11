"""
Vision Agent — captures webcam frame, runs YOLO, answers with Ollama.
Uses direct HTTP to Ollama (no LangChain) to avoid NVIDIA key conflicts.
"""

import sys
import os
import cv2

# Allow importing from garud-vision sibling folder
_VISION_DIR = os.path.join(os.path.dirname(__file__), "..", "garud-vision")
if _VISION_DIR not in sys.path:
    sys.path.insert(0, _VISION_DIR)

from detectors.yolo_detector import YOLODetector


# Lazy-loaded singleton so YOLO only loads once
_detector: YOLODetector | None = None


def _get_detector() -> YOLODetector:
    global _detector
    if _detector is None:
        model_path = os.path.join(_VISION_DIR, "yolov8s.pt")
        _detector = YOLODetector(model_path=model_path)
    return _detector


def _ask_ollama(prompt: str, timeout: int = 8) -> str:
    """Direct HTTP call to local Ollama. Tries fast models first."""
    # Try models in order of speed — lightest first for vision queries
    models = ["llama3:latest", "qwen2.5-coder:3b", "qwen3:8b"]
    for model in models:
        try:
            resp = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.3, "num_predict": 100},
                },
                timeout=timeout,
            )
            resp.raise_for_status()
            result = resp.json().get("response", "").strip()
            if result:
                return result
        except Exception as e:
            print(f"[Vision] Ollama '{model}' error: {e}")
            continue
    return ""


def capture_and_detect() -> list[dict]:
    """
    Opens the default webcam, grabs one frame, runs YOLO.
    Returns detections as list of {class_name, confidence}.
    """
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return []

    # Single warmup frame (faster than 3)
    cap.read()
    ok, frame = cap.read()
    cap.release()

    if not ok or frame is None:
        return []

    detector = _get_detector()
    results = detector.detect(frame)
    return detector.get_detections(results)


def _build_counts(detections: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for d in detections:
        name = d["class_name"]
        counts[name] = counts.get(name, 0) + 1
    return counts


def _rule_answer(query: str, counts: dict[str, int]) -> str:
    """Fast rule-based fallback — always instant."""
    q = query.lower()
    items_str = ", ".join(f"{v} {k}" for k, v in counts.items())

    if not counts:
        return "I can't detect any objects in the frame right now."

    if any(kw in q for kw in ["hand", "holding", "is this", "what is"]):
        # Answer specifically about things in hand
        hand_objects = {k: v for k, v in counts.items() if k not in ["person", "people"]}
        if hand_objects:
            items = ", ".join(f"{v} {k}" for k, v in hand_objects.items())
            return f"I can see {items} in the frame."
        return f"I can see: {items_str}."

    if "how many" in q:
        for obj, count in counts.items():
            if obj in q:
                return f"I can see {count} {obj}(s) in the frame."
        return f"Total objects detected: {sum(counts.values())}."

    if any(kw in q for kw in ["what do you see", "what can you see", "see"]):
        return f"I can currently see: {items_str}."

    return f"Objects in frame: {items_str}."


def answer_vision_query(query: str) -> str:
    """Main entry — detect objects then answer instantly via rule-based logic."""
    try:
        detections = capture_and_detect()
    except Exception as e:
        return f"[Vision] Camera error: {e}"

    if not detections:
        return "I couldn't detect any objects. Is the webcam connected?"

    counts = _build_counts(detections)
    return _rule_answer(query, counts)


def vision_node(state: dict) -> dict:
    state["result"] = answer_vision_query(state["query"])
    state["agent"] = "vision"
    return state
