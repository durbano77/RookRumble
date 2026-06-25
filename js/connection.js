import { promotionPanelEl, statusEl } from "./dom.js";
import { state, websocketUrl, send } from "./state.js";
import { defaultVariants, defaultBotDifficulties } from "./constants.js";
import { updateHud } from "./hud.js";
import { renderGame } from "./board.js";
import { setStep } from "./menu.js";

export function setConnectionState(nextState) {
  state.connectionState = nextState;
  updateHud();
}

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
}

export function connectSocket() {
  setConnectionState("connecting");

  const ws = new WebSocket(websocketUrl());
  state.ws = ws;

  ws.addEventListener("open", () => {
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

