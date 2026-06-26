# Week 8 Devlog: Integration Testing and the Demo App

## Objective

The goal for Week 8 was to secure the repository, write end-to-end integration tests, and build a separate demo application to generate real errors and feed them into the AI engine. 

---

## Day 1: Git Securing and Integration Tests

Started by making sure I didn't accidentally leak secrets. I ran `git log --all --full-history -- .env` to check if the `.env` file was anywhere in the commit history. Thankfully, nothing returned. 

I then wrote integration tests in `ai-engine/tests/test_integration.py` using FastAPI's `TestClient`. I wanted to verify the main endpoints actually worked together. 
*   Tested `/errors` to ensure it returned a 200 status code and a list of data.
*   Tested `/errors/stats` to make sure the response had the correct keys like `total` and `unresolved`.
*   Tested `/errors/999999/fix` with a dummy payload to confirm that fixing a non-existent error properly returns a 404 or 400.

All 3 tests passed. I saw a deprecation warning about `httpx` in the output, but the tests are green so I left it alone for now.

---

## Day 2: Building the Demo App

I needed a way to generate real, messy errors to feed into the system. I built an intentionally broken FastAPI app in `demo/main.py`. 
*   Created endpoints like `/crash/null-pointer` and `/crash/db-timeout` that just raise exceptions when hit.
*   Added a global exception handler in `demo/main.py` that catches the crash, formats the traceback, and POSTs it to the AI engine's ingestion endpoint.
*   Built a single-page frontend in `demo/index.html` to act as a crash trigger panel. It lets me fire individual crashes or log custom manual errors. 
*   Ran both apps side-by-side. The demo app ran on port 8001 and successfully talked to the AI engine on port 8000. Seeing the errors pop up in the TraceRAG backend felt like the project was finally a real product.

---

## Day 3: Discovering the Boilerplate Flaw

While testing the demo app, I noticed a massive flaw in my deduplication logic. Different errors coming from the same demo app were being flagged as duplicates. The occurrence count just kept going up instead of creating new records.

I initially blamed the 0.9 similarity threshold. But the real issue was how I was handling the stack traces. To keep the prompt manageable, I was truncating the trace to the first 300 characters. 

In a real application, the first 300 characters are just boilerplate FastAPI internal garbage. The actual error is at the very end of the trace. Because the boilerplate was identical across different errors, the embedding model thought they were the exact same error. This was a huge realization. Truncating the front of the trace completely destroys the semantic meaning for the deduplication check.

---

## End of Week 8 Status

*   **Tests Added:** Integration tests in `ai-engine/tests/test_integration.py` are passing.
*   **Demo App Complete:** `demo/main.py` and `demo/index.html` are fully functional and feeding errors to the backend.
*   **Architecture Flaw Found:** The 300-character truncation logic is broken for real-world stack traces.
*   **Next Steps:** Fix the truncation logic to grab the actual exception lines from the end of the trace instead of the first 300 characters. Then, finalize the system for presentation.