// JVO — Service Worker
// Cache statique pour fonctionnement hors-ligne

const CACHE  = 'jvo-v1';
const ASSETS = [
  '/JVO/',
  '/JVO/index.html',
  '/JVO/manifest.json',
  '/JVO/logo.png',
  '/JVO/404.png',
  '/JVO/nin_.png',
  '/JVO/ps_.png',
  '/JVO/xbox_.png',
];

// Installation — mise en cache des assets statiques
self.addEventListener('install', function(e) {
  e.waitUntil(
    caches.open(CACHE).then(function(cache) {
      return cache.addAll(ASSETS);
    })
  );
  self.skipWaiting();
});

// Activation — nettoyer les anciens caches
self.addEventListener('activate', function(e) {
  e.waitUntil(
    caches.keys().then(function(keys) {
      return Promise.all(
        keys.filter(function(k) { return k !== CACHE; })
            .map(function(k) { return caches.delete(k); })
      );
    })
  );
  self.clients.claim();
});

// Fetch — stratégie : réseau en priorité, cache en fallback
self.addEventListener('fetch', function(e) {
  // Ne pas intercepter les requêtes Firebase (toujours réseau)
  var url = e.request.url;
  if (url.includes('firestore.googleapis.com') ||
      url.includes('firebase') ||
      url.includes('googleapis.com')) {
    return;
  }

  e.respondWith(
    fetch(e.request)
      .then(function(response) {
        // Mettre en cache les images de jaquettes (covers/)
        if (url.includes('/covers/') && response.ok) {
          var clone = response.clone();
          caches.open(CACHE).then(function(cache) {
            cache.put(e.request, clone);
          });
        }
        return response;
      })
      .catch(function() {
        // Fallback cache
        return caches.match(e.request).then(function(cached) {
          return cached || caches.match('/JVO/');
        });
      })
  );
});
