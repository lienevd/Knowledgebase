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
from src.indexing.indexer import delete_indexed_document, get_or_create_index, index_document
from src.keywords.keyword_loader import (
    load_keyword_categories,
    load_keywords,
    normalize_category,
    normalize_keyword,
)
from src.processing.extractor import extract_text
from src.storage.document_store import (
    delete_document as delete_stored_document,
    get_all_documents,
    get_document,
    save_uploaded_file,
    store_document,
)

KEYWORDS = load_keywords()
KEYWORD_MAP = load_keyword_categories()

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


def display_category(category: Optional[str]) -> str:
    if not category or category == "Uncategorized":
        return "Uncategorized"

    return normalize_category(category)

BASE_DIR = Path(__file__).resolve().parent
INDEX_DIR = BASE_DIR / "data" / "indexdir"
REQUESTS_FILE = BASE_DIR / "data" / "download_requests.json"
SEARCH_TEXT_CACHE_FILE = BASE_DIR / "data" / "search_text_cache.json"
SEARCH_TEXT_CACHE: Optional[Dict[str, str]] = None
SEARCH_TEXT_CACHE_CHANGED = False

app = FastAPI()
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


if not KEYWORD_MAP:
    KEYWORD_MAP = {"Security & Risk": KEYWORD_EXAMPLES}

KEYWORD_TO_CATEGORIES: Dict[str, List[str]] = {}
for category_name, category_keywords in KEYWORD_MAP.items():
    for keyword_value in category_keywords:
        KEYWORD_TO_CATEGORIES.setdefault(normalize_keyword(keyword_value), []).append(category_name)


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

            classification = classify_document(extracted_text, KEYWORD_MAP)
            category = classification.get("category", "Uncategorized")
            category_keywords = KEYWORD_MAP.get(category, [])
            extracted_text_lower = extracted_text.lower()
            keyword_scores = {}
            for keyword in category_keywords:
                count = extracted_text_lower.count(keyword.lower())
                if count > 0:
                    keyword_scores[keyword] = count
            index_entries = build_index_entries(
                file.filename,
                extracted_text,
                category,
                keyword_scores,
            )
            summary_keywords = first_summary_keywords(keyword_scores)

            store_document(
                document_id,
                file.filename,
                extracted_text,
                keyword_scores,
                category=category,
                file_path=file_path,
                category_scores=classification.get("scores", {}),
                matched_keywords=classification.get("matched_keywords", {}),
                index_entries=index_entries,
                summary_keywords=summary_keywords,
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


def count_keyword_occurrences(text: str, keyword: str) -> int:
    clean_keyword = keyword.strip().lower()
    if not clean_keyword:
        return 0

    return (text or "").lower().count(clean_keyword)


def extract_keyword_context(text: str, keyword: str, context_length: int = 150) -> str:
    content = text or ""
    keyword_lower = keyword.strip().lower()
    match_index = content.lower().find(keyword_lower)

    if match_index == -1:
        return ""

    start = max(0, match_index - context_length)
    end = min(len(content), match_index + len(keyword_lower) + context_length)
    context = normalize_document_text(content[start:end])

    if start > 0:
        context = "..." + context
    if end < len(content):
        context = context + "..."

    return context


def extract_keyword_snippets(
    text: str,
    keyword: str,
    context_length: int = 32,
    max_snippets: int = 25,
) -> List[str]:
    clean_keyword = keyword.strip()
    if not clean_keyword:
        return []

    snippets = []
    pattern = re.compile(re.escape(clean_keyword), re.IGNORECASE)

    for match in pattern.finditer(text or ""):
        start = max(0, match.start() - context_length)
        end = min(len(text), match.end() + context_length)
        snippet = normalize_document_text((text or "")[start:end])

        if start > 0:
            snippet = "..." + snippet
        if end < len(text or ""):
            snippet = snippet + "..."

        snippets.append(snippet)
        if len(snippets) >= max_snippets:
            break

    return snippets


def build_index_entries(
    filename: str,
    text: str,
    category: str,
    keyword_scores: Dict[str, int],
) -> List[Dict[str, str]]:
    entries = []

    for keyword in keyword_scores:
        for snippet in extract_keyword_snippets(text, keyword):
            entries.append({
                "Filename": filename,
                "Keyword": keyword,
                "Category": category,
                "Snippet": snippet,
            })

    return entries


def first_summary_keywords(keyword_scores: Dict[str, int], limit: int = 10) -> List[str]:
    return [
        keyword
        for keyword, count in sorted(
            keyword_scores.items(),
            key=lambda item: (-item[1], item[0].lower()),
        )
        if count > 0
    ][:limit]


def is_searchable_stored_text(text: str) -> bool:
    if not text or not text.strip():
        return False

    sample = text[:2000]
    if sample.lstrip().startswith("%PDF-"):
        return False

    control_chars = sum(
        1 for char in sample
        if ord(char) < 32 and char not in "\r\n\t"
    )
    return control_chars / max(len(sample), 1) < 0.02


def load_search_text_cache() -> Dict[str, str]:
    global SEARCH_TEXT_CACHE

    if SEARCH_TEXT_CACHE is not None:
        return SEARCH_TEXT_CACHE

    if SEARCH_TEXT_CACHE_FILE.exists():
        with SEARCH_TEXT_CACHE_FILE.open("r", encoding="utf-8") as cache_file:
            SEARCH_TEXT_CACHE = json.load(cache_file)
    else:
        SEARCH_TEXT_CACHE = {}

    return SEARCH_TEXT_CACHE


def save_search_text_cache() -> None:
    global SEARCH_TEXT_CACHE_CHANGED

    if not SEARCH_TEXT_CACHE_CHANGED:
        return

    SEARCH_TEXT_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with SEARCH_TEXT_CACHE_FILE.open("w", encoding="utf-8") as cache_file:
        json.dump(load_search_text_cache(), cache_file, ensure_ascii=False)
    SEARCH_TEXT_CACHE_CHANGED = False


def document_cache_key(document: Dict) -> Optional[str]:
    file_path = document.get("file_path")
    if not file_path:
        return None

    path = Path(file_path)
    if not path.exists():
        return None

    stat = path.stat()
    return f"{path.resolve()}|{stat.st_size}|{stat.st_mtime_ns}"


def get_searchable_document_text(document: Dict) -> str:
    global SEARCH_TEXT_CACHE_CHANGED

    stored_text = document.get("content") or ""
    if is_searchable_stored_text(stored_text):
        return stored_text

    cache_key = document_cache_key(document)
    cache = load_search_text_cache()
    if cache_key and cache_key in cache:
        return cache[cache_key]

    extracted_text = read_document_text(document)
    if cache_key and is_searchable_stored_text(extracted_text):
        cache[cache_key] = extracted_text
        SEARCH_TEXT_CACHE_CHANGED = True

    return extracted_text


def sort_results_by_keyword_count(results: List[Dict]) -> List[Dict]:
    return sorted(
        results,
        key=lambda item: (-item["keyword_count"], item["filename"].lower()),
    )


def categories_for_search_keyword(keyword: str) -> List[str]:
    return KEYWORD_TO_CATEGORIES.get(normalize_keyword(keyword), [])


def indexed_keyword_result(document_id: str, document: Dict, keyword: str) -> Optional[Dict]:
    normalized_query = normalize_keyword(keyword)
    stored_entries = document.get("index_results") or document.get("index_entries", [])
    entries = [
        entry
        for entry in stored_entries
        if normalize_keyword(entry.get("Keyword") or entry.get("keyword", "")) == normalized_query
    ]

    if not entries:
        return None

    keyword_scores = document.get("keyword_scores", {})
    indexed_keyword = entries[0].get("Keyword") or entries[0].get("keyword")
    count = keyword_scores.get(indexed_keyword, len(entries))

    return {
        "document_id": document_id,
        "filename": document.get("filename", "Unknown"),
        "keyword_count": count,
        "category": display_category(document.get("category")),
        "context": entries[0].get("Snippet") or entries[0].get("snippet", ""),
    }


def search_documents_by_keyword(keyword: str, limit: int = 10) -> Dict:
    results = []
    target_categories = categories_for_search_keyword(keyword)

    for document_id, document in get_all_documents().items():
        document_category = document.get("category")
        if (
            target_categories
            and document_category in KEYWORD_MAP
            and document_category not in target_categories
        ):
            continue

        indexed_result = indexed_keyword_result(document_id, document, keyword)
        if indexed_result:
            results.append(indexed_result)
            continue

        text = get_searchable_document_text(document)
        count = count_keyword_occurrences(text, keyword)

        if count <= 0:
            continue

        results.append({
            "document_id": document_id,
            "filename": document.get("filename", "Unknown"),
            "keyword_count": count,
            "category": display_category(document.get("category")),
            "context": extract_keyword_context(text, keyword),
        })

    results = sort_results_by_keyword_count(results)
    save_search_text_cache()

    limited_results = results[:limit]

    return {
        "keyword": keyword,
        "total_matches": len(results),
        "displayed_matches": len(limited_results),
        "result_limit": limit,
        "searched_categories": target_categories,
        "top_document": limited_results[0] if limited_results else None,
        "all_results": limited_results,
    }


@app.get("/search")
async def search(keyword: str):
    if not keyword or not keyword.strip():
        raise HTTPException(status_code=400, detail="Keyword cannot be empty")

    return search_documents_by_keyword(keyword.strip())


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


def summarize_text(
    text: str,
    category: str = "",
    priority_keywords: Optional[List[str]] = None,
    max_chars: int = 520,
) -> str:
    clean = normalize_document_text(text)
    if not clean:
        return "No readable content was found for this document."

    sentences = split_sentences(clean)
    if not sentences:
        return clean[:max_chars].rsplit(" ", 1)[0] + ("..." if len(clean) > max_chars else "")

    priority_terms = [
        keyword.lower()
        for keyword in (priority_keywords or [])
        if keyword and keyword.strip()
    ][:10]
    important_terms = set(priority_terms or meaningful_terms(clean))
    category_terms = set(KEYWORD_MAP.get(category, DEFAULT_CATEGORY_RULES.get(category, [])))
    scored_sentences = []

    for index, sentence in enumerate(sentences):
        sentence_lower = sentence.lower()
        words = re.findall(r"[A-Za-z][A-Za-z\-]{3,}", sentence_lower)
        term_hits = sum(1 for word in words if word in important_terms)
        priority_hits = sum(sentence_lower.count(term) for term in priority_terms)
        category_hits = sum(sentence_lower.count(term) for term in category_terms)
        length_score = 1 if 80 <= len(sentence) <= 260 else 0
        position_score = max(0, 3 - index * 0.15)
        score = (priority_hits * 4) + term_hits + (category_hits * 2) + length_score + position_score
        scored_sentences.append((score, index, sentence))

    _, _, summary = max(scored_sentences, key=lambda item: (item[0], -item[1]))

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
    summary_keywords = document.get("summary_keywords") or first_summary_keywords(
        document.get("keyword_scores", {})
    )
    summary = summarize_text(
        text,
        category=document.get("category", ""),
        priority_keywords=summary_keywords,
    )

    return {
        "document_id": document_id,
        "filename": document.get("filename", "Unknown"),
        "category": display_category(document.get("category")),
        "summary": summary,
        "summary_keywords": summary_keywords,
        "source_character_count": len(normalize_document_text(text)),
    }

@app.get("/documents-count")
async def get_documents_count():

    from src.storage.document_store import get_all_documents

    documents = get_all_documents()

    return {"total_documents": len(documents)}


@app.get("/documents")
async def list_documents():
    documents = get_all_documents()
    document_list = [
        {
            "document_id": document_id,
            "title": document.get("filename", "Untitled document"),
            "category": display_category(document.get("category")),
        }
        for document_id, document in documents.items()
    ]

    document_list.sort(key=lambda item: item["title"].lower())

    return {
        "total_documents": len(document_list),
        "documents": document_list,
    }


@app.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    document = get_document(document_id)

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    deleted = delete_stored_document(document_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")

    delete_indexed_document(document_id, INDEX_DIR)

    return {
        "status": "deleted",
        "message": "Document deleted.",
        "document_id": document_id,
        "filename": document.get("filename", "Unknown"),
    }
