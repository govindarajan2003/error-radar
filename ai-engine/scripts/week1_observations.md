
# Week 1 Observations

---

## 🔹 Embedding Model Findings

- The embedding vector created using `nomic-embed-text` uses **768 dimensions**
    
- The dimension **remains consistent regardless of input**
    

### Why this matters

- Required for **vector database storage**
    
- Ensures compatibility for **similarity search** (cosine similarity, etc.)
    
- Prevents dimension mismatch errors in retrieval pipelines
    

---

## 🔹 Ollama Embedding API Response Structure

```json
{
  "model": "nomic-embed-text",
  "embeddings": [[0.048153706, -0.018771712, -0.11261949, ... , -0.050136752]],
  "total_duration": 84908800,
  "load_duration": 30895900,
  "prompt_eval_count": 25
}
```

### Notes

- `embeddings` → list of vectors (each vector is a list of floats)
    
- `total_duration` → total processing time (nanoseconds)
    
- `load_duration` → model loading time (nanoseconds)
    
- `prompt_eval_count` → number of tokens processed
    

---

## 🔹 Vector Comparison Experiment

### Input 1

`java.lang.NullPointerException: Cannot invoke 'String.trim()' because 'line' is null`

#### Iterations (First 5 values)

```
0.048153706,
-0.018771712,
-0.11261949,
-0.06635322,
0.07208312
```

(Same values observed across 5 iterations)

---

### Input 2

`java.lang.NullPointerException: Cannot invoke 'String.trim()'`

#### Iterations (First 5 values)

```
0.048153706,
-0.018771712,
-0.11261949,
-0.06635322,
0.07208312
```

(Same values observed across 5 iterations)

---

### Observations

- Embeddings are **deterministic**
    
- Same input → **identical vectors across runs**
    
- Minor input change (shortened message) still produced **identical prefix values**
    

👉 This makes embeddings **reliable for caching and retrieval systems**

---

## 🔹 Ollama Generate API Response Structure

```json
{
  "model": "mistral",
  "created_at": "2026-04-30T18:03:12.9427934Z",
  "response": "{ \"root_cause\": \"...\", \"suggested_fix\": \"...\" }",
  "done": true,
  "done_reason": "stop",
  "context": [3, 29473, ...],
  "total_duration": 5120896400,
  "load_duration": 3470286300,
  "prompt_eval_count": 82,
  "prompt_eval_duration": 67966800,
  "eval_count": 88,
  "eval_duration": 1197316200
}
```

### Notes

- `response` → **stringified JSON** (must be parsed again using `json.loads`)
    
- `context` → token context window
    
- `eval_count` → number of tokens generated
    
- `eval_duration` → generation time (nanoseconds)
    

---

# 🔹 Temperature Experiment

---

## Hypothesis

Temperature controls how creatively the model responds.

---

## Temperature = 1 (High Creativity)

### Iteration 1

```json
{
  "error": {
    "type": "java.lang.NullPointerException",
    "message": "Cannot invoke 'String.trim()' because 'line' is null",
    "root_cause": "...",
    "suggested_fix": "..."
  }
}
```

### Iteration 2

```json
{
  "error_type": "NullPointerException",
  "description": "...",
  "root_cause": "...",
  "suggested_fix": "..."
}
```

### Observations

- Model **ignored schema**
    
- Added extra fields (`type`, `description`)
    
- Changed structure
    

👉 AI takes **creative liberty**

---

## Temperature = 0 (Deterministic)

### Iterations (1–10)

```json
{
  "root_cause": "The variable 'line' is being used before it has been assigned a value.",
  "suggested_fix": "Ensure that the 'line' variable is properly initialized before using it."
}
```

(Same output across all iterations)

---

### Key Observations

- Output is **consistent**
    
- Schema is **strictly followed**
    
- No extra fields added
    

---

### Key Learnings

- Temperature directly impacts **schema reliability**
    
- High temperature → **creativity → schema drift**
    
- Low temperature → **determinism → schema adherence**
    
- Prompt alone is **not enough** — parameters matter
    

---

# 🔹 Timeout, Connection Errors & Retry Strategy

---

## Problem

Real systems are unreliable:

- Server may fail
    
- Model may not respond
    
- Network issues can occur
    

---

## Experiment

- Simulated failures using **very low timeout**
    
- Implemented **exception handling**
    
- Added **exponential backoff**
    

---

## Retry Strategy

- Initial timeout → intentionally low (forces failure)
    
- On failure:
    
    - Wait time increases exponentially (`1 → 2 → 4 → 8`)
        
- Final attempt:
    
    - Uses normal timeout → allows success
        

---

## Key Learnings

- Systems must handle **transient failures**
    
- Retry with backoff improves **resilience**
    
- Proper exception handling prevents crashes
    
- Recovery logic is as important as failure detection
    

---

## 🔹 API Access Patterns

- To get embedding vector:
    
    ```python
    data['embeddings'][0]
    ```
    
- To get generated response:
    
    ```python
    data['response']
    ```
    

---

# Final Insight

LLM systems are not just about prompts — they require:

- Structured outputs
    
- Deterministic control
    
- Failure handling
    
- Performance awareness
    

👉 This week focused on building the **foundation of a reliable AI system**, not just calling a model.
