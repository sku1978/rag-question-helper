from fastapi import FastAPI, Query
from api.search import search_questions

# Define app **before** using it
app = FastAPI()

@app.get("/search")
def search(query: str, limit: int = 5):
    return {
        "query": query,
        "results": search_questions(query, limit)
    }
