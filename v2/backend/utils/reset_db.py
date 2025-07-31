# reset_db.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import engine, Base

if __name__ == "__main__":
    # Drop all tables
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("All tables dropped.")

    # Recreate all tables
    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)
    print("All tables created.")