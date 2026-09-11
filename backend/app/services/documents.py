import io
import math
import re
from collections import Counter
from dataclasses import dataclass, asdict
from uuid import uuid4

from pypdf import PdfReader


@dataclass
class DocumentChunk:
    document_id: str
    filename: str
    mrn: str
    page: int
    chunk_index: int
    text: str


DOCUMENTS: dict[str, list[dict]] = {}
CHUNKS: dict[str, list[DocumentChunk]] = {}


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _chunk_text(text: str, size: int = 900, overlap: int = 150) -> list[str]:
    text = _clean(text)
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + size)
        chunk = text[start:end]
        if end < len(text):
            boundary = max(chunk.rfind(". "), chunk.rfind("; "), chunk.rfind(" "))
            if boundary > size * 0.55:
                end = start + boundary + 1
                chunk = text[start:end]
        chunks.append(chunk.strip())
        if end >= len(text):
            break
        start = max(start + 1, end - overlap)
    return chunks


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _vector(text: str) -> Counter:
    return Counter(t for t in _tokens(text) if len(t) > 2)


def _cosine(a: Counter, b: Counter) -> float:
    if not a or not b:
        return 0.0
    dot = sum(v * b.get(k, 0) for k, v in a.items())
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0


def ingest_pdf(mrn: str, filename: str, payload: bytes) -> dict:
    reader = PdfReader(io.BytesIO(payload))
    document_id = str(uuid4())
    doc_chunks: list[DocumentChunk] = []
    extracted_pages = 0

    for page_no, page in enumerate(reader.pages, start=1):
        text = _clean(page.extract_text() or "")
        if not text:
            continue
        extracted_pages += 1
        for index, chunk in enumerate(_chunk_text(text)):
            doc_chunks.append(DocumentChunk(document_id, filename, mrn, page_no, index, chunk))

    if not doc_chunks:
        raise ValueError("No readable text was found in this PDF. Scanned/image-only PDFs need OCR, which is not enabled in this demo.")

    metadata = {
        "document_id": document_id,
        "filename": filename,
        "mrn": mrn,
        "pages": len(reader.pages),
        "text_pages": extracted_pages,
        "chunks": len(doc_chunks),
    }
    DOCUMENTS.setdefault(mrn, []).append(metadata)
    CHUNKS.setdefault(mrn, []).extend(doc_chunks)
    return metadata


def list_documents(mrn: str) -> list[dict]:
    return DOCUMENTS.get(mrn, [])


def has_documents(mrn: str) -> bool:
    return bool(CHUNKS.get(mrn))


def retrieve_document_chunks(mrn: str, question: str, k: int = 5) -> list[dict]:
    query_vec = _vector(question)
    scored = []
    for chunk in CHUNKS.get(mrn, []):
        score = _cosine(query_vec, _vector(chunk.text))
        scored.append((score, chunk))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [
        {**asdict(chunk), "score": round(score, 4)}
        for score, chunk in scored[:k]
        if score > 0 or not query_vec
    ]


def _best_sentences(question: str, hits: list[dict], limit: int = 4):
    query = set(_tokens(question))
    ranked = []
    for hit in hits:
        for sentence in re.split(r"(?<=[.!?])\s+", hit["text"]):
            sentence = sentence.strip()
            if len(sentence) < 20:
                continue
            overlap = len(query & set(_tokens(sentence)))
            ranked.append((overlap + float(hit.get("score", 0)), sentence, hit))
    ranked.sort(key=lambda x: x[0], reverse=True)
    selected = []
    seen = set()
    for item in ranked:
        key = item[1].lower()
        if key in seen:
            continue
        seen.add(key)
        selected.append(item)
        if len(selected) >= limit:
            break
    return selected


def answer_from_documents(mrn: str, question: str) -> dict:
    hits = retrieve_document_chunks(mrn, question, k=6)
    if not hits:
        return {"answer": "I could not find relevant text in the uploaded PDFs for that question.", "sources": []}

    chosen = _best_sentences(question, hits)
    if not chosen:
        chosen = [(hit.get("score", 0), hit["text"][:350], hit) for hit in hits[:3]]

    answer_lines = [sentence for _, sentence, _ in chosen]
    sources = []
    source_keys = set()
    for _, _, hit in chosen:
        key = (hit["filename"], hit["page"])
        if key not in source_keys:
            source_keys.add(key)
            sources.append({"filename": hit["filename"], "page": hit["page"], "score": hit.get("score", 0)})

    return {"answer": " ".join(answer_lines), "sources": sources}
