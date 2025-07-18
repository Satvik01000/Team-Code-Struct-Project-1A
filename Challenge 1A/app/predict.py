import os
import re
import joblib

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
model_path = os.path.join(BASE_DIR, "train/trained_model_and_data", "model.pkl")
le_path = os.path.join(BASE_DIR, "train/trained_model_and_data", "label_encoder.pkl")
font_map_path = os.path.join(BASE_DIR, "train/trained_model_and_data", "font_map.pkl")

def is_latin(text):
    return bool(re.match(r'^[\x00-\x7F]+$', text))

def predict_headings(text_blocks):
    model = joblib.load(model_path)
    le = joblib.load(le_path)
    font_to_index = joblib.load(font_map_path)

    predictions = []

    for block in text_blocks:
        text = block["text"]
        font_idx = font_to_index.get(block["font"], -1)
        if font_idx == -1:
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
            int(text[0].isdigit())
        ]

        pred_encoded = model.predict([features])[0]
        label = le.inverse_transform([pred_encoded])[0]

        if label != "O":
            predictions.append({
                "level": label,
                "text": text,
                "page": block["page"]
            })

    return predictions