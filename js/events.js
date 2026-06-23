import {
  promotionPanelEl, createRoomButton, playBotButton, botDifficultySelect,
  joinRoomButton, roomCodeInput, leaveRoomButton,
  startMatchButton, pauseMatchButton, restartMatchButton,
  overlayActionButton, continueToPlayButton, backToSetupButton,
  playBackToGamesButton, playBackToSetupButton,
  menuButton, closeMenuButton, menuExitMainButton, menuExitGamesButton,
  menuOpenSettingsButton, settingsBackButton, menuModal,
  themeSelect, patternSelect, boardSelect, pieceSelect,
  stepButtons,
} from "./dom.js";
import { state, send } from "./state.js";
import { applyAppearance } from "./appearance.js";
import { renderBotSelector } from "./variants.js";
import { setStep } from "./menu.js";
import { openMenu, closeMenu, showMenuView, exitToMainMenu, exitToGameSelection } from "./menu.js";

// Promotion buttons
for (const button of promotionPanelEl.querySelectorAll("[data-promotion]")) {
  button.addEventListener("click", () => {
    if (!state.pendingPromotion) return;
    send("chess_move", {
      from: state.pendingPromotion.from,
      to: state.pendingPromotion.to,
      promotion: button.dataset.promotion,
    });
    state.selectedSquare = null;
    state.pendingPromotion = null;
    promotionPanelEl.classList.add("is-hidden");
  });
}

// Room actions
createRoomButton.addEventListener("click", () => {
  state.pendingStepAfterRoom = "games";
  send("create_room");
});

playBotButton.addEventListener("click", () => {
  state.pendingStepAfterRoom = "games";
  send("create_bot_room", { difficulty: botDifficultySelect.value });
});

joinRoomButton.addEventListener("click", () => {
  const roomCode = roomCodeInput.value.trim();
  state.pendingStepAfterRoom = "games";
  send("join_room", { roomCode });
});

leaveRoomButton.addEventListener("click", () => {
  state.pendingStepAfterRoom = null;
  setStep("setup");
  send("leave_room");
});

// Match controls
startMatchButton.addEventListener("click", () => { send("start_game"); });
pauseMatchButton.addEventListener("click", () => { send("toggle_pause"); });
restartMatchButton.addEventListener("click", () => { send("restart_game"); });

// Overlay action (context-dependent)
overlayActionButton.addEventListener("click", () => {
  if (!state.roomCode) {
    state.pendingStepAfterRoom = "games";
    send("create_room");
    return;
  }
  if (!state.isHost || state.selectedGame === "none") return;
  if (["waiting", "ready"].includes(state.game.gameState)) { send("start_game"); return; }
  if (state.game.gameState === "paused") { send("toggle_pause"); return; }
  if (state.game.gameState === "gameover") { send("restart_game"); }
});

// Step navigation
continueToPlayButton.addEventListener("click", () => { setStep("play"); });
backToSetupButton.addEventListener("click", () => { exitToMainMenu(); });
playBackToGamesButton.addEventListener("click", () => { exitToGameSelection(); });
playBackToSetupButton.addEventListener("click", () => { exitToMainMenu(); });

for (const button of stepButtons) {
  button.addEventListener("click", () => { setStep(button.dataset.stepTarget); });
}

// Appearance
for (const select of [themeSelect, patternSelect, boardSelect, pieceSelect]) {
  select.addEventListener("change", () => {
    applyAppearance({
      theme: themeSelect.value,
      pattern: patternSelect.value,
      board: boardSelect.value,
      pieces: pieceSelect.value,
    });
  });
}

// Bot selector
botDifficultySelect.addEventListener("change", () => { renderBotSelector(); });

// Room code input: digits only
roomCodeInput.addEventListener("input", () => {
  roomCodeInput.value = roomCodeInput.value.replace(/\D/g, "").slice(0, 6);
});

// Menu
menuButton.addEventListener("click", () => { openMenu("main"); });
closeMenuButton.addEventListener("click", () => { closeMenu(); });
menuExitMainButton.addEventListener("click", () => { exitToMainMenu(); });
menuExitGamesButton.addEventListener("click", () => { exitToGameSelection(); });
menuOpenSettingsButton.addEventListener("click", () => { showMenuView("settings"); });
settingsBackButton.addEventListener("click", () => { showMenuView("main"); });

menuModal.addEventListener("click", (event) => {
  if (event.target === menuModal) closeMenu();
});

window.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !menuModal.classList.contains("is-hidden")) closeMenu();
});
