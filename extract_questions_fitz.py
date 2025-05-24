import fitz  # PyMuPDF
import os

def extract_pdf_by_page(pdf_path):
    doc = fitz.open(pdf_path)
    output = {}

    for i, page in enumerate(doc):
        page_text = page.get_text()
        output[i + 1] = page_text.strip().split("\n")

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

if __name__ == "__main__":
    pdf_path = "sample_papers/Edexcel_Science GCSE_Biology_2019.pdf"

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"{pdf_path} not found.")

    pages = extract_pdf_by_page(pdf_path)

    for page_num, lines in pages.items():
        print(f"\n\n\n--- PAGE {page_num} ---")
        for line in lines:
            print(line)

    detailed_layout = extract_detailed_layout(pdf_path)
    for item in detailed_layout:
        print(f"Page {item['page']}: {item['text']} (bbox: {item['bbox']}, font: {item['font']}, size: {item['size']})")
