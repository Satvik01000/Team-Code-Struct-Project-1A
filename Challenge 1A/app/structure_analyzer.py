import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from collections import Counter, defaultdict
from typing import List, Dict, Any, Tuple
import re

class StructureAnalyzer:
    def __init__(self):
        self.STYLE_WEIGHT = 0.5
        self.POSITION_WEIGHT = 0.4
        self.CONTENT_WEIGHT = 0.1
        self.HEADING_THRESHOLD_RATIO = 1.2

        self.CONTENT_PATTERNS = {
            'english': [
                r'^[A-Z][A-Z\s]{2,}$',       # ALL CAPS
                r'^\d+\.?\s+[A-Z]',          # e.g., "1. Introduction"
                r'^[IVX]+\.?\s+[A-Z]',       # e.g., "I. Overview"
                r'^(Chapter|Section)\s+\d+'
            ],
            'multilingual': [
                r'^[\u4e00-\u9fff]+',
                r'^[\u3040-\u309f]+',
                r'^[\u30a0-\u30ff]+',
            ]
        }

    def analyze(self, doc_content: Dict[str, Any]) -> Tuple[str, List[Dict[str, Any]]]:
        title = self._find_document_title(doc_content)
        all_spans = self._get_all_spans(doc_content)

        if not all_spans:
            return title, []

        style_metrics = self._calculate_style_metrics(all_spans)
        heading_candidates = self._score_candidates(all_spans, style_metrics)
        headings = self._classify_candidates(heading_candidates)
        
        return title, headings

    def _get_all_spans(self, doc_content: Dict[str, Any]) -> List[Dict[str, Any]]:
        all_spans = []
        for page in doc_content.get("pages", []):
            for span in page.get("content_spans", []):
                enriched_span = span.copy()
                enriched_span["page_index"] = page.get("page_index", 1)
                if enriched_span.get("text", "").strip():
                    all_spans.append(enriched_span)
        return all_spans
        
    def _calculate_style_metrics(self, all_spans: List[Dict[str, Any]]) -> Dict[str, Any]:
        sizes = [s.get("style_info", {}).get("size", 12) for s in all_spans]
        median_size = np.median(sizes)
        
        significant_sizes = sorted(
            [size for size in set(sizes) if size > median_size * self.HEADING_THRESHOLD_RATIO],
            reverse=True
        )
        return {"median_size": median_size, "significant_sizes": significant_sizes}

    def _score_candidates(self, all_spans: List[Dict[str, Any]], metrics: Dict) -> List:
        scored_spans = []
        for span in all_spans:
            score = self._calculate_span_score(span, metrics)
            if score > 0.35: # Keep spans with a reasonable chance of being a heading.
                span["heading_score"] = score
                scored_spans.append(span)
        return scored_spans

    def _calculate_span_score(self, span: Dict, metrics: Dict) -> float:
        style_info = span.get("style_info", {})
        text = span.get("text", "")
        
        size_score = 0.0
        size = style_info.get("size", 12)
        if size in metrics["significant_sizes"]:
            size_score = min(size / (metrics["median_size"] * 2.5), 1.0)

        content_score = 0.0
        for pattern in self.CONTENT_PATTERNS['english']:
            if re.match(pattern, text):
                content_score = 0.5; break
        if text.isupper(): content_score = max(content_score, 0.4)
        if text.istitle(): content_score = max(content_score, 0.2)
        
        y_pos = style_info.get("y0", 500)
        position_score = max(1.0 - (y_pos / 800), 0) # Assumes ~800 page height.
        
        final_score = (
            size_score * self.STYLE_WEIGHT +
            position_score * self.POSITION_WEIGHT +
            content_score * self.CONTENT_WEIGHT
        )

        if len(text) > 150: final_score *= 0.5

        return final_score

    def _classify_candidates(self, candidates: List[Dict]) -> List[Dict[str, Any]]:
        if not candidates: return []

        size_groups = defaultdict(list)
        for cand in candidates:
            size = cand.get("style_info", {}).get("size", 12)
            size_groups[size].append(cand)
        
        sorted_sizes = sorted(size_groups.keys(), reverse=True)[:3]
        
        headings = []
        for i, size in enumerate(sorted_sizes):
            level = f"H{i+1}"
            for cand in size_groups[size]:
                headings.append({
                    "level": level,
                    "text": cand.get("text", "").strip(),
                    "page": cand.get("page_index", 1)
                })

        headings.sort(key=lambda h: (h["page"], h["level"]))
        return self._deduplicate(headings)

    def _find_document_title(self, doc_content: Dict[str, Any]) -> str:
        if doc_content.get("title", "").strip():
            return doc_content["title"]

        if doc_content.get("pages"):
            first_page_spans = doc_content["pages"][0].get("content_spans", [])
            top_spans = [s for s in first_page_spans if s.get("style_info",{}).get("y0", 500) < 200]
            if top_spans:
                top_spans.sort(key=lambda s: s.get("style_info",{}).get("size", 0), reverse=True)
                return top_spans[0].get("text", "Untitled Document").strip()

        return "Untitled Document"
        
    def _deduplicate(self, headings: List[Dict]) -> List[Dict]:
        unique_headings = []
        seen_text = set()
        for h in headings:
            text_key = h["text"].lower().strip()
            if text_key not in seen_text:
                seen_text.add(text_key)
                unique_headings.append(h)
        return unique_headings