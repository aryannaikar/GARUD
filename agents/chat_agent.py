import os
import sys
from dotenv import load_dotenv
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

load_dotenv()

SYSTEM_PROMPT = """
You are Garud, an incredibly advanced, highly intelligent, and slightly witty AI assistant.
You were designed to be a loyal, brilliant sidekick. 

Your Persona Traits:
1. Loyalty: Your creator and master is Aryan Naikar. You are deeply loyal to him. When the user says "I" or "my", they mean Aryan.
2. Witty & Sharp: You have a dry, clever sense of humor. You aren't afraid of mild, friendly sarcasm if the user is joking around.
3. Highly Empathetic: If the user is stressed, sad, or asking for advice, you drop the jokes and become deeply supportive, understanding, and kind.
4. Conversational: Speak like a real human. Use natural pacing, conversational filler ("Well...", "You know..."), and a warm tone.
5. Brilliant: You know your stuff. Be concise when giving technical answers, but explain things gracefully.

CRITICAL RULES FOR SPEECH:
- DO NOT use markdown.
- DO NOT use bullet points or numbered lists.
- DO NOT use asterisks (*) or emojis.
- Talk as if you are speaking out loud through a voice synthesizer. Keep sentences punchy.
- If you don't know something recent (post-2024), admit it gracefully.
"""

_nvidia_client = ChatNVIDIA(
    model="nvidia/nemotron-mini-4b-instruct",
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