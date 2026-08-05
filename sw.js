/*
  MechanicDB PWA Service Worker
  Strategy: network-first pass-through for navigations, Stale-While-Revalidate
  for same-origin subresources (CSS/JS/CSVs).
  Strict bypass for non-GET requests (Web3Forms inquiries) and cross-origin
  endpoints (Stripe, Amazon, analytics).

  Cloudflare Pages clean URLs: /landing/powertrain.html 308-redirects to
  /landing/powertrain. A service worker must never answer a navigation with a
  redirected response (Chrome fails it with net::ERR_FAILED), so:
    - precache uses the clean extensionless URLs only,
    - navigations are passed through with the original Request (redirect mode
      "manual", so the browser handles the 308 itself),
    - redirected responses are never written to or served from the cache.
*/

const CACHE_NAME = 'mechanicdb-public-cache-v2026.07.2';
const CORE_ASSETS = [
  '/',
  '/site.webmanifest',
  '/dtc_codes.csv',
  '/diagnostic_fixes.csv',
  '/replacement_parts.csv',
  '/landing/powertrain',
  '/landing/chassis',
  '/landing/body',
  '/landing/network'
];

const cacheable = res => res && res.ok && !res.redirected && res.type === 'basic';

self.addEventListener('install', event => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache =>
      cache.addAll(CORE_ASSETS.map(url => new Request(url, { cache: 'reload' }))).catch(() => {})
    )
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return; // Stripe/Web3Forms/analytics untouched

  if (req.mode === 'navigate') {
    // Pass the original Request through so the browser follows any 308 itself;
    // fall back to the cached clean-URL page when offline.
    const cleanPath = url.pathname.endsWith('.html')
      ? url.pathname.slice(0, -5) : url.pathname;
    event.respondWith(
      fetch(req).then(res => {
        if (cacheable(res)) {
          const copy = res.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(cleanPath, copy));
        }
        return res;
      }).catch(() =>
        caches.match(cleanPath).then(cached => cached || caches.match('/'))
      )
    );
    return;
  }

  event.respondWith(
    caches.open(CACHE_NAME).then(cache =>
      cache.match(req).then(cached => {
        const network = fetch(req).then(res => {
          if (cacheable(res)) cache.put(req, res.clone());
          return res;
        }).catch(() => cached);
        return cached || network;
      })
    )
  );
});
