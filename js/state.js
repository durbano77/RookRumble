import { defaultVariants, defaultBotDifficulties } from "./constants.js";

export const state = {
  ws: null,
  connectionState: "connecting",
  roomCode: "",
  selectedGame: "none",
  availableGames: defaultVariants,
  playerIndex: null,
  isHost: false,
  bot: { enabled: false, difficulty: null, label: null, color: null },
  botDifficulties: defaultBotDifficulties,
  players: [
    { connected: false, label: "White" },
    { connected: false, label: "Black" },
  ],
  game: {
    kind: "none",
    gameState: "waiting",
    message: "Create or join a room to begin.",
  },
  selectedSquare: null,
  pendingPromotion: null,
  uiStep: "setup",
  pendingStepAfterRoom: null,
  inQueue: false,
  // Offline mode: when set, send() routes through this function instead of WebSocket
  _offlineSend: null,
};

export function websocketUrl() {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}/ws`;
}

export function canSend() {
  return state.ws && state.ws.readyState === WebSocket.OPEN;
}

export function send(type, payload = {}) {
  if (state._offlineSend) {
    state._offlineSend(type, payload);
    return;
  }
  if (canSend()) {
    state.ws.send(JSON.stringify({ type, ...payload }));
  }
}

export function playerColor() {
  if (state.playerIndex === 0) return "white";
  if (state.playerIndex === 1) return "black";
  return null;
}

export function isMyTurn() {
  return state.game.gameState === "playing" && playerColor() === state.game.turn;
}

export function pendingMutator() {
  return state.game.variant?.pendingMutator || null;
}

export function isMyMutatorChoice() {
  const pending = pendingMutator();
  return Boolean(pending && pending.chooser === playerColor());
}

export function currentGameIsActive() {
  return ["playing", "paused"].includes(state.game.gameState);
}

export function variantTitle(variantId = state.selectedGame) {
  return state.availableGames.find((v) => v.id === variantId)?.label || "Chess";
}

export function botLabel() {
  return (
    state.bot.label ||
    state.botDifficulties.find((b) => b.id === state.bot.difficulty)?.label ||
    "Bot"
  );
}
