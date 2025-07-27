import time
import psutil
import os
import threading
import gc
from typing import Dict, Any

from app.document_processor import DocumentProcessor
from app.structure_analyzer import StructureAnalyzer
from app.output_generator import OutputGenerator

class FastPDFProcessor:

    def __init__(self):
        self.processor = DocumentProcessor()
        self.analyzer = StructureAnalyzer()
        self.generator = OutputGenerator()

    def process_pdf(self, file_path: str) -> Dict[str, Any]:
        doc_content = self.processor.extract_structured_content(file_path)
        title, headings = self.analyzer.analyze(doc_content)
        output_data = self.generator.format_json_outline(title, headings)
        return output_data

class ResourceMonitor:

    def __init__(self):
        self.start_time = time.time()
        self.peak_memory = 0
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._is_running = False

    def start(self):
        self._is_running = True
        self._monitor_thread.start()

    def stop(self):
        self._is_running = False

    def _monitor_loop(self):
        process = psutil.Process()
        while self._is_running:
            try:
                mem_info = process.memory_info().rss
                self.peak_memory = max(self.peak_memory, mem_info)
                time.sleep(0.1)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                break
    
    def get_report(self, files_processed: int, total_pages: int) -> Dict:
        elapsed_time = time.time() - self.start_time
        return {
            "files_processed": files_processed,
            "total_pages": total_pages,
            "total_time_seconds": round(elapsed_time, 2),
            "peak_memory_mb": round(self.peak_memory / (1024 * 1024), 2),
            "avg_time_per_file": round(elapsed_time / files_processed if files_processed else 0, 2)
        }