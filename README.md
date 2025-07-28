
# PDF Structure Extraction Solution

## Overview

This is the solution for problem 1A. It automatically processes PDF documents to extract a structured outline, including the document title and a hierarchy of headings (H1, H2, H3).

The entire process runs offline within a Docker container, designed for speed and efficiency to meet the specified performance constraints.

## How It Works

The solution follows a modular, three-stage pipeline to process each PDF:

1. **Extraction**: The system first reads the PDF and extracts not just the text, but also critical metadata for each piece of text, such as font size, font weight (bold), and its precise X/Y coordinates on the page.

2. **Analysis**: Next, this rich data is passed to an analysis engine. Instead of relying on a single attribute, this engine uses a weighted scoring algorithm to determine if a piece of text is a heading. The score is based on a combination of style (font size, weight), position (text near the top of a page scores higher), and content (text that matches common heading patterns like "1.1 Section" or "Chapter 2").

3. **Classification & Generation**: Based on the calculated scores and font sizes, the potential headings are classified into H1, H2, and H3 levels. The final structured data, including the document title, is then formatted and saved as a JSON file.

## Code Structure

- `main.py`: The main entry point that orchestrates the entire workflow. It finds PDF files, manages the processing loop, and generates the final performance report.

- `app/document_processor.py`: Responsible for reading the PDF file using `PyMuPDF` and extracting the detailed text and style information from each page.

- `app/structure_analyzer.py`: The core of the solution. It contains the logic for scoring text spans, identifying the document title, and classifying headings based on the heuristic model.

- `app/output_generator.py`: Handles the formatting of the final data into the required JSON structure and sanitizes the output text.

- `app/optimize.py`: Contains the main processing pipeline class and a resource monitor to track execution time and peak memory usage, ensuring the solution adheres to performance requirements.

## Key Libraries Used

- **PyMuPDF**: For robust and efficient PDF parsing and data extraction.
- **scikit-learn & numpy**: Used for statistical calculations (median, quantiles) that help in the heading classification logic.
- **psutil**: To monitor the system's resource usage (CPU/memory) during execution.

## How to Build and Run

The solution is fully containerized with Docker.

### 1. Build the Docker Image

Navigate to the project's root directory (where the `Dockerfile` is located) and run the following command:

```bash
docker build --platform linux/amd64 -t pdf-processor .
````

### 2. Run the Container

To process PDFs, place them in an `input` directory on your host machine. The container will write the resulting JSON files to an `output` directory.

Use the following command to run the container. It mounts the local `input` and `output` directories and disables networking as per the challenge requirements.

```bash
docker run --rm -v $(pwd)/input:/app/input:ro -v $(pwd)/output:/app/output --network none pdf-processor
```

The container will automatically process all `.pdf` files found in `/app/input` and place the corresponding `.json` files in `/app/output`.