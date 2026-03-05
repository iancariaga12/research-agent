import streamlit as st
import requests
import json
import os
from exporter import export_pdf, export_docx

st.set_page_config(
    page_title="Research Agent",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def load_css(path: str):
    with open(path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css("styles.css")

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

# Session state
for key, default in {
    "report": "",
    "topic_saved": "",
    "tool_count": 0,
    "format_saved": "Research Report"
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# Header
st.markdown('<h1>Research<br><i>Agent</i></h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Autonomous · Web-powered · AI-synthesized</p>', unsafe_allow_html=True)

# Input row
col1, col2, col3 = st.columns([3, 1, 1])
with col1:
    topic = st.text_input("Research Topic")
with col2:
    report_format = st.selectbox(
        "Format",
        ["Research Report", "Essay", "Briefing Doc"]
    )
with col3:
    st.markdown("<br>", unsafe_allow_html=True)
    research_clicked = st.button(
        "Research →",
        disabled=not topic,
        use_container_width=True
    )

# Run research
if research_clicked and topic:
    st.session_state.update({
        "report": "",
        "topic_saved": topic,
        "format_saved": report_format,
        "tool_count": 0
    })

    report = ""
    tool_calls = []

    with st.status("Agent initializing...", expanded=True) as status:
        with requests.post(
            f"{API_URL}/research",
            json={"topic": topic, "format": report_format},
            stream=True
        ) as response:
            for line in response.iter_lines():
                if line:
                    raw = line.decode("utf-8")
                    if raw.startswith("data: "):
                        data = json.loads(raw[6:])

                        if data["type"] == "tool_call":
                            tool_calls.append(data["content"])
                            st.markdown(
                                f'<div class="tool-call">→ <span>{data["content"]}</span></div>',
                                unsafe_allow_html=True
                            )
                            status.update(label=f"🔍 {data['content'][:60]}...")

                        elif data["type"] == "report":
                            st.session_state["report"] = data["content"]
                            st.session_state["tool_count"] = len(tool_calls)

                        elif data["type"] == "error":
                            st.warning(data["content"])

        status.update(
            label=f"✓ Research complete — {len(tool_calls)} sources consulted",
            state="complete",
            expanded=False
        )

# Display report
if st.session_state["report"]:
    report = st.session_state["report"]
    saved_topic = st.session_state["topic_saved"]
    tool_count = st.session_state["tool_count"]
    saved_format = st.session_state["format_saved"]

    pdf_bytes = export_pdf(report, saved_topic)
    docx_bytes = export_docx(report, saved_topic)

    col1, col2, col3 = st.columns([5, 1, 1])
    with col1:
        st.markdown(f"""
        <div class="report-header">
            <div class="format-tag">{saved_format}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.download_button(
            label="↓ PDF",
            data=pdf_bytes,
            file_name=f"{saved_topic[:30].replace(' ', '_')}_report.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        st.download_button(
            label="↓ Word",
            data=docx_bytes,
            file_name=f"{saved_topic[:30].replace(' ', '_')}_report.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )

    st.markdown('<div class="report-body-marker"></div>', unsafe_allow_html=True)
    st.markdown(report)

    st.markdown(
        f'<div class="status-bar">Generated · {len(report)} characters · {tool_count} tool calls · {saved_format}</div>',
        unsafe_allow_html=True
    )