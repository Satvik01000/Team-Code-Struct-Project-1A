import sys
import json
from app.extract_features import extract_pdf_features
from app.predict import predict_headings

def extract_title(text_blocks):
    first_page_blocks = [b for b in text_blocks if b["page"] == 1]
    first_page_blocks.sort(key=lambda b: -b["size"])
    for block in first_page_blocks:
        if len(block["text"].strip()) > 10:
            return block["text"].strip()
    return ""

def main(pdf_path):
    text_blocks = extract_pdf_features(pdf_path)
    outline = predict_headings(text_blocks)
    title = extract_title(text_blocks)
    result = {
        "title": title,
        "outline": outline
    }

    print(json.dumps(result, indent=4, ensure_ascii=False))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py path/to/file.pdf")
        sys.exit(1)

    pdf_path = sys.argv[1]
    main(pdf_path)
