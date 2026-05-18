from services.embedding_service import embed_error
from sqlalchemy import text, create_engine
from dotenv import load_dotenv
import os

# Load environment variables from `.env` into the process environment.
load_dotenv()

def run_integration_test():
    """
    End-to-end integration test for the embedding pipeline

    Test flow:
    1. Insert a temporary row into database
    2. Generate embedding using ollama
    3. Store the embedded vector as string into Neon Postgres
    4. Verify embedding column is populated
    5. Clean up after test

    This validates real-time interaction between:
    - python applications
    - ollama embedding vector
    - SQLAlchemy 
    - Neon Postgres Database
    """

    # Creates SQLAlchemy engine using DATABASE_URL environment variables.
    # Manages the database connectivity and transaction
    engine = create_engine(os.getenv('DATABASE_URL'))

    # Inserts dummy data into database.
    # Opens a transaction commits on success and rolls back on failure.
    with engine.begin() as connection:
        insert_query = text("""
            INSERT INTO errors (message, stack_trace, sanitized_trace, service_name)
            VALUES ('Text error message', 'Raw Stack Trace', 'Sanitized Trace', 'test_service')
            RETURNING id;
        """)
        result = connection.execute(insert_query)
        inserted_id = result.fetchone()[0]
    print(f"Dummy row inserted with ID: {inserted_id}")

    
    embed_error(inserted_id, "Sanitized stack trace...")

    print("Verifying vector column is no longer null")

    # Verifies if vector column has values or not
    with engine.connect() as connection:
        verify_query = text("SELECT embedding IS NOT NULL FROM errors WHERE id = :id")
        has_embedding = connection.execute(verify_query, {
            "id": inserted_id
        }).scalar()
    print(f"Verifying result: has_embedding = {has_embedding}")

    print("Cleaning up dummy row")
    # Deletes dummy data to free up space
    with engine.begin() as connection:
        delete_query = text("DELETE FROM errors where id = :id")
        connection.execute(delete_query,{
            "id": inserted_id
        })
    if has_embedding:
        print("\n INTEGRATION TEST SUCCESSFUL! Vector saved to cloud Neon DB.")
    else:
        print("\n INTEGRATION TEST FAILED: Vector column is still null.")
if __name__ == '__main__':
    run_integration_test()