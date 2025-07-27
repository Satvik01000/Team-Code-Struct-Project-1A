import json
from typing import List, Dict, Any

class OutputGenerator:
    def format_json_outline(self, title: str, headings: List[Dict]) -> Dict:
        return {
            "title": self._sanitize(title, 200),
            "outline": self._validate_headings(headings)
        }
        
    def _validate_headings(self, headings: List[Dict]) -> List[Dict]:
        validated = []
        for h in headings:
            text = self._sanitize(h.get("text", ""), 150)
            level = h.get("level", "H1")
            page = h.get("page", 0)

            if text and level in ["H1", "H2", "H3"]:
                validated.append({"level": level, "text": text, "page": page})
        return validated

    def _sanitize(self, text: str, max_len: int) -> str:
        if not text or not isinstance(text, str): 
            return ""
        cleaned = " ".join(text.split())
        if len(cleaned) > max_len:
            cleaned = cleaned[:max_len] + "..."
        return cleaned

    def save_to_file(self, data: Dict, file_path: str):
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving output to {file_path}: {e}")
            return False