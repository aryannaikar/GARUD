from tools.chroma_tools import save_memory, delete_memory

def memory_node(state):
    query = state["query"].lower()
    
    if "forget" in query or "delete memory" in query:
        result = delete_memory(query)
    else:
        result = save_memory(query)
        
    state["result"] = result
    return state
