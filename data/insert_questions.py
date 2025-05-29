import os
import json
import psycopg2
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()


# --- Postgres connection ---
conn = psycopg2.connect(
    dbname=os.getenv("POSTGRES_DB"),
    user=os.getenv("PGUSER"),
    password=os.getenv("PGPASSWORD"),  # store in .env
    host=os.getenv("PGHOST", "localhost"),
    port=5432,
)
cur = conn.cursor()

# --- Load list of input files ---
with open("data/question_file_list.txt", "r", encoding="utf-8") as list_file:
    file_paths = [
        line.strip()
        for line in list_file
        if line.strip() and not line.strip().startswith("#")
    ]

for input_file in file_paths:
    print(f"\n📄 Processing: {input_file}")

    # --- Remove existing rows from this source file ---
    cur.execute("DELETE FROM questions WHERE source_file = %s", (input_file,))
    print("🧹 Existing records deleted.")

    # --- Load questions from the JSON file ---
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            questions = json.load(f)
    except Exception as e:
        print(f"❌ Failed to read {input_file}: {e}")
        continue

    for q in questions:
        # Combine text + keywords
        combined_text = q["question_text"] + " " + " ".join(q["context_keywords"])

        # Generate embedding
        try:
            response = client.embeddings.create(
                input=combined_text,
                model="text-embedding-ada-002"
            )
            embedding = response.data[0].embedding
        except Exception as e:
            print(f"⚠️ Skipping question {q.get('question_id')} due to embedding error: {e}")
            continue

        # Insert with source_file
        cur.execute("""
            INSERT INTO questions (
                question_id, question_text, context_keywords, page,
                document_name, subject, year, source_file, embedding, load_time
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
        """, (
            q["question_id"],
            q["question_text"],
            q["context_keywords"],
            q["page"],
            q["document_name"],
            q["subject"],
            q["year"],
            input_file,  # ✅ Source file tracking
            embedding
        ))

        print(f"✅ Inserted: {q['question_id']}")

conn.commit()
cur.close()
conn.close()
print("\n🎉 All files processed.")