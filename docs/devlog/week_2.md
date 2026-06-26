# Week 2 Devlog: Embedding Service Module and Database Integration

## Objective

The goal for Week 2 was to transition from exploratory scripts to production code. The focus shifted to building `ai-engine/services/embedding_service.py` with a strong emphasis on designing for failure, testability, and clear interfaces. This module acts as the bridge between the backend and the AI layer, taking sanitized error traces and converting them into vector embeddings for storage.

---

## Day 1: Designing for Failure and Dependency Injection

Instead of jumping straight into the happy path, started by identifying potential failure points: the Ollama server going down, API timeouts, and unexpected vector dimensions.

*   Defined custom exceptions upfront in `ai-engine/services/embedding_service.py` to provide clean signals to downstream systems.
*   Created `OllamaUnavailableError`, `OllamaTimeoutError`, and `EmbeddingDimensionError`.
*   Moved hardcoded values like the API URL and model name into `ai-engine/.env` using `dotenv`. This allows easy configuration changes across different machines without touching the code.
*   Discovered Python type hints. Added them to function signatures to make the code more readable and maintainable for collaboration.
*   Caught a sneaky bug with default parameters. Using `os.getenv()` directly in the function signature bakes the value at definition time, breaking unit test overrides. Moved the environment variable resolution inside the function body to allow dynamic overrides.

---

## Day 2: Implementing `get_embedding` and Backoff Logic

With the skeleton in place, implemented the core API call logic in `ai-engine/services/embedding_service.py`.

*   Added proper docstrings to explain the function's purpose, arguments, return types, and raised exceptions. Realized inline comments are not enough for industry-standard code.
*   Implemented exponential backoff for `requests.exceptions.Timeout`. The system now waits 1s, 2s, 4s before giving up.
*   Made a deliberate decision NOT to retry on `requests.exceptions.ConnectionError`. If the daemon is completely offline, retrying is pointless. It immediately raises `OllamaUnavailableError`.

---

## Day 3: The `embed_error` Bridge Layer

Built the `embed_error` function to act as a pipeline connector between the backend API and the embedding layer.

*   The function takes an `error_id` and a `sanitized_trace`. It calls `get_embedding` and prepares the vector for database storage.
*   Initially mocked the database insert with a simple print statement to avoid blocking progress while waiting for the database layer to be ready.
*   Spotted a dumb bug. Passed the literal `str` type to `get_embedding` instead of the `sanitized_trace` variable. Fixed it so it actually embeds the error content.

---

## Day 4: Unit Testing and Exception Masking

Started writing unit tests in `ai-engine/tests/test_embedding.py` using `pytest` and `unittest.mock.patch`. This was a new concept but made sense quickly.

*   Mocked `requests.post` to simulate connection errors, timeouts, and successful embeddings without needing the real Ollama server running.
*   Wrote a test for incorrect embedding dimensions. Passed a 788-dimension vector and expected an `EmbeddingDimensionError`.
*   Hit a frustrating bug. The generic `except Exception` block in `get_embedding` was catching the custom `EmbeddingDimensionError` and wrapping it in a standard `Exception`. This masked the specific error type from the unit test.
*   Fixed the issue by adding a specific `except EmbeddingDimensionError` block before the generic catch-all. Order of exception blocks matters.

---

## Day 5: Neon Database Integration and Vector Formatting

Connected the application to a real cloud database using Neon. Stored the connection URL in `ai-engine/.env`.

*   Anticipated a lazy engine issue. If the environment variables are not loaded properly, the application would crash with an obscure error. Added an explicit check to raise `EnvironmentError` if `DATABASE_URL` is missing.
*   Set up the `errors` table in Neon with the `vector` extension enabled, defining the embedding column as `VECTOR(768)`.
*   Updated `embed_error` to write vectors to the database using raw SQL via SQLAlchemy `text()`.
*   Fixed a vector formatting issue. Using a plain `str(vector)` conversion could cause format mismatches with pgvector. Updated the logic to format it explicitly as `"[" + ",".join(str(v) for v in vector) + "]"`.
*   Wrote an integration test in `ai-engine/tests/test_integration.py`. The test inserts a dummy row, runs `embed_error`, verifies the embedding column is no longer null, and cleans up the row. 
*   Fixed the timeout unit test to assert `mock_post.call_count == 3`, proving the retry logic actually hits the API three times before failing.

---

## End of Week 2 Status

*   **Module Complete:** `ai-engine/services/embedding_service.py` is written with custom exceptions, retry logic, and dimension validation.
*   **Test Coverage:** Unit tests in `ai-engine/tests/test_embedding.py` pass without Ollama running by using mocks. Integration tests in `ai-engine/tests/test_integration.py` successfully write and verify vectors in the live Neon database.
*   **Database Integration:** Vectors are correctly formatted and inserted into the Neon `VECTOR(768)` column.
*   **Next Steps:** Communicate the custom exception class names to Dev A so they can catch `OllamaUnavailableError` properly in their API endpoints. Begin working on the RAG service module for semantic search.