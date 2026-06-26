import { promotionPanelEl, statusEl } from "./dom.js";
import { state, websocketUrl, send } from "./state.js";
import { defaultVariants, defaultBotDifficulties } from "./constants.js";
import { updateHud } from "./hud.js";
import { renderGame } from "./board.js";
import { setStep } from "./menu.js";
import { initOfflineAdapter, sendOffline } from "./offline-adapter.js";

// ── Offline mode ──────────────────────────────────────────────────────────────

export let isOffline = false;
let everConnected = false;  // true once WebSocket has successfully opened
let stockfishWorker = null;

export function setConnectionState(nextState) {
  state.connectionState = nextState;
  updateHud();
}

// ── Sync handler ──────────────────────────────────────────────────────────────

export function applySync(payload) {
  const prevSelectedGame = state.selectedGame;

  state.roomCode = payload.roomCode || "";
  state.selectedGame = payload.selectedGame || "none";
  state.availableGames = payload.availableGames || defaultVariants;
  state.playerIndex = typeof payload.playerIndex === "number" ? payload.playerIndex : null;
  state.isHost = Boolean(payload.isHost);
  state.bot = payload.bot || { enabled: false, difficulty: null, label: null, color: null };
  state.botDifficulties = payload.botDifficulties || defaultBotDifficulties;
  state.players = payload.players || state.players;
  state.game = payload.game || state.game;
  state.inQueue = Boolean(payload.queued);

  if (!state.roomCode) {
    if (!state.inQueue) {
      state.pendingStepAfterRoom = null;
    }
    setStep("setup");
  } else if (state.pendingStepAfterRoom) {
    setStep(state.pendingStepAfterRoom);
    state.pendingStepAfterRoom = null;
  } else if (state.uiStep === "games" && prevSelectedGame === "none" && state.selectedGame !== "none") {
    setStep("play");
  }

  if (state.game.gameState !== "playing") {
    state.selectedSquare = null;
    state.pendingPromotion = null;
    promotionPanelEl.classList.add("is-hidden");
  }

  updateHud();
  renderGame();

  // For online bot games with Stockfish engine, trigger client-side move computation
  if (!isOffline) {
    maybeRunStockfishOnline(payload);
  }
}

// ── Online Stockfish ──────────────────────────────────────────────────────────

function maybeRunStockfishOnline(payload) {
  const bot = payload.bot;
  const game = payload.game;
  if (!bot?.enabled || !bot.difficulty?.startsWith("stockfish")) return;
  if (game?.gameState !== "playing" || game.turn !== "black") return;

  const skillMap = { stockfish_1: 5, stockfish_2: 12, stockfish_3: 20 };
  const skill = skillMap[bot.difficulty] ?? 20;

  getStockfishMove(game.fen, skill).then((move) => {
    if (move) send("engine_move", { from: move.slice(0, 2), to: move.slice(2, 4), promotion: move[4] || null });
  });
}

function getStockfishMove(fen, skillLevel) {
  return new Promise((resolve) => {
    if (!stockfishWorker) {
      stockfishWorker = new Worker("/js/workers/stockfish-worker.js");
    }
    const handler = (e) => {
      stockfishWorker.removeEventListener("message", handler);
      resolve(e.data.bestmove || null);
    };
    stockfishWorker.addEventListener("message", handler);
    stockfishWorker.postMessage({ fen, skillLevel });
  });
}

// ── Switch to offline mode ────────────────────────────────────────────────────

function switchToOffline() {
  isOffline = true;
  state.ws = null;

  // Route all send() calls through the offline adapter
  state._offlineSend = sendOffline;

  initOfflineAdapter((syncPayload) => {
    applySync(syncPayload);
  });

  setConnectionState("connected");
  state.game = {
    kind: "none",
    gameState: "waiting",
    message: "You are offline. Bot games available.",
  };
  updateHud();
  renderGame();
}

// ── WebSocket ─────────────────────────────────────────────────────────────────

export function connectSocket() {
  // Skip WebSocket entirely if already in offline mode
  if (isOffline) return;

  setConnectionState("connecting");

  const ws = new WebSocket(websocketUrl());
  state.ws = ws;

  ws.addEventListener("open", () => {
    everConnected = true;
    setConnectionState("connected");
  });

  ws.addEventListener("message", (event) => {
    const payload = JSON.parse(event.data);
    if (payload.type === "sync") {
      applySync(payload);
      return;
    }
    if (payload.type === "error") {
      statusEl.textContent = payload.message;
    }
  });

  ws.addEventListener("close", () => {
    state.ws = null;

    // First connection failure (never connected) → switch to offline mode
    if (!isOffline && !everConnected) {
      switchToOffline();
      return;
    }

    if (isOffline) return;

    setConnectionState("disconnected");
    state.roomCode = "";
    state.selectedGame = "none";
    state.playerIndex = null;
    state.isHost = false;
    state.bot = { enabled: false, difficulty: null, label: null, color: null };
    state.botDifficulties = defaultBotDifficulties;
    state.players = [
      { connected: false, label: "White" },
      { connected: false, label: "Black" },
    ];
    state.game = {
      kind: "none",
      gameState: "waiting",
      message: "Server connection lost. Retrying...",
    };
    state.pendingStepAfterRoom = null;
    setStep("setup");
    updateHud();
    renderGame();
    window.setTimeout(connectSocket, 1200);
  });

  ws.addEventListener("error", () => {
    ws.close();
  });
}
