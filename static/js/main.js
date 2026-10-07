/**
 * PyShort - Main Client-Side Logic & PWA Controller
 * Pure Vanilla JavaScript for interactivity, clipboard, QR modal, AJAX updates, and PWA integration.
 */

document.addEventListener('DOMContentLoaded', () => {
    // Flag body that JS is active for progressive tab layout
    document.body.classList.add('js-ready');

    // DOM Elements - Core Shortener
    const shortenForm = document.getElementById('shorten-form');
    const longUrlInput = document.getElementById('long-url-input');
    const aliasToggleBtn = document.getElementById('alias-toggle-btn');
    const aliasWrapper = document.getElementById('alias-wrapper');
    const customAliasInput = document.getElementById('custom-alias-input');
    const submitBtn = document.getElementById('submit-btn');

    // Result card elements
    const resultCard = document.getElementById('result-card');
    const resultShortUrl = document.getElementById('result-short-url');
    const resultOriginalUrl = document.getElementById('result-original-url');
    const resultStatusText = document.getElementById('result-status-text');
    const resultCopyBtn = document.getElementById('result-copy-btn');
    const resultQrBtn = document.getElementById('result-qr-btn');
    const resultVisitBtn = document.getElementById('result-visit-btn');

    // Stats elements
    const statTotalUrls = document.getElementById('stat-total-urls');
    const statTotalClicks = document.getElementById('stat-total-clicks');
    const statAvgClicks = document.getElementById('stat-avg-clicks');
    const statTopLink = document.getElementById('stat-top-link');
    const refreshStatsBtn = document.getElementById('refresh-stats-btn');
    const homeMetricUrls = document.getElementById('home-metric-urls');
    const homeMetricClicks = document.getElementById('home-metric-clicks');

    // Table & Pagination elements
    const urlsTableBody = document.getElementById('urls-table-body');
    const emptyState = document.getElementById('empty-state');
    const searchInput = document.getElementById('search-input');
    const paginationControls = document.getElementById('pagination-controls');
    const currentPageNum = document.getElementById('current-page-num');
    const totalPagesNum = document.getElementById('total-pages-num');
    const totalUrlsCount = document.getElementById('total-urls-count');
    const prevPageBtn = document.getElementById('prev-page-btn');
    const nextPageBtn = document.getElementById('next-page-btn');

    let currentPage = parseInt(paginationControls?.getAttribute('data-page') || '1', 10);
    let totalPages = parseInt(paginationControls?.getAttribute('data-total-pages') || '1', 10);
    const perPage = parseInt(paginationControls?.getAttribute('data-per-page') || '25', 10);

    // QR Modal elements
    const qrModal = document.getElementById('qr-modal');
    const qrModalClose = document.getElementById('qr-modal-close');
    const qrModalUrl = document.getElementById('qr-modal-url');
    const qrImage = document.getElementById('qr-image');
    const qrDownloadBtn = document.getElementById('qr-download-btn');
    const qrCopyBtn = document.getElementById('qr-copy-btn');

    // Theme toggles
    const themeToggle = document.getElementById('theme-toggle');
    const themeBtnDark = document.getElementById('theme-btn-dark');
    const themeBtnLight = document.getElementById('theme-btn-light');
    const metaThemeColor = document.getElementById('meta-theme-color');

    // PWA & Navigation elements
    const appViews = document.querySelectorAll('.app-view');
    const bottomNavItems = document.querySelectorAll('.bottom-nav-item');
    const desktopNavLinks = document.querySelectorAll('#desktop-nav .nav-link');
    const tabTriggers = document.querySelectorAll('[data-tab-target]');
    const headerInstallBtn = document.getElementById('header-install-btn');
    const settingsInstallBtn = document.getElementById('settings-install-btn');
    const pwaStatusText = document.getElementById('pwa-status-text');
    const pwaStatusDesc = document.getElementById('pwa-status-desc');
    const pwaIndicatorDot = document.getElementById('pwa-indicator-dot');
    const offlineBanner = document.getElementById('offline-banner');
    const swStatusLabel = document.getElementById('sw-status-label');

    let deferredPrompt = null;
    let currentQrLink = '';

    // =========================================================================
    // Theme Management (Dark / Light)
    // =========================================================================
    function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('pyshort-theme', theme);

        if (metaThemeColor) {
            metaThemeColor.setAttribute('content', theme === 'dark' ? '#0b0f19' : '#f8fafc');
        }

        if (themeBtnDark && themeBtnLight) {
            if (theme === 'dark') {
                themeBtnDark.classList.add('active');
                themeBtnLight.classList.remove('active');
            } else {
                themeBtnLight.classList.add('active');
                themeBtnDark.classList.remove('active');
            }
        }
    }

    function initTheme() {
        const savedTheme = localStorage.getItem('pyshort-theme') || 'dark';
        applyTheme(savedTheme);
    }

    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
            const nextTheme = currentTheme === 'dark' ? 'light' : 'dark';
            applyTheme(nextTheme);
            showToast(`Switched to ${nextTheme} mode`, 'info');
        });
    }

    if (themeBtnDark) {
        themeBtnDark.addEventListener('click', () => {
            applyTheme('dark');
            showToast('Dark mode enabled', 'info');
        });
    }

    if (themeBtnLight) {
        themeBtnLight.addEventListener('click', () => {
            applyTheme('light');
            showToast('Light mode enabled', 'info');
        });
    }

    initTheme();

    // =========================================================================
    // App View Navigation & Tab Switching
    // =========================================================================
    function switchTab(targetTab) {
        const normalizedTab = (targetTab || 'home').toLowerCase();
        let targetViewId = 'view-home';

        if (normalizedTab === 'links' || normalizedTab === 'recent') {
            targetViewId = 'view-links';
        } else if (normalizedTab === 'analytics' || normalizedTab === 'dashboard') {
            targetViewId = 'view-analytics';
        } else if (normalizedTab === 'settings') {
            targetViewId = 'view-settings';
        } else {
            targetViewId = 'view-home';
        }

        const activeKey = targetViewId.replace('view-', '');

        // Update view visibility
        appViews.forEach((view) => {
            if (view.id === targetViewId) {
                view.classList.add('active');
                view.removeAttribute('hidden');
            } else {
                view.classList.remove('active');
            }
        });

        // Update Mobile Bottom Nav
        bottomNavItems.forEach((btn) => {
            const tabTarget = btn.getAttribute('data-tab-target');
            if (tabTarget === activeKey) {
                btn.classList.add('active');
                btn.setAttribute('aria-current', 'page');
            } else {
                btn.classList.remove('active');
                btn.removeAttribute('aria-current');
            }
        });

        // Update Desktop Nav
        desktopNavLinks.forEach((link) => {
            const tabTarget = link.getAttribute('data-tab-target');
            if (tabTarget === activeKey) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });

        // Update location hash without page reload
        if (window.location.hash !== `#${activeKey}`) {
            history.replaceState(null, '', `#${activeKey}`);
        }

        // Scroll to top of content for seamless app feel
        window.scrollTo({ top: 0, behavior: 'instant' });
    }

    // Attach click listeners to all tab target elements
    tabTriggers.forEach((trigger) => {
        trigger.addEventListener('click', (e) => {
            const target = trigger.getAttribute('data-tab-target');
            if (target) {
                e.preventDefault();
                switchTab(target);
            }
        });
    });

    // Handle hash on initial load & history navigation
    function handleHashChange() {
        const hash = window.location.hash.replace('#', '').trim();
        if (hash) {
            switchTab(hash);
        } else {
            switchTab('home');
        }
    }

    window.addEventListener('hashchange', handleHashChange);
    handleHashChange();

    // =========================================================================
    // Custom Alias Accordion
    // =========================================================================
    if (aliasToggleBtn && aliasWrapper) {
        aliasToggleBtn.addEventListener('click', () => {
            const isHidden = aliasWrapper.classList.contains('hidden');
            if (isHidden) {
                aliasWrapper.classList.remove('hidden');
                aliasToggleBtn.classList.add('open');
                aliasToggleBtn.setAttribute('aria-expanded', 'true');
                customAliasInput.focus();
            } else {
                aliasWrapper.classList.add('hidden');
                aliasToggleBtn.classList.remove('open');
                aliasToggleBtn.setAttribute('aria-expanded', 'false');
            }
        });
    }

    // =========================================================================
    // Shorten URL Form Submission
    // =========================================================================
    if (shortenForm) {
        shortenForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const rawUrl = longUrlInput.value.trim();
            const customAlias = customAliasInput.value.trim();

            if (!rawUrl) {
                showToast('Please enter a URL to shorten.', 'error');
                longUrlInput.focus();
                return;
            }

            // Set loading state
            setLoading(true);

            try {
                const response = await fetch('/api/shorten', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify({
                        url: rawUrl,
                        custom_alias: customAlias
                    })
                });

                const data = await response.json();

                if (!response.ok || !data.success) {
                    throw new Error(data.error || 'Failed to shorten URL.');
                }

                // Show success result card
                displayResult(data);

                // Add or update recent link in table
                if (!data.reused) {
                    prependTableRow(data);
                }

                // Update analytics
                updateAnalytics();

                // Clear or reset fields
                customAliasInput.value = '';
                if (aliasWrapper && !aliasWrapper.classList.contains('hidden')) {
                    aliasWrapper.classList.add('hidden');
                    aliasToggleBtn.classList.remove('open');
                    aliasToggleBtn.setAttribute('aria-expanded', 'false');
                }

                showToast(data.message || 'URL successfully shortened!', 'success');

                // Smooth scroll to result
                resultCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

            } catch (err) {
                showToast(err.message, 'error');
            } finally {
                setLoading(false);
            }
        });
    }

    function setLoading(isLoading) {
        if (!submitBtn) return;
        if (isLoading) {
            submitBtn.classList.add('is-loading');
            submitBtn.disabled = true;
        } else {
            submitBtn.classList.remove('is-loading');
            submitBtn.disabled = false;
        }
    }

    function displayResult(data) {
        if (!resultCard) return;

        resultShortUrl.textContent = data.short_url;
        resultShortUrl.href = data.short_url;

        resultOriginalUrl.textContent = data.original_url;
        resultOriginalUrl.title = data.original_url;

        resultVisitBtn.href = data.short_url;

        if (data.reused) {
            resultStatusText.textContent = 'Existing Short URL Found!';
        } else {
            resultStatusText.textContent = 'Your Short Link is Ready!';
        }

        currentQrLink = data.short_url;

        resultCard.classList.remove('hidden');

        // Setup copy action for result card
        resultCopyBtn.onclick = () => copyShortUrl(data.short_url, resultCopyBtn);

        // Setup QR modal trigger for result card
        resultQrBtn.onclick = () => openQrModal(data.short_code, data.short_url);
    }

    // =========================================================================
    // Table Row & Pagination Operations
    // =========================================================================
    function prependTableRow(item) {
        if (emptyState) emptyState.classList.add('hidden');
        if (!urlsTableBody) return;

        const dateStr = (item.created_at || '').substring(0, 10) || 'Today';
        const tr = document.createElement('tr');
        tr.id = `row-${item.id || item.short_code}`;
        tr.setAttribute('data-search', `${item.short_code} ${item.original_url}`);

        tr.innerHTML = `
            <td>
                <div class="cell-short-link">
                    <a href="/${item.short_code}" target="_blank" rel="noopener noreferrer" class="link-primary" id="short-link-${item.id || item.short_code}">
                        ${item.short_url}
                    </a>
                    ${item.is_custom ? '<span class="badge badge-custom" title="Custom alias">Custom</span>' : ''}
                </div>
            </td>
            <td>
                <div class="cell-original-url">
                    <a href="${escapeHtml(item.original_url)}" target="_blank" rel="noopener noreferrer" class="link-secondary truncate" title="${escapeHtml(item.original_url)}">
                        ${escapeHtml(item.original_url)}
                    </a>
                </div>
            </td>
            <td>
                <span class="clicks-badge">
                    <span class="dot"></span>
                    <span id="clicks-count-${item.id || item.short_code}">${item.clicks || 0}</span>
                </span>
            </td>
            <td>
                <span class="cell-date">${dateStr}</span>
            </td>
            <td style="text-align: right;">
                <div class="action-buttons-group">
                    <button type="button" class="btn-table-action" onclick="copyShortUrl('${item.short_url}', this)" title="Copy short URL" aria-label="Copy short link">
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
                    </button>
                    <button type="button" class="btn-table-action" onclick="openQrModal('${item.short_code}', '${item.short_url}')" title="Show QR code" aria-label="View QR code">
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
                    </button>
                    <a href="/${item.short_code}" target="_blank" rel="noopener noreferrer" class="btn-table-action" title="Open and test redirect" aria-label="Visit link">
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
                    </a>
                    <button type="button" class="btn-table-action btn-delete" onclick="deleteLink(${item.id})" title="Delete link" aria-label="Delete link">
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                    </button>
                </div>
            </td>
        `;

        urlsTableBody.insertBefore(tr, urlsTableBody.firstChild);

        if (totalUrlsCount) {
            const count = parseInt(totalUrlsCount.textContent || '0', 10);
            totalUrlsCount.textContent = count + 1;
        }
    }

    function updatePaginationUI(pagination) {
        if (!pagination || !paginationControls) return;
        currentPage = pagination.page;
        totalPages = pagination.total_pages;

        paginationControls.setAttribute('data-page', currentPage);
        paginationControls.setAttribute('data-total-pages', totalPages);

        if (currentPageNum) currentPageNum.textContent = currentPage;
        if (totalPagesNum) totalPagesNum.textContent = totalPages;
        if (totalUrlsCount) totalUrlsCount.textContent = pagination.total_count;

        if (prevPageBtn) prevPageBtn.disabled = !pagination.has_prev;
        if (nextPageBtn) nextPageBtn.disabled = !pagination.has_next;
    }

    async function loadPage(page) {
        try {
            const res = await fetch(`/api/links?page=${page}&per_page=${perPage}`);
            const data = await res.json();
            if (data.success && data.links) {
                if (!urlsTableBody) return;
                urlsTableBody.innerHTML = '';
                for (let i = data.links.length - 1; i >= 0; i--) {
                    prependTableRow(data.links[i]);
                }
                if (data.pagination) {
                    updatePaginationUI(data.pagination);
                }
                if (searchInput && searchInput.value.trim()) {
                    filterTableRows(searchInput.value.toLowerCase().trim());
                }
            }
        } catch (e) {
            console.error('Failed to load page:', e);
            showToast('Failed to load page links', 'error');
        }
    }

    if (prevPageBtn) {
        prevPageBtn.addEventListener('click', () => {
            if (currentPage > 1) {
                loadPage(currentPage - 1);
            }
        });
    }

    if (nextPageBtn) {
        nextPageBtn.addEventListener('click', () => {
            if (currentPage < totalPages) {
                loadPage(currentPage + 1);
            }
        });
    }

    // =========================================================================
    // Analytics Refresh
    // =========================================================================
    async function updateAnalytics() {
        try {
            const res = await fetch('/api/stats');
            const data = await res.json();
            if (data.success && data.stats) {
                const s = data.stats;
                if (statTotalUrls) statTotalUrls.textContent = s.total_urls;
                if (statTotalClicks) statTotalClicks.textContent = s.total_clicks;
                if (statAvgClicks) statAvgClicks.textContent = s.avg_clicks;
                if (homeMetricUrls) homeMetricUrls.textContent = s.total_urls;
                if (homeMetricClicks) homeMetricClicks.textContent = s.total_clicks;
                if (statTopLink) {
                    if (s.most_active) {
                        statTopLink.textContent = `${s.most_active.clicks} clicks (${s.most_active.short_code})`;
                    } else {
                        statTopLink.textContent = 'No clicks yet';
                    }
                }
            }
        } catch (e) {
            console.error('Failed to update stats:', e);
        }
    }

    if (refreshStatsBtn) {
        refreshStatsBtn.addEventListener('click', async () => {
            refreshStatsBtn.classList.add('is-loading');
            await updateAnalytics();
            setTimeout(() => {
                refreshStatsBtn.classList.remove('is-loading');
                showToast('Analytics refreshed', 'info');
            }, 300);
        });
    }

    // =========================================================================
    // Search / Filter Logic
    // =========================================================================
    function filterTableRows(query) {
        const rows = urlsTableBody ? urlsTableBody.querySelectorAll('tr') : [];
        let visibleCount = 0;

        rows.forEach((row) => {
            const searchData = (row.getAttribute('data-search') || '').toLowerCase();
            if (searchData.includes(query)) {
                row.style.display = '';
                visibleCount++;
            } else {
                row.style.display = 'none';
            }
        });

        if (emptyState) {
            if (visibleCount === 0 && rows.length > 0) {
                emptyState.classList.remove('hidden');
                emptyState.querySelector('h3').textContent = 'No Matching Links';
                emptyState.querySelector('p').textContent = 'Try searching with a different keyword or short code.';
            } else if (rows.length === 0) {
                emptyState.classList.remove('hidden');
                emptyState.querySelector('h3').textContent = 'No Shortened URLs Yet';
                emptyState.querySelector('p').textContent = 'Paste a link on the Home screen to generate your first trackable short URL!';
            } else {
                emptyState.classList.add('hidden');
            }
        }
    }

    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            filterTableRows(e.target.value.toLowerCase().trim());
        });
    }

    // =========================================================================
    // QR Code Modal Controls
    // =========================================================================
    window.openQrModal = function(shortCode, fullUrl) {
        if (!qrModal) return;
        currentQrLink = fullUrl;
        qrModalUrl.textContent = fullUrl;

        const qrEndpoint = `/qr/${shortCode}`;
        qrImage.src = qrEndpoint;
        qrDownloadBtn.href = qrEndpoint;
        qrDownloadBtn.setAttribute('download', `pyshort-${shortCode}.png`);

        qrCopyBtn.onclick = () => copyShortUrl(fullUrl, qrCopyBtn);

        qrModal.classList.add('open');
        qrModal.setAttribute('aria-hidden', 'false');
    };

    function closeQrModal() {
        if (!qrModal) return;
        qrModal.classList.remove('open');
        qrModal.setAttribute('aria-hidden', 'true');
    }

    if (qrModalClose) {
        qrModalClose.addEventListener('click', closeQrModal);
    }

    if (qrModal) {
        qrModal.addEventListener('click', (e) => {
            if (e.target === qrModal) {
                closeQrModal();
            }
        });
    }

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && qrModal && qrModal.classList.contains('open')) {
            closeQrModal();
        }
    });

    // =========================================================================
    // Clipboard Copy Helper
    // =========================================================================
    window.copyShortUrl = async function(text, triggerBtn) {
        try {
            if (navigator.clipboard && window.isSecureContext) {
                await navigator.clipboard.writeText(text);
            } else {
                // Fallback for non-HTTPS or older environments
                const textarea = document.createElement('textarea');
                textarea.value = text;
                textarea.style.position = 'fixed';
                textarea.style.opacity = '0';
                document.body.appendChild(textarea);
                textarea.select();
                document.execCommand('copy');
                document.body.removeChild(textarea);
            }

            showToast('Short URL copied to clipboard!', 'success');

            // Quick button visual feedback if button passed
            if (triggerBtn) {
                const originalHtml = triggerBtn.innerHTML;
                triggerBtn.style.borderColor = 'var(--success)';
                setTimeout(() => {
                    triggerBtn.innerHTML = originalHtml;
                    triggerBtn.style.borderColor = '';
                }, 1200);
            }
        } catch (err) {
            console.error('Copy failed: ', err);
            showToast('Failed to copy. Please select and copy manually.', 'error');
        }
    };

    // =========================================================================
    // Delete Link
    // =========================================================================
    window.deleteLink = async function(urlId) {
        if (!confirm('Are you sure you want to delete this short link? Any future clicks will fail.')) {
            return;
        }

        try {
            const res = await fetch(`/api/links/${urlId}`, {
                method: 'DELETE',
                headers: { 'Accept': 'application/json' }
            });
            const data = await res.json();

            if (!res.ok || !data.success) {
                throw new Error(data.error || 'Failed to delete URL.');
            }

            // Remove from DOM
            const row = document.getElementById(`row-${urlId}`);
            if (row) {
                row.style.opacity = '0';
                row.style.transform = 'translateX(20px)';
                setTimeout(() => {
                    row.remove();
                    if (totalUrlsCount) {
                        const count = parseInt(totalUrlsCount.textContent || '0', 10);
                        if (count > 0) totalUrlsCount.textContent = count - 1;
                    }
                    const remainingRows = urlsTableBody ? urlsTableBody.querySelectorAll('tr').length : 0;
                    if (remainingRows === 0) {
                        if (currentPage > 1) {
                            loadPage(currentPage - 1);
                        } else if (emptyState) {
                            emptyState.classList.remove('hidden');
                        }
                    }
                }, 200);
            }

            showToast('Short link deleted.', 'info');
            updateAnalytics();
        } catch (err) {
            showToast(err.message, 'error');
        }
    };

    // =========================================================================
    // PWA Service Worker & Install Prompt Logic
    // =========================================================================
    // 1. Service Worker Registration
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
            navigator.serviceWorker.register('/sw.js')
                .then((reg) => {
                    console.log('[PyShort PWA] Service Worker registered:', reg.scope);
                    if (swStatusLabel) {
                        swStatusLabel.textContent = 'Active & Caching Shell';
                    }
                })
                .catch((err) => {
                    console.warn('[PyShort PWA] Service Worker registration failed:', err);
                    if (swStatusLabel) {
                        swStatusLabel.textContent = 'Registration bypassed';
                    }
                });
        });
    }

    // 2. Detect Standalone / Installed mode
    function isStandaloneMode() {
        return (
            window.matchMedia('(display-mode: standalone)').matches ||
            window.matchMedia('(display-mode: window-controls-overlay)').matches ||
            window.navigator.standalone === true
        );
    }

    function updatePwaInstallationUI() {
        const isInstalled = isStandaloneMode();
        if (pwaStatusText && pwaIndicatorDot) {
            if (isInstalled) {
                pwaStatusText.textContent = 'Installed as Standalone App';
                pwaIndicatorDot.className = 'status-indicator-dot dot-active';
                if (pwaStatusDesc) {
                    pwaStatusDesc.textContent = 'PyShort is running in full native-like standalone window mode.';
                }
                if (headerInstallBtn) headerInstallBtn.classList.add('hidden');
                if (settingsInstallBtn) settingsInstallBtn.classList.add('hidden');
            } else {
                pwaStatusText.textContent = deferredPrompt ? 'Ready to Install' : 'Running in Web Browser';
                pwaIndicatorDot.className = 'status-indicator-dot dot-idle';
            }
        }
    }

    updatePwaInstallationUI();

    // 3. Handle beforeinstallprompt event
    window.addEventListener('beforeinstallprompt', (e) => {
        // Prevent Chrome mini-infobar
        e.preventDefault();
        deferredPrompt = e;

        // Show install buttons
        if (headerInstallBtn) headerInstallBtn.classList.remove('hidden');
        if (settingsInstallBtn) settingsInstallBtn.classList.remove('hidden');

        updatePwaInstallationUI();
    });

    async function triggerInstallFlow() {
        if (!deferredPrompt) {
            showToast('To install, use browser menu and select "Add to Home Screen"', 'info');
            return;
        }

        deferredPrompt.prompt();
        const choiceResult = await deferredPrompt.userChoice;
        if (choiceResult.outcome === 'accepted') {
            showToast('Installing PyShort app...', 'success');
        }
        deferredPrompt = null;
        if (headerInstallBtn) headerInstallBtn.classList.add('hidden');
        if (settingsInstallBtn) settingsInstallBtn.classList.add('hidden');
        updatePwaInstallationUI();
    }

    if (headerInstallBtn) {
        headerInstallBtn.addEventListener('click', triggerInstallFlow);
    }

    if (settingsInstallBtn) {
        settingsInstallBtn.addEventListener('click', triggerInstallFlow);
    }

    window.addEventListener('appinstalled', () => {
        deferredPrompt = null;
        if (headerInstallBtn) headerInstallBtn.classList.add('hidden');
        if (settingsInstallBtn) settingsInstallBtn.classList.add('hidden');
        updatePwaInstallationUI();
        showToast('PyShort was successfully installed!', 'success');
    });

    // 4. Offline / Online Connectivity Listeners
    window.addEventListener('online', () => {
        if (offlineBanner) offlineBanner.classList.add('hidden');
        showToast('Internet connection restored', 'success');
        updateAnalytics();
    });

    window.addEventListener('offline', () => {
        if (offlineBanner) offlineBanner.classList.remove('hidden');
        showToast('You are currently offline', 'info');
    });

    if (!navigator.onLine && offlineBanner) {
        offlineBanner.classList.remove('hidden');
    }

    // =========================================================================
    // Toast Notification System
    // =========================================================================
    window.showToast = function(message, type = 'info') {
        const container = document.getElementById('toast-container');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;

        let icon = 'ℹ️';
        if (type === 'success') icon = '✓';
        if (type === 'error') icon = '⚠️';

        toast.innerHTML = `
            <span class="toast-icon">${icon}</span>
            <span class="toast-message">${escapeHtml(message)}</span>
        `;

        container.appendChild(toast);

        // Auto remove after 3.2 seconds
        setTimeout(() => {
            toast.classList.add('toast-exit');
            setTimeout(() => toast.remove(), 250);
        }, 3200);
    };

    function escapeHtml(text) {
        if (!text) return '';
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }
});
