# Week 7 Devlog: System Evaluation and Architecture Documentation

## Objective

The goal for Week 7 was to step back from writing features and critically evaluate the system. I needed to measure the retrieval accuracy using the Precision at 1 (P@1) metric, document the architecture decisions, and analyze the limitations of the current RAG pipeline.

---

## Day 1: P@1 Evaluation

Started by defining what P@1 means for this project. If the top result returned by the system is relevant, it gets a 1. If not, it gets a 0. I wrote a driver script in `ai-engine/scripts/evaluate_rag.py` to run 10 blind test queries against the database.

*   Ran the tests and got a final score of 0.70 (70%). The system did great with well-represented categories like NullPointers and JWTs.
*   Hit some failures on Test 4, 7, and 8. The embedding model struggled to bridge the gap between raw Java exception syntax (like `org.postgresql.util.PSQLException`) and plain English database records (like "Database connection timeout"). 
*   The similarity scores just dropped below my 0.70 threshold. It showed me that semantic search has limits when technical jargon diverges too far from natural language descriptions.

---

## Day 2: Architecture and Prompt Documentation

Spent time writing out the actual system architecture. Documented why I chose local embeddings via Ollama instead of OpenAI to keep PII inside the host machine and eliminate API latency. 

*   Explained the pgvector setup on Neon and why I am using an IVFFlat index with `lists=1` for now.
*   Reviewed the prompt design in `ai-engine/prompts/suggestion.txt`. 
*   The biggest win was the RAG override instruction. I ran A/B tests on a Database Timeout error. Without the override, the LLM gave generic advice like "check your pool configuration". With the override, it used the historical context and suggested "bump timeout to 30000ms".
*   Documented why I ripped confidence scoring out of the LLM. Mistral was just hallucinating 0.95 every single time. Moving that calculation to the Python backend fixed it.

---

## Day 3: Analyzing Limitations and Future Work

Had to be honest about the gaps in the system. 

*   The 25-record seed dataset is way too sparse. The vector space needs more data to improve retrieval accuracy for edge cases.
*   Noted that my IVFFlat index provides no real performance benefit at 20 rows. I will need to increase the `lists` parameter once I hit 10,000 rows.
*   The confidence score in the UI only measures retrieval quality, not generation quality. The LLM can still spit out a bad suggestion even if the similarity score is high. 
*   There is no negative feedback loop right now. The system learns from recorded fixes, but it has no way to learn from unhelpful AI suggestions.

---

## End of Week 7 Status

*   **Evaluation Complete:** P@1 score is 0.70. Failures analyzed and documented.
*   **Architecture Documented:** Rationale for embedding, storage, and generation choices is written down.
*   **Limitations Identified:** Sparse dataset, index scaling needs, and lack of feedback loops are on the radar.
*   **Next Steps:** Fine-tune an embedding model on engineering vocabulary, implement a two-pass hybrid search combining vector and keyword matching, and add a `/feedback` endpoint to capture engineer ratings.