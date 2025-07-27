import fitz

def normalize_font(font_name):
    return font_name.lower().replace("-", "").replace("mt", "")

def merge_nearby_blocks(blocks, h_threshold=10, v_threshold=5):
    """Merge text blocks that are close together horizontally"""
    if not blocks:
        return blocks
    
    # Sort blocks by page, then by top, then by left
    sorted_blocks = sorted(blocks, key=lambda b: (b['page'], b['top'], b.get('left', 0)))
    
    merged = []
    current = None
    
    for block in sorted_blocks:
        if current is None:
            current = block.copy()
        elif (block['page'] == current['page'] and 
              abs(block['top'] - current['top']) < v_threshold and
              block.get('left', 0) - current.get('right', current.get('left', 0)) < h_threshold):
            # Merge blocks on same line
            current['text'] = current['text'].rstrip() + ' ' + block['text'].lstrip()
            current['right'] = block.get('right', block.get('left', 0))
            # Keep the larger font size
            current['size'] = max(current['size'], block['size'])
        else:
            merged.append(current)
            current = block.copy()
    
    if current:
        merged.append(current)
    
    return merged

def extract_pdf_features(pdf_path):
    doc = fitz.open(pdf_path)
    all_spans = []
    
    for page_num, page in enumerate(doc):
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            for line in block.get("lines", []):
                for span in line["spans"]:
                    text = span["text"].strip()
                    if not text:
                        continue
                    all_spans.append({
                        "text": text,
                        "font": normalize_font(span["font"]),
                        "size": span["size"],
                        "top": span["bbox"][1],
                        "left": span["bbox"][0],
                        "right": span["bbox"][2],
                        "page": page_num
                    })
    
    # Merge nearby blocks
    merged_spans = merge_nearby_blocks(all_spans)
    
    # Clean up - remove left/right as they're not used elsewhere
    for span in merged_spans:
        span.pop('left', None)
        span.pop('right', None)
    
    return merged_spans