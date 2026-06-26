# Week 1 Devlog: Tool Exploration and Empirical Development

## Objective

The goal for Week 1 was to establish the initial AI-engine structure and validate foundational tools (`nomic-embed-text` for embeddings and `mistral` for generation) using Ollama. The focus was strictly on experiment-driven development: writing exploratory scripts to understand API behaviors, response structures, and failure modes before writing production modules. 

All exploratory work was isolated in the `ai-engine/scripts/` directory, keeping production code clean. The primary branch for this phase was `feat/devb-tool-exploration`.

---

## Day 1: Embedding Validation and API Structure

The first step was validating the `nomic-embed-text` model. Needed to confirm the exact vector dimensionality and understand the raw API response structure from Ollama. 

Initially tested this via the CLI, which returned a 768-dimensional vector. To integrate this into Python, wrote `ai-engine/scripts/test_embedding.py` using the `requests` library to hit the local Ollama REST API (`http://localhost:11434/api/embed`).

```python
# ai-engine/scripts/test_embedding.py excerpt
payload = {
    'model': 'nomic-embed-text',
    'input': "java.lang.NullPointerException: Cannot invoke 'String.trim()' because 'line' is null"
}
response = requests.post(url, json = payload)
data = response.json()
embedding_length = len(data['embeddings'][0])
```

The API confirmed a 768-dimension vector. Also observed the performance metrics returned by Ollama. The `total_duration` is returned in nanoseconds. Converting this to milliseconds (dividing by 1,000,000) showed an inference time of roughly 84ms, which is highly performant for local inference.

Tested failure states too. Passing an invalid model name returns a clean HTTP 404 with a JSON error payload, which will be easy to handle in `ai-engine/services/embedding_service.py` later.

---

## Day 2: Generation, Performance, and Statelessness

Next, shifted to the `mistral` model using `ai-engine/scripts/test_mistral.py`. Chose to use the `requests` library instead of the Ollama Python SDK to maintain a lower-level understanding of the API and avoid hidden abstractions.

Initially used the `/api/chat` endpoint. However, the RAG pipeline does not require conversational memory. Each error analysis is an isolated task. Because of this, switched to the `/api/generate` endpoint, which is stateless and better suited for deterministic backend pipelines.

```python
# ai-engine/scripts/test_mistral.py excerpt
payload = {
    'model': 'mistral',
    'prompt': prompt,
    'stream': False,
    'format': 'json'
}
response = requests.post(url, json=payload)
```

Using `/api/generate` yielded a slight performance improvement (from ~71.2 tokens/second to ~72.9 tokens/second). 

A critical observation: even when passing `format: 'json'`, Ollama returns the JSON as a stringified payload inside the `response` key. Downstream code in `ai-engine/services/rag_service.py` will need to implement `json.loads()` and schema validation to parse this safely.

---

## Day 3: Schema Enforcement and Temperature Tuning

With generation working, needed to force the LLM to return structured data matching a specific JSON schema. 

Briefly overthought the database schema integration, wondering if LLM outputs needed to map directly to database columns. Caught myself: Dev A owns the Postgres tables. My responsibility is strictly the JSON contract. The LLM outputs a payload, and the API layer handles the database insertion. 

First prompt attempt was a naive string concatenation:
```python
prompt = "you are going to strictly follow this schema..." + json.dumps(ErrorSchema, indent=2) + error
```

While this worked, it is poor prompt engineering for production. Refactored the prompt structure in `ai-engine/scripts/test_mistral.py` to separate the System Role, Task, Input, and Constraints clearly, a practice that will be formalized in `ai-engine/prompts/suggestion.txt`.

Ran an experiment comparing temperature settings:
*   **Temperature 1.0 (High Creativity):** The model took creative liberties. Ignored the schema, added extra fields (`type`, `description`), and changed the structure between iterations.
*   **Temperature 0.0 (Deterministic):** The output was perfectly consistent. The schema was followed exactly, with no extra fields.

This confirmed that for structured data extraction in RAG pipelines, temperature must be locked at 0 to prevent schema drift.

---

## Day 4: Failure Simulation and Resilience

The final experiment was testing what happens when the Ollama daemon fails. 

Initially assumed a dead daemon would return an HTTP 502 Bad Gateway. This was incorrect. If the Ollama daemon is completely shut down, there is no server to return an HTTP status code. The connection is refused at the socket level, raising `requests.exceptions.ConnectionError`. 

Wrote a retry loop using exponential backoff to handle `requests.exceptions.Timeout` (which occurs when the server is reachable but slow to respond). To test this, intentionally set the timeout to `0.001` seconds for the first three attempts, forcing failures, and set a realistic `30` second timeout on the final attempt to prove recovery.

```python
# ai-engine/scripts/test_mistral.py excerpt
for attempt in range(max_attempts):
    try:
        if attempt != max_attempts - 1:
            response = requests.post(url, json=payload, timeout=time_out)
            print("success")
            break # Crucial: stop the loop if the request succeeds
        else:
            response = requests.post(url, json=payload, timeout=30)
            print("success")
            break
    except requests.exceptions.Timeout as err:
        time.sleep(wait_time)
        print(f"wait {wait_time} second")
        wait_time *= 2
    except requests.exceptions.ConnectionError:
        print("Server couldn't be reached")
        break
```

A key correction during this phase was adding the `break` statement on success. Without it, a successful request would just loop again, bombarding the LLM with duplicate requests. 

---

## End of Week 1 Status

*   **Scripts Complete:** `ai-engine/scripts/test_embedding.py` and `ai-engine/scripts/test_mistral.py` are clean, commented, and fully runnable.
*   **Empirical Data Captured:** Vector dimensions (768), API response structures, and performance metrics (nanosecond to millisecond conversions) are documented in `ai-engine/scripts/week1_observations.md`.
*   **Architecture Decisions Made:** Shifted from `/api/chat` to `/api/generate` for stateless processing. Locked temperature at 0 for schema adherence. Established the difference between handling `Timeout` (slow server) and `ConnectionError` (dead server).
*   **Next Steps:** Hand off the confirmed 768-dimension requirement to Dev A for pgvector setup, and begin migrating script logic into the production modules (`ai-engine/services/embedding_service.py` and `ai-engine/services/rag_service.py`).