// Wraps stockfish.js (an Emscripten UCI engine) as a nested Worker.
// Receives { fen, skillLevel, movetime? } and replies { bestmove }.
//
// stockfish.js is a self-contained Emscripten build that owns self.onmessage
// and self.postMessage directly — it cannot be used via importScripts() +
// factory call. Spawning it as a nested Worker is the correct pattern.

let sfWorker = null;
let uciReady = false;
let pendingSearch = null;

function sendSearch({ fen, skillLevel, movetime }) {
  sfWorker.postMessage('ucinewgame');
  sfWorker.postMessage(`setoption name Skill Level value ${skillLevel}`);
  sfWorker.postMessage(`position fen ${fen}`);
  sfWorker.postMessage(`go movetime ${movetime}`);
}

function ensureEngine() {
  if (sfWorker) return;
  sfWorker = new Worker('/static/stockfish.js');
  sfWorker.onmessage = (e) => {
    const line = typeof e.data === 'string' ? e.data : '';
    if (!uciReady) {
      if (line === 'uciok') {
        uciReady = true;
        if (pendingSearch) {
          sendSearch(pendingSearch);
          pendingSearch = null;
        }
      }
      return;
    }
    if (line.startsWith('bestmove')) {
      const move = line.split(' ')[1];
      self.postMessage({ bestmove: move && move !== '(none)' ? move : null });
    }
  };
  sfWorker.postMessage('uci');
}

self.onmessage = (e) => {
  const { fen, skillLevel = 20, movetime = 1000 } = e.data;
  ensureEngine();
  const search = { fen, skillLevel, movetime };
  if (uciReady) {
    sendSearch(search);
  } else {
    pendingSearch = search;
  }
};
