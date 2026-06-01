
# AI-Powered Semantic Error Resolution Engine

A production-grade Retrieval-Augmented Generation (RAG) pipeline built to eliminate redundant debugging. This system intercepts software stack traces, converts them into high-dimensional vector embeddings using a local LLM, and performs sub-second semantic similarity searches using PostgreSQL and `pgvector`. 

By matching intent and mathematical root-cause rather than exact keyword syntax, the engine accurately clusters related system failures (e.g., grouping `JWT expired` with `Invalid credentials`) to instantly surface historical solutions.

## ⚙️ Tech Stack
* **Backend:** Python 3.x
* **Vector Generation:** Ollama (Local LLM Embeddings)
* **Database:** Serverless PostgreSQL (Neon)
* **Vector Search:** `pgvector` (Cosine Distance `<=>` / IVFFlat Indexing)
* **ORM & Data Integrity:** SQLAlchemy
* **Testing:** `pytest`, `unittest.mock`

---

## 🏗 System Architecture

The pipeline is decoupled into three primary execution layers:

### 1. The Ingestion & Vectorization Layer
* Raw stack traces are sanitized and parsed.
* The clean text is passed to an asynchronous Ollama embedding model, returning a `768`-dimensional mathematical vector.
* **Resilience:** Wrapped in a custom exponential backoff retry loop. Network timeouts, `OllamaUnavailableError`, and `EmbeddingDimensionError` are explicitly handled or propagated to prevent silent pipeline failures.

### 2. The Cloud Storage Layer
* Vectors are cast and stored in a serverless Neon PostgreSQL database.
* Uses SQLAlchemy `engine.begin()` context managers to guarantee atomic transactions (commit on success, rollback on failure).
* **Optimization:** The vector column is optimized with an `IVFFlat` (Inverted File Flat) index, partitioning the vector space to prevent expensive full-table scans during high-load retrieval.

### 3. The Semantic Retrieval Layer
* Converts incoming live errors into query vectors.
* Executes raw SQL against the database, calculating the Cosine Distance (`<=>`) between the query vector and historical data.
* Automatically filters out unrelated anomalies using a strict `.env` controlled `SIMILARITY_THRESHOLD`.

---

## 🧮 The Mathematics of Retrieval

Traditional observability tools rely on keyword `ILIKE` or `Regex` searches, which break when variable names or line numbers change. This engine relies on **Cosine Similarity**.

The retrieval query calculates the angle between two 768-dimensional vectors:
```sql
SELECT 
    id, message, sanitized_trace, service_name,
    1 - (embedding <=> :query_vector) AS similarity_score
FROM errors
WHERE embedding IS NOT NULL
ORDER BY embedding <=> :query_vector ASC
LIMIT :top_n

```

* **Distance to Similarity:** The pgvector `<=>` operator returns a distance score (0.0 = identical, 1.0 = orthogonal). The SQL query mathematically inverts this (`1 - distance`) to return a clean, human-readable similarity percentage to the application layer.

---

## 🧪 Testing Strategy

The system prioritizes predictable failure management and isolated dependency testing:

* **Isolated Network Mocks:** Uses Python's `unittest.mock` to intercept and fake LLM network calls, verifying retry-logic and error propagation without requiring a live model.
* **SQLAlchemy Context Mocks:** Mocks `__enter__` context managers and `fetchall()` returns to validate threshold filtering and math rounding logic entirely in memory.
* **Self-Cleaning Integration Tests:** An end-to-end cloud pipeline test that connects to the live Neon database, inserts a dummy vector, validates storage, and issues a teardown `DELETE` command to prevent production data pollution.

---

## 🚀 Quick Start

### 1. Environment Setup

Create a `.env` file in the root directory:

```env
DATABASE_URL="postgresql://user:password@ep-your-database.neon.tech/neondb"
SIMILARITY_THRESHOLD=0.70
TOP_N_RESULTS=5

```

### 2. Install Dependencies

```bash
pip install -r requirements.txt

```

### 3. Initialize the Database

Ensure your PostgreSQL instance has the vector extension enabled:

```sql
CREATE EXTENSION IF NOT EXISTS vector;

```

### 4. Run the Pipeline

Seed the database with the initial vector clusters:

```bash
python -m scripts.seed

```

Run a live semantic search validation:

```bash
python -m scripts.validation_experiment

```

### 5. Run the Test Suite

```bash
python -m pytest

```

