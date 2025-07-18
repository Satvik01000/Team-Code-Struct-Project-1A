import csv
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from collections import Counter
import re

def is_latin(text):
    return bool(re.match(r'^[\x00-\x7F]+$', text))

with open("label_data.csv", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    data = list(reader)

X = []
y = []

font_to_index = {}
font_index_counter = 0

for item in data:
    font = item["font"]
    if font not in font_to_index:
        font_to_index[font] = font_index_counter
        font_index_counter += 1

    text = item["text"]
    use_case_features = is_latin(text)

    features = [
        float(item["size"]),
        float(item["top"]),
        font_to_index[font],
        int(text.isupper()) if use_case_features else 0,
        int(text.endswith(":")),
        int(text.istitle()) if use_case_features else 0,
        len(text.split()),
        len(text),
        int(text[0].isdigit())
    ]

    X.append(features)
    y.append(item["label"])

print("Label distribution:", Counter(y))

le = LabelEncoder()
y_encoded = le.fit_transform(y)

X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42)

model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"Validation Accuracy: {accuracy * 100:.2f}%")

joblib.dump(model, "trained_model_and_data/model.pkl")
joblib.dump(le, "trained_model_and_data/label_encoder.pkl")
joblib.dump(font_to_index, "trained_model_and_data/font_map.pkl")

print("Model trained and saved.")