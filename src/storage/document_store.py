import json
import os
from pathlib import Path
from typing import Dict, List, Optional

STORAGE_FILE = Path("data") / "documents.json"
UPLOAD_DIR = Path("data") / "uploads"

def ensure_storage_dir():
    """Ensure storage directory exists"""
    STORAGE_FILE.parent.mkdir(parents=True, exist_ok=True)


def ensure_upload_dir():
    """Ensure upload directory exists"""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def load_documents() -> Dict:
    """Load all stored documents from storage file"""
    ensure_storage_dir()
    if STORAGE_FILE.exists():
        with open(STORAGE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_documents(documents: Dict):
    """Save documents to storage file"""
    ensure_storage_dir()
    with open(STORAGE_FILE, 'w', encoding='utf-8') as f:
        json.dump(documents, f, indent=2, ensure_ascii=False)

def save_uploaded_file(document_id: str, filename: str, file_bytes: bytes) -> str:
    """Save raw uploaded file bytes to the uploads folder and return the path."""
    ensure_upload_dir()
    safe_name = f"{document_id}_{Path(filename).name}"
    upload_path = UPLOAD_DIR / safe_name
    with open(upload_path, "wb") as out_file:
        out_file.write(file_bytes)
    return str(upload_path)


def resolve_file_path(document_id: str, filename: str, file_path: Optional[str] = None) -> Optional[str]:
    """Resolve the document file path, falling back to the uploads folder if needed."""
    if file_path:
        if Path(file_path).exists():
            return file_path

    fallback = UPLOAD_DIR / f"{document_id}_{Path(filename).name}"
    if fallback.exists():
        return str(fallback)

    return None


def store_document(
    document_id: str,
    filename: str,
    content: str,
    keyword_scores: Dict[str, int],
    category: str = "Uncategorized",
    file_path: Optional[str] = None,
    category_scores: Optional[Dict[str, int]] = None,
    matched_keywords: Optional[Dict[str, Dict[str, int]]] = None,
    index_entries: Optional[List[Dict[str, str]]] = None,
    summary_keywords: Optional[List[str]] = None,
):
    """Store a new document"""
    documents = load_documents()
    resolved_path = resolve_file_path(document_id, filename, file_path)
    documents[document_id] = {
        "filename": filename,
        "content": content,
        "keyword_scores": keyword_scores,
        "category": category,
        "file_path": resolved_path,
        "category_scores": category_scores or {},
        "matched_keywords": matched_keywords or {},
        "index_entries": index_entries or [],
        "index_results": index_entries or [],
        "summary_keywords": summary_keywords or [],
    }
    save_documents(documents)


def get_document(document_id: str) -> Optional[Dict]:
    """Retrieve a specific document"""
    documents = load_documents()
    document = documents.get(document_id)
    if document and document.get("file_path") is None and document.get("filename"):
        resolved_path = resolve_file_path(document_id, document["filename"], None)
        if resolved_path:
            document["file_path"] = resolved_path
            documents[document_id] = document
            save_documents(documents)
    return document

def get_all_documents() -> Dict:
    """Get all stored documents"""
    documents = load_documents()
    active_documents = {
        document_id: document
        for document_id, document in documents.items()
        if not is_missing_uploaded_file(document)
    }

    if len(active_documents) != len(documents):
        save_documents(active_documents)

    return active_documents


def is_missing_uploaded_file(document: Dict) -> bool:
    """Return True when a stored upload record points at a file that no longer exists."""
    file_path = document.get("file_path")
    return bool(file_path) and not Path(file_path).exists()


def delete_uploaded_file(document: Dict) -> bool:
    """Delete the uploaded source file if it is still present in the upload folder."""
    file_path = document.get("file_path")
    candidate_paths = []

    if file_path:
        candidate_paths.append(Path(file_path))

    filename = document.get("filename")
    document_id = document.get("document_id")
    if document_id and filename:
        candidate_paths.append(UPLOAD_DIR / f"{document_id}_{Path(filename).name}")

    upload_root = UPLOAD_DIR.resolve()
    deleted = False

    for path in candidate_paths:
        try:
            resolved_path = path.resolve()
            if resolved_path.exists() and upload_root in resolved_path.parents:
                resolved_path.unlink()
                deleted = True
        except OSError:
            continue

    return deleted

def search_keyword(keyword: str) -> Dict:
    """
    Search for a keyword across all documents.
    Returns the document with highest keyword count and ranking of all documents.
    """
    documents = load_documents()
    results = []
    
    keyword_lower = keyword.lower()
    
    for doc_id, doc_data in documents.items():
        content = doc_data.get("content", "").lower()
        count = content.count(keyword_lower)
        
        if count > 0:
            results.append({
                "document_id": doc_id,
                "filename": doc_data.get("filename", "Unknown"),
                "keyword_count": count,
                "category": doc_data.get("category", "Uncategorized"),
                "context": extract_context(doc_data.get("content", ""), keyword_lower)
            })
    
    # Sort by keyword count (descending)
    results.sort(key=lambda x: x["keyword_count"], reverse=True)
    
    if results:
        return {
            "keyword": keyword,
            "total_matches": len(results),
            "top_document": results[0],
            "all_results": results
        }
    
    return {
        "keyword": keyword,
        "total_matches": 0,
        "top_document": None,
        "all_results": []
    }

def extract_context(content: str, keyword: str, context_length: int = 100) -> str:
    """Extract context around the first occurrence of the keyword"""
    idx = content.find(keyword)
    if idx == -1:
        return ""
    
    start = max(0, idx - context_length)
    end = min(len(content), idx + len(keyword) + context_length)
    context = content[start:end].strip()
    
    # Add ellipsis if not at start/end
    if start > 0:
        context = "..." + context
    if end < len(content):
        context = context + "..."
    
    return context

def delete_document(document_id: str) -> bool:
    """Delete a document from storage and remove its uploaded file when possible."""
    documents = load_documents()
    if document_id in documents:
        document = documents[document_id]
        document["document_id"] = document_id
        delete_uploaded_file(document)
        del documents[document_id]
        save_documents(documents)
        return True
    return False

def clear_all_documents():
    """Clear all stored documents"""
    if os.path.exists(STORAGE_FILE):
        os.remove(STORAGE_FILE)
