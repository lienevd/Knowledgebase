function hideSuggestions() {
    if (!suggestionsBox) return;

    suggestionsBox.classList.remove('active');
    suggestionsBox.innerHTML = '';
}

const basketCountEl = document.getElementById('basket-count');
const basketListEl = document.getElementById('basket-list');
const requestBasketBtn = document.getElementById('request-basket-btn');
const clearBasketBtn = document.getElementById('clear-basket-btn');

let basket = JSON.parse(localStorage.getItem('documentBasket') || '[]');
// Tabs
function activateTab(tabName) {
    const navBtns = document.querySelectorAll('.nav-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    navBtns.forEach(btn => {
        if (btn.dataset.tab === tabName) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
    
    tabContents.forEach(content => {
        if (content.id === tabName) {
            content.classList.add('active');
        } else {
            content.classList.remove('active');
        }
    });
}

// Use event delegation for nav buttons
document.addEventListener('click', (e) => {
    const navBtn = e.target.closest('.nav-btn');
    if (navBtn && navBtn.dataset.tab) {
        e.preventDefault();
        activateTab(navBtn.dataset.tab);
    }
});

// Get DOM elements
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

async function refreshDocumentCount() {
  try {
    const response = await fetch('/documents-count');
    const data = await response.json();

    if (docCountEl) {
      docCountEl.textContent = data.total_documents || 0;
    }
  } catch (error) {
    console.error('Could not refresh document count:', error);
  }
}

function saveBasket() {
  localStorage.setItem('documentBasket', JSON.stringify(basket));
  renderBasket();
}

function addToBasket(documentId, filename) {
  if (basket.some(item => item.document_id === documentId)) {
    safeSetText(searchMessage, 'This document is already in your basket.');
    showElement(searchMessage);
    return;
  }

  basket.push({
    document_id: documentId,
    filename,
  });

  saveBasket();

  safeSetText(searchMessage, `"${filename}" added to your basket.`);
  showElement(searchMessage);
}

function removeFromBasket(documentId) {
  basket = basket.filter(item => item.document_id !== documentId);
  saveBasket();
}

function clearBasket() {
  basket = [];
  saveBasket();
}

function renderBasket() {
  if (basketCountEl) {
    basketCountEl.textContent = basket.length;
  }

  if (!basketListEl) return;

  if (!basket.length) {
    basketListEl.innerHTML = '<p class="basket-empty">No documents selected yet.</p>';
    if (requestBasketBtn) requestBasketBtn.disabled = true;
    if (clearBasketBtn) clearBasketBtn.disabled = true;
    return;
  }

  basketListEl.innerHTML = basket.map(item => `
    <div class="basket-item">
      <span>${item.filename}</span>
      <button type="button" class="basket-remove-btn" onclick="removeFromBasket('${item.document_id}')">
        Remove
      </button>
    </div>
  `).join('');

  if (requestBasketBtn) requestBasketBtn.disabled = false;
  if (clearBasketBtn) clearBasketBtn.disabled = false;
}

async function requestBasketDocuments() {
  if (!basket.length) return;

  try {
    const response = await fetch('/request-bulk-download', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        document_ids: basket.map(item => item.document_id),
        keyword: searchInput?.value || '',
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || 'Unable to request basket documents.');
    }

    safeSetText(searchMessage, data.message);
    showElement(searchMessage);
    clearBasket();
  } catch (error) {
    safeSetText(searchError, error.message || 'Unable to request basket documents.');
    showElement(searchError);
  }
}

async function showDocumentSummary(documentId) {
  try {
    const response = await fetch(`/preview?document_id=${encodeURIComponent(documentId)}`);
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || 'Unable to load summary.');
    }

    const summaryBox = document.getElementById(`summary-${documentId}`);

    if (summaryBox) {
      summaryBox.innerHTML = `
        <strong>Summary</strong>
        <p>${data.summary}</p>
      `;
      summaryBox.classList.toggle('active');
    }
  } catch (error) {
    safeSetText(searchError, error.message || 'Unable to load summary.');
    showElement(searchError);
  }
}

// Upload area event listeners
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
    `);

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
    
    refreshDocumentCount();

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
    `);

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
    `);
    suggestionsBox.classList.add('active');

    suggestionsBox.querySelectorAll('.suggestion-item').forEach(item => {
        item.addEventListener('click', () => {
            // Extract the keyword text (remove the emoji prefix)
            const text = item.textContent.trim();
            searchInput.value = text.startsWith('🏷') ? text.substring(1).trim() : text;
            suggestionsBox.classList.remove('active');
            performSearch();
        });
    });
}

function escapeHTML(value) {
    return String(value || '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function renderSearchResults(data) {
  const keyword = data.keyword || searchInput.value.trim();
  const results = data.all_results || [];

  if (!searchResultsContainer) return;

  if (!results.length) {
    safeSetHTML(searchResultsContainer, `
      <div class="empty-search">
        <p>No documents found containing <strong>${keyword}</strong>.</p>
        <p>Try searching for a different keyword.</p>
      </div>
    `);
    showElement(searchResultsContainer);
    return;
  }

  const sortedResults = [...results].sort(
    (a, b) => (b.keyword_count || 0) - (a.keyword_count || 0)
  );

  const topResult = sortedResults[0];
  const remainingResults = sortedResults.slice(1);

  let html = `
    <div class="search-results-header">
      <h3>${results.length} document${results.length === 1 ? '' : 's'} found for "${keyword}"</h3>
    </div>
  `;

  html += renderResultCard(topResult, true);

  if (remainingResults.length > 0) {
    html += `
      <div class="collapsible-results">
        <button type="button" id="other-results-toggle" class="collapsible-toggle">
          <span class="toggle-icon">▶</span>
          ${remainingResults.length} other result${remainingResults.length === 1 ? '' : 's'}
        </button>

        <div id="other-results-list" class="collapsible-content" style="display: none;">
          ${remainingResults.map(item => renderResultCard(item, false)).join('')}
        </div>
      </div>
    `;
  }

  safeSetHTML(searchResultsContainer, html);

  const toggleBtn = document.getElementById('other-results-toggle');
  const collapsibleContent = document.getElementById('other-results-list');

  if (toggleBtn && collapsibleContent) {
    toggleBtn.addEventListener('click', () => {
      const isOpen = collapsibleContent.style.display !== 'none';
      collapsibleContent.style.display = isOpen ? 'none' : 'block';

      const icon = toggleBtn.querySelector('.toggle-icon');
      if (icon) icon.textContent = isOpen ? '▶' : '▼';
    });
  }

  showElement(searchResultsContainer);
}

function renderResultCard(item, isTopResult) {
  return `
    <div class="result-card ${isTopResult ? 'top-result' : ''}">
      ${isTopResult ? '<span class="top-badge">Top Match</span>' : ''}

      <h3>${item.filename}</h3>

      <p class="result-meta">
        ${item.keyword_count || 0} ${(item.keyword_count || 0) === 1 ? 'match' : 'matches'}
        · Category: ${item.category || 'Uncategorized'}
      </p>

      <p class="result-context">${item.context || 'No context available.'}</p>

      <div class="result-actions">
        <button type="button" onclick="showDocumentSummary('${item.document_id}')">
          Preview Summary
        </button>

        <button type="button" onclick="addToBasket('${item.document_id}', '${item.filename.replace(/'/g, "\\'")}')">
          Add to Basket
        </button>

        <button type="button" onclick="sendDownloadRequest('${item.document_id}', '${searchInput.value.trim()}')">
          Request Single Document
        </button>
      </div>

      <div id="summary-${item.document_id}" class="summary-box"></div>
    </div>
  `;
}

async function performSearch() {
    const keyword = searchInput.value.trim();

    // Hide suggestions dropdown
    if (suggestionsBox) suggestionsBox.classList.remove('active');
    
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

if (requestBasketBtn) {
  requestBasketBtn.addEventListener('click', requestBasketDocuments);
}

if (clearBasketBtn) {
  clearBasketBtn.addEventListener('click', clearBasket);
}

// Initialize state
clearSelection();
hideElement(searchLoading);
hideElement(searchError);
hideElement(searchMessage);
hideElement(uploadError);
hideElement(searchResultsContainer);
hideElement(uploadResults);
refreshDocumentCount();
renderBasket();
