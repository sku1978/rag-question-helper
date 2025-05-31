import fitz
import os
import re

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

def extract_pdf_to_pages(subject, document_name):
    base_dir = f"sample_papers/{subject}"
    output_dir = f"output/{subject}/{document_name.replace('.pdf', '')}"
    os.makedirs(output_dir, exist_ok=True)

    pdf_path = os.path.join(base_dir, document_name)
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"{pdf_path} not found")

    print(f"📄 Extracting: {document_name}")
    pages = extract_pdf_by_page(pdf_path)

    output_file = os.path.join(output_dir, "pages.txt")
    with open(output_file, "w", encoding="utf-8") as f:
        for page_num, lines in pages.items():
            f.write(f"\n\n\n--- PAGE {page_num} ---\n")
            for line in lines:
                f.write(line + "\n")

    print(f"✅ Extracted pages written to {output_file}")
    return output_file
