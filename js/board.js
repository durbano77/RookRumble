import {
  chessBoardEl, chessTurnEl, chessResultEl,
  mutatorPanelEl, mutatorOptionsEl, mutatorTitleEl,
  promotionPanelEl, moveListEl,
} from "./dom.js";
import { pieceSymbols } from "./constants.js";
import {
  state, send, playerColor, isMyTurn, pendingMutator, isMyMutatorChoice, variantTitle,
} from "./state.js";

// ── Drag & drop ────────────────────────────────────────────────────────────

let dragState = null;  // { fromSquare, ghost, moved }
let ignoreNextClick = false;

function startDrag(e, square) {
  if (!isMyTurn() || state.pendingPromotion || pendingMutator()) return;
  const piece = state.game.board?.[square];
  if (!piece || piece.color !== playerColor() || legalMovesFrom(square).length === 0) return;

  e.preventDefault(); // Prevent text selection (mouse) and page scroll (touch)

  const clientX = e.touches ? e.touches[0].clientX : e.clientX;
  const clientY = e.touches ? e.touches[0].clientY : e.clientY;

  state.selectedSquare = square;
  renderChessBoard();

  const ghost = document.createElement("div");
  ghost.className = "drag-ghost";
  ghost.classList.add(piece.color === "white" ? "piece-white" : "piece-black");
  ghost.textContent = pieceText(piece.symbol);
  ghost.style.left = `${clientX}px`;
  ghost.style.top = `${clientY}px`;
  document.body.append(ghost);

  chessBoardEl.style.touchAction = "none";
  dragState = { fromSquare: square, ghost, moved: false };
}

function onDragMove(e) {
  if (!dragState) return;
  e.preventDefault(); // Prevent scroll on touch while dragging a piece

  const clientX = e.touches ? e.touches[0].clientX : e.clientX;
  const clientY = e.touches ? e.touches[0].clientY : e.clientY;
  dragState.moved = true;
  dragState.ghost.style.left = `${clientX}px`;
  dragState.ghost.style.top = `${clientY}px`;
}

function onDragEnd(e) {
  if (!dragState) return;

  const clientX = e.changedTouches ? e.changedTouches[0].clientX : e.clientX;
  const clientY = e.changedTouches ? e.changedTouches[0].clientY : e.clientY;
  const { fromSquare, ghost, moved } = dragState;

  dragState = null;
  ghost.remove();
  chessBoardEl.style.touchAction = "";

  if (!moved) return; // No meaningful movement — let the click event handle it

  ignoreNextClick = true;

  // Find drop target by bounding rect — more reliable than elementFromPoint when
  // other elements overlap the board (panels, modals, etc.)
  let targetSquare = null;
  for (const sq of chessBoardEl.querySelectorAll("[data-square]")) {
    const r = sq.getBoundingClientRect();
    if (clientX >= r.left && clientX <= r.right && clientY >= r.top && clientY <= r.bottom) {
      targetSquare = sq.dataset.square;
      break;
    }
  }

  if (targetSquare && isLegalTarget(targetSquare)) {
    const matchingMoves = legalMovesFrom(fromSquare).filter(m => m.to === targetSquare);
    if (matchingMoves.some(m => m.promotion)) {
      state.pendingPromotion = { from: fromSquare, to: targetSquare };
      promotionPanelEl.classList.remove("is-hidden");
    } else {
      send("chess_move", { from: fromSquare, to: targetSquare, promotion: null });
      state.selectedSquare = null;
    }
  }

  renderChessBoard();
}

document.addEventListener("mousemove", onDragMove);
document.addEventListener("mouseup", onDragEnd);
document.addEventListener("touchmove", onDragMove, { passive: false });
document.addEventListener("touchend", onDragEnd, { passive: false });

function pieceText(symbol) {
  return pieceSymbols[symbol] || symbol;
}

function squareIsLight(square) {
  const file = square.charCodeAt(0) - "a".charCodeAt(0);
  const rank = Number(square[1]) - 1;
  return (file + rank) % 2 === 1;
}

export function chessSquaresForPlayer() {
  const files = ["a", "b", "c", "d", "e", "f", "g", "h"];
  const ranks = ["8", "7", "6", "5", "4", "3", "2", "1"];

  if (playerColor() === "black") {
    return ranks.flatMap((rank) => files.slice().reverse().map((file) => `${file}${rank}`));
  }
  return ranks.flatMap((rank) => files.map((file) => `${file}${rank}`));
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
  if (!variant) return state.game.message || "Choose a variant";
  if (variant.id === "dice" && variant.dicePiece) return `${variant.label}: ${variant.dicePiece}`;
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

export function renderChessBoard() {
  const game = state.game;
  const board = game.board || {};
  const legalFromSquares = new Set(Object.keys(game.legalMoves || {}));
  const fogSquares = new Set(game.hiddenSquares || []);

  chessTurnEl.textContent =
    game.gameState === "playing"
      ? `${game.turn === "white" ? "White" : "Black"} to move`
      : variantTitle();
  chessResultEl.textContent =
    game.result ? `${game.message} (${game.result})` : variantBadgeText();
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
    if (legalFromSquares.has(square) && isMyTurn()) {
      cell.addEventListener("mousedown", (e) => startDrag(e, square));
      cell.addEventListener("touchstart", (e) => startDrag(e, square), { passive: false });
    }
    chessBoardEl.append(cell);
  }
}

export function handleChessSquareClick(square) {
  if (ignoreNextClick) { ignoreNextClick = false; return; }
  if (!isMyTurn() || state.pendingPromotion || pendingMutator()) return;

  const piece = state.game.board?.[square];
  const color = playerColor();

  if (state.selectedSquare && isLegalTarget(square)) {
    const matchingMoves = legalMovesFrom(state.selectedSquare).filter((m) => m.to === square);
    const promotionMoves = matchingMoves.filter((m) => m.promotion);

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

function renderMoveList() {
  const moves = state.game.moveHistorySan || [];
  if (moves.length === 0) {
    moveListEl.innerHTML = "";
    return;
  }

  const cells = [];
  for (let i = 0; i < moves.length; i += 2) {
    const n = Math.floor(i / 2) + 1;
    cells.push(`<span class="move-number">${n}.</span>`);
    cells.push(`<span class="move-san">${moves[i]}</span>`);
    cells.push(`<span class="move-san">${moves[i + 1] ?? ""}</span>`);
  }
  moveListEl.innerHTML = cells.join("");
  moveListEl.scrollTop = moveListEl.scrollHeight;
}

export function renderGame() {
  renderChessBoard();
  renderMoveList();
}
