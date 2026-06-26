// Offline adapter — routes game messages to Pyodide worker instead of WebSocket
// Implements the same send/receive interface as the WebSocket connection in connection.js

let pyodideWorker = null;
let stockfishWorker = null;
let pyodideReady = false;
let pendingMessages = [];
let onSyncCallback = null;

export function initOfflineAdapter(onSync) {
  onSyncCallback = onSync;
  pyodideWorker = new Worker('/js/workers/pyodide-worker.js');
  pyodideWorker.onmessage = handleWorkerMessage;
  pyodideWorker.postMessage({ type: 'init' });
}

export function isOfflineAdapterReady() {
  return pyodideReady;
}

export function sendOffline(msgType, payload = {}) {
  const msg = { type: msgType, ...payload };
  if (!pyodideReady) {
    pendingMessages.push(msg);
    return;
  }
  dispatch(msg);
}

export function disposeOfflineAdapter() {
  if (pyodideWorker) { pyodideWorker.terminate(); pyodideWorker = null; }
  if (stockfishWorker) { stockfishWorker.terminate(); stockfishWorker = null; }
  pyodideReady = false;
  pendingMessages = [];
  onSyncCallback = null;
}

// ── Internal ────────────────────────────────────────────────────────────────

function dispatch(msg) {
  pyodideWorker.postMessage(msg);
}

function handleWorkerMessage(e) {
  const payload = e.data;
  if (payload.type === 'ready') {
    pyodideReady = true;
    for (const msg of pendingMessages) dispatch(msg);
    pendingMessages = [];
    return;
  }
  if (payload.type === 'error') {
    console.error('[Offline] Pyodide error:', payload.message);
    return;
  }

  // It's a sync payload — check if Stockfish needs to move
  if (onSyncCallback) onSyncCallback(payload);
  maybeRunStockfish(payload);
}

function maybeRunStockfish(sync) {
  const game = sync.game;
  const bot = sync.bot;
  if (!bot?.enabled || !bot.difficulty?.startsWith('stockfish')) return;
  if (game?.gameState !== 'playing') return;
  if (game.turn !== 'black') return;  // Bot is always black (slot 1)

  // Determine skill level from difficulty id
  const skillMap = { stockfish_1: 5, stockfish_2: 12, stockfish_3: 20 };
  const skill = skillMap[bot.difficulty] ?? 20;

  runStockfish(game.fen, skill).then((move) => {
    if (!move) return;
    sendOffline('engine_move', { from: move.slice(0, 2), to: move.slice(2, 4), promotion: move[4] || null });
  });
}

function runStockfish(fen, skillLevel) {
  return new Promise((resolve) => {
    if (!stockfishWorker) {
      stockfishWorker = new Worker('/js/workers/stockfish-worker.js');
    }
    const handler = (e) => {
      stockfishWorker.removeEventListener('message', handler);
      resolve(e.data.bestmove || null);
    };
    stockfishWorker.addEventListener('message', handler);
    stockfishWorker.postMessage({ fen, skillLevel });
  });
}
