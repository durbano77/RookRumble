import {
  roomCodeDisplayEl, connectionStateEl, connectionHintEl,
  score1El, score2El, player1StateEl, player2StateEl,
  roleDisplayEl, roleHintEl, statusEl,
  startMatchButton, pauseMatchButton, restartMatchButton,
  continueToPlayButton, backToSetupButton, playBackToGamesButton, playBackToSetupButton,
  createRoomButton, playBotButton, botDifficultySelect, joinRoomButton, leaveRoomButton,
  menuExitMainButton, menuExitGamesButton,
  overlayKickerEl, overlayTitleEl, overlayTextEl, overlayActionButton, overlayEl,
} from "./dom.js";
import {
  state, playerColor, currentGameIsActive, variantTitle, botLabel,
} from "./state.js";
import { renderVariantPicker, renderBotSelector } from "./variants.js";
import { setStep } from "./menu.js";

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

  renderBotSelector();
  createRoomButton.disabled = !connected;
  playBotButton.disabled = !connected;
  botDifficultySelect.disabled = !connected;
  joinRoomButton.disabled = !connected;
  leaveRoomButton.disabled = !inRoom;
  startMatchButton.disabled =
    !hostReady || !bothConnected || !hasVariant || currentGameIsActive();
  pauseMatchButton.disabled =
    !hostReady || !hasVariant || !["playing", "paused"].includes(state.game.gameState);
  pauseMatchButton.textContent = state.game.gameState === "paused" ? "Resume" : "Pause";
  restartMatchButton.disabled = !hostReady || !bothConnected || !hasVariant;
  continueToPlayButton.disabled = !inRoom || !hasVariant;
  backToSetupButton.disabled = !connected;
  playBackToGamesButton.disabled = !inRoom || !hasVariant;
  playBackToSetupButton.disabled = !connected;
  menuExitMainButton.disabled = !connected && !inRoom;
  menuExitGamesButton.disabled = !inRoom;
  renderVariantPicker();
  setStep(state.uiStep);
}

export function updateHud() {
  const game = state.game;

  roomCodeDisplayEl.textContent = state.roomCode || "----";
  connectionStateEl.textContent = state.connectionState === "connected" ? "Connected" : "Disconnected";
  connectionHintEl.textContent = state.connectionState === "connected"
    ? "Chess room sync is active."
    : "Trying to reach the chess server.";

  score1El.textContent = "White";
  score2El.textContent = state.bot.enabled ? botLabel() : "Black";
  player1StateEl.textContent = state.players[0].connected
    ? game.turn === "white" && game.gameState === "playing" ? "To move" : "Connected"
    : "Waiting";
  player2StateEl.textContent = state.players[1].connected
    ? game.turn === "black" && game.gameState === "playing"
      ? state.bot.enabled ? "Bot to move" : "To move"
      : "Connected"
    : "Waiting";

  if (state.playerIndex === null) {
    roleDisplayEl.textContent = "Not In Room";
    roleHintEl.textContent = "Create or join a room to claim a side.";
  } else {
    roleDisplayEl.textContent = state.playerIndex === 0 ? "White" : "Black";
    roleHintEl.textContent = state.bot.enabled
      ? `You play White against ${botLabel()}.`
      : state.isHost
        ? "You host this room and play White."
        : "You play Black in this room.";
  }

  statusEl.textContent = game.message || "Choose a variant to begin.";
  updateButtons();
  syncOverlay();
}
