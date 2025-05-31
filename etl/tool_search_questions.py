import os
import psycopg2
import psycopg2.extras
from ai.openai_client import get_openai_client
from dotenv import load_dotenv
import argparse

load_dotenv()
client = get_openai_client()

# ---- Argument parser ----
parser = argparse.ArgumentParser(description="Search GCSE questions via vector similarity")
parser.add_argument("--top", type=int, default=5, help="Number of top results to return (default: 5)")
args = parser.parse_args()

# ---- Database connection ----
from db.db_connection import get_db_connection
conn = get_db_connection()
cur = conn.cursor()

# ---- User input query ----
query = input("🔍 Enter a topic or question to search: ").strip()

# ---- Generate embedding ----
print("🔗 Generating embedding...")
embedding = client.embeddings.create(
    input=query,
    model="text-embedding-ada-002"
).data[0].embedding

# ---- Search with vector similarity ----
print("🔎 Searching database...\n")
cur.execute("""
    SELECT
        question_id,
        question_text,
        page,
        document_name,
        subject,
        year,
        source_file,
        1 - (embedding <=> %s) AS similarity  -- ✅ Now higher is better
    FROM questions
    ORDER BY embedding <=> %s
    LIMIT %s
""", (
    psycopg2.extras.Json(embedding),
    psycopg2.extras.Json(embedding),
    args.top
))

results = cur.fetchall()

# ---- Display results ----
for idx, row in enumerate(results, 1):
    print(f"#{idx}:")
    print(f"  ID         : {row[0]}")
    print(f"  Text       : {row[1][:200]}{'...' if len(row[1]) > 200 else ''}")
    print(f"  Page       : {row[2]}")
    print(f"  Document   : {row[3]}")
    print(f"  Subject    : {row[4]}")
    print(f"  Year       : {row[5]}")
    print(f"  Source     : {row[6]}")
    print(f"  Similarity : {row[7]:.4f}")
    print("")

cur.close()
conn.close()
