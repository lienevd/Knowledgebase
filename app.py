from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import html
import uuid
from pathlib import Path
from typing import Dict, List

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


@app.get("/preview")
async def preview(document_id: str):

    document = get_document(document_id)

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    file_path = document.get("file_path")

    if not file_path or not Path(file_path).exists():
        raise HTTPException(status_code=404, detail="File not available")

    extension = Path(file_path).suffix.lower()

    if extension == ".pdf":
        return FileResponse(
            path=file_path,
            media_type="application/pdf",
            filename=document.get("filename", "document.pdf"),
        )

    if extension == ".txt":
        return FileResponse(
            path=file_path,
            media_type="text/plain",
            filename=document.get("filename", "document.txt"),
        )

    if extension == ".docx":
        try:
            from docx import Document as DocxDocument

            doc = DocxDocument(file_path)

            text_content = "\n\n".join(
                p.text for p in doc.paragraphs if p.text
            )

            return HTMLResponse(
                f"""
                <html>
                    <body>
                        <pre style='white-space: pre-wrap;
                                    font-family: ui-monospace;'>
                            {html.escape(text_content)}
                        </pre>
                    </body>
                </html>
                """
            )

        except Exception:
            raise HTTPException(
                status_code=415,
                detail="Preview not available for this file type",
            )

    raise HTTPException(
        status_code=415,
        detail="Preview not available for this file type",
    )


@app.get("/documents-count")
async def get_documents_count():

    from src.storage.document_store import get_all_documents

    documents = get_all_documents()

    return {"total_documents": len(documents)}