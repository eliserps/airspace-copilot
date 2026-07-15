# airspace-copilot

An AI copilot for airspace monitoring. It reads live air traffic and aviation weather and explains what’s happening in plain language, in English and Brazilian Portuguese.

This is **not** a flight tracker. A map shows *where* planes are; this project uses AI to explain *what is happening and why*. The map is the frame — the AI is the product.

## Why

Air traffic and aviation weather data are public, abundant and unreadable. A report like `SBPA 120300Z 23005KT 4000 BR OVC003 15/15 Q1013` only makes sense to trained pilots. This project turns that raw data into clear, grounded, bilingual explanations.

## What it does today

- **Live traffic** — fetches real aircraft data from the OpenSky Network (OAuth2), filtered to a geographic region
- **Airspace briefing** — generates a natural-language summary of the current airspace, in EN and PT-BR
- **METAR decoding (RAG)** — translates raw aviation weather codes into plain language, grounded in official reference documentation using retrieval, so the model explains from the source instead of guessing

## Architecture

The project is built as independent modules, each with a single responsibility:

| Module | Responsibility |
|———|-—————|
| `config.py` | Loads secrets and configuration |
| `opensky.py` | Client for the live air traffic API (OAuth2) |
| `weather.py` | Client for the aviation weather API (METAR) |
| `llm.py` | LLM provider adapter — swappable in one file |
| `rag.py` | Knowledge ingestion + semantic search (Chroma) |
| `briefing.py` | Airspace briefing logic |
| `decoder.py` | RAG-grounded METAR decoding |
| `main.py` | Entry point |

The LLM layer is deliberately isolated: the project was validated by switching providers without touching the rest of the code.

## Known limitations

- **Partial coverage.** OpenSky relies on volunteer-operated receivers. Coverage is strong over Europe and North America and sparser elsewhere, so the data shows *detected* aircraft, not all traffic. The system always states this.
- **RAG reduces hallucination, it doesn’t eliminate it.** Grounding the model in documentation improves accuracy, but factual errors still occur. Automated evaluation is on the roadmap to measure and control this.

## Tech stack

Python · Chroma (vector database) · OpenSky Network API · Aviation Weather Center API · LLM via provider API

## Roadmap

- ✅ Live traffic + bilingual briefing
- ✅ RAG-based METAR decoding
- 🔜 Agent with tool calling (natural-language questions about the airspace)
- 🔜 Automated evaluation (golden dataset) + guardrails
- 🔜 REST API (FastAPI) + React frontend + deployment

## Running locally

**Prerequisites:** Python 3.11 or newer, plus API credentials (see step 3).

**1. Clone and enter the project**

    git clone https://github.com/eliserps/airspace-copilot.git
    cd airspace-copilot

**2. Create and activate a virtual environment**

    python -m venv .venv
    # Windows (PowerShell): .venv\Scripts\Activate.ps1
    # macOS / Linux: source .venv/bin/activate

**3. Install dependencies**

    pip install -r requirements.txt

**4. Set up your credentials.** Create a file named `.env` in the project root with:

    GROQ_API_KEY=your_groq_key
    OPENSKY_CLIENT_ID=your_opensky_client_id
    OPENSKY_CLIENT_SECRET=your_opensky_client_secret

Get a Groq key at https://console.groq.com and OpenSky credentials at https://opensky-network.org (Account → API Client).

**5. Build the knowledge base (one time).** This reads the reference docs, creates embeddings and stores them in Chroma:

    python src/rag.py

**6. Run the project**

    python src/main.py

You should see live aircraft counts, decoded weather and a bilingual airspace briefing in your terminal.
