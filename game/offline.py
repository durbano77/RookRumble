import random
from .room import Room
from .registry import BOT_DIFFICULTIES, lobby_sync_payload, variants_payload, bots_payload


class OfflineSession:
    """Synchronous single-player session for use inside Pyodide."""

    def __init__(self):
        self.room = None
        self.player_index = 0  # Human is always white (slot 0)

    def handle(self, message_type, payload):
        method = getattr(self, f"_on_{message_type}", None)
        if method:
            return method(payload)
        return lobby_sync_payload("Unknown message.")

    # ── Room sync ──────────────────────────────────────────────────────────

    def _sync(self):
        room = self.room
        game = room.active_game()
        return {
            "type": "sync",
            "roomCode": room.code,
            "selectedGame": room.selected_game,
            "availableGames": variants_payload(),
            "playerIndex": self.player_index,
            "isHost": True,
            "players": room.players_payload(),
            "bot": room.bot_payload(),
            "botDifficulties": bots_payload(),
            "game": game.snapshot(self.player_index) if game else room.empty_game_snapshot(),
        }

    # ── Handlers ──────────────────────────────────────────────────────────

    def _on_create_bot_room(self, payload):
        difficulty = str(payload.get("difficulty", "easy")).lower()
        if difficulty not in BOT_DIFFICULTIES:
            return lobby_sync_payload("Unknown difficulty.")
        self.room = Room("offline")
        self.room.clients[0] = True  # Sentinel: human connected
        self.room.bot_difficulty = difficulty
        self.room.sync_presence()
        return self._sync()

    def _on_select_game(self, payload):
        if not self.room:
            return lobby_sync_payload()
        timer_raw = payload.get("timer")
        timer = None
        if isinstance(timer_raw, dict):
            minutes = timer_raw.get("minutes")
            increment = timer_raw.get("increment", 0)
            if isinstance(minutes, (int, float)) and 0 < minutes <= 60:
                timer = {"minutes": int(minutes), "increment": max(0, int(increment))}
        self.room.select_game(str(payload.get("game", "")), timer)
        return self._sync()

    def _on_start_game(self, payload):
        if not self.room:
            return lobby_sync_payload()
        game = self.room.active_game()
        if game:
            game.start()
            self._run_bot_turns()
        return self._sync()

    def _on_chess_move(self, payload):
        if not self.room:
            return lobby_sync_payload()
        game = self.room.active_game()
        if game:
            game.move(self.player_index,
                      str(payload.get("from", "")),
                      str(payload.get("to", "")),
                      payload.get("promotion"))
            self._run_bot_turns()
        return self._sync()

    def _on_engine_move(self, payload):
        """Apply a move from the client-side Stockfish engine as the bot."""
        if not self.room:
            return lobby_sync_payload()
        game = self.room.active_game()
        if game and game.game_state == "playing" and game.player_index_for_turn() == 1:
            game.move(1, str(payload.get("from", "")), str(payload.get("to", "")), payload.get("promotion"))
        return self._sync()

    def _on_choose_mutator(self, payload):
        if not self.room:
            return lobby_sync_payload()
        game = self.room.active_game()
        if game:
            game.choose_mutator(self.player_index, str(payload.get("mutatorId", "")))
            self._run_bot_turns()
        return self._sync()

    def _on_restart_game(self, payload):
        if not self.room:
            return lobby_sync_payload()
        game = self.room.active_game()
        if game:
            game.restart()
            self._run_bot_turns()
        return self._sync()

    def _on_return_to_games(self, payload):
        if not self.room:
            return lobby_sync_payload()
        game = self.room.active_game()
        if game:
            game.return_to_ready()
        return self._sync()

    def _on_toggle_pause(self, payload):
        if not self.room:
            return lobby_sync_payload()
        game = self.room.active_game()
        if game:
            game.toggle_pause()
        return self._sync()

    def _on_leave_room(self, payload):
        self.room = None
        return lobby_sync_payload("You left the room.")

    # ── Bot ───────────────────────────────────────────────────────────────

    def _run_bot_turns(self):
        game = self.room.active_game()
        difficulty = self.room.bot_difficulty
        if not game or not self.room.bot_enabled():
            return
        if BOT_DIFFICULTIES.get(difficulty, {}).get("engine"):
            return  # Engine moves come from client-side Stockfish
        safety = 0
        while game.game_state == "playing" and game.player_index_for_turn() == 1 and safety < 4:
            safety += 1
            if game.pending_mutator:
                options = game.pending_mutator.get("options", [])
                if not options:
                    break
                game.choose_mutator(1, random.choice(options)["id"])
                continue
            if not game.bot_move(difficulty):
                break
