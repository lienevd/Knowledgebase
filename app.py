from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
import uuid
from pathlib import Path
from typing import List
from src.storage.document_store import store_document, search_keyword, save_uploaded_file, get_document
from src.keywords.keyword_loader import load_keywords

KEYWORDS = load_keywords()
KEYWORD_EXAMPLES = KEYWORDS[:8] if KEYWORDS else ["security", "risk", "authentication", "encryption", "cloud"]

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def home():
    keyword_options = "".join(f'<option value="{kw}">\n' for kw in KEYWORDS)
    keyword_hint = ", ".join(f"<strong>{kw}</strong>" for kw in KEYWORD_EXAMPLES)

    page_html = """
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
                margin-bottom: 10px;
            }

            input[type="text"] {
                flex: 1;
                padding: 12px 15px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                font-size: 1em;
                transition: all 0.3s ease;
            }

            .search-hint {
                color: #666;
                font-size: 0.92em;
                margin-bottom: 20px;
                line-height: 1.5;
            }

            .search-stats {
                background: #f4f6fb;
                padding: 12px;
                border-radius: 8px;
                margin-bottom: 20px;
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
                gap: 10px;
                border: 1px solid #e5e8f0;
            }

            .stat-value {
                font-size: 1.5em;
                font-weight: 700;
                color: #3b4d6b;
            }

            .stat-label {
                font-size: 0.85em;
                color: #7a8699;
                margin-top: 5px;
            }

            .search-result.collapsible-result {
                border-left-color: #9c27b0;
            }

            .search-result.collapsible-result summary {
                cursor: pointer;
                display: flex;
                justify-content: space-between;
                align-items: center;
                list-style: none;
                font-size: 1em;
                font-weight: 600;
                color: #333;
            }

            .search-result.collapsible-result summary::-webkit-details-marker {
                display: none;
            }

            .search-result.collapsible-result summary .collapse-label {
                color: #4f5b76;
                font-size: 0.95em;
                font-weight: 500;
            }

            .search-result.collapsible-result[open] {
                background: #f8f9ff;
            }

            .search-result.collapsible-result .result-content {
                margin-top: 15px;
                color: #555;
                line-height: 1.5;
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
                        <h3>Drop documents here</h3>
                        <p>or click to browse</p>
                        <p style="font-size: 0.9em; color: #999; margin-top: 10px;">Select multiple files</p>
                        <input type="file" id="file-input" accept=".pdf,.doc,.docx,.txt" multiple>
                    </div>

                    <div id="selected-files" style="margin: 20px 0;"></div>

                    <div class="btn-group">
                        <button class="btn-primary" id="upload-btn" disabled>Upload Documents</button>
                        <button class="btn-secondary" id="clear-btn">Clear</button>
                    </div>

                    <div class="loading" id="loading">
                        <div class="spinner"></div>
                        <p id="loading-text">Uploading documents...</p>
                    </div>

                    <div class="error" id="error"></div>

                    <div class="results" id="results">
                        <div class="result-item">
                            <h4>✅ Upload Successful</h4>
                            <div id="upload-summary"></div>
                        </div>
                    </div>
                </div>

                <!-- Search Tab -->
                <div id="search-tab" class="tab-content">
                    <div class="search-section">
                        <h3 style="margin-bottom: 20px;">🔍 Search Documents</h3>
                        <div class="search-input-group">
                            <input type="text" id="search-input" list="keyword-examples" placeholder="Try security, risk, encryption...">
                            <datalist id="keyword-examples">
                                __KEYWORD_OPTIONS__
                            </datalist>
                            <button class="btn-primary" id="search-btn">Search</button>
                        </div>
                        <div class="search-hint">Examples: __KEYWORD_HINT__</div>
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
            const selectedFilesDiv = document.getElementById('selected-files');
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
                handleFileSelect(e.target.files);
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
                    handleFileSelect(e.dataTransfer.files);
                }
            });

            // Handle file selection
            function handleFileSelect(files) {
                if (files && files.length > 0) {
                    let html = '<div style="background: #f8f9ff; padding: 15px; border-radius: 8px;"><strong>Selected Files (' + files.length + '):</strong><ul style="margin: 10px 0 0 20px;">';
                    for (let file of files) {
                        html += '<li>' + file.name + ' (' + (file.size / 1024).toFixed(2) + ' KB)</li>';
                    }
                    html += '</ul></div>';
                    selectedFilesDiv.innerHTML = html;
                    uploadBtn.disabled = false;
                    error.classList.remove('show');
                }
            }

            // Upload documents
            uploadBtn.addEventListener('click', async () => {
                const files = fileInput.files;
                if (!files || files.length === 0) return;

                const formData = new FormData();
                for (let file of files) {
                    formData.append('files', file);
                }

                loading.style.display = 'block';
                results.classList.remove('show');
                error.classList.remove('show');
                document.getElementById('loading-text').textContent = 'Uploading ' + files.length + ' document(s)...';

                try {
                    const response = await fetch('/upload', {
                        method: 'POST',
                        body: formData
                    });

                    if (!response.ok) {
                        throw new Error('Upload failed');
                    }

                    const data = await response.json();
                    displayUploadResults(data);
                } catch (err) {
                    showError('Failed to upload documents. Please try again.');
                } finally {
                    loading.style.display = 'none';
                }
            });

            // Display upload results
            function displayUploadResults(data) {
                let html = '<p style="margin-bottom: 15px;"><strong>' + data.uploaded_count + ' document(s) uploaded successfully!</strong></p>';
                html += '<div style="background: #f8f9ff; padding: 15px; border-radius: 8px;">';
                html += '<strong>Uploaded Files:</strong><ul style="margin: 10px 0 0 20px;">';
                
                data.uploaded_files.forEach(file => {
                    html += '<li>' + file + '</li>';
                });
                
                html += '</ul></div>';
                
                if (data.skipped_files && data.skipped_files.length > 0) {
                    html += '<p style="color: #ff9800; margin-top: 15px;"><strong>⚠️ Skipped:</strong> ' + data.skipped_files.join(', ') + '</p>';
                }
                
                document.getElementById('upload-summary').innerHTML = html;
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
                selectedFilesDiv.innerHTML = '';
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
                    const moreMatches = data.all_results.slice(1);
                    html += `
                        <details class="search-result collapsible-result" style="padding: 0;">
                            <summary>
                                <span>More matches (${moreMatches.length})</span>
                                <span class="collapse-label">Click to expand</span>
                            </summary>
                            <div class="result-content">
                                ${moreMatches.map(result => `
                                    <div class="search-result" style="margin: 15px 0; border-left-color: #9c27b0; padding: 15px;">
                                        <h5 style="margin-bottom: 10px;">${result.filename}</h5>
                                        <div class="keyword-count">${result.keyword_count} occurrences</div>
                                        ${result.context ? `<div class="context">${escapeHtml(result.context)}</div>` : '<div class="context">No preview available.</div>'}
                                    </div>
                                `).join('')}
                            </div>
                        </details>
                    `;
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

    return page_html.replace("__KEYWORD_OPTIONS__", keyword_options).replace("__KEYWORD_HINT__", keyword_hint)
    """Upload multiple documents and store them locally"""
    uploaded_files = []
    skipped_files = []
    
    for file in files:
        try:
            content = await file.read()
            document_id = str(uuid.uuid4())
            text = content.decode(errors="ignore")
            
            # Use the keyword list loaded from the CSV file
            keywords = KEYWORDS if KEYWORDS else [
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
            uploaded_files.append(file.filename)
        except Exception as e:
            skipped_files.append(f"{file.filename} (error)")
    
    return {
        "uploaded_count": len(uploaded_files),
        "uploaded_files": uploaded_files,
        "skipped_files": skipped_files
    }


@app.get("/search")
async def search(keyword: str):
    """Search for a keyword across all stored documents"""
    if not keyword or len(keyword.strip()) == 0:
        return {"error": "Keyword cannot be empty"}
    
    results = search_keyword(keyword)
    return results


@app.get("/documents-count")
async def get_documents_count():
    """Get the count of stored documents"""
    from src.storage.document_store import get_all_documents
    documents = get_all_documents()
    return {"total_documents": len(documents)}