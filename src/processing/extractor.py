import re
from pathlib import Path
from html import unescape

import fitz


def extract_text(file_path: str) -> str:
    file_path = Path(file_path)
    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        text = ""
        with fitz.open(str(file_path)) as doc:
            for page in doc:
                text += page.get_text()
        return text

    if suffix == ".txt":
        return file_path.read_text(encoding="utf-8", errors="ignore")

    if suffix == ".docx":
        try:
            from docx import Document as DocxDocument

            doc = DocxDocument(str(file_path))
            return "\n".join(p.text for p in doc.paragraphs if p.text)
        except Exception:
            return ""

    if suffix in {".html", ".htm"}:
        raw_html = file_path.read_text(encoding="utf-8", errors="ignore")
        text = re.sub(r"<script[\s\S]*?<\/script>", " ", raw_html, flags=re.IGNORECASE)
        text = re.sub(r"<style[\s\S]*?<\/style>", " ", text, flags=re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", text)
        return unescape(text)

    return ""
