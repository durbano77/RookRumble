const serverUrlEl = document.getElementById("server-url");
const roomCodeDisplayEl = document.getElementById("room-code-display");
const connectionStateEl = document.getElementById("connection-state");
const connectionHintEl = document.getElementById("connection-hint");
const roomCodeInput = document.getElementById("room-code-input");
const createRoomButton = document.getElementById("create-room");
const playBotButton = document.getElementById("play-bot");
const botDifficultySelect = document.getElementById("bot-difficulty");
const botDescriptionEl = document.getElementById("bot-description");
const joinRoomButton = document.getElementById("join-room");
const leaveRoomButton = document.getElementById("leave-room");
const variantPickerEl = document.getElementById("variant-picker");
const variantPickerHintEl = document.getElementById("variant-picker-hint");
const score1El = document.getElementById("score1");
const score2El = document.getElementById("score2");
const player1StateEl = document.getElementById("player1-state");
const player2StateEl = document.getElementById("player2-state");
const roleDisplayEl = document.getElementById("role-display");
const roleHintEl = document.getElementById("role-hint");
const statusEl = document.getElementById("status");
const startMatchButton = document.getElementById("start-match");
const pauseMatchButton = document.getElementById("pause-match");
const restartMatchButton = document.getElementById("restart-match");
const chessBoardEl = document.getElementById("chess-board");
const chessTurnEl = document.getElementById("chess-turn");
const chessResultEl = document.getElementById("chess-result");
const mutatorPanelEl = document.getElementById("mutator-panel");
const mutatorOptionsEl = document.getElementById("mutator-options");
const mutatorTitleEl = document.getElementById("mutator-title");
const promotionPanelEl = document.getElementById("promotion-panel");
const overlayEl = document.getElementById("overlay");
const overlayKickerEl = document.getElementById("overlay-kicker");
const overlayTitleEl = document.getElementById("overlay-title");
const overlayTextEl = document.getElementById("overlay-text");
const overlayActionButton = document.getElementById("overlay-action");
const themeSelect = document.getElementById("theme-select");
const patternSelect = document.getElementById("pattern-select");
const boardSelect = document.getElementById("board-select");
const pieceSelect = document.getElementById("piece-select");
const continueToPlayButton = document.getElementById("continue-to-play");
const backToSetupButton = document.getElementById("back-to-setup");
const playBackToGamesButton = document.getElementById("play-back-to-games");
const playBackToSetupButton = document.getElementById("play-back-to-setup");
const menuButton = document.getElementById("menu-button");
const menuModal = document.getElementById("menu-modal");
const menuMainView = document.getElementById("menu-main-view");
const menuSettingsView = document.getElementById("menu-settings-view");
const closeMenuButton = document.getElementById("close-menu");
const menuExitMainButton = document.getElementById("menu-exit-main");
const menuExitGamesButton = document.getElementById("menu-exit-games");
const menuOpenSettingsButton = document.getElementById("menu-open-settings");
const settingsBackButton = document.getElementById("settings-back");
const stepButtons = [...document.querySelectorAll("[data-step-target]")];
const stepPanels = [...document.querySelectorAll("[data-step-panel]")];

const appearanceStorageKey = "rook-rumble-appearance";
const appearanceOptions = {
  theme: ["forest", "midnight", "paper", "ocean", "berry"],
  pattern: ["argyle", "dots", "grid", "plain"],
  board: ["classic", "slate", "sand", "contrast"],
  pieces: ["classic", "three_d", "woodcut", "marble"],
};

const pieceSymbols = {
  P: "♟",
  N: "♞",
  B: "♝",
  R: "♜",
  Q: "♛",
  K: "♚",
  p: "♟",
  n: "♞",
  b: "♝",
  r: "♜",
  q: "♛",
  k: "♚",
};

const defaultVariants = [
  { id: "classic", label: "Classic", description: "Regular chess, clean and familiar." },
  { id: "three_check", label: "Three-Check", description: "Win by checking the enemy king three times." },
  { id: "king_hill", label: "King of the Hill", description: "Win by marching your king into the center." },
  { id: "atomic", label: "Atomic", description: "Captures explode nearby pieces." },
  { id: "dice", label: "Dice Chess", description: "A die chooses which piece type must move." },
  { id: "fog", label: "Fog of War", description: "You only see what your army can reach." },
  { id: "thress", label: "Thress", description: "Every third move, pick one of three silly rule cards." },
];

const variantCardMeta = {
  classic: {
    icon: "♔",
    gradient: "linear-gradient(160deg, #ffeaa7 0%, #fdcb6e 55%, #e17055 100%)",
  },
  three_check: {
    icon: "♚",
    gradient: "linear-gradient(160deg, #fab1a0 0%, #ff7675 55%, #d63031 100%)",
  },
  king_hill: {
    icon: "⛰",
    gradient: "linear-gradient(160deg, #55efc4 0%, #00b894 55%, #0984e3 100%)",
  },
  atomic: {
    icon: "💥",
    gradient: "linear-gradient(160deg, #ffeaa7 0%, #fd79a8 50%, #e84393 100%)",
  },
  dice: {
    icon: "🎲",
    gradient: "linear-gradient(160deg, #a29bfe 0%, #6c5ce7 55%, #341f97 100%)",
  },
  fog: {
    icon: "🌫",
    gradient: "linear-gradient(160deg, #dfe6e9 0%, #b2bec3 55%, #636e72 100%)",
  },
  thress: {
    icon: "🃏",
    gradient: "linear-gradient(160deg, #fd79a8 0%, #fdcb6e 50%, #00cec9 100%)",
  },
};

const defaultVariantCardMeta = {
  icon: "♟",
  gradient: "linear-gradient(160deg, #dfe6e9 0%, #b2bec3 55%, #636e72 100%)",
};

const defaultBotDifficulties = [
  { id: "easy", label: "Easy Explorer", description: "Mostly random legal moves while it learns what the pieces do." },
  { id: "medium", label: "Balanced Club Bot", description: "A normal casual opponent that likes sensible tactics." },
  { id: "hard", label: "Hard Grinder", description: "Low-chaos material play with sharper tactical priorities." },
  { id: "dougdoug", label: "DougDoug Chaos", description: "Unofficially inspired by streamer-brain chess: fearless, confused, funny." },
  { id: "greedy_goblin", label: "Greedy Goblin", description: "If it can capture something, it probably will." },
  { id: "coffeehouse", label: "Coffeehouse Attacker", description: "Checks, threats, sacrifices, vibes. Hates quiet positions." },
  { id: "gotham", label: "Gotham Tactics", description: "Unofficial GothamChess-flavored bot: tactical, instructive, and solid." },
  { id: "magnus", label: "Magnus-ish Endboss", description: "Unofficial elite-flavored bot: calm, flexible, and hard to trick." },
];

const state = {
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
};

let pendingStepAfterRoom = null;

serverUrlEl.textContent = window.location.origin;

function loadAppearance() {
  try {
    return JSON.parse(window.localStorage.getItem(appearanceStorageKey)) || {};
  } catch (_error) {
    return {};
  }
}

function validAppearanceValue(kind, value, fallback) {
  return appearanceOptions[kind].includes(value) ? value : fallback;
}

function applyAppearance(nextAppearance = {}) {
  const appearance = {
    theme: validAppearanceValue("theme", nextAppearance.theme || themeSelect.value, "forest"),
    pattern: validAppearanceValue("pattern", nextAppearance.pattern || patternSelect.value, "argyle"),
    board: validAppearanceValue("board", nextAppearance.board || boardSelect.value, "classic"),
    pieces: validAppearanceValue("pieces", nextAppearance.pieces || pieceSelect.value, "classic"),
  };

  document.body.dataset.theme = appearance.theme;
  document.body.dataset.pattern = appearance.pattern;
  document.body.dataset.board = appearance.board;
  document.body.dataset.pieces = appearance.pieces;

  themeSelect.value = appearance.theme;
  patternSelect.value = appearance.pattern;
  boardSelect.value = appearance.board;
  pieceSelect.value = appearance.pieces;

  window.localStorage.setItem(appearanceStorageKey, JSON.stringify(appearance));
  renderChessBoard();
}

function pieceText(symbol) {
  return pieceSymbols[symbol] || symbol;
}

function openMenu(view = "main") {
  menuModal.classList.remove("is-hidden");
  showMenuView(view);
}

function closeMenu() {
  menuModal.classList.add("is-hidden");
}

function showMenuView(view) {
  const showSettings = view === "settings";
  menuMainView.classList.toggle("is-hidden", showSettings);
  menuSettingsView.classList.toggle("is-hidden", !showSettings);
}

function exitToMainMenu() {
  pendingStepAfterRoom = null;
  setStep("setup");
  closeMenu();
  if (state.roomCode) {
    send("leave_room");
  }
}

function exitToGameSelection() {
  closeMenu();
  setStep("games");
  if (state.isHost && state.selectedGame !== "none" && currentGameIsActive()) {
    send("return_to_games");
  }
}

function canShowStep(step) {
  if (step === "setup") {
    return true;
  }
  if (step === "games") {
    return Boolean(state.roomCode);
  }
  if (step === "play") {
    return Boolean(state.roomCode && state.selectedGame !== "none");
  }
  return false;
}

function setStep(step) {
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

function websocketUrl() {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}/ws`;
}

function canSend() {
  return state.ws && state.ws.readyState === WebSocket.OPEN;
}

function send(type, payload = {}) {
  if (canSend()) {
    state.ws.send(JSON.stringify({ type, ...payload }));
  }
}

function variantTitle(variantId = state.selectedGame) {
  return (
    state.availableGames.find((variant) => variant.id === variantId)?.label ||
    "Chess"
  );
}

function botLabel() {
  return (
    state.bot.label ||
    state.botDifficulties.find((bot) => bot.id === state.bot.difficulty)?.label ||
    "Bot"
  );
}

function renderBotSelector() {
  const selected = botDifficultySelect.value || "dougdoug";
  const options = state.botDifficulties.length ? state.botDifficulties : defaultBotDifficulties;
  const selectedExists = options.some((bot) => bot.id === selected);
  botDifficultySelect.innerHTML = "";

  for (const bot of options) {
    const option = document.createElement("option");
    option.value = bot.id;
    option.textContent = bot.label;
    option.title = bot.description;
    option.selected = selectedExists ? bot.id === selected : bot.id === "dougdoug";
    botDifficultySelect.append(option);
  }

  if (!selectedExists && !options.some((bot) => bot.id === "dougdoug")) {
    botDifficultySelect.value = options.some((bot) => bot.id === "dougdoug")
      ? "dougdoug"
      : options[0]?.id || "easy";
  }

  const activeBot = options.find((bot) => bot.id === botDifficultySelect.value);
  botDescriptionEl.textContent = activeBot?.description || "Choose your opponent's vibe.";
}

function showOverlay({ kicker, title, text, actionLabel, hidden, disabled = false }) {
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

function playerColor() {
  if (state.playerIndex === 0) {
    return "white";
  }
  if (state.playerIndex === 1) {
    return "black";
  }
  return null;
}

function isMyTurn() {
  return (
    state.game.gameState === "playing" &&
    playerColor() === state.game.turn
  );
}

function pendingMutator() {
  return state.game.variant?.pendingMutator || null;
}

function isMyMutatorChoice() {
  const pending = pendingMutator();
  return Boolean(pending && pending.chooser === playerColor());
}

function currentGameIsActive() {
  return ["playing", "paused"].includes(state.game.gameState);
}

function variantCardVisual(variantId) {
  return variantCardMeta[variantId] || defaultVariantCardMeta;
}

function updateVariantPickerHint() {
  if (!variantPickerHintEl) {
    return;
  }

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

function renderVariantPicker() {
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

function updateButtons() {
  const connected = state.connectionState === "connected";
  const inRoom = Boolean(state.roomCode);
  const bothPlayersConnected = state.players.every((player) => player.connected);
  const hostReady = connected && inRoom && state.isHost;
  const hasSelectedVariant = state.selectedGame !== "none";

  renderBotSelector();
  createRoomButton.disabled = !connected;
  playBotButton.disabled = !connected;
  botDifficultySelect.disabled = !connected;
  joinRoomButton.disabled = !connected;
  leaveRoomButton.disabled = !inRoom;
  startMatchButton.disabled =
    !hostReady || !bothPlayersConnected || !hasSelectedVariant || currentGameIsActive();
  pauseMatchButton.disabled =
    !hostReady || !hasSelectedVariant || !["playing", "paused"].includes(state.game.gameState);
  pauseMatchButton.textContent = state.game.gameState === "paused" ? "Resume" : "Pause";
  restartMatchButton.disabled = !hostReady || !bothPlayersConnected || !hasSelectedVariant;
  continueToPlayButton.disabled = !inRoom || !hasSelectedVariant;
  backToSetupButton.disabled = !connected;
  playBackToGamesButton.disabled = !inRoom || !hasSelectedVariant;
  playBackToSetupButton.disabled = !connected;
  menuExitMainButton.disabled = !connected && !inRoom;
  menuExitGamesButton.disabled = !inRoom;
  renderVariantPicker();
  setStep(state.uiStep);
}

function updateHud() {
  const game = state.game;

  roomCodeDisplayEl.textContent = state.roomCode || "----";
  connectionStateEl.textContent =
    state.connectionState === "connected" ? "Connected" : "Disconnected";
  connectionHintEl.textContent =
    state.connectionState === "connected"
      ? "Chess room sync is active."
      : "Trying to reach the chess server.";

  score1El.textContent = "White";
  score2El.textContent = state.bot.enabled ? botLabel() : "Black";
  player1StateEl.textContent = state.players[0].connected
    ? game.turn === "white" && game.gameState === "playing"
      ? "To move"
      : "Connected"
    : "Waiting";
  player2StateEl.textContent = state.players[1].connected
    ? game.turn === "black" && game.gameState === "playing"
      ? state.bot.enabled
        ? "Bot to move"
        : "To move"
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

function syncOverlay() {
  const bothPlayersConnected = state.players.every((player) => player.connected);

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
      text: state.isHost
        ? "Pick a card from the Games shelf below."
        : "Waiting for the host to pick a game.",
      actionLabel: state.isHost ? "Choose Below" : "Waiting...",
      disabled: true,
    });
    return;
  }

  if (["waiting", "ready"].includes(state.game.gameState)) {
    showOverlay({
      kicker: `Room ${state.roomCode}`,
      title: `${variantTitle()} Ready`,
      text: bothPlayersConnected
        ? state.bot.enabled
          ? `${botLabel()} is ready. Start whenever you are ready.`
          : state.isHost
            ? "Both players are connected. Start whenever you are ready."
            : "Both players are connected. Waiting for the host to start."
        : "Waiting for another player to join this room.",
      actionLabel: state.isHost ? "Start" : "Waiting...",
      disabled: !state.isHost || !bothPlayersConnected,
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

function chessSquaresForPlayer() {
  const files = ["a", "b", "c", "d", "e", "f", "g", "h"];
  const ranks = ["8", "7", "6", "5", "4", "3", "2", "1"];

  if (playerColor() === "black") {
    return ranks.flatMap((rank) => files.slice().reverse().map((file) => `${file}${rank}`));
  }

  return ranks.flatMap((rank) => files.map((file) => `${file}${rank}`));
}

function squareIsLight(square) {
  const file = square.charCodeAt(0) - "a".charCodeAt(0);
  const rank = Number(square[1]) - 1;
  return (file + rank) % 2 === 1;
}

function legalMovesFrom(square) {
  return state.game.legalMoves?.[square] || [];
}

function isLegalTarget(square) {
  return Boolean(
    state.selectedSquare &&
      legalMovesFrom(state.selectedSquare).some((move) => move.to === square)
  );
}

function isLastMoveSquare(square) {
  return (
    state.game.lastMove &&
    (state.game.lastMove.from === square || state.game.lastMove.to === square)
  );
}

function variantBadgeText() {
  const variant = state.game.variant;
  if (!variant) {
    return state.game.message || "Choose a variant";
  }

  if (variant.id === "dice" && variant.dicePiece) {
    return `${variant.label}: ${variant.dicePiece}`;
  }

  if (variant.id === "three_check" && variant.checks) {
    return `${variant.label}: W ${variant.checks.white}/3, B ${variant.checks.black}/3`;
  }

  if (variant.id === "thress" && variant.pendingMutator) {
    return `${variant.label}: ${variant.pendingMutator.chooser} picks a card`;
  }

  return variant.label;
}

function renderMutatorPanel() {
  const pending = pendingMutator();
  mutatorOptionsEl.innerHTML = "";

  if (!pending) {
    mutatorPanelEl.classList.add("is-hidden");
    return;
  }

  mutatorTitleEl.textContent = isMyMutatorChoice()
    ? "Pick one Thress card before moving"
    : `${pending.chooser === "white" ? "White" : "Black"} is choosing a Thress card`;

  for (const option of pending.options || []) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "mutator-card";
    button.disabled = !isMyMutatorChoice();

    const name = document.createElement("span");
    name.textContent = option.name;
    const description = document.createElement("strong");
    description.textContent = option.description;

    button.append(name, description);
    button.addEventListener("click", () => {
      send("choose_mutator", { mutatorId: option.id });
    });
    mutatorOptionsEl.append(button);
  }

  mutatorPanelEl.classList.remove("is-hidden");
}

function renderChessBoard() {
  const game = state.game;
  const board = game.board || {};
  const legalFromSquares = new Set(Object.keys(game.legalMoves || {}));
  const fogSquares = new Set(game.hiddenSquares || []);

  chessTurnEl.textContent =
    game.gameState === "playing"
      ? `${game.turn === "white" ? "White" : "Black"} to move`
      : variantTitle();
  chessResultEl.textContent = game.result ? `${game.message} (${game.result})` : variantBadgeText();
  renderMutatorPanel();
  chessBoardEl.innerHTML = "";

  for (const square of chessSquaresForPlayer()) {
    const piece = board[square];
    const cell = document.createElement("button");
    cell.type = "button";
    cell.className = "chess-square";
    cell.dataset.square = square;
    cell.classList.add(squareIsLight(square) ? "light" : "dark");
    cell.classList.toggle("is-selected", state.selectedSquare === square);
    cell.classList.toggle("is-target", isLegalTarget(square));
    cell.classList.toggle("is-last-move", isLastMoveSquare(square));
    cell.classList.toggle("is-movable", legalFromSquares.has(square) && isMyTurn());
    cell.classList.toggle("is-fog", fogSquares.has(square));
    cell.classList.toggle("has-piece", Boolean(piece));
    cell.classList.toggle("piece-white", piece?.color === "white");
    cell.classList.toggle("piece-black", piece?.color === "black");
    cell.textContent = piece ? pieceText(piece.symbol) : "";
    cell.setAttribute("aria-label", piece ? `${piece.color} ${piece.type} on ${square}` : square);
    cell.addEventListener("click", () => handleChessSquareClick(square));
    chessBoardEl.append(cell);
  }
}

function handleChessSquareClick(square) {
  if (!isMyTurn() || state.pendingPromotion || pendingMutator()) {
    return;
  }

  const piece = state.game.board?.[square];
  const color = playerColor();

  if (state.selectedSquare && isLegalTarget(square)) {
    const matchingMoves = legalMovesFrom(state.selectedSquare).filter((move) => move.to === square);
    const promotionMoves = matchingMoves.filter((move) => move.promotion);

    if (promotionMoves.length > 0) {
      state.pendingPromotion = { from: state.selectedSquare, to: square };
      promotionPanelEl.classList.remove("is-hidden");
      return;
    }

    send("chess_move", { from: state.selectedSquare, to: square, promotion: null });
    state.selectedSquare = null;
    renderChessBoard();
    return;
  }

  if (piece && piece.color === color && legalMovesFrom(square).length > 0) {
    state.selectedSquare = square;
  } else {
    state.selectedSquare = null;
  }

  renderChessBoard();
}

function renderGame() {
  renderChessBoard();
}

function applySync(payload) {
  state.roomCode = payload.roomCode || "";
  state.selectedGame = payload.selectedGame || "none";
  state.availableGames = payload.availableGames || defaultVariants;
  state.playerIndex =
    typeof payload.playerIndex === "number" ? payload.playerIndex : null;
  state.isHost = Boolean(payload.isHost);
  state.bot = payload.bot || { enabled: false, difficulty: null, label: null, color: null };
  state.botDifficulties = payload.botDifficulties || defaultBotDifficulties;
  state.players = payload.players || state.players;
  state.game = payload.game || state.game;

  if (!state.roomCode) {
    pendingStepAfterRoom = null;
    setStep("setup");
  } else if (pendingStepAfterRoom) {
    setStep(pendingStepAfterRoom);
    pendingStepAfterRoom = null;
  }

  if (state.game.gameState !== "playing") {
    state.selectedSquare = null;
    state.pendingPromotion = null;
    promotionPanelEl.classList.add("is-hidden");
  }

  updateHud();
  renderGame();
}

function setConnectionState(nextState) {
  state.connectionState = nextState;
  updateHud();
}

function connectSocket() {
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
    pendingStepAfterRoom = null;
    setStep("setup");
    updateHud();
    renderGame();
    window.setTimeout(connectSocket, 1200);
  });

  ws.addEventListener("error", () => {
    ws.close();
  });
}

for (const button of promotionPanelEl.querySelectorAll("[data-promotion]")) {
  button.addEventListener("click", () => {
    if (!state.pendingPromotion) {
      return;
    }

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

createRoomButton.addEventListener("click", () => {
  pendingStepAfterRoom = "games";
  send("create_room");
});

playBotButton.addEventListener("click", () => {
  pendingStepAfterRoom = "games";
  send("create_bot_room", { difficulty: botDifficultySelect.value });
});

joinRoomButton.addEventListener("click", () => {
  const roomCode = roomCodeInput.value.trim();
  pendingStepAfterRoom = "games";
  send("join_room", { roomCode });
});

leaveRoomButton.addEventListener("click", () => {
  pendingStepAfterRoom = null;
  setStep("setup");
  send("leave_room");
});

startMatchButton.addEventListener("click", () => {
  send("start_game");
});

pauseMatchButton.addEventListener("click", () => {
  send("toggle_pause");
});

restartMatchButton.addEventListener("click", () => {
  send("restart_game");
});

overlayActionButton.addEventListener("click", () => {
  if (!state.roomCode) {
    pendingStepAfterRoom = "games";
    send("create_room");
    return;
  }

  if (!state.isHost || state.selectedGame === "none") {
    return;
  }

  if (["waiting", "ready"].includes(state.game.gameState)) {
    send("start_game");
    return;
  }

  if (state.game.gameState === "paused") {
    send("toggle_pause");
    return;
  }

  if (state.game.gameState === "gameover") {
    send("restart_game");
  }
});

roomCodeInput.addEventListener("input", () => {
  roomCodeInput.value = roomCodeInput.value.replace(/\D/g, "").slice(0, 6);
});

botDifficultySelect.addEventListener("change", () => {
  renderBotSelector();
});

continueToPlayButton.addEventListener("click", () => {
  setStep("play");
});

backToSetupButton.addEventListener("click", () => {
  exitToMainMenu();
});

playBackToGamesButton.addEventListener("click", () => {
  exitToGameSelection();
});

playBackToSetupButton.addEventListener("click", () => {
  exitToMainMenu();
});

for (const button of stepButtons) {
  button.addEventListener("click", () => {
    setStep(button.dataset.stepTarget);
  });
}

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

menuButton.addEventListener("click", () => {
  openMenu("main");
});

closeMenuButton.addEventListener("click", () => {
  closeMenu();
});

menuExitMainButton.addEventListener("click", () => {
  exitToMainMenu();
});

menuExitGamesButton.addEventListener("click", () => {
  exitToGameSelection();
});

menuOpenSettingsButton.addEventListener("click", () => {
  showMenuView("settings");
});

settingsBackButton.addEventListener("click", () => {
  showMenuView("main");
});

menuModal.addEventListener("click", (event) => {
  if (event.target === menuModal) {
    closeMenu();
  }
});

window.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !menuModal.classList.contains("is-hidden")) {
    closeMenu();
  }
});

applyAppearance(loadAppearance());
updateHud();
renderGame();
connectSocket();
