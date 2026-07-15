import os
import re
import uuid
import fitz
import chromadb
from sentence_transformers import SentenceTransformer
from pathlib import Path

CHUNK_SIZE = 450
CHUNK_OVERLAP = 80
EMBED_MODEL = "all-MiniLM-L6-v2"
COLLECTION_NAME = "industrial_docs"
EQUIPMENT_PATTERN = re.compile(r'\b[A-Z]{1,3}-\d{2,4}[A-Z]?\b')

_client = None
_collection = None
_embedder = None

def get_chroma_client():
    global _client
    if _client is None:
        use_memory = os.getenv("USE_MEMORY_DB", "false").lower() == "true"
        if use_memory:
            _client = chromadb.Client()
        else:
            _client = chromadb.PersistentClient(path="./chroma_db")
    return _client

def get_collection():
    global _collection
    if _collection is None:
        _collection = get_chroma_client().get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
    return _collection

def get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer(EMBED_MODEL)
    return _embedder

def chunk_text(text):
    chunks = []
    start = 0
    while start < len(text):
        chunk = text[start:start + CHUNK_SIZE].strip()
        if len(chunk) > 30:
            chunks.append(chunk)
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks

def extract_equipment_tags(text):
    return list(set(EQUIPMENT_PATTERN.findall(text)))

def ingest_document(file_path: str) -> dict:
    path = Path(file_path)
    doc_name = path.name
    collection = get_collection()

    existing = collection.get(where={"source": doc_name})
    if existing and existing["ids"]:
        count = len(existing["ids"])
        return {
            "document_name": doc_name,
            "chunks_created": count,
            "entities_found": [],
            "pages_processed": 0,
            "already_existed": True
        }

    try:
        pdf = fitz.open(file_path)
    except Exception as e:
        return {"error": str(e), "document_name": doc_name}

    pages = []
    for i, page in enumerate(pdf, 1):
        text = page.get_text("text").strip()
        if text:
            pages.append((i, text))
    pdf.close()

    if not pages:
        return {"error": "PDF is empty or image-only", "document_name": doc_name}

    chunks, metas, ids, all_text = [], [], [], ""
    for page_num, page_text in pages:
        all_text += " " + page_text
        for i, chunk in enumerate(chunk_text(page_text)):
            chunks.append(chunk)
            metas.append({"source": doc_name, "page": page_num, "chunk_index": i})
            ids.append(f"{doc_name}__p{page_num}__c{i}__{uuid.uuid4().hex[:6]}")

    if not chunks:
        return {"error": "No text chunks extracted", "document_name": doc_name}

    embedder = get_embedder()
    embeddings = embedder.encode(chunks, show_progress_bar=False).tolist()

    for i in range(0, len(chunks), 100):
        collection.add(
            ids=ids[i:i+100],
            documents=chunks[i:i+100],
            metadatas=metas[i:i+100],
            embeddings=embeddings[i:i+100]
        )

    entities = extract_equipment_tags(all_text)
    print(f"Ingested {doc_name}: {len(chunks)} chunks, {len(pages)} pages, entities: {entities}")

    return {
        "document_name": doc_name,
        "chunks_created": len(chunks),
        "entities_found": entities,
        "pages_processed": len(pages),
        "already_existed": False
    }

def get_all_documents():
    try:
        result = get_collection().get(include=["metadatas"])
        if not result or not result["metadatas"]:
            return []
        counts = {}
        for m in result["metadatas"]:
            n = m.get("source", "unknown")
            counts[n] = counts.get(n, 0) + 1
        return [{"name": k, "chunks": v} for k, v in sorted(counts.items())]
    except Exception:
        return []

def delete_document(name: str) -> bool:
    try:
        existing = get_collection().get(where={"source": name})
        if not existing or not existing["ids"]:
            return False
        get_collection().delete(ids=existing["ids"])
        return True
    except Exception:
        return False

def get_collection_stats():
    try:
        result = get_collection().get(include=["metadatas"])
        if not result or not result["metadatas"]:
            return {"total_chunks": 0, "total_documents": 0}
        docs = set(m.get("source") for m in result["metadatas"])
        return {"total_chunks": len(result["metadatas"]), "total_documents": len(docs)}
    except Exception:
        return {"total_chunks": 0, "total_documents": 0}