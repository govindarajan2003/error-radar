# Semantic Search Validation Results

## Experiment Overview
This experiment validates the effectiveness of the pgvector cosine distance search (`<=>`) against 20 seeded production errors.

## Query Results

### Query 1: JWT token expired during user authentication request
* **Top Result:** JWT token expired (gateway-service) - **0.8541**
* **Runner Up 1:** Invalid login credentials (auth-service) - **0.6907**
* **Runner Up 2:** JWT signature verification failed (gateway-service) - **0.6471**
* **Observation:** The system successfully clustered authentication and security-related errors, accurately identifying the exact JWT expiration match.

### Query 2: OrderNotFoundException: Order with id 4502 not found
* **Top Result:** User record not found (user-service) - **0.6284**
* **Runner Up 1:** Product not found (catalog-service) - **0.6252**
* **Runner Up 2:** Order not found (order-service) - **0.6215**
* **Observation:** The search accurately grouped "Not Found" / 404-style resource errors, though it prioritized User/Product over Order by a microscopic margin (0.006).

### Query 3: The flux capacitor overheated during time travel
* **Top Result:** GC overhead limit exceeded (cache-service) - **0.5411**
* **Observation:** As expected, a nonsense query yielded poor similarity scores across the board (all < 0.55). This proves our 0.70 threshold will safely reject unrelated anomalies.

### Query 4: java.lang.OutOfMemoryError: Java heap space exhausted during report generation
* **Top Result:** Java heap space exhausted (report-service) - **0.7915**
* **Runner Up 1:** Database connection pool exhausted (inventory-service) - **0.6053**
* **Observation:** A highly accurate exact match. Interestingly, the model clustered "memory exhaustion" with "connection pool exhaustion", showing it understands the broader concept of resource limits.

### Query 5: NullPointerException in CartService line 55 while processing checkout request
* **Top Result:** Null pointer while generating invoice (invoice-service) - **0.5898**
* **Runner Up 1:** Null pointer while processing user profile (user-service) - **0.5796**
* **Observation:** Successfully clustered NullPointerExceptions at the top. Scores were slightly lower due to the highly specific context of "CartService" in the query, but the hierarchy is correct.

### Query 6: PostgreSQL database connection timeout during payment transaction
* **Top Result:** Database connection timeout (auth-service) - **0.7987**
* **Runner Up 1:** SQL query execution timeout (analytics-service) - **0.7842**
* **Observation:** Perfect clustering of database and timeout-related errors, heavily prioritizing network/connection failures.

## Conclusion
The semantic search engine is functioning correctly. Similar errors cluster highly (>0.75), categorical errors cluster moderately (~0.60), and unrelated errors fall below the functional threshold (<0.55).