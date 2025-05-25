import fitz  # PyMuPDF
import os
import re

# Define bounding box for content area
SUBJECT='Chemistry'
DOCUMENT_NAME = "Edexcel_Science_GCSE_ChemistryPaper2_2023.pdf"
MIN_X, MAX_X = 20, 540
MIN_Y, MAX_Y = 50, 800


def extract_pdf_by_page(pdf_path):
    doc = fitz.open(pdf_path)
    output = {}

    for page_num, page in enumerate(doc, start=1):
        blocks = page.get_text("dict")["blocks"]
        lines = []

        for block in blocks:
            if block["type"] != 0:
                continue  # Skip non-text blocks

            for line in block["lines"]:
                line_text = []
                for span in line["spans"]:
                    x0, y0, x1, y1 = span["bbox"]
                    if x0 >= MIN_X and x1 <= MAX_X and y0 >= MIN_Y and y1 <= MAX_Y:
                        line_text.append(span["text"].strip())

                if line_text:
                    full_line = " ".join(filter(None, line_text))

                    # ❌ Skip lines that are just marks in brackets (e.g. (3))
                    if re.fullmatch(r"\(\d{1,2}\)", full_line):
                        continue

                    # ❌ Skip lines with total marks summary in brackets
                    if re.search(r"\(.*?\d{1,2}\s*marks.*?\)", full_line, re.IGNORECASE):
                        continue

                    lines.append(full_line)

        output[page_num] = lines

    return output

def extract_detailed_layout(pdf_path):
    doc = fitz.open(pdf_path)
    detailed = []

    for page_num, page in enumerate(doc, start=1):
        blocks = page.get_text("dict")["blocks"]

        for block in blocks:
            if block["type"] != 0:  # skip images etc.
                continue

            for line in block["lines"]:
                for span in line["spans"]:
                    x0, y0, x1, y1 = span["bbox"]

                    # Only include spans that fall within the "main body"
                    if x0 >= MIN_X and x1 <= MAX_X and y0 >= MIN_Y and y1 <= MAX_Y:
                        detailed.append({
                            "page": page_num,
                            "text": span["text"].strip(),
                            "bbox": span["bbox"],
                            "font": span["font"],
                            "size": span["size"],
                            "flags": span["flags"],
                            "block_bbox": block["bbox"],
                        })

    return detailed

def generate_batches_with_continuity(pages_dict, main_batch_size=10, max_context_pages=2):
    page_nums = sorted(pages_dict.keys())
    batches = []
    total_pages = len(page_nums)

    for start_idx in range(0, total_pages, main_batch_size):
        main_pages = page_nums[start_idx:start_idx + main_batch_size]

        # Calculate how many context pages to include (max 2)
        context_start = max(0, start_idx - max_context_pages)
        continuity_pages = page_nums[context_start:start_idx]

        batch_pages = continuity_pages + main_pages

        batches.append({
            "batch_index": len(batches),
            "pages": batch_pages,
            "main_pages": main_pages
        })

    return batches



if __name__ == "__main__":
    pdf_path = f"../sample_papers/{SUBJECT}/{DOCUMENT_NAME}"
    output_dir = f"../output/{SUBJECT}/{DOCUMENT_NAME.replace('.pdf', '')}"
    os.makedirs(output_dir, exist_ok=True)

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"{pdf_path} not found.")

    pages = extract_pdf_by_page(pdf_path)
    pages_output_path = os.path.join(output_dir, "pages.txt")
    with open(pages_output_path, "w", encoding="utf-8") as f:
        for page_num, lines in pages.items():
            f.write(f"\n\n\n--- PAGE {page_num} ---\n")
            for line in lines:
                f.write(line + "\n")

    detailed_layout = extract_detailed_layout(pdf_path)
    detailed_output_path = os.path.join(output_dir, "detailed_layout.txt")
    with open(detailed_output_path, "w", encoding="utf-8") as f:
        for item in detailed_layout:
            f.write(
                f"Page {item['page']}: {item['text']} "
                f"(bbox: {item['bbox']}, font: {item['font']}, size: {item['size']})\n"
            )
