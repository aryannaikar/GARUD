import os
import webbrowser
import subprocess


def open_youtube(search_query: str = ""):
    if search_query:
        import urllib.parse
        import urllib.request
        import re
        encoded = urllib.parse.quote_plus(search_query)
        try:
            html = urllib.request.urlopen(f"https://www.youtube.com/results?search_query={encoded}")
            video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
            if video_ids:
                webbrowser.open(f"https://www.youtube.com/watch?v={video_ids[0]}")
                return f"Playing '{search_query}' on YouTube..."
        except Exception:
            pass
        # Fallback to search results if auto-play extraction fails
        webbrowser.open(f"https://www.youtube.com/results?search_query={encoded}")
        return f"Searching '{search_query}' on YouTube..."
        
    webbrowser.open("https://www.youtube.com")
    return "Opening YouTube..."


def open_google():
    webbrowser.open("https://www.google.com")
    return "Opening Google..."


def open_chrome():
    try:
        subprocess.Popen(
            r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        )
        return "Opening Chrome..."
    except Exception as e:
        return f"Could not open Chrome: {e}"


def open_vscode():
    try:
        subprocess.Popen(
            r"C:\Users\Aryan Naikar\AppData\Local\Programs\Microsoft VS Code\Code.exe"
        )
        return "Opening VS Code..."
    except Exception as e:
        return f"Could not open VS Code: {e}"


def open_antigravity():
    try:
        subprocess.Popen(
            r"C:\Users\Aryan Naikar\AppData\Local\Programs\Antigravity\Antigravity.exe"
        )
        return "Opening Antigravity..."
    except Exception as e:
        return f"Could not open Antigravity: {e}"

def open_whatsapp(person_name: str = ""):
    try:
        os.system("start whatsapp:")
        if person_name:
            import time
            import pyautogui
            # Give WhatsApp a moment to launch and come into focus
            time.sleep(2.5)
            # WhatsApp Desktop shortcut to focus search is Ctrl+F
            pyautogui.hotkey('ctrl', 'f')
            time.sleep(0.5)
            # Type the person's name
            pyautogui.write(person_name)
            time.sleep(0.8)
            # Press enter to open the top result
            pyautogui.press('enter')
            return f"Opening WhatsApp and navigating to {person_name}'s chat..."
        return "Opening WhatsApp..."
    except Exception as e:
        return f"Could not open WhatsApp: {e}"