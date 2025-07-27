import sys
import os
import json
from app.extract_features import extract_pdf_features
from app.predict import predict_headings

def extract_title(text_blocks):
    """
    Extract title with better handling for multi-line, multi-block titles
    """
    # Look at first few pages for title
    early_blocks = [b for b in text_blocks if b["page"] <= 2]
    
    if not early_blocks:
        return ""
    
    # Special handling for RFP-style documents
    # Look for "RFP:" or "Request for Proposal" patterns
    rfp_blocks = []
    for block in early_blocks:
        if any(pattern in block["text"] for pattern in ["RFP:", "Request for Proposal", "REQUEST FOR PROPOSAL"]):
            rfp_blocks.append(block)
    
    # If we found RFP blocks, try to build the complete title
    if rfp_blocks:
        # Sort by page then position
        rfp_blocks.sort(key=lambda b: (b["page"], b["top"]))
        
        # Find all blocks on the same page as the first RFP block
        first_rfp_page = rfp_blocks[0]["page"]
        page_blocks = [b for b in early_blocks if b["page"] == first_rfp_page]
        page_blocks.sort(key=lambda b: b["top"])
        
        # Find the RFP block index
        rfp_index = next((i for i, b in enumerate(page_blocks) if "RFP:" in b["text"] or "Request for Proposal" in b["text"]), 0)
        
        # Collect title parts starting from RFP block
        title_parts = []
        for i in range(rfp_index, min(rfp_index + 6, len(page_blocks))):
            text = page_blocks[i]["text"].strip()
            # Stop if we hit a date or very different formatting
            if any(month in text.upper() for month in ["JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE", 
                                                       "JULY", "AUGUST", "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER"]):
                break
            if text and len(text) > 2:
                title_parts.append(text)
        
        if title_parts:
            # Clean up the title
            title = " ".join(title_parts)
            # Remove extra spaces
            title = " ".join(title.split())
            return title
    
    # Fallback to original logic for non-RFP documents
    pages = {}
    for block in early_blocks:
        page = block["page"]
        if page not in pages:
            pages[page] = []
        pages[page].append(block)
    
    for page_num in sorted(pages.keys()):
        page_blocks = pages[page_num]
        page_blocks.sort(key=lambda b: -b["size"])
        
        if not page_blocks:
            continue
            
        max_size = page_blocks[0]["size"]
        large_blocks = [b for b in page_blocks if b["size"] >= max_size * 0.8]
        
        if not large_blocks:
            continue
        
        large_blocks.sort(key=lambda b: b["top"])
        
        # Group blocks that are close together vertically
        grouped_blocks = []
        current_group = [large_blocks[0]]
        
        for i in range(1, len(large_blocks)):
            if large_blocks[i]["top"] - large_blocks[i-1]["top"] < 100:
                current_group.append(large_blocks[i])
            else:
                grouped_blocks.append(current_group)
                current_group = [large_blocks[i]]
        
        grouped_blocks.append(current_group)
        
        best_group = None
        best_score = 0
        
        for group in grouped_blocks:
            avg_size = sum(b["size"] for b in group) / len(group)
            total_length = sum(len(b["text"].strip()) for b in group)
            
            if total_length > 200:
                continue
                
            score = avg_size * min(total_length, 100)
            
            if group[0]["top"] < 400:
                score *= 1.5
                
            if score > best_score:
                best_score = score
                best_group = group
        
        if best_group:
            title_parts = []
            total_chars = 0
            
            for block in best_group:
                text = block["text"].strip()
                if len(text) > 2 and not text.isdigit() and total_chars < 200:
                    title_parts.append(text)
                    total_chars += len(text)
            
            if title_parts:
                title = " ".join(title_parts)
                
                content_indicators = [
                    "ingredients:", "instructions:", "•", "method:", "recipe", "step", "procedure"
                ]
                
                if any(indicator in title.lower() for indicator in content_indicators):
                    continue
                
                if len(title) > 150:
                    title = title.split('\n')[0].split('.')[0].strip()
                
                if len(title) > 150:
                    return ""
                    
                return title
    
    return ""

def main(pdf_path):
    text_blocks = extract_pdf_features(pdf_path)
    outline = predict_headings(text_blocks)
    title = extract_title(text_blocks)
    result = {
        "title": title,
        "outline": outline
    }
    base_filename = 'output'
    output_path = os.path.join(os.getcwd(), f"{base_filename}.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4, ensure_ascii=False)

    with open(output_path, "r", encoding="utf-8") as f:
        content = f.read()
        print(content)
    

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py path/to/file.pdf")
        sys.exit(1)

    pdf_path = sys.argv[1]
    main(pdf_path)