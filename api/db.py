# api/db.py
import os
import psycopg2
from psycopg2.extras import register_default_jsonb

register_default_jsonb(globally=True, loads=lambda x: x)

def get_connection():
    return psycopg2.connect(
        dbname=os.getenv("POSTGRES_DB", "question_vector_db"),
        user=os.getenv("PGUSER"),
        password=os.getenv("PGPASSWORD"),
        host=os.getenv("PGHOST", "shared-postgres"),
        port=5432,
    )
