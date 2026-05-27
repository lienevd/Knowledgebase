from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
import uuid

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <html>
        <head>
            <title>IBC Document Intelligence</title>
        </head>
        <body>
            <h1>IBC Document Intelligence Platform</h1>

            <form action="/upload" enctype="multipart/form-data" method="post">
                <input name="file" type="file">
                <input type="submit">
            </form>
        </body>
    </html>
    """

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    content = await file.read()

    document_id = str(uuid.uuid4())

    text = content.decode(errors="ignore")

    keywords = [
        "security",
        "risk",
        "authentication",
        "encryption",
        "cloud"
    ]

    scores = {}

    for keyword in keywords:
        scores[keyword] = text.lower().count(keyword)

    return {
        "document_id": document_id,
        "filename": file.filename,
        "keyword_scores": scores
    }