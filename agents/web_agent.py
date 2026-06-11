import os
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


def web_search(query: str) -> str:
    """
    Fast web search — returns Tavily's own answer + top snippet.
    No LLM synthesis step, so it's one API call only.
    """
    try:
        response = _client.search(
            query=query,
            max_results=2,
            include_answer=True,       # Tavily generates a short answer itself
        )

        # Tavily's own synthesized answer (usually 1-2 sentences)
        answer = response.get("answer", "").strip()
        if answer:
            return answer

        # Fallback: return the first result snippet
        results = response.get("results", [])
        if results:
            return results[0].get("content", "No result found.")[:400]

        return "Couldn't find relevant information."

    except Exception as e:
        return f"Search error: {e}"


def web_node(state):
    state["result"] = web_search(state["query"])
    return state