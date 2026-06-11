import os
import chromadb
from chromadb.utils import embedding_functions
import uuid

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "memory_db")

# Use a fast local embedding model (downloads automatically on first use)
_ef = embedding_functions.DefaultEmbeddingFunction()

# Initialize Persistent Client
_client = chromadb.PersistentClient(path=DB_PATH)

# Get or create the memory collection
_collection = _client.get_or_create_collection(
    name="garud_memory",
    embedding_function=_ef
)


def save_memory(text: str) -> str:
    """Save a fact to long-term memory."""
    # Clean the keyword if present
    clean_text = text.lower().replace("remember this", "").replace("remember that", "").replace("remember", "").strip()
    if clean_text.startswith(":") or clean_text.startswith("-"):
        clean_text = clean_text[1:].strip()
        
    if not clean_text:
        return "Please tell me what exactly you want me to remember."
        
    # Generate a unique ID
    mem_id = str(uuid.uuid4())
    
    try:
        _collection.add(
            documents=[clean_text],
            ids=[mem_id]
        )
        return f"Got it. I will remember: '{clean_text}'"
    except Exception as e:
        if "timed out" in str(e).lower() or "timeout" in str(e).lower():
            return "I am currently downloading my long-term memory AI model in the background. It might take a few minutes. Please try saving this again shortly!"
        return f"Error saving memory: {e}"


def retrieve_memory(query: str, top_k: int = 3) -> str:
    """Fetch relevant long-term memories based on the query."""
    if _collection.count() == 0:
        return ""
        
    results = _collection.query(
        query_texts=[query],
        n_results=min(top_k, _collection.count())
    )
    
    documents = results.get("documents", [])
    if not documents or not documents[0]:
        return ""
        
    # Combine retrieved memories into a single string
    memories = "\n".join([f"- {doc}" for doc in documents[0]])
    return memories

def delete_memory(text: str) -> str:
    """Delete a specific fact from long-term memory."""
    clean_text = text.lower().replace("forget this", "").replace("forget that", "").replace("forget", "").strip()
    
    if not clean_text:
        return "Please tell me exactly what you want me to forget."
        
    if _collection.count() == 0:
        return "My memory banks are currently empty."
        
    # Search for the closest matching memory
    results = _collection.query(
        query_texts=[clean_text],
        n_results=1
    )
    
    documents = results.get("documents", [])
    ids = results.get("ids", [])
    
    if not documents or not documents[0]:
        return "I couldn't find any memory matching that description."
        
    found_doc = documents[0][0]
    found_id = ids[0][0]
    
    try:
        _collection.delete(ids=[found_id])
        return f"I have deleted the following memory: '{found_doc}'"
    except Exception as e:
        return f"Error deleting memory: {e}"
