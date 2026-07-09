
# IBC Amsterdam – Intelligent Document Classification System

## Overview
This project implements a secure document intelligence platform for IBC Amsterdam consultants.

**The PHP app in [`php/`](php/) is the primary, actively developed version** — it runs on
plain PHP shared hosting (e.g. MijnDomein.nl), which has no Python support. The original
Python/FastAPI app at the repo root is kept for local development and reference, but is no
longer the default deployment target.

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

### PHP app (default — deploy this one)

From the `php/` folder, using PHP's built-in dev server:

```powershell
cd php
php -d enable_post_data_reading=0 -S 127.0.0.1:8000 index.php
```

Open `http://127.0.0.1:8000/`. The `enable_post_data_reading=0` flag is required for
multi-file uploads to work correctly on PHP's built-in server (Apache reads it from
`php/.user.ini` in production instead).

Dependencies (`smalot/pdfparser`, `phpmailer/phpmailer`) are pre-built and committed under
`php/vendor/`, since most PHP shared hosts (including MijnDomein.nl) only offer FTP access,
not SSH/Composer. If you need to rebuild them:

```bash
cd php
composer install
```

**Email setup**: create `php/.env` (already blocked from web access via `.htaccess`) with:

```text
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your.email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=your.email@gmail.com
REQUEST_OWNER_EMAIL=s.e.vdongen@gmail.com
```

Use an app password or SMTP token from your email provider instead of your normal account
password. The request owner can also be changed in Settings while the app is running.

**Deploying to MijnDomein.nl (or similar PHP-only shared hosting)**: upload the entire
`php/` folder — including `vendor/` — via FTP to the hosting account's web root, then point
the domain's DNS at that hosting account. No server-side Composer or build step is needed.

### Python app (legacy / local development)

The original FastAPI implementation still lives at the repo root and is useful for local
prototyping, but is not the deployment target anymore.

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

Email setup uses the same SMTP environment variables as the PHP app, set before starting:

```powershell
$env:SMTP_HOST="smtp.gmail.com"
$env:SMTP_PORT="587"
$env:SMTP_USERNAME="your.email@gmail.com"
$env:SMTP_PASSWORD="your-app-password"
$env:SMTP_FROM="your.email@gmail.com"
$env:REQUEST_OWNER_EMAIL="s.e.vdongen@gmail.com"
.\start.ps1
```

Manual start, without the script:

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
