"""History Research Helper: build sourced research packs and fact-check video scripts.

Run with:  streamlit run app.py
"""

from html import escape

import requests
import streamlit as st
from dotenv import load_dotenv
from google.genai import errors

from research import examples, ui
from research.export import factcheck_to_markdown, to_markdown
from research.factcheck import FactCheckResult, fact_check
from research.llm import has_api_key, is_daily_limit
from research.pack import ResearchPack, build_pack
from research.sources import Source, gather_sources
from research.web_sources import TRUSTED_DOMAINS, search_web

load_dotenv()

st.set_page_config(page_title="History Research Helper", page_icon="🗺️", layout="wide")
st.markdown(ui.CSS, unsafe_allow_html=True)
st.markdown(ui.header(), unsafe_allow_html=True)


def show(html: str) -> None:
    st.markdown(html, unsafe_allow_html=True)


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


def show_pack(topic: str, pack: ResearchPack, sources: list[Source], example: bool = False) -> None:
    if example:
        st.info(f"This is a saved example for “{topic}”. Type your own topic above to build a new pack.")
    show(ui.pack_html(pack, sources))
    st.write("")
    st.download_button(
        "Download as Markdown",
        to_markdown(topic, pack, sources),
        file_name=f"research-{topic.lower().replace(' ', '-')[:40]}.md",
    )


def show_factcheck(result: FactCheckResult, example_script: str = "") -> None:
    if example_script:
        st.info("This is a saved example. It checked this script, which has a planted mistake:")
        show(f'<blockquote class="example-script">{escape(example_script)}</blockquote>')
    show(ui.factcheck_html(result))
    st.write("")
    st.download_button("Download report as Markdown", factcheck_to_markdown(result), file_name="fact-check.md")


use_web = st.toggle(
    "Also search trusted websites",
    help="Uses Google Search to find pages on " + ", ".join(TRUSTED_DOMAINS) + ". Slower, and uses more of your free daily limit.",
)

pack_tab, check_tab = st.tabs(["Research pack", "Fact-check a script"])

# Results are kept in session_state so they survive reruns, like clicking a download button.
with pack_tab:
    with st.form("topic_form"):
        topic = st.text_input("What's your video about?", placeholder="The Fall of the Vijayanagara Empire")
        num_sources = st.slider("Wikipedia articles to read", 1, 5, 3)
        submitted = st.form_submit_button("Build research pack")

    if submitted and topic.strip():
        def build():
            with st.spinner("Finding sources..."):
                sources = gather_sources(topic, max_articles=num_sources)
                if use_web:
                    sources += search_web(topic)
            if not sources:
                raise ValueError("No Wikipedia articles matched that topic. Try a broader or differently worded topic.")
            with st.spinner(f"Reading {len(sources)} sources and building your pack..."):
                return build_pack(topic, sources), sources

        pack, sources = run_safely(build)
        st.session_state["pack"] = (topic, pack, sources, False)

    if "pack" in st.session_state:
        show_pack(*st.session_state["pack"])
    else:
        show(ui.empty_state(
            "You'll get a short summary, a timeline, the key people, points where sources disagree, "
            "myths to avoid and ideas for your video. Every fact links to the article it came from."
        ))
        if st.button("Show an example"):
            st.session_state["pack"] = (*examples.load_pack(), True)
            st.rerun()

with check_tab:
    with st.form("check_form"):
        check_topic = st.text_input("What's the video about?", placeholder="Vijayanagara Empire",
                                    help="Helps find the right Wikipedia articles.")
        script = st.text_area("Your script", height=220, placeholder="Paste the narration you want to check.")
        check_submitted = st.form_submit_button("Fact-check script")

    if check_submitted and script.strip():
        def check():
            extra = []
            if use_web:
                with st.spinner("Searching trusted websites..."):
                    extra = search_web(check_topic or script[:300])
            with st.spinner("Splitting the script into claims and checking each one..."):
                return fact_check(script, check_topic, extra_sources=extra)

        st.session_state["check"] = (run_safely(check), "")

    if "check" in st.session_state:
        show_factcheck(*st.session_state["check"])
    else:
        show(ui.empty_state(
            "Each factual claim in your script is marked supported, disputed, contradicted or not found, "
            "with the sentence from the source that backs it up."
        ))
        if st.button("Show an example", key="check_example"):
            script_text, result = examples.load_check()
            st.session_state["check"] = (result, script_text)
            st.rerun()
