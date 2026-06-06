import os

from dotenv import load_dotenv
from sqlalchemy import create_engine

# Load environment variables from the .env file into the
# current process so configuration can be accessed via os.getenv().
load_dotenv()

# Retrieve the database connection string from the environment.
# The application cannot start without a valid database URL.
database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise EnvironmentError(
        "Database URL not set, check the .env file"
    )

# Create a shared SQLAlchemy Engine instance.
engine = create_engine(database_url)