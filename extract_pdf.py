from pdfminer.high_level import extract_text
import re
import json
import os

def extract_lines(pdf_path):
    raw_text = extract_text(pdf_path)
    lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
    return lines

def parse_questions(lines, pdf_name):
    results = []
    current_qid = None
    current_parent = None
    current_text = ""

    def flush():
        nonlocal current_qid, current_text
        if current_qid and current_text.strip():
            results.append({
                "question_id": current_qid,
                "parent_id": current_parent if current_qid != current_parent else None,
                "text": current_text.strip(),
                "source": pdf_name
            })
        current_qid = None
        current_text = ""

    for line in lines:
        # Filter out noisy page footer/header lines
        if any(skip in line for skip in [
            "DO NOT WRITE", "Turn over", "*P6", "PMT", "Edexcel", "Centre Number", "Candidate Number"
        ]) or re.match(r'^\.+$', line):
            continue

        # Match question number with letter: 1(a), 2(b)
        m_main = re.match(r"^(\d+)\s*\(([a-z])\)\s*(.*)", line)
        if m_main:
            flush()
            qnum = m_main.group(1)
            part = m_main.group(2)
            rest = m_main.group(3)
            current_qid = f"{qnum}({part})"
            current_parent = qnum
            current_text = rest
            continue

        # Match subparts like (i), (ii)
        m_sub = re.match(r"^\(([ivx]+)\)\s*(.*)", line)
        if m_sub:
            flush()
            roman = m_sub.group(1)
            rest = m_sub.group(2)
            current_qid = f"{current_parent}({roman})"
            current_text = rest
            continue

        # Match full question with number only: 2 Explain...
        m_root = re.match(r"^(\d+)\s+(.*)", line)
        if m_root and not re.match(r"^\d{4}", m_root.group(1)):  # Avoid 2019, etc.
            flush()
            current_qid = m_root.group(1)
            current_parent = current_qid
            current_text = m_root.group(2)
            continue

        # Include diagrammatic instructions with the previous question
        if re.match(r"^Figure\s+\d+", line) or re.match(r"^(crush|filter|add ethanol)", line.lower()):
            current_text += "\n" + line
            continue

        # Append other lines to current question text
        current_text += " " + line

    flush()
    return results


if __name__ == "__main__":
    pdf_path = "sample_papers/Edexcel_Science GCSE_Biology_2019.pdf"
    pdf_name = os.path.basename(pdf_path)

    lines = extract_lines(pdf_path)
    parsed = parse_questions(lines, pdf_name)

    # Preview the first few
    for q in parsed[:10]:
        print(json.dumps(q, indent=2))

    # Save to file
    with open("parsed_questions_pdfminer.json", "w", encoding="utf-8") as f:
        json.dump(parsed, f, indent=2)
