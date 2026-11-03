# 📜 History Research Helper

A free research and fact-checking assistant for history and geography YouTube videos, powered by Google Gemini's free tier.

## Features
**📖 Research pack:** type a topic and get a sourced:
- 🗓️ timeline of key events
- 👤 key figures and why they matter
- ⚠️ points where sources disagree
- ❌ popular myths to avoid
- 🎬 video angles and hooks

**🔍 Script fact-checker:** paste your script. It is split into individual claims, and each one is marked:
- ✅ supported
- ⚠️ disputed
- ❌ contradicted
- ❓ no source found

Each verdict comes with the exact sentence from the source that backs it.

**🌐 Trusted websites (optional):** besides Wikipedia, it can use Google Search to find pages on World History Encyclopedia, Smithsonian, HistoryExtra and others. It downloads the real page text from those sites.

**Built-in honesty checks:**
- The AI is only allowed to use the sources it fetched, not its own memory.
- Every quote is checked word for word against the source. If the AI made a quote up, the app warns you.

Everything can be downloaded as Markdown for your script notes.

## Setup (free)
1. Install Python 3.10+.
2. Install the libraries:
   ```bash
   pip install -r requirements.txt
   ```
3. Get a free API key at https://aistudio.google.com/apikey.
   - A Gemini app subscription is *not* needed and doesn't include API access. The free tier is enough.
   - Copy `.env.example` to `.env` and paste the key in.
4. Run the app:
   ```bash
   streamlit run app.py
   ```

Free tier notes:
- Google limits requests per minute and per day. If you hit the limit, the app tells you; just wait and try again.
- On the free tier, Google may use your prompts to improve its products, so don't paste anything private.

## Run the tests
```bash
python -m pytest
```
The tests need no internet or API key.

## How it works
```
topic / script → claims → Wikipedia (+ trusted sites) → Gemini, sources only → verdicts → quote check
```
| File | What it does |
|---|---|
| `research/sources.py` | Finds and fetches Wikipedia articles (cached in `.cache/`) |
| `research/web_sources.py` | Finds trusted web pages via Google Search and downloads their text |
| `research/llm.py` | The one place that talks to Gemini |
| `research/pack.py` | Builds the research pack |
| `research/factcheck.py` | Splits scripts into claims, checks them and verifies quotes |
| `research/export.py` | Markdown downloads |
| `evals/` | Accuracy test: 37 labelled true and false claims, plus a scorer |
| `app.py` | The Streamlit web interface |

## Roadmap
- [x] Week 1: research pack from Wikipedia
- [x] Week 2: paste a script and fact-check every claim
- [x] Week 3: trusted websites and exact supporting quotes
- [x] Week 4: accuracy test set, to measure how many false claims it catches

## Measuring accuracy (Week 4)

**Latest result (3 Nov 2026, Gemini Flash, free tier): 92% accurate**

| | Score |
|---|---|
| True claims confirmed | 18/20 |
| False claims caught | 16/17 |
| False claims wrongly marked true | **0** |
| Quotes found word for word in the source | 35/35 |

[Full report](evals/results/20261103-180711.md)

What the 3 misses were:
- **"Hampi was the capital" → contradicted.** The sources name the capital city *Vijayanagara*, whose ruins are at Hampi, so this is partly a wording problem.
- **"Third Battle of Panipat... 1761" → no source found.** The right article wasn't fetched for this topic.
- **"Great Wall visible from the Moon" → no source found.** It wasn't marked true, but it wasn't caught as a myth either.

`evals/claims.json` has 37 claims across 6 topics. I already know which are true (20) and which are false (17). To score the fact-checker, run:
```bash
python -m evals.run_eval
```
- This uses 6 Gemini requests, which is free.
- It prints a report and saves it to `evals/results/`.
- If you change a prompt, run it again and compare the scores.
- Add your own claims to `claims.json` from topics you cover.

What the scores mean:
- **True claims confirmed:** true claims marked ✅ supported.
- **False claims caught:** false claims marked ❌ contradicted or ⚠️ disputed.
- **False claims wrongly marked supported:** the worst kind of mistake. This should be 0.
- **Quotes verified:** quotes found word for word in the source, which shows whether the AI is inventing evidence.
