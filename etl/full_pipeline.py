# etl/full_pipeline.py

import os
import argparse

from etl.pdf_extraction import extract_pdf_to_pages
from etl.question_reconstruction import reconstruct_questions
from etl.etl_utils import insert_questions

def run_full_pipeline(subject, document_name, year):

    # STEP 1: Extract PDF to pages.txt
    extract_pdf_to_pages(subject, document_name)

    # STEP 2: Run reconstruction (LLM extraction)
    reconstruct_questions(subject, document_name, year)

    # STEP 3: Insert into database from deduped output
    output_dir = f"output/{subject}/{document_name.replace('.pdf', '')}"
    deduped_file = os.path.join(output_dir, "all_questions_deduped.json")

    if not os.path.exists(deduped_file):
        raise FileNotFoundError(f"❌ Deduped file missing: {deduped_file}")

    import json
    with open(deduped_file, "r", encoding="utf-8") as f:
        questions = json.load(f)

    # Use full file path as source_file to allow incremental loading
    insert_questions(questions, source_file=deduped_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Full ETL Pipeline")
    parser.add_argument("--subject", required=True, help="Subject name")
    parser.add_argument("--document", required=True, help="PDF document filename (e.g. Edexcel_....pdf)")
    parser.add_argument("--year", type=int, required=True, help="Exam year")

    args = parser.parse_args()
    run_full_pipeline(args.subject, args.document, args.year)
