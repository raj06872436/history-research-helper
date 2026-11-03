"""History Research Helper: build sourced research packs and fact-check video scripts.

Run with:  streamlit run app.py
"""

import requests
import streamlit as st
from dotenv import load_dotenv
from google.genai import errors

from research.export import VERDICT_LABELS, factcheck_to_markdown, to_markdown
from research.factcheck import FactCheckResult, fact_check
from research.llm import has_api_key, is_daily_limit
from research.pack import ResearchPack, build_pack
from research.sources import Source, gather_sources
from research.web_sources import TRUSTED_DOMAINS, search_web

load_dotenv()

st.set_page_config(page_title="History Research Helper", page_icon="📜", layout="wide")
st.title("📜 History Research Helper")
st.caption("Every fact linked to its source, so you can check it before you publish.")


def cite(index: int, sources: list[Source]) -> str:
    """Turn a source number into a clickable markdown link."""
    if 1 <= index <= len(sources):
        return f"[[{index}]]({sources[index - 1].url})"
    return f"[{index}]"


def show_sources(sources: list[Source]) -> None:
    st.subheader("📚 Sources")
    for i, s in enumerate(sources, 1):
        st.markdown(f"{i}. [{s.title}]({s.url})")


def run_safely(task):
    """Run an AI task and turn common failures into friendly messages."""
    if not has_api_key():
        st.error("No Gemini API key found. Copy .env.example to .env and paste your free key into it.")
        st.stop()
    try:
        return task()
    except errors.ClientError as err:
        if err.code == 429 and is_daily_limit(err):
            st.error("Today's free Gemini requests are used up on every model. They reset tomorrow.")
        elif err.code == 429:
            st.error("Too many requests in one minute for the free tier. Wait a minute and try again.")
        elif err.code in (400, 401, 403) and "key" in str(err).lower():
            st.error("Your Gemini API key is wrong. Check the key in your .env file.")
        else:
            st.error(f"The AI service rejected the request: {err.message}")
    except errors.ServerError:
        st.error("Gemini is busy right now. Try again in a minute.")
    except requests.ConnectionError:
        st.error("Couldn't connect. Check your internet connection.")
    except requests.HTTPError:
        st.error("Wikipedia is busy right now. Wait a minute and try again.")
    except (ValueError, RuntimeError) as err:
        st.error(str(err))
    st.stop()


def show_pack(topic: str, pack: ResearchPack, sources: list[Source]) -> None:
    st.subheader("Summary")
    st.write(pack.summary)

    left, right = st.columns(2)
    with left:
        st.subheader("🗓️ Timeline")
        for e in pack.timeline:
            st.markdown(f"**{e.date}**: {e.event} {cite(e.source_index, sources)}")
    with right:
        st.subheader("👤 Key figures")
        for f in pack.key_figures:
            st.markdown(f"**{f.name}**: *{f.role}*  \n{f.significance} {cite(f.source_index, sources)}")

    if pack.disputed_points:
        st.subheader("⚠️ Disputed points")
        for d in pack.disputed_points:
            st.markdown(f"- {d}")

    if pack.myths:
        st.subheader("❌ Myths to avoid")
        for m in pack.myths:
            st.markdown(f"- **Myth:** {m.claim}  \n  **Reality:** {m.reality} {cite(m.source_index, sources)}")

    st.subheader("🎬 Video angles")
    for a in pack.video_angles:
        st.markdown(f"- {a}")

    show_sources(sources)
    st.download_button(
        "Download as Markdown",
        to_markdown(topic, pack, sources),
        file_name=f"research-{topic.lower().replace(' ', '-')[:40]}.md",
    )


def show_factcheck(result: FactCheckResult) -> None:
    counts = {v: sum(c.check.verdict == v for c in result.claims) for v in VERDICT_LABELS}
    for col, (verdict, label) in zip(st.columns(4), VERDICT_LABELS.items()):
        col.metric(label, counts[verdict])

    for c in result.claims:
        with st.container(border=True):
            st.markdown(f"**{VERDICT_LABELS[c.check.verdict]}**: {c.check.claim}")
            st.write(c.check.explanation)
            if c.source and c.check.quote:
                st.markdown(f"> {c.check.quote}\n\n[{c.source.title}]({c.source.url})")
                if not c.quote_verified:
                    st.warning("This quote could not be found word for word in the source. Check it yourself.")

    show_sources(result.sources)
    st.download_button("Download report as Markdown", factcheck_to_markdown(result), file_name="fact-check.md")


use_web = st.toggle(
    "Also search trusted websites",
    help="Uses Google Search to find pages on " + ", ".join(TRUSTED_DOMAINS) + ". Slower, and uses more of your free daily limit.",
)

pack_tab, check_tab = st.tabs(["📖 Research pack", "🔍 Fact-check script"])

with pack_tab:
    with st.form("topic_form"):
        topic = st.text_input("Video topic", placeholder="e.g. The Fall of the Vijayanagara Empire")
        num_sources = st.slider("Number of Wikipedia articles to use", 1, 5, 3)
        submitted = st.form_submit_button("Build research pack")

    if submitted and topic.strip():
        def build():
            with st.spinner("Finding sources..."):
                sources = gather_sources(topic, max_articles=num_sources)
                if use_web:
                    sources += search_web(topic)
            if not sources:
                raise ValueError("No sources found. Try different wording.")
            with st.spinner(f"Reading {len(sources)} sources and building your pack..."):
                return build_pack(topic, sources), sources

        pack, sources = run_safely(build)
        show_pack(topic, pack, sources)

with check_tab:
    with st.form("check_form"):
        check_topic = st.text_input("Video topic (helps find the right sources)", placeholder="e.g. Maratha Empire")
        script = st.text_area("Paste your script", height=250)
        check_submitted = st.form_submit_button("Fact-check script")

    if check_submitted and script.strip():
        def check():
            extra = []
            if use_web:
                with st.spinner("Searching trusted websites..."):
                    extra = search_web(check_topic or script[:300])
            with st.spinner("Splitting the script into claims and checking each one..."):
                return fact_check(script, check_topic, extra_sources=extra)

        show_factcheck(run_safely(check))
