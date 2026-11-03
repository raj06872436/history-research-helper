# 📜 History Research Helper

A research assistant for history and geography YouTube videos.
Type a topic and get a **research pack**, with every fact linked to the Wikipedia article it came from:

- 🗓️ Timeline of key events
- 👤 Key figures and why they matter
- ⚠️ Points where sources disagree
- ❌ Popular myths to avoid
- 🎬 Video angles and hooks
- 📥 Download as Markdown for your script notes

The AI is told to write **only from the sources it fetched**, never from memory, so you can check every claim.

## Setup

1. Install Python 3.10+.
2. Install the libraries:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and paste in your Anthropic API key (get one at https://console.anthropic.com).
4. Run the app:
   ```bash
   streamlit run app.py
   ```

## Run the tests
```bash
python -m pytest
```
The tests need no internet or API key.

## How it works
```
topic → Wikipedia search → article text → Claude (sources only) → structured research pack
```
- `research/sources.py`: finds and fetches Wikipedia articles (cached in `.cache/` so repeat lookups are free)
- `research/pack.py`: sends the sources to Claude and gets back a validated research pack
- `app.py`: the Streamlit web interface

## Roadmap
- [x] Week 1: Research pack from Wikipedia
- [ ] Week 2: Paste a script and fact-check every claim (✅ / ⚠️ / ❌)
- [ ] Week 3: More sources (Britannica, archive.org) and exact supporting quotes
- [ ] Week 4: Accuracy test set, to measure how many false claims it catches
