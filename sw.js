/*
  MechanicDB PWA Service Worker
  Strategy: Stale-While-Revalidate for local HTML/CSS/JS/CSVs.
  Strict bypass for non-GET requests (e.g. POST form submissions to FormSubmit) and cross-origin endpoints (Stripe, Amazon, Google Fonts).
*/

const CACHE_NAME = 'mechanicdb-public-cache-v2026.07.1';
const CORE_ASSETS = [
  '/',
  '/index.html',
  '/site.webmanifest',
  '/dtc_codes.csv',
  '/diagnostic_fixes.csv',
  '/replacement_parts.csv',
  '/landing/powertrain.html',
  '/landing/chassis.html',
  '/landing/body.html',
  '/landing/network.html'
];

self.addEventListener('install', event => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(CORE_ASSETS.map(url => new Request(url, { cache: 'reload' }))).catch(() => {});
    })
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => {
      return Promise.all(
        keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key))
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  /* 1. Strict POST/non-GET bypass: allow FormSubmit inquiries without caching interception */
  if (event.request.method !== 'GET') {
    return;
  }

  const url = new URL(event.request.url);

  /* 2. Strict cross-origin bypass: allow Stripe, Amazon, FormSubmit, and analytics to pass through directly */
  if (url.origin !== self.location.origin) {
    return;
  }

  /* 3. Stale-While-Revalidate strategy for same-origin resources */
  event.respondWith(
    caches.open(CACHE_NAME).then(cache => {
      return cache.match(event.request).then(cachedResponse => {
        const fetchPromise = fetch(event.request).then(networkResponse => {
          if (networkResponse && networkResponse.status === 200 && networkResponse.type === 'basic') {
            cache.put(event.request, networkResponse.clone());
          }
          return networkResponse;
        }).catch(() => cachedResponse);

        return cachedResponse || fetchPromise;
      });
    })
  );
});
