# Week 6 Devlog: Stats APIs, Sanitization, and Frontend

## Objective

The goal for Week 6 was to expose error statistics for trend analysis, secure the logging pipeline by sanitizing PII, and begin building a frontend dashboard to visualize the data. 

---

## Day 1: Building the Stats APIs

I started by building two new endpoints in `ai-engine/api/routes/error_routes.py` to expose error statistics. The first one is `/errors/stats`, which just returns the total error count, unresolved count, and the most frequently occurring error. The second one is `/errors/stats/daily`, which takes an interval parameter and returns the daily error counts so I can chart trends. 

I kept the three-layer architecture intact, pushing the raw SQL down into `ai-engine/repositories/error_repo.py` and keeping the aggregation logic in `ai-engine/services/stats_service.py`. Getting the date interval SQL right was a fun little puzzle. I ended up using `NOW() - (:interval * INTERVAL '1 day')` to filter the timeframe dynamically.

---

## Day 2: PII Sanitization

While testing the log ingestion, I looked at the stack traces and realized they were full of PII. Emails, IP addresses, JWT tokens, and API keys were just sitting there in plain text. I wrote a sanitizer function to redact all that personal info before the traces ever hit the database. Now, when a trace comes in, it scrubs out emails and IPs and replaces them with `REDACTED EMAIL` and `REDACTED IP ADDRESS`.

I had a minor scare with the sanitizer function early on. My initial regex was too greedy and started eating parts of the actual stack trace that I needed for debugging. I had to tune the patterns to specifically target the `Request Context` section where the user emails and tokens were dumped, leaving the actual Java exception lines alone.

---

## Day 3: Frontend Shell and CORS

With the backend stable, I started building a single-page frontend dashboard in `ai-engine/index.html`. It is mostly HTML and CSS right now to get the layout looking decent. I called it "Error Radar". 

The classic frontend-backend hurdle hit me almost immediately. I fired up my local HTML file, tried to fetch data from the API, and nothing worked. The browser console was throwing errors. I spent way too long debugging my JavaScript fetch calls before realizing it was just CORS blocking the request. A quick addition of the FastAPI CORS middleware in `ai-engine/main.py` fixed it, but it took me a minute to get there.

---

## End of Week 6 Status

*   **Stats APIs Complete:** `/errors/stats` and `/errors/stats/daily` are functional and returning data.
*   **Sanitization Added:** PII is successfully redacted from stack traces before database insertion.
*   **Frontend Started:** Basic HTML/CSS shell exists in `ai-engine/index.html`, and CORS is configured.
*   **Next Steps:** Write the JavaScript to fetch the stats and populate the error table dynamically. Wire up the "mark as resolved" button and look into charting libraries to make the daily stats look like an actual graph.