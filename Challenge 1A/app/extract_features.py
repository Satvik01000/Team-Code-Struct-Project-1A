import fitz

def extract_pdf_features(pdf_path):
    doc = fitz.open(pdf_path)
    all_spans = []

    for page_num, page in enumerate(doc):
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            for line in block.get("lines", []):
                text = " ".join(span["text"].strip() for span in line["spans"])
                if not text:
                    continue
                span = line["spans"][0]
                all_spans.append({
                    "text": text,
                    "font": span["font"],
                    "size": span["size"],
                    "top": span["bbox"][1],
                    "page": page_num + 1
                })
    return all_spans
