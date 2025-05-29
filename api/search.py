# api/search.py

import os
import psycopg2
import psycopg2.extras
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()

def search_questions(query: str, limit: int = 5):
    # Generate embedding using OpenAI
    embedding = client.embeddings.create(
        input=query,
        model="text-embedding-ada-002"
    ).data[0].embedding

    # Connect to Postgres
    conn = psycopg2.connect(
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("PGUSER"),
        password=os.getenv("PGPASSWORD"),
        host=os.getenv("PGHOST", "localhost"),
        port=5432,
    )
    cur = conn.cursor()

    cur.execute("""
        SELECT
            question_id,
            question_text,
            page,
            document_name,
            subject,
            year,
            source_file,
            1 - (embedding <=> %s) AS similarity
        FROM questions
        ORDER BY embedding <=> %s
        LIMIT %s
    """, (
        psycopg2.extras.Json(embedding),
        psycopg2.extras.Json(embedding),
        limit
    ))

    results = cur.fetchall()
    cur.close()
    conn.close()

    # Format output for API
    return [
        {
            "question_id": row[0],
            "question_text": row[1],
            "page": row[2],
            "document_name": row[3],
            "subject": row[4],
            "year": row[5],
            "source_file": row[6],
            "similarity": round(row[7], 4)
        }
        for row in results
    ]
