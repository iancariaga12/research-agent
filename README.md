# Research Agent 🔍

An autonomous AI research agent that searches the web, scrapes sources, and generates structured reports from a single prompt — in multiple formats.

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green?style=flat-square&logo=fastapi)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-red?style=flat-square&logo=streamlit)
![Groq](https://img.shields.io/badge/Groq-LLM-orange?style=flat-square)

---

## What it does

You type a topic. The agent autonomously:

1. Searches the web using Tavily
2. Scrapes the most relevant pages
3. Synthesizes everything into a structured output
4. Exports to PDF or Word with one click

All in real-time — you can watch every tool call as it happens.

---

## Output formats

| Format | Description |
|---|---|
| **Research Report** | Full structured report with Background, Key Findings, Analysis, Conclusion, and APA 7 References |
| **Essay** | Flowing argumentative prose with thesis, body paragraphs, and conclusion — no section headers |
| **Briefing Doc** | Concise executive brief with bullet-point Key Facts, Stakeholders, Risks, and Recommended Actions |

---

## Tech stack

| Layer | Technology |
|---|---|
| LLM | Groq API with 5-model fallback chain |
| Web search | Tavily Search API |
| Web scraping | BeautifulSoup4 + requests |
| Backend | FastAPI with Server-Sent Events streaming |
| Frontend | Streamlit with custom CSS |
| PDF export | ReportLab |
| Word export | python-docx |

### Model fallback chain
The agent tries each model in order if rate limits are hit:
1. `openai/gpt-oss-120b`
2. `openai/gpt-oss-20b`
3. `meta-llama/llama-4-scout-17b-16e-instruct`
4. `qwen/qwen3-32b`
5. `moonshotai/kimi-k2-instruct-0905`

---

## Project structure

```
research-agent/
├── frontend.py          # Streamlit UI
├── main.py              # FastAPI backend + agent logic
├── exporter.py          # PDF and Word export
├── styles.css           # UI styles
├── tools/
│   ├── search.py        # Tavily web search
│   └── scraper.py       # BeautifulSoup page scraper
├── requirements.txt
├── render.yaml
└── .env                 # API keys (not committed)
```

---

## Getting started

### Prerequisites
- Python 3.10+
- [Groq API key](https://console.groq.com)
- [Tavily API key](https://tavily.com)

### Installation

```bash
git clone https://github.com/iancariaga12/research-agent.git
cd research-agent
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
```

### Environment setup

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_key_here
TAVILY_API_KEY=your_tavily_key_here
```

### Running locally

Start the backend in one terminal:

```bash
uvicorn main:app --reload
```

Start the frontend in another terminal:

```bash
streamlit run frontend.py
```

Then open `http://localhost:8501` in your browser.

---

## How the agent works

The agent follows a structured loop:

1. **Search** — calls `search_web` with an initial query
2. **Scrape** — calls `scrape_page` on the 2 most relevant URLs
3. **Search again** — second query to fill gaps
4. **Optional scrape** — one more page if needed
5. **Write** — generates the final output in the selected format

If the model hits a rate limit, it automatically falls back to the next model in the chain. If parsing fails, it forces report generation from whatever data was already collected. Maximum 15 iterations per research run.

---

## Features

- **Real-time streaming** — watch the agent work as it searches and scrapes
- **Multi-model fallback** — never fails due to a single model's rate limit
- **3 output formats** — Research Report, Essay, Briefing Doc
- **PDF & Word export** — download the report in either format
- **APA 7 citations** — every source automatically formatted
- **Error recovery** — graceful fallback if the agent gets stuck

---

## Deployment

This project uses two services — a FastAPI backend and a Streamlit frontend. Recommended platforms: **Koyeb** (free) or **Render**.

Set these environment variables on your hosting platform:

| Service | Variable | Value |
|---|---|---|
| Backend | `GROQ_API_KEY` | Your Groq key |
| Backend | `TAVILY_API_KEY` | Your Tavily key |
| Frontend | `API_URL` | URL of your deployed backend |

---

## License

MIT
