from .registry import BOT_DIFFICULTIES, VARIANTS, bots_payload, variants_payload
from .variants import VARIANT_CLASSES


class Room:
    def __init__(self, code):
        self.code = code
        self.clients = [None, None]
        self.host_index = 0
        self.selected_game = "none"
        self.chess_game = None
        self.bot_difficulty = None

    def active_game(self):
        return self.chess_game

    def bot_enabled(self):
        return self.bot_difficulty in BOT_DIFFICULTIES

    def bot_payload(self):
        if not self.bot_enabled():
            return {"enabled": False, "difficulty": None, "label": None, "color": None}
        difficulty = BOT_DIFFICULTIES[self.bot_difficulty]
        return {
            "enabled": True,
            "difficulty": self.bot_difficulty,
            "label": difficulty["label"],
            "color": "black",
        }

    def players_payload(self):
        players = []
        for index, client in enumerate(self.clients):
            label = "White" if index == 0 else "Black"
            connected = client is not None
            if index == 1 and self.bot_enabled():
                label = BOT_DIFFICULTIES[self.bot_difficulty]["label"]
                connected = True
            players.append({"connected": connected, "label": label})
        return players

    def connected_count(self):
        return self.human_connected_count() + (1 if self.bot_enabled() else 0)

    def human_connected_count(self):
        return sum(client is not None for client in self.clients)

    def available_slot(self):
        if self.bot_enabled():
            return None
        for index, client in enumerate(self.clients):
            if client is None:
                return index
        return None

    def get_slot(self, ws):
        for index, client in enumerate(self.clients):
            if client is ws:
                return index
        return None

    def select_game(self, variant_id, timer_config=None):
        if variant_id not in VARIANTS:
            return False
        self.selected_game = variant_id
        self.chess_game = VARIANT_CLASSES[variant_id](variant_id)
        if timer_config:
            self.chess_game.set_timer(timer_config)
        self.sync_presence()
        return True

    def sync_presence(self):
        if self.human_connected_count() == 1:
            occupied = [i for i, c in enumerate(self.clients) if c is not None]
            self.host_index = occupied[0]

        if not self.chess_game:
            return

        if self.connected_count() < 2:
            self.chess_game.set_waiting("Waiting for another player to join this room.")
            return

        if self.chess_game.game_state in {"waiting", "ready"}:
            self.chess_game.set_ready()

    def empty_game_snapshot(self):
        return {
            "kind": "none",
            "gameState": "waiting",
            "message": "Create or join a room, then choose a chess variant.",
        }

    async def send_sync(self, ws):
        slot = self.get_slot(ws)
        payload = {
            "type": "sync",
            "roomCode": self.code,
            "selectedGame": self.selected_game,
            "availableGames": variants_payload(),
            "playerIndex": slot,
            "isHost": slot == self.host_index,
            "players": self.players_payload(),
            "bot": self.bot_payload(),
            "botDifficulties": bots_payload(),
            "game": (
                self.chess_game.snapshot(slot)
                if self.chess_game
                else self.empty_game_snapshot()
            ),
        }
        await ws.send_json(payload)

    async def broadcast_sync(self):
        for ws in self.clients:
            if ws is not None:
                await self.send_sync(ws)
