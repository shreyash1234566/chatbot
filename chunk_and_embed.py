import os
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
import faiss
import pickle

# --- Paths ---
html_dir = "mosdac_crawl_all/html"
vector_dir = "vector_store"
os.makedirs(vector_dir, exist_ok=True)

# --- 1. Load & Clean HTML ---
def clean_html_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')
        return soup.get_text(separator="\n", strip=True)
    except Exception as e:
        print(f"⚠️ Error reading {path}: {e}")
        return ""

documents = []

# Load all .html files from subfolder
for file in os.listdir(html_dir):
    if file.endswith(".html"):
        full_path = os.path.join(html_dir, file)
        text = clean_html_file(full_path)
        if text.strip():
            documents.append(text)

# Also include optional .txt file if present
txt_path = os.path.join("mosdac_crawl_all", "main_page_content.txt")
if os.path.exists(txt_path):
    with open(txt_path, "r", encoding="utf-8") as f:
        text = f.read().strip()
        if text:
            documents.append(text)

print(f"📄 Total documents loaded: {len(documents)}")

# --- 2. Chunk Text ---
def chunk_text(text, max_len=500):
    words = text.split()
    return [" ".join(words[i:i + max_len]) for i in range(0, len(words), max_len)]

chunks = []
for doc in documents:
    chunks.extend(chunk_text(doc))

print(f"✂️ Total text chunks generated: {len(chunks)}")

# --- Early Exit if No Data ---
if not chunks:
    print("❌ No chunks found. Check if HTML files have readable text.")
    exit()

# --- 3. Load Embedding Model ---
print("🔄 Loading embedding model...")
model = SentenceTransformer("all-MiniLM-L6-v2")

print("🧠 Embedding chunks...")
embeddings = model.encode(chunks)

if len(embeddings) == 0:
    print("❌ No embeddings created. Please check your text content.")
    exit()

# --- 4. Save FAISS Vector Store ---
dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(embeddings)

faiss.write_index(index, os.path.join(vector_dir, "mosdac_index.faiss"))
with open(os.path.join(vector_dir, "mosdac_chunks.pkl"), "wb") as f:
    pickle.dump(chunks, f)

print("✅ All embeddings saved in FAISS.")
print(f"📂 Vector store created at: {vector_dir}/")
