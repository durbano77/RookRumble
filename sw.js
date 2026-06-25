const CACHE = 'rook-rumble-v1';

// App shell — static assets that make the page load fast on repeat visits
const SHELL = [
  '/',
  '/css/variables.css',
  '/css/layout.css',
  '/css/lobby.css',
  '/css/game-cards.css',
  '/css/board.css',
  '/css/overlay.css',
  '/css/menu.css',
  '/css/responsive.css',
  '/js/main.js',
  '/js/ads.js',
  '/manifest.json',
  '/favicon.ico',
  '/icons/icon-192.png',
];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)));
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (e) => {
  // WebSocket and live game API — always go to network, never cache
  if (e.request.url.includes('/ws')) return;

  e.respondWith(
    fetch(e.request)
      .then((response) => {
        // Cache successful GET responses for the shell
        if (e.request.method === 'GET' && response.status === 200) {
          const clone = response.clone();
          caches.open(CACHE).then((c) => c.put(e.request, clone));
        }
        return response;
      })
      .catch(() => caches.match(e.request))
  );
});
