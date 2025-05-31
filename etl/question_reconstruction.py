# etl/question_reconstruction.py

import os
import json
import time
import glob
import argparse
from typing import List, Dict, Any
from dotenv import load_dotenv
from ai.openai_client import get_openai_client

load_dotenv()
client = get_openai_client()

# -------------------------------
# Core batch processing logic
# -------------------------------

def build_prompt(subject, document_name, year, batch_text, last_question_id=None, main_pages=None):
    continuation_note = ""
    if last_question_id:
        page_list = ", ".join(str(p) for p in main_pages or [])
        continuation_note = f"""
Note:
- The first few pages are *context pages* provided from the previous batch to help preserve continuity.
- **Do not extract or repeat any questions from these context pages.**
- Only extract questions from the new pages: {page_list}
- You must continue from the last known question, which was "{last_question_id}".
- Do not reset question numbering.
"""

    return [
        {"role": "system", "content": "You are a helpful assistant that reads GCSE exam papers and extracts structured question metadata for a RAG system."},
        {"role": "user", "content": f"""
You will be given OCR-style extracted text from a GCSE {subject} exam paper.

Your task is to extract and reconstruct each exam question into a structured JSON format with the following fields:
- `question_id`: e.g., "1(a)", "1(b)(ii)"
- `question_text`: complete question wording
- `page`: page number the question appears on
- `context_keywords`: 3–7 subject-specific terms for semantic retrieval
- `document_name`: "{document_name}"
- `subject`: "{subject}"
- `year`: {year}

Important instructions:
- If a question has subparts like (i), (ii), etc., and shares a setup or context, ensure that context is **prepended** to each subpart’s `question_text`.
- Treat each subpart as standalone. Include the shared context **every time**, not just once.
- Continue parsing all questions across all pages, even after "Question 1" or "Question 4".
{continuation_note}

Text starts below:

{batch_text}
"""}
    ]

def generate_batches_with_continuity(pages_dict, main_batch_size=5, max_context_pages=2):
    page_nums = sorted(pages_dict.keys())
    batches = []

    for start_idx in range(0, len(page_nums), main_batch_size):
        main_pages = page_nums[start_idx:start_idx + main_batch_size]
        context_start = max(0, start_idx - max_context_pages)
        continuity_pages = page_nums[context_start:start_idx]
        batch_pages = continuity_pages + main_pages

        batches.append({
            "batch_index": len(batches),
            "pages": batch_pages,
            "main_pages": main_pages
        })

    return batches

def load_extracted_pages(path):
    pages = {}
    current_page = None
    lines = []

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip()
            if line.startswith("--- PAGE"):
                if current_page and lines:
                    pages[current_page] = lines
                current_page = int(line.split()[-2])
                lines = []
            elif current_page is not None:
                lines.append(line)
        if current_page and lines:
            pages[current_page] = lines

    return pages

def stitch_batch_text(batch, pages_dict):
    texts = []
    for p in batch["pages"]:
        content = "\n".join(pages_dict[p])
        texts.append(f"[Page {p}]\n{content}")
    return "\n\n".join(texts)

def call_openai(messages, retries=3, delay=30):
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4-turbo",
                messages=messages,
                temperature=0.2,
                max_tokens=4096,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Retry {attempt + 1} failed: {e}")
            time.sleep(delay)
    raise RuntimeError("OpenAI API call failed after retries.")

def safe_parse_json(text: str) -> List[Dict[str, Any]]:
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return data
        raise ValueError("Parsed JSON is not a list")
    except Exception:
        start = text.find("[")
        end = text.rfind("]") + 1
        try:
            data = json.loads(text[start:end])
            if isinstance(data, list):
                return data
        except Exception:
            raise ValueError("Response could not be parsed as a list of questions")

def run_batch_with_retries(messages, batch_index, retries=3, delay=30):
    for attempt in range(retries):
        try:
            print(f"🚀 Batch {batch_index}: Attempt {attempt + 1}")
            response_text = call_openai(messages)
            parsed_questions = safe_parse_json(response_text)
            last_qid = parsed_questions[-1]["question_id"]
            return parsed_questions, last_qid
        except Exception as e:
            print(f"⚠️ Attempt {attempt + 1} failed for batch {batch_index}: {e}")
            if attempt < retries - 1:
                time.sleep(delay)

    print(f"❌ Batch {batch_index} failed after retries.")
    return None, None

def deduplicate_batches(output_dir: str) -> List[Dict]:
    batch_files = sorted(glob.glob(os.path.join(output_dir, "questions_batch_*.json")))
    questions = []

    for file in batch_files:
        with open(file, "r", encoding="utf-8") as f:
            questions.extend(json.load(f))

    seen = set()
    unique = []
    for q in questions:
        key = (q["question_id"], q["page"])
        if key not in seen:
            seen.add(key)
            unique.append(q)

    final_path = os.path.join(output_dir, "all_questions_deduped.json")
    with open(final_path, "w", encoding="utf-8") as f:
        json.dump(unique, f, indent=2)

    print(f"✅ Deduplicated file saved: {final_path}")
    return unique

# ------------------------------------------------
# Public entry point to be called from pipeline
# ------------------------------------------------

def reconstruct_questions(subject, document_name, year):
    extracted_path = f"output/{subject}/{document_name.replace('.pdf','')}/pages.txt"
    output_dir = f"output/{subject}/{document_name.replace('.pdf','')}"
    os.makedirs(output_dir, exist_ok=True)

    pages_dict = load_extracted_pages(extracted_path)
    batches = generate_batches_with_continuity(pages_dict)

    all_questions = []
    last_qid = None
    failed_batches = []

    for batch in batches:
        print(f"Processing batch {batch['batch_index']} (pages {batch['pages']})")
        batch_text = stitch_batch_text(batch, pages_dict)
        messages = build_prompt(subject, document_name, year, batch_text, last_question_id=last_qid, main_pages=batch["main_pages"])

        parsed_questions, last_qid = run_batch_with_retries(messages, batch["batch_index"])

        if not parsed_questions:
            failed_batches.append(batch["batch_index"])
            continue

        batch_file = os.path.join(output_dir, f"questions_batch_{batch['batch_index']}.json")
        with open(batch_file, "w", encoding="utf-8") as f:
            json.dump(parsed_questions, f, indent=2)

        all_questions.extend(parsed_questions)
        print(f"✅ Saved {len(parsed_questions)} questions from batch {batch['batch_index']}")

    # Deduplicate at end
    unique = deduplicate_batches(output_dir)
    print(f"\n🎉 Completed. Total unique questions: {len(unique)}")
    return failed_batches

# ------------------------------------------------
# CLI Entry Point
# ------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Question Reconstruction Pipeline")
    parser.add_argument("--subject", required=True, help="Subject name")
    parser.add_argument("--document", required=True, help="PDF document filename (e.g. Edexcel_....pdf)")
    parser.add_argument("--year", type=int, required=True, help="Exam year")

    args = parser.parse_args()

    reconstruct_questions(args.subject, args.document, args.year)
