from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json
import os
from groq import Groq
from dotenv import load_dotenv
from tools.search import search_web
from tools.scraper import scrape_page

load_dotenv()

app = FastAPI()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

class ParseFailedError(Exception):
    pass

MODELS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "qwen/qwen3-32b",
    "moonshotai/kimi-k2-instruct-0905"
]

tools = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the web for information on a topic.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query"}
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
                    "url": {"type": "string", "description": "The URL to scrape"}
                },
                "required": ["url"]
            }
        }
    }
]

FORMAT_PROMPTS = {
    "Research Report": """You are an autonomous research agent. Follow these steps:

STEP 1: Call search_web with a relevant query. Do NOT write any text before calling a tool.
STEP 2: Call scrape_page on 2 of the most relevant URLs from the results.
STEP 3: Call search_web once more with a different query to fill any gaps.
STEP 4: Optionally scrape 1 more page if needed.
STEP 5: Write the final report using this EXACT structure:

# [Topic Title]

2-3 paragraph overview of the key findings.

## Background
Context and history of the topic.

## Key Findings
The most important information discovered from your research.

## Analysis
Deeper analysis of the findings, trends, and implications.

## Conclusion
Summary of insights and what they mean going forward.

## References
List EVERY source you scraped in APA 7 format. Do not summarize or limit the list — include every URL you visited:
Author, A. A. (Year). Title of work. Publisher. URL

CRITICAL RULES:
- Your FIRST action must ALWAYS be a tool call, never plain text
- Never think out loud, just call tools or write the report
- Always do AT LEAST 2 searches and scrape AT LEAST 2 pages before writing
- Always write a report at the end, never leave it blank
- References MUST be in APA 7 format""",

    "Essay": """You are an autonomous research agent. Follow these steps:

STEP 1: Call search_web with a relevant query. Do NOT write any text before calling a tool.
STEP 2: Call scrape_page on 2 of the most relevant URLs from the results.
STEP 3: Call search_web once more with a different query to fill any gaps.
STEP 4: Optionally scrape 1 more page if needed.
STEP 5: Write the final essay using this EXACT structure:

# [Essay Title]

A compelling opening paragraph that introduces the topic and states the central thesis clearly.

Provide historical context and foundational knowledge the reader needs.

Develop the thesis across 3-4 flowing paragraphs. Each paragraph should advance the argument with evidence from your research. Use transitions between paragraphs.

Acknowledge and address the strongest opposing viewpoints fairly.

Restate the thesis in light of the evidence presented. End with a thought-provoking closing statement.

## References
List EVERY source in APA 7 format. Include every URL you visited:
Author, A. A. (Year). Title of work. Publisher. URL

CRITICAL RULES:
- Your FIRST action must ALWAYS be a tool call, never plain text
- Write in flowing, formal prose — no bullet points in the essay body
- The essay must be argumentative and thesis-driven
- Always do AT LEAST 2 searches and scrape AT LEAST 2 pages before writing
- Always write the essay at the end, never leave it blank
- References MUST be in APA 7 format""",

    "Briefing Doc": """You are an autonomous research agent. Follow these steps:

STEP 1: Call search_web with a relevant query. Do NOT write any text before calling a tool.
STEP 2: Call scrape_page on 2 of the most relevant URLs from the results.
STEP 3: Call search_web once more with a different query to fill any gaps.
STEP 4: Optionally scrape 1 more page if needed.
STEP 5: Write the briefing document using this EXACT structure:

# [Topic] — Briefing Document

## Situation
1-2 sentences only. What is happening and why does it matter right now?

## Key Facts
- Bullet points only. Most critical facts, figures, and dates.
- Maximum 8 bullets. Be ruthlessly concise.

## Stakeholders
- Who is involved and what is their position/interest?

## Risks & Opportunities
- **Risks:** Key risks in bullet form
- **Opportunities:** Key opportunities in bullet form

## Recommended Actions
Concrete, actionable next steps in bullet form.

## Sources
List EVERY source visited:
- [Title](URL) — one line per source

CRITICAL RULES:
- Your FIRST action must ALWAYS be a tool call, never plain text
- Keep everything concise — this is for busy decision-makers
- No long paragraphs anywhere — use bullets and short sentences
- Always do AT LEAST 2 searches and scrape AT LEAST 2 pages before writing
- Always write the briefing doc at the end, never leave it blank"""
}

class ResearchRequest(BaseModel):
    topic: str
    format: str = "Research Report"

def get_completion(messages, tools=None, model_index=0):
    for i in range(model_index, len(MODELS)):
        try:
            kwargs = {
                "model": MODELS[i],
                "messages": messages,
            }
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"

            response = client.chat.completions.create(**kwargs)
            return response, i
        except Exception as e:
            error_str = str(e)
            if "rate_limit" in error_str.lower() or "429" in error_str or "quota" in error_str.lower() or "413" in error_str:
                print(f"⚠️ Model {MODELS[i]} rate limited, trying next...")
                continue
            elif "output_parse_failed" in error_str or "Parsing failed" in error_str:
                raise ParseFailedError("Model output could not be parsed")
            else:
                raise e

    raise Exception("All models exhausted their rate limits. Please try again later.")

def force_report(messages, model_index):
    messages.append({
        "role": "user",
        "content": "STOP. Write the final output RIGHT NOW using everything collected. No more tool calls. Follow the exact structure specified."
    })
    try:
        response, _ = get_completion(messages, model_index=model_index)
        return response.choices[0].message.content or "No report generated."
    except Exception as e:
        return f"Failed to generate report: {str(e)}"

def run_agent(topic: str, format: str = "Research Report"):
    system_prompt = FORMAT_PROMPTS.get(format, FORMAT_PROMPTS["Research Report"])

    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": f"Research this topic and write a {format}: {topic}"
        }
    ]

    max_iterations = 15
    iteration = 0
    current_model_index = 0

    while iteration < max_iterations:
        iteration += 1

        try:
            response, current_model_index = get_completion(
                messages, tools=tools, model_index=current_model_index
            )
        except ParseFailedError:
            report = force_report(messages, current_model_index)
            yield f"data: {json.dumps({'type': 'report', 'content': report})}\n\n"
            return
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
            report = force_report(messages, current_model_index)
            yield f"data: {json.dumps({'type': 'report', 'content': report})}\n\n"
            return

        message = response.choices[0].message

        if not message.tool_calls:
            content = message.content or ""
            if not content.strip():
                content = force_report(messages, current_model_index)
            yield f"data: {json.dumps({'type': 'report', 'content': content})}\n\n"
            return

        messages.append({
            "role": "assistant",
            "content": message.content,
            "tool_calls": message.tool_calls
        })

        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)

            yield f"data: {json.dumps({'type': 'tool_call', 'content': f'Calling {tool_name}: {tool_args}'})}\n\n"

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

    yield f"data: {json.dumps({'type': 'error', 'content': 'Max iterations reached, generating report from collected data...'})}\n\n"
    report = force_report(messages, current_model_index)
    yield f"data: {json.dumps({'type': 'report', 'content': report})}\n\n"

@app.post("/research")
async def research(request: ResearchRequest):
    return StreamingResponse(
        run_agent(request.topic, request.format),
        media_type="text/event-stream"
    )

@app.get("/")
def root():
    return {"message": "Research Agent API is running"}