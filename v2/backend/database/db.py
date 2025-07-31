import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Configure logging for database operations
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Environment variables for database connection
DB_HOST = os.getenv("DB_HOST")
DB_DATABASE = os.getenv("DB_DATABASE")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT")

def create_database_if_not_exists(verbose=False):
    """
    Create the database if it does not exist.

    Connects to the PostgreSQL server and creates the database specified in DB_DATABASE
    if it doesn't already exist. Uses psycopg2 for direct database creation.

    Args:
        verbose (bool): If True, print informational messages about database creation.

    Raises:
        Exception: If connection or creation fails, logs the error and raises it.

    Example:
        create_database_if_not_exists(verbose=True)

    Notes:
        - Should be called during application setup, not on every import.
        - Uses ISOLATION_LEVEL_AUTOCOMMIT for database creation.
        - In production, ensure DB_USER has sufficient permissions.
        - Log errors for debugging and auditing.
    """
    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()

        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_DATABASE,))
        exists = cur.fetchone()

        if not exists:
            cur.execute(f'CREATE DATABASE "{DB_DATABASE}"')
            logger.info(f"Database '{DB_DATABASE}' created")
            if verbose:
                print(f"[INFO] Database '{DB_DATABASE}' created.")
        else:
            logger.info(f"Database '{DB_DATABASE}' already exists")
            if verbose:
                print(f"[INFO] Database '{DB_DATABASE}' already exists.")

        cur.close()
        conn.close()

    except Exception as e:
        logger.error(f"Failed to create/check database '{DB_DATABASE}': {str(e)}")
        if verbose:
            print(f"[ERROR] Failed to create/check database: {e}")
        raise

# SQLAlchemy setup
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}"
engine = create_engine(DATABASE_URL, echo=False)  # Set echo=True for debugging only

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# Professional session getter for use in services/handlers
def get_db_session():
    """
    Returns a new SQLAlchemy session. Use with context management or close manually.
    Example:
        with get_db_session() as session:
            ...
    """
    return SessionLocal()

# Note: Call create_database_if_not_exists() in a setup script, not here, to avoid
# running on every import. Example: python scripts/setup_db.py