import os
from dotenv import load_dotenv

# Loads environment variable into os
load_dotenv()

# Custom error: Triggered when the server is not running or bad request (503 status code)
class OllamaUnavailableError(Exception):
    pass

# Custom error: Triggered when server takes more time than expected
class OllamaTimeoutError(Exception):
    pass

# Custom error: Triggered when vector embedding dimensions anything other than 768
class EmbeddingDimensionError(Exception):
    pass

# Call ollama server, embeds the string.
def get_embedding(
        text: str,
        url: str = None,
        model: str = None
    ) -> list[float]:
    api_url = url or os.getenv('OLLAMA_API_URL')
    model_name = model or os.getenv('EMBEDDING_MODEL')
    print(url)
    print(model_name)


get_embedding()