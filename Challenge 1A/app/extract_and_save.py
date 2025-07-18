import json
import csv
from extract_features import extract_pdf_features

pdf_path = "../pdfs/E0CCG5S312.pdf"

blocks = extract_pdf_features(pdf_path)

print(f"Extracted {len(blocks)} text blocks.")

with open("sample/label_data.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["text", "font", "size", "top", "page", "label"])
    for block in blocks:
        writer.writerow([
            block["text"],
            block["font"],
            block["size"],
            block["top"],
            block["page"],
            ""
        ])
print("Saved to extracted_blocks.csv")
