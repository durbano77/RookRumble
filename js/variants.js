import {
  variantPickerEl, variantPickerHintEl, botDifficultySelect, botDescriptionEl,
  gameSelectModal, gameModalKicker, gameModalDesc, timerGrid,
} from "./dom.js";
import { defaultBotDifficulties, variantCardMeta, defaultVariantCardMeta } from "./constants.js";
import { state, send, currentGameIsActive, variantTitle } from "./state.js";

let pendingVariantId = null;

export function variantCardVisual(variantId) {
  return variantCardMeta[variantId] || defaultVariantCardMeta;
}

export function openGameSelectModal(variantId) {
  const variant = state.availableGames.find((v) => v.id === variantId);
  if (!variant) return;
  pendingVariantId = variantId;
  gameModalKicker.textContent = variant.label;
  gameModalDesc.textContent = variant.description;
  for (const btn of timerGrid.querySelectorAll(".timer-option")) {
    btn.classList.toggle("is-selected", btn.dataset.minutes === "");
  }
  gameSelectModal.classList.remove("is-hidden");
}

export function confirmGameSelect() {
  if (!pendingVariantId) return;
  const selected = timerGrid.querySelector(".timer-option.is-selected");
  let timer = null;
  if (selected && selected.dataset.minutes !== "") {
    timer = {
      minutes: parseInt(selected.dataset.minutes, 10),
      increment: parseInt(selected.dataset.increment || "0", 10),
    };
  }
  send("select_game", { game: pendingVariantId, timer });
  gameSelectModal.classList.add("is-hidden");
  pendingVariantId = null;
  // Navigation to play step happens automatically via applySync
  // when the server confirms the selection and state.selectedGame updates.
}

export function closeGameSelectModal() {
  gameSelectModal.classList.add("is-hidden");
  pendingVariantId = null;
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
    variantPickerHintEl.textContent = "Tap a card to choose your game and timer, then head to the board.";
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
      openGameSelectModal(variant.id);
    });
    variantPickerEl.append(button);
  }
}

export function renderBotSelector() {
  const selected = botDifficultySelect.value || "dougdoug";
  const options = state.botDifficulties.length ? state.botDifficulties : defaultBotDifficulties;
  const selectedExists = options.some((b) => b.id === selected);
  botDifficultySelect.innerHTML = "";

  const personalityBots = options.filter((b) => !b.engine);
  const engineBots = options.filter((b) => b.engine);

  if (engineBots.length > 0) {
    const personalityGroup = document.createElement("optgroup");
    personalityGroup.label = "Personality Bots";
    for (const bot of personalityBots) {
      const option = document.createElement("option");
      option.value = bot.id;
      option.textContent = bot.label;
      option.title = bot.description;
      option.selected = selectedExists ? bot.id === selected : bot.id === "dougdoug";
      personalityGroup.append(option);
    }
    botDifficultySelect.append(personalityGroup);

    const engineGroup = document.createElement("optgroup");
    engineGroup.label = "Stockfish Engine";
    for (const bot of engineBots) {
      const option = document.createElement("option");
      option.value = bot.id;
      option.textContent = bot.label;
      option.title = bot.description;
      option.selected = selectedExists ? bot.id === selected : false;
      engineGroup.append(option);
    }
    botDifficultySelect.append(engineGroup);
  } else {
    for (const bot of options) {
      const option = document.createElement("option");
      option.value = bot.id;
      option.textContent = bot.label;
      option.title = bot.description;
      option.selected = selectedExists ? bot.id === selected : bot.id === "dougdoug";
      botDifficultySelect.append(option);
    }
  }

  if (!selectedExists && !options.some((b) => b.id === "dougdoug")) {
    botDifficultySelect.value = options[0]?.id || "easy";
  }

  const activeBot = options.find((b) => b.id === botDifficultySelect.value);
  botDescriptionEl.textContent = activeBot?.description || "Choose your opponent's vibe.";
}
