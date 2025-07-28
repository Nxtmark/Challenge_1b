import os
import json
import fitz
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from concurrent.futures import ProcessPoolExecutor
import subprocess

vectorizer = TfidfVectorizer()

def translate_with_apertium(text, src_lang="ja", tgt_lang="en"):
    try:
        result = subprocess.run(
            ["apertium", f"{src_lang}-{tgt_lang}"],
            input=text,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return result.stdout.strip()
    except:
        return text

def translate_if_needed(text):
    if any("\u3040" <= ch <= "\u30ff" for ch in text):
        return translate_with_apertium(text)
    return text

def extract_blocks(pdf_path):
    doc = fitz.open(pdf_path)
    blocks = []
    for i, page in enumerate(doc, start=1):
        for block in page.get_text("blocks"):
            text = block[4].strip()
            if len(text) > 100:
                translated_text = translate_if_needed(text)
                blocks.append({
                    "text": translated_text,
                    "page_number": i,
                    "document": os.path.basename(pdf_path)
                })
    return blocks

def deduplicate_blocks(blocks):
    texts = [b["text"] for b in blocks]
    tfidf_matrix = vectorizer.fit_transform(texts)
    seen = set()
    unique = []
    for i in range(len(texts)):
        if i in seen:
            continue
        unique.append(blocks[i])
        for j in range(i + 1, len(texts)):
            if cosine_similarity(tfidf_matrix[i], tfidf_matrix[j])[0][0] > 0.8:
                seen.add(j)
    return unique

def rank_blocks(blocks, query):
    texts = [b["text"] for b in blocks]
    tfidf_matrix = vectorizer.fit_transform(texts + [query])
    query_vec = tfidf_matrix[-1]
    scores = cosine_similarity(tfidf_matrix[:-1], query_vec)
    ranked = sorted(zip(blocks, scores), key=lambda x: -x[1][0])
    return [x[0] for x in ranked[:2]]

def extract_title(text):
    first_line = text.strip().split("\n")[0]
    return first_line[:80] + "..." if len(first_line) > 80 else first_line

def extract_and_rank(pdf_path, query):
    blocks = extract_blocks(pdf_path)
    blocks = deduplicate_blocks(blocks)
    return rank_blocks(blocks, query)

def analyze_documents(input_data, pdf_dir):
    persona = input_data["persona"]["role"]
    job = input_data["job_to_be_done"]["task"]
    files = [doc["filename"] for doc in input_data["documents"]]
    result = {
        "metadata": {
            "persona": persona,
            "job_to_be_done": job,
            "input_documents": files,
            "timestamp": str(datetime.now())
        },
        "extracted_sections": [],
        "subsection_analysis": []
    }
    pdf_paths = [os.path.join(pdf_dir, f) for f in files]
    query = f"{persona} needs to {job}"
    with ProcessPoolExecutor() as executor:
        results = executor.map(extract_and_rank, pdf_paths, [query] * len(pdf_paths))
    top_blocks = [b for r in results for b in r]
    top_blocks.sort(key=lambda b: -len(b["text"]))
    for rank, block in enumerate(top_blocks[:10], 1):
        result["extracted_sections"].append({
            "document": block["document"],
            "page_number": block["page_number"],
            "section_title": extract_title(block["text"]),
            "importance_rank": rank
        })
        result["subsection_analysis"].append({
            "document": block["document"],
            "page_number": block["page_number"],
            "refined_text": block["text"]
        })
    return result

def run_all_collections():
    base_dir = "."
    for folder in os.listdir(base_dir):
        folder_path = os.path.join(base_dir, folder)
        if os.path.isdir(folder_path):
            input_file = os.path.join(folder_path, "challenge1b_input.json")
            pdf_dir = os.path.join(folder_path, "PDFs")
            if os.path.exists(input_file) and os.path.isdir(pdf_dir):
                try:
                    with open(input_file, "r", encoding="utf-8") as f:
                        input_data = json.load(f)
                    missing_pdfs = [
                        doc["filename"] for doc in input_data["documents"]
                        if not os.path.exists(os.path.join(pdf_dir, doc["filename"]))
                    ]
                    if missing_pdfs:
                        print(f"[!] Missing PDFs in {folder}: {missing_pdfs}")
                        continue
                    output = analyze_documents(input_data, pdf_dir)
                    output_file = os.path.join(folder_path, "challenge1b_output.json")
                    with open(output_file, "w", encoding="utf-8") as out_f:
                        json.dump(output, out_f, indent=2, ensure_ascii=False)
                    print(f"[✓] Processed: {folder}")
                except Exception as e:
                    print(f"[!] Error processing {folder}: {e}")

if __name__ == "__main__":
    run_all_collections()
