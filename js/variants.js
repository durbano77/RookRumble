import { variantPickerEl, variantPickerHintEl, botDifficultySelect, botDescriptionEl } from "./dom.js";
import { defaultBotDifficulties, variantCardMeta, defaultVariantCardMeta } from "./constants.js";
import { state, send, currentGameIsActive, variantTitle } from "./state.js";

export function variantCardVisual(variantId) {
  return variantCardMeta[variantId] || defaultVariantCardMeta;
}

export function updateVariantPickerHint() {
  if (!variantPickerHintEl) return;

  if (!state.roomCode) {
    variantPickerHintEl.textContent = "Choose online or bot play first, then pick a mode.";
    return;
  }
  if (currentGameIsActive()) {
    variantPickerHintEl.textContent = "Use Back To Games from the board to reset before changing modes.";
    return;
  }
  if (!state.isHost) {
    variantPickerHintEl.textContent = "Waiting for the host to choose a game below.";
    return;
  }
  if (state.selectedGame === "none") {
    variantPickerHintEl.textContent = "Tap a card to choose what you are playing, then continue to the board.";
    return;
  }
  variantPickerHintEl.textContent = `${variantTitle()} selected. Continue to the board or pick another card.`;
}

export function renderVariantPicker() {
  variantPickerEl.innerHTML = "";
  updateVariantPickerHint();

  const canSelect = state.isHost && state.roomCode && !currentGameIsActive();

  for (const variant of state.availableGames) {
    const meta = variantCardVisual(variant.id);
    const isSelected = variant.id === state.selectedGame;

    const button = document.createElement("button");
    button.className = "game-card";
    button.type = "button";
    button.dataset.game = variant.id;
    button.classList.toggle("is-selected", isSelected);
    button.disabled = !canSelect;
    button.setAttribute(
      "aria-label",
      `${variant.label}. ${variant.description}${isSelected ? " Selected." : ""}`
    );

    const art = document.createElement("div");
    art.className = "game-card-art";
    art.style.background = meta.gradient;

    const icon = document.createElement("span");
    icon.className = "game-card-icon";
    icon.textContent = meta.icon;
    icon.setAttribute("aria-hidden", "true");

    const body = document.createElement("div");
    body.className = "game-card-body";

    const title = document.createElement("h3");
    title.className = "game-card-title";
    title.textContent = variant.label;

    const description = document.createElement("p");
    description.className = "game-card-desc";
    description.textContent = variant.description;

    art.append(icon);
    body.append(title, description);

    if (isSelected) {
      const badge = document.createElement("span");
      badge.className = "game-card-badge";
      badge.textContent = "Selected";
      body.prepend(badge);
    }

    button.append(art, body);
    button.addEventListener("click", () => {
      send("select_game", { game: variant.id });
    });
    variantPickerEl.append(button);
  }
}

export function renderBotSelector() {
  const selected = botDifficultySelect.value || "dougdoug";
  const options = state.botDifficulties.length ? state.botDifficulties : defaultBotDifficulties;
  const selectedExists = options.some((b) => b.id === selected);
  botDifficultySelect.innerHTML = "";

  for (const bot of options) {
    const option = document.createElement("option");
    option.value = bot.id;
    option.textContent = bot.label;
    option.title = bot.description;
    option.selected = selectedExists ? bot.id === selected : bot.id === "dougdoug";
    botDifficultySelect.append(option);
  }

  if (!selectedExists && !options.some((b) => b.id === "dougdoug")) {
    botDifficultySelect.value = options[0]?.id || "easy";
  }

  const activeBot = options.find((b) => b.id === botDifficultySelect.value);
  botDescriptionEl.textContent = activeBot?.description || "Choose your opponent's vibe.";
}
