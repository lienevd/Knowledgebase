from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import html
import uuid
from pathlib import Path
from typing import List

from src.storage.document_store import (
    store_document,
    search_keyword,
    save_uploaded_file,
    get_document,
)

from src.keywords.keyword_loader import load_keywords

KEYWORDS = load_keywords()

KEYWORD_EXAMPLES = (
    KEYWORDS[:8]
    if KEYWORDS
    else ["security", "risk", "authentication", "encryption", "cloud"]
)

app = FastAPI()

# Static + templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


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

            text = content_bytes.decode(errors="ignore")

            keywords = (
                KEYWORDS
                if KEYWORDS
                else [
                    "security",
                    "risk",
                    "authentication",
                    "encryption",
                    "cloud",
                ]
            )

            scores = {}

            for keyword in keywords:
                scores[keyword] = text.lower().count(keyword)

            file_path = save_uploaded_file(
                document_id,
                file.filename,
                content_bytes,
            )

            store_document(
                document_id,
                file.filename,
                text,
                scores,
                file_path=file_path,
            )

            uploaded_files.append(file.filename)

        except Exception:
            skipped_files.append(f"{file.filename} (error)")

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

    if not keyword or len(keyword.strip()) == 0:
        return {"error": "Keyword cannot be empty"}

    results = search_keyword(keyword)

    return results


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