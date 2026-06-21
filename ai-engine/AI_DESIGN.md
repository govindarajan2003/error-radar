# System Architecture

**Overview**
Error Radar is a local, AI-assisted error tracking and diagnostic platform. It ingests application stack traces, matches them against a historical ledger of resolved errors, and uses a local LLM to generate actionable fixes. Because the embedding and generation models run entirely on the host machine, sensitive PII and credentials within the stack traces never leave the local environment.

**Embedding Layer**
Stack traces are converted to vector embeddings using `nomic-embed-text` via Ollama. We opted for local embeddings over external APIs like OpenAI to remove latency, eliminate recurring costs, and guarantee data privacy. The model's 768-dimension output provides accurate semantic clustering for technical text without incurring the storage overhead of larger models. Initial benchmarks confirmed the expected dimensionality and validated the cosine similarity operator for accurate distance mapping.

**Vector Storage**
We store embeddings in PostgreSQL using the `pgvector` extension (hosted on Neon) rather than a dedicated vector database like Pinecone. Since the application already requires a relational database for the error ledger and fixes, adding a `vector` column keeps the data model monolithic and avoids cross-database synchronization. For indexing, we use an `IVFFlat` index with `lists=1`. At our current dataset size, this effectively performs a flat scan, which is appropriate. The index will need to be rebuilt with a higher `lists` parameter once the row count scales past 10,000.

**Generation Layer**
Mistral 7B, running locally via Ollama, handles diagnostic generation. This model was chosen because it fits within our 8GB VRAM constraint while maintaining strong instruction-following capabilities for technical tasks. The generation temperature is set to `0.1`. Testing showed that `0.0` occasionally caused infinite repetition loops, while higher temperatures introduced JSON schema drift. A setting of `0.1` provides the deterministic structure needed for reliable parsing without triggering repetitive outputs.

**Deduplication Architecture**
To prevent duplicate logs from bloating the database, the system runs an aggressive deduplication check before inserting new errors. Incoming traces are embedded and queried against the database using a strict `0.9` cosine similarity threshold. This is distinct from the `0.7` threshold used during diagnostic retrieval: `0.7` indicates semantic similarity, whereas `0.9` denotes the exact same error. If a new error hits the `0.9` threshold, it is dropped, and the `occurrence_count` on the existing record is incremented.

**Confidence Calculation**
We originally asked the LLM to output its own confidence score, but testing revealed a common limitation: the model consistently hallucinated high confidence (e.g., `0.95`) regardless of context quality. Because 7B-class models struggle with reliable self-evaluation, we moved confidence scoring out of the LLM and into the Python backend. The system now calculates confidence by averaging the cosine similarity scores of the retrieved context vectors, providing a reliable measure of retrieval quality rather than an LLM guess.

***

# Prompt Design

## Current Version (`prompts/suggestion.txt`)

```text
You are an expert Principal Staff Engineer. 
A production application has thrown a new error. I will provide you with the stack trace of the new error, along with a list of similar historical errors from our database.

Analyze the new error in the context of how the historical errors were resolved.

CONSTRAINTS:
1. You must output ONLY valid JSON.
2. Do not include markdown formatting or conversational text.
3. The "suggested_fix" field MUST be a single, flat string. DO NOT output a dictionary, object, or array for this field. If you have multiple steps, format them clearly within that single string using newline characters (\n).
4. You MUST output your response in raw, valid JSON format matching this exact schema. Do not include any markdown formatting, code blocks, or conversational text. Output ONLY JSON.
{
  "root_cause": "A detailed explanation of why the error occurred.",
  "suggested_fix": "Actionable steps or code changes to fix the issue."
}

NEW ERROR:
{query_error}

HISTORICAL ERRORS:
{historical_errors}

INSTRUCTIONS FOR FIX:
If a historical error has a high similarity score and a recorded past fix, you MUST strongly base your "suggested_fix" on that recorded past fix.
```

## Design Rationale

**System Role**
Setting a "Principal Staff Engineer" persona directs the model to analyze problems architecturally rather than offering basic, junior-level debugging advice.

**Constraints & Schema Enforcement**
LLMs naturally drift toward conversational output (e.g., "Here is the JSON...") or inconsistent data structures. The uppercase constraints explicitly prevent this. For example, the model previously returned dictionaries or arrays for the `suggested_fix` field, which broke the API parser. Adding Constraint #3 eliminated this schema drift. As a secondary fallback, the backend also strips residual markdown or prefix text before parsing the JSON.

**Explicit JSON Schema**
Providing the exact keys and structure in the prompt ensures the payload can be parsed immediately by the backend without additional transformation logic.

**Context Window Management**
To avoid bloating the prompt and diluting the model's attention, we limit retrieval to the top 3 most similar errors and truncate historical stack traces to 300 characters. Dumping full stack traces increases latency and confuses the model; this strict curation maintains a high signal-to-noise ratio.

**RAG Override**
Instructing the model to strongly base its fix on historical data prevents it from defaulting to generic pre-trained knowledge when a specific, internal solution exists in the context.

## RAG Impact (Week 5 Evaluation)

The value of the RAG override instruction was observed directly during A/B testing on a Database Connection Timeout error:

*   **Without RAG Instruction:** The model relied on general knowledge, outputting: *"Check your pool configuration."*
*   **With RAG Instruction:** The model utilized the injected historical context, outputting: *"Bump timeout to 30000ms and optimize indexing on active tables."*

This demonstrates the system's ability to prioritize internal engineering context over generic LLM advice.

***

# Evaluation Results

## Retrieval Quality (P@1)

Precision at 1 (P@1) was used to evaluate the retrieval system using a test set of 10 blind queries.

| **ID** | **Query Summary** | **Expected Category** | **Top Match** | **Score** | **Status** |
|---|---|---|---|---|---|
| 1 | java.lang.NullPointerException... at NotificationService | NullPointerException | Null pointer while parsing customer address | 0.7069 | PASS |
| 2 | Application crashed... uninitialized request object. | NullPointerException | Null pointer during payment validation | 0.7149 | PASS |
| 3 | TimeoutError: Failed to acquire database connection... | DB Connection / Timeout | SQL query execution timeout | 0.7598 | PASS |
| 4 | org.postgresql.util.PSQLException: Database server did not respond... | DB Connection / Timeout | NONE (Below threshold) | N/A | FAIL |
| 5 | AuthenticationException: Bearer token signature validation failed. | JWT / Authentication | JWT signature verification failed | 0.7173 | PASS |
| 6 | Unauthorized request received. JWT token expired... | JWT / Authentication | JWT token expired | 0.7204 | PASS |
| 7 | UserProfileNotFoundException: No profile exists for userId=78291... | Resource Not Found | NONE (Below threshold) | N/A | FAIL |
| 8 | java.lang.OutOfMemoryError: Java heap space exhausted... | OutOfMemoryError | NONE (Below threshold) | N/A | FAIL |
| 9 | Failed to load authenticated user information... | Ambiguous (Auth/DB/NotFound) | User record not found | 0.7143 | PASS |
| 10 | Redis cache eviction policy triggered... | Unrelated (Should be Empty) | NONE (Below threshold) | N/A | PASS |

**Final P@1 Score: 0.70 (70%)**

The system hit the 70% target, showing strong retrieval for well-represented categories. Failures (Tests 4, 7, 8) happened when raw Java exception syntax diverged too far from plain English database records, dropping the similarity score below the 0.70 threshold.

## Generation Quality

I manually evaluated the LLM's generation quality across three distinct error types (Database, Authentication, Null Pointer) in Week 4. Two outputs were rated Good, and one was Acceptable. The key finding was that injecting historical context with recorded fixes shifted the output from generic debugging advice to system-specific solutions, vastly outperforming LLM-only generation.

***

# Limitations and Future Work

## Limitations

**Small Seed Dataset**
The retrieval system is only as good as its historical data. With only twenty seed errors, some categories have just one or two examples, which hurts retrieval accuracy. While this naturally improves in production as errors accumulate, the current sparse vector space causes some queries to return no matches.

**IVFFlat Index at Small Scale**
At 20 rows, the `pgvector` IVFFlat index provides no real performance benefit over an exact KNN search. The benefit becomes tangible at 10,000+ rows, at which point the `lists` parameter should be increased to `rows / 1000`.

**Single-Model Confidence Scoring**
The UI currently displays the average cosine similarity of the retrieved results as a confidence score. This only measures retrieval quality, not generation quality. The LLM can still produce a poor suggestion even when retrieval confidence is high.

**No Negative Feedback Loop**
Recording a fix improves future suggestions for similar errors, but there is no mechanism to learn from unhelpful or incorrect AI suggestions. A production system needs explicit user feedback to flag bad responses.

## Future Work

**Fine-Tuning the Embedding Model**
Fine-tune an embedding model on engineering-specific vocabulary (like specific Java exception classes) to better align raw stack traces with plain English records.

**Hybrid Search**
Implement a two-pass retrieval system combining semantic vector search with keyword-based BM25 search to catch exact matches (like `PSQLException`).

**Feedback Endpoint**
Add a `/feedback` endpoint to capture engineer ratings on AI suggestions, building a dataset for future model fine-tuning.