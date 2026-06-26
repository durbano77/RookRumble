const CACHE = 'rook-rumble-v6';

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
  // '/js/ads.js',
  '/js/offline-adapter.js',
  '/js/workers/stockfish-worker.js',
  '/js/workers/pyodide-worker.js',
  '/static/stockfish.js',
  '/static/chess.whl',
  '/static/pyodide/pyodide.js',
  '/static/pyodide/pyodide.asm.js',
  '/static/pyodide/pyodide.asm.wasm',
  '/static/pyodide/python_stdlib.zip',
  '/static/pyodide/pyodide-lock.json',
  '/static/pyodide/micropip-0.6.0-py3-none-any.whl',
  '/static/pyodide/packaging-23.2-py3-none-any.whl',
  '/game/__init__.py',
  '/game/base.py',
  '/game/constants.py',
  '/game/lobby.py',
  '/game/offline.py',
  '/game/registry.py',
  '/game/room.py',
  '/game/variants/__init__.py',
  '/game/variants/atomic.py',
  '/game/variants/classic.py',
  '/game/variants/dice.py',
  '/game/variants/fog.py',
  '/game/variants/king_hill.py',
  '/game/variants/three_check.py',
  '/game/variants/thress.py',
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
