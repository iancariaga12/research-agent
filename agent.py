import os
import json
from groq import Groq
from dotenv import load_dotenv
from tools.search import search_web
from tools.scraper import scrape_page

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Define the tools for the LLM
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the web for information on a topic. Use this to find relevant sources.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "scrape_page",
            "description": "Scrape the full content of a webpage given its URL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL of the page to scrape"
                    }
                },
                "required": ["url"]
            }
        }
    }
]

def run_agent(topic: str) -> str:
    print(f"\n🔍 Researching: {topic}\n")

    messages = [
        {
             "role": "system",
             "content": """You are an autonomous research agent. When given a topic:
1. Search the web for relevant information (1-2 searches max)
2. Scrape 2-3 of the most relevant pages
3. Write a detailed, structured research report based on what you found

Be selective — only scrape the most promising URLs. Do not over-search."""
        },
        {
            "role": "user",
            "content": f"Research this topic and write a detailed report: {topic}"
        }
    ]

    max_iterations = 10
    iteration = 0

    while iteration < max_iterations:
        iteration += 1

        try:
            response = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=messages,
                tools=tools,
                tool_choice="auto"
            )
        except Exception as e:
            print(f"⚠️ API error: {e}. Retrying without tools...")
            response = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=messages
            )

        message = response.choices[0].message

        if not message.tool_calls:
            print("Final Report:\n")
            print(message.content)
            return message.content

        messages.append({
            "role": "assistant",
            "content": message.content,
            "tool_calls": message.tool_calls
        })

        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)

            print(f"Calling tool: {tool_name} with args: {tool_args}")

            if tool_name == "search_web":
                result = search_web(**tool_args)
            elif tool_name == "scrape_page":
                result = scrape_page(**tool_args)
            else:
                result = "Tool not found"

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result)
            })

    return "Max iterations reached."
