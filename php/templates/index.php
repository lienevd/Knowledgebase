<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>IBC Document Intelligence</title>
  <link rel="stylesheet" href="/static/style.css?v=17" />
</head>
<body>
  <div class="app-shell" id="app-shell">
    <aside class="sidebar" aria-label="Workspace sidebar">
      <div class="sidebar-top">
        <div class="brand-lockup">
          <div class="brand-mark" aria-hidden="true">
            <svg viewBox="0 0 24 24"><path d="M6 3h8l5 5v13H6z"/><path d="M14 3v5h5"/><path d="M9 13h6"/><path d="M9 17h4"/></svg>
          </div>
          <div class="brand-copy">
            <p class="brand-kicker">Document Intelligence</p>
            <h1 class="brand-title">IBC Analysis</h1>
          </div>
        </div>

        <button class="icon-btn sidebar-toggle" id="sidebar-toggle" type="button" aria-label="Collapse sidebar" aria-expanded="true">
          <svg viewBox="0 0 24 24"><path d="M15 18l-6-6 6-6"/></svg>
        </button>
      </div>

      <div class="user-card">
        <img src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 96 96'%3E%3Crect width='96' height='96' rx='48' fill='%23245b5a'/%3E%3Ccircle cx='48' cy='38' r='15' fill='white' opacity='.95'/%3E%3Cpath d='M22 78c4-17 18-25 26-25s22 8 26 25' fill='white' opacity='.95'/%3E%3C/svg%3E" alt="Profile picture" />
        <div class="user-copy">
          <strong>IBC User</strong>
          <span>Document reviewer</span>
        </div>
      </div>

      <nav class="navigation-section" aria-label="Sidebar navigation">
        <button class="nav-btn tab-link active" data-tab="upload-tab" type="button" title="Upload documents">
          <svg viewBox="0 0 24 24"><path d="M12 3v12"/><path d="M7 8l5-5 5 5"/><path d="M5 21h14"/></svg>
          <span class="nav-text">Upload</span>
        </button>
        <button class="nav-btn tab-link" data-tab="search-tab" type="button" title="Search documents">
          <svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/><path d="M20 20l-4.5-4.5"/></svg>
          <span class="nav-text">Search</span>
        </button>
        <button class="nav-btn tab-link" data-tab="documents-tab" type="button" title="View documents">
          <svg viewBox="0 0 24 24"><path d="M8 6h13"/><path d="M8 12h13"/><path d="M8 18h13"/><path d="M3 6h.01"/><path d="M3 12h.01"/><path d="M3 18h.01"/></svg>
          <span class="nav-text">Documents</span>
        </button>
        <button class="nav-btn tab-link" data-tab="settings-tab" type="button" title="Settings">
          <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .34 1.88l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.7 1.7 0 0 0-1.88-.34 1.7 1.7 0 0 0-1 1.55V21a2 2 0 1 1-4 0v-.09a1.7 1.7 0 0 0-1-1.55 1.7 1.7 0 0 0-1.88.34l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.7 1.7 0 0 0 4.6 15a1.7 1.7 0 0 0-1.55-1H3a2 2 0 1 1 0-4h.09a1.7 1.7 0 0 0 1.55-1 1.7 1.7 0 0 0-.34-1.88l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.7 1.7 0 0 0 9 4.6a1.7 1.7 0 0 0 1-1.55V3a2 2 0 1 1 4 0v.09a1.7 1.7 0 0 0 1 1.55 1.7 1.7 0 0 0 1.88-.34l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.7 1.7 0 0 0 19.4 9a1.7 1.7 0 0 0 1.55 1H21a2 2 0 1 1 0 4h-.09a1.7 1.7 0 0 0-1.51 1z"/></svg>
          <span class="nav-text">Settings</span>
        </button>
      </nav>

      <footer class="sidebar-footer">
        <div class="mini-metrics">
          <div>
            <span>Documents</span>
            <strong id="doc-count">0</strong>
          </div>
          <div>
            <span>Keywords</span>
            <strong id="keyword-count"><?= count($keywords) ?></strong>
          </div>
        </div>
      </footer>
    </aside>

    <main class="main-panel">
      <header class="topbar">
        <nav class="top-nav" aria-label="Primary navigation">
          <button class="top-nav-link tab-link active" data-tab="upload-tab" type="button">
            <svg viewBox="0 0 24 24"><path d="M12 3v12"/><path d="M7 8l5-5 5 5"/><path d="M5 21h14"/></svg>
            Upload
          </button>
          <button class="top-nav-link tab-link" data-tab="search-tab" type="button">
            <svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/><path d="M20 20l-4.5-4.5"/></svg>
            Search
          </button>
          <button class="top-nav-link tab-link" data-tab="documents-tab" type="button">
            <svg viewBox="0 0 24 24"><path d="M8 6h13"/><path d="M8 12h13"/><path d="M8 18h13"/><path d="M3 6h.01"/><path d="M3 12h.01"/><path d="M3 18h.01"/></svg>
            Documents
          </button>
        </nav>

        <button class="basket-trigger" id="basket-trigger" type="button" aria-haspopup="dialog" aria-controls="basket-drawer">
          <svg viewBox="0 0 24 24"><path d="M6 6h15l-1.5 8.5H8L6 3H3"/><circle cx="9" cy="20" r="1"/><circle cx="18" cy="20" r="1"/></svg>
          Basket
          <span class="basket-count" data-basket-count>0</span>
        </button>
      </header>

      <div class="main-banner">
        <div class="banner-copy">
          <p class="eyebrow">Compliance workspace</p>
          <h2>Review documents, find keyword evidence, and request files from one focused workspace.</h2>
        </div>
      </div>

      <div id="upload-tab" class="tab-content active">
        <header class="page-header">
          <h1>Upload Documents</h1>
          <p class="page-subtitle">Add source files to the library for classification and keyword analysis.</p>
        </header>

        <div class="upload-container">
          <div class="upload-area" id="upload-area">
            <div class="upload-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24"><path d="M12 3v12"/><path d="M7 8l5-5 5 5"/><path d="M5 21h14"/></svg>
            </div>
            <h2 class="upload-title">Select documents</h2>
            <p class="upload-subtitle">PDF, Word, text, Markdown, and HTML files are supported.</p>
            <div class="file-types" aria-label="Supported file types">
              <span>.pdf</span>
              <span>.docx</span>
              <span>.txt</span>
              <span>.md</span>
              <span>.html</span>
            </div>
            <input id="file-input" type="file" accept=".pdf,.doc,.docx,.txt,.md,.html,.htm" multiple />
          </div>

          <div id="selected-files"></div>

          <div class="button-group">
            <button class="btn-primary" id="upload-btn" disabled>Upload Documents</button>
            <button class="btn-secondary" id="clear-btn">Clear</button>
          </div>

          <div class="loading" id="loading" hidden>
            <div class="spinner"></div>
            <p>Processing documents...</p>
          </div>

          <div class="error" id="error"></div>
          <div class="results" id="results"><div id="upload-summary"></div></div>

          <div class="empty-state" id="empty-state">
            <p>Your uploaded documents will appear here after processing.</p>
          </div>
        </div>
      </div>

      <div id="search-tab" class="tab-content">
        <header class="page-header">
          <h1>Search Keywords</h1>
          <p class="page-subtitle">Search indexed documents and add useful matches to your request basket.</p>
        </header>

        <div class="search-container">
          <div class="search-card">
            <label for="search-input" class="search-label">Search Keyword</label>
            <div class="search-input-group">
              <div class="search-dropdown">
                <input id="search-input" type="text" placeholder="Enter a keyword" autocomplete="off" />
                <div id="search-suggestions" class="suggestions"></div>
              </div>
              <button class="btn-primary" id="search-btn">Search</button>
            </div>
            <div class="search-hint">Common examples: <?= $keywordHint ?></div>
            <div id="search-message" class="message message-success" hidden></div>
          </div>

          <div class="loading" id="search-loading" hidden>
            <div class="spinner"></div>
            <p>Searching documents...</p>
          </div>

          <div class="error" id="search-error"></div>
          <div id="search-results-container"></div>
        </div>
      </div>

      <div id="documents-tab" class="tab-content">
        <header class="page-header">
          <h1>Documents</h1>
          <p class="page-subtitle">Browse uploaded documents and their assigned categories.</p>
        </header>

        <div class="documents-container">
          <div class="documents-toolbar">
            <div>
              <span class="documents-count" id="documents-list-count">0 documents</span>
            </div>
            <label class="documents-filter">
              <span>Category</span>
              <select id="documents-category-filter">
                <option value="all">All categories</option>
              </select>
            </label>
            <button class="btn-secondary" id="refresh-documents-btn" type="button">Refresh</button>
          </div>

          <div class="loading" id="documents-loading" hidden>
            <div class="spinner"></div>
            <p>Loading documents...</p>
          </div>

          <div class="error" id="documents-error"></div>
          <div class="message message-success" id="documents-message" hidden></div>
          <div id="documents-list" class="documents-list"></div>
        </div>
      </div>

      <div id="settings-tab" class="tab-content">
        <header class="page-header">
          <h1>Settings</h1>
          <p class="page-subtitle">Manage workspace preferences and request defaults.</p>
        </header>

        <section class="settings-grid">
          <div class="settings-panel">
            <h2>Profile</h2>
            <label>
              Display name
              <input type="text" value="IBC User" />
            </label>
            <label>
              Role
              <input type="text" value="Document reviewer" />
            </label>
          </div>
          <div class="settings-panel">
            <h2>Requests</h2>
            <label>
              Request owner
              <input id="request-owner-email" type="email" value="<?= htmlspecialchars($requestOwnerEmail, ENT_QUOTES, 'UTF-8') ?>" />
            </label>
            <label class="toggle-row">
              <input type="checkbox" checked />
              Include keyword context in basket checkout
            </label>
          </div>
        </section>
      </div>
    </main>
  </div>

  <div class="drawer-overlay" id="drawer-overlay" hidden></div>
  <aside class="basket-drawer" id="basket-drawer" role="dialog" aria-modal="true" aria-labelledby="basket-title" hidden>
    <header class="drawer-header">
      <div>
        <p class="eyebrow">Request basket</p>
        <h2 id="basket-title">Selected documents</h2>
      </div>
      <button class="icon-btn" id="basket-close" type="button" aria-label="Close basket">
        <svg viewBox="0 0 24 24"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
      </button>
    </header>

    <div class="drawer-summary">
      <span data-basket-count>0</span>
      <p>documents ready to request</p>
    </div>

    <div id="basket-list" class="basket-list">
      <p class="basket-empty">No documents selected yet.</p>
    </div>

    <div class="request-details" id="basket-request-details" hidden>
      <label class="request-message-field" for="requester-email">
        Your email
        <input id="requester-email" type="email" placeholder="you@example.com" autocomplete="email" />
      </label>

      <label class="request-message-field drawer-request-message" for="basket-request-message">
        Message to admin <span>optional</span>
        <textarea id="basket-request-message" rows="4" placeholder="Tell the admin what you need the documents for"></textarea>
      </label>
    </div>

    <footer class="drawer-footer">
      <button id="clear-basket-btn" class="btn-secondary" type="button" disabled>Clear Basket</button>
      <button id="request-basket-btn" class="btn-primary" type="button" disabled>Checkout</button>
    </footer>
  </aside>

  <script>
    window.KEYWORD_SUGGESTIONS = <?= json_encode($keywords) ?> || [];
    window.DEFAULT_REQUEST_OWNER_EMAIL = <?= json_encode($requestOwnerEmail) ?>;
  </script>
  <script src="/static/app.js?v=17"></script>
</body>
</html>
