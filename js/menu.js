import { menuModal, menuMainView, menuSettingsView, stepPanels, stepButtons } from "./dom.js";
import { state, send, currentGameIsActive } from "./state.js";

export function canShowStep(step) {
  if (step === "setup") return true;
  if (step === "games") return Boolean(state.roomCode);
  if (step === "play") return Boolean(state.roomCode && state.selectedGame !== "none");
  return false;
}

export function setStep(step) {
  const nextStep = canShowStep(step) ? step : "setup";
  state.uiStep = nextStep;
  document.body.dataset.step = nextStep;

  for (const panel of stepPanels) {
    panel.classList.toggle("is-active", panel.dataset.stepPanel === nextStep);
  }

  for (const button of stepButtons) {
    const isActive = button.dataset.stepTarget === nextStep;
    button.classList.toggle("is-active", isActive);
    button.disabled = !canShowStep(button.dataset.stepTarget);
  }
}

export function openMenu(view = "main") {
  menuModal.classList.remove("is-hidden");
  showMenuView(view);
}

export function closeMenu() {
  menuModal.classList.add("is-hidden");
}

export function showMenuView(view) {
  const showSettings = view === "settings";
  menuMainView.classList.toggle("is-hidden", showSettings);
  menuSettingsView.classList.toggle("is-hidden", !showSettings);
}

export function exitToMainMenu() {
  state.pendingStepAfterRoom = null;
  setStep("setup");
  closeMenu();
  if (state.roomCode) {
    send("leave_room");
  }
}

export function exitToGameSelection() {
  closeMenu();
  setStep("games");
  if (state.isHost && state.selectedGame !== "none" && currentGameIsActive()) {
    send("return_to_games");
  }
}
