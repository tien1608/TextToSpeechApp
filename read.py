import fitz
from docx import Document
import os

def read_pdf(path):
    text = ""
    with fitz.open(path) as doc:
        for page in doc:
            text += page.get_text()
    return text.strip()

def read_docx(path):
    doc = Document(path)
    return " ".join(p.text.strip() for p in doc.paragraphs if p.text.strip())

def split_text(text, chunk_words):
    words = text.split()
    return [" ".join(words[i:i+chunk_words]) for i in range(0, len(words), chunk_words)]

def save_chunks(chunks, folder):
    os.makedirs(folder, exist_ok=True)
    for i, chunk in enumerate(chunks):
        with open(os.path.join(folder, f"text_{i:03}.txt"), "w", encoding="utf-8") as f:
            f.write(chunk)

def load_chunks(folder):
    chunks = []
    i = 0
    while True:
        path = os.path.join(folder, f"text_{i:03}.txt")
        if not os.path.exists(path):
            break
        with open(path, "r", encoding="utf-8") as f:
            chunks.append(f.read())
        i += 1
    return chunks