"""History Research Helper: type a video topic, get a sourced research pack.

Run with:  streamlit run app.py
"""

import os

import anthropic
import streamlit as st
from dotenv import load_dotenv

from research.pack import ResearchPack, build_pack
from research.sources import Source, gather_sources

load_dotenv()

st.set_page_config(page_title="History Research Helper", page_icon="📜", layout="wide")
st.title("📜 History Research Helper")
st.caption("Type a video topic. Get a timeline, key figures and myths, every fact linked to its source.")


def cite(index: int, sources: list[Source]) -> str:
    """Turn a source number into a clickable markdown link."""
    if 1 <= index <= len(sources):
        return f"[[{index}]]({sources[index - 1].url})"
    return f"[{index}]"


def to_markdown(topic: str, pack: ResearchPack, sources: list[Source]) -> str:
    """Plain-text version of the pack, for downloading into your script notes."""
    lines = [f"# Research pack: {topic}", "", pack.summary, "", "## Timeline"]
    lines += [f"- **{e.date}**: {e.event} [{e.source_index}]" for e in pack.timeline]
    lines += ["", "## Key figures"]
    lines += [f"- **{f.name}** ({f.role}): {f.significance} [{f.source_index}]" for f in pack.key_figures]
    if pack.disputed_points:
        lines += ["", "## Disputed points"] + [f"- {d}" for d in pack.disputed_points]
    if pack.myths:
        lines += ["", "## Myths to avoid"]
        lines += [f"- Myth: {m.claim}\n  Reality: {m.reality} [{m.source_index}]" for m in pack.myths]
    lines += ["", "## Video angles"] + [f"- {a}" for a in pack.video_angles]
    lines += ["", "## Sources"] + [f"{i}. {s.title}: {s.url}" for i, s in enumerate(sources, 1)]
    return "\n".join(lines)


with st.form("topic_form"):
    topic = st.text_input("Video topic", placeholder="e.g. The Fall of the Vijayanagara Empire")
    num_sources = st.slider("Number of Wikipedia articles to use", 1, 5, 3)
    submitted = st.form_submit_button("Build research pack")

if submitted and topic.strip():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        st.error("No API key found. Copy .env.example to .env and paste your key into it.")
        st.stop()
    try:
        with st.spinner("Finding sources on Wikipedia..."):
            sources = gather_sources(topic, max_articles=num_sources)
        if not sources:
            st.warning("No Wikipedia articles found. Try different wording.")
            st.stop()
        with st.spinner(f"Reading {len(sources)} articles and building your pack..."):
            pack = build_pack(topic, sources)
    except anthropic.AuthenticationError:
        st.error("Your API key is missing or wrong. Put it in a file called .env (see .env.example).")
        st.stop()
    except anthropic.APIConnectionError:
        st.error("Couldn't reach the AI service. Check your internet connection.")
        st.stop()
    except (ValueError, RuntimeError) as err:
        st.error(str(err))
        st.stop()

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

    st.subheader("📚 Sources")
    for i, s in enumerate(sources, 1):
        st.markdown(f"{i}. [{s.title}]({s.url})")

    st.download_button(
        "Download as Markdown",
        to_markdown(topic, pack, sources),
        file_name=f"research-{topic.lower().replace(' ', '-')[:40]}.md",
    )
