import {
  themeSelect, patternSelect, boardSelect, pieceSelect,
} from "./dom.js";
import { appearanceStorageKey, appearanceOptions } from "./constants.js";

export function loadAppearance() {
  try {
    return JSON.parse(window.localStorage.getItem(appearanceStorageKey)) || {};
  } catch (_error) {
    return {};
  }
}

function validValue(kind, value, fallback) {
  return appearanceOptions[kind].includes(value) ? value : fallback;
}

export function applyAppearance(nextAppearance = {}) {
  const appearance = {
    theme:   validValue("theme",   nextAppearance.theme   || themeSelect.value,   "forest"),
    pattern: validValue("pattern", nextAppearance.pattern || patternSelect.value, "argyle"),
    board:   validValue("board",   nextAppearance.board   || boardSelect.value,   "classic"),
    pieces:  validValue("pieces",  nextAppearance.pieces  || pieceSelect.value,   "classic"),
  };

  document.body.dataset.theme   = appearance.theme;
  document.body.dataset.pattern = appearance.pattern;
  document.body.dataset.board   = appearance.board;
  document.body.dataset.pieces  = appearance.pieces;

  themeSelect.value   = appearance.theme;
  patternSelect.value = appearance.pattern;
  boardSelect.value   = appearance.board;
  pieceSelect.value   = appearance.pieces;

  window.localStorage.setItem(appearanceStorageKey, JSON.stringify(appearance));
}
