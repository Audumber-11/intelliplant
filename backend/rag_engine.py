import os
import re
import time
from anthropic import Anthropic
from ingestion import get_collection, get_embedder, EQUIPMENT_PATTERN

SYSTEM_PROMPT = (
    "You are IntelliPlant AI, an expert industrial knowledge assistant. "
    "Engineers and technicians ask you about equipment, safety, maintenance, and procedures. "
    "RULES: "
    "1. Answer ONLY using the document excerpts in the context provided. "
    "2. Always cite the source document name and page number in your answer. "
    "3. For procedures, use numbered steps (1. 2. 3.). "
    "4. If the answer is not in the context, say exactly: "
    "This information is not available in the currently indexed documents. "
    "5. Be precise and technical. Keep answers under 350 words."
)

NO_DOCS_RESPONSE = {
    "answer": (
        "No documents are indexed yet.\n\n"
        "To get started:\n"
        "1. Click the Knowledge Base tab on the left\n"
        "2. Click Load Sample Documents\n"
        "3. Wait for indexing to complete\n"
        "4. Then come back and ask your question"
    ),
    "confidence": 0.0,
    "sources": [],
    "query_time_ms": 0,
    "chunks_searched": 0
}

def query_knowledge_base(question: str) -> dict:
    start = time.time()
    collection = get_collection()
    if collection.count() == 0:
        return NO_DOCS_RESPONSE

    embedder = get_embedder()
    q_embed = embedder.encode([question], show_progress_bar=False).tolist()[0]

    n = min(5, collection.count())
    results = collection.query(
        query_embeddings=[q_embed],
        n_results=n,
        include=["documents", "metadatas", "distances"]
    )

    docs = results["documents"][0] if results["documents"] else []
    metas = results["metadatas"][0] if results["metadatas"] else []
    distances = results["distances"][0] if results["distances"] else []

    if not docs:
        return NO_DOCS_RESPONSE

    sims = [max(0.0, min(1.0, 1.0 - d)) for d in distances]
    confidence = round(sum(sims[:3]) / min(3, len(sims)), 3)

    context_parts = []
    for doc, meta in zip(docs, metas):
        label = f"[Source: {meta.get('source','?')} | Page {meta.get('page','?')}]"
        context_parts.append(f"{label}\n{doc}")
    context = "\n\n---\n\n".join(context_parts)

    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=900,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion: {question}"
        }]
    )

    answer = response.content[0].text
    elapsed_ms = int((time.time() - start) * 1000)

    sources = []
    seen = set()
    for doc, meta in zip(docs, metas):
        key = f"{meta.get('source')}_{meta.get('page')}"
        if key not in seen:
            seen.add(key)
            excerpt = doc[:220].strip()
            if len(doc) > 220:
                excerpt += "..."
            sources.append({
                "document": meta.get("source", "?"),
                "page": meta.get("page", 0),
                "excerpt": excerpt
            })

    return {
        "answer": answer,
        "confidence": confidence,
        "sources": sources,
        "query_time_ms": elapsed_ms,
        "chunks_searched": len(docs)
    }

def get_entity_relationships() -> dict:
    collection = get_collection()
    if collection.count() == 0:
        return {"nodes": [], "edges": []}

    result = collection.get(include=["documents", "metadatas"])
    docs = result.get("documents") or []
    metas = result.get("metadatas") or []

    doc_nodes = {}
    eq_nodes = {}
    edges = []
    seen_edges = set()

    for text, meta in zip(docs, metas):
        name = meta.get("source", "unknown")
        doc_id = "doc__" + re.sub(r'[^a-zA-Z0-9]', '_', name)

        if doc_id not in doc_nodes:
            label = name.replace(".pdf", "").replace("_", " ")
            doc_nodes[doc_id] = {"id": doc_id, "label": label, "type": "document"}

        for tag in set(EQUIPMENT_PATTERN.findall(text)):
            eq_id = f"eq__{tag}"
            if eq_id not in eq_nodes:
                eq_nodes[eq_id] = {"id": eq_id, "label": tag, "type": "equipment"}
            edge_key = f"{doc_id}__{eq_id}"
            if edge_key not in seen_edges:
                seen_edges.add(edge_key)
                edges.append({
                    "id": edge_key,
                    "source": doc_id,
                    "target": eq_id,
                    "label": "CONTAINS"
                })

    nodes = list(doc_nodes.values()) + list(eq_nodes.values())
    return {"nodes": nodes, "edges": edges}