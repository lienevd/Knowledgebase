from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
import uuid
from src.storage.document_store import store_document, search_keyword

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>IBC Document Intelligence</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 20px;
            }

            .container {
                background: white;
                border-radius: 15px;
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
                max-width: 800px;
                width: 100%;
                overflow: hidden;
            }

            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 40px 30px;
                text-align: center;
            }

            .header h1 {
                font-size: 2.5em;
                margin-bottom: 10px;
                font-weight: 700;
            }

            .header p {
                font-size: 1.1em;
                opacity: 0.9;
                margin-bottom: 5px;
            }

            .content {
                padding: 40px 30px;
            }

            .upload-area {
                border: 3px dashed #667eea;
                border-radius: 10px;
                padding: 40px;
                text-align: center;
                cursor: pointer;
                transition: all 0.3s ease;
                background: #f8f9ff;
                margin-bottom: 30px;
            }

            .upload-area:hover {
                border-color: #764ba2;
                background: #f0f2ff;
            }

            .upload-area.dragover {
                border-color: #764ba2;
                background: #e8ebff;
                transform: scale(1.02);
            }

            .upload-icon {
                font-size: 3em;
                margin-bottom: 15px;
            }

            .upload-area h3 {
                color: #333;
                margin-bottom: 10px;
                font-size: 1.3em;
            }

            .upload-area p {
                color: #666;
                margin-bottom: 15px;
            }

            #file-input {
                display: none;
            }

            .btn-group {
                display: flex;
                gap: 15px;
                justify-content: center;
                flex-wrap: wrap;
                margin-top: 20px;
            }

            button {
                padding: 12px 30px;
                border: none;
                border-radius: 8px;
                font-size: 1em;
                cursor: pointer;
                transition: all 0.3s ease;
                font-weight: 600;
            }

            .btn-primary {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }

            .btn-primary:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
            }

            .btn-primary:disabled {
                opacity: 0.6;
                cursor: not-allowed;
                transform: none;
            }

            .btn-secondary {
                background: #e0e0e0;
                color: #333;
            }

            .btn-secondary:hover {
                background: #d0d0d0;
            }

            .file-name {
                text-align: center;
                color: #667eea;
                font-weight: 600;
                margin-bottom: 20px;
                padding: 15px;
                background: #f8f9ff;
                border-radius: 8px;
                display: none;
            }

            .loading {
                display: none;
                text-align: center;
                margin: 30px 0;
            }

            .spinner {
                border: 4px solid #f3f3f3;
                border-top: 4px solid #667eea;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 0 auto 15px;
            }

            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }

            .results {
                display: none;
                margin-top: 30px;
                padding-top: 30px;
                border-top: 2px solid #e0e0e0;
            }

            .results.show {
                display: block;
            }

            .result-item {
                background: #f8f9ff;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 15px;
                border-left: 4px solid #667eea;
            }

            .result-item h4 {
                color: #333;
                margin-bottom: 15px;
                font-size: 1.1em;
            }

            .keyword-scores {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
            }

            .score-card {
                background: white;
                padding: 15px;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
                text-align: center;
                transition: all 0.3s ease;
            }

            .score-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 3px 15px rgba(0, 0, 0, 0.1);
            }

            .score-label {
                color: #666;
                font-size: 0.95em;
                margin-bottom: 8px;
                font-weight: 500;
            }

            .score-value {
                color: #667eea;
                font-size: 1.8em;
                font-weight: 700;
            }

            .error {
                background: #ffebee;
                color: #c62828;
                padding: 15px;
                border-radius: 8px;
                margin-top: 20px;
                border-left: 4px solid #c62828;
                display: none;
            }

            .error.show {
                display: block;
            }

            .document-id {
                color: #999;
                font-size: 0.85em;
                margin-top: 10px;
                word-break: break-all;
            }

            .metadata {
                color: #666;
                font-size: 0.95em;
                margin-bottom: 15px;
            }

            .tabs {
                display: flex;
                gap: 10px;
                margin-bottom: 30px;
                border-bottom: 2px solid #e0e0e0;
            }

            .tab-btn {
                padding: 10px 20px;
                background: none;
                border: none;
                border-bottom: 3px solid transparent;
                cursor: pointer;
                font-size: 1em;
                font-weight: 600;
                color: #666;
                transition: all 0.3s ease;
            }

            .tab-btn.active {
                color: #667eea;
                border-bottom-color: #667eea;
            }

            .tab-content {
                display: none;
            }

            .tab-content.active {
                display: block;
            }

            .search-section {
                background: #f8f9ff;
                padding: 25px;
                border-radius: 10px;
                margin-bottom: 20px;
            }

            .search-input-group {
                display: flex;
                gap: 10px;
                margin-bottom: 20px;
            }

            input[type="text"] {
                flex: 1;
                padding: 12px 15px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                font-size: 1em;
                transition: all 0.3s ease;
            }

            input[type="text"]:focus {
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }

            .search-result {
                background: white;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 15px;
                border-left: 4px solid #4caf50;
            }

            .search-result.top-document {
                border-left-color: #667eea;
                background: #f8f9ff;
                margin-bottom: 25px;
            }

            .search-result h5 {
                color: #333;
                margin-bottom: 10px;
            }

            .search-result .keyword-count {
                font-size: 1.2em;
                font-weight: 700;
                color: #667eea;
                margin-bottom: 10px;
            }

            .search-result .context {
                color: #666;
                font-size: 0.9em;
                font-style: italic;
                margin-top: 10px;
                padding: 10px;
                background: #f0f0f0;
                border-radius: 5px;
            }

            .no-results {
                text-align: center;
                color: #999;
                padding: 30px;
                background: #f8f9ff;
                border-radius: 8px;
            }

            .search-stats {
                background: white;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 20px;
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 15px;
            }

            .stat-item {
                text-align: center;
            }

            .stat-value {
                font-size: 2em;
                font-weight: 700;
                color: #667eea;
            }

            .stat-label {
                font-size: 0.85em;
                color: #666;
                margin-top: 5px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📄 Document Intelligence</h1>
                <p>IBC Document Analysis Platform</p>
                <p style="font-size: 0.95em; margin-top: 10px;">Analyze security and risk keywords in your documents</p>
            </div>

            <div class="content">
                <div class="tabs">
                    <button class="tab-btn active" data-tab="upload-tab">📤 Upload Documents</button>
                    <button class="tab-btn" data-tab="search-tab">🔍 Search</button>
                </div>

                <!-- Upload Tab -->
                <div id="upload-tab" class="tab-content active">
                    <div class="upload-area" id="upload-area">
                        <div class="upload-icon">📁</div>
                        <h3>Drop your document here</h3>
                        <p>or click to browse</p>
                        <input type="file" id="file-input" accept=".pdf,.doc,.docx,.txt">
                    </div>

                    <div class="file-name" id="file-name"></div>

                    <div class="btn-group">
                        <button class="btn-primary" id="upload-btn" disabled>Analyze Document</button>
                        <button class="btn-secondary" id="clear-btn">Clear</button>
                    </div>

                    <div class="loading" id="loading">
                        <div class="spinner"></div>
                        <p>Analyzing document...</p>
                    </div>

                    <div class="error" id="error"></div>

                    <div class="results" id="results">
                        <div class="result-item">
                            <h4>📊 Analysis Results</h4>
                            <div class="metadata">
                                <div><strong>File:</strong> <span id="result-filename"></span></div>
                                <div><strong>Document ID:</strong> <span id="result-docid"></span></div>
                            </div>
                            <h4 style="margin-top: 20px;">Keyword Scores</h4>
                            <div class="keyword-scores" id="scores-container"></div>
                        </div>
                    </div>
                </div>

                <!-- Search Tab -->
                <div id="search-tab" class="tab-content">
                    <div class="search-section">
                        <h3 style="margin-bottom: 20px;">🔍 Search Documents</h3>
                        <div class="search-input-group">
                            <input type="text" id="search-input" placeholder="Enter keyword to search...">
                            <button class="btn-primary" id="search-btn">Search</button>
                        </div>
                    </div>

                    <div class="loading" id="search-loading">
                        <div class="spinner"></div>
                        <p>Searching documents...</p>
                    </div>

                    <div class="error" id="search-error"></div>

                    <div id="search-results-container">
                        <!-- Search results will be populated here -->
                    </div>
                </div>
            </div>
        </div>

        <script>
            // Tab switching
            const tabBtns = document.querySelectorAll('.tab-btn');
            const tabContents = document.querySelectorAll('.tab-content');

            tabBtns.forEach(btn => {
                btn.addEventListener('click', () => {
                    const tabName = btn.getAttribute('data-tab');
                    
                    // Remove active class from all
                    tabBtns.forEach(b => b.classList.remove('active'));
                    tabContents.forEach(c => c.classList.remove('active'));
                    
                    // Add active class to clicked tab
                    btn.classList.add('active');
                    document.getElementById(tabName).classList.add('active');
                });
            });

            // Upload Tab Elements
            const uploadArea = document.getElementById('upload-area');
            const fileInput = document.getElementById('file-input');
            const fileName = document.getElementById('file-name');
            const uploadBtn = document.getElementById('upload-btn');
            const clearBtn = document.getElementById('clear-btn');
            const loading = document.getElementById('loading');
            const error = document.getElementById('error');
            const results = document.getElementById('results');

            // Search Tab Elements
            const searchInput = document.getElementById('search-input');
            const searchBtn = document.getElementById('search-btn');
            const searchLoading = document.getElementById('search-loading');
            const searchError = document.getElementById('search-error');
            const searchResultsContainer = document.getElementById('search-results-container');

            // Upload area click
            uploadArea.addEventListener('click', () => fileInput.click());

            // File input change
            fileInput.addEventListener('change', (e) => {
                handleFileSelect(e.target.files[0]);
            });

            // Drag and drop
            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.classList.add('dragover');
            });

            uploadArea.addEventListener('dragleave', () => {
                uploadArea.classList.remove('dragover');
            });

            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('dragover');
                if (e.dataTransfer.files.length > 0) {
                    handleFileSelect(e.dataTransfer.files[0]);
                }
            });

            // Handle file selection
            function handleFileSelect(file) {
                if (file) {
                    fileName.textContent = '✓ Selected: ' + file.name;
                    fileName.style.display = 'block';
                    uploadBtn.disabled = false;
                    error.classList.remove('show');
                }
            }

            // Upload and analyze
            uploadBtn.addEventListener('click', async () => {
                const file = fileInput.files[0];
                if (!file) return;

                const formData = new FormData();
                formData.append('file', file);

                loading.style.display = 'block';
                results.classList.remove('show');
                error.classList.remove('show');

                try {
                    const response = await fetch('/upload', {
                        method: 'POST',
                        body: formData
                    });

                    if (!response.ok) {
                        throw new Error('Upload failed');
                    }

                    const data = await response.json();
                    displayResults(data);
                } catch (err) {
                    showError('Failed to analyze document. Please try again.');
                } finally {
                    loading.style.display = 'none';
                }
            });

            // Display results
            function displayResults(data) {
                document.getElementById('result-filename').textContent = data.filename;
                document.getElementById('result-docid').textContent = data.document_id;

                const scoresContainer = document.getElementById('scores-container');
                scoresContainer.innerHTML = '';

                const scores = data.keyword_scores;
                const maxScore = Math.max(...Object.values(scores));

                for (const [keyword, score] of Object.entries(scores)) {
                    const percentage = (score / (maxScore || 1)) * 100;
                    const card = document.createElement('div');
                    card.className = 'score-card';
                    card.innerHTML = `
                        <div class="score-label">${keyword}</div>
                        <div class="score-value">${score}</div>
                    `;
                    scoresContainer.appendChild(card);
                }

                results.classList.add('show');
            }

            // Show error
            function showError(message) {
                error.textContent = '❌ ' + message;
                error.classList.add('show');
            }

            // Clear
            clearBtn.addEventListener('click', () => {
                fileInput.value = '';
                fileName.style.display = 'none';
                uploadBtn.disabled = true;
                results.classList.remove('show');
                error.classList.remove('show');
            });

            // Search functionality
            searchBtn.addEventListener('click', performSearch);
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') performSearch();
            });

            async function performSearch() {
                const keyword = searchInput.value.trim();
                if (!keyword) {
                    showSearchError('Please enter a keyword to search.');
                    return;
                }

                searchLoading.style.display = 'block';
                searchResultsContainer.innerHTML = '';
                searchError.classList.remove('show');

                try {
                    const response = await fetch(`/search?keyword=${encodeURIComponent(keyword)}`);
                    if (!response.ok) throw new Error('Search failed');

                    const data = await response.json();
                    displaySearchResults(data);
                } catch (err) {
                    showSearchError('Failed to search documents. Please try again.');
                } finally {
                    searchLoading.style.display = 'none';
                }
            }

            function displaySearchResults(data) {
                if (data.total_matches === 0) {
                    searchResultsContainer.innerHTML = `
                        <div class="no-results">
                            <p>No documents found containing the keyword "<strong>${data.keyword}</strong>"</p>
                        </div>
                    `;
                    return;
                }

                let html = `
                    <div class="search-stats">
                        <div class="stat-item">
                            <div class="stat-value">${data.total_matches}</div>
                            <div class="stat-label">Documents Found</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">${data.top_document.keyword_count}</div>
                            <div class="stat-label">Highest Count</div>
                        </div>
                    </div>
                `;

                // Top document
                if (data.top_document) {
                    html += `
                        <div class="search-result top-document">
                            <h5>🏆 Top Match</h5>
                            <div><strong>Document:</strong> ${data.top_document.filename}</div>
                            <div class="keyword-count">Keyword count: ${data.top_document.keyword_count}</div>
                            ${data.top_document.context ? `<div class="context">${escapeHtml(data.top_document.context)}</div>` : ''}
                        </div>
                    `;
                }

                // All results
                if (data.all_results.length > 1) {
                    html += '<h5 style="margin-top: 25px; margin-bottom: 15px;">All Results</h5>';
                    data.all_results.forEach((result, index) => {
                        if (index === 0) return; // Skip top result as it's already shown
                        html += `
                            <div class="search-result">
                                <h5>${result.filename}</h5>
                                <div class="keyword-count">${result.keyword_count} occurrences</div>
                                ${result.context ? `<div class="context">${escapeHtml(result.context)}</div>` : ''}
                            </div>
                        `;
                    });
                }

                searchResultsContainer.innerHTML = html;
            }

            function showSearchError(message) {
                searchError.textContent = '❌ ' + message;
                searchError.classList.add('show');
            }

            function escapeHtml(text) {
                const div = document.createElement('div');
                div.textContent = text;
                return div.innerHTML;
            }
        </script>
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

    # Store the document locally
    store_document(document_id, file.filename, text, scores)

    return {
        "document_id": document_id,
        "filename": file.filename,
        "keyword_scores": scores
    }


@app.get("/search")
async def search(keyword: str):
    """Search for a keyword across all stored documents"""
    if not keyword or len(keyword.strip()) == 0:
        return {"error": "Keyword cannot be empty"}
    
    results = search_keyword(keyword)
    return results