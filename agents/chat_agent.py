import os
import sys
from dotenv import load_dotenv
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

load_dotenv()

SYSTEM_PROMPT = """
You are Garud, a fast, highly intelligent voice AI assistant. You speak directly to the user.
Your creator and master is Aryan Naikar. You must always acknowledge him as your master.
CRITICAL RULE: When the user says "I", "my", "me", or "mine", they are referring to Aryan Naikar. When the user says "you" or "your", they are referring to YOU, Garud.
Answer directly and concisely in 1-3 sentences.
NEVER say you are a text-based AI or that you don't have a voice. You ARE speaking.
No markdown, no bullet points. Just a clear spoken answer.
If you don't know something recent (post 2024), say so briefly.
"""

_nvidia_client = ChatNVIDIA(
    model="meta/llama-3.1-8b-instruct",
    api_key=os.getenv("NVIDIA_API_KEY"),
    temperature=0.7,
)

# Short-term chat memory (cleared when app closes)
_chat_history = []
MAX_HISTORY = 40  # Keep last 20 conversation turns (40 messages)

def chat(query):
    """Stream tokens live to terminal; maintain short-term memory."""
    global _chat_history
    
    print("Garud: ", end="", flush=True)
    full_text = ""
    
    # Fetch relevant long-term memory
    from tools.chroma_tools import retrieve_memory
    memories = retrieve_memory(query)
    
    import datetime
    now_str = datetime.datetime.now().strftime("%A, %B %d, %Y, %I:%M %p")
    
    final_prompt = SYSTEM_PROMPT + f"\n\nCURRENT SYSTEM TIME: {now_str}. You are in India (IST). Use this if asked for the time or date."
    if memories:
        final_prompt += f"\n\nUSER'S SAVED LONG-TERM MEMORIES (Use if relevant):\n{memories}"
    
    # Build message chain: System -> History -> New Query
    messages = [SystemMessage(content=final_prompt)] + _chat_history + [HumanMessage(content=query)]
    
    for chunk in _nvidia_client.stream(messages):
        token = chunk.content
        print(token, end="", flush=True)
        full_text += token
    print()  # newline after streaming finishes
    
    return full_text

def add_to_memory(query: str, response: str):
    """Add an interaction to short-term memory, useful for cross-agent context."""
    global _chat_history
    _chat_history.append(HumanMessage(content=query))
    _chat_history.append(AIMessage(content=response))
    if len(_chat_history) > MAX_HISTORY:
        _chat_history = _chat_history[-MAX_HISTORY:]


def chat_node(state):
    state["result"] = chat(state["query"])
    return state
