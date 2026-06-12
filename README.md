
# IBC Amsterdam – Intelligent Document Classification System

## Overview
This project implements a secure document intelligence platform for IBC Amsterdam consultants.

The platform supports:
- Intelligent document classification
- Multi-format document processing
- Knowledge indexing and search
- Keyword-driven categorization
- Unique document identifiers
- Contextual snippet extraction

## Completed Epics

### Epic 1 – Intelligent Document Classification System
Business Goal:
Automatically categorize and organize documents based on content analysis.

Features:
- Keyword-based document classification
- Weighted keyword counting
- Multi-category assignment
- Confidence scoring
- UUID generation

### Epic 2 – Multi-Format Document Processing
Business Goal:
Enable comprehensive content extraction from various document types.

Supported formats:
- PDF
- DOCX
- TXT
- HTML

Features:
- Text extraction
- Metadata extraction
- OCR-ready architecture
- Content normalization

### Epic 3 – Knowledge Management & Indexing
Business Goal:
Create searchable indexes of document content with contextual snippets.

Features:
- Full-text indexing
- Snippet generation
- Search API
- Document metadata storage
- Category filtering

---

## Suggested Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python + FastAPI |
| Search | Whoosh / Elasticsearch |
| Document Parsing | PyMuPDF, python-docx |
| Database | SQLite/PostgreSQL |
| Frontend | React (optional) |
| Deployment | Docker |

---

## Suggested Repository Structure

```text
ibc-document-intelligence/
│
├── src/
│   ├── classification/
│   ├── processing/
│   ├── indexing/
│   └── api/
│
├── data/
│   ├── raw/
│   └── processed/
│
├── tests/
├── docs/
├── requirements.txt
├── README.md
└── main.py
```

---

## Getting Started

### Windows quick start

Run one of these from the project folder:

```powershell
.\start.ps1
```

or:

```bat
start.bat
```

The startup script creates or repairs `.venv`, installs `requirements.txt`, and starts the app at:

```text
http://127.0.0.1:8000
```

Useful options:

```powershell
.\start.ps1 -Port 8001
.\start.ps1 -SkipInstall
.\start.ps1 -NoReload
.\start.ps1 -SetupOnly
```

From VS Code, you can also run `Terminal > Run Task... > Start IBC app`.

### Email request setup

The Request and Checkout buttons send an email through SMTP when these environment
variables are set before starting the app:

```powershell
$env:SMTP_HOST="smtp.gmail.com"
$env:SMTP_PORT="587"
$env:SMTP_USERNAME="your.email@gmail.com"
$env:SMTP_PASSWORD="your-app-password"
$env:SMTP_FROM="your.email@gmail.com"
$env:REQUEST_OWNER_EMAIL="s.e.vdongen@gmail.com"
.\start.ps1
```

Use an app password or SMTP token from your email provider instead of your normal
account password. The request owner can be changed in Settings while the app is
running, or later by changing `REQUEST_OWNER_EMAIL` before startup.

### Manual start

```bash
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

## GitHub Repository Setup

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/<your-username>/ibc-document-intelligence.git
git push -u origin main
```
