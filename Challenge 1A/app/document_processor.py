import fitz
import pdfplumber
from typing import List, Dict, Any
import logging

class DocumentProcessor:

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.preview_page_count = 5

    def extract_structured_content(self, file_path: str) -> Dict[str, Any]:
        try:
            engine = self._select_extraction_engine(file_path)
            
            if engine == "pdfplumber":
                return self._process_with_pdfplumber(file_path)
            else:
                return self._process_with_fitz(file_path)

        except Exception as e:
            self.logger.error(f"Could not process file {file_path}: {e}")
            return self._create_empty_output()

    def _process_with_fitz(self, file_path: str) -> Dict[str, Any]:
        doc_content = self._create_empty_output()
        doc_content["extraction_engine"] = "fitz"

        try:
            doc = fitz.open(file_path)
            doc_content["total_pages"] = len(doc)
            doc_content["title"] = doc.metadata.get("title", "")

            for i, page in enumerate(doc):
                page_content = self._extract_page_data_fitz(page, i + 1)
                doc_content["pages"].append(page_content)
            doc.close()
        except Exception as e:
            self.logger.error(f"Fitz extraction failed: {e}")
            return self._create_empty_output()
        
        return doc_content

    def _process_with_pdfplumber(self, file_path: str) -> Dict[str, Any]:
        doc_content = self._create_empty_output()
        doc_content["extraction_engine"] = "pdfplumber"

        try:
            with pdfplumber.open(file_path) as pdf:
                doc_content["total_pages"] = len(pdf.pages)
                doc_content["title"] = pdf.metadata.get("Title", "")

                for i, page in enumerate(pdf.pages, 1):
                    page_content = self._extract_page_data_pdfplumber(page, i)
                    doc_content["pages"].append(page_content)
        except Exception as e:
            self.logger.error(f"Pdfplumber extraction failed: {e}")
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
                                    "font": span.get("font", ""), "size": span.get("size", 12),
                                    "flags": span.get("flags", 0), "x0": bbox[0], "y0": bbox[1],
                                }
                            }
                            page_content["content_spans"].append(span_data)
        except Exception as e:
            self.logger.warning(f"Fitz page {page_idx} processing error: {e}")
        
        return page_content

    def _extract_page_data_pdfplumber(self, page, page_idx: int) -> Dict[str, Any]:
        # Extract all text spans from a single page using pdfplumber.
        page_content = {
            "page_index": page_idx, "content_spans": [], "raw_text": "",
            "width": page.width, "height": page.height
        }
        try:
            page_content["raw_text"] = page.extract_text() or ""
        except Exception as e:
             self.logger.warning(f"Pdfplumber page {page_idx} processing error: {e}")
             
        return page_content

    def _select_extraction_engine(self, file_path: str) -> str:
        try:
            with pdfplumber.open(file_path) as pdf:
                text_found_count = 0
                num_preview_pages = min(len(pdf.pages), self.preview_page_count)
                if num_preview_pages == 0: return "fitz"

                for i in range(num_preview_pages):
                    if pdf.pages[i].extract_text():
                        text_found_count += 1
                
                if (text_found_count / num_preview_pages) > 0.8:
                    return "pdfplumber"
        except Exception:
            return "fitz"
        return "fitz"

    def _create_empty_output(self) -> Dict[str, Any]:
        return {"title": "", "total_pages": 0, "pages": [], "extraction_engine": "none"}