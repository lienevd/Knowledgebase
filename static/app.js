// Tabs
const navBtns = document.querySelectorAll('.nav-btn');
const tabContents = document.querySelectorAll('.tab-content');

const uploadArea = document.getElementById('upload-area');
const fileInput = document.getElementById('file-input');
const selectedFilesDiv = document.getElementById('selected-files');
const uploadBtn = document.getElementById('upload-btn');
const clearBtn = document.getElementById('clear-btn');
const loadingPanel = document.getElementById('loading');
const uploadError = document.getElementById('error');
const uploadResults = document.getElementById('results');
const uploadSummary = document.getElementById('upload-summary');

const searchBtn = document.getElementById('search-btn');
const searchInput = document.getElementById('search-input');
const suggestionsBox = document.getElementById('search-suggestions');
const searchLoading = document.getElementById('search-loading');
const searchError = document.getElementById('search-error');
const searchMessage = document.getElementById('search-message');
const searchResultsContainer = document.getElementById('search-results-container');

const docCountEl = document.getElementById('doc-count');
const keywordCountEl = document.getElementById('keyword-count');

const keywordSuggestions = window.KEYWORD_SUGGESTIONS || [];

let selectedFiles = [];
function safeSetHTML(el, html) {
    if (!el) return;
    el.innerHTML = html;
}

function safeSetText(el, text) {
    if (!el) return;
    el.textContent = text;
}

function activateTab(tabName) {
    navBtns.forEach(btn => btn.classList.toggle('active', btn.dataset.tab === tabName));
    tabContents.forEach(content => content.classList.toggle('active', content.id === tabName));
}

navBtns.forEach(btn => {
    if (!btn) return;
    btn.addEventListener('click', () => {
        activateTab(btn.dataset.tab);
    });
});
if (uploadArea) {
    uploadArea.addEventListener('click', () => fileInput?.click());
    uploadArea.addEventListener('dragover', (event) => {
        event.preventDefault();
        uploadArea.classList.add('drag-over');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('drag-over');
    });

    uploadArea.addEventListener('drop', (event) => {
        event.preventDefault();
        uploadArea.classList.remove('drag-over');
        handleFileSelect(event.dataTransfer.files);
    });
}
if (fileInput) {
    fileInput.addEventListener('change', (e) => handleFileSelect(e.target.files));
}
if (clearBtn) {
    clearBtn.addEventListener('click', clearSelection);
}
if (searchBtn) {
    searchBtn.addEventListener('click', performSearch);
}
if (searchInput) {
    searchInput.addEventListener('input', (e) => updateSuggestions(e.target.value));
    searchInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            event.preventDefault();
            performSearch();
        }
    });
}
document.addEventListener('click', (event) => {
    if (!event.target.closest('.search-dropdown')) {
        if (suggestionsBox) suggestionsBox.classList.remove('active');
    }
});

function showElement(el) {
    if (!el) return;
    el.classList.add('active');
    if (el.hasAttribute && el.hasAttribute('hidden')) el.removeAttribute('hidden');
}

function hideElement(el) {
    if (!el) return;
    el.classList.remove('active');
    if (el.setAttribute) el.setAttribute('hidden', 'true');
}

function setLoading(el, enabled) {
    if (enabled) {
        showElement(el);
    } else {
        hideElement(el);
    }
}

function handleFileSelect(files) {
    selectedFiles = Array.from(files || []);
    if (selectedFiles.length === 0) {
        clearSelection();
        return;
    }

    const listItems = selectedFiles.map(file => `
        <li>
            <span>${file.name}</span>
            <span>${(file.size / 1024).toFixed(1)} KB</span>
        </li>
    `).join('');
        safeSetHTML(selectedFilesDiv, `
        <div class="selected-files-box">
            <div class="selected-files-header">Selected Files (${selectedFiles.length})</div>
            <ul>${listItems}</ul>
        </div>
    `;

    uploadBtn.disabled = false;
    clearBtn.disabled = false;
    safeSetText(uploadError, '');
    hideElement(uploadError);
    hideElement(uploadResults);
}

function clearSelection() {
    if (fileInput) fileInput.value = '';
    selectedFiles = [];
        safeSetHTML(selectedFilesDiv, '');
    uploadBtn.disabled = true;
    clearBtn.disabled = true;
    safeSetText(uploadError, '');
    hideElement(uploadError);
    hideElement(loadingPanel);
    hideElement(uploadResults);
}

function renderUploadResults(data) {
    const uploadedCount = data.uploaded_count || 0;
    const skippedCount = data.skipped_files ? data.skipped_files.length : 0;
    
    // Update document count in sidebar
    if (docCountEl) {
        const currentCount = parseInt(docCountEl.textContent) || 0;
        docCountEl.textContent = currentCount + uploadedCount;
    }

        safeSetHTML(uploadSummary, `
        <div class="result-card">
            <h4>${uploadedCount > 0 ? 'Upload Complete' : 'Upload status'}</h4>
            <p>${uploadedCount} file${uploadedCount === 1 ? '' : 's'} uploaded successfully.</p>
            ${skippedCount > 0 ? `<p>${skippedCount} file${skippedCount === 1 ? '' : 's'} could not be processed.</p>` : ''}
            ${data.uploaded_files.length ? `
                <div class="result-summary">
                    <div class="summary-item">
                        <strong>Uploaded</strong>
                        ${data.uploaded_files.map(name => `<div>${name}</div>`).join('')}
                    </div>
                </div>
            ` : ''}
            ${skippedCount > 0 ? `
                <div class="result-summary">
                    <div class="summary-item">
                        <strong>Skipped Files</strong>
                        ${data.skipped_files.map(name => `<div>${name}</div>`).join('')}
                    </div>
                </div>
            ` : ''}
        </div>
    `;

    showElement(uploadResults);
    hideElement(document.getElementById('empty-state'));
}

async function uploadDocuments() {
    if (selectedFiles.length === 0) {
        safeSetText(uploadError, 'Please select at least one file to upload.');
        return;
    }

    safeSetText(uploadError, '');
    const formData = new FormData();
    selectedFiles.forEach(file => formData.append('files', file));

    setLoading(loadingPanel, true);
    uploadBtn.disabled = true;
    clearBtn.disabled = true;

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData,
        });

        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || 'Upload failed. Please try again.');
        }

        renderUploadResults(data);
    } catch (error) {
        safeSetText(uploadError, error.message || 'Upload failed. Please try again.');
        showElement(uploadError);
    } finally {
        setLoading(loadingPanel, false);
        uploadBtn.disabled = selectedFiles.length === 0;
        clearBtn.disabled = selectedFiles.length === 0;
    }
}

if (uploadBtn) {
    uploadBtn.addEventListener('click', uploadDocuments);
}

function updateSuggestions(query) {
    const normalized = query.trim().toLowerCase();

    if (!normalized) {
            safeSetHTML(suggestionsBox, '');
        suggestionsBox.classList.remove('active');
        return;
    }

    const matches = keywordSuggestions
        .map(keyword => String(keyword))
        .filter(keyword => keyword.toLowerCase().includes(normalized))
        .slice(0, 8);

    if (matches.length === 0) {
            safeSetHTML(suggestionsBox, '');
        suggestionsBox.classList.remove('active');
        return;
    }

        safeSetHTML(suggestionsBox, `
        <ul>
            ${matches.map(keyword => `<li class="suggestion-item">${keyword}</li>`).join('')}
        </ul>
    `;
    suggestionsBox.classList.add('active');

    suggestionsBox.querySelectorAll('.suggestion-item').forEach(item => {
        item.addEventListener('click', () => {
            searchInput.value = item.textContent;
            suggestionsBox.classList.remove('active');
            performSearch();
        });
    });
}

function renderSearchResults(data) {
    const keyword = data.keyword || searchInput.value.trim();
    const results = data.all_results || [];

    if (!searchResultsContainer) return;

    if (!results.length) {
        safeSetHTML(searchResultsContainer, `
            <div class="result-card">
                <h4>No matches found</h4>
                <p>There are no documents containing <strong>${keyword}</strong>. Try a broader keyword.</p>
            </div>
        `);
        showElement(searchResultsContainer);
        return;
    }

    const resultItems = results.map(item => `
        <div class="result-item-card">
            <div class="result-item-header">
                <h5>${item.filename}</h5>
                <div class="action-buttons">
                    <button type="button" class="btn-secondary preview-btn" data-id="${item.document_id}">Preview</button>
                    <button type="button" class="btn-primary request-btn" data-id="${item.document_id}" data-name="${encodeURIComponent(item.filename)}">Request Document</button>
                </div>
            </div>
            <p><strong>${item.keyword_count}</strong> matches</p>
            <p>${item.context || 'No snippet available.'}</p>
            <p class="meta">Category: ${item.category || 'Uncategorized'}</p>
        </div>
    `).join('');

    safeSetHTML(searchResultsContainer, `
        <div class="result-card">
            <h4>${results.length} document${results.length === 1 ? '' : 's'} matched</h4>
            <p>Showing top ${Math.min(results.length, 5)} results for <strong>${keyword}</strong>.</p>
        </div>
        <div class="result-list">${resultItems}</div>
    `;

    searchResultsContainer.querySelectorAll('.preview-btn').forEach(button => {
        button.addEventListener('click', () => {
            const documentId = button.dataset.id;
            window.open(`/preview?document_id=${encodeURIComponent(documentId)}`, '_blank');
        });
    });

    searchResultsContainer.querySelectorAll('.request-btn').forEach(button => {
        button.addEventListener('click', async () => {
            const documentId = button.dataset.id;
            const keyword = searchInput.value.trim();
            await sendDownloadRequest(documentId, keyword);
        });
    });

    showElement(searchResultsContainer);
}

async function performSearch() {
    const keyword = searchInput.value.trim();

    safeSetText(searchError, '');
    hideElement(searchError);
    hideElement(searchResultsContainer);

    if (!keyword) {
        safeSetText(searchError, 'Please type a keyword or select one of the suggested terms.');
        showElement(searchError);
        return;
    }

    setLoading(searchLoading, true);
    safeSetText(searchMessage, '');
    hideElement(searchMessage);

    try {
        const response = await fetch(`/search?keyword=${encodeURIComponent(keyword)}`);
        const data = await response.json();

        if (!response.ok || data.error) {
            throw new Error(data.error || 'Search failed.');
        }

        renderSearchResults(data);
    } catch (error) {
        safeSetText(searchError, error.message || 'Unable to perform search. Please try again.');
        showElement(searchError);
    } finally {
        setLoading(searchLoading, false);
    }
}

async function sendDownloadRequest(documentId, keyword) {
    safeSetText(searchError, '');
    hideElement(searchError);
    try {
        const response = await fetch('/request-download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ document_id: documentId, keyword }),
        });

        const data = await response.json();
        if (!response.ok || data.detail || data.error) {
            throw new Error(data.detail || data.error || 'Unable to request document.');
        }

        safeSetText(searchMessage, data.message || 'Your request has been submitted.');
        showElement(searchMessage);
    } catch (error) {
        safeSetText(searchError, error.message || 'Unable to request document. Please try again.');
        showElement(searchError);
    }
}

// Initialize state
clearSelection();
hideElement(searchLoading);
hideElement(searchError);
hideElement(searchMessage);
hideElement(uploadError);
hideElement(searchResultsContainer);
hideElement(uploadResults);
