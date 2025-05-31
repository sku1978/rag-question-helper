# Use this for only for incremental loading of deduplicated questions into the database.
# etl/ingest_questions.py
import os
import json
from etl.etl_utils import insert_questions
from db.db_connection import get_db_connection

ROOT_OUTPUT_DIR = "output"

def find_deduped_files():
    deduped_files = []
    for root, dirs, files in os.walk(ROOT_OUTPUT_DIR):
        for file in files:
            if file == "all_questions_deduped.json":
                full_path = os.path.join(root, file)
                deduped_files.append(full_path)
    return deduped_files

def is_already_loaded(conn, source_file):
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM questions WHERE source_file = %s LIMIT 1", (source_file,))
    exists = cur.fetchone() is not None
    cur.close()
    return exists

def main():
    conn = get_db_connection()

    all_files = find_deduped_files()
    print(f"🔎 Found {len(all_files)} deduplicated files to check...")

    for file_path in all_files:
        print(f"\n📂 Processing: {file_path}")

        if is_already_loaded(conn, file_path):
            print("✅ Already loaded — skipping.")
            continue

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                questions = json.load(f)
        except Exception as e:
            print(f"❌ Failed to read {file_path}: {e}")
            continue

        insert_questions(questions, file_path)

    conn.close()

if __name__ == "__main__":
    main()
