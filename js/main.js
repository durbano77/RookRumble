import { applyAppearance, loadAppearance } from "./appearance.js";
import { connectSocket } from "./connection.js";
import { updateHud } from "./hud.js";
import { renderGame } from "./board.js";
import "./events.js"; // registers all event listeners as a side effect

applyAppearance(loadAppearance());
updateHud();
renderGame();
connectSocket();
