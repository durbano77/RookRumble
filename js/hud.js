import {
  statusEl,
  startMatchButton, pauseMatchButton, restartMatchButton,
  continueToPlayButton, backToSetupButton,
  createRoomButton, playBotButton, botDifficultySelect, joinRoomButton, leaveRoomButton,
  menuExitMainButton, menuExitGamesButton,
  overlayKickerEl, overlayTitleEl, overlayTextEl, overlayActionButton, overlayEl,
  clockBarEl, clock0El, clock1El,
  quickMatchButton, quickMatchGroupEl, matchmakingRowEl,
} from "./dom.js";
import {
  state, playerColor, currentGameIsActive, variantTitle, botLabel,
} from "./state.js";
import { renderVariantPicker, renderBotSelector } from "./variants.js";
import { setStep } from "./menu.js";

// ── Clock ─────────────────────────────────────────────────────────────────────

let clockInterval = null;
let clockData = null;

function formatClock(seconds) {
  const s = Math.max(0, Math.floor(seconds));
  const m = Math.floor(s / 60);
  const rem = s % 60;
  return `${m}:${rem.toString().padStart(2, "0")}`;
}

function renderClocks() {
  if (!clockData) return;
  const { remaining, receivedAt } = clockData;
  const elapsed = (Date.now() - receivedAt) / 1000;
  const activeIdx = state.game.turn === "white" ? 0 : 1;

  const times = [...remaining];
  if (state.game.gameState === "playing") {
    times[activeIdx] = Math.max(0, times[activeIdx] - elapsed);
  }

  [clock0El, clock1El].forEach((el, i) => {
    el.textContent = formatClock(times[i]);
    el.classList.toggle("clock-urgent", times[i] < 30);
    el.classList.toggle("clock-active", state.game.gameState === "playing" && i === activeIdx);
  });
}

function updateClockDisplay(clock) {
  clockData = clock ? { ...clock, receivedAt: Date.now() } : null;

  if (clock) {
    clockBarEl.classList.remove("is-hidden");
    if (!clockInterval) {
      clockInterval = setInterval(renderClocks, 100);
    }
    renderClocks();
  } else {
    clockBarEl.classList.add("is-hidden");
    if (clockInterval) {
      clearInterval(clockInterval);
      clockInterval = null;
    }
  }
}

// ── Overlay ───────────────────────────────────────────────────────────────────

export function showOverlay({ kicker, title, text, actionLabel, hidden, disabled = false }) {
  if (hidden) {
    overlayEl.classList.add("is-hidden");
    return;
  }
  overlayKickerEl.textContent = kicker;
  overlayTitleEl.textContent = title;
  overlayTextEl.textContent = text;
  overlayActionButton.textContent = actionLabel;
  overlayActionButton.disabled = disabled;
  overlayEl.classList.remove("is-hidden");
}

export function syncOverlay() {
  const bothConnected = state.players.every((p) => p.connected);

  if (!state.roomCode) {
    showOverlay({
      kicker: "Chess Room",
      title: "Create Or Join A Room",
      text: "Create a room for two players, or start a single-player bot match.",
      actionLabel: "Create Room",
      disabled: state.connectionState !== "connected",
    });
    return;
  }

  if (state.selectedGame === "none") {
    showOverlay({
      kicker: `Room ${state.roomCode}`,
      title: "Choose A Game",
      text: state.isHost ? "Pick a card from the Games shelf below." : "Waiting for the host to pick a game.",
      actionLabel: state.isHost ? "Choose Below" : "Waiting...",
      disabled: true,
    });
    return;
  }

  if (["waiting", "ready"].includes(state.game.gameState)) {
    showOverlay({
      kicker: `Room ${state.roomCode}`,
      title: `${variantTitle()} Ready`,
      text: bothConnected
        ? state.bot.enabled
          ? `${botLabel()} is ready. Start whenever you are ready.`
          : state.isHost
            ? "Both players are connected. Start whenever you are ready."
            : "Both players are connected. Waiting for the host to start."
        : "Waiting for another player to join this room.",
      actionLabel: state.isHost ? "Start" : "Waiting...",
      disabled: !state.isHost || !bothConnected,
    });
    return;
  }

  if (state.game.gameState === "paused") {
    showOverlay({
      kicker: "Paused",
      title: `${variantTitle()} Paused`,
      text: state.isHost ? "Resume or restart the game." : "The host has paused the game.",
      actionLabel: state.isHost ? "Resume" : "Paused",
      disabled: !state.isHost,
    });
    return;
  }

  if (state.game.gameState === "gameover") {
    showOverlay({
      kicker: "Game Over",
      title: variantTitle(),
      text: state.game.message,
      actionLabel: state.isHost ? "Play Again" : "Round Complete",
      disabled: !state.isHost,
    });
    return;
  }

  showOverlay({ hidden: true });
}

export function updateButtons() {
  const connected = state.connectionState === "connected";
  const inRoom = Boolean(state.roomCode);
  const bothConnected = state.players.every((p) => p.connected);
  const hostReady = connected && inRoom && state.isHost;
  const hasVariant = state.selectedGame !== "none";
  const busy = !connected || state.inQueue;

  renderBotSelector();
  createRoomButton.disabled = busy;
  playBotButton.disabled = busy;
  botDifficultySelect.disabled = busy;
  joinRoomButton.disabled = busy;
  quickMatchButton.disabled = busy;
  quickMatchGroupEl.classList.toggle("is-hidden", state.inQueue);
  matchmakingRowEl.classList.toggle("is-hidden", !state.inQueue);

  leaveRoomButton.disabled = !inRoom;
  startMatchButton.disabled =
    !hostReady || !bothConnected || !hasVariant || currentGameIsActive();
  pauseMatchButton.disabled =
    !hostReady || !hasVariant || !["playing", "paused"].includes(state.game.gameState);
  pauseMatchButton.textContent = state.game.gameState === "paused" ? "Resume" : "Pause";
  restartMatchButton.disabled = !hostReady || !bothConnected || !hasVariant;
  continueToPlayButton.disabled = !inRoom || !hasVariant;
  backToSetupButton.disabled = !connected;
  menuExitMainButton.disabled = !connected && !inRoom;
  menuExitGamesButton.disabled = !inRoom;
  renderVariantPicker();
  setStep(state.uiStep);
}

export function updateHud() {
  const game = state.game;

  statusEl.textContent = game.message || "Choose a variant to begin.";
  updateClockDisplay(game.clock || null);
  updateButtons();
  syncOverlay();
}
