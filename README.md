
# Error Radar

**A local-first, AI-powered error diagnostics system that reads your stack traces, finds historically similar failures, and suggests fixes — without ever sending your code's secrets to someone else's cloud.**

---

## What This Is, In Plain English

When a production service crashes, it spits out a stack trace. Engineers see the trace, scratch their heads, search Slack, grep old tickets, and hopefully remember that this same class of bug was fixed three months ago by someone who has since left the team.

Error Radar tries to short-circuit that loop. It does four things:

1. It takes a stack trace and turns it into a 768-dimensional vector (a list of numbers that captures the "meaning" of the error).
2. It searches a database of past errors — also stored as vectors — to find ones that are semantically similar, even if the wording is completely different.
3. It hands the top matches to a local language model (Mistral 7B) along with how those errors were fixed in the past, and asks for a root-cause analysis and a suggested fix.
4. When the same error keeps coming in, it deduplicates them so your database doesn't fill up with 5,000 copies of the same `NullPointerException`.

The "Zero Trust" part is the privacy model. Stack traces routinely contain emails, IPs, JWT tokens, internal service names, customer IDs, and stray secrets. Error Radar runs the embedding model and the LLM locally through Ollama, so none of that data ever leaves your machine.

---

## Demo and Screenshots

### Video Demo

[![Error Radar Demo Video](https://img.youtube.com/vi/vXdLkXAu2tg/hqdefault.jpg)](https://youtu.be/vXdLkXAu2tg "Click to watch the demo on YouTube")
*Click the thumbnail above to watch the full walkthrough of the RAG pipeline, deduplication, and local LLM diagnosis.*

### Screenshots

![Dashboard with data](docs/screenshots/dashboard-with-data.png)
*Stats cards show total errors, unresolved count, and most 
frequent error. The error table shows occurrence counts — 
`TypeError: 'NoneType' object is not subscriptable` has fired 
3 times, deduplicated to a single row.*

### AI Diagnosis

![AI Diagnosis panel](docs/screenshots/ai-diagnosis.png)

*The AI diagnosis panel shows similar past errors with similarity 
scores, a root cause analysis, and a suggested fix. Confidence 
badge shows HIGH (1.00) because the query matched an identical 
error.*

### Demo App

![Demo crash panel](docs/screenshots/demo-crash-panel.png)

*The demo app crash trigger panel. Each card fires a different 
error type. Both connection indicators are green — the demo app 
on :8001 and the AI engine on :8000 are running.*

![Demo response log](docs/screenshots/demo-response-log.png)

*The demo app response log after firing crashes. `GET /crash/auth-failure` 
returned 500 (expected — the crash was triggered), and the error 
was automatically forwarded to `POST /errors/log-error` which 
returned 200.*

---

## The Problem

Traditional error-tracking tools — Sentry, Rollbar, Bugsnag — group stack traces using exact string matching, fingerprinting, or regex rules. This works until it doesn't:

- A developer renames a variable. The fingerprint changes. The same bug gets filed as a new issue.
- A line number shifts after a small refactor. The match breaks.
- The same logical failure (`JWT expired`) shows up in three services with three different exception class names. They're treated as unrelated.
- A junior engineer debugs the same class of error that a senior engineer solved six months ago, because nobody remembers and the search doesn't surface it.

The result is wasted time. Teams re-debug failures they have already debugged.

## Why Error Radar Exists

The core idea: **errors should be matched by meaning, not by string.**

A `NullPointerException` thrown while parsing a customer address and a `Cannot invoke String.trim() because line is null` are cousins. They live close to each other in vector space. Error Radar exploits that fact to surface historical fixes when a new error arrives — without requiring anyone to remember, tag, or search for them.

## How It Compares To Other Tools

| Tool | Matching Method | Privacy Model | AI Diagnosis |
|---|---|---|---|
| Sentry / Rollbar / Bugsnag | String fingerprinting + rules | Cloud (vendor-hosted) | None / bolted-on |
| GitHub Copilot Chat | N/A (IDE assistant) | Cloud | Yes, but generic |
| LangChain-based RAG demos | Usually OpenAI embeddings + OpenAI LLM | Cloud | Yes |
| **Error Radar** | **Vector similarity (local embeddings)** | **Fully local** | **Yes, grounded in your own past fixes** |

Error Radar is not a replacement for Sentry. It is a focused experiment in one specific thing: **can a small local LLM, grounded in a vector index of your own historical errors, produce useful root-cause analysis without any data leaving your machine?**

---

## Why No LangChain / LlamaIndex / Framework

This is worth calling out explicitly, because it is a deliberate choice, not an oversight.

Frameworks like LangChain and LlamaIndex are excellent for shipping fast. They give you `RetrievalQA.from_chain_type(...)` and you're done. But that abstraction hides the parts that actually matter when you're trying to learn how RAG works:

- How the embedding API is called and what its failure modes are.
- How vectors are stored, indexed, and queried.
- Why cosine distance is `1 - similarity` and not the other way around.
- What happens to the prompt when retrieved context is too long, too short, or off-topic.
- Why a 7B model at temperature 0.0 sometimes loops and at 0.1 doesn't.
- Why LLM-generated confidence scores are useless and have to be computed externally.

Building this from scratch with raw SQL against `pgvector`, direct `requests.post` calls to Ollama, and a hand-written prompt template taught me more in two weeks than wrapping `RetrievalQA` would have in two hours. If you're here to learn RAG internals, you should consider doing the same. If you're here to ship a product tomorrow, use a framework — this repo will look like unnecessary work.

---

## Architecture

```text
┌──────────────────────────────────────────────────────────────────┐
│                        Error Radar UI                            │
│              (index.html — vanilla JS dashboard)                 │
└────────────────────────────────┬─────────────────────────────────┘
                                 │  HTTP (fetch)
                                 ▼
┌──────────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                              │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────────────┐  │
│  │ Error Routes│  │ Query Routes│  │     Stats Routes         │  │
│  │  /errors/*  │  │  /query     │  │  /errors/stats           │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬───────────────┘  │
│         │                │                     │                 │
│         ▼                ▼                     ▼                 │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    Service Layer                            │ │
│  │  rag_service.py · embedding_service.py · stats_service.py   │ │
│  └──────────────────────┬──────────────────────────────────────┘ │
│                         │                                        │
│         ┌───────────────┼────────────────┐                       │
│         ▼               ▼                ▼                       │
│  ┌────────────┐  ┌────────────┐  ┌────────────────────┐          │
│  │  Ollama    │  │  pgvector  │  │  Prompt Engine     │          │
│  │ (local)    │  │ (Neon DB)  │  │ suggestion.txt     │          │
│  │            │  │            │  │                    │          │
│  │ embed API  │  │ cosine <=> │  │ {query_error}      │          │
│  │ generate   │  │ IVFFlat    │  │ {historical_errors}│          │
│  └────────────┘  └────────────┘  └────────────────────┘          │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                    Demo App (port 8001)                          │
│  Intentionally broken endpoints that auto-report crashes         │
│  to the Error Radar engine via POST /errors/log-error            │
└──────────────────────────────────────────────────────────────────┘
```

### Data Flow

**Ingestion path** — a new error arrives:

1. The stack trace is **sanitized**. Emails, IPs, JWTs, passwords, and API keys are redacted with regex.
2. The sanitized trace is **truncated** to the last 8 lines, to strip framework boilerplate that would skew similarity.
3. The text is **embedded** into a 768-dim vector via `nomic-embed-text` running locally in Ollama.
4. The vector is compared against existing records at a **0.9 cosine similarity threshold**. If something that similar already exists, it's a duplicate — increment `occurrence_count` and stop.
5. Otherwise, insert a new row with the embedding.

**Query path** — an engineer clicks "Query AI":

1. The error trace is embedded into a query vector.
2. `pgvector`'s `<=>` operator returns the top-N most similar historical errors.
3. Anything below **0.7 similarity** is discarded as unrelated noise.
4. The top 3 matches (truncated to 300 characters each) plus their recorded past fixes are injected into a prompt template.
5. Mistral 7B generates a structured `{root_cause, suggested_fix}` JSON response.
6. A **confidence score** is computed in Python as the average similarity of the retrieved results. This is not the LLM's own assessment — 7B models will tell you they're 99% confident about anything.

---

## Project Structure

```text
Error-Radar/
├── ai-engine/                   # Core RAG backend
│   ├── main.py                  # FastAPI app entrypoint
│   ├── index.html               # Error Radar dashboard (single-file SPA)
│   ├── AI_DESIGN.md             # Architecture & design decision docs
│   ├── requirements.txt         # Python dependencies
│   ├── .env.example             # Environment variable template
│   │
│   ├── api/routes/
│   │   ├── error_routes.py      # CRUD + stats endpoints for errors
│   │   └── query_routes.py      # RAG query endpoint
│   │
│   ├── services/
│   │   ├── embedding_service.py # Ollama embedding with retry logic
│   │   ├── rag_service.py       # Semantic search, LLM generation, dedup, sanitization
│   │   └── stats_service.py     # Dashboard aggregate statistics
│   │
│   ├── repositories/
│   │   └── error_repo.py        # Raw SQL queries against pgvector
│   │
│   ├── schemas/
│   │   └── error_schemas.py     # Pydantic request models
│   │
│   ├── core/
│   │   └── database.py          # SQLAlchemy engine factory
│   │
│   ├── exceptions/
│   │   └── database_exceptions.py
│   │
│   ├── prompts/
│   │   └── suggestion.txt       # Externalized LLM prompt template
│   │
│   ├── scripts/                 # Seed data, evaluation, exploration scripts
│   │   ├── seed.py              # Seeds 20 production-like errors
│   │   ├── seed_past_fixes.py   # Backfills historical fix descriptions
│   │   ├── evaluate_rag.py      # P@1 retrieval evaluation
│   │   ├── validation_experiment.py
│   │   └── *.md                 # Evaluation results & observations
│   │
│   └── tests/
│       ├── test_embedding.py    # Embedding service unit tests
│       ├── test_rag.py          # RAG pipeline unit tests
│       ├── test_deduplication.py # Dedup logic tests
│       └── test_integration.py  # E2E API tests (live DB)
│
├── demo/                        # Intentionally broken demo application
│   ├── main.py                  # FastAPI app with crash endpoints
│   ├── index.html               # Demo app trigger UI
│   └── requirements.txt
│
└── devlog.txt                   # Full development log
```

---

## Getting Started

### Prerequisites

| Dependency | Purpose |
|---|---|
| **Python 3.10+** | Runtime |
| **[Ollama](https://ollama.com)** | Local LLM and embedding inference |
| **PostgreSQL** with `pgvector` | Vector storage (Neon's free tier works, or run locally) |

### 1. Clone and install Ollama models

```bash
git clone https://github.com/govindarajan2003/Error-Radar.git
cd Error-Radar/ai-engine

# Pull the required local models
ollama pull nomic-embed-text
ollama pull mistral
```

Make sure the Ollama daemon is running (`ollama serve`, or it autostarts on install).

### 2. Set up the database

Create a PostgreSQL database (Neon's free tier is the easiest path) and enable the vector extension:

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS errors (
    id               SERIAL PRIMARY KEY,
    message          TEXT NOT NULL,
    stack_trace      TEXT,
    sanitized_trace  TEXT,
    service_name     TEXT,
    embedding        VECTOR(768),
    occurrence_count INTEGER DEFAULT 1,
    resolved         BOOLEAN DEFAULT FALSE,
    past_fix         TEXT,
    created_at       TIMESTAMPTZ DEFAULT NOW(),
    last_seen_at     TIMESTAMPTZ DEFAULT NOW()
);

-- IVFFlat index for approximate nearest-neighbor search
CREATE INDEX ON errors USING ivfflat (embedding vector_cosine_ops) WITH (lists = 1);
```

A note on `lists = 1`: that's the right value for the ~20-row seed dataset. Once you cross roughly 10,000 rows, rebuild the index with `lists = rows / 1000`. Below that threshold, IVFFlat behaves like a flat scan, which is fine.

### 3. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env`:

```env
# PostgreSQL connection string (Neon or local)
DATABASE_URL=postgresql://user:password@ep-your-database.neon.tech/neondb?sslmode=require

# Ollama settings
OLLAMA_BASE_URL=http://localhost:11434
EMBEDDING_MODEL=nomic-embed-text
LLM_MODEL=mistral

# Model configuration
EXPECTED_EMBEDDING_DIM=768
TOP_N_RESULTS=5
SIMILARITY_THRESHOLD=0.70
```

### 4. Install dependencies and seed the database

```bash
pip install -r requirements.txt

# Seeds 20 production-realistic errors with embeddings
python -m scripts.seed

# (Optional) Backfills historical fix descriptions for seeded errors
python -m scripts.seed_past_fixes
```

### 5. Start the server

```bash
uvicorn main:app --reload --port 8000
```

Open the dashboard at **[http://127.0.0.1:8000/index.html](http://127.0.0.1:8000/index.html)**. You can also serve `index.html` separately — it just talks to `localhost:8000`.

### 6. Run the demo app (Optional)

The demo is a small FastAPI service with intentionally broken endpoints. Each crash auto-reports itself to the Error Radar engine via `POST /errors/log-error`.

```bash
cd ../demo
pip install -r requirements.txt
python main.py
```

The demo runs on `http://127.0.0.1:8001`. Open `demo/index.html` in your browser to see the crash trigger panel.

Available crash routes:

| Route | Error Type |
|---|---|
| `/crash/null-pointer` | TypeError — `None` object access |
| `/crash/auth-failure` | ValueError — JWT expired |
| `/crash/not-found` | LookupError — missing user record |
| `/crash/memory` | MemoryError — heap exhausted |
| `/crash/db-timeout` | TimeoutError — connection pool exhausted |

Click a crash card, refresh the main dashboard, and the error will be there.

![Custom error form](docs/screenshots/demo-custom-error.png)

*The manual error logger allows submitting arbitrary errors 
directly to the AI engine without going through the crash routes.*

---

## API Reference

### Error Management

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/errors` | List all errors (optional `?resolved=true\|false` filter) |
| `GET` | `/errors/stats` | Aggregate stats: total count, unresolved count, most frequent error |
| `GET` | `/errors/stats/daily?interval=14` | Daily error counts over the specified interval |
| `POST` | `/errors/log-error` | Ingest a new error (with auto-dedup and embedding) |
| `POST` | `/errors/{id}/fix` | Mark an error resolved with a human-provided fix description |

### AI Query

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/query` | Submit an error for RAG-powered diagnosis |

**Example — Query AI:**

```bash
curl -X POST http://127.0.0.1:8000/query \
  -H "Content-Type: application/json" \
  -d '{"error_log": "java.lang.NullPointerException: Cannot invoke String.trim() because line is null"}'
```

Response:

```json
{
  "similar_cases": [
    {
      "id": 5,
      "message": "Null pointer while parsing customer address",
      "similarity_score": 0.7069,
      "service_name": "customer-service",
      "past_fix": "Added null-check before accessing address fields"
    }
  ],
  "response": {
    "root_cause": "The variable 'line' is null when String.trim() is called...",
    "suggested_fix": "Add a null-check before invoking trim(): if (line != null) { line.trim(); }",
    "confidence": 0.71
  }
}
```

---

## How the RAG Pipeline Works

### 1. Embedding Layer

Stack traces are embedded using `nomic-embed-text` via Ollama's local `/api/embed` endpoint.

- 768-dimensional output vectors.
- Deterministic — same input always produces the same vector.
- Wrapped in an exponential backoff retry loop (1s, then 2s, then 4s) with three custom exceptions:
  - `OllamaUnavailableError` — daemon not reachable.
  - `OllamaTimeoutError` — request timed out after retries.
  - `EmbeddingDimensionError` — unexpected vector dimensions (e.g. wrong model loaded).

### 2. Vector Storage and Search

Embeddings live in PostgreSQL via `pgvector`. Retrieval uses cosine distance:

```sql
SELECT id, message, sanitized_trace, service_name, past_fix,
       1 - (embedding <=> :query_vector) AS similarity_score
FROM errors
WHERE embedding IS NOT NULL
ORDER BY embedding <=> :query_vector ASC
LIMIT :top_n
```

The `<=>` operator returns cosine distance (0 = identical, 1 = orthogonal). The query inverts it (`1 - distance`) to produce a similarity score that reads the way a human expects.

### 3. Deduplication

Before inserting any new error, the system checks for near-duplicates:

| Threshold | Purpose |
|---|---|
| **≥ 0.9** | Same error — deduplicate by incrementing `occurrence_count` |
| **≥ 0.7** | Related error — retrieve as context for the RAG prompt |
| **< 0.7** | Unrelated — filtered out |

### 4. PII Sanitization (the "Zero Trust" part)

Before embedding, stack traces pass through a sanitization pipeline that redacts the obvious leakage vectors:

| Pattern | Replacement |
|---|---|
| Email addresses | `REDACTED EMAIL` |
| IP addresses | `REDACTED IP ADDRESS` |
| JWT Bearer tokens | `REDACTED JWT TOKEN` |
| Passwords, secrets, API keys | `REDACTED TEXT` |

Traces are also truncated to the last 8 lines. Framework boilerplate at the top of a trace (Spring Boot startup spam, Django middleware chains, etc.) would otherwise dominate the embedding and wash out the actual exception.

### 5. Generation Layer

Mistral 7B runs locally through Ollama with:

- **Temperature 0.1** — low enough for consistent JSON output, but not 0.0. At 0.0, Mistral occasionally falls into infinite repetition loops.
- **Externalized prompt** at `prompts/suggestion.txt` — editable without touching code, version-controlled alongside everything else.
- **Confidence scoring computed in Python**, as the average cosine similarity of retrieved results. Not by the LLM. 7B models consistently hallucinate high confidence regardless of context quality — try it and you'll see "95% confident" attached to a totally wrong answer.

---

## Evaluation Results

### Retrieval Quality — Precision at 1 (P@1)

10 blind test queries run against the seeded error database:

| Query | Expected Category | Top Match | Score | Status |
|---|---|---|---|---|
| NullPointerException at NotificationService | NullPointerException | Null pointer while parsing customer address | 0.7069 | pass |
| Application crashed, uninitialized request object | NullPointerException | Null pointer during payment validation | 0.7149 | pass |
| TimeoutError: Failed to acquire DB connection | DB Connection / Timeout | SQL query execution timeout | 0.7598 | pass |
| PSQLException: Database server did not respond | DB Connection / Timeout | — (below threshold) | — | fail |
| Bearer token signature validation failed | JWT / Authentication | JWT signature verification failed | 0.7173 | pass |
| JWT token expired | JWT / Authentication | JWT token expired | 0.7204 | pass |
| UserProfileNotFoundException | Resource Not Found | — (below threshold) | — | fail |
| OutOfMemoryError: Java heap space | OutOfMemoryError | — (below threshold) | — | fail |
| Failed to load authenticated user info | Ambiguous | User record not found | 0.7143 | pass |
| Redis cache eviction triggered | Unrelated (should be empty) | — (below threshold) | — | pass |

**Final P@1: 0.70.** The failures cluster where raw Java exception syntax (`PSQLException`, `OutOfMemoryError`) diverged too far from the plain-English phrasing of the seed records. Hybrid search (vector + BM25 keyword) would close most of this gap.

To reproduce:

```bash
cd ai-engine
python -m scripts.evaluate_rag
```

The script runs 10 queries through the live similarity search, asks for human judgment on each result, and prints the final P@1 score.

### Generation Quality

10 error types evaluated for LLM diagnostic quality:

| Verdict | Count |
|---|---|
| Good | 8 |
| Acceptable | 2 |
| Poor | 0 |

The key finding was not surprising but worth measuring: injecting historical context with recorded fixes shifted the output from generic debugging advice to system-specific recommendations.

**A/B Test — RAG vs. No RAG** on a Database Connection Timeout error:

- Without RAG: *"Check your pool configuration."*
- With RAG: *"Bump timeout to 30000ms and optimize indexing on active tables."*

The second answer came directly from the `past_fix` field of a retrieved historical error. That's the whole point of the system.

---

## Key Design Decisions

| Decision | Why |
|---|---|
| **Local LLM (Ollama)** over OpenAI API | Zero data exfiltration. Stack traces contain PII, credentials, internal service names. |
| **nomic-embed-text** for embeddings | 768-dim output balances accuracy vs. storage. Runs within 8 GB VRAM. |
| **Mistral 7B** for generation | Fits the 8 GB VRAM constraint with strong instruction-following for structured JSON output. |
| **Temperature 0.1** (not 0.0) | 0.0 caused infinite repetition loops in testing. 0.1 is deterministic enough for reliable JSON parsing. |
| **pgvector** over Pinecone / Weaviate | Already using PostgreSQL for the error ledger. One database, no sync overhead. |
| **Python-side confidence** (not LLM) | 7B models hallucinate high confidence scores. Average cosine similarity is objective. |
| **Two similarity thresholds** | 0.9 for dedup (same error), 0.7 for retrieval (related error). |
| **Externalized prompt template** | Iterate on prompts without touching code. Version-controlled in `prompts/`. |
| **Top-3 context, 300-char truncation** | Prevents prompt bloat that increases latency and dilutes model attention. |
| **No LangChain / LlamaIndex** | Built manually to learn the mechanics. See the section above. |

---

## Running Tests

To verify the API contract and database integration without requiring Ollama to be running:

```bash
cd ai-engine
python -m pytest tests/test_integration.py -v
```

To run the full test suite:

```bash
cd ai-engine
python -m pytest
```

### Test Coverage

| Test File | What It Covers |
|---|---|
| `test_embedding.py` | Connection errors, timeouts (verifies 3 retry attempts), dimension validation, successful embedding, invalid status codes |
| `test_rag.py` | Happy-path retrieval, empty results, similarity-threshold filtering, embedding-failure propagation |
| `test_deduplication.py` | Duplicate detection → occurrence increment, new record insertion when no match |
| `test_integration.py` | E2E API tests against live DB — error listing, stats shape, 404 on nonexistent fix |

Unit tests use `unittest.mock` to isolate Ollama network calls and SQLAlchemy database interactions. Integration tests run against the live Neon database.

---

## Known Limitations

**Vocabulary gap.** Retrieval works best when query vocabulary matches seed-data vocabulary. Queries using raw Java exception class names (`PSQLException`) against plain-English seed records (`Database connection timeout`) can fall below the similarity threshold. Hybrid search (vector + BM25) would address this.

**Boilerplate sensitivity.** The current implementation truncates stack traces to 300 characters for context-window management. If your application's first 300 characters are identical boilerplate across all errors, different errors can collapse into duplicates. In production, traces should be pre-processed to extract the meaningful exception lines before embedding.

**Small seed dataset.** 20 seed errors means some categories are underrepresented. Retrieval accuracy improves naturally as real errors accumulate.

**IVFFlat at small scale.** Provides no real performance benefit below 10,000 rows; it acts as a flat scan. Switch to HNSW once you have real volume.

**Single-dimension confidence.** The confidence score measures retrieval quality only, not generation quality. A high confidence with garbage context still produces garbage output.

**No negative feedback loop.** There's no mechanism yet to flag or learn from bad AI suggestions. Engineers can record fixes, but they can't tell the system "this suggestion was wrong."

**LLM is a 7B model.** It will sometimes produce plausible-sounding but incorrect root causes. Treat suggestions as a starting point, not a verdict.

---

## Future Work

- **Fine-tune the embedding model** on engineering vocabulary — Java exceptions, framework-specific terminology.
- **Hybrid search** combining semantic vector search with BM25 keyword search to close the vocabulary gap.
- **Feedback endpoint** (`/feedback`) to capture engineer ratings for future model tuning.
- **HNSW index** to replace IVFFlat once the dataset scales past 10K rows.
- **Multi-tenant support** — per-service embedding namespaces so unrelated services don't pollute each other's retrieval results.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.10+, FastAPI, Uvicorn |
| Embedding | Ollama + nomic-embed-text (768-dim, local) |
| Generation | Ollama + Mistral 7B (local) |
| Database | PostgreSQL + pgvector (Neon serverless) |
| ORM | SQLAlchemy (raw SQL via `text()`) |
| Validation | Pydantic v2 |
| Frontend | Vanilla HTML / CSS / JS (single-file SPA) |
| Testing | pytest, unittest.mock, FastAPI TestClient |

---
## Additional research

For a deep dive into the system architecture, embedding tradeoffs, prompt design, and the P@1 retrieval evaluation, see AI_DESIGN.md.

## Disclaimer

AI suggestions are generated by a local LLM and should be reviewed by a developer before being acted on. The system is an engineering exercise, not a production incident-response tool. Do not wire it into your on-call pipeline without understanding its failure modes.

## License

MIT — Built to learn about generative AI and RAG. See [LICENSE](./LICENSE) for the 
full text.
