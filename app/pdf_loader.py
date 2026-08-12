import os
from pypdf import PdfReader

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def load_all_pdfs():
    documents = []

    for root, dirs, files in os.walk(DATA_DIR):
        for filename in files:
            if filename.lower().endswith(".pdf"):
                filepath = os.path.join(root, filename)
                text = extract_text_from_pdf(filepath)
                relative_path = os.path.relpath(filepath, DATA_DIR)
                documents.append({
                    "source": relative_path,
                    "text": text
                })

    return documents


def extract_text_from_pdf(filepath):
    reader = PdfReader(filepath)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text


if __name__ == "__main__":
    docs = load_all_pdfs()
    print(f"Loaded {len(docs)} PDF files.\n")
    for doc in docs[:3]:
        print(f"Source: {doc['source']}")
        print(f"Preview: {doc['text'][:200]}...")
        print("---")