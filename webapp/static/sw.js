const CACHE_NAME = 'air-quality-v1';
const STATIC_RESOURCES = [
  '/',
  '/static/manifest.json',
  'https://cdnjs.cloudflare.com/ajax/libs/tailwindcss/2.2.19/tailwind.min.css',
  'https://cdn.jsdelivr.net/npm/chart.js',
  'https://cdn.jsdelivr.net/npm/gaugeJS',
  '/static/icons/icon-192x192.png',
  '/static/icons/icon-512x512.png',
  '/static/good.webp',
  '/static/moderate.webp',
  '/static/unhealthy_sensitive.webp',
  '/static/unhealthy.webp',
  '/static/very_unhealthy.webp',
  '/static/hazardous.webp'
];

// Install event - cache static resources
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(STATIC_RESOURCES))
  );
});

// Activate event - cleanup old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames
          .filter(name => name !== CACHE_NAME)
          .map(name => caches.delete(name))
      );
    })
  );
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Return cached response if found
        if (response) {
          return response;
        }

        // If request is for API, try network first, then show offline message
        if (event.request.url.includes('/api/')) {
          return fetch(event.request)
            .catch(() => new Response(
              JSON.stringify({ error: 'Sie sind offline. Daten können nicht aktualisiert werden.' }),
              { headers: { 'Content-Type': 'application/json' } }
            ));
        }

        // Otherwise fetch from network and cache
        return fetch(event.request)
          .then(response => {
            const responseClone = response.clone();
            caches.open(CACHE_NAME)
              .then(cache => cache.put(event.request, responseClone));
            return response;
          })
          .catch(() => {
            return new Response(
              '<html><body><h1>Offline</h1><p>Sie sind offline. Bitte überprüfen Sie Ihre Internetverbindung.</p></body></html>',
              { headers: { 'Content-Type': 'text/html' } }
            );
          });
      })
  );
});
