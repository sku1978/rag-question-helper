import time
from db.db_connection import get_db_connection
from ai.openai_client import get_openai_client

def generate_embedding(text, retries=3, delay=10):
    client = get_openai_client()

    for attempt in range(1, retries + 1):
        try:
            response = client.embeddings.create(
                input=text,
                model="text-embedding-ada-002"
            )
            return response.data[0].embedding

        except Exception as e:
            print(f"⚠️ Embedding attempt {attempt} failed: {e}")
            if attempt < retries:
                time.sleep(delay)
            else:
                print("❌ All embedding retries failed.")
                raise


def insert_questions(questions, source_file):
    conn = get_db_connection()
    cur = conn.cursor()

    # Delete existing records for this file
    cur.execute("DELETE FROM questions WHERE source_file = %s", (source_file,))
    print(f"🧹 Existing records deleted for {source_file}")

    for q in questions:
        combined_text = q["question_text"] + " " + " ".join(q["context_keywords"])
        embedding = generate_embedding(combined_text)

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
            source_file,
            embedding
        ))

        print(f"✅ Inserted: {q['question_id']}")

    conn.commit()
    cur.close()
    conn.close()
