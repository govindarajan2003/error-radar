# RAG Retrieval Evaluation (Precision at 1)

## Methodology
We use Precision at 1 (P@1) to evaluate the retrieval system, scoring a `1` if the top result matches the expected category and `0` if it is irrelevant or falls below the confidence threshold. In an automated RAG pipeline, the top result heavily influences the LLM's final diagnosis, making P@1 the most practical metric for catching retrieval failures. 

I designed 10 test queries using varied phrasing and error traces not present in the seed data. Relevance was judged manually rather than via keyword matching, since automated keyword checks fail to capture semantic intent.

## Test Set

| **ID** | **Query Summary** | **Expected Category** | **Top Match** | **Score** | **Status** |
| :--- | :--- | :--- | :--- | :--- | :--- |
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

## Results & Interpretation
**Final P@1 Score: 0.70 (70%)**

The system hit the 70% target, showing strong retrieval for well-represented categories like Null Pointers and JWTs. However, the search algorithm struggled with three specific cases where relevant records actually existed in the database:

*   **Test 4 (DB Timeout):** The algorithm caught "TimeoutError" in Test 3, but the specific phrasing here (`org.postgresql.util.PSQLException`) dropped the similarity score below the 0.70 threshold, causing it to miss the existing timeout record.
*   **Test 7 (Resource Not Found):** The embedding model failed to correlate the technical `UserProfileNotFoundException` string with the simpler database record "User record not found."
*   **Test 8 (Out of Memory):** An exact root-cause match exists in the database, but the embeddings couldn't bridge the gap between the Java exception syntax and the plain English description.

## Limitations

**Semantic Gaps**
When the structure differs significantly—such as a raw Java stack trace versus a plain English summary—the embedding model struggles to recognize the similarity, causing false negatives.

**Small Seed Dataset**
The system currently relies on roughly 25 seeded records. A sparse vector space directly impacted the failures in the Not Found and OOM categories; a larger dataset is required to populate the vector space effectively.

**Single Annotator**
The Pass/Fail judgments were made by a single developer. A more robust evaluation would involve multiple engineers grading the results to remove personal bias.

**Strict P@1 Metric**
Measuring only the absolute top result is unforgiving. Tracking P@3 (Precision at 3) or MRR (Mean Reciprocal Rank) would provide a better picture of whether the correct context is at least making it into the top 3 results passed to the LLM.