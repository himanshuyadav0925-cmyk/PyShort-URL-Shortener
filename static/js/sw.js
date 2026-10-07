/**
 * PyShort - Safe PWA Service Worker
 * Ensures reliable offline shell while strictly bypassing all dynamic URL shortener APIs and redirects.
 */

const CACHE_NAME = 'pyshort-v1';

// Static App Shell assets to cache
const PRECACHE_ASSETS = [
    '/',
    '/static/css/style.css',
    '/static/js/main.js',
    '/static/manifest.json',
    '/static/icons/icon-192.png',
    '/static/icons/icon-512.png',
    '/static/icons/icon-maskable.png',
    '/static/icons/apple-touch-icon.png',
    '/static/icons/icon.svg'
];

// Install event - precache static shell
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(PRECACHE_ASSETS).catch((err) => {
                console.warn('[PyShort SW] Pre-cache warning:', err);
            });
        }).then(() => self.skipWaiting())
    );
});

// Activate event - cleanup stale caches & claim clients
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) => {
            return Promise.all(
                keys.map((key) => {
                    if (key !== CACHE_NAME) {
                        return caches.delete(key);
                    }
                })
            );
        }).then(() => self.clients.claim())
    );
});

// Fetch event - safe network routing
self.addEventListener('fetch', (event) => {
    const request = event.request;
    const url = new URL(request.url);

    // 1. Only intercept GET requests
    if (request.method !== 'GET') {
        return;
    }

    // 2. NEVER cache dynamic endpoints:
    // - /api/* (shortening, links list, live stats, delete)
    // - /qr/* (live QR code streaming)
    // - /health (service health probe)
    // - Any short code redirect routes (single-slug paths that aren't static)
    if (
        url.pathname.startsWith('/api/') ||
        url.pathname.startsWith('/qr/') ||
        url.pathname === '/health'
    ) {
        return; // Let browser perform direct network request
    }

    // 3. Navigation requests (HTML pages)
    if (request.mode === 'navigate') {
        // Only the homepage / should use network-first with cache fallback
        if (url.pathname === '/' || url.pathname === '') {
            event.respondWith(
                fetch(request)
                    .then((networkResponse) => {
                        if (networkResponse && networkResponse.status === 200) {
                            const responseClone = networkResponse.clone();
                            caches.open(CACHE_NAME).then((cache) => cache.put(request, responseClone));
                        }
                        return networkResponse;
                    })
                    .catch(async () => {
                        const cached = await caches.match('/');
                        if (cached) return cached;
                        return new Response(
                            '<!DOCTYPE html><html><body style="font-family:sans-serif;text-align:center;padding:3rem;background:#0b0f19;color:#fff;"><h2>PyShort is currently offline</h2><p>Please check your connection.</p></body></html>',
                            { headers: { 'Content-Type': 'text/html' } }
                        );
                    })
            );
            return;
        }

        // Any other navigate request could be a short-code redirect (e.g. /my-slug)!
        // MUST bypass service worker cache so 302 redirect and click tracking work seamlessly!
        return;
    }

    // 4. Static assets (CSS, JS, Icons, Images, Fonts)
    if (url.pathname.startsWith('/static/') || url.hostname.includes('fonts.gstatic.com') || url.hostname.includes('fonts.googleapis.com')) {
        event.respondWith(
            caches.match(request).then((cachedResponse) => {
                if (cachedResponse) {
                    // Stale-while-revalidate for local static assets
                    fetch(request).then((networkResponse) => {
                        if (networkResponse && networkResponse.status === 200) {
                            caches.open(CACHE_NAME).then((cache) => cache.put(request, networkResponse));
                        }
                    }).catch(() => {});
                    return cachedResponse;
                }
                return fetch(request).then((networkResponse) => {
                    if (networkResponse && networkResponse.status === 200) {
                        const responseClone = networkResponse.clone();
                        caches.open(CACHE_NAME).then((cache) => cache.put(request, responseClone));
                    }
                    return networkResponse;
                });
            })
        );
        return;
    }
});
