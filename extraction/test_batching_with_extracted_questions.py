import os
import json

SUBJECT='Biology'
DOCUMENT_NAME = "Edexcel_Science_GCSE_Biology_2019.pdf"
YEAR=2019

def generate_batches_with_continuity(pages_dict, main_batch_size=10, max_context_pages=2):
    page_nums = sorted(pages_dict.keys())
    batches = []
    total_pages = len(page_nums)

    for start_idx in range(0, total_pages, main_batch_size):
        main_pages = page_nums[start_idx:start_idx + main_batch_size]

        # Include up to 2 continuity pages before start
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
    with open(path, "r", encoding="utf-8") as f:
        pages = {}
        current_page = None
        lines = []

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


def print_batch_preview(batches, pages_dict, num_batches=2):
    for batch in batches[:num_batches]:
        print(f"\n--- BATCH {batch['batch_index']} ---")
        print(f"Pages: {batch['pages']}")
        print(f"Main Pages: {batch['main_pages']}")

        combined_text = []
        for page in batch["pages"]:
            page_lines = pages_dict.get(page, [])
            combined_text.append(f"\n[Page {page}]\n" + "\n".join(page_lines))

        print("\n".join(combined_text))

#### Use for testing one batch #####

from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()  # uses OPENAI_API_KEY from env by default

def build_prompt(subject, document_name, year, batch_text):
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
- If a main question (e.g. "1(b)") contains subparts like (i), (ii), etc., and has shared context, ensure the **shared context is prepended** to the `question_text` of each subpart.
- Always reconstruct the full question in natural English even if it is split across lines or pages.
- Ignore non-question content like headers, footers, and mark schemes such as "(3)" or "(Total for Question...)".

Below is the extracted text from multiple pages of the exam.  
Your task is to extract **every question from every page**, including all subparts like (i), (ii), (iii), and later numbered questions like 2(a), 2(b), 3(c), etc.

Even if a question appears to end (e.g., "1(c)"), continue parsing the following pages.  
Do not stop early — ensure all questions across all pages are reconstructed.

Text starts below:

{batch_text}
"""}
    ]

def call_openai_api(messages, model="gpt-4-turbo"):
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.2,
        max_tokens=4096,
    )
    return response.choices[0].message.content

def stitch_batch_text(batch, pages_dict):
    texts = []
    for p in batch["pages"]:
        content = "\n".join(pages_dict[p])
        texts.append(f"[Page {p}]\n{content}")
    return "\n\n".join(texts)


# --- Run the test ---
if __name__ == "__main__":
    extracted_file = f"output/{SUBJECT}/{DOCUMENT_NAME.replace('.pdf', '')}/pages.txt"  # path to your previously written text file

    if not os.path.exists(extracted_file):
        raise FileNotFoundError("Please generate 'pages.txt' first.")

    pages_dict = load_extracted_pages(extracted_file)
    batches = generate_batches_with_continuity(pages_dict, main_batch_size=10, max_context_pages=2)

    #print_batch_preview(batches, pages_dict, num_batches=2)


    # Assume pages_dict and batches are already loaded
    # E.g. pages_dict = load_extracted_pages('output/pages.txt')
    #       batches = generate_batches_with_continuity(pages_dict)

    # --- Run on Batch 0 ---
    batch = batches[0]  # from previous step
    batch_text = stitch_batch_text(batch, pages_dict)
    messages = build_prompt(SUBJECT, DOCUMENT_NAME, YEAR, batch_text)

    print("Calling OpenAI API...\n")
    response = call_openai_api(messages)

    print("OpenAI response:")
    print(response)
