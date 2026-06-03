from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import html
import json
import re
import uuid
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from src.classification.classifier import classify_document
from src.indexing.indexer import get_or_create_index, index_document, search_index
from src.keywords.keyword_loader import load_keywords
from src.processing.extractor import extract_text
from src.storage.document_store import (
    get_all_documents,
    get_document,
    save_uploaded_file,
    search_keyword,
    store_document,
)

KEYWORDS = load_keywords()

KEYWORD_EXAMPLES = KEYWORDS[:8] if KEYWORDS else [
    "security",
    "risk",
    "authentication",
    "encryption",
    "cloud",
]

DEFAULT_CATEGORY_RULES = {
    "Security": ["security", "threat", "breach", "vulnerability", "malware", "attack"],
    "Risk": ["risk", "exposure", "compliance", "governance", "audit"],
    "Authentication": ["authentication", "auth", "login", "password", "credential"],
    "Encryption": ["encryption", "crypto", "ssl", "tls", "cipher"],
    "Cloud": ["cloud", "azure", "aws", "gcp"],
    "Privacy": ["privacy", "personal", "data protection", "gdpr"],
}

BASE_DIR = Path(__file__).resolve().parent
INDEX_DIR = BASE_DIR / "data" / "indexdir"
REQUESTS_FILE = BASE_DIR / "data" / "download_requests.json"

app = FastAPI()
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def build_keyword_map(keywords: List[str]) -> Dict[str, List[str]]:
    categories: Dict[str, List[str]] = {key: [] for key in DEFAULT_CATEGORY_RULES}
    categories["General"] = []

    for keyword_value in keywords:
        normalized = keyword_value.lower()
        matched = False

        for category, tokens in DEFAULT_CATEGORY_RULES.items():
            if any(token in normalized for token in tokens):
                categories[category].append(keyword_value)
                matched = True

        if not matched:
            categories["General"].append(keyword_value)

    return {category: values for category, values in categories.items() if values}


KEYWORD_MAP = build_keyword_map(KEYWORDS) if KEYWORDS else {"Security & Risk": KEYWORD_EXAMPLES}


@app.on_event("startup")
async def startup_event():
    get_or_create_index(INDEX_DIR)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):

    keyword_hint = ", ".join(
        f"<strong>{kw}</strong>" for kw in KEYWORD_EXAMPLES
    )

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "keyword_hint": keyword_hint,
            "keywords": KEYWORDS,
        },
    )


@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    uploaded_files = []
    skipped_files = []

    for file in files:
        try:
            content_bytes = await file.read()
            document_id = str(uuid.uuid4())
            file_path = save_uploaded_file(document_id, file.filename, content_bytes)
            extracted_text = extract_text(file_path).strip()

            if not extracted_text:
                extracted_text = content_bytes.decode(errors="ignore").strip()

            if not extracted_text:
                raise ValueError("No text could be extracted from this file.")

            keyword_scores = {
                keyword: extracted_text.lower().count(keyword.lower())
                for keyword in (KEYWORDS or KEYWORD_EXAMPLES)
            }

            classification = classify_document(extracted_text, KEYWORD_MAP)
            category = classification.get("category", "Uncategorized")

            store_document(
                document_id,
                file.filename,
                extracted_text,
                keyword_scores,
                category=category,
                file_path=file_path,
            )
            index_document(document_id, file.filename, extracted_text, category, INDEX_DIR)
            uploaded_files.append(file.filename)
        except Exception as exc:
            skipped_files.append(f"{file.filename} ({exc})")

    return {
        "uploaded_count": len(uploaded_files),
        "uploaded_files": uploaded_files,
        "skipped_files": skipped_files,
    }


@app.get("/download")
async def download(document_id: str):

    document = get_document(document_id)

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    file_path = document.get("file_path")

    if not file_path or not Path(file_path).exists():
        raise HTTPException(status_code=404, detail="File not available")

    return FileResponse(
        path=file_path,
        filename=document.get("filename", "document"),
        media_type="application/octet-stream",
    )


def save_download_request(document_id: str, keyword: Optional[str] = None, filename: Optional[str] = None):
    REQUESTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if REQUESTS_FILE.exists():
        with REQUESTS_FILE.open("r", encoding="utf-8") as request_file:
            requests = json.load(request_file)
    else:
        requests = []

    requests.append({
        "document_id": document_id,
        "filename": filename or "Unknown",
        "keyword": keyword or "",
        "requested_at": datetime.utcnow().isoformat() + "Z",
        "status": "pending",
    })

    with REQUESTS_FILE.open("w", encoding="utf-8") as request_file:
        json.dump(requests, request_file, indent=2, ensure_ascii=False)


@app.post("/request-download")
async def request_download(request: Request):
    payload = await request.json()
    document_id = payload.get("document_id")
    keyword = payload.get("keyword")

    if not document_id:
        raise HTTPException(status_code=400, detail="Document ID is required")

    document = get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    save_download_request(document_id, keyword, document.get("filename"))
    return {
        "status": "requested",
        "message": "Your download request has been sent to the manager.",
        "document_name": document.get("filename"),
    }

@app.post("/request-bulk-download")
async def request_bulk_download(request: Request):
    payload = await request.json()
    document_ids = payload.get("document_ids", [])
    keyword = payload.get("keyword", "")

    if not document_ids:
        raise HTTPException(status_code=400, detail="No documents selected")

    requested_documents = []

    for document_id in document_ids:
        document = get_document(document_id)

        if document:
            save_download_request(
                document_id,
                keyword,
                document.get("filename")
            )

            requested_documents.append({
                "document_id": document_id,
                "filename": document.get("filename", "Unknown"),
            })

    return {
        "status": "requested",
        "message": f"{len(requested_documents)} document request(s) sent to the manager.",
        "requested_documents": requested_documents,
    }

@app.get("/search")
async def search(keyword: str):
    if not keyword or not keyword.strip():
        raise HTTPException(status_code=400, detail="Keyword cannot be empty")

    results = search_index(keyword, INDEX_DIR)
    if not results:
        return search_keyword(keyword)

    return {
        "keyword": keyword,
        "total_matches": len(results),
        "top_document": results[0] if results else None,
        "all_results": results,
    }


def normalize_document_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def split_sentences(text: str) -> List[str]:
    clean = normalize_document_text(text)
    if not clean:
        return []

    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", clean)
    return [
        sentence.strip()
        for sentence in sentences
        if 40 <= len(sentence.strip()) <= 520
    ]


def meaningful_terms(text: str, limit: int = 18) -> List[str]:
    stop_words = {
        "about", "after", "also", "and", "are", "because", "been", "but", "can",
        "for", "from", "has", "have", "into", "its", "may", "not", "our", "that",
        "the", "their", "there", "these", "this", "those", "was", "were", "will",
        "with", "within", "you", "your",
    }
    words = re.findall(r"[A-Za-z][A-Za-z\-]{3,}", text.lower())
    counts = Counter(word for word in words if word not in stop_words)
    return [word for word, _ in counts.most_common(limit)]


def summarize_text(text: str, category: str = "", max_sentences: int = 5, max_chars: int = 1100) -> str:
    clean = normalize_document_text(text)
    if not clean:
        return "No readable content was found for this document."

    sentences = split_sentences(clean)
    if not sentences:
        return clean[:max_chars].rsplit(" ", 1)[0] + ("..." if len(clean) > max_chars else "")

    important_terms = set(meaningful_terms(clean))
    category_terms = set(DEFAULT_CATEGORY_RULES.get(category, []))
    scored_sentences = []

    for index, sentence in enumerate(sentences):
        sentence_lower = sentence.lower()
        words = re.findall(r"[A-Za-z][A-Za-z\-]{3,}", sentence_lower)
        term_hits = sum(1 for word in words if word in important_terms)
        category_hits = sum(sentence_lower.count(term) for term in category_terms)
        length_score = 1 if 80 <= len(sentence) <= 260 else 0
        position_score = max(0, 3 - index * 0.15)
        score = term_hits + (category_hits * 2) + length_score + position_score
        scored_sentences.append((score, index, sentence))

    selected = sorted(scored_sentences, reverse=True)[:max_sentences]
    selected_in_order = [sentence for _, _, sentence in sorted(selected, key=lambda item: item[1])]

    summary = " ".join(selected_in_order)
    if len(summary) > max_chars:
        summary = summary[:max_chars].rsplit(" ", 1)[0] + "..."

    return summary


def read_document_text(document: Dict) -> str:
    file_path = document.get("file_path")

    if file_path and Path(file_path).exists():
        extracted = extract_text(file_path).strip()
        if extracted:
            return extracted

        suffix = Path(file_path).suffix.lower()
        if suffix in {".txt", ".md", ".html", ".htm"}:
            return Path(file_path).read_text(encoding="utf-8", errors="ignore").strip()

    return (document.get("content") or "").strip()


@app.get("/preview")
async def preview(document_id: str):
    document = get_document(document_id)

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    text = read_document_text(document)
    summary = summarize_text(text, category=document.get("category", ""))

    return {
        "document_id": document_id,
        "filename": document.get("filename", "Unknown"),
        "category": document.get("category", "Uncategorized"),
        "summary": summary,
        "source_character_count": len(normalize_document_text(text)),
    }

@app.get("/documents-count")
async def get_documents_count():

    from src.storage.document_store import get_all_documents

    documents = get_all_documents()

    return {"total_documents": len(documents)}
