import fitz
from typing import List, Dict, Any
import logging

class DocumentProcessor:

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def extract_structured_content(self, file_path: str) -> Dict[str, Any]:
        try:
            return self._process_with_fitz(file_path)
        except Exception as e:
            self.logger.error(f"Could not process file {file_path}: {e}")
            return self._create_empty_output()

    def _process_with_fitz(self, file_path: str) -> Dict[str, Any]:
        doc_content = self._create_empty_output()

        try:
            doc = fitz.open(file_path)
            doc_content["total_pages"] = len(doc)
            doc_content["title"] = doc.metadata.get("title", "")

            for i, page in enumerate(doc, 0):
                page_content = self._extract_page_data_fitz(page, i)
                doc_content["pages"].append(page_content)
            doc.close()
        except Exception as e:
            self.logger.error(f"Fitz extraction failed: {e}")
            return self._create_empty_output()
        
        return doc_content

    def _extract_page_data_fitz(self, page, page_idx: int) -> Dict[str, Any]:
        page_content = {
            "page_index": page_idx, "content_spans": [], "raw_text": "",
            "width": page.rect.width, "height": page.rect.height
        }
        try:
            blocks = page.get_text("dict").get("blocks", [])
            page_content["raw_text"] = page.get_text()
            
            for block in blocks:
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        if span.get("text", "").strip():
                            bbox = span.get("bbox", (0, 0, 0, 0))
                            span_data = {
                                "text": span.get("text", ""),
                                "style_info": {
                                    "font": span.get("font", ""), 
                                    "size": span.get("size", 12),
                                    "flags": span.get("flags", 0), 
                                    "x0": bbox[0], 
                                    "y0": bbox[1],
                                    "x1": bbox[2],
                                    "y1": bbox[3]
                                }
                            }
                            page_content["content_spans"].append(span_data)
        except Exception as e:
            self.logger.warning(f"Fitz page {page_idx} processing error: {e}")
        
        return page_content

    def _create_empty_output(self) -> Dict[str, Any]:
        return {"title": "", "total_pages": 0, "pages": []}