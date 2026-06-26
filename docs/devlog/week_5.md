# Week 5 Devlog: Architecture Refactor and RAG Context Injection

## Objective

The goal for Week 5 was to clean up the codebase by enforcing a strict three-layer architecture, inject human-written historical fixes into the LLM prompt to improve suggestion quality, and implement deduplication logic for incoming errors. 

---

## Day 1: Three-Layer Architecture and Fixes API

Database operations, business logic, and API routes were tangled together. Spent time refactoring the project into distinct layers: Controller, Service, and Repository.

*   **Controller Layer:** `ai-engine/api/routes/error_routes.py` now strictly handles HTTP requests and converts application exceptions into HTTP responses.
*   **Service Layer:** `ai-engine/services/rag_service.py` handles business rules like preventing empty fix descriptions and coordinating updates.
*   **Repository Layer:** `ai-engine/repositories/error_repo.py` is completely isolated and only interacts with the database.
*   Built a new endpoint to accept an error ID and fix description, then update the database.
*   Used `result.rowcount > 0` in the repository to check if an update actually happened. If not, the service layer raises a custom `ErrorLogNotFoundError` from `ai-engine/exceptions/database_exceptions.py`.
*   Updated `get_all_errors_from_db` in `ai-engine/repositories/error_repo.py` to include the `past_fix` column in the API response.

---

## Day 2: Seeding Human Fixes and RAG Evaluation

Ran a script to seed the Neon database with realistic, human-written `past_fix` strings for historical errors.

*   Modified `generate_suggestion()` in `ai-engine/services/rag_service.py` to inject the top 3 similar historical errors and their `past_fix` data into the LLM prompt.
*   Ran integration tests in `ai-engine/scripts/log_test_errors.py` to compare the output against Week 4.
*   Noticed a massive improvement in output quality. The LLM stopped suggesting generic boilerplate advice.
*   For database timeouts, the system now explicitly suggested "bumping to 30000ms" and optimizing indexing configurations, pulling vocabulary directly from the injected human fixes.
*   For memory errors, the LLM transitioned from basic `-Xmx` arguments to advanced architectural recommendations like streaming pagination. 

---

## Day 3: Deduplication Logic and Testing

Built a new `/log-error` endpoint in `ai-engine/api/routes/error_routes.py` to ingest new errors.

*   Implemented deduplication logic in `ai-engine/services/rag_service.py`. Generates an embedding for the incoming error and checks the database for a cosine similarity score above 0.9.
*   If a match is found, the system increments the `occurrence_count` and updates the `last_seen_at` timestamp instead of inserting a duplicate row.
*   Wrote unit tests in `ai-engine/tests/test_deduplication.py` to verify the logic. 
*   Ran the full test suite and found that the recent refactoring broke older tests. Updated the mocking paths in `ai-engine/tests/test_rag.py` to point to the new module paths.
*   Fixed a typo in the database column name, changing "occurance" to "occurrence" across the codebase.

---

## End of Week 5 Status

*   **Architecture Cleaned:** Codebase strictly separated into `ai-engine/api/routes/`, `ai-engine/services/`, and `ai-engine/repositories/`.
*   **RAG Quality Improved:** Human fixes are successfully injected into the prompt, resulting in highly actionable AI suggestions.
*   **Deduplication Complete:** New errors are checked against existing records to prevent duplicate database entries.
*   **Next Steps:** Finalize API contracts and begin preparing the system for frontend integration.