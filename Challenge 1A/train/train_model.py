import json
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from collections import Counter

with open("label_data.json", "r") as f:
    data = json.load(f)

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

    features = [
        item["size"],
        item["top"],
        font_to_index[font],
        int(text.isupper()),
        int(text.endswith(":")),
        int(text.istitle()),
        len(text.split()),
        len(text),
        int(text[0].isdigit())
    ]

    X.append(features)
    y.append(item["label"])

print("Label distribution:", Counter(y))

le = LabelEncoder()
y_encoded = le.fit_transform(y)

X_train, X_test, y_train, y_test = train_test_split( X, y_encoded, test_size=0.2, random_state=42)

model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"Validation Accuracy: {accuracy * 100:.2f}%")

joblib.dump(model, "model.pkl")
joblib.dump(le, "label_encoder.pkl")
joblib.dump(font_to_index, "font_map.pkl")

print("Model trained and saved.")