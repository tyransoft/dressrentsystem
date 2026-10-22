self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open('sw-cache').then(function(cache) {
      return cache.addAll([
        '/dashboard/',
      ]).catch(err => console.log('Cache add error:', err));
    })
  );
  self.skipWaiting();
});

self.addEventListener('activated', function(event) {
  event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', function(event) {
  event.respondWith(
    caches.match(event.request).then(function(response) {
      return response || fetch(event.request);
    })
  );
});