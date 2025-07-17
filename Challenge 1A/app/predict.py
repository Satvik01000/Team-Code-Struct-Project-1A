import os
import joblib

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
model_path = os.path.join(BASE_DIR, "train", "model.pkl")
le_path = os.path.join(BASE_DIR, "train", "label_encoder.pkl")
font_map_path = os.path.join(BASE_DIR, "train", "font_map.pkl")

def predict_headings(text_blocks):
    model = joblib.load(model_path)
    le = joblib.load(le_path)
    font_to_index = joblib.load(font_map_path)

    predictions = []

    for block in text_blocks:
        font_idx = font_to_index.get(block["font"], -1)
        if font_idx == -1:
            continue

        features = [
            block["size"],
            block["top"],
            font_idx,
            int(block["text"].isupper()),
            int(block["text"].endswith(":"))
        ]

        pred_encoded = model.predict([features])[0]
        label = le.inverse_transform([pred_encoded])[0]

        if label != "O":
            predictions.append({
                "level": label,
                "text": block["text"],
                "page": block["page"]
            })

    return predictions
