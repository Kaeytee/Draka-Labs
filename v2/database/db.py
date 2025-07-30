# db.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os

# Load environment variables
load_dotenv()

# Environment variables
DB_HOST = os.getenv("DB_HOST")
DB_DATABASE = os.getenv("DB_DATABASE")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT")

def create_database_if_not_exists(verbose=False):
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
			if verbose:
				print(f"[INFO] Database '{DB_DATABASE}' created.")
		else:
			if verbose:
				print(f"[INFO] Database '{DB_DATABASE}' already exists.")

		cur.close()
		conn.close()
	except Exception as e:
		print(f"[ERROR] Failed to create/check database: {e}")

# Optional: Call this manually in your setup script, not always on startup
# create_database_if_not_exists(verbose=True)

# SQLAlchemy engine
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}"
engine = create_engine(DATABASE_URL, echo=False)  # Set echo=True only during debugging

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()
