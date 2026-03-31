// Service Worker for TransPyC — Progressive Web App
// Cache strategy:
// - Static assets (HTML, CSS, JS, fonts): Cache-first (with network update in background)
// - API calls (/api/*): Network-first (fallback to cached response if offline)
// - Errors: Graceful offline handling with cached data or fallback response

const CACHE_VERSION = 'v3';
const STATIC_CACHE = `transpyc-static-${CACHE_VERSION}`;
const API_CACHE = `transpyc-api-${CACHE_VERSION}`;
const FONT_CACHE = `transpyc-fonts-${CACHE_VERSION}`;

// Assets to cache on service worker install
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/app.js',
  '/styles.css',
  '/manifest.json',
  '/Images/favicon.ico',
  '/Images/favicon-16x16.png',
  '/Images/favicon-32x32.png',
  '/Images/apple-touch-icon.png',
  '/Images/icon-192x192.png',
  '/Images/icon-192x192-maskable.png',
  '/Images/icon-512x512.png',
  '/Images/icon-512x512-maskable.png'
];

// Font URLs to cache
const FONT_ASSETS = [
  'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap',
  'https://fonts.gstatic.com/s/inter/v12/UcCO3FwrK3iLTeHAPUlC7A.woff2',
  'https://fonts.gstatic.com/s/inter/v12/UcCO3FwrK3iLTeHAPUlC5Z-eVwucqVJY.woff2',
  'https://fonts.gstatic.com/s/jetbrainsmono/v8/tDbk2o-flNjnDkXdKXtu75VZHmU8Gmt_RR8zHw.woff2',
  'https://fonts.gstatic.com/s/jetbrainsmono/v8/tDbk2o-flNjnDkXdKXtu75VZHmU8GNRs.woff2'
];

// ═══════════════════════════════════════════════════════════
// INSTALL: Cache static assets
// ═══════════════════════════════════════════════════════════
self.addEventListener('install', event => {
  console.log('[SW] Installing service worker...');
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(cache => {
        console.log('[SW] Caching static assets...');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => {
        // Cache fonts in parallel (non-critical)
        return caches.open(FONT_CACHE)
          .then(cache => cache.addAll(FONT_ASSETS).catch(() => {
            console.log('[SW] Some fonts could not be cached (might be offline during install)');
          }));
      })
      .then(() => {
        console.log('[SW] Skipping waiting, immediately activate...');
        return self.skipWaiting();
      })
      .catch(err => console.error('[SW] Install failed:', err))
  );
});

// ═══════════════════════════════════════════════════════════
// ACTIVATE: Clean up old caches
// ═══════════════════════════════════════════════════════════
self.addEventListener('activate', event => {
  console.log('[SW] Activating service worker...');
  event.waitUntil(
    caches.keys()
      .then(cacheNames => {
        return Promise.all(
          cacheNames
            .filter(cacheName => {
              const isOldStatic = cacheName.startsWith('transpyc-static-') && cacheName !== STATIC_CACHE;
              const isOldApi = cacheName.startsWith('transpyc-api-') && cacheName !== API_CACHE;
              const isOldFont = cacheName.startsWith('transpyc-fonts-') && cacheName !== FONT_CACHE;
              return isOldStatic || isOldApi || isOldFont;
            })
            .map(cacheName => {
              console.log('[SW] Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            })
        );
      })
      .then(() => self.clients.claim())
      .catch(err => console.error('[SW] Activate failed:', err))
  );
});

// ═══════════════════════════════════════════════════════════
// FETCH: Smart caching strategy
// ═══════════════════════════════════════════════════════════
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // API calls: network-first, fallback to cache
  if (url.pathname.startsWith('/api/')) {
    return event.respondWith(networkFirstStrategy(request, API_CACHE));
  }

  // Fonts: cache-first
  if (url.origin === 'https://fonts.googleapis.com' || url.origin === 'https://fonts.gstatic.com') {
    return event.respondWith(cacheFirstStrategy(request, FONT_CACHE));
  }

  // Static assets: cache-first
  return event.respondWith(cacheFirstStrategy(request, STATIC_CACHE));
});

// ═══════════════════════════════════════════════════════════
// STRATEGY: Cache-first (offline-friendly, fast)
// ═══════════════════════════════════════════════════════════
function cacheFirstStrategy(request, cacheName) {
  return caches.match(request)
    .then(response => {
      if (response) {
        console.log('[SW] Cache hit:', request.url);
        return response;
      }

      console.log('[SW] Cache miss, fetching:', request.url);
      return fetch(request)
        .then(response => {
          // Don't cache non-200 responses
          if (!response || response.status !== 200 || response.type === 'error') {
            return response;
          }

          // Clone and cache the response
          const responseToCache = response.clone();
          caches.open(cacheName)
            .then(cache => cache.put(request, responseToCache))
            .catch(() => console.log('[SW] Failed to cache:', request.url));

          return response;
        })
        .catch(err => {
          console.error('[SW] Fetch failed for:', request.url, err);
          // Return offline fallback if available
          return caches.match(request);
        });
    });
}

// ═══════════════════════════════════════════════════════════
// STRATEGY: Network-first (always try fresh, fallback to cache)
// ═══════════════════════════════════════════════════════════
function networkFirstStrategy(request, cacheName) {
  return fetch(request)
    .then(response => {
      // Cache successful responses
      if (response && response.status === 200) {
        const responseToCache = response.clone();
        caches.open(cacheName)
          .then(cache => cache.put(request, responseToCache))
          .catch(() => console.log('[SW] Failed to cache API response:', request.url));
      }
      return response;
    })
    .catch(err => {
      console.error('[SW] Network request failed:', request.url, err);
      // Try to return cached response (offline fallback)
      return caches.match(request)
        .then(cachedResponse => {
          if (cachedResponse) {
            console.log('[SW] Returning cached API response (offline):', request.url);
            return cachedResponse;
          }
          // No cache available, return offline response
          return offlineResponse();
        });
    });
}

// ═══════════════════════════════════════════════════════════
// OFFLINE FALLBACK: Return JSON error for API calls
// ═══════════════════════════════════════════════════════════
function offlineResponse() {
  return new Response(
    JSON.stringify({
      error: 'offline',
      message: 'You are currently offline. Conversion requires an active internet connection.',
      warnings: [
        {
          type: 'error',
          message: 'Network unavailable — please reconnect to convert code',
          line: 0,
          hint: 'Check your internet connection and try again.'
        }
      ],
      ir: []
    }),
    {
      status: 503,
      statusText: 'Service Unavailable',
      headers: { 'Content-Type': 'application/json' }
    }
  );
}

// ═══════════════════════════════════════════════════════════
// MESSAGE HANDLING: Update detection & cache versioning
// ═══════════════════════════════════════════════════════════
self.addEventListener('message', event => {
  const { type } = event.data;

  if (type === 'SKIP_WAITING') {
    console.log('[SW] Received SKIP_WAITING, reloading...');
    self.skipWaiting();
  }

  if (type === 'CLEAR_CACHE') {
    console.log('[SW] Clearing all caches...');
    caches.keys().then(names => Promise.all(names.map(n => caches.delete(n))));
  }
});
