const CACHE = 'rook-rumble-v9';

// Critical shell — small files that must be cached at install time for the
// app to load at all. If any of these fail, the SW install fails gracefully
// (skipWaiting still fires, we just won't have a warm cache).
const CRITICAL = [
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
  '/js/offline-adapter.js',
  '/manifest.json',
  '/icons/icon-192.png',
];

// Heavy assets (Pyodide, Stockfish, Python source) are cached lazily on first
// request via the fetch handler below — no blocking the SW install on them.

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE).then((c) => c.addAll(CRITICAL)).catch(() => {})
  );
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
  // WebSocket — always network, never cache
  if (e.request.url.includes('/ws')) return;

  e.respondWith(
    fetch(e.request)
      .then((response) => {
        // Lazily cache any successful GET response (covers Pyodide, Stockfish, game files)
        if (e.request.method === 'GET' && response.status === 200) {
          const clone = response.clone();
          caches.open(CACHE).then((c) => c.put(e.request, clone));
        }
        return response;
      })
      .catch(() => caches.match(e.request))
  );
});
