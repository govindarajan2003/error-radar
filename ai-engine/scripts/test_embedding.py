import requests
import sys

url = 'http://localhost:11434/api/embed'

# Input error message to be converted into an embedding vector
error = "java.lang.NullPointerException: Cannot invoke 'String.trim()' because 'line' is null"

# Embedding model name 
model = "nomic-embed-text"

# Payload structure required by ollama's /api/embed endpoint
# 'input' is the text to embed.
payload = {
    'model':model,
    'input':error
    }


# Send request to local ollama server.
# Assumption: ollama daemon is running on localhost:11434
try:
    response = requests.post(url, json = payload)
except requests.exceptions.ConnectionError:
    print("Ollama is not running. Start it with ollama server.")
    sys.exit(1)
except:
    print("Error has occured, please try again later")
    sys.exit(1)

# Raw response (useful for debugging)
print(response.text)

# Parse JSON response to access structured data.
data = response.json()

# Embedding vector is returned as a list of floats.
# We check its dimensionality to validate correctness.
embedding_length = len(data['embeddings'][0])
print(f"Embedding length: {embedding_length} dimensions")

# Performance metrics returned by ollama (in nanoseconds)
# Convert to milliseconds for readability
total_durations = data['total_duration']
print(f"Total duration = {total_durations/1000000} ms")

load_durations = data['load_duration']
print(f"Load durr = {load_durations/1000000} ms")