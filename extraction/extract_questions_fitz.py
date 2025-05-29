import fitz  # PyMuPDF
import os
import re

SUBJECT = 'Physics'
BASE_DIR = f"sample_papers/{SUBJECT}"
OUTPUT_ROOT = f"output/{SUBJECT}"

# Bounding box for main content
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
                continue

            for line in block["lines"]:
                line_text = []
                for span in line["spans"]:
                    x0, y0, x1, y1 = span["bbox"]
                    if x0 >= MIN_X and x1 <= MAX_X and y0 >= MIN_Y and y1 <= MAX_Y:
                        line_text.append(span["text"].strip())

                if line_text:
                    full_line = " ".join(filter(None, line_text))

                    if re.fullmatch(r"\(\d{1,2}\)", full_line):
                        continue
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
            if block["type"] != 0:
                continue

            for line in block["lines"]:
                for span in line["spans"]:
                    x0, y0, x1, y1 = span["bbox"]
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


def process_pdf(document_name):
    pdf_path = os.path.join(BASE_DIR, document_name)
    output_dir = os.path.join(OUTPUT_ROOT, document_name.replace('.pdf', ''))
    os.makedirs(output_dir, exist_ok=True)

    print(f"📄 Processing: {document_name}")

    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        return

    pages = extract_pdf_by_page(pdf_path)
    with open(os.path.join(output_dir, "pages.txt"), "w", encoding="utf-8") as f:
        for page_num, lines in pages.items():
            f.write(f"\n\n\n--- PAGE {page_num} ---\n")
            for line in lines:
                f.write(line + "\n")

    detailed_layout = extract_detailed_layout(pdf_path)
    with open(os.path.join(output_dir, "detailed_layout.txt"), "w", encoding="utf-8") as f:
        for item in detailed_layout:
            f.write(
                f"Page {item['page']}: {item['text']} "
                f"(bbox: {item['bbox']}, font: {item['font']}, size: {item['size']})\n"
            )

    print(f"✅ Done: {document_name}")


if __name__ == "__main__":
    for file in os.listdir(BASE_DIR):
        if file.lower().endswith(".pdf"):
            process_pdf(file)