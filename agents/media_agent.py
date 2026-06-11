import os
from tools.media_tools import (
    open_chrome,
    open_google,
    open_youtube,
    open_vscode,
    open_antigravity,
    open_whatsapp
)

def handle_media(query):
    query = query.lower()

    if "whatsapp" in query:
        # Check if they asked for a specific person
        import re
        match = re.search(r'open\s+(.*?)\s+(chat\s+)?on\s+whatsapp', query)
        person = match.group(1).title() if match else ""
        return open_whatsapp(person)

    # ── Sending messages (Auto-Typer) ──
    if query.startswith("send"):
        import re, time, pyautogui
        # Extract the message: "send hi to her", "send hello"
        match = re.search(r'send\s+["\']?(.*?)["\']?(?:\s+to\s+.*)?$', query, re.IGNORECASE)
        msg = match.group(1).strip() if match else "Hello"
        # Type and send
        pyautogui.write(msg)
        time.sleep(0.2)
        pyautogui.press('enter')
        return f"Message sent: '{msg}'"
        
    # ── Skip Ads (YouTube) ──
    if "skip" in query and "ad" in query:
        import pyautogui
        # The 'Skip Ad' button is typically in the bottom right corner of the screen.
        w, h = pyautogui.size()
        # Click a few common regions where the button appears on standard displays
        pyautogui.click(int(w * 0.85), int(h * 0.85))
        pyautogui.click(int(w * 0.90), int(h * 0.90))
        return "Attempting to click the Skip Ad button..."

    # ── Media Controls (Pause/Resume/Next/Prev) ──
    if any(kw in query for kw in ["pause", "stop the song", "stop playing"]):
        import pyautogui
        pyautogui.press('playpause')
        return "Media paused."
    if "resume" in query:
        import pyautogui
        pyautogui.press('playpause')
        return "Media resumed."
    if "next song" in query:
        import pyautogui
        pyautogui.press('nexttrack')
        return "Skipping to next track..."
    if "previous song" in query:
        import pyautogui
        pyautogui.press('prevtrack')
        return "Going to previous track..."

    # ── Play media (default to YouTube) ──
    if "play" in query:
        import re
        match = re.search(r'play\s+(.*?)(?:\s+on\s+youtube)?$', query, re.IGNORECASE)
        song = match.group(1).title() if match else ""
        from tools.media_tools import open_youtube
        return open_youtube(song)

    if "chrome" in query:
        return open_chrome()
    elif "google" in query:
        return open_google()
    elif "vscode" in query or "vs code" in query:
        return open_vscode()
    elif "antigravity" in query:
        return open_antigravity()
    
    # Generic OS apps fallback
    elif "calculator" in query:
        os.system("start calc")
        return "Opening Calculator..."
    elif "notepad" in query:
        os.system("start notepad")
        return "Opening Notepad..."
    elif "settings" in query:
        os.system("start ms-settings:")
        return "Opening Settings..."

    return "I couldn't understand the media request."

def media_node(state):
    state["result"] = handle_media(state["query"])
    return state