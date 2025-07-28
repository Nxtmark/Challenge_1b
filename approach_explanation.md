

# PDF Relevance Extraction – Process Overview (Adobe Hackathon Round 1B)



1. The process starts by accepting three key inputs:
   - A folder containing the PDF documents
   - A defined persona (e.g., "Investment Analyst")
   - A job-to-be-done related to that persona (e.g., "Analyze revenue trends...")

2. A query is automatically constructed using these inputs.  
   Example: "Investment Analyst needs to Analyze revenue trends..."

3. Each PDF is processed in parallel using Python’s ProcessPoolExecutor.  
   This ensures the system handles multiple documents efficiently within the 60-second constraint.

4. For every PDF:
   - The file is opened and all pages are scanned.
   - Text blocks are extracted from each page.
   - Only blocks longer than 100 characters are retained to ensure content richness.

5. Deduplication:
   - All text blocks are vectorized using TF-IDF (Term Frequency–Inverse Document Frequency).
   - Cosine similarity is calculated between all blocks.
   - Blocks with a similarity score greater than 0.8 are considered duplicates and removed.

6. Relevance scoring:
   - The semantic query is also vectorized using TF-IDF.
   - Each remaining block is compared against the query using cosine similarity.
   - The two most relevant blocks from each PDF are selected.

7. Top blocks from all PDFs are gathered and sorted by length (assuming longer blocks contain more substance).  
   The top 10 blocks are chosen.

8. For each top block:
   - A section title is extracted from the first line.
   - A structured summary is created, including document name, page number, and importance rank.
   - The full block text is added to a separate subsection analysis section.

9. The final output is saved as a structured JSON file at: `challenge1b_output.json` in the same collection folder.


Other Things --->>>>>>
==============================
1-Model & Technical Constraints
==============================

- Vectorization: TF-IDF from scikit-learn  
- Translation Support: Apertium (offline multilingual translation)  
- No SentenceTransformer used  
- No GPU needed (runs fully on CPU)  
- Internet Access: Not required  
- Runtime: Under 60 seconds for 3–5 PDFs  
- Compliance: Entire setup stays under 1GB (PDFs, translation model, code, and output)


==============================
2-Output Format
==============================

The output JSON includes:

1. metadata:
   - persona  
   - job_to_be_done  
   - input_documents (PDF filenames)  
   - timestamp  

2. extracted_sections:
   - document  
   - page_number  
   - section_title  
   - importance_rank  

3. subsection_analysis:
   - document  
   - page_number  
   - refined_text  


==============================
3-How to Run
==============================

▶ Option 1: Run Locally (Python environment)

1. Install dependencies:  
   `pip install -r requirements.txt`

2. Ensure collections are in the same folder as analyze.py

3. Run:  
   `python analyze.py`

4. Output appears inside each collection folder as:  
   `challenge1b_output.json`


▶ Option 2: Run in Docker

1. Build image:  
   `docker build --platform linux/amd64 -t adobe1b .`

2. Run container:  
   `docker run --rm -v "%cd%:/app" --network none adobe1b`
