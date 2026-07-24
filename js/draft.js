import {
  draftPanelEl, draftBudgetEl, draftPaletteEl,
  draftResetButton, draftSubmitButton, draftStatusEl,
} from "./dom.js";
import { pieceSymbols } from "./constants.js";
import { state, send, playerColor } from "./state.js";

const PIECE_ORDER = ["queen", "rook", "bishop", "knight", "pawn"];
const PIECE_LABELS = { queen: "Queen", rook: "Rook", bishop: "Bishop", knight: "Knight", pawn: "Pawn" };
const PIECE_LETTERS = { queen: "q", rook: "r", bishop: "b", knight: "n", pawn: "p" };
const DEFAULT_VALUES = { pawn: 1, knight: 3, bishop: 3, rook: 5, queen: 9 };

let localPlacements = new Map(); // square -> piece kind, cleared once a fresh draft phase begins
let armedPiece = null;
let submittedLocally = false;

export function isDrafting() {
  return state.game.gameState === "drafting";
}

function draftValues() {
  return state.game.variant?.draftPieceValues || DEFAULT_VALUES;
}

function draftBudget() {
  return state.game.variant?.draftBudget ?? 39;
}

function spentPoints() {
  const values = draftValues();
  let total = 0;
  for (const kind of localPlacements.values()) total += values[kind] || 0;
  return total;
}

function ownRanks() {
  return playerColor() === "black" ? ["7", "8"] : ["1", "2"];
}

function ownKingSquare() {
  return playerColor() === "black" ? "e8" : "e1";
}

export function isOwnDraftSquare(square) {
  return ownRanks().includes(square[1]) && square !== ownKingSquare();
}

export function hasSubmittedDraft() {
  const idx = state.playerIndex;
  if (idx !== 0 && idx !== 1) return false;
  return Boolean(state.game.variant?.draftReady?.[idx]);
}

export function draftLocalPieceAt(square) {
  if (!isDrafting() || hasSubmittedDraft()) return null;
  const kind = localPlacements.get(square);
  if (!kind) return null;
  return { symbol: PIECE_LETTERS[kind], color: playerColor() };
}

// A restart resets draftReady to [false, false] server-side — detect that
// transition here so a stale local army from a finished draft doesn't linger.
function syncDraftLifecycle() {
  if (!isDrafting()) {
    localPlacements = new Map();
    armedPiece = null;
    submittedLocally = false;
    return;
  }
  const ready = hasSubmittedDraft();
  if (!ready && submittedLocally) {
    localPlacements = new Map();
    armedPiece = null;
  }
  submittedLocally = ready;
}

export function handleDraftSquareClick(square) {
  if (!isDrafting() || hasSubmittedDraft() || !isOwnDraftSquare(square)) return;

  if (localPlacements.has(square)) {
    localPlacements.delete(square);
  } else if (armedPiece) {
    const cost = draftValues()[armedPiece] || 0;
    if (spentPoints() + cost > draftBudget()) return;
    localPlacements.set(square, armedPiece);
  }
  renderDraftPanel();
}

function pieceGlyph(kind) {
  return pieceSymbols[PIECE_LETTERS[kind]] || "?";
}

function renderPalette() {
  draftPaletteEl.innerHTML = "";
  const values = draftValues();
  const locked = hasSubmittedDraft();
  const remaining = draftBudget() - spentPoints();

  for (const kind of PIECE_ORDER) {
    const cost = values[kind] ?? DEFAULT_VALUES[kind];
    const button = document.createElement("button");
    button.type = "button";
    button.className = "draft-piece";
    button.classList.toggle("is-armed", armedPiece === kind);
    button.disabled = locked || cost > remaining;

    const glyph = document.createElement("span");
    glyph.className = "draft-piece-glyph";
    glyph.textContent = pieceGlyph(kind);
    const label = document.createElement("span");
    label.className = "draft-piece-label";
    label.textContent = PIECE_LABELS[kind];
    const costEl = document.createElement("span");
    costEl.className = "draft-piece-cost";
    costEl.textContent = cost;

    button.append(glyph, label, costEl);
    button.addEventListener("click", () => {
      armedPiece = armedPiece === kind ? null : kind;
      renderDraftPanel();
    });
    draftPaletteEl.append(button);
  }
}

export function renderDraftPanel() {
  syncDraftLifecycle();
  const active = isDrafting();
  draftPanelEl.classList.toggle("is-hidden", !active);
  if (!active) return;

  const locked = hasSubmittedDraft();
  const budget = draftBudget();

  draftBudgetEl.textContent = locked
    ? "Army locked"
    : `${budget - spentPoints()} / ${budget} pts left`;

  renderPalette();

  const idx = state.playerIndex;
  const opponentReady = Boolean(state.game.variant?.draftReady?.[idx === 0 ? 1 : 0]);

  draftStatusEl.textContent = locked
    ? opponentReady
      ? "Both armies locked — starting the match."
      : "Army locked in. Waiting for your opponent to finish drafting…"
    : "Pick a unit below, then tap a square on your first two ranks to place it. Tap a placed unit to remove it.";

  draftResetButton.disabled = locked || localPlacements.size === 0;
  draftSubmitButton.disabled = locked;
  draftSubmitButton.textContent = locked ? "Army Submitted" : "Submit Army";
}

export function resetDraft() {
  if (!isDrafting() || hasSubmittedDraft()) return;
  localPlacements = new Map();
  armedPiece = null;
  renderDraftPanel();
}

export function submitDraftArmy() {
  if (!isDrafting() || hasSubmittedDraft()) return;
  const placements = [...localPlacements.entries()].map(([square, kind]) => ({ type: kind, square }));
  send("submit_draft", { placements });
}
