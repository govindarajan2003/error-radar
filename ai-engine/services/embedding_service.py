import os
from dotenv import load_dotenv
import requests
import time

# Loads environment variable into process
load_dotenv()

# Raised when Ollama server is unreachable (e.g. not running or wrong URL)
class OllamaUnavailableError(Exception):
    pass

#Raised when request exceeds retry attempts due to timeout
class OllamaTimeoutError(Exception):
    pass

# Raised when embedding vector does not match expected dimensions
class EmbeddingDimensionError(Exception):
    pass

# Call ollama server, embeds the input 
# Returns embedding vector (list[int])
    
def get_embedding(
        text: str,
        url: str = None,
        model: str = None
    ) -> list[float]:
    """
    Calls Ollama embedding API and returns embedding vector.

    Args:
        text: Input text to embed
        url: Optional override for Ollama base URL
        model: Optional override for embedding model

    Returns:
        List of floats representing embedding vector

    Raises:
        OllamaUnavailableError
        OllamaTimeoutError
        EmbeddingDimensionError
    """
    # Resolve configuration (allows overrides for testing)
    api_url = url or os.getenv('OLLAMA_BASE_URL')
    api_url += "/api/embed"

    model_name = model or os.getenv('EMBEDDING_MODEL')

    payload = {
        'model':model_name,
        'input':text
    }

    max_attempt = 3
    wait_time = 1
    for attempt in range(max_attempt):
        try:
            # Make request to ollama embedding endpoint
            response = requests.post(api_url, json = payload, timeout = 10.00)
            
            data = response.json()
            # Validate embedding dimension
            embed_length = get_vector_length(data)
            if(embed_length != 768):
                raise EmbeddingDimensionError(f"Expected 768 dimensions, got {embed_length} dimensions!")
            return get_embedded_vector(response.json())
            
        except requests.exceptions.ConnectionError:
            raise OllamaUnavailableError("Ollama daemon is unreachable!")

        except requests.exceptions.Timeout:
            if attempt < max_attempt-1:
                time.sleep(wait_time)
                wait_time *= 2
                continue
            raise OllamaTimeoutError("Embedding request timed out after multiple attempts!")

        except Exception as e:
            raise Exception(f"Unexpected error: {e}")
    
    
def get_vector_length(response: dict) -> int:
    """
    Extracts embedding vector length from response.
    Assumes response format: { 'embeddings': [[...]] }
    """
    embedding_length = len(response['embeddings'][0])
    return embedding_length

def get_embedded_vector(response:dict) -> list[float]:
    """
    Extracts embedding vector from response.
    """
    return response['embeddings'][0]

