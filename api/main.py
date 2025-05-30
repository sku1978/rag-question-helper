from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from api.search import search_questions

app = FastAPI()

# Static files and templates
app.mount("/pdfs", StaticFiles(directory="sample_papers"), name="pdfs")
templates = Jinja2Templates(directory="templates")

# Optional: allow local front-end dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Renders HTML page ----
@app.get("/search-ui", response_class=HTMLResponse)
async def render_search_page(request: Request):
    return templates.TemplateResponse("search.html", {"request": request})

# ---- JSON API endpoint ----
@app.get("/api/search")
def api_search(query: str, limit: int = 5):
    results = search_questions(query, limit=limit)
    return {"results": results}
