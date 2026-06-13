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

    # ── Close Applications ──
    if "close" in query or "quit" in query or "exit" in query:
        import pyautogui
        if "whatsapp" in query:
            os.system("taskkill /f /im WhatsApp.exe /im WhatsApp.Root.exe >nul 2>&1")
            return "Closed WhatsApp."
        elif "chrome" in query or "google" in query:
            os.system("taskkill /f /im chrome.exe >nul 2>&1")
            return "Closed Google Chrome."
        elif "vscode" in query or "vs code" in query:
            os.system("taskkill /f /im Code.exe >nul 2>&1")
            return "Closed Visual Studio Code."
        elif "youtube" in query:
            pyautogui.hotkey('ctrl', 'w')
            return "Closed the active tab."
        elif "calculator" in query:
            os.system("taskkill /f /im CalculatorApp.exe >nul 2>&1")
            return "Closed Calculator."
        elif "notepad" in query:
            os.system("taskkill /f /im notepad.exe >nul 2>&1")
            return "Closed Notepad."
        elif "settings" in query:
            os.system("taskkill /f /im SystemSettings.exe >nul 2>&1")
            return "Closed Settings."
        else:
            pyautogui.hotkey('alt', 'f4')
            return "Closed the active window."

    if "whatsapp" in query:
        import re
        
        # Check for introduction request
        intro_match = re.search(r'introduce\s+yourself\s+to\s+(.*?)\s+(chat\s+)?on\s+whatsapp', query)
        if intro_match:
            person = intro_match.group(1).title()
            msg = "Hello! I am Garud, an advanced AI sidekick created by Aryan Naikar. He asked me to introduce myself to you!"
            return open_whatsapp(person, message=msg)
            
        # Normal open chat request
        match = re.search(r'open\s+(.*?)\s+(chat\s+)?on\s+whatsapp', query)
        person = match.group(1).title() if match else ""
        return open_whatsapp(person)

    # ── Sending & Generating messages (Auto-Typer & Ghostwriter) ──
    is_generation = any(kw in query for kw in ["type ", "reply ", "apologize", "apology", "message her", "message him"])
    is_send = query.startswith("send") or "send it" in query
    
    if is_generation or is_send:
        import time, pyautogui
        
        try:
            from agents.chat_agent import _chat_history, _nvidia_client
            from langchain_core.messages import SystemMessage, HumanMessage
            
            if is_generation:
                sys_prompt = (
                    "You are a ghostwriter for the user. "
                    "The user wants you to generate a message to send to someone based on their prompt. "
                    "Write the EXACT message they should send. Keep it natural, human-like, and appropriate for text messaging (WhatsApp). "
                    "CRITICAL RULES:\n"
                    "1. Return ONLY the raw text message to be sent.\n"
                    "2. DO NOT include quotes, intros, or explanations like 'Here is the apology:'\n"
                    "3. Write it from the user's perspective (using 'I')."
                )
            else:
                sys_prompt = (
                    "You are a strict data extraction script, not a conversational AI. "
                    "The user is asking to send a message. Based on the chat history, extract ONLY the raw text payload to be sent. "
                    "CRITICAL RULES:\n"
                    "1. DO NOT reply to the user. DO NOT say 'Sure' or 'I can help'.\n"
                    "2. DO NOT include the voice command itself (e.g., if they say 'send message hi', output: hi)\n"
                    "3. If they refer to a previous item (e.g., 'the third one'), find that exact text in the history and output it.\n"
                    "4. Output strictly the message text, nothing else."
                )
            
            messages = [SystemMessage(content=sys_prompt)] + _chat_history + [HumanMessage(content=f"PROMPT: '{query}'")]
            response = _nvidia_client.invoke(messages)
            msg = response.content.strip().strip("'").strip('"')
            
            # Reject if the LLM hallucinated a conversational response or grabbed a system message
            bad_prefixes = ["sure", "i can", "here is", "the message is", "please provide", "i'll send", "message sent"]
            if not msg or len(msg) > 1000 or msg.lower() == query.lower() or any(msg.lower().startswith(p) for p in bad_prefixes) or "message sent" in msg.lower():
                raise ValueError(f"Bad LLM extraction: {msg}")
                
        except Exception as e:
            # Fallback to basic regex if NVIDIA fails or no internet
            import re
            query_clean = re.sub(r'^(send|type|reply)\s+(a\s+)?(message\s+)?', 'send ', query, flags=re.IGNORECASE)
            match = re.search(r'send\s+["\']?(.*?)["\']?(?:\s+to\s+.*)?$', query_clean, re.IGNORECASE)
            msg = match.group(1).strip() if match else "Hello"

        # Type and send
        pyautogui.write(msg)
        time.sleep(0.2)
        pyautogui.press('enter')
        return f"Message sent!"
        
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