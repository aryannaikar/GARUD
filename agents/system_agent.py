import os
import psutil
import pyautogui
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv

load_dotenv()
_sys_llm = ChatNVIDIA(
    model="nvidia/nemotron-mini-4b-instruct",
    api_key=os.getenv("NVIDIA_API_KEY"),
    temperature=0.4
)

def handle_system_request(query: str) -> str:
    query = query.lower()
    
    if "screenshot" in query:
        desktop_path = os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop")
        if not os.path.exists(desktop_path):
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        
        save_path = os.path.join(desktop_path, "garud_screenshot.png")
        screenshot = pyautogui.screenshot()
        screenshot.save(save_path)
        return f"Screenshot taken and saved to your desktop as 'garud_screenshot.png'."

    if any(kw in query for kw in ["status", "stats", "battery", "cpu", "ram", "memory usage", "disk"]):
        # Gather diagnostics
        cpu_percent = psutil.cpu_percent(interval=0.5)
        ram = psutil.virtual_memory()
        ram_gb_used = round(ram.used / (1024 ** 3), 1)
        ram_gb_total = round(ram.total / (1024 ** 3), 1)
        
        battery = psutil.sensors_battery()
        if battery:
            batt_plugged = "Plugged In" if battery.power_plugged else "On Battery"
            batt_str = f"{battery.percent}% ({batt_plugged})"
        else:
            batt_str = "Desktop PC (No Battery)"
        
        disk = psutil.disk_usage('C:\\')
        disk_percent = disk.percent

        sys_prompt = f"""
        You are Garud's system diagnostics module. 
        Read these raw system stats and provide a sleek, fast, JARVIS-style status report (1-2 sentences max).
        CPU: {cpu_percent}%
        RAM: {ram_gb_used}GB / {ram_gb_total}GB ({ram.percent}%)
        Battery: {batt_str}
        Disk: {disk_percent}%
        """
        
        resp = _sys_llm.invoke([
            SystemMessage(content=sys_prompt),
            HumanMessage(content=query)
        ])
        return resp.content

    return "System module active, but unable to parse that specific command."

def system_node(state):
    state["result"] = handle_system_request(state["query"])
    return state
