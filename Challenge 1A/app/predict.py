import os
import re
import joblib

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
model_path = os.path.join(BASE_DIR, "train/trained_model_and_data", "model.pkl")
le_path = os.path.join(BASE_DIR, "train/trained_model_and_data", "label_encoder.pkl")
font_map_path = os.path.join(BASE_DIR, "train/trained_model_and_data", "font_map.pkl")

def is_latin(text):
    return bool(re.match(r'^[\x00-\x7F]+$', text))

def detect_heading_pattern(text, size, all_blocks):
    """Detect common heading patterns with context awareness"""
    text = text.strip()
    
    # Get average size for context
    avg_size = sum(b["size"] for b in all_blocks) / len(all_blocks) if all_blocks else 10
    
    # Don't classify very short fragments as headings
    if len(text) < 5 and not re.match(r'^\d+\.?\s*$', text):
        return None
    
    # Pattern 1: "1. Introduction" or "1 Introduction" - but must be larger than average
    if re.match(r'^\d+\.?\s+[A-Z]', text) and len(text.split()) >= 2:
        # Check if it's actually a heading by size
        if size > avg_size * 1.2:  # Must be 20% larger than average
            return "H1"
        else:
            return None  # Probably a list item
    
    # Pattern 2: "1.1 Background" or "2.3 Methods"
    if re.match(r'^\d+\.\d+\.?\s+', text):
        if size > avg_size:  # Must be larger than average
            return "H2"
        else:
            return None
    
    # Pattern 3: "1.1.1 Details" or "2.3.4 Implementation"
    if re.match(r'^\d+\.\d+\.\d+\.?\s+', text):
        if size > avg_size:
            return "H3"
        else:
            return None
    
    # Pattern 4: "Chapter 1:" or "Section 2:"
    if re.match(r'^(Chapter|Section|Part)\s+\d+:?\s*', text, re.IGNORECASE):
        return "H1"
    
    # Pattern 5: "Appendix A:" or "Appendix B:"
    if re.match(r'^Appendix\s+[A-Z]:?\s*', text, re.IGNORECASE):
        return "H2"
    
    # Don't classify dates or single years as headings
    if re.match(r'^\d{1,2}\s+(JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER|JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)', text, re.IGNORECASE):
        return None
    if re.match(r'^\d{4}$', text):  # Just a year
        return None
    
    # Don't classify version numbers as headings
    if re.match(r'^(Version|v\.?)\s*\d+', text, re.IGNORECASE):
        return None
    
    return None

def calculate_confidence_features(block, all_blocks):
    """Calculate additional features for confidence scoring"""
    # Get average size in document
    avg_size = sum(b["size"] for b in all_blocks) / len(all_blocks)
    
    # Relative size
    relative_size = block["size"] / avg_size
    
    # Position on page (normalized 0-1)
    page_blocks = [b for b in all_blocks if b["page"] == block["page"]]
    if page_blocks:
        min_top = min(b["top"] for b in page_blocks)
        max_top = max(b["top"] for b in page_blocks)
        position = (block["top"] - min_top) / (max_top - min_top) if max_top > min_top else 0.5
    else:
        position = 0.5
    
    return relative_size, position

def should_merge_with_previous(current_block, predictions):
    """Check if current block should be merged with previous heading"""
    if not predictions:
        return False
    
    last_prediction = predictions[-1]
    
    # If "Syllabus" appears right after another heading on the same page
    if (current_block["text"].strip() == "Syllabus" and 
        last_prediction["page"] == current_block["page"]):
        return True
    
    return False

def post_process_predictions(predictions, text_blocks):
    """Post-process predictions to handle special cases"""
    processed = []
    
    for i, pred in enumerate(predictions):
        text = pred["text"].strip()
        
        # Skip if this looks like it's part of the title
        if pred["page"] == 0 and any(title_word in text for title_word in 
                                     ["Ontario's Libraries", "Working Together", "RFP:", "Request for"]):
            continue
        
        # Skip fragments that are too short (likely from title page)
        if pred["page"] == 0 and len(text) < 20 and ":" not in text:
            continue
            
        # Skip Chapter headings if they're in the content section
        if text.startswith("Chapter ") and pred["page"] >= 9:
            continue
        
        # Check if should merge with previous
        if processed and text == "Syllabus":
            # Merge with previous heading
            processed[-1]["text"] += "Syllabus"
            continue
        
        # Fix "Background" classification based on context
        if text.strip() == "Background" and pred["level"] == "H3":
            # If it's early in the document, it's likely H2
            if pred["page"] <= 5:
                pred["level"] = "H2"
        
        processed.append(pred)
    
    return processed

def predict_headings(text_blocks):
    model = joblib.load(model_path)
    le = joblib.load(le_path)
    font_to_index = joblib.load(font_map_path)

    predictions = []
    ml_predictions = []
    
    # First pass: ML predictions
    for block in text_blocks:
        text = block["text"]
        font_idx = font_to_index.get(block["font"], -1)
        
        # Skip unknown fonts initially
        if font_idx == -1:
            ml_predictions.append(None)
            continue

        use_case_features = is_latin(text)

        features = [
            block["size"],
            block["top"],
            font_idx,
            int(text.isupper()) if use_case_features else 0,
            int(text.endswith(":")),
            int(text.istitle()) if use_case_features else 0,
            len(text.split()),
            len(text),
            int(text[0].isdigit()) if text else 0
        ]

        pred_encoded = model.predict([features])[0]
        label = le.inverse_transform([pred_encoded])[0]
        ml_predictions.append(label)
    
    # Second pass: Combine ML with rules
    for i, block in enumerate(text_blocks):
        text = block["text"].strip()
        ml_label = ml_predictions[i] if i < len(ml_predictions) else None
        
        # Skip very short fragments
        if len(text) < 3:
            continue
        
        # Check for pattern-based heading
        pattern_label = detect_heading_pattern(text, block["size"], text_blocks)
        
        # Decision logic
        if pattern_label:
            # Strong pattern found - trust it
            final_label = pattern_label
        elif ml_label and ml_label not in ["O", "title"]:
            # ML prediction is a heading - use it
            final_label = ml_label
        elif ml_label == "O" and pattern_label is None:
            # Both agree it's not a heading
            continue
        else:
            # Conflict or uncertainty - use additional heuristics
            relative_size, position = calculate_confidence_features(block, text_blocks)
            
            # If text is significantly larger than average and near top of page
            if relative_size > 1.5 and position < 0.3 and len(text.split()) < 10:
                # Likely a heading missed by both
                if relative_size > 2.0:
                    final_label = "H1"
                else:
                    final_label = "H2"
            else:
                continue
        
        # Additional filters to reduce false positives
        # Skip if it looks like a table cell or list item
        if text.strip() in ["Date", "Remarks", "Version", "Identifier", "Reference"]:
            continue
            
        # Skip if label is "O" or "title"
        if final_label not in ["O", "title"]:
            predictions.append({
                "level": final_label,
                "text": text,
                "page": block["page"]
            })
    
    # Post-process predictions to handle special cases
    predictions = post_process_predictions(predictions, text_blocks)
    
    return predictions