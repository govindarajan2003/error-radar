import os
import requests
import json
from dotenv import load_dotenv
from sqlalchemy import text, create_engine
from services.embedding_service import get_embedding
from pathlib import Path
from typing import Optional

# Loads environment values
load_dotenv()

# Creates engine for the database 
database_url = os.getenv('DATABASE_URL')
if not database_url:
    raise EnvironmentError("Database URL not set, check the .env file")
engine = create_engine(database_url)

def find_similar_errors(
        query_text: str,
        top_n: int = int(os.getenv('TOP_N_RESULTS', 5)),
        min_similarity: float = float(os.getenv('SIMILARITY_THRESHOLD', 0.70))
) -> list[dict]:
    """
    Executes a semantic similarity search using pgvector's cosine distance operator.
    
    Args:
        query_text (str): The incoming error stack trace or message.
        top_n (int): Max results to return. Defaults to env config.
        min_similarity (float): The threshold for filtering weak matches. Defaults to env config.
        
    Returns:
        list[dict]: A list of historical errors that semantically match the query, 
                    including their calculated similarity score (1 - distance).
    """
    # Fallback to Environment Variables if explicit parameters aren't passed
    # Wrapping in int() and float() ensures string configs are cast correctly.
    if top_n is None:
        top_n = int(os.getenv('TOP_N_RESULTS', 5))
    if min_similarity is None:
        min_similarity = float(os.getenv('SIMILARITY_THRESHOLD', 0.70))
    
    # Convert the incoming string to a 768-dimensional vector via local LLM
    vector = get_embedding(query_text)

    # Format strictly for pgvector compatibility (e.g., '[0.1, 0.2, ...]')
    query_vector = "[" + "," .join(str(v) for v in vector) + "]"
    
    # Execute Read-Only Transaction
    with engine.connect() as connection:
        query = text("""
            SELECT
                id,
                message,
                sanitized_trace,
                service_name,
                1 - (embedding <=> :query_vector) AS similarity_score
            FROM errors
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> :query_vector ASC
            LIMIT :top_n
        """)
        result = connection.execute(query,{
            'top_n': top_n,
            'query_vector': query_vector
        })
        
        rows = result.fetchall()
        results_list = []
        # Parse, Filter, and Format Results
        for row in rows:
            if row.similarity_score >= min_similarity:
                match = {
                    "id": row.id,
                    "message": row.message,
                    "sanitized_trace": row.sanitized_trace,
                    "service_name": row.service_name,
                    "similarity_score": round(row.similarity_score, 4)
                }
                results_list.append(match)
    return results_list

def generate_suggestion(
        query_text: str,
        similar_errors: list[dict],
) -> dict:
    """
    Generate a structured root-cause analysis and suggested fix for a new error.

    The function retrieves a prompt template from suggestion.txt, injects the
    incoming error and similar historical errors, then sends the completed prompt
    to the configured LLM through Ollama.

    Args:
        query_text (str): The incoming error stack trace or message.
        similar_errors (list[dict]): Previously encountered error similar to query_text
        
    Returns:
        dict: Returns a standardized JSON structure regardless of whether the LLM succeeds
    or fails.
    """

    model = os.getenv('LLM_MODEL')
    api_url = os.getenv('OLLAMA_BASE_URL') + "/api/generate"

    # Load the prompt template used to construct the LLM request.
    # Keeping prompts externalized allows prompt updates without code changes.
    try:
        project_root = Path(__file__).resolve().parent.parent
        suggestion_prompt_path = project_root / "prompts" / "suggestion.txt"

        with open(suggestion_prompt_path,"r") as suggestion:
            content = suggestion.read()
    
    except FileNotFoundError as e:
        return {
            "root_cause": "Prompt missing", 
            "suggested_fix": "Check file path", 
            "confidence": 0.0
        }

    
    prompt = content.format(
        query_error=query_text,
        historical_errors= json.dumps(similar_errors, indent=2)
    )

    payload = {
        'model':model,
        'prompt':prompt,
        'stream':False,
        'format':'json',
        'options':{
            "temperature": 0.1
        }
    }
    # Submit the generated prompt to the configured LLM endpoint and
    # retrieve the model's structured diagnostic response.
    try:
        response = requests.post(api_url, json=payload)
        response.raise_for_status()
        response_data = response.json()
        raw_text = response_data.get('response','')
    except  requests.exceptions.Timeout as err:
        return {
            "root_cause": "Connection Timeout", 
            "suggested_fix": "Try again Later", 
            "confidence": 0.0
        }
    except requests.exceptions.ConnectionError:
        return {
            "root_cause": "Connection Issue", 
            "suggested_fix": "Check if ollama engine is running", 
            "confidence": 0.0
        }
    except requests.exceptions.RequestException as err:
        return {
            "root_cause": "LLM API Error", 
            "suggested_fix": f"Network or HTTP error occurred: {str(err)}", 
            "confidence": 0.0
        }
    # Normalize the model output by removing markdown code fences.
    clean_text = raw_text.strip()
    if clean_text.startswith('```json'):
        clean_text = clean_text[7:]
    elif clean_text.startswith('```'):
        clean_text = clean_text[3:]
    if clean_text.endswith('```'):
        clean_text = clean_text[:-3]
    clean_text = clean_text.strip()
    
    # Derive a retrieval confidence score from the average similarity
    # of all matched historical incidents. Higher similarity implies
    # stronger evidence supporting the generated diagnosis.
    calculated_confidence = 0.0
    num_of_errors = 0

    for error in similar_errors:
        confidence = error.get("similarity_score")

        if confidence is not None:
            calculated_confidence += confidence
            num_of_errors += 1

    if num_of_errors > 0:
        calculated_confidence /= num_of_errors
    else:
        # Lower score because no historical error are found and llm has to derive on own
        calculated_confidence = 0.50
        
    try:
        parsed_json = json.loads(clean_text)
        
        formatted_json = { 
            "root_cause": parsed_json.get("root_cause"),
            "suggested_fix": parsed_json.get("suggested_fix"),
            "confidence": calculated_confidence
        } 
        return formatted_json
    
    except json.JSONDecodeError as e:
        return {
            "root_cause": "LLM failed to return valid JSON", 
            "suggested_fix": "Manual review required", 
            "confidence": 0.0
        }
        
        
def get_all_errors(
        resolved: Optional[bool] = None) -> list[dict]:
    """
    Retrieve stored errors from the database.
    Optionally filter by resolution status and always return results
    ordered from newest to oldest.
    
    Args:
       resolved (Optional[bool]): If provided, only return errors matching the specified resolution status.
        
    Returns:
        list[dict]: Error records matching the requested filter, ordered by creation date descending.
    """
    # Build the base query dynamically so that resolution filtering
    # can be applied only when explicitly requested by the caller.
    with engine.connect() as connection:
        sql_text = """
            SELECT
                id,
                message,
                sanitized_trace,
                service_name,
                resolved,
                created_at
            FROM errors
        """
        # Apply resolution-status filtering when a value is provided.
        # A value of None indicates that all records should be returned.
        params = {}
        if resolved is not None:
            sql_text += " WHERE resolved = :resolved "
            params['resolved'] = resolved

        sql_text += "ORDER BY created_at DESC;"
        query = text(sql_text)
        
        result = connection.execute(query, params)
        result = result.fetchall()
        # Convert SQLAlchemy Row objects into plain dictionaries to
        # provide a consistent API response format.
        errors = []
        for row in result:
            errors.append(
                {
                    "id": row.id,
                    "message": row.message,
                    "sanitized_trace": row.sanitized_trace,
                    "service_name":row.service_name,
                    "resolved":row.resolved,
                    "created_at":row.created_at,
                }
            )
        return errors
                