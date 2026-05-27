import json
import os
from pathlib import Path
from typing import Dict, List, Optional

STORAGE_FILE = "data/documents.json"

def ensure_storage_dir():
    """Ensure storage directory exists"""
    os.makedirs(os.path.dirname(STORAGE_FILE), exist_ok=True)

def load_documents() -> Dict:
    """Load all stored documents from storage file"""
    ensure_storage_dir()
    if os.path.exists(STORAGE_FILE):
        with open(STORAGE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_documents(documents: Dict):
    """Save documents to storage file"""
    ensure_storage_dir()
    with open(STORAGE_FILE, 'w', encoding='utf-8') as f:
        json.dump(documents, f, indent=2, ensure_ascii=False)

def store_document(document_id: str, filename: str, content: str, keyword_scores: Dict[str, int]):
    """Store a new document"""
    documents = load_documents()
    documents[document_id] = {
        "filename": filename,
        "content": content,
        "keyword_scores": keyword_scores
    }
    save_documents(documents)

def get_document(document_id: str) -> Optional[Dict]:
    """Retrieve a specific document"""
    documents = load_documents()
    return documents.get(document_id)

def get_all_documents() -> Dict:
    """Get all stored documents"""
    return load_documents()

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
    """Delete a document from storage"""
    documents = load_documents()
    if document_id in documents:
        del documents[document_id]
        save_documents(documents)
        return True
    return False

def clear_all_documents():
    """Clear all stored documents"""
    if os.path.exists(STORAGE_FILE):
        os.remove(STORAGE_FILE)
