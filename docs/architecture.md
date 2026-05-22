
# System Architecture

## Core Components

### 1. Document Processing Engine
Responsibilities:
- Parse PDFs, DOCX, TXT
- Normalize extracted text
- Generate metadata

### 2. Classification Engine
Responsibilities:
- Read cybersecurity keyword taxonomy
- Count keyword frequency
- Assign category
- Generate confidence score

### 3. Indexing Engine
Responsibilities:
- Build searchable index
- Generate snippets
- Enable fast retrieval

### 4. Security Layer
Responsibilities:
- Role-based access
- Named-user authentication
- Admin account management

---

## Processing Flow

1. Upload document
2. Extract text
3. Normalize content
4. Generate UUID
5. Match keywords
6. Assign category
7. Store metadata
8. Index content
9. Enable search
