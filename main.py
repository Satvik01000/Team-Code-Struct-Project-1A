import os
from app.optimize import FastPDFProcessor, ResourceMonitor
from app.output_generator import OutputGenerator

INPUT_DIRECTORY = "/app/input"
OUTPUT_DIRECTORY = "/app/output"

def main():
    os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)
    
    try:
        pdf_files = [f for f in os.listdir(INPUT_DIRECTORY) if f.lower().endswith(".pdf")]
    except FileNotFoundError:
        print(f"Error: Input directory not found at '{INPUT_DIRECTORY}'.")
        return

    print(f"Found {len(pdf_files)} PDF(s) to process.")

    monitor = ResourceMonitor()
    monitor.start()

    processor = FastPDFProcessor()
    generator = OutputGenerator()
    total_pages = 0

    for file_name in pdf_files:
        input_file = os.path.join(INPUT_DIRECTORY, file_name)
        output_file = os.path.join(OUTPUT_DIRECTORY, f"{os.path.splitext(file_name)[0]}.json")
        
        try:
            result_data = processor.process_pdf(input_file)
            generator.save_to_file(result_data, output_file)
            total_pages += len(result_data.get("outline", []))
        except Exception as e:
            print(f"FATAL ERROR processing {file_name}: {e}")

    monitor.stop()
    report = monitor.get_report(len(pdf_files), total_pages)
    
    print("\n--- PERFORMANCE REPORT ---")
    print(f"  Files Processed: {report['files_processed']}")
    print(f"  Total Time: {report['total_time_seconds']}s")
    print(f"  Peak Memory Usage: {report['peak_memory_mb']} MB")
    print("--------------------------\n")

if __name__ == "__main__":
    main()