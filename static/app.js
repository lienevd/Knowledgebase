// Tabs
const tabBtns = document.querySelectorAll('.tab-btn');
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
const searchResultsContainer = document.getElementById('search-results-container');

const keywordSuggestions = window.KEYWORD_SUGGESTIONS || [];

let selectedFiles = [];

function activateTab(tabName) {
    tabBtns.forEach(btn => btn.classList.toggle('active', btn.dataset.tab === tabName));
    tabContents.forEach(content => content.classList.toggle('active', content.id === tabName));
}

tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        activateTab(btn.dataset.tab);
    });
});

uploadArea.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', (e) => handleFileSelect(e.target.files));
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
clearBtn.addEventListener('click', clearSelection);
searchBtn.addEventListener('click', performSearch);
searchInput.addEventListener('input', (e) => updateSuggestions(e.target.value));
searchInput.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
        event.preventDefault();
        performSearch();
    }
});
document.addEventListener('click', (event) => {
    if (!event.target.closest('.search-dropdown')) {
        suggestionsBox.classList.remove('active');
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

    selectedFilesDiv.innerHTML = `
        <div class="selected-files-box">
            <div class="selected-files-header">Selected Files (${selectedFiles.length})</div>
            <ul>${listItems}</ul>
        </div>
    `;

    uploadBtn.disabled = false;
    clearBtn.disabled = false;
    uploadError.textContent = '';
    hideElement(uploadError);
    hideElement(uploadResults);
}

function clearSelection() {
    fileInput.value = '';
    selectedFiles = [];
    selectedFilesDiv.innerHTML = '';
    uploadBtn.disabled = true;
    clearBtn.disabled = true;
    uploadError.textContent = '';
    hideElement(uploadError);
    hideElement(loadingPanel);
    hideElement(uploadResults);
}

function renderUploadResults(data) {
    const uploadedCount = data.uploaded_count || 0;
    const skippedCount = data.skipped_files ? data.skipped_files.length : 0;

    uploadSummary.innerHTML = `
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
}

async function uploadDocuments() {
    if (selectedFiles.length === 0) {
        uploadError.textContent = 'Please select at least one file to upload.';
        return;
    }

    uploadError.textContent = '';
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
        uploadError.textContent = error.message || 'Upload failed. Please try again.';
        showElement(uploadError);
    } finally {
        setLoading(loadingPanel, false);
        uploadBtn.disabled = selectedFiles.length === 0;
        clearBtn.disabled = selectedFiles.length === 0;
    }
}

uploadBtn.addEventListener('click', uploadDocuments);

function updateSuggestions(query) {
    const normalized = query.trim().toLowerCase();

    if (!normalized) {
        suggestionsBox.innerHTML = '';
        suggestionsBox.classList.remove('active');
        return;
    }

    const matches = keywordSuggestions
        .map(keyword => String(keyword))
        .filter(keyword => keyword.toLowerCase().includes(normalized))
        .slice(0, 8);

    if (matches.length === 0) {
        suggestionsBox.innerHTML = '';
        suggestionsBox.classList.remove('active');
        return;
    }

    suggestionsBox.innerHTML = `
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

    if (!results.length) {
        searchResultsContainer.innerHTML = `
            <div class="result-card">
                <h4>No matches found</h4>
                <p>There are no documents containing <strong>${keyword}</strong>. Try a broader keyword.</p>
            </div>
        `;
        showElement(searchResultsContainer);
        return;
    }

    const resultItems = results.map(item => `
        <div class="result-item-card">
            <h5>${item.filename}</h5>
            <p>Keyword frequency: <strong>${item.keyword_count}</strong></p>
            <p>${item.context || 'No snippet available.'}</p>
            <span class="tag">Document ID: ${item.document_id}</span>
        </div>
    `).join('');

    searchResultsContainer.innerHTML = `
        <div class="result-card">
            <h4>${results.length} document${results.length === 1 ? '' : 's'} matched</h4>
            <p>Showing top ${Math.min(results.length, 5)} results for <strong>${keyword}</strong>.</p>
        </div>
        <div class="result-list">${resultItems}</div>
    `;
    showElement(searchResultsContainer);
}

async function performSearch() {
    const keyword = searchInput.value.trim();

    searchError.textContent = '';
    hideElement(searchError);
    hideElement(searchResultsContainer);

    if (!keyword) {
        searchError.textContent = 'Please type a keyword or select one of the suggested terms.';
        showElement(searchError);
        return;
    }

    setLoading(searchLoading, true);

    try {
        const response = await fetch(`/search?keyword=${encodeURIComponent(keyword)}`);
        const data = await response.json();

        if (!response.ok || data.error) {
            throw new Error(data.error || 'Search failed.');
        }

        renderSearchResults(data);
    } catch (error) {
        searchError.textContent = error.message || 'Unable to perform search. Please try again.';
        showElement(searchError);
    } finally {
        setLoading(searchLoading, false);
    }
}

// Initialize state
clearSelection();
hideElement(searchLoading);
hideElement(searchError);
hideElement(uploadError);
hideElement(searchResultsContainer);
hideElement(uploadResults);
