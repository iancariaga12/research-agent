from tavily import TavilyClient
from dotenv import load_dotenv
import os

load_dotenv()

client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

def search_web(query: str, max_results: int = 5, **kwargs) -> list[dict]:
    response = client.search(query, max_results=max_results)
    results = response["results"]
    return [{"title": r["title"], "url": r["url"], "content": r["content"][:200]} for r in results]

