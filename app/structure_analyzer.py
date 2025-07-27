import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from collections import Counter, defaultdict
from typing import List, Dict, Any, Tuple
import re

class StructureAnalyzer:
    def __init__(self):
        self.STYLE_WEIGHT = 0.5
        self.POSITION_WEIGHT = 0.3
        self.CONTENT_WEIGHT = 0.2
        self.HEADING_THRESHOLD_RATIO = 1.2

        self.CONTENT_PATTERNS = {
            'english': [
                r'^[A-Z][A-Z\s]{2,}$',              # ALL CAPS
                r'^\d+\.?\s+[A-Z]',                 # 1. Introduction
                r'^[IVX]+\.?\s+[A-Z]',              # I. Overview
                r'^(Chapter|Section)\s+\d+',        # Chapter 1
                r'^\d+\.\d+\.?\s+',                 # 1.1 Subsection
                r'^\d+\.\d+\.\d+\.?\s+',            # 1.1.1 Sub-subsection
                r'^[A-Z]\.\s+',                     # A. Section
                r'^(Appendix|Annex)\s+[A-Z]',       # Appendix A
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
            if score > 0.3:
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
        
        flags = style_info.get("flags", 0)
        if flags & 16:  # Bold flag in fitz
            size_score = min(size_score + 0.2, 1.0)
        elif "bold" in style_info.get("font", "").lower():
            size_score = min(size_score + 0.1, 1.0)

        content_score = 0.0
        for pattern in self.CONTENT_PATTERNS['english']:
            if re.match(pattern, text):
                content_score = 0.5
                break
        
        if text.isupper() and len(text.split()) <= 10:
            content_score = max(content_score, 0.4)
        if text.istitle() and len(text.split()) <= 8:
            content_score = max(content_score, 0.2)
        
        if len(text.split()) <= 5 and size > metrics["median_size"] * 1.5:
            content_score = max(content_score, 0.3)
        
        y_pos = style_info.get("y0", 500)
        position_score = max(1.0 - (y_pos / 800), 0)
        
        final_score = (
            size_score * self.STYLE_WEIGHT +
            position_score * self.POSITION_WEIGHT +
            content_score * self.CONTENT_WEIGHT
        )

        if len(text) > 150:
            final_score *= 0.5
        
        if text.rstrip().endswith((',', ';', 'and', 'or')):
            final_score *= 0.7
        
        if re.match(r'^[\d\s\-\./]+$', text):
            final_score *= 0.3

        return final_score

    def _classify_candidates(self, candidates: List[Dict]) -> List[Dict[str, Any]]:
        if not candidates:
            return []

        candidates.sort(key=lambda x: x.get("heading_score", 0), reverse=True)
        
        size_groups = defaultdict(list)
        for cand in candidates:
            size = round(cand.get("style_info", {}).get("size", 12))  # Round to avoid float issues
            size_groups[size].append(cand)
        
        sorted_sizes = sorted(size_groups.keys(), reverse=True)
        
        if len(sorted_sizes) >= 3:
            headings = []
            for i, size in enumerate(sorted_sizes[:3]):
                level = f"H{i+1}"
                for cand in size_groups[size]:
                    headings.append({
                        "level": level,
                        "text": cand.get("text", "").strip(),
                        "page": cand.get("page_index", 1)
                    })
        else:
            headings = []
            total = len(candidates)
            
            for i, cand in enumerate(candidates):
                if i < total * 0.3:
                    level = "H1"
                elif i < total * 0.6:
                    level = "H2"
                else:
                    level = "H3"
                
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
            
            page_height = doc_content["pages"][0].get("height", 800)
            top_spans = [s for s in first_page_spans 
                         if s.get("style_info",{}).get("y0", 500) < page_height * 0.25]
            
            if top_spans:
                top_spans.sort(key=lambda s: s.get("style_info",{}).get("y0", 0))
                
                title_parts = []
                last_y = -1
                last_size = -1
                
                for span in top_spans[:5]:  # Check first 5 spans
                    y = span.get("style_info",{}).get("y0", 0)
                    size = span.get("style_info",{}).get("size", 0)
                    text = span.get("text", "").strip()
                    
                    if (last_y == -1 or 
                        (y - last_y < 50 and abs(size - last_size) < 4 and len(text) > 3)):
                        title_parts.append(text)
                        last_y = y
                        last_size = size
                    else:
                        break
                
                if title_parts:
                    return " ".join(title_parts)

        return "Untitled Document"
        
    def _deduplicate(self, headings: List[Dict]) -> List[Dict]:
        unique_headings = []
        seen_text = set()
        
        for h in headings:
            text = h["text"].strip()
            text_key = text.lower()
            
            if text_key in seen_text:
                continue
            
            if re.match(r'^(page\s+)?\d+$', text_key):
                continue
            
            if len(text) < 3:
                continue
            
            if re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', text):
                continue
            
            seen_text.add(text_key)
            unique_headings.append(h)
        
        return unique_headings[:50]