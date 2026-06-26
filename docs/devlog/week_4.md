# Week 4 Devlog: API Integration and End-to-End Validation

## Objective

The goal for Week 4 was to wrap the RAG pipeline in a FastAPI application, wire up the local Mistral model for generating fix suggestions, and validate the entire system end-to-end. The focus shifted from isolated scripts to building a real product, handling unreliable LLM outputs, fixing schema drift, and running a formal evaluation of the model's suggestions.

---

## Day 1: FastAPI and Pydantic Setup

Started working with FastAPI for the first time. Configured the basic application in `ai-engine/main.py`.

*   Defined the `QueryRequest` Pydantic model to handle JSON validation automatically. No more manual checks for missing fields.
*   Launched the app using `uvicorn main:app --reload` and discovered the auto-generated Swagger UI at `/docs`.
*   Tested the `/query` endpoint. FastAPI successfully converts the JSON body into a Python object, executes logic, and serializes the response.
*   Noticed FastAPI automatically handles `422 Unprocessable Entity` errors for invalid payloads before the application logic even runs.

---

## Day 2: LLM Generation and Prompt Engineering

Implemented the core LLM generation logic in `ai-engine/services/rag_service.py` using a prompt template stored in `ai-engine/prompts/suggestion.txt`.

*   The `generate_suggestion()` function loads the prompt, injects the new error and historical context, and sends it to Ollama.
*   Learned that LLMs do not always follow instructions. Even when asked for raw JSON, Mistral sometimes wraps the output in Markdown code blocks.
*   Added cleanup logic to strip ` ```json ` and ` ``` ` markers before attempting to parse the response.
*   Implemented `response.raise_for_status()` to catch HTTP errors like 400, 401, 404, and 500 from the Ollama API, rather than just handling timeouts and connection errors.

---

## Day 3: FastAPI Server and String Formatting

Connected the retrieval and generation layers in `ai-engine/main.py` and hit a frustrating issue with Python string formatting.

*   Used `str.format()` to inject variables into the prompt template, but Python tried to substitute the JSON schema's curly braces.
*   Fixed this by escaping literal curly braces in `ai-engine/prompts/suggestion.txt` using double braces (`{{` and `}}`).
*   Tested the full pipeline through Swagger UI. A request traveled from FastAPI to the database, to Mistral, and back as structured JSON.
*   Removed debug print statements (`print("1")`, `print("2")`) from the `/query` endpoint to keep production code clean.

---

## Day 4: Filtering API and Optional Parameters

Built a filtering API in `ai-engine/main.py` to retrieve errors based on resolution status, backed by a database function in `ai-engine/repositories/error_repo.py`.

*   Learned why `Optional[bool]` is necessary. A normal boolean only gives True or False, but filtering requires a third state (`None`) to return all errors regardless of status.
*   Dynamically built SQL queries in SQLAlchemy based on user input.
*   Discovered that SQLAlchemy handles empty parameter dictionaries gracefully, as long as the SQL query string does not contain any bind parameters.
*   Exposed the endpoint at `/errors` and verified it returned structured JSON sorted by newest errors first.

---

## Day 5: End-to-End Testing and Evaluation

Moved beyond isolated unit tests and simulated real production traffic using `ai-engine/scripts/log_test_errors.py`.

*   The first test run failed with a 500 error. The test script successfully reached the API, which narrowed the problem down to the backend.
*   Fixed the backend issue and ran the test again. The entire pipeline completed successfully.
*   Caught severe schema drift. The prompt defined `suggested_fix` as a string, but Mistral kept returning a dictionary of options.
*   Updated `ai-engine/prompts/suggestion.txt` with aggressive constraints, explicitly stating the field must be a single flat string and not an object or array.
*   Noticed every response had a confidence score of 0.95. The LLM was blindly spitting out that number.
*   Ripped the confidence field out of the prompt entirely. Now calculating it deterministically in `ai-engine/services/rag_service.py` by averaging the cosine similarity scores of retrieved historical errors.
*   Bumped the temperature from 0 to 0.1 to prevent repetitive and rigid outputs.
*   Ran 10 different error types through the API and documented the results in `ai-engine/scripts/generation_evaluation.md`.

---

## End of Week 4 Status

*   **API Complete:** FastAPI application running with `/query` and `/errors` endpoints in `ai-engine/main.py`.
*   **Schema Fixed:** Enforced strict JSON string formatting for suggestions in `ai-engine/prompts/suggestion.txt`.
*   **Evaluation Done:** Generated `ai-engine/scripts/generation_evaluation.md` with 10 test cases scoring Good or Acceptable.
*   **Next Steps:** Close out Week 4 and move into Week 5. Focus on tighter API integration and preparing for frontend development.