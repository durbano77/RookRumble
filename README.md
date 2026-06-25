# Rook Rumble — Casual Chess Club

Rook Rumble is a casual chess platform: classic chess plus playful variants, playable on LAN (desktop and mobile), against another player or against personality-driven bots. The vibe is a friendly chess clubhouse with chaotic modes—not a serious chess server.

**Stack:** vanilla HTML/CSS/JS client + Python (`aiohttp` + `python-chess`) WebSocket server. No build step, no frontend framework, no database.

---

## Quick start

```bash
pip install -r requirements.txt
python server.py
```

- **Local:** `http://localhost:8000`
- **LAN:** the server prints a LAN URL (binds `0.0.0.0`, port from `PORT` env var, default `8000`)

Open the URL on two devices to play multiplayer, or use **Play Bot** for single-player.

---

## Repository layout

| File | Purpose |
|------|---------|
| `server.py` | HTTP static server, WebSocket handler, rooms, game logic, bot AI, variant rules |
| `game.js` | Browser client: WebSocket sync, 3-step UI flow, appearance controls, game shelf rendering, board rendering, move input, overlays |
| `index.html` | Page structure: hero, flow bar, appearance controls, setup panel, Games hub, chess board, overlays |
| `styles.css` | Theme system, mobile-first responsive layout, game cards, board/piece skins, chess board styling |
| `requirements.txt` | `aiohttp==3.13.5`, `chess==1.11.2` |

There is no `package.json`, test suite, or build pipeline. Changes to static files are picked up on refresh; restart `server.py` after Python changes.

---

## Architecture

```
Browser (game.js)  ──WebSocket /ws──►  server.py (authoritative)
       │                                      │
       └── HTTP GET /, /game.js, /styles.css  └── python-chess boards + variants
```

**Authoritative server:** clients send *intents* (create room, move, pick mutator). The server validates with `python-chess`, updates state, and broadcasts a full `sync` payload. Clients never apply moves locally without server confirmation.

**Per-viewer state:** Fog of War builds different `board` and `legalMoves` per player index in `ChessVariantGame.snapshot(viewer_index)`.

**Room model:** Each room has a 6-digit numeric code, two player slots (White=0, Black=1), one host, optional bot filling Black, one active `ChessVariantGame`, and a selected variant id. The server caps live rooms at `MAX_ROOMS = 1000`; `create_room` and `create_bot_room` return an error if that limit is reached, preventing unbounded memory growth and an infinite loop in `create_room_code`.

---

## Game flow

1. Client opens on **Step 1: Opponent**, choosing online room play or offline bot play.
2. **Create Room** → host assigned White, room code issued; **Join Room** assigns Black; **Play Bot** creates a bot room with the bot occupying Black.
3. The UI advances to **Step 2: Game**, where the host selects a variant from the Games shelf.
4. **Continue To Board** opens **Step 3: Play**, where the host starts the selected game.
5. Moves alternate; bot moves run immediately after human moves in bot rooms.
6. Host may **Pause/Resume**, **Restart**, **Back To Games**, or **Back To Opponent**.

**Game states:** `waiting` → `ready` → `playing` | `paused` → `gameover`

When all humans disconnect, the room is deleted from memory (no persistence).

**Navigation behavior:**

- **Back To Opponent** leaves the room and returns to setup.
- **Back To Games** keeps the room, and hosts send `return_to_games` to reset the selected variant to `ready`.
- Variant change is blocked while `playing` or `paused`, so the reset path is the intended way back from active gameplay.

---

## Chess variants

Defined in `VARIANTS` (`server.py`) and mirrored in `defaultVariants` (`game.js`). Host-only selection via `select_game`. Client-side card art lives in `variantCardMeta` (`game.js`) with a safe default for variants that do not define custom art.

| ID | Label | Implementation notes |
|----|-------|----------------------|
| `classic` | Classic | `chess.Board` |
| `three_check` | Three-Check | `chess.variant.ThreeCheckBoard`; check counts in `variant.checks` |
| `king_hill` | King of the Hill | `chess.variant.KingOfTheHillBoard` |
| `atomic` | Atomic | `chess.variant.AtomicBoard` |
| `dice` | Dice Chess | Standard board; `dice_piece` rolled each turn; only that piece type may move |
| `fog` | Fog of War | Standard board; `visible_squares()` filters board/moves per viewer |
| `thress` | Thress | Every 3rd move (`move_count`), active player picks 1 of 3 mutator cards before moving |

### Thress mutators

Eight cards in `THRESS_MUTATORS` (`server.py`). Choosing a card calls `apply_mutator()` which mutates the board directly (pawn advances, piece removal, file shifts, etc.). These mutations are **not** re-validated as standard chess positions—they are intentional chaos.

Mutator ids: `march_pawns`, `the_rumbling`, `they_deserved_it`, `going_woke`, `horse_girl_summoning`, `rook_market_crash`, `pawn_union`, `minor_inconvenience`.

Thress uses custom `moveHistory` and `mutatorHistory` arrays because direct board edits can clear `python-chess`' internal `move_stack`. `moveHistory` preserves UCI moves; `mutatorHistory` records which card was chosen, who chose it, the target ply, and the resulting message.

`advance_all_pawns` (used by `march_pawns` and `the_rumbling`), `shift_files_left` (used by `going_woke`), and `shift_friendly_pawns_right` (used by `pawn_union`) all use a **snapshot approach**: they build a complete list of valid moves from the original board state, then execute them. This guarantees each piece moves at most one square per activation and prevents chain reactions where a vacated square is immediately reused by the next piece in iteration order.

---

## Game shelf UI

The variant picker is a neal.fun-style game shelf: large illustrated cards in a responsive grid, with the title and short description below each thumbnail area.

**Layout (`index.html`):**

- The old compact variant picker is now a **Games** hub section.
- `game-hub-header` contains the `Games` title and contextual `variant-picker-hint`.
- Cards render into `game-card-grid`, which auto-fills a responsive card layout.
- The shelf uses the system font stack (`"Segoe UI", system-ui, sans-serif`) — no external font requests.

**Card design (`styles.css`):**

- White elevated cards with rounded corners and soft shadows.
- Colorful 4:3 art panels per mode using a unique gradient and large icon.
- Hover lift/scale effect for a clickable "door into a game" feel.
- Gold ring plus a **Selected** badge for the active mode.
- Disabled state when the user is not host, not in a room, or a match is active.
- `button.game-card` overrides keep global pill-button styles from affecting the cards.

**Rendering (`game.js`):**

- `variantCardMeta` maps each variant id to an icon and gradient.
- `renderVariantPicker()` builds cards as art panel, title, and description.
- `updateVariantPickerHint()` changes helper copy based on room/host/game state.
- Overlay copy now says `Choose A Game` and directs hosts to pick from the Games shelf.

Per-mode visuals:

| Mode | Icon | Vibe |
|------|------|------|
| Classic | ♔ | Warm gold |
| Three-Check | ♚ | Red/orange |
| King of the Hill | ⛰ | Green/teal |
| Atomic | 💥 | Pink blast |
| Dice Chess | 🎲 | Purple |
| Fog of War | 🌫 | Gray mist |
| Thress | 🃏 | Rainbow chaos |

---

## Appearance system

The UI exposes lightweight client-side appearance controls. Choices are stored in `localStorage` under `rook-rumble-appearance` and applied as data attributes on `<body>`.

| Control | Body attribute | Options |
|---------|----------------|---------|
| Theme | `data-theme` | `forest`, `midnight`, `paper`, `ocean`, `berry` |
| Background | `data-pattern` | `argyle`, `dots`, `grid`, `plain` |
| Board | `data-board` | `classic`, `slate`, `sand`, `contrast` |
| Pieces | `data-pieces` | `classic`, `three_d`, `woodcut`, `marble` |

Themes are CSS variable overrides for text, panels, accents, shadows, and page gradients. Pattern choices swap the page background layer. Board choices override `--board-light`/`--board-dark` square colors. Piece choices override `--piece-white`/`--piece-black` glyph colors; the `three_d` style adds a layered `text-shadow` depth effect on top.

Because these are purely client-side preferences, two players in the same room can use different themes, boards, and piece styles without affecting game state.

---

## Bot system

Bots are defined in `BOT_DIFFICULTIES` (`server.py`). Each has `skill`, `chaos`, `aggression`, `greed`, and optional `style` (`chaos`, `greedy`, `attacker`, `coach`, `endboss`).

| ID | Label |
|----|-------|
| `easy` | Easy Explorer |
| `medium` | Balanced Club Bot |
| `hard` | Hard Grinder |
| `dougdoug` | DougDoug Chaos |
| `greedy_goblin` | Greedy Goblin |
| `coffeehouse` | Coffeehouse Attacker |
| `gotham` | Gotham Tactics |
| `magnus` | Magnus-ish Endboss |

**Move selection:** `ChessVariantGame.choose_bot_move()` scores legal moves (material, checks, center, personality bonuses), adds randomness scaled by `chaos`/`skill`, and picks from the top band. The `chaos` style applies a **reduced** penalty (not a bonus) for early queen and king moves: non-chaos bots are penalized 22/30 points respectively; chaos bots are penalized 8/5 points. `score_bot_move` wraps `board.push`/`board.pop` in a `try/finally` so the board is always restored to its pre-scoring state even if an exception occurs mid-evaluation.

**Bot rooms:** `create_bot_room` sets `room.bot_difficulty`; Black slot is treated as connected. `play_bot_turns()` runs after human moves, start, and restart; it also auto-picks Thress mutators for the bot. Each bot move and mutator pick is followed by `await asyncio.sleep(0)` to yield control back to the event loop between synchronous CPU-bound scoring calls.

**UI note:** `index.html` hardcodes three bot options in the dropdown (DougDoug, Gotham, Magnus). The server sends the full list in `sync.botDifficulties`; `game.js` `renderBotSelector()` rebuilds options from that payload.

---

## WebSocket protocol

**Endpoint:** `ws://<host>/ws` (or `wss://` if served over HTTPS)

### Client → server

| `type` | Payload | Who | Notes |
|--------|---------|-----|-------|
| `create_room` | — | anyone | Host becomes White |
| `create_bot_room` | `{ difficulty }` | anyone | Bot as Black |
| `join_room` | `{ roomCode }` | anyone | 6-digit string |
| `leave_room` | — | in room | Returns lobby sync |
| `select_game` | `{ game }` | host | Variant id from `VARIANTS` |
| `start_game` | — | host | Requires 2 connected sides + variant |
| `toggle_pause` | — | host | `playing` ↔ `paused` |
| `restart_game` | — | host | Resets board; bot may move if Black starts |
| `return_to_games` | — | host | Resets selected variant to `ready` so the UI can return to game selection |
| `chess_move` | `{ from, to, promotion? }` | current player | Squares like `"e2"`; promotion `"q"`/`"r"`/`"b"`/`"n"` |
| `choose_mutator` | `{ mutatorId }` | Thress chooser | Required before move when `pendingMutator` set |

### Server → client

**`sync`** — full state snapshot (sent on connect, after every room/game change):

```json
{
  "type": "sync",
  "roomCode": "123456",
  "selectedGame": "classic",
  "availableGames": [{ "id", "label", "description" }],
  "playerIndex": 0,
  "isHost": true,
  "players": [{ "connected", "label" }],
  "bot": { "enabled", "difficulty", "label", "color" },
  "botDifficulties": [{ "id", "label", "description" }],
  "game": { /* see Game snapshot below */ }
}
```

**`error`** — `{ "type": "error", "message": "..." }` for validation failures, including non-object JSON payloads (the server rejects any message whose top-level JSON value is not a `{…}` object).

### Game snapshot (`sync.game`)

Key fields from `ChessVariantGame.snapshot()`:

| Field | Description |
|-------|-------------|
| `kind` | `"chess"` or `"none"` |
| `gameState` | `waiting`, `ready`, `playing`, `paused`, `gameover` |
| `message` | Human-readable status |
| `board` | `{ "e2": { "symbol", "color", "type" }, ... }` — fog-filtered per viewer |
| `turn` | `"white"` or `"black"` |
| `legalMoves` | `{ "e2": [{ "to", "promotion" }], ... }` — only when `playing` |
| `lastMove` | `{ "from", "to", "promotion" }` |
| `moveHistory` | UCI move list preserved separately from `python-chess`' internal stack |
| `mutatorHistory` | Thress card choices and resulting mutation messages |
| `result` | e.g. `"1-0"` when game over |
| `variant` | `{ "id", "label", "checks?", "dicePiece?", "pendingMutator?", "activeMutators?" }` |

---

## Key server classes (`server.py`)

| Class / object | Role |
|----------------|------|
| `ChessVariantGame` | Board, moves, variant rules, bot scoring, Thress mutators, snapshots |
| `Room` | Player slots, host, selected variant, bot config, broadcast sync |
| `GameServer` | Room registry, message routing, bot turn loop |
| `server` | Global `GameServer` instance |

**Important methods:**

- `ChessVariantGame.move()` — validates and pushes moves
- `ChessVariantGame.bot_move()` / `choose_bot_move()` — bot AI
- `ChessVariantGame.choose_mutator()` / `apply_mutator()` — Thress
- `ChessVariantGame.visible_squares()` — Fog of War
- `Room.broadcast_sync()` — sends per-client snapshots
- `GameServer.handle_message()` — WebSocket message dispatcher

**HTTP routes:** `GET /`, `/index.html`, `/game.js`, `/styles.css`, `/ws`

---

## Client behavior (`game.js`)

**State object:** `state` holds `ws`, `roomCode`, `playerIndex`, `isHost`, `bot`, `players`, `game`, UI selection (`selectedSquare`, `pendingPromotion`).

**Rendering:**

- `applySync()` — applies server payload, triggers HUD + board
- `setStep()` — controls the 3-step UI (`setup`, `games`, `play`)
- `applyAppearance()` — applies and persists theme/pattern/board/piece preferences
- `renderChessBoard()` — 8×8 grid; orientation flips for Black via `chessSquaresForPlayer()`: ranks stay descending (8→1 top-to-bottom) for both colors; only files reverse for Black (h→a), giving Black rank 8 at the top and the h-file on the left
- `renderVariantPicker()` — neal.fun-style game cards; host-only, disabled during active games
- `updateVariantPickerHint()` — dynamic helper text for the Games shelf
- `renderBotSelector()` — rebuilds bot personality options from server sync
- `syncOverlay()` — modal flow for lobby / variant / start / pause / game over
- `renderMutatorPanel()` — Thress card buttons

**Reconnect:** On WebSocket close, client clears room state and reconnects after 1200ms.

**Move input:** Click own piece with legal moves → click target. Promotion shows panel; sends `chess_move` with promotion piece. Blocked during opponent turn, pending promotion, or pending Thress mutator.

---

## UI structure (`index.html`)

Sections: hero → flow bar → appearance panel → Step 1 setup panel → Step 2 Games hub/game shelf → Step 3 player HUD and game shell.

The three step panels are:

- `setup-panel` (`data-step-panel="setup"`): online room creation/joining, offline bot creation, URL/room/connection cards.
- `games-panel` (`data-step-panel="games"`): back/leave/continue actions plus the Games shelf.
- `play-panel` (`data-step-panel="play"`): back actions, HUD, chess board, mutator/promotion panels, overlay, start/pause/restart controls.

Element ids match `document.getElementById(...)` calls at the top of `game.js`. Overlay action button mirrors create/start/resume/restart depending on state.

---

## Styling (`styles.css`)

CSS variables in `:root` define the default forest olive/gold theme. `body[data-theme]`, `body[data-pattern]`, `body[data-board]`, and `body[data-pieces]` override the look without changing layout or game logic.

Board classes: `.chess-square`, `.light`/`.dark`, `.is-selected`, `.is-target`, `.is-last-move`, `.is-movable`. Square colors read `--board-light`/`--board-dark`; piece colors read `--piece-white`/`--piece-black`.

Game shelf classes: `.game-hub`, `.game-card-grid`, `.game-card`, `.game-card-art`, `.game-card-icon`, `.game-card-body`, `.game-card-badge`.

Flow and mobile classes: `.flow-bar`, `.flow-step`, `.appearance-panel`, `.step-panel`, `.mode-grid`, `.mode-card`, `.step-actions`.

Menu and settings classes: `.menu-button` (fixed gear icon), `.menu-modal` (fixed overlay), `.menu-card`, `.menu-view`, `.menu-header`, `.icon-button`, `.menu-actions`. Settings panel: `.settings-layout` (flex row), `.settings-fields`, `.settings-preview`, `.preview-board` (4×4 grid), `.preview-square` — the preview squares use the same CSS variables as the board so all theme, board, and piece style changes are reflected immediately.

Responsive breakpoints:

- `920px`: stacks setup/gameplay grids and action rows.
- `720px`: tightens app padding, reduces heading/piece sizes, uses a near-full-width board, and makes cards single-column for mobile-app-style screens.

---

## Conventions for contributors and AI agents

1. **Server is source of truth.** Never trust client-side move legality for game state changes.
2. **Keep variant lists in sync.** Add variants to `VARIANTS` in `server.py`; add matching entry to `defaultVariants` in `game.js`; optionally add `variantCardMeta` art so the game shelf does not fall back to the generic card.
3. **Bot personalities** only need server-side `BOT_DIFFICULTIES` changes unless exposing new defaults in HTML.
4. **Thress mutators** must implement logic in `apply_mutator()` and register in `THRESS_MUTATORS`; record enough detail in `mutatorHistory` if the card affects replay/debugging.
5. **Fog of War** changes belong in `visible_squares()` and will automatically affect snapshots.
6. **Appearance changes** should prefer CSS variables/data attributes over branching game logic.
7. **Step navigation** is client-only except for `return_to_games`, which intentionally resets a host's active game to ready.
8. **No tests exist.** Manually verify: create/join room, each variant, bot game, promotion, pause/restart, step navigation, themes, mobile width, disconnect/reconnect.
9. **Minimal diffs preferred.** Match existing patterns: plain functions in `game.js`, async handlers in `server.py`, no new frameworks without explicit request.

---

## Known limitations

- No persistence (rooms, games, accounts)
- No chess clocks or matchmaking
- No authentication or chess-clock timers
- Bot strength is heuristic, not engine-based (no Stockfish)
- Thress board mutations may produce non-standard positions
- Thress replay requires both `moveHistory` and `mutatorHistory`; UCI moves alone are not enough to reconstruct mutated boards
- HTML bot dropdown initially contains a small subset, then expands from server `botDifficulties` after WebSocket sync
- Appearance preferences are per-browser only and are not synced between players
- Mobile-friendly layout is responsive web UI; there is no native app wrapper yet
- No git hooks, CI, or automated tests in repo

---

## Extension ideas (not implemented)

The room + `ChessVariantGame` abstraction supports adding:

- New variants (register board class + rules in `ChessVariantGame`)
- Stronger bots (integrate UCI engine or deeper search)
- Saved games / replay using `moveHistory`, `mutatorHistory`, final FEN, and room metadata
- Timers, ratings, online deployment behind reverse proxy
- Matchmaking or invite links

When adding features, extend `handle_message()` and the `sync` payload shape together so clients stay in sync.

---

## Environment

| Variable | Default | Purpose |
|----------|---------|---------|
| `PORT` | `8000` | HTTP/WebSocket listen port |

Host is always `0.0.0.0` for LAN access. `local_ip()` uses a UDP trick to print the LAN address on startup.

---

## Security

This is a casual game with no accounts, no personal data, and no reason to collect any user information. The following measures protect the server and its users:

### HTTP headers (all responses)

Injected by `security_headers_middleware` in `server.py`:

| Header | Value |
|--------|-------|
| `Content-Security-Policy` | `default-src 'self'; connect-src 'self' ws: wss:; img-src 'self' data:; object-src 'none'; base-uri 'self'; frame-ancestors 'none'` |
| `X-Frame-Options` | `DENY` |
| `X-Content-Type-Options` | `nosniff` |
| `Referrer-Policy` | `no-referrer` |
| `Permissions-Policy` | `geolocation=(), camera=(), microphone=()` |

The CSP blocks external scripts, external styles, plugins, and framing. `Permissions-Policy` prevents the app from requesting geolocation, camera, or microphone access.

### WebSocket limits

| Constant | Value | Effect |
|----------|-------|--------|
| `MAX_MSG_SIZE` | 16 384 bytes | Message larger than 16 kB is rejected before parsing |
| `MAX_CONNECTIONS_PER_IP` | 6 | IP with ≥ 6 open connections gets HTTP 429 on the next attempt |
| `MSG_RATE_LIMIT` | 10 messages / 1 second | Connection sending more is closed immediately |

IP detection uses `X-Forwarded-For` (required behind Render's proxy) with a fallback to `request.remote`. IP counts are stored in the module-level `_ip_connections` dict and decremented in a `finally` block so counts are always accurate even on abnormal disconnect.

### No user data retained

- No database, no logging, no analytics.
- Rooms and game state live only in process memory and are deleted when all players disconnect.
- No cookies, sessions, or tokens are issued.
- No external services are contacted at runtime (fonts are system-stack, no CDN requests).
- HTTPS is terminated by Render's edge; the app never handles TLS directly and never stores IP addresses.

---

## Cloud deployment (Render.com)

`render.yaml` is included. To deploy:

1. Push the repo to GitHub.
2. Go to [render.com](https://render.com), create an account, and click **New → Blueprint**.
3. Connect the GitHub repo — Render reads `render.yaml` and auto-configures the service.
4. Deploy. Render gives you a URL like `https://rook-rumble-xxxx.onrender.com`.

The server already reads `PORT` from the environment and serves all static files — no extra config needed.

> **Free tier note:** Render free web services spin down after 15 minutes of inactivity. The first request after spin-down takes ~30 s. Upgrade to the $7/month Starter plan to keep the server always on.

---

## Android app (Google Play Store)

The Android app uses [Capacitor](https://capacitorjs.com/) to wrap the web client as a native Android WebView app that loads your Render deployment.

### Prerequisites

- [Node.js](https://nodejs.org/) 18+
- [Android Studio](https://developer.android.com/studio) with the Android SDK installed
- A deployed Render.com URL (see above)

### One-time setup

```bash
# 1. Install Capacitor
npm install

# 2. Edit capacitor.config.json — replace the placeholder with your Render URL:
#    "url": "https://YOUR-APP.onrender.com"

# 3. Add the Android platform (creates the android/ directory)
npx cap add android

# 4. Sync web assets into the Android project
npx cap sync
```

### Building the APK / AAB

```bash
# Open the project in Android Studio
npx cap open android
```

In Android Studio:

1. Wait for Gradle sync to finish.
2. **Build → Generate Signed Bundle / APK…**
3. Choose **Android App Bundle** (required for Play Store) or **APK** (for direct install).
4. Create a new keystore (save it somewhere safe — you need it for every future update).
5. Build the release bundle.

### Submitting to Google Play

1. Create a [Google Play Console](https://play.google.com/console) account ($25 one-time fee).
2. **Create app → Production → Create new release**.
3. Upload the `.aab` file from `android/app/build/outputs/bundle/release/`.
4. Fill in the store listing (description, screenshots, content rating).
5. Submit for review (typically 1–3 days).

### Updating the app

After changing `server.py`, `game.js`, or `styles.css`:

```bash
# Server changes: just push to GitHub — Render auto-deploys.
# Client changes (CSS/JS): push to GitHub, then:
npx cap sync
# Rebuild in Android Studio and submit a new release to Play Store.
```

### App ID

The default `appId` in `capacitor.config.json` is `com.yourname.rookrumble`. Change this to a reverse-domain identifier you control (e.g. `com.marco.rookrumble`) before running `npx cap add android` — it cannot be changed after the app is published.
