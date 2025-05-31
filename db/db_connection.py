import os
import psycopg2

def get_db_connection():
    conn = psycopg2.connect(
        dbname=os.getenv("POSTGRES_DB", "question_vector_db"),
        user=os.getenv("PGUSER", "kumar_s"),
        password=os.getenv("PGPASSWORD", "postgres"),
        host=os.getenv("PGHOST", "localhost"),
        port=int(os.getenv("PGPORT", 5432))
    )
    return conn
