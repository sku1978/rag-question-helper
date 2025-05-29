# api/test_search.py
from api.search import search_questions

if __name__ == "__main__":
    query = input("🔍 Enter a topic or question to search: ")
    results = search_questions(query, limit=5)

    print(f"\n✅ Top {len(results)} matches for: \"{query}\"\n")
    for i, row in enumerate(results, 1):
        print(f"{i}. {row['question_id']} | Page {row['page']} | {row['question_text'][:100]}...")
