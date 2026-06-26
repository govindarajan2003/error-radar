# Week 3 Devlog: Semantic Search and Vector Indexing

## Objective

This week was about moving from just generating embeddings to actually retrieving useful data. The goal was to build the semantic search module, seed the database with realistic production errors, and prove that vector similarity actually works. I also had to face my fear of unit testing and figure out how to mock database calls properly.

---

## Day 1: Seeding Realistic Production Data

Needed real data to test retrieval. So I created 20 production-style errors covering NullPointers, DB timeouts, and auth failures. I put this into `ai-engine/scripts/seed.py`.

The script checks if an error already exists, inserts it if not, grabs the new ID, and calls `embed_error()` from `ai-engine/services/embedding_service.py` to generate the vector. 

Ran into a weird issue with the `INSERT ... RETURNING id` query. The returned value wasn't just an integer. I had to use SQLAlchemy's `.scalar()` method to actually extract the integer ID. Before that, the vector updates were failing because I was passing a weird object instead of an ID.

---

## Day 2: Semantic Search with Vector Similarity

Built the core retrieval logic in `ai-engine/services/rag_service.py`. This is where semantic search happens.

Instead of matching keywords, it compares meanings using cosine distance. I used the pgvector `<=>` operator to calculate the distance. But distance is confusing. A score of 0 means identical, 2 means opposite. I converted it to a similarity score using `1 - (embedding <=> :query_vector)`. Now a score of 0.95 means almost identical.

I implemented `find_similar_errors()` which takes a query string, embeds it, and searches the database. I also added a `min_similarity` threshold defaulting to 0.70 to filter out weak matches.

---

## Day 3: Validation Experiments

Wrote `ai-engine/scripts/validation_experiment.py` to test if the search actually works. 

I threw several queries at it covering NPEs, DB timeouts, auth failures, and memory errors. The authentication query matched other auth failures perfectly with a score of 0.85. 

I even threw in a completely unrelated query about a flux capacitor overheating during time travel. The system correctly returned low scores around 0.54 and filtered them out. It was pretty cool to see it group errors by meaning even when the service names and wording were totally different.

---

## Day 4: IVFFlat Indexing for Performance

Looked into optimizing the vector search using IVFFlat indexing in pgvector. IVFFlat groups vectors into clusters to speed up retrieval.

I created the index using `USING ivfflat (embedding vector_cosine_ops)`. 

I set `WITH (lists = 1)` because my dataset only has 20 records. The rule of thumb is `lists = rows / 1000`. Splitting 20 rows into multiple lists would just hurt performance. 

I did learn a major limitation though. The index is built using the data that exists right now. If the dataset grows to 100,000 records later, the clusters will be completely outdated. I will have to rebuild the index when the data scales.

---

## Day 5: Unit Testing and Mocking

Finally sat down to write unit tests in `ai-engine/tests/test_rag.py`. I will admit I procrastinated on this because the mocking syntax looked like gibberish.

I used `@patch()` decorators to mock `get_embedding` and `engine.connect`. The hardest part was figuring out that decorators stack in reverse order. The bottom patch maps to the first test parameter. 

I also had to chain `MagicMock` returns to simulate the database query flow. It looked insane at first, but once I broke it down it mirrored the `with engine.connect() as conn:` flow perfectly. I wrote tests for the happy path, empty results, and similarity threshold filtering.

I made a deliberate choice NOT to put a try/except block for `OllamaUnavailableError` inside `find_similar_errors`. If I caught it and returned an empty list, the API caller would just think there are no similar errors. They wouldn't know the system actually crashed. It is better to let the exception propagate.

I also fixed a unit test in `ai-engine/tests/test_embedding.py`. I added `assert mock_post.call_count == 3` to prove the retry logic actually hits the API three times before giving up.

---

## End of Week 3 Status

*   **Database Seeded:** 20 realistic production errors with vectors stored in Neon pgvector via `ai-engine/scripts/seed.py`.
*   **Search Module Complete:** `ai-engine/services/rag_service.py` successfully retrieves semantically similar errors using cosine distance and thresholding.
*   **Testing Established:** Unit tests in `ai-engine/tests/test_rag.py` cover core logic using mocks. Retry logic verified in `ai-engine/tests/test_embedding.py`.
*   **Next Steps:** Move towards LLM generation. Take the retrieved similar errors and feed them to Mistral to generate a suggested fix.