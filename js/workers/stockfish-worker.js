// Stockfish UCI wrapper for use as a Web Worker
// Loaded via: new Worker('/js/workers/stockfish-worker.js')
importScripts('/static/stockfish.js');

let stockfish;
let resolveMove;

function init() {
  stockfish = Stockfish();
  stockfish.onmessage = (event) => {
    const line = typeof event === 'string' ? event : event.data;
    if (typeof line !== 'string') return;
    if (line.startsWith('bestmove')) {
      const parts = line.split(' ');
      const move = parts[1];
      if (resolveMove && move && move !== '(none)') {
        resolveMove(move);
        resolveMove = null;
      }
    }
  };
  stockfish.postMessage('uci');
}

self.onmessage = (e) => {
  const { fen, skillLevel = 20, movetime = 1000 } = e.data;
  if (!stockfish) init();

  resolveMove = (move) => {
    self.postMessage({ bestmove: move });
  };

  stockfish.postMessage('ucinewgame');
  stockfish.postMessage(`setoption name Skill Level value ${skillLevel}`);
  stockfish.postMessage(`position fen ${fen}`);
  stockfish.postMessage(`go movetime ${movetime}`);
};
