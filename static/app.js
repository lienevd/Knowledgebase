(() => {
  const SELECTORS = {
    appShell: 'app-shell',
    sidebarToggle: 'sidebar-toggle',
    basketTrigger: 'basket-trigger',
    basketDrawer: 'basket-drawer',
    basketClose: 'basket-close',
    drawerOverlay: 'drawer-overlay',
    basketList: 'basket-list',
    requestBasketBtn: 'request-basket-btn',
    clearBasketBtn: 'clear-basket-btn',
    uploadArea: 'upload-area',
    fileInput: 'file-input',
    selectedFiles: 'selected-files',
    uploadBtn: 'upload-btn',
    clearBtn: 'clear-btn',
    loadingPanel: 'loading',
    uploadError: 'error',
    uploadResults: 'results',
    uploadSummary: 'upload-summary',
    emptyState: 'empty-state',
    searchBtn: 'search-btn',
    searchInput: 'search-input',
    suggestionsBox: 'search-suggestions',
    searchLoading: 'search-loading',
    searchError: 'search-error',
    searchMessage: 'search-message',
    searchResults: 'search-results-container',
    docCount: 'doc-count',
    documentsLoading: 'documents-loading',
    documentsError: 'documents-error',
    documentsMessage: 'documents-message',
    documentsList: 'documents-list',
    documentsListCount: 'documents-list-count',
    documentsCategoryFilter: 'documents-category-filter',
    refreshDocumentsBtn: 'refresh-documents-btn',
  };

  const STORAGE_KEYS = {
    basket: 'documentBasket',
  };

  const state = {
    selectedFiles: [],
    basket: readStoredBasket(),
    keywordSuggestions: window.KEYWORD_SUGGESTIONS || [],
    documents: [],
    documentCategory: 'all',
  };

  const els = getElements(SELECTORS);
  const basketCountEls = document.querySelectorAll('[data-basket-count]');

  function getElements(selectors) {
    return Object.fromEntries(
      Object.entries(selectors).map(([name, id]) => [name, document.getElementById(id)]),
    );
  }

  function readStoredBasket() {
    try {
      const basket = JSON.parse(localStorage.getItem(STORAGE_KEYS.basket) || '[]');
      return Array.isArray(basket) ? basket : [];
    } catch (error) {
      console.warn('Could not read stored basket:', error);
      return [];
    }
  }

  function escapeHTML(value) {
    return String(value || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function setHTML(el, html) {
    if (el) el.innerHTML = html;
  }

  function setText(el, text) {
    if (el) el.textContent = text;
  }

  function show(el) {
    if (!el) return;
    el.classList.add('active');
    el.removeAttribute('hidden');
  }

  function hide(el) {
    if (!el) return;
    el.classList.remove('active');
    el.setAttribute('hidden', 'true');
  }

  function setBusy(el, isBusy) {
    isBusy ? show(el) : hide(el);
  }

  function showMessage(el, message) {
    setText(el, message);
    show(el);
  }

  function clearMessage(el) {
    setText(el, '');
    hide(el);
  }

  async function parseJsonResponse(response, fallbackMessage) {
    const data = await response.json();

    if (!response.ok || data.error || data.detail) {
      throw new Error(data.detail || data.error || fallbackMessage);
    }

    return data;
  }

  const api = {
    async fetchDocumentCount() {
      const response = await fetch('/documents-count');
      return parseJsonResponse(response, 'Could not load document count.');
    },

    async fetchDocuments() {
      const response = await fetch('/documents');
      return parseJsonResponse(response, 'Could not load documents.');
    },

    async deleteDocument(documentId) {
      const response = await fetch(`/documents/${encodeURIComponent(documentId)}`, {
        method: 'DELETE',
      });
      return parseJsonResponse(response, 'Could not delete document.');
    },

    async uploadDocuments(files) {
      const formData = new FormData();
      files.forEach((file) => formData.append('files', file));

      const response = await fetch('/upload', {
        method: 'POST',
        body: formData,
      });

      return parseJsonResponse(response, 'Upload failed. Please try again.');
    },

    async search(keyword) {
      const response = await fetch(`/search?keyword=${encodeURIComponent(keyword)}`);
      return parseJsonResponse(response, 'Search failed.');
    },

    async requestDownload(documentId, keyword) {
      const response = await fetch('/request-download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ document_id: documentId, keyword }),
      });

      return parseJsonResponse(response, 'Unable to request document.');
    },

    async requestBulkDownload(documentIds, keyword) {
      const response = await fetch('/request-bulk-download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ document_ids: documentIds, keyword }),
      });

      return parseJsonResponse(response, 'Unable to request basket documents.');
    },

    async fetchPreview(documentId) {
      const response = await fetch(`/preview?document_id=${encodeURIComponent(documentId)}`);
      return parseJsonResponse(response, 'Unable to load summary.');
    },
  };

  const navigation = {
    init() {
      document.addEventListener('click', (event) => {
        const navBtn = event.target.closest('.tab-link');
        if (!navBtn?.dataset.tab) return;

        event.preventDefault();
        this.activateTab(navBtn.dataset.tab);
      });

      els.sidebarToggle?.addEventListener('click', () => this.toggleSidebar());
    },

    activateTab(tabName) {
      document.querySelectorAll('.tab-link').forEach((btn) => {
        btn.classList.toggle('active', btn.dataset.tab === tabName);
      });

      document.querySelectorAll('.tab-content').forEach((content) => {
        content.classList.toggle('active', content.id === tabName);
      });

      if (tabName === 'documents-tab') {
        documents.load();
      }
    },

    toggleSidebar() {
      const isCollapsed = els.appShell?.classList.toggle('sidebar-collapsed');

      if (!els.sidebarToggle) return;

      els.sidebarToggle.setAttribute('aria-expanded', String(!isCollapsed));
      els.sidebarToggle.setAttribute(
        'aria-label',
        isCollapsed ? 'Expand sidebar' : 'Collapse sidebar',
      );
    },
  };

  const metrics = {
    async refreshDocumentCount() {
      try {
        const data = await api.fetchDocumentCount();
        setText(els.docCount, data.total_documents || 0);
      } catch (error) {
        console.error('Could not refresh document count:', error);
      }
    },
  };

  const basket = {
    init() {
      els.basketList?.addEventListener('click', (event) => {
        const removeBtn = event.target.closest('[data-remove-basket]');
        if (removeBtn) this.remove(removeBtn.dataset.removeBasket);
      });

      els.requestBasketBtn?.addEventListener('click', () => this.requestDocuments());
      els.clearBasketBtn?.addEventListener('click', () => this.clear());
      els.basketTrigger?.addEventListener('click', () => this.openDrawer());
      els.basketClose?.addEventListener('click', () => this.closeDrawer());
      els.drawerOverlay?.addEventListener('click', () => this.closeDrawer());

      document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') this.closeDrawer();
      });

      this.render();
    },

    add(documentId, filename) {
      if (state.basket.some((item) => item.document_id === documentId)) {
        showMessage(els.searchMessage, 'This document is already in your basket.');
        return;
      }

      state.basket.push({ document_id: documentId, filename });
      this.save();
      showMessage(els.searchMessage, `"${filename}" added to your basket.`);
    },

    remove(documentId) {
      state.basket = state.basket.filter((item) => item.document_id !== documentId);
      this.save();
    },

    clear() {
      state.basket = [];
      this.save();
    },

    save() {
      localStorage.setItem(STORAGE_KEYS.basket, JSON.stringify(state.basket));
      this.render();
    },

    openDrawer() {
      this.render();
      els.basketDrawer?.removeAttribute('hidden');
      els.drawerOverlay?.removeAttribute('hidden');

      requestAnimationFrame(() => {
        els.basketDrawer?.classList.add('active');
        els.drawerOverlay?.classList.add('active');
      });
    },

    closeDrawer() {
      els.basketDrawer?.classList.remove('active');
      els.drawerOverlay?.classList.remove('active');

      window.setTimeout(() => {
        els.basketDrawer?.setAttribute('hidden', 'true');
        els.drawerOverlay?.setAttribute('hidden', 'true');
      }, 180);
    },

    async requestDocuments() {
      if (!state.basket.length) return;

      try {
        const data = await api.requestBulkDownload(
          state.basket.map((item) => item.document_id),
          els.searchInput?.value || '',
        );

        showMessage(els.searchMessage, data.message);
        this.clear();
        this.closeDrawer();
      } catch (error) {
        showMessage(
          els.searchError,
          error.message || 'Unable to request basket documents.',
        );
      }
    },

    render() {
      basketCountEls.forEach((el) => {
        el.textContent = state.basket.length;
      });

      if (!els.basketList) return;

      if (els.requestBasketBtn) els.requestBasketBtn.disabled = state.basket.length === 0;
      if (els.clearBasketBtn) els.clearBasketBtn.disabled = state.basket.length === 0;

      if (!state.basket.length) {
        setHTML(els.basketList, '<p class="basket-empty">No documents selected yet.</p>');
        return;
      }

      setHTML(els.basketList, state.basket.map(renderBasketItem).join(''));
    },
  };

  const upload = {
    init() {
      els.uploadArea?.addEventListener('click', () => els.fileInput?.click());
      els.uploadArea?.addEventListener('dragover', (event) => {
        event.preventDefault();
        els.uploadArea.classList.add('drag-over');
      });
      els.uploadArea?.addEventListener('dragleave', () => {
        els.uploadArea.classList.remove('drag-over');
      });
      els.uploadArea?.addEventListener('drop', (event) => {
        event.preventDefault();
        els.uploadArea.classList.remove('drag-over');
        this.selectFiles(event.dataTransfer.files);
      });

      els.fileInput?.addEventListener('change', (event) => {
        this.selectFiles(event.target.files);
      });
      els.clearBtn?.addEventListener('click', () => this.clearSelection());
      els.uploadBtn?.addEventListener('click', () => this.uploadSelectedFiles());

      this.clearSelection();
    },

    selectFiles(files) {
      state.selectedFiles = Array.from(files || []);

      if (!state.selectedFiles.length) {
        this.clearSelection();
        return;
      }

      setHTML(els.selectedFiles, renderSelectedFiles(state.selectedFiles));
      this.setControlsEnabled(true);
      clearMessage(els.uploadError);
      hide(els.uploadResults);
    },

    clearSelection() {
      if (els.fileInput) els.fileInput.value = '';
      state.selectedFiles = [];
      setHTML(els.selectedFiles, '');
      this.setControlsEnabled(false);
      clearMessage(els.uploadError);
      hide(els.loadingPanel);
      hide(els.uploadResults);
    },

    setControlsEnabled(enabled) {
      if (els.uploadBtn) els.uploadBtn.disabled = !enabled;
      if (els.clearBtn) els.clearBtn.disabled = !enabled;
    },

    async uploadSelectedFiles() {
      if (!state.selectedFiles.length) {
        showMessage(els.uploadError, 'Please select at least one file to upload.');
        return;
      }

      clearMessage(els.uploadError);
      setBusy(els.loadingPanel, true);
      this.setControlsEnabled(false);

      try {
        const data = await api.uploadDocuments(state.selectedFiles);
        this.renderResults(data);
      } catch (error) {
        showMessage(els.uploadError, error.message || 'Upload failed. Please try again.');
      } finally {
        setBusy(els.loadingPanel, false);
        this.setControlsEnabled(state.selectedFiles.length > 0);
      }
    },

    renderResults(data) {
      setHTML(els.uploadSummary, renderUploadSummary(data));
      show(els.uploadResults);
      hide(els.emptyState);
      metrics.refreshDocumentCount();
      documents.load();
    },
  };

  const documents = {
    init() {
      els.refreshDocumentsBtn?.addEventListener('click', () => this.load());
      els.documentsCategoryFilter?.addEventListener('change', (event) => {
        state.documentCategory = event.target.value || 'all';
        this.renderCurrent();
      });
      els.documentsList?.addEventListener('click', (event) => {
        const deleteBtn = event.target.closest('[data-delete-document]');
        if (deleteBtn) this.delete(deleteBtn.dataset.deleteDocument, deleteBtn.dataset.filename);
      });
    },

    async load({ clearStatus = true } = {}) {
      if (!els.documentsList) return;

      clearMessage(els.documentsError);
      if (clearStatus) clearMessage(els.documentsMessage);
      setBusy(els.documentsLoading, true);

      try {
        const data = await api.fetchDocuments();
        this.render(data);
      } catch (error) {
        showMessage(
          els.documentsError,
          error.message || 'Unable to load documents. Please try again.',
        );
      } finally {
        setBusy(els.documentsLoading, false);
      }
    },

    async delete(documentId, filename = 'this document') {
      if (!documentId) return;
      if (!window.confirm(`Delete "${filename}" from the app?`)) return;

      clearMessage(els.documentsError);
      clearMessage(els.documentsMessage);

      try {
        const data = await api.deleteDocument(documentId);
        basket.remove(documentId);
        await this.load({ clearStatus: false });
        showMessage(els.documentsMessage, data.message || 'Document deleted.');
        metrics.refreshDocumentCount();
      } catch (error) {
        showMessage(
          els.documentsError,
          error.message || 'Unable to delete document. Please try again.',
        );
      }
    },

    render(data) {
      state.documents = data.documents || [];
      this.renderCategoryOptions(state.documents);
      this.renderCurrent(data.total_documents);
    },

    renderCategoryOptions(list) {
      if (!els.documentsCategoryFilter) return;

      const categories = uniqueCategories(list);
      const currentCategory = categories.includes(state.documentCategory)
        ? state.documentCategory
        : 'all';
      state.documentCategory = currentCategory;

      setHTML(
        els.documentsCategoryFilter,
        `
          <option value="all">All categories</option>
          ${categories
            .map((category) => `
              <option value="${escapeHTML(category)}"${category === currentCategory ? ' selected' : ''}>
                ${escapeHTML(category)}
              </option>
            `)
            .join('')}
        `,
      );
    },

    renderCurrent(totalFromResponse) {
      const total = totalFromResponse || state.documents.length;
      const list = filterDocumentsByCategory(state.documents, state.documentCategory);
      setText(
        els.documentsListCount,
        state.documentCategory === 'all'
          ? `${total} document${total === 1 ? '' : 's'}`
          : `${list.length} of ${total} document${total === 1 ? '' : 's'}`,
      );

      if (!state.documents.length) {
        setHTML(els.documentsList, renderDocumentsEmpty('No uploaded documents found yet.'));
        return;
      }

      if (!list.length) {
        setHTML(els.documentsList, renderDocumentsEmpty('No documents found in this category.'));
        return;
      }

      setHTML(els.documentsList, renderDocumentsList(list));
    },
  };

  const search = {
    init() {
      els.searchBtn?.addEventListener('click', () => this.perform());
      els.searchInput?.addEventListener('input', (event) => {
        this.updateSuggestions(event.target.value);
      });
      els.searchInput?.addEventListener('keydown', (event) => {
        if (event.key !== 'Enter') return;
        event.preventDefault();
        this.perform();
      });

      els.suggestionsBox?.addEventListener('click', (event) => {
        const item = event.target.closest('.suggestion-item');
        if (!item || !els.searchInput) return;

        els.searchInput.value = item.textContent.trim();
        els.suggestionsBox.classList.remove('active');
        this.perform();
      });

      els.searchResults?.addEventListener('click', (event) => {
        const actionBtn = event.target.closest('[data-result-action]');
        if (actionBtn) this.handleResultAction(actionBtn);
      });

      document.addEventListener('click', (event) => {
        if (!event.target.closest('.search-dropdown')) {
          els.suggestionsBox?.classList.remove('active');
        }
      });
    },

    updateSuggestions(query) {
      const normalized = query.trim().toLowerCase();

      if (!normalized) {
        this.hideSuggestions();
        return;
      }

      const matches = state.keywordSuggestions
        .map((keyword) => String(keyword))
        .filter((keyword) => keyword.toLowerCase().includes(normalized))
        .slice(0, 8);

      if (!matches.length) {
        this.hideSuggestions();
        return;
      }

      setHTML(els.suggestionsBox, renderSuggestions(matches));
      els.suggestionsBox?.classList.add('active');
    },

    hideSuggestions() {
      setHTML(els.suggestionsBox, '');
      els.suggestionsBox?.classList.remove('active');
    },

    async perform() {
      const keyword = els.searchInput?.value.trim() || '';

      this.hideSuggestions();
      clearMessage(els.searchError);
      clearMessage(els.searchMessage);
      hide(els.searchResults);

      if (!keyword) {
        showMessage(
          els.searchError,
          'Please type a keyword or select one of the suggested terms.',
        );
        return;
      }

      setBusy(els.searchLoading, true);

      try {
        const data = await api.search(keyword);
        this.renderResults(data);
      } catch (error) {
        showMessage(
          els.searchError,
          error.message || 'Unable to perform search. Please try again.',
        );
      } finally {
        setBusy(els.searchLoading, false);
      }
    },

    renderResults(data) {
      if (!els.searchResults) return;

      const keyword = data.keyword || els.searchInput?.value.trim() || '';
      const results = data.all_results || [];

      if (!results.length) {
        setHTML(els.searchResults, renderEmptySearch(keyword));
        show(els.searchResults);
        return;
      }

      const sortedResults = [...results].sort(
        (a, b) => (b.keyword_count || 0) - (a.keyword_count || 0),
      );

      setHTML(els.searchResults, renderSearchResults(data, sortedResults, keyword));
      bindCollapsibleResults();
      show(els.searchResults);
    },

    async handleResultAction(actionBtn) {
      const documentId = actionBtn.dataset.documentId;
      const filename = actionBtn.dataset.filename || '';
      const action = actionBtn.dataset.resultAction;

      if (action === 'summary') {
        await this.showDocumentSummary(documentId);
      }

      if (action === 'basket') {
        basket.add(documentId, filename);
      }

      if (action === 'request') {
        await this.requestDocument(documentId);
      }
    },

    async showDocumentSummary(documentId) {
      try {
        const data = await api.fetchPreview(documentId);
        const summaryBox = document.getElementById(`summary-${documentId}`);

        if (!summaryBox) return;

        setHTML(summaryBox, renderSummary(data));
        summaryBox.classList.toggle('active');
      } catch (error) {
        showMessage(els.searchError, error.message || 'Unable to load summary.');
      }
    },

    async requestDocument(documentId) {
      clearMessage(els.searchError);

      try {
        const data = await api.requestDownload(
          documentId,
          els.searchInput?.value.trim() || '',
        );
        showMessage(els.searchMessage, data.message || 'Your request has been submitted.');
      } catch (error) {
        showMessage(
          els.searchError,
          error.message || 'Unable to request document. Please try again.',
        );
      }
    },
  };

  function renderBasketItem(item) {
    const documentId = escapeHTML(item.document_id);
    const filename = escapeHTML(item.filename);

    return `
      <div class="basket-item">
        <div>
          <strong>${filename}</strong>
          <span>ID ${documentId}</span>
        </div>
        <button type="button" class="basket-remove-btn" data-remove-basket="${documentId}" aria-label="Remove ${filename} from basket">
          <svg viewBox="0 0 24 24"><path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M19 6l-1 15H6L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/></svg>
        </button>
      </div>
    `;
  }

  function renderSelectedFiles(files) {
    const listItems = files.map((file) => `
      <li>
        <span>${escapeHTML(file.name)}</span>
        <span>${(file.size / 1024).toFixed(1)} KB</span>
      </li>
    `).join('');

    return `
      <div class="selected-files-box">
        <div class="selected-files-header">Selected files (${files.length})</div>
        <ul>${listItems}</ul>
      </div>
    `;
  }

  function renderUploadSummary(data) {
    const uploadedFiles = data.uploaded_files || [];
    const skippedFiles = data.skipped_files || [];
    const uploadedCount = data.uploaded_count || 0;
    const skippedCount = skippedFiles.length;

    return `
      <div class="result-card">
        <h4>${uploadedCount > 0 ? 'Upload complete' : 'Upload status'}</h4>
        <p>${uploadedCount} file${uploadedCount === 1 ? '' : 's'} uploaded successfully.</p>
        ${skippedCount > 0 ? `<p>${skippedCount} file${skippedCount === 1 ? '' : 's'} could not be processed.</p>` : ''}
        ${renderFileSummary('Uploaded', uploadedFiles)}
        ${renderFileSummary('Skipped files', skippedFiles)}
      </div>
    `;
  }

  function renderFileSummary(title, files) {
    if (!files.length) return '';

    return `
      <div class="result-summary">
        <div class="summary-item">
          <strong>${title}</strong>
          ${files.map((name) => `<div>${escapeHTML(name)}</div>`).join('')}
        </div>
      </div>
    `;
  }

  function renderSuggestions(matches) {
    return `
      <ul>
        ${matches.map((keyword) => `<li class="suggestion-item">${escapeHTML(keyword)}</li>`).join('')}
      </ul>
    `;
  }

  function renderEmptySearch(keyword) {
    return `
      <div class="empty-search">
        <p>No documents found containing <strong>${escapeHTML(keyword)}</strong>.</p>
        <p>Try searching for a different keyword.</p>
      </div>
    `;
  }

  function renderSearchResults(data, sortedResults, keyword) {
    const totalMatches = data.total_matches || sortedResults.length;
    const resultLimit = data.result_limit || 10;
    const topResult = sortedResults[0];
    const remainingResults = sortedResults.slice(1);

    return `
      <div class="search-results-header">
        <h3>Top ${Math.min(resultLimit, totalMatches)} of ${totalMatches} document${totalMatches === 1 ? '' : 's'} found for "${escapeHTML(keyword)}"</h3>
      </div>
      ${renderResultCard(topResult, true)}
      ${renderRemainingResults(remainingResults)}
    `;
  }

  function renderRemainingResults(results) {
    if (!results.length) return '';

    return `
      <div class="collapsible-results">
        <button type="button" id="other-results-toggle" class="collapsible-toggle">
          <span class="toggle-icon">+</span>
          ${results.length} remaining top match${results.length === 1 ? '' : 'es'} sorted by match count
        </button>

        <div id="other-results-list" class="collapsible-content" style="display: none;">
          ${results.map((item) => renderResultCard(item, false)).join('')}
        </div>
      </div>
    `;
  }

  function renderResultCard(item, isTopResult) {
    const documentId = escapeHTML(item.document_id);
    const filename = escapeHTML(item.filename);
    const category = escapeHTML(item.category || 'Uncategorized');
    const context = escapeHTML(item.context || 'No context available.');
    const keywordCount = item.keyword_count || 0;

    return `
      <div class="result-card ${isTopResult ? 'top-result' : ''}">
        ${isTopResult ? '<span class="top-badge">Top Result</span>' : ''}

        <h3>${filename}</h3>

        <p class="result-meta">
          ${keywordCount} ${keywordCount === 1 ? 'match' : 'matches'} | Category: ${category}
        </p>

        <p class="result-context">${context}</p>

        <div class="result-actions">
          <button type="button" data-result-action="summary" data-document-id="${documentId}" data-filename="${filename}">
            <svg viewBox="0 0 24 24"><path d="M6 3h8l5 5v13H6z"/><path d="M14 3v5h5"/><path d="M9 13h6"/><path d="M9 17h4"/></svg>
            Preview
          </button>

          <button type="button" data-result-action="basket" data-document-id="${documentId}" data-filename="${filename}">
            <svg viewBox="0 0 24 24"><path d="M6 6h15l-1.5 8.5H8L6 3H3"/><path d="M10 11h6"/></svg>
            Add to Basket
          </button>

          <button type="button" data-result-action="request" data-document-id="${documentId}" data-filename="${filename}">
            <svg viewBox="0 0 24 24"><path d="M22 2 11 13"/><path d="m22 2-7 20-4-9-9-4z"/></svg>
            Request
          </button>
        </div>

        <div id="summary-${documentId}" class="summary-box"></div>
      </div>
    `;
  }

  function renderSummary(data) {
    return `
      <strong>Summary</strong>
      <span class="summary-meta">${Number(data.source_character_count || 0).toLocaleString()} extracted characters read</span>
      <p>${escapeHTML(data.summary)}</p>
    `;
  }

  function uniqueCategories(items) {
    return [...new Set(
      items.map((item) => item.category || 'Uncategorized'),
    )].sort((a, b) => a.localeCompare(b));
  }

  function filterDocumentsByCategory(items, category) {
    if (!category || category === 'all') return items;
    return items.filter((item) => (item.category || 'Uncategorized') === category);
  }

  function renderDocumentsEmpty(message) {
    return `
      <div class="empty-state">
        <p>${escapeHTML(message)}</p>
      </div>
    `;
  }

  function renderDocumentsList(items) {
    return `
      <div class="documents-table" role="table" aria-label="Uploaded documents">
        <div class="documents-row documents-head" role="row">
          <div role="columnheader">Title</div>
          <div role="columnheader">Category</div>
          <div role="columnheader">Actions</div>
        </div>
        ${items.map(renderDocumentRow).join('')}
      </div>
    `;
  }

  function renderDocumentRow(item) {
    const documentId = escapeHTML(item.document_id);
    const title = escapeHTML(item.title || 'Untitled document');
    const category = escapeHTML(item.category || 'Uncategorized');

    return `
      <div class="documents-row" role="row">
        <div class="documents-title" role="cell">${title}</div>
        <div role="cell"><span class="pill">${category}</span></div>
        <div role="cell" class="documents-actions">
          <button type="button" class="document-delete-btn" data-delete-document="${documentId}" data-filename="${title}" aria-label="Delete ${title}" title="Delete">
            <svg viewBox="0 0 24 24"><path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M19 6l-1 15H6L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/></svg>
          </button>
        </div>
      </div>
    `;
  }

  function bindCollapsibleResults() {
    const toggleBtn = document.getElementById('other-results-toggle');
    const content = document.getElementById('other-results-list');

    if (!toggleBtn || !content) return;

    toggleBtn.addEventListener('click', () => {
      const isOpen = content.style.display !== 'none';
      content.style.display = isOpen ? 'none' : 'grid';

      const icon = toggleBtn.querySelector('.toggle-icon');
      if (icon) icon.textContent = isOpen ? '+' : '-';
    });
  }

  function init() {
    navigation.init();
    basket.init();
    upload.init();
    search.init();
    documents.init();

    hide(els.searchLoading);
    hide(els.searchError);
    hide(els.searchMessage);
    hide(els.uploadError);
    hide(els.searchResults);
    hide(els.uploadResults);
    hide(els.documentsLoading);
    hide(els.documentsError);
    hide(els.documentsMessage);

    metrics.refreshDocumentCount();
    documents.load();
  }

  init();
})();
