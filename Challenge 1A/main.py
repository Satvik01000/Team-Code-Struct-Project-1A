import app.extract_features as ef
import json

pdf=ef.extract_spans('./Adobe-India-Hackathon25-main/Challenge - 1(a)/Datasets/Pdfs/Math For ML.pdf')
print(json.dumps(pdf, indent=2))